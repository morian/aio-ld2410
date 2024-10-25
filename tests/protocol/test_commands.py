from __future__ import annotations

import pytest

from aio_ld2410.protocol import BaudRateIndex, Command, CommandCode, CommandFrame, Reply

_COMMAND_TRACES = {
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
    CommandCode.LIGHT_CONTROL_SET: 'fd fc fb fa 06 00 ad 00 01 60 00 00 04 03 02 01',
    CommandCode.LIGHT_CONTROL_GET: 'fd fc fb fa 02 00 ae 00 04 03 02 01',
}

_REPLY_TRACES = {
    CommandCode.PARAMETERS_WRITE: 'fd fc fb fa 04 00 60 01 00 00 04 03 02 01',
    CommandCode.PARAMETERS_READ: (
        'fd fc fb fa 1c 00 61 01 00 00 aa 08 08 08 14 14'
        '14 14 14 14 14 14 14 19 19 19 19 19 19 19 19 19'
        '05 00 04 03 02 01'
    ),
    CommandCode.ENGINEERING_ENABLE: 'fd fc fb fa 04 00 62 01 00 00 04 03 02 01',
    CommandCode.ENGINEERING_DISABLE: 'fd fc fb fa 04 00 63 01 00 00 04 03 02 01',
    CommandCode.GATE_SENSITIVITY_SET: 'fd fc fb fa 04 00 64 01 00 00 04 03 02 01',
    CommandCode.FIRMWARE_VERSION: (
        'fd fc fb fa 0c 00 a0 01 00 00 00 00 02 01 16 24' '06 22 04 03 02 01'
    ),
    CommandCode.BAUD_RATE_SET: 'fd fc fb fa 04 00 a1 01 00 00 04 03 02 01',
    CommandCode.FACTORY_RESET: 'fd fc fb fa 04 00 a2 01 00 00 04 03 02 01',
    CommandCode.MODULE_RESTART: 'fd fc fb fa 04 00 a3 01 00 00 04 03 02 01',
    CommandCode.BLUETOOTH_SET: 'fd fc fb fa 04 00 a4 01 00 00 04 03 02 01',
    CommandCode.BLUETOOTH_MAC_GET: (
        'fd fc fb fa 0a 00 a5 01 00 00 8f 27 2e b8 0f 65 04 03 02 01'
    ),
    CommandCode.CONFIG_ENABLE: 'fd fc fb fa 08 00 ff 01 00 00 01 00 40 00 04 03 02 01',
    CommandCode.CONFIG_DISABLE: 'fd fc fb fa 04 00 fe 01 00 00 04 03 02 01',
    CommandCode.BLUETOOTH_AUTHENTICATE: 'fd fc fb fa 04 00 a8 01 00 00 04 03 02 01',
    CommandCode.BLUETOOTH_PASSWORD_SET: 'fd fc fb fa 04 00 a9 01 00 00 04 03 02 01',
    CommandCode.DISTANCE_RESOLUTION_SET: 'fd fc fb fa 04 00 aa 01 00 00 04 03 02 01',
    CommandCode.DISTANCE_RESOLUTION_GET: 'fd fc fb fa 06 00 ab 01 00 00 01 00 04 03 02 01',
    CommandCode.LIGHT_CONTROL_SET: 'fd fc fb fa 04 00 ad 01 00 00 04 03 02 01',
    CommandCode.LIGHT_CONTROL_GET: 'fd fc fb fa 08 00 ae 01 00 00 00 80 00 00 04 03 02 01',
}


def test_good_baud_rate():
    rate = BaudRateIndex.from_integer(256000)
    assert rate == BaudRateIndex.RATE_256000


def test_bad_baud_rate():
    with pytest.raises(KeyError):
        BaudRateIndex.from_integer(256001)


@pytest.mark.parametrize(('code', 'trace'), _COMMAND_TRACES.items())
def test_commands(code, trace):
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


@pytest.mark.parametrize(('code', 'trace'), _REPLY_TRACES.items())
def test_replies(code, trace):
    raw = bytes.fromhex(trace)

    frame = CommandFrame.parse(raw)
    reply = Reply.parse(frame.data)

    # Rebuild the command and check it.
    reply_rebuild = Reply.build(reply)
    assert reply_rebuild == frame.data

    # Rebuild the frame around the command and check it.
    frame_rebuild = CommandFrame.build({'data': reply_rebuild})
    assert frame_rebuild == raw
