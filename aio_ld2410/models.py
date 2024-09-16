from enum import IntEnum

from construct import Const, Enum, Error, Int16ul, Pass, Rebuild, Struct, Switch, len_


class CommandCode(IntEnum):
    """List of available command OpCodes."""

    FIRMWARE_VERSION = 0xa0
    DISABLE_CONFIG = 0xfe
    ENABLE_CONFIG = 0xff


# According to the following documentations:
# LD2410C Serial communucation protocol v1.00
# HLK-LD2410 Serial Communication Protocol V1.02

FRAME_HEADER = b'\xfd\xfc\xfb\xfa'
FRAME_FOOTER = b'\x04\x03\x02\x01'

_CommandSwitch = Switch(
    lambda this: this.code,
    {
        CommandCode.FIRMWARE_VERSION.name: Pass,
        CommandCode.DISABLE_CONFIG.name: Pass,
        CommandCode.ENABLE_CONFIG.name: Struct('value' / Const(1, Int16ul)),
    },
    Error,
)


Command = Struct(
    'code' / Enum(Int16ul, CommandCode),
    'data' / _CommandSwitch,
)

CommandFrame = Struct(
    'header' / Const(FRAME_HEADER),
    'length' / Rebuild(Int16ul, len_(lambda this: this.command)),
    'command' / Command,
    'footer' / Const(FRAME_FOOTER),
)
