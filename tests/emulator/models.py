from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Any

from aio_ld2410 import (
    ConfigModeStatus,
    FirmwareVersion,
    LightControl,
    LightControlStatus,
    OutPinLevel,
    ParametersStatus,
)
from aio_ld2410.protocol import BaudRateIndex, ResolutionIndex

_DefaultConfigModeStatus = ConfigModeStatus(
    buffer_size=64,
    protocol_version=1,
)
_DefaultBluetoothAddress = bytes.fromhex('8f272eb80f65')
_DefaultBluetoothPassword = 'HiLink'
_DefaultFirmwareVersion = FirmwareVersion(
    type=0,
    major=1,
    minor=2,
    revision=0x22062416,
)
_DefaultParameters = ParametersStatus(
    max_distance_gate=8,
    moving_max_distance_gate=8,
    moving_threshold=[50, 50, 40, 30, 20, 15, 15, 15, 15],
    static_max_distance_gate=8,
    static_threshold=[0, 0, 40, 40, 30, 30, 20, 20, 20],
    presence_timeout=5,
)
_DefaultLight = LightControlStatus(
    control=LightControl.DISABLED,
    threshold=128,
    default=OutPinLevel.LOW,
)


class EmulatorCode(IntEnum):
    """
    Emulator-specific commands codes.

    These are used to control the behavior of the emulator through
    a REPORT frame sent from the client to the fake device.

    """

    #: Tell the emulator to disconnect immediately.
    DISCONNECT_NOW = auto()

    #: Tell the emulator to disconnect after the next command is received.
    DISCONNECT_AFTER_COMMAND = auto()

    #: Generate and push a corrupted frame immediately.
    GENERATE_CORRUPTED_FRAME = auto()

    #: Generate and push a corrupted reply frame.
    GENERATE_CORRUPTED_COMMAND = auto()

    #: Generate and push an unsolicited reply frame immediately.
    GENERATE_SPURIOUS_REPLY = auto()

    #: The next DISTANCE_RESOLUTION_GET command will receive an invalid resolution index.
    RETURN_INVALID_RESOLUTION = auto()


@dataclass
class EmulatorCommand:
    """
    Emulator-specific commands.

    These are used to control the behavior of the emulator through a REPORT
    frame sent from the client to the fake device. ``data`` is currently
    unused because no emulator require additional data.

    """

    #: Command core sent to the emulator.
    code: EmulatorCode

    #: Additional parameters for the command code (unused for now).
    data: Mapping[str, Any] | None = None


@dataclass
class DeviceStatus:
    """Internal state of the emulated device."""

    baud_rate: BaudRateIndex = BaudRateIndex.RATE_256000
    configuring: bool = False
    config_mode: ConfigModeStatus = _DefaultConfigModeStatus
    engineering_mode: bool = False
    bluetooth_mode: bool = True
    bluetooth_address: bytes = _DefaultBluetoothAddress
    bluetooth_password: str = _DefaultBluetoothPassword
    firmware_version: FirmwareVersion = _DefaultFirmwareVersion
    parameters: ParametersStatus = field(
        default_factory=lambda: copy.deepcopy(_DefaultParameters)
    )
    resolution: ResolutionIndex = ResolutionIndex.RESOLUTION_75CM
    light: LightControlStatus = field(default_factory=lambda: copy.deepcopy(_DefaultLight))

    def reset_to_factory(self) -> None:
        """Reset these parameters to factory settings."""
        self.baud_rate = BaudRateIndex.RATE_256000
        self.bluetooth_mode = True
        self.bluetooth_password = _DefaultBluetoothPassword
        self.engineering_mode = False
        self.parameters = copy.deepcopy(_DefaultParameters)
        self.resolution = ResolutionIndex.RESOLUTION_75CM
