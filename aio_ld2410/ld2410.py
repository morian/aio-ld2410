from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, Any

from serial_asyncio_fast import open_serial_connection

from .command import Reply
from .frame import Frame, FrameType
from .report import Report

if TYPE_CHECKING:
    from types import TracebackType

    from construct import Container
    from typing_extensions import Self


logger = logging.getLogger(__package__)


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
        self._context = None  # type: AsyncExitStack | None
        self._replies = None  # type: asyncio.Queue[Container[Any]] | None
        self._rdtask = None  # type: asyncio.Task[None] | None
        self._writer = None  # type: asyncio.StreamWriter | None

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
            reader, writer = await open_serial_connection(
                baudrate=self._baudrate,
                limit=self._read_bufsize,
                url=self._device,
            )
            context.push_async_callback(writer.wait_closed)
            context.callback(writer.close)

            replies = asyncio.Queue()  # type: asyncio.Queue[Container[Any]]
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
            self._context = None
            self._replies = None
            self._rdtask = None
            self._writer = None

        # Do not prevent the original exception from going further.
        return False

    async def _reader_task(
        self,
        reader: asyncio.StreamReader,
        replies: asyncio.Queue[Container[Any]],
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
                        report = Report.parse(frame.data)
                        # await replies.put(report)
                        # TODO: find a way to provide these reports appropriately.
                        print(report)
                except Exception:
                    logger.exception('Unable to parse frame content')
                    print(chunk.hex(' '))
        finally:
            # TODO: so domething to clear everything and shut-down.
            pass
