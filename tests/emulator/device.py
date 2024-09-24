from __future__ import annotations

import asyncio
import logging
from asyncio import Event
from contextlib import AsyncExitStack
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from aio_ld2410.protocol import Command, CommandCode, CommandFrame, Reply, ReplyStatus

from .models import DeviceStatus

logger = logging.getLogger(__package__)


if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter
    from types import TracebackType

    from construct import Container
    from typing_extensions import Self


class DeviceEmulator:
    """Emulate a fake device for test purpose."""

    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        """Create a new emulated LD2410 device from a generic reader/writer."""
        self._closing = Event()
        self._context = None  # type: AsyncExitStack | None
        self._handlers = {
            CommandCode.CONFIG_DISABLE: self._cmd_config_disable,
            CommandCode.CONFIG_ENABLE: self._cmd_config_enable,
        }
        self._status = DeviceStatus()
        self._reader = reader
        self._writer = writer

    async def _cmd_config_disable(self, command: Container[Any]) -> bytes:
        """Handle the CONFIG_DISABLE command."""
        self._status.configuring = False
        return Reply.build(
            {
                'code': command.code,
                'status': ReplyStatus.SUCCESS,
            }
        )

    async def _cmd_config_enable(self, command: Container[Any]) -> bytes:
        """Handle the CONFIG_ENABLE command."""
        self._status.configuring = True
        return Reply.build(
            {
                'code': command.code,
                'status': ReplyStatus.SUCCESS,
                'data': asdict(self._status.config_mode),
            }
        )

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
