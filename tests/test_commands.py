import pytest

from aio_ld2410 import Command, CommandCode, CommandFrame


class Trace:
    FIRMWARE_VERSION = 'fd fc fb fa 02 00 a0 00 04 03 02 01'
    ENABLE_CONFIG = 'fd fc fb fa 04 00 ff 00 01 00 04 03 02 01'
    DISABLE_CONFIG = 'fd fc fb fa 02 00 fe 00 04 03 02 01'


@pytest.mark.parametrize(
    ('code', 'trace'),
    [
        (CommandCode.FIRMWARE_VERSION, Trace.FIRMWARE_VERSION),
        (CommandCode.DISABLE_CONFIG, Trace.DISABLE_CONFIG),
        (CommandCode.ENABLE_CONFIG, Trace.ENABLE_CONFIG),
    ],
)
def test_commands(code, trace):
    raw = bytes.fromhex(trace)
    frame = CommandFrame.parse(raw)
    assert int(frame.command.code) == code
    print(frame)
