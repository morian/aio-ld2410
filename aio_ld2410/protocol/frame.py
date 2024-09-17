from __future__ import annotations

from enum import IntEnum

from construct import Bytes, Computed, Const, Error, Int16ul, Rebuild, Struct, Switch, len_

_FRAME_HEADER_COMMAND = b'\xfd\xfc\xfb\xfa'
_FRAME_FOOTER_COMMAND = b'\x04\x03\x02\x01'
_FRAME_HEADER_REPORT = b'\xf4\xf3\xf2\xf1'
_FRAME_FOOTER_REPORT = b'\xf8\xf7\xf6\xf5'


class FrameType(IntEnum):
    """All possible frame types."""

    COMMAND = 1
    REPORT = 2


_FRAME_HEADER_TO_TYPE = {
    _FRAME_HEADER_COMMAND: FrameType.COMMAND,
    _FRAME_HEADER_REPORT: FrameType.REPORT,
}

CommandFrame = Struct(
    Const(_FRAME_HEADER_COMMAND),
    'length' / Rebuild(Int16ul, len_(lambda this: this.data)),
    'data' / Bytes(lambda this: this.length),
    Const(_FRAME_FOOTER_COMMAND),
)


ReportFrame = Struct(
    Const(_FRAME_HEADER_REPORT),
    'length' / Rebuild(Int16ul, len_(lambda this: this.data)),
    'data' / Bytes(lambda this: this.length),
    Const(_FRAME_FOOTER_REPORT),
)


_FrameFooterSwitch = Switch(
    lambda this: this.type,
    {
        FrameType.COMMAND: Const(_FRAME_FOOTER_COMMAND),
        FrameType.REPORT: Const(_FRAME_FOOTER_REPORT),
    },
    Error,
)

Frame = Struct(
    'header' / Bytes(4),
    # The following lambda is supposed to return nothing according to construct-typing.
    # Do note that this Computed field is also used as a header check.
    'type' / Computed(lambda this: _FRAME_HEADER_TO_TYPE[this.header]),  # type: ignore
    'length' / Rebuild(Int16ul, len_(lambda this: this.data)),
    'data' / Bytes(lambda this: this.length),
    'footer' / _FrameFooterSwitch,
)
