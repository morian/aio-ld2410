from dataclasses import dataclass

from aio_ld2410 import ConfigModeStatus, FirmwareVersion
from aio_ld2410.protocol import BaudRateIndex, ResolutionIndex

_DefaultConfigModeStatus = ConfigModeStatus(
    buffer_size=64,
    protocol_version=1,
)
_DefaultBluetoothAddress = bytes.fromhex('8f272eb80f65')
_DefaultFirmwareVersion = FirmwareVersion(
    type=0,
    major=1,
    minor=2,
    revision=0x22062416,
)


@dataclass
class DeviceStatus:
    """Contains the internal state of a device."""

    baudrate = BaudRateIndex.RATE_256000
    configuring: bool = False
    config_mode: ConfigModeStatus = _DefaultConfigModeStatus
    engineering_mode: bool = False
    bluetooth_mode: bool = True
    bluetooth_address: bytes = _DefaultBluetoothAddress
    bluetooth_password: bytes = b'HiLink'
    firmware_version: FirmwareVersion = _DefaultFirmwareVersion
    resolution: ResolutionIndex = ResolutionIndex.RESOLUTION_75CM
