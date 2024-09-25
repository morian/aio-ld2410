from __future__ import annotations

import asyncio
import copy
import logging
import sys
from asyncio import StreamReader, StreamWriter
from contextlib import AsyncExitStack, asynccontextmanager, suppress
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar, cast

from construct import Container
from serial_asyncio_fast import open_serial_connection

from .exception import CommandError, CommandStatusError, ConnectError, ModuleRestartedError
from .models import (
    AuxiliaryControlConfig,
    AuxiliaryControlStatus,
    ConfigModeStatus,
    FirmwareVersion,
    GateSensitivityConfig,
    ParametersConfig,
    ParametersStatus,
    ReportStatus,
    container_to_model,
)
from .protocol import (
    BaudRateIndex,
    Command,
    CommandCode,
    CommandFrame,
    Frame,
    FrameType,
    Reply,
    ReplyStatus,
    Report,
    ResolutionIndex,
)

if sys.version_info >= (3, 11):  # pragma: no branch
    from asyncio import timeout
else:  # pragma: no cover
    from async_timeout import timeout  # type: ignore[import-not-found]

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Mapping
    from types import TracebackType

    from typing_extensions import Concatenate, Never, ParamSpec, Self, TypeAlias, Unpack

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

    DEFAULT_COMMAND_TIMEOUT = 2.0
    DEFAULT_BAUDRATE = 256000

    def __init__(
        self,
        device: str,
        *,
        baudrate: int = DEFAULT_BAUDRATE,
        command_timeout: float | None = DEFAULT_COMMAND_TIMEOUT,
        read_bufsize: int | None = None,
    ) -> None:
        """Create a new client the supplied device."""
        self._baudrate = baudrate
        self._command_timeout = command_timeout
        self._device = device
        self._config_lock = asyncio.Lock()
        self._read_bufsize = read_bufsize
        self._report = None  # type: ReportStatus | None
        self._report_condition = asyncio.Condition()
        self._request_lock = asyncio.Lock()
        self._connected = False
        self._context = None  # type: AsyncExitStack | None
        self._replies = None  # type: asyncio.Queue[_ReplyType | None] | None
        self._restarted = False
        self._rdtask = None  # type: asyncio.Task[None] | None
        self._writer = None  # type: StreamWriter | None

    @property
    def configuring(self) -> bool:
        """Tell whether configuration mode is currently entered."""
        return bool(not self._restarted and self._config_lock.locked())

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
                    elif frame.type == FrameType.REPORT:  # pragma: no branch
                        report = Report.parse(frame.data)
                        async with self._report_condition:
                            self._report = container_to_model(ReportStatus, report.data)
                            self._report_condition.notify_all()
                except Exception:
                    # Happens when we received a frame with unknown content.
                    # For the user perpective this will most likely ends with a timeout.
                    logger.exception('Unable to handle frame: %s', chunk.hex(' '))
        finally:
            self._connected = False
            # This is needed here because we may be stuck waiting on a reply.
            with suppress(asyncio.QueueFull):
                replies.put_nowait(None)

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

            async with timeout(self._command_timeout):
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
                        raise ConnectError('Device has disconnected')

                    valid_reply = bool(code == int(reply.code))
                    if not valid_reply:
                        logger.warning('Got reply code %u (request was %u)', reply.code, code)

        # MyPy does not see that reply cannot be None on here.
        reply = cast(_ReplyType, reply)
        if int(reply.status) != ReplyStatus.SUCCESS:
            raise CommandStatusError(f'Command {code} received bad status: {reply.status}')

        return reply

    @asynccontextmanager
    async def configure(self) -> AsyncIterator[ConfigModeStatus]:
        """Enter configuration mode."""
        async with self._config_lock:
            resp = await self._request(CommandCode.CONFIG_ENABLE)
            try:
                yield container_to_model(ConfigModeStatus, resp.data)
            except ModuleRestartedError:
                logger.info('Configuration context has closed due to module restart.')
            finally:
                if not self._restarted:
                    await self._request(CommandCode.CONFIG_DISABLE)
                self._restarted = False

    @configuration
    async def get_auxiliary_controls(self) -> AuxiliaryControlStatus:
        """Get the auxiliary controls (OUT pin)."""
        resp = await self._request(CommandCode.AUXILIARY_CONTROL_GET)
        return container_to_model(AuxiliaryControlStatus, resp.data)

    @configuration
    async def get_bluetooth_address(self) -> bytes:
        """Get the module's bluetooth mac address."""
        resp = await self._request(CommandCode.BLUETOOTH_MAC_GET)
        return bytes(resp.data.address)

    @configuration
    async def get_distance_resolution(self) -> int:
        """Get the gate distance resolution (in centimeter).

        This command seems to be available for a few devices / firmwares.
        """
        resp = await self._request(CommandCode.DISTANCE_RESOLUTION_GET)
        index = int(resp.data.resolution)
        if index == ResolutionIndex.RESOLUTION_20CM:
            return 20
        if index == ResolutionIndex.RESOLUTION_75CM:
            return 75
        raise CommandError(f'Unhandled distance resolution index {index}')

    @configuration
    async def get_firmware_version(self) -> FirmwareVersion:
        """Get the current firmware version."""
        resp = await self._request(CommandCode.FIRMWARE_VERSION)
        return container_to_model(FirmwareVersion, resp.data)

    def get_last_report(self) -> ReportStatus | None:
        """Get the latest report available, if any."""
        return copy.deepcopy(self._report)

    @configuration
    async def get_parameters(self) -> ParametersStatus:
        """Read general parameters."""
        resp = await self._request(CommandCode.PARAMETERS_READ)
        return container_to_model(ParametersStatus, resp.data)

    async def get_next_report(self) -> ReportStatus:
        """Wait and get the next available report."""
        async with self._report_condition:
            await self._report_condition.wait()
            report = cast(ReportStatus, self._report)
        return copy.deepcopy(report)

    async def get_reports(self) -> AsyncIterator[ReportStatus]:
        """Get reports as an asynchronous iterator."""
        while True:
            yield await self.get_next_report()

    @configuration
    async def reset_to_factory(self) -> None:
        """Reset the module to its factory settings.

        This command is effective after a module restart.
        """
        await self._request(CommandCode.FACTORY_RESET)

    @configuration
    async def restart_module(self) -> Never:
        """Restart the module.

        Please note that it can take at least 1100ms for it to be available again.
        Raises a `ModuleRestartedError` intended to be caught by the configuration context.
        """
        await self._request(CommandCode.MODULE_RESTART)
        self._restarted = True
        raise ModuleRestartedError('Module is being restarted')

    @configuration
    async def set_auxiliary_controls(self, **kwargs: Unpack[AuxiliaryControlConfig]) -> None:
        """Configure the auxiliary controls (OUT pin)."""
        await self._request(
            CommandCode.AUXILIARY_CONTROL_SET,
            AuxiliaryControlConfig(**kwargs),
        )

    @configuration
    async def set_baudrate(self, baudrate: int) -> None:
        """Set the serial baud rate to operate.

        Only baud rates from `BaudRateIndex` are valid, a KeyError is raised otherwise.
        This command is effective after a module restart.
        """
        await self._request(
            CommandCode.BAUD_RATE_SET,
            {'index': int(BaudRateIndex.from_integer(baudrate))},
        )

    @configuration
    async def set_bluetooth_mode(self, enabled: bool) -> None:
        """Set device bluetooth mode."""
        await self._request(CommandCode.BLUETOOTH_SET, {'enabled': enabled})

    @configuration
    async def set_bluetooth_password(self, password: str) -> None:
        """Set device bluetooth password.

        This command seems to be available for a few devices / firmwares.
        The password must have no more than 6 ascii characters.
        """
        if len(password) > 6 or not password.isascii():
            raise CommandError('Bluetooth password must have less than 7 ascii characters.')
        await self._request(CommandCode.BLUETOOTH_PASSWORD_SET, {'password': password})

    @configuration
    async def set_distance_resolution(self, resolution: int) -> None:
        """Set the gate distance resolution (in centimeter).

        This command seems to be available for a few devices / firmwares.
        This command requires a module restart to be effective.
        `resolution` can only be 20 or 75 centimeters.
        """
        index = ResolutionIndex.RESOLUTION_75CM
        if resolution == 20:
            index = ResolutionIndex.RESOLUTION_20CM
        elif resolution != 75:
            raise CommandError(f'Unknown index for distance resolution {resolution}')
        await self._request(CommandCode.DISTANCE_RESOLUTION_SET, {'resolution': index})

    @configuration
    async def set_engineering_mode(self, enabled: bool) -> None:
        """Set device in engineering mode."""
        code = CommandCode.ENGINEERING_ENABLE if enabled else CommandCode.ENGINEERING_DISABLE
        await self._request(code)

    @configuration
    async def set_parameters(self, **kwargs: Unpack[ParametersConfig]) -> None:
        """Set general parameters."""
        # This step is needed to ensure argument correctness.
        await self._request(CommandCode.PARAMETERS_WRITE, ParametersConfig(**kwargs))

    @configuration
    async def set_gate_sentivity(self, **kwargs: Unpack[GateSensitivityConfig]) -> None:
        """Set the sensor sensitivity."""
        await self._request(CommandCode.GATE_SENSITIVITY_SET, GateSensitivityConfig(**kwargs))
