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
    """All kind of emulator-specific commands."""

    DISCONNECT_NOW = auto()
    DISCONNECT_AFTER_COMMAND = auto()
    GENERATE_CORRUPTED_FRAME = auto()
    GENERATE_CORRUPTED_COMMAND = auto()
    GENERATE_SPURIOUS_REPLY = auto()
    RETURN_INVALID_RESOLUTION = auto()


@dataclass
class EmulatorCommand:
    """A command sent to the emulator."""

    code: EmulatorCode
    data: Mapping[str, Any] | None = None


@dataclass
class DeviceStatus:
    """Contains the internal state of a device."""

    baud_rate = BaudRateIndex.RATE_256000
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
