from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar, TypedDict

from construct import Container, EnumIntegerString

if TYPE_CHECKING:
    from .protocol import AuxiliaryControl, OutPinLevel

_T = TypeVar('_T')


@dataclass
class AuxiliaryControlStatus:
    """Status of the auxiliary controls (OUT pin)."""

    control: AuxiliaryControl
    threshold: int
    default: OutPinLevel


class AuxiliaryControlConfig(TypedDict):
    """Configuration of the auxiliary control (OUT pin)."""

    control: AuxiliaryControl
    threshold: int
    default: OutPinLevel


@dataclass
class ConfigModeStatus:
    """Status received when entering configuration mode."""

    buffer_size: int
    protocol_version: int


@dataclass
class FirmwareVersion:
    """Get the current firmware version."""

    type: int
    major: int
    minor: int
    revision: int

    def __str__(self) -> str:
        """Get a textual representation of the firmware version."""
        return f'{self.major}.{self.minor:02d}.{self.revision:08x}'


class GateSensitivityConfig(TypedDict):
    """Get current sensitivity values."""

    distance_gate: int  # 0 to 8, can be 0xFFFF for broadcast
    motion_sensitivity: int
    standstill_sensitivity: int


class ParametersConfig(TypedDict):
    """Configuration parameters."""

    motion_max_distance_gate: int
    standstill_max_distance_gate: int
    no_one_idle_duration: int


@dataclass
class ParametersStatus:
    """List of current parameters."""

    max_distance_gate: int
    motion_max_distance_gate: int
    motion_sensitivity: Sequence[int]
    standstill_max_distance_gate: int
    standstill_sensitivity: Sequence[int]
    no_one_idle_duration: int


def _filter_out_private(pair: tuple[str, Any]) -> bool:
    key, _ = pair
    return bool(not key.startswith('_'))


def _value_to_atom(val: Any) -> Any:
    """Convert any kind of value to something suitable for a dictionary."""
    if isinstance(val, EnumIntegerString):
        return val.intvalue  # type: ignore[attr-defined]
    if isinstance(val, Mapping):
        return _container_to_dict(val)
    if isinstance(val, Sequence) and not isinstance(val, (str, bytes)):
        return _sequence_to_list(val)
    return val


def _container_to_dict(data: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a construct container to a real dictionary."""
    d = {}
    for key, val in data.items():
        if not key.startswith('_'):
            d[key] = _value_to_atom(val)
    return d


def _sequence_to_list(data: Sequence[Any]) -> list[Any]:
    """Convert a sequence of items to something suitable for a dictionary."""
    print(data, type(data))
    return list(map(_value_to_atom, data))


def container_to_model(cls: type[_T], data: Container[Any]) -> _T:
    """Map the provided container to a model."""
    return cls(**_container_to_dict(data))
