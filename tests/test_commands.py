import pytest

from aio_ld2410 import Command, CommandCode, CommandFrame

_TRACES = {
    CommandCode.PARAMETERS_WRITE: (
        'fd fc fb fa 14 00 60 00 00 00 08 00 00 00 01'
        '00 08 00 00 00 02 00 05 00 00 00 04 03 02 01'
    ),
    CommandCode.PARAMETERS_READ: 'fd fc fb fa 02 00 61 00 04 03 02 01',
    CommandCode.ENGINEERING_ENABLE: 'fd fc fb fa 02 00 62 00 04 03 02 01',
    CommandCode.ENGINEERING_DISABLE: 'fd fc fb fa 02 00 63 00 04 03 02 01',
    CommandCode.GATE_SENSITIVITY_SET: (
        'fd fc fb fa 14 00 64 00 00 00 03 00 00 00 01'
        '00 28 00 00 00 02 00 28 00 00 00 04 03 02 01'
    ),
    CommandCode.FIRMWARE_VERSION: 'fd fc fb fa 02 00 a0 00 04 03 02 01',
    CommandCode.BAUD_RATE_SET: 'fd fc fb fa 04 00 a1 00 07 00 04 03 02 01',
    CommandCode.FACTORY_RESET: 'fd fc fb fa 02 00 a2 00 04 03 02 01',
    CommandCode.MODULE_RESTART: 'fd fc fb fa 02 00 a3 00 04 03 02 01',
    CommandCode.BLUETOOTH_SET: 'fd fc fb fa 04 00 a4 00 01 00 04 03 02 01',
    CommandCode.BLUETOOTH_MAC_GET: 'fd fc fb fa 04 00 a5 00 01 00 04 03 02 01',
    CommandCode.BLUETOOTH_AUTHENTICATE: (
        'fd fc fb fa 08 00 a8 00 48 69 4c 69 6e 6b 04 03 02 01'
    ),
    CommandCode.BLUETOOTH_PASSWORD_SET: (
        'fd fc fb fa 08 00 a9 00 48 69 4c 69 6e 6b 04 03 02 01'
    ),
    CommandCode.DISTANCE_RESOLUTION_SET: 'fd fc fb fa 04 00 aa 00 01 00 04 03 02 01',
    CommandCode.DISTANCE_RESOLUTION_GET: 'fd fc fb fa 02 00 ab 00 04 03 02 01',
    CommandCode.CONFIG_ENABLE: 'fd fc fb fa 04 00 ff 00 01 00 04 03 02 01',
    CommandCode.CONFIG_DISABLE: 'fd fc fb fa 02 00 fe 00 04 03 02 01',
}


@pytest.mark.parametrize(('code', 'trace'), _TRACES.items())
def test_good_commands(code, trace):
    raw = bytes.fromhex(trace)

    # Check frame parsing.
    frame = CommandFrame.parse(raw)
    command = Command.parse(frame.data)
    assert int(command.code) == code

    # Rebuild the command and check it.
    command_rebuild = Command.build(command)
    assert command_rebuild == frame.data

    # Rebuild the frame around the command and check it.
    frame_rebuild = CommandFrame.build({'data': command_rebuild})
    assert frame_rebuild == raw

    print(command)
