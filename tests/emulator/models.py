from dataclasses import dataclass

from aio_ld2410 import ConfigModeStatus
from aio_ld2410.protocol import ResolutionIndex

_DefaultConfigModeStatus = ConfigModeStatus(
    buffer_size=64,
    protocol_version=1,
)


@dataclass
class DeviceStatus:
    """Contains the internal state of a device."""

    configuring: bool = False
    config_mode: ConfigModeStatus = _DefaultConfigModeStatus
    engineering_mode: bool = False
    bluetooth_mode: bool = True
    bluetooth_address: bytes = bytes.fromhex('8f272eb80f65')
    bluetooth_password: bytes = b'HiLink'
    resolution: ResolutionIndex = ResolutionIndex.RESOLUTION_75CM
