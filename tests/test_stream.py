from __future__ import annotations

from aio_ld2410.protocol import CommandFrame
from aio_ld2410.stream import FrameStream


class TestFrameStream:
    def test_with_only_garbage(self):
        """Push garbage and check that we have no frame."""
        stream = FrameStream(b'This is garbage data')
        count = len(list(stream))
        assert count == 0

    def test_garbage_and_frame(self, caplog):
        """Push garbage and a real frame afterward."""
        junk = b'This is junk data'
        stream = FrameStream(junk)
        stream.push(CommandFrame.build({'data': b'STUFF'}))
        count = len(list(stream))
        assert count == 1
        assert len(caplog.records) == 1
        assert caplog.records[0].message.startswith(f'Skipping {len(junk)} garbage bytes:')

    def test_full_then_partial_frames(self):
        """Push a full frame and a partial one, check that it works."""
        frame = CommandFrame.build({'data': b'STUFF'})
        stream = FrameStream(frame + frame[:10])
        count = len(list(stream))
        assert count == 1

    def test_partial_then_complete_frame(self):
        """Push a partial frame, and complete it afterward."""
        frame = CommandFrame.build({'data': b'STUFF'})
        stream = FrameStream()

        stream.push(frame[:4])
        count = len(list(stream))
        assert count == 0

        stream.push(frame[4:])
        count = len(list(stream))
        assert count == 1

    def test_corrupted_footer_then_frame(self, caplog):
        frame = CommandFrame.build({'data': b'STUFF'})
        stream = FrameStream(frame[:-1] + frame)
        count = len(list(stream))
        assert count == 1
        assert len(caplog.records) == 2
        assert caplog.records[0].message.startswith('Skipping corrupted header:')
