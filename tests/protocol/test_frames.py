from __future__ import annotations

import pytest
from construct import ConstError

from aio_ld2410.protocol import Frame, FrameType


@pytest.mark.parametrize(
    ('expected', 'trace'),
    [
        (FrameType.COMMAND, 'fd fc fb fa 04 00 ff 00 01 00 04 03 02 01'),
        (FrameType.REPORT, 'f4 f3 f2 f1 04 00 ff 00 01 00 f8 f7 f6 f5'),
    ],
)
def test_frame_types(expected, trace):
    frame = Frame.parse(bytes.fromhex(trace))
    assert frame.type == expected


def test_bad_frame_header():
    trace = 'fd fc fc fa 02 00 fe 00 04 03 02 01'
    with pytest.raises(KeyError):
        Frame.parse(bytes.fromhex(trace))


@pytest.mark.parametrize(
    'trace',
    [
        'fd fc fb fa 02 00 fe 00 04 04 02 01',
        'fd fc fb fa 02 00 fe 00 f8 f7 f6 f5',
    ],
)
def test_bad_frame_footer(trace):
    with pytest.raises(ConstError):
        Frame.parse(bytes.fromhex(trace))
