from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING, Any

from construct import Container, GreedyRange

from .protocol import FRAME_HEADER_COMMAND, FRAME_HEADER_REPORT, Frame, FrameHeader

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__package__)


class FrameStream(io.BytesIO):
    """A custom BytesIO subclass used to handle frames."""

    FRAME_MIN_SIZE: int = 10

    def append(self, data: bytes) -> int:
        """Append data to the end of the stream with no change to the current position."""
        pos = self.tell()
        self.seek(0, io.SEEK_END)
        try:
            count = self.write(data)
        finally:
            self.seek(pos, io.SEEK_SET)
        return count

    def read_frames(self) -> Iterator[Container[Any]]:
        """Iterate over full frames from the buffer (consumed)."""
        parsing = True

        while parsing:
            yield from GreedyRange(Frame).parse_stream(self)

            # Stop parsing when there is less than a frame left.
            remain = self.remaining_length()
            parsing = bool(remain >= self.FRAME_MIN_SIZE)
            if parsing:
                data = bytes(self.getbuffer()[-remain:])
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
                        self.seek(pos, io.SEEK_CUR)
                    else:
                        # We already have a header at offset 0.
                        hdr = FrameHeader.parse(data)
                        framelen = self.FRAME_MIN_SIZE + hdr.length
                        # Stop parsing if we have a partial frame.
                        parsing = bool(remain >= framelen)
                        if parsing:
                            # We have a header but some data may be corrupted.
                            logger.warning('Skipping corrupted header: %s', data[:4].hex(' '))
                            self.seek(4, io.SEEK_CUR)
                else:
                    # No header in sight, stop parsing.
                    parsing = False
            elif not remain:  # pragma: no branch
                # Discard processed bytes when nothing remaing.
                self.truncate()

    def remaining_length(self) -> int:
        """Tell how many bytes are left from the current position."""
        pos_cur = self.tell()
        self.seek(0, io.SEEK_END)
        pos_end = self.tell()
        self.seek(pos_cur, io.SEEK_SET)
        return pos_end - pos_cur
