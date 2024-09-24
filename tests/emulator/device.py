from __future__ import annotations

import asyncio
from asyncio import Event
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter
    from types import TracebackType

    from typing_extensions import Self


class DeviceEmulator:
    """Emulate a fake device for test purpose."""

    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        """Create a new emulated LD2410 device from a generic reader/writer."""
        self._closing = Event()
        self._context = None  # type: AsyncExitStack | None
        self._reader = reader
        self._writer = writer

    async def _command_task(self) -> None:
        """Read and handle commands."""
        # TODO: handle commands and push responses.
        while chunk := await self._reader.read(2048):
            print(chunk.hex(' '))
        self._closing.set()

    async def _report_task(self) -> None:
        """Report tasks regularly."""
        while True:  # noqa: ASYNC110
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
