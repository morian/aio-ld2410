from __future__ import annotations

import asyncio
import logging
from asyncio import Event
from contextlib import AsyncExitStack
from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, Any

from aio_ld2410.protocol import (
    BaudRateIndex,
    Command,
    CommandCode,
    CommandFrame,
    Reply,
    ReplyStatus,
    ResolutionIndex,
)

from .models import DeviceStatus

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
            return self._build_reply(command.code, ReplyStatus.FAILURE)
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
            CommandCode.BLUETOOTH_MAC_GET: self._cmd_bluetooth_mac_get,
            CommandCode.BLUETOOTH_PASSWORD_SET: self._cmd_bluetooth_password_set,
            CommandCode.BLUETOOTH_SET: self._cmd_bluetooth_set,
            CommandCode.FIRMWARE_VERSION: self._cmd_firmware_version,
            CommandCode.DISTANCE_RESOLUTION_GET: self._cmd_distance_resolution_get,
            CommandCode.DISTANCE_RESOLUTION_SET: self._cmd_distance_resolution_set,
        }
        self._status = DeviceStatus()
        self._reader = reader
        self._writer = writer

    def _build_reply(
        self,
        code: EnumIntegerString | int,
        status: ReplyStatus = ReplyStatus.SUCCESS,
        data: Any = None,
    ) -> bytes:
        """Build a reply to a command."""
        if is_dataclass(data):
            data = asdict(data)
        return Reply.build({'code': code, 'status': status, 'data': data})

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
        self._status.baudrate = BaudRateIndex.RATE_256000
        self._status.bluetooth_mode = True
        self._status.resolution = ResolutionIndex.RESOLUTION_75CM
        return self._build_reply(command.code)

    @need_configuration_mode
    async def _cmd_baud_rate_set(self, command: Container[Any]) -> bytes:
        """Handle command BAUD_RATE_SET."""
        self._status.baudrate = BaudRateIndex(command.data.index.intvalue)
        return self._build_reply(command.code)

    async def _command_task(self) -> None:
        """Read and handle commands."""
        while chunk := await self._reader.read(2048):
            try:
                frame = CommandFrame.parse(chunk)
                command = Command.parse(frame.data)
                handler = self._handlers.get(command.code.intvalue)
                if handler is not None:
                    reply_data = await handler(command)
                    reply_frame = CommandFrame.build({'data': reply_data})
                    self._writer.write(reply_frame)
                    await self._writer.drain()
                else:
                    print(chunk.hex(' '))
                    print(command)
            except Exception:
                logger.exception('Unable to handle frame: %s', chunk.hex(' '))
        self._closing.set()

    async def _report_task(self) -> None:
        """Report tasks regularly."""
        while True:
            if not self._status.configuring:
                pass
            await asyncio.sleep(0.5)

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
            context.push_callback(task_command.cancel)
            context.push_callback(task_report.cancel)
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

    async def wait_for_closing(self) -> None:
        """Wait until we are told to stop emulating the device."""
        await self._closing.wait()
