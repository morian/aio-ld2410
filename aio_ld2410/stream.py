from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from construct import GreedyRange

from .protocol import FRAME_HEADER_COMMAND, FRAME_HEADER_REPORT, Frame, FrameHeader

if TYPE_CHECKING:
    from collections.abc import Iterator

    from construct import Container
    from typing_extensions import TypeAlias

    ConstructFrame: TypeAlias = Container[Any]

logger = logging.getLogger(__package__)


class FrameStream:
    """Utility class used to produce frames out :class:`bytes`."""

    FRAME_MIN_SIZE: ClassVar[int] = 10

    def __init__(self, initial_bytes: bytes = b'') -> None:
        """
        Create a new frame stream processor.

        Args:
            initial_bytes: initial bytes pushed to the internal buffer.

        """
        self._buffer = io.BytesIO(initial_bytes)

    def _get_remaining_length(self) -> int:
        """
        Tell how many bytes are left from the current position in the internal buffer.

        Returns:
            The current cursor position in the internal buffer.

        """
        pos_cur = self._buffer.tell()
        self._buffer.seek(0, io.SEEK_END)
        pos_end = self._buffer.tell()
        self._buffer.seek(pos_cur, io.SEEK_SET)
        return pos_end - pos_cur

    def push(self, data: bytes) -> int:
        """
        Push new received data to the stream.

        Args:
            data: additional :class:`bytes` to append.

        Returns:
            The number of bytes written to the internal buffer.

        """
        pos = self._buffer.tell()
        self._buffer.seek(0, io.SEEK_END)
        try:
            count = self._buffer.write(data)
        finally:
            self._buffer.seek(pos, io.SEEK_SET)
        return count

    def __iter__(self) -> Iterator[ConstructFrame]:
        """
        Iterate over full frames from the internal buffer.

        Yields:
            Frames received from the device.

        """
        parsing = True

        while parsing:
            yield from GreedyRange(Frame).parse_stream(self._buffer)

            # Stop parsing when there is less than a frame left.
            remain = self._get_remaining_length()
            parsing = bool(remain >= self.FRAME_MIN_SIZE)
            if parsing:
                data = bytes(self._buffer.getbuffer()[-remain:])
                positions = []
                for hdr_bytes in (FRAME_HEADER_COMMAND, FRAME_HEADER_REPORT):
                    pos = data.find(hdr_bytes)
                    if pos >= 0:
                        positions.append(pos)

                if positions:
                    pos = min(positions)
                    if pos > 0:
                        logger.warning(
                            'Skipping %u garbage bytes: %s',
                            pos,
                            data[:pos].hex(' '),
                        )
                        self._buffer.seek(pos, io.SEEK_CUR)
                    else:
                        # We already have a header at offset 0.
                        hdr = FrameHeader.parse(data)
                        framelen = self.FRAME_MIN_SIZE + hdr.length
                        # Stop parsing if we have a partial frame.
                        parsing = bool(remain >= framelen)
                        if parsing:
                            # We have a header but some data may be corrupted.
                            logger.warning('Skipping corrupted header: %s', data[:4].hex(' '))
                            self._buffer.seek(4, io.SEEK_CUR)
                else:
                    # No header in sight, stop parsing.
                    parsing = False
            elif not remain:
                # Discard processed bytes when nothing remains.
                self._buffer.truncate()
