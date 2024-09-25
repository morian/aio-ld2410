from __future__ import annotations

import asyncio
import json
import logging
from asyncio import Event
from contextlib import AsyncExitStack
from dataclasses import asdict, is_dataclass
from random import randrange
from typing import TYPE_CHECKING, Any

import dacite

from aio_ld2410 import (
    AuxiliaryControl,
    BaudRateIndex,
    OutPinLevel,
    ReportBasicStatus,
    ReportEngineeringStatus,
    ReportStatus,
    TargetStatus,
)
from aio_ld2410.protocol import (
    Command,
    CommandCode,
    CommandFrame,
    Frame,
    FrameType,
    Reply,
    ReplyStatus,
    Report,
    ReportFrame,
    ReportType,
    ResolutionIndex,
)

from .models import DeviceStatus, EmulatorConfig

logger = logging.getLogger(__package__)


if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter
    from types import TracebackType

    from construct import Container, EnumIntegerString
    from typing_extensions import Self


def need_configuration_mode(func):
    """Decorate an async method so we can check for the configuration mode."""

    async def _check_configuration_mode(self, command: Container[Any]) -> bytes:
        if not self._status.configuring:
            return self._build_reply_error(command.code)
        return await func(self, command)

    return _check_configuration_mode


class DeviceEmulator:
    """Emulate a fake device for test purpose."""

    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        """Create a new emulated LD2410 device from a generic reader/writer."""
        self._closing = Event()
        self._context = None  # type: AsyncExitStack | None
        self._handlers = {
            CommandCode.BAUD_RATE_SET: self._cmd_baud_rate_set,
            CommandCode.CONFIG_DISABLE: self._cmd_config_disable,
            CommandCode.CONFIG_ENABLE: self._cmd_config_enable,
            CommandCode.ENGINEERING_DISABLE: self._cmd_engineering_disable,
            CommandCode.ENGINEERING_ENABLE: self._cmd_engineering_enable,
            CommandCode.FACTORY_RESET: self._cmd_factory_reset,
            CommandCode.MODULE_RESTART: self._cmd_module_restart,
            CommandCode.BLUETOOTH_MAC_GET: self._cmd_bluetooth_mac_get,
            CommandCode.BLUETOOTH_PASSWORD_SET: self._cmd_bluetooth_password_set,
            CommandCode.BLUETOOTH_SET: self._cmd_bluetooth_set,
            CommandCode.FIRMWARE_VERSION: self._cmd_firmware_version,
            CommandCode.DISTANCE_RESOLUTION_GET: self._cmd_distance_resolution_get,
            CommandCode.DISTANCE_RESOLUTION_SET: self._cmd_distance_resolution_set,
            CommandCode.GATE_SENSITIVITY_SET: self._cmd_gate_sensitivity_set,
            CommandCode.PARAMETERS_READ: self._cmd_parameters_read,
            CommandCode.PARAMETERS_WRITE: self._cmd_parameters_write,
            CommandCode.AUXILIARY_CONTROL_GET: self._cmd_auxiliary_control_get,
            CommandCode.AUXILIARY_CONTROL_SET: self._cmd_auxiliary_control_set,
        }
        self._status = DeviceStatus()
        self._reader = reader
        self._writer = writer
        self._write_lock = asyncio.Lock()

    def _build_reply(
        self,
        code: EnumIntegerString | int,
        *,
        data: Any = None,
        status: ReplyStatus = ReplyStatus.SUCCESS,
    ) -> bytes:
        """Build a reply to a command."""
        if is_dataclass(data):
            data = asdict(data)
        return Reply.build({'code': code, 'status': status, 'data': data})

    def _build_reply_error(self, code: EnumIntegerString | int) -> bytes:
        """Build a generic error reply."""
        return self._build_reply(code, status=ReplyStatus.FAILURE)

    def _build_report(self) -> ReportStatus:
        """Build a report with fully random values."""
        gate_range_cm = [75, 20][self._status.resolution]
        max_range_cm = gate_range_cm * (self._status.parameters.max_distance_gate + 1)
        target_status = TargetStatus(randrange(0, 4))
        basic = ReportBasicStatus(
            target_status=target_status,
            motion_distance=randrange(0, max_range_cm),
            motion_energy=randrange(0, 101),
            standstill_distance=randrange(0, max_range_cm),
            standstill_energy=randrange(0, 101),
            detection_distance=randrange(0, max_range_cm),
        )
        engineering = None
        if self._status.engineering_mode:
            params = self._status.parameters
            gate_range = params.max_distance_gate + 1
            engineering = ReportEngineeringStatus(
                motion_max_distance_gate=params.motion_max_distance_gate,
                standstill_max_distance_gate=params.standstill_max_distance_gate,
                motion_gate_energy=[randrange(0, 101) for _ in range(gate_range)],
                standstill_gate_energy=[randrange(0, 101) for _ in range(gate_range)],
                photosensitive_value=randrange(0, 256),
                out_pin_status=OutPinLevel(randrange(0, 2)),
            )
        return ReportStatus(basic=basic, engineering=engineering)

    async def _cmd_config_disable(self, command: Container[Any]) -> bytes:
        """Handle command CONFIG_DISABLE."""
        self._status.configuring = False
        return self._build_reply(command.code)

    async def _cmd_config_enable(self, command: Container[Any]) -> bytes:
        """Handle command CONFIG_ENABLE."""
        self._status.configuring = True
        return self._build_reply(command.code, data=self._status.config_mode)

    @need_configuration_mode
    async def _cmd_engineering_disable(self, command: Container[Any]) -> bytes:
        """Handle command ENGINEERING_DISABLE."""
        self._status.engineering_mode = False
        return self._build_reply(command.code)

    @need_configuration_mode
    async def _cmd_engineering_enable(self, command: Container[Any]) -> bytes:
        """Handle command ENGINEERING_ENABLE."""
        self._status.engineering_mode = True
        return self._build_reply(command.code)

    @need_configuration_mode
    async def _cmd_bluetooth_mac_get(self, command: Container[Any]) -> bytes:
        """Handle command BLUETOOTH_MAC_GET."""
        return self._build_reply(
            command.code, data={'address': self._status.bluetooth_address}
        )

    @need_configuration_mode
    async def _cmd_bluetooth_password_set(self, command: Container[Any]) -> bytes:
        """Handle command BLUETOOTH_PASSWORD_SET."""
        self._status.bluetooth_password = command.data.password
        return self._build_reply(command.code)

    @need_configuration_mode
    async def _cmd_bluetooth_set(self, command: Container[Any]) -> bytes:
        """Handle command BLUETOOTH_SET."""
        self._status.bluetooth_mode = bool(command.data.enabled)
        return self._build_reply(command.code)

    @need_configuration_mode
    async def _cmd_firmware_version(self, command: Container[Any]) -> bytes:
        """Handle command FIRMWARE_VERSION."""
        return self._build_reply(command.code, data=self._status.firmware_version)

    @need_configuration_mode
    async def _cmd_distance_resolution_get(self, command: Container[Any]) -> bytes:
        """Handle command DISTANCE_RESOLUTION_GET."""
        return self._build_reply(command.code, data={'resolution': self._status.resolution})

    @need_configuration_mode
    async def _cmd_distance_resolution_set(self, command: Container[Any]) -> bytes:
        """Handle command DISTANCE_RESOLUTION_SET."""
        self._status.resolution = ResolutionIndex(command.data.resolution.intvalue)
        return self._build_reply(command.code)

    @need_configuration_mode
    async def _cmd_factory_reset(self, command: Container[Any]) -> bytes:
        """Handle command FACTORY_RESET."""
        self._status.reset_to_factory()
        return self._build_reply(command.code)

    @need_configuration_mode
    async def _cmd_baud_rate_set(self, command: Container[Any]) -> bytes:
        """Handle command BAUD_RATE_SET."""
        self._status.baudrate = BaudRateIndex(command.data.index.intvalue)
        return self._build_reply(command.code)

    @need_configuration_mode
    async def _cmd_parameters_read(self, command: Container[Any]) -> bytes:
        """Handle command PARAMETERS_READ."""
        return self._build_reply(command.code, data=self._status.parameters)

    @need_configuration_mode
    async def _cmd_parameters_write(self, command: Container[Any]) -> bytes:
        """Handle command PARAMETERS_WRITE."""
        data = command.data
        params = self._status.parameters
        # Upper bits are discarded as observed on the real device.
        # It seems like the gate number can be set beyond the real gate....
        params.motion_max_distance_gate = data.motion_max_distance_gate & 0xFF
        params.standstill_max_distance_gate = data.standstill_max_distance_gate & 0xFF
        params.no_one_idle_duration = data.no_one_idle_duration & 0xFFFF
        return self._build_reply(command.code)

    @need_configuration_mode
    async def _cmd_gate_sensitivity_set(self, command: Container[Any]) -> bytes:
        """Handle command GATE_SENSITIVITY_SET."""
        data = command.data
        params = self._status.parameters

        # Upper bits are discarded as observed on the real device.
        index = data.distance_gate & 0xFFFF
        # 0xFFFF is a special value used to broadcast sensitivity to all gates.
        if index > params.max_distance_gate and index != 0xFFFF:
            return self._build_reply_error(command.code)

        indices = range(params.max_distance_gate + 1) if index == 0xFFFF else [index]
        for i in indices:
            params.motion_sensitivity[i] = data.motion_sensitivity & 0xFF
            params.standstill_sensitivity[i] = data.standstill_sensitivity & 0xFF
        return self._build_reply(command.code)

    @need_configuration_mode
    async def _cmd_module_restart(self, command: Container[Any]) -> bytes:
        """Handle command MODULE_RESTART."""
        self._status.configuring = False
        self._status.engineering_mode = False
        return self._build_reply(command.code)

    @need_configuration_mode
    async def _cmd_auxiliary_control_get(self, command: Container[Any]) -> bytes:
        """Handle command AUXILIARY_CONTROL_GET."""
        return self._build_reply(command.code, data=self._status.auxiliary)

    @need_configuration_mode
    async def _cmd_auxiliary_control_set(self, command: Container[Any]) -> bytes:
        """Handle command AUXILIARY_CONTROL_SET."""
        data = command.data
        aux = self._status.auxiliary
        aux.control = AuxiliaryControl(data.control.intvalue)
        aux.threshold = data.threshold & 0xFF
        aux.default = OutPinLevel(data.default.intvalue)
        return self._build_reply(command.code)

    async def _command_task(self) -> None:
        """Read and handle commands."""
        while chunk := await self._reader.read(2048):
            try:
                frame = Frame.parse(chunk)
                if frame.type == FrameType.COMMAND:
                    command = Command.parse(frame.data)
                    handler = self._handlers.get(command.code.intvalue)
                    if handler is not None:
                        reply_data = await handler(command)
                        reply_frame = CommandFrame.build({'data': reply_data})
                        async with self._write_lock:
                            self._writer.write(reply_frame)
                            await self._writer.drain()
                    else:
                        print(chunk.hex(' '))
                        print(command)
                # This is only used for test purpose to communicate extra test config.
                elif frame.type == FrameType.REPORT:
                    config = dacite.from_dict(
                        data_class=EmulatorConfig,
                        data=json.loads(frame.data),
                    )
                    print(config)
            except Exception:
                logger.exception('Unable to handle frame: %s', chunk.hex(' '))
        self._closing.set()

    async def _report_task(self) -> None:
        """Report tasks regularly."""
        while True:
            await asyncio.sleep(0.1)
            try:
                if not self._status.configuring:
                    report = self._build_report()
                    report_type = (
                        ReportType.BASIC
                        if report.engineering is None
                        else ReportType.ENGINEERING
                    )
                    report_data = Report.build({'type': report_type, 'data': asdict(report)})
                    report_frame = ReportFrame.build({'data': report_data})
                    async with self._write_lock:
                        self._writer.write(report_frame)
                        await self._writer.drain()
            except Exception:
                logger.exception('Unable to build report frame')

    async def __aenter__(self) -> Self:
        """Enter the device context."""
        # For now, stop the emulation as soon as possible.
        context = await AsyncExitStack().__aenter__()
        try:
            context.push_async_callback(self._writer.wait_closed)
            context.callback(self._writer.close)

            task_command = asyncio.create_task(
                self._command_task(),
                name='aio_ld2410.tests.emulator.command',
            )
            task_report = asyncio.create_task(
                self._report_task(),
                name='aio_ld2410.tests.emulator.report',
            )

            context.push_async_callback(
                asyncio.gather,
                task_command,
                task_report,
                return_exceptions=True,
            )
            context.callback(task_report.cancel)
            context.callback(task_command.cancel)
        except BaseException:
            await context.aclose()
            raise
        else:
            self._context = context
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
            self._context = None

        # Do not prevent the original exception from going further.
        return False

    async def wait_for_closing(self) -> None:
        """Wait until we are told to stop emulating the device."""
        await self._closing.wait()
