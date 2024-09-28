from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from construct import (
    Array,
    Byte,
    Bytes,
    Const,
    Default,
    Enum,
    Error,
    FlagsEnum,
    Hex,
    If,
    Int16ub,
    Int16ul,
    Int32ul,
    PaddedString,
    Pass,
    Struct,
    Switch,
)

if TYPE_CHECKING:
    from typing_extensions import Self


class CommandCode(IntEnum):
    """List of known command OpCodes."""

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

    # The following commands are only available on some variants.
    BLUETOOTH_AUTHENTICATE = 0xA8
    BLUETOOTH_PASSWORD_SET = 0xA9
    DISTANCE_RESOLUTION_SET = 0xAA
    DISTANCE_RESOLUTION_GET = 0xAB

    # The following replies are available on FW v2.4 and later.
    # https://github.com/esphome/feature-requests/issues/2156#issuecomment-1472962509
    LIGHT_CONTROL_SET = 0xAD
    LIGHT_CONTROL_GET = 0xAE


class LightControl(IntEnum):
    """Configuration of the light control."""

    DISABLED = 0  #: The ``OUT`` pin will never be affected by photo-sensor
    BELOW = 1  #: The ``OUT`` pin is HIGH when value is under threshold.
    ABOVE = 2  #: The ``OUT`` pin is HIGH when value is above threshold.


class BaudRateIndex(IntEnum):
    """Configurable baud rates."""

    RATE_9600 = 0x01  #: Baud rate set to 9600Hz.
    RATE_19200 = 0x02  #: Baud rate set to 19200Hz.
    RATE_38400 = 0x03  #: Baud rate set to 38400Hz.
    RATE_57600 = 0x04  #: Baud rate set to 57600Hz.
    RATE_115200 = 0x05  #: Baud rate set to 115200Hz.
    RATE_230400 = 0x06  #: Baud rate set to 230400Hz.
    RATE_256000 = 0x07  #: Baud rate set to 256000Hz.
    RATE_460800 = 0x08  #: Baud rate set to 460800Hz.

    @classmethod
    def from_integer(cls, rate: int) -> Self:
        """
        Get the appropriate index from the provided baud rate.

        Args:
            rate: the baud rate as an :class:`int`.

        Raises:
            KeyError: when the provided rate is not configurable.

        """
        return cls[f'RATE_{rate}']


class OutPinLevel(IntEnum):
    """Tell the default status of the ``OUT`` pin."""

    LOW = 0
    HIGH = 1


class ReplyStatus(IntEnum):
    """Command ACK status."""

    SUCCESS = 0
    FAILURE = 1


class ResolutionIndex(IntEnum):
    """
    All possible gate resolution.

    The sensors divides the area in some fixed number of zones called ``gates`` (typically 9).
    Gates have a default resolution of 75 centimeters, but some models / firmwares allow for
    more precise resolutions.

    See Also:
        - :meth:`.LD2410.get_distance_resolution`
        - :meth:`.LD2410.set_distance_resolution`

    """

    RESOLUTION_75CM = 0x00  #: Each gate covers 75 centimeters.
    RESOLUTION_20CM = 0x01  #: Each gate covers 20 centimeters.


_CommandSwitch = Switch(
    lambda this: int(this.code),
    {
        # This following configuration is persistent and does not require a restart.
        CommandCode.PARAMETERS_WRITE: Struct(
            Const(0, Int16ul),  # Maximum moving distance gate word
            'moving_max_distance_gate' / Int32ul,  # Range 2-8 (gate)
            Const(1, Int16ul),  # Maximum static distance gate word
            'static_max_distance_gate' / Int32ul,  # Range 2-8 (gate)
            Const(2, Int16ul),  # No one duration
            'presence_timeout' / Int32ul,  # Range 0-65535 (seconds)
        ),
        CommandCode.PARAMETERS_READ: Pass,
        # The following configuration is lost on restart.
        CommandCode.ENGINEERING_ENABLE: Pass,
        CommandCode.ENGINEERING_DISABLE: Pass,
        # The following configuration is persistent and does not require a restart.
        CommandCode.GATE_SENSITIVITY_SET: Struct(
            Const(0, Int16ul),  # Distance gate word
            'distance_gate' / Int32ul,  # Range 1-8 or 0xFFFF for all gates
            Const(1, Int16ul),  # Moving sensitivity word
            'moving_threshold' / Int32ul,  # Range 0-100 (percent)
            Const(2, Int16ul),  # Static sensitivity word
            'static_threshold' / Int32ul,  # Range 0-100 (percent)
        ),
        CommandCode.FIRMWARE_VERSION: Pass,
        # The following configuration takes effect after module restart.
        CommandCode.BAUD_RATE_SET: Struct('index' / Enum(Int16ul, BaudRateIndex)),
        # The following configuration takes effect after module restart.
        CommandCode.FACTORY_RESET: Pass,
        CommandCode.MODULE_RESTART: Pass,
        # The following configuration takes effect after module restart.
        CommandCode.BLUETOOTH_SET: FlagsEnum(Int16ul, enabled=1),
        CommandCode.BLUETOOTH_MAC_GET: Struct('value' / Const(1, Int16ul)),
        CommandCode.CONFIG_DISABLE: Pass,
        # The following configuration is lost on restart.
        CommandCode.CONFIG_ENABLE: Struct('value' / Const(1, Int16ul)),
        ## The following commands are only available on LD2410C.
        # The following command is only available through bluetooth.
        CommandCode.BLUETOOTH_AUTHENTICATE: Struct(
            'password' / PaddedString(6, 'ascii'),
        ),
        CommandCode.BLUETOOTH_PASSWORD_SET: Struct('password' / PaddedString(6, 'ascii')),
        # The following configuration takes effect after module restart.
        CommandCode.DISTANCE_RESOLUTION_SET: Struct(
            'resolution' / Enum(Int16ul, ResolutionIndex),
        ),
        CommandCode.DISTANCE_RESOLUTION_GET: Pass,
        CommandCode.LIGHT_CONTROL_SET: Struct(
            'control' / Enum(Byte, LightControl),
            'threshold' / Byte,  # From 0 to 255
            'default' / Enum(Int16ul, OutPinLevel),
        ),
        CommandCode.LIGHT_CONTROL_GET: Pass,
    },
    Error,
)


Command = Struct(
    'code' / Enum(Byte, CommandCode),
    Const(0, Byte),
    'data' / _CommandSwitch,
)


_ReplySwitch = Switch(
    lambda this: int(this.code),
    {
        CommandCode.PARAMETERS_WRITE: Pass,
        CommandCode.PARAMETERS_READ: Struct(
            Const(0xAA, Byte),  # Header
            'max_distance_gate' / Byte,  # The farthest gate this chip can handle (0x08)
            'moving_max_distance_gate' / Byte,  # Configured max moving gate
            'static_max_distance_gate' / Byte,  # Configured max static gate
            'moving_threshold' / Array(9, Byte),  # percent
            'static_threshold' / Array(9, Byte),  # percent
            'presence_timeout' / Int16ul,  # Range 0-65535 (seconds)
        ),
        CommandCode.ENGINEERING_ENABLE: Pass,
        CommandCode.ENGINEERING_DISABLE: Pass,
        CommandCode.GATE_SENSITIVITY_SET: Pass,
        # Documentation says major = what we call here major.minor
        # Note that revision seems to always be displayed in hex.
        CommandCode.FIRMWARE_VERSION: Struct(
            'type' / Int16ub,
            'minor' / Byte,
            'major' / Byte,
            'revision' / Hex(Int32ul),
        ),
        CommandCode.BAUD_RATE_SET: Pass,
        CommandCode.FACTORY_RESET: Pass,
        CommandCode.MODULE_RESTART: Pass,
        CommandCode.BLUETOOTH_SET: Pass,
        CommandCode.BLUETOOTH_MAC_GET: Struct(
            'address' / Hex(Bytes(6)),
        ),
        CommandCode.CONFIG_DISABLE: Pass,
        CommandCode.CONFIG_ENABLE: Struct(
            'protocol_version' / Int16ul,
            'buffer_size' / Int16ul,
        ),
        ## The following replies can only be received on LD2410C.
        CommandCode.BLUETOOTH_AUTHENTICATE: Pass,
        CommandCode.BLUETOOTH_PASSWORD_SET: Pass,
        CommandCode.DISTANCE_RESOLUTION_SET: Pass,
        CommandCode.DISTANCE_RESOLUTION_GET: Struct(
            'resolution' / Enum(Int16ul, ResolutionIndex),
        ),
        # The following replies are available on FW v2.4 and later.
        # It seems to be related to the OUT pin behavior.
        CommandCode.LIGHT_CONTROL_SET: Pass,
        CommandCode.LIGHT_CONTROL_GET: Struct(
            'control' / Enum(Byte, LightControl),
            'threshold' / Byte,  # From 0 to 255
            'default' / Enum(Int16ul, OutPinLevel),
        ),
    },
    Error,
)

_ReplySwitchOrNone = If(
    lambda this: int(this.status) == ReplyStatus.SUCCESS,
    _ReplySwitch,
)


Reply = Struct(
    'code' / Enum(Byte, CommandCode),
    Const(1, Byte),
    # All commands have a status, therefore it is put in common here.
    'status' / Enum(Int16ul, ReplyStatus),
    # 'data' is only present when status is 0 (success).
    'data' / Default(_ReplySwitchOrNone, None),
)
