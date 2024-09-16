from __future__ import annotations

from enum import IntEnum

from construct import (
    Const,
    Enum,
    Error,
    FlagsEnum,
    Int16ul,
    Int32ul,
    PaddedString,
    Pass,
    Struct,
    Switch,
)
from typing_extensions import Self


class CommandCode(IntEnum):
    """List of available command OpCodes."""

    PARAMETERS_WRITE = 0x60
    PARAMETERS_READ = 0x61
    ENGINEERING_ENABLE = 0x62
    ENGINEERING_DISABLE = 0x63
    GATE_SENSITIVITY_SET = 0x64
    FIRMWARE_VERSION = 0xA0
    BAUD_RATE_SET = 0xA1
    FACTORY_RESET = 0xA2
    MODULE_RESTART = 0xA3
    BLUETOOTH_SET = 0xA4
    BLUETOOTH_MAC_GET = 0xA5
    CONFIG_DISABLE = 0xFE
    CONFIG_ENABLE = 0xFF

    # The following commands are only available on LD2410C.
    BLUETOOTH_AUTHENTICATE = 0xA8
    BLUETOOTH_PASSWORD_SET = 0xA9
    DISTANCE_RESOLUTION_SET = 0xAA
    DISTANCE_RESOLUTION_GET = 0xAB


class BaudRateIndex(IntEnum):
    """List of available baud rates."""

    RATE_9600 = 0x01
    RATE_19200 = 0x02
    RATE_38400 = 0x03
    RATE_57600 = 0x04
    RATE_115200 = 0x05
    RATE_230400 = 0x06
    RATE_256000 = 0x07
    RATE_460800 = 0x08

    @classmethod
    def from_integer(cls, rate: int) -> Self:
        """Get the appropriate index from the provided baud rate.

        Raises a KeyError when the provided rate cannot be used.
        """
        return cls[f'RATE_{rate}']


class ResolutionIndex(IntEnum):
    """Set sensor resolution for LD2410C (gate length)."""

    RESOLUTION_20CM = 0x00
    RESOLUTION_75CM = 0x01


_CommandSwitch = Switch(
    lambda this: this.code,
    {
        # This following configuration is persistent and does not require a restart.
        CommandCode.PARAMETERS_WRITE.name: Struct(
            Const(0, Int16ul),  # Maximum motion distance gate word
            'motion_max_distance_gate' / Int32ul,  # Range 2-8 (gate)
            Const(1, Int16ul),  # Maximum standstill distance gate word
            'standstill_max_distance_gate' / Int32ul,  # Range 2-8 (gate)
            Const(2, Int16ul),  # No one duration
            'no_one_idle_duration' / Int32ul,  # Range 0-65535 (seconds)
        ),
        CommandCode.PARAMETERS_READ.name: Pass,
        # The following configuration is lost on restart.
        CommandCode.ENGINEERING_ENABLE.name: Pass,
        CommandCode.ENGINEERING_DISABLE.name: Pass,
        # The following configuration is persistent and does not require a restart.
        CommandCode.GATE_SENSITIVITY_SET.name: Struct(
            Const(0, Int16ul),  # Distance gate word
            'distance_gate' / Int32ul,  # Range 1-8 or 0xFFFF for all gates
            Const(1, Int16ul),  # Motion sensitivity word
            'motion_sensitivity' / Int32ul,  # Range 0-100 (percent)
            Const(2, Int16ul),  # Standstill sensitivity word
            'standstill_sensitivity' / Int32ul,  # Range 0-100 (percent)
        ),
        CommandCode.FIRMWARE_VERSION.name: Pass,
        # The following configuration takes effect after module restart.
        CommandCode.BAUD_RATE_SET.name: Struct('index' / Enum(Int16ul, BaudRateIndex)),
        # The following configuration takes effect after module restart.
        CommandCode.FACTORY_RESET.name: Pass,
        CommandCode.MODULE_RESTART.name: Pass,
        # The following configuration takes effect after module restart.
        CommandCode.BLUETOOTH_SET.name: FlagsEnum(Int16ul, enabled=1),
        CommandCode.BLUETOOTH_MAC_GET.name: Struct('value' / Const(1, Int16ul)),
        CommandCode.CONFIG_DISABLE.name: Pass,
        # The following configuration is lost on restart.
        CommandCode.CONFIG_ENABLE.name: Struct('value' / Const(1, Int16ul)),
        ## The following commands are only available on LD2410C.
        # The following command is only available through bluetooth.
        CommandCode.BLUETOOTH_AUTHENTICATE.name: Struct(
            'password' / PaddedString(6, 'ascii'),
        ),
        CommandCode.BLUETOOTH_PASSWORD_SET.name: Struct('password' / PaddedString(6, 'ascii')),
        # The following configuration takes effect after module restart.
        CommandCode.DISTANCE_RESOLUTION_SET.name: Struct(
            'resolution' / Enum(Int16ul, ResolutionIndex),
        ),
        CommandCode.DISTANCE_RESOLUTION_GET.name: Pass,
    },
    Error,
)


Command = Struct(
    'code' / Enum(Int16ul, CommandCode),
    'data' / _CommandSwitch,
)
