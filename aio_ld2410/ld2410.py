from __future__ import annotations

import asyncio
import copy
import functools
import logging
import sys
from asyncio import StreamReader, StreamWriter
from contextlib import AsyncExitStack, asynccontextmanager, suppress
from typing import TYPE_CHECKING, Any, Callable, ClassVar, TypeVar, cast

from construct import Container
from serial_asyncio_fast import open_serial_connection

from .exceptions import (
    CommandContextError,
    CommandParamError,
    CommandReplyError,
    CommandStatusError,
    ConnectionClosedError,
    ModuleRestartedError,
)
from .models import (
    ConfigModeStatus,
    FirmwareVersion,
    GateSensitivityConfig,
    LightControlConfig,
    LightControlStatus,
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
    FrameType,
    Reply,
    ReplyStatus,
    Report,
    ResolutionIndex,
)
from .stream import FrameStream

if sys.version_info >= (3, 11):  # pragma: no branch
    from asyncio import timeout
else:  # pragma: no cover
    from async_timeout import timeout  # type: ignore[import-not-found]

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Mapping
    from types import TracebackType

    from typing_extensions import Concatenate, ParamSpec, Self, TypeAlias, Unpack

    _ParamSpec = ParamSpec('_ParamSpec')
    _T = TypeVar('_T')

ConstructReply: TypeAlias = Container[Any]
logger = logging.getLogger(__package__)


def configuration(
    func: Callable[Concatenate[LD2410, _ParamSpec], Awaitable[_T]],
) -> Callable[Concatenate[LD2410, _ParamSpec], Awaitable[_T]]:
    """
    Decorate an async method so we can check for the configuration context.

    Raises:
        CommandContextError: When the configuration context is not entered.

    """
    if not asyncio.iscoroutinefunction(func):
        msg = '@configuration decorator is only suitable for async methods.'
        raise RuntimeError(msg)

    @functools.wraps(func)
    async def _check_config_context(
        self: LD2410,
        *args: _ParamSpec.args,
        **kwargs: _ParamSpec.kwargs,
    ) -> _T:
        if not self.configuring:
            msg = 'This method requires a configuration context'
            raise CommandContextError(msg)
        return await func(self, *args, **kwargs)

    return _check_config_context


class LD2410:
    """Client of the LD2410 sensor."""

    DEFAULT_COMMAND_TIMEOUT: ClassVar[float] = 2.0
    DEFAULT_BAUD_RATE: ClassVar[int] = 256000

    def __init__(
        self,
        device: str,
        *,
        baud_rate: int = DEFAULT_BAUD_RATE,
        command_timeout: float | None = DEFAULT_COMMAND_TIMEOUT,
        read_bufsize: int | None = None,
    ) -> None:
        """
        Create a new async client for the provided LD2410 device.

        Important:
            The command timeout affects all command requests when enabled.
            If the device doesn't reply within this period, an ``asyncio.TimoutError``
            is raised (which is equivalent to a :exc:`TimeoutError`) on Python 3.10+.

        Args:
            device: path to the device to use.
            baud_rate: serial baud rate to use.
            command_timeout: how long to wait for a command reply (in seconds),
                :obj:`None` to disable.
            read_bufsize: max buffer size used by the underlying :class:`asyncio.StreamReader`.

        """
        self._baud_rate = baud_rate
        self._command_timeout = command_timeout
        self._device = device
        self._config_lock = asyncio.Lock()
        self._read_bufsize = read_bufsize
        self._report = None  # type: ReportStatus | None
        self._report_condition = asyncio.Condition()
        self._request_lock = asyncio.Lock()
        self._connected = False
        self._context = None  # type: AsyncExitStack | None
        self._replies = None  # type: asyncio.Queue[ConstructReply | None] | None
        self._restarted = False
        self._rdtask = None  # type: asyncio.Task[None] | None
        self._writer = None  # type: StreamWriter | None

    @property
    def configuring(self) -> bool:
        """Tell whether a configuration context is currently entered."""
        return bool(not self._restarted and self._config_lock.locked())

    @property
    def connected(self) -> bool:
        """Tell whether we are still connected and receiving data frames."""
        return bool(self._connected and self._writer is not None and self._replies is not None)

    @property
    def entered(self) -> bool:
        """Tell whether the device's context manager is entered."""
        return bool(self._context is not None)

    async def __aenter__(self) -> Self:
        """
        Enter the device's context, open the device.

        This initializes the serial link and creates the reader :class:`asyncio.Task`.

        This method, along with :meth:`__aexit__` are called with the following syntax::

            async with LD2410('/dev/ttyUSB0'):
                pass

        Raises:
            RuntimeError: when the device is already in use (:attr:`entered`).

        Returns:
            The exact same :class:`LD2410` object.

        """
        if self.entered:
            msg = "LD2410's instance is already entered!"
            raise RuntimeError(msg)
        context = await AsyncExitStack().__aenter__()
        try:
            reader, writer = await self._open_serial_connection()
            context.push_async_callback(writer.wait_closed)
            context.callback(writer.close)

            replies = asyncio.Queue()  # type: asyncio.Queue[ConstructReply | None]
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
        """
        Exit the device's context and close the serial link.

        The reader task is also canceled.

        Returns:
            :obj:`False` to let any exception flow through the call stack.

        """
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
        # This cannot be tested and is superseded during tests.
        return await open_serial_connection(
            baudrate=self._baud_rate,
            limit=self._read_bufsize,
            url=self._device,
        )  # pragma: no cover

    async def _reader_task(
        self,
        reader: StreamReader,
        replies: asyncio.Queue[ConstructReply | None],
    ) -> None:
        stream = FrameStream()
        try:
            while chunk := await reader.read(2048):
                stream.push(chunk)
                for frame in stream:
                    try:
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
                        # For the user perspective this will most likely ends with a timeout.
                        logger.exception('Unable to handle frame: %s', frame.data.hex(' '))
        finally:
            self._connected = False
            # This is needed here because we may be stuck waiting on a reply.
            with suppress(asyncio.QueueFull):
                replies.put_nowait(None)

    async def _request(
        self,
        code: CommandCode,
        args: Mapping[str, Any] | None = None,
    ) -> ConstructReply:
        """
        Send any kind of command to the device.

        This method waits until the reply arrives (or a timeout occurs).

        Args:
            code: command opcode
            args: a map of arguments or :obj:`None`

        Returns:
            The reply container from construct.

        """
        command = Command.build({'code': code, 'data': args})
        async with self._request_lock:
            if not self.connected:
                msg = 'We are not connected to the device anymore!'
                raise ConnectionClosedError(msg)

            async with timeout(self._command_timeout):
                frame = CommandFrame.build({'data': command})
                # Casts are valid here since we just checked `self.connected`.
                replies = cast('asyncio.Queue[ConstructReply | None]', self._replies)
                writer = cast('StreamWriter', self._writer)

                writer.write(frame)
                await writer.drain()

                # Loop until we get our reply.
                valid_reply = False
                while not valid_reply:
                    reply = await replies.get()
                    replies.task_done()
                    if reply is None:
                        msg = 'Device has disconnected'
                        raise ConnectionClosedError(msg)

                    valid_reply = bool(code == int(reply.code))
                    if not valid_reply:
                        logger.warning('Got reply code %u (request was %u)', reply.code, code)

        # MyPy does not see that reply cannot be None on here.
        reply = cast('ConstructReply', reply)
        if int(reply.status) != ReplyStatus.SUCCESS:
            msg = f'Command {code} received bad status: {reply.status}'
            raise CommandStatusError(msg)

        return reply

    @asynccontextmanager
    async def configure(self) -> AsyncIterator[ConfigModeStatus]:
        """
        Enter the configuration mode.

        As stated on the LD2410 documentation, no reports are generated when the configuration
        mode is active but the device now accepts configuration commands.

        Notes:
            - This context is protected with an :class:`asyncio.Lock`.
            - This context absorbs :exc:`.ModuleRestartedError` (see :meth:`restart_module`)

        USE EXAMPLE::

            async with LD2410('/dev/ttyUSB0') as dev:
                async with dev.configure():
                    # Some configuration commands

        Yields:
            Device's protocol information.

            This is the standard reply for command :attr:`~.CommandCode.CONFIG_ENABLE`.

            You most likely don't need this returned value.

        Returns:
            An asynchronous iterator (seel YIELDS).

        """
        async with self._config_lock:
            resp = await self._request(CommandCode.CONFIG_ENABLE)
            try:
                yield container_to_model(ConfigModeStatus, resp.data)
            except ModuleRestartedError:
                logger.info('Configuration context has closed due to module restart.')
            finally:
                if not self._restarted and self.connected:
                    await self._request(CommandCode.CONFIG_DISABLE)
                self._restarted = False

    @configuration
    async def get_bluetooth_address(self) -> bytes:
        """
        Get the device's bluetooth mac address.

        USE EXAMPLE::

            async with LD2410('/dev/ttyUSB0') as dev:
                async with dev.configure():
                    addr = await dev.get_bluetooth_address()

                print('MAC address:', addr.hex(':'))

        Returns:
            The MAC address in 6 :class:`bytes`.

        """
        resp = await self._request(CommandCode.BLUETOOTH_MAC_GET)
        return bytes(resp.data.address)

    @configuration
    async def get_distance_resolution(self) -> int:
        """
        Get the gate distance resolution (in centimeter).

        Caution:
            This command may not be available on your variant or with your firmware.

        See Also:
            The internal :class:`.ResolutionIndex` for a list of available resolutions.

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandReplyError: when the device returns an unknown resolution index.
            CommandStatusError: when the device replies with a failed status.

        Returns:
            The distance resolution in centimeters.

        """
        resp = await self._request(CommandCode.DISTANCE_RESOLUTION_GET)
        index = int(resp.data.resolution)
        if index == ResolutionIndex.RESOLUTION_20CM:
            return 20
        if index == ResolutionIndex.RESOLUTION_75CM:
            return 75
        msg = f'Unhandled distance resolution index {index}'
        raise CommandReplyError(msg)

    @configuration
    async def get_firmware_version(self) -> FirmwareVersion:
        """
        Get the device's firmware version.

        USE EXAMPLE::

            async with LD2410('/dev/ttyUSB0') as device:
                async with device.configure():
                    ver = await device.get_firmware_version()
                    print(f'[+] Running with firmware v{ver}')

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandStatusError: when the device replies with a failed status.

        Returns:
            The firmware version structure.

        """
        resp = await self._request(CommandCode.FIRMWARE_VERSION)
        return container_to_model(FirmwareVersion, resp.data)

    def get_last_report(self) -> ReportStatus | None:
        """
        Get the latest report received from the device, if any.

        Note:
            This report can be very outdated if you spent too much time in configuration mode.

        Tip:
            This method does not way for anything and it not asynchronous.

        Returns:
            The last report we received from the device.

        """
        return copy.deepcopy(self._report)

    @configuration
    async def get_light_control(self) -> LightControlStatus:
        """
        Get the light controls parameters for ``OUT`` pin.

        This gets the specific configuration used to control the ``OUT`` pin status
        with the integrated photo sensor.

        Caution:
            This command may not be available on your variant or with your firmware.

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandStatusError: when the device replies with a failed status.

        Returns:
            The status of the light configuration.

        """
        resp = await self._request(CommandCode.LIGHT_CONTROL_GET)
        return container_to_model(LightControlStatus, resp.data)

    async def get_next_report(self) -> ReportStatus:
        """
        Wait and get the next available report.

        Caution:
            Must be called outside of the configuration context as no report is being
            generated in configuration mode.

        Returns:
            The next report we just received from the device (if any).

        """
        async with self._report_condition:
            await self._report_condition.wait()
            report = cast('ReportStatus', self._report)
        return copy.deepcopy(report)

    @configuration
    async def get_parameters(self) -> ParametersStatus:
        """
        Get the standard configuration parameters.

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandStatusError: when the device replies with a failed status.

        Returns:
            The currently applied standard parameters.

        """
        resp = await self._request(CommandCode.PARAMETERS_READ)
        return container_to_model(ParametersStatus, resp.data)

    async def get_reports(self) -> AsyncIterator[ReportStatus]:
        """
        Get reports as they arrive with an asynchronous iterator.

        This is just a simple loop around :meth:`get_next_report`.

        Caution:
            Must be called outside of the configuration context as no report is being
            generated in configuration mode.

        Yields:
            An asynchronous iterator for :class:`.ReportStatus`.

        Returns:
            An asynchronous iterator (seel YIELDS).

        """
        while True:
            yield await self.get_next_report()

    @configuration
    async def reset_to_factory(self) -> None:
        """
        Reset the device to its factory settings.

        Tell the device to reset all its parameters to factory settings.


        Important:
            This command requires a module restart to be effective!

        Hint:
            In factory settings, you get the following parameters:

            ============================= ==============
            Max moving distance gate              8
            Max static distance gate              8
            No-one duration                       5 sec
            Serial port baud rate            256000 Hz
            Bluetooth mode                  enabled
            Bluetooth password               HiLink
            Distance resolution                  75 cm
            Light control                  disabled
            Light threshold                     128
            Light default                       LOW
            ============================= ==============

            ====== ================== ===================
             Gate   Moving threshold    Static threshold
            ====== ================== ===================
                 0                50%                 N/A
                 1                50%                 N/A
                 2                40%                 40%
                 3                30%                 40%
                 4                20%                 30%
                 5                15%                 30%
                 6                15%                 20%
                 7                15%                 20%
                 8                15%                 20%
            ====== ================== ===================

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandStatusError: when the device replies with a failed status.

        """
        await self._request(CommandCode.FACTORY_RESET)

    @configuration
    async def restart_module(self, *, close_config_context: bool = False) -> None:
        """
        Restart the module immediately.

        On my tests it takes at least 1100ms for the module to be responsive again.

        Important:
            If you chose close the current configuration context using ``close_config_context``
            you will have to exit the context by yourself before you can issue new commands.

        Keyword Args:
            close_config_context: close the surrounding configuration context by raising a
                :exc:`.ModuleRestartedError` (see :meth:`configure`).

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandStatusError: when the device replies with a failed status.
            ModuleRestartedError: when ``close_config_context`` is True (do not catch it).

        """
        await self._request(CommandCode.MODULE_RESTART)

        self._restarted = True

        if close_config_context:
            msg = "Module is being restarted from user's request."
            raise ModuleRestartedError(msg)

    @configuration
    async def set_baud_rate(self, baud_rate: int) -> None:
        """
        Set the serial port baud rate.

        Important:
            This command requires a module restart to be effective!

        Args:
            baud_rate: the baud rate you want to apply (see :class:`.BaudRateIndex`).

        See Also:
            The internal :class:`.BaudRateIndex` for a list of available baud rates.

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandParamError: when the provided baud rate is not suitable.
            CommandStatusError: when the device replies with a failed status.

        """
        try:
            index = BaudRateIndex.from_integer(baud_rate)
        except KeyError:
            msg = f'Unknown index for baud rate {baud_rate}'
            raise CommandParamError(msg) from None

        await self._request(CommandCode.BAUD_RATE_SET, {'index': int(index)})

    @configuration
    async def set_bluetooth_mode(self, enabled: bool) -> None:
        """
        Enable of disable bluetooth mode.

        Important:
            This command requires a module restart to be effective!

        Args:
            enabled: whether bluetooth should be enabled on the device.

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandStatusError: when the device replies with a failed status.

        """
        await self._request(CommandCode.BLUETOOTH_SET, {'enabled': enabled})

    @configuration
    async def set_bluetooth_password(self, password: str) -> None:
        """
        Set the device's bluetooth password.

        Caution:
            This command may not be available on your variant or with your firmware.

        Args:
            password: must have less than 7 ASCII characters.

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandParamError: when the password is not ASCII or has more than 6 chars.
            CommandStatusError: when the device replies with a failed status.

        """
        if len(password) > 6 or not password.isascii():
            msg = 'Bluetooth password must have less than 7 ASCII characters.'
            raise CommandParamError(msg)
        await self._request(CommandCode.BLUETOOTH_PASSWORD_SET, {'password': password})

    @configuration
    async def set_distance_resolution(self, resolution: int) -> None:
        """
        Set the gate distance resolution (in centimeter).

        Important:
            This command requires a module restart to be effective!

        Caution:
            This command seems to be available for a few devices / firmwares.

        Args:
            resolution: per-gate distance (the only valid values are 20 and 75 cm).

        See Also:
            The internal :class:`.ResolutionIndex` for a list of available resolutions.

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandParamError: when the provided resolution is not suitable.
            CommandStatusError: when the device replies with a failed status.

        """
        index = ResolutionIndex.RESOLUTION_75CM
        if resolution == 20:
            index = ResolutionIndex.RESOLUTION_20CM
        elif resolution != 75:
            msg = f'Unknown index for distance resolution {resolution}'
            raise CommandParamError(msg)
        await self._request(CommandCode.DISTANCE_RESOLUTION_SET, {'resolution': index})

    @configuration
    async def set_engineering_mode(self, enabled: bool) -> None:
        """
        Enable or disable engineering reports.

        Caution:
            The engineering mode is lost after a device restart.

        Args:
            enabled: whether :class:`.ReportStatus` should contain an advanced report.

        See Also:
            - :class:`.ReportStatus` for the complete description of reports.
            - :class:`.ReportEngineeringStatus` for the engineering part.

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandStatusError: when the device replies with a failed status.

        """
        code = CommandCode.ENGINEERING_ENABLE if enabled else CommandCode.ENGINEERING_DISABLE
        await self._request(code)

    @configuration
    async def set_light_control(self, **kwargs: Unpack[LightControlConfig]) -> None:
        """
        Set the light controls parameters for ``OUT`` pin.

        This sets the specific configuration used to control the ``OUT`` pin status
        with the integrated photo sensor.


        Caution:
            This command may not be available on your variant or with your firmware.

        Hint:
            See :class:`.LightControlConfig` for keyword arguments.

        USE EXAMPLE::

            async with LD2410('/dev/ttyUSB0') as dev:
                async with dev.configure():
                    await dev.set_light_control(
                        control=LightControl.BELOW,
                        default=OutPinLevel.LOW,
                        threshold=120,
                    )


        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandParamError: when a mandatory keyword argument is missing.
            CommandStatusError: when the device replies with a failed status.

        """
        data = LightControlConfig(**kwargs)
        missing = LightControlConfig.__required_keys__.difference(data.keys())
        if missing:
            msg = f'Missing parameters: {set(missing)}'
            raise CommandParamError(msg)
        await self._request(CommandCode.LIGHT_CONTROL_SET, data)

    @configuration
    async def set_parameters(self, **kwargs: Unpack[ParametersConfig]) -> None:
        """
        Set the standard configuration parameters.

        This method only sets basic configuration parameters.


        Hint:
            See :class:`.ParametersConfig` for keyword arguments.

        Tip:
            These parameters apply immediately and are persistent across module restart.

        USE EXAMPLE::

            async with LD2410('/dev/ttyUSB0') as dev:
                async with dev.configure():
                    await dev.set_parameters(
                        moving_max_distance_gate=7,
                        static_max_distance_gate=7,
                        presence_timeout=5,
                    )


        See Also:
            :meth:`set_gate_sensitivity` to set additional parameters.

        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandParamError: when a mandatory keyword argument is missing.
            CommandStatusError: when the device replies with a failed status.

        """
        data = ParametersConfig(**kwargs)
        missing = ParametersConfig.__required_keys__.difference(data.keys())
        if missing:
            msg = f'Missing parameters: {set(missing)}'
            raise CommandParamError(msg)
        await self._request(CommandCode.PARAMETERS_WRITE, data)

    @configuration
    async def set_gate_sensitivity(self, **kwargs: Unpack[GateSensitivityConfig]) -> None:
        """
        Set gate sensitivities.

        This command is used to configure gate sensitivity to one or to all gate.


        Hint:
            See :class:`.GateSensitivityConfig` for keyword arguments.

        Tip:
            - These parameters apply immediately and are persistent across module restart.
            - ``distance_gate`` keyword argument can be set to ``0xFFFF`` to broadcast
              to all gates.

        USE EXAMPLE::

            async with LD2410('/dev/ttyUSB0') as dev:
                async with dev.configure():
                    # Set sensitivities for gate 4.
                    await dev.set_gate_sensitivity(
                        distance_gate=4,
                        moving_threshold=25,
                        static_threshold=20,
                    )


        Raises:
            CommandContextError: when called outside of the configuration context.
            CommandParamError: when a mandatory keyword argument is missing.
            CommandStatusError: when the device replies with a failed status.

        """
        data = GateSensitivityConfig(**kwargs)
        missing = GateSensitivityConfig.__required_keys__.difference(data.keys())
        if missing:
            msg = f'Missing parameters: {set(missing)}'
            raise CommandParamError(msg)
        await self._request(CommandCode.GATE_SENSITIVITY_SET, data)
