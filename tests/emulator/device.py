from __future__ import annotations

from asyncio import Event
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
        self._reader = reader
        self._writer = writer

    async def __aenter__(self) -> Self:
        """Enter the device context."""
        # For now, stop the emulation as soon as possible.
        self._closing.set()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Exit the device's context."""

    async def wait_for_closing(self) -> None:
        """Wait until we are told to stop emulating the device."""
        await self._closing.wait()
