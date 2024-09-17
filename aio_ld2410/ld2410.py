from __future__ import annotations

import asyncio
import logging
from asyncio import StreamReader, StreamWriter
from contextlib import AsyncExitStack, asynccontextmanager, suppress
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar, cast

from construct import Container
from serial_asyncio_fast import open_serial_connection

from .exception import CommandError, CommandStatusError, ConnectError
from .models import (
    ConfigModeStatus,
    FirmwareVersion,
    GateSensitivityConfig,
    ParametersConfig,
    ParametersStatus,
    container_to_model,
)
from .protocol import (
    Command,
    CommandCode,
    CommandFrame,
    Frame,
    FrameType,
    Reply,
    ReplyStatus,
    Report,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Mapping
    from types import TracebackType

    from typing_extensions import Concatenate, ParamSpec, Self, TypeAlias, Unpack

    _P = ParamSpec('_P')
    _T = TypeVar('_T')

_ReplyType: TypeAlias = Container[Any]
logger = logging.getLogger(__package__)


def configuration(
    func: Callable[Concatenate[LD2410, _P], Awaitable[_T]],
) -> Callable[Concatenate[LD2410, _P], Awaitable[_T]]:
    """Decorate an async method so we can check for the configuration context."""
    if not asyncio.iscoroutinefunction(func):
        raise RuntimeError('@configuration decorator is only suitable for async methods.')

    async def _check_config_context(
        self: LD2410,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> _T:
        if not self.configuring:
            raise CommandError('This method requires a configuration context')
        return await func(self, *args, **kwargs)

    return _check_config_context


class LD2410:
    """Client of the LD2410 sensor."""

    DEFAULT_BAUDRATE = 256000

    def __init__(
        self,
        device: str,
        *,
        baudrate: int = DEFAULT_BAUDRATE,
        read_bufsize: int | None = None,
    ) -> None:
        """Create a new client the supplied device."""
        self._baudrate = baudrate
        self._device = device
        self._read_bufsize = read_bufsize
        self._config_lock = asyncio.Lock()
        self._request_lock = asyncio.Lock()
        self._connected = False
        self._context = None  # type: AsyncExitStack | None
        self._replies = None  # type: asyncio.Queue[_ReplyType | None] | None
        self._rdtask = None  # type: asyncio.Task[None] | None
        self._writer = None  # type: StreamWriter | None

    @property
    def configuring(self) -> bool:
        """Tell whether configuration mode is currently entered."""
        return self._config_lock.locked()

    @property
    def connected(self) -> bool:
        """Tell whether we are still connected and listening to frames."""
        return bool(self._connected and self._writer is not None and self._replies is not None)

    @property
    def entered(self) -> bool:
        """Tell whether the context manager is already entered."""
        return bool(self._context is not None)

    async def __aenter__(self) -> Self:
        """Enter the device's context, open the device."""
        if self.entered:
            raise RuntimeError("LD2410's instance is already entered!")

        context = await AsyncExitStack().__aenter__()
        try:
            reader, writer = await self._open_serial_connection()
            context.push_async_callback(writer.wait_closed)
            context.callback(writer.close)

            replies = asyncio.Queue()  # type: asyncio.Queue[_ReplyType | None]
            rdtask = asyncio.create_task(
                self._reader_task(reader, replies),
                name='aio_ld2410.ld2410.reader',
            )

            async def cancel_reader(task: asyncio.Task[None]) -> None:
                task.cancel('Device is closing')
                await asyncio.gather(task, return_exceptions=True)

            context.push_async_callback(cancel_reader, rdtask)
        except BaseException:
            await context.aclose()
            raise
        else:
            self._context = context
            self._connected = True
            self._replies = replies
            self._rdtask = rdtask
            self._writer = writer
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Exit the device's context."""
        context = self._context
        try:
            if context is not None:
                await context.__aexit__(exc_type, exc_val, exc_tb)
        finally:
            self._connected = False
            self._context = None
            self._replies = None
            self._rdtask = None
            self._writer = None

        # Do not prevent the original exception from going further.
        return False

    async def _open_serial_connection(self) -> tuple[StreamReader, StreamWriter]:
        """Open a serial connection for this device."""
        return await open_serial_connection(
            baudrate=self._baudrate,
            limit=self._read_bufsize,
            url=self._device,
        )

    async def _reader_task(
        self,
        reader: StreamReader,
        replies: asyncio.Queue[_ReplyType | None],
    ) -> None:
        try:
            while chunk := await reader.read(2048):
                try:
                    frame = Frame.parse(chunk)
                    if frame.type == FrameType.COMMAND:
                        reply = Reply.parse(frame.data)
                        await replies.put(reply)
                        print(reply)
                    elif frame.type == FrameType.REPORT:
                        Report.parse(frame.data)
                        # report = Report.parse(frame.data)
                        # TODO: Handle reports
                        # - Transform this report into a dataclass
                        # - Use an asyncio.Condition() to notify when a new status is received.
                        # print(report)
                except Exception:
                    logger.warning('Unable to parse frame: %s', chunk.hex(' '))
        finally:
            self._connected = False
            # This is needed here because we may be stuck waiting on a reply.
            with suppress(asyncio.QueueFull):
                replies.put_nowait(None)

    def _raise_for_status(self, reply: _ReplyType) -> None:
        """Raise when the reply status is unsuccessful."""
        if int(reply.status) != ReplyStatus.SUCCESS:
            raise CommandStatusError(
                f'Command {reply.code} returned a bad status: {reply.status}'
            )

    def _warn_for_status(self, reply: _ReplyType) -> None:
        """Warn on logger when the reply status is unsuccessful."""
        if int(reply.status) != ReplyStatus.SUCCESS:
            logger.warning('Command %s returned a bad status: %u', reply.code, reply.status)

    async def _request(
        self,
        code: CommandCode,
        args: Mapping[str, Any] | None = None,
    ) -> _ReplyType:
        """Send any kind of command to the device.

        Wait and dequeue the corresponding reply.
        """
        command = Command.build({'code': code, 'data': args})
        async with self._request_lock:
            if not self.connected:
                raise ConnectError('We are not connected to the device anymore!')

            frame = CommandFrame.build({'data': command})
            # Casts are valid here since we just checked `self.connected`.
            replies = cast(asyncio.Queue[Optional[_ReplyType]], self._replies)
            writer = cast(StreamWriter, self._writer)

            writer.write(frame)
            await writer.drain()

            # Loop until we get our reply.
            valid_reply = False
            while not valid_reply:
                reply = await replies.get()
                replies.task_done()
                if reply is None:
                    raise ConnectError('Device has been disconnected')

                valid_reply = bool(code == int(reply.code))
                if not valid_reply:
                    logger.warning('Got reply OpCode %u (request was %u)', reply.code, code)

        # MyPy does not see that reply cannot be None on here.
        return cast(_ReplyType, reply)

    @asynccontextmanager
    async def configure(self) -> AsyncIterator[ConfigModeStatus]:
        """Enter configuration mode."""
        async with self._config_lock:
            resp = await self._request(CommandCode.CONFIG_ENABLE)
            self._raise_for_status(resp)

            try:
                yield container_to_model(ConfigModeStatus, resp.data)
            finally:
                resp = await self._request(CommandCode.CONFIG_DISABLE)
                self._warn_for_status(resp)

    # @configuration
    async def get_firmware_version(self) -> FirmwareVersion:
        """Get the current firmware version."""
        resp = await self._request(CommandCode.FIRMWARE_VERSION)
        self._raise_for_status(resp)
        return container_to_model(FirmwareVersion, resp.data)

    @configuration
    async def get_parameters(self) -> ParametersStatus:
        """Read general parameters (requires configuration mode)."""
        resp = await self._request(CommandCode.PARAMETERS_READ)
        self._raise_for_status(resp)
        return container_to_model(ParametersStatus, resp.data)

    @configuration
    async def set_engineering_mode(self, enabled: bool) -> None:
        """Set device in engineering mode (requires configuration mode)."""
        code = CommandCode.ENGINEERING_ENABLE if enabled else CommandCode.ENGINEERING_DISABLE
        resp = await self._request(code)
        self._raise_for_status(resp)

    @configuration
    async def set_parameters(self, **kwargs: Unpack[ParametersConfig]) -> None:
        """Set general parameters (requires configuration mode)."""
        # This step is needed to ensure argument correctness.
        params = ParametersConfig(**kwargs)
        resp = await self._request(CommandCode.PARAMETERS_WRITE, params)
        self._raise_for_status(resp)

    @configuration
    async def set_gate_sentivity(self, **kwargs: Unpack[GateSensitivityConfig]) -> None:
        """Set the sensor sensitivity."""
        params = GateSensitivityConfig(**kwargs)
        resp = await self._request(CommandCode.GATE_SENSITIVITY_SET, params)
        self._raise_for_status(resp)
