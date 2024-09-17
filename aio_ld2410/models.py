from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, TypeVar, TypedDict

if TYPE_CHECKING:
    from construct import Container

_T = TypeVar('_T')


class ConfigModeStatus(TypedDict):
    """Status received when entering configuration mode."""

    buffer_size: int
    protocol_version: int


class ParametersConfig(TypedDict):
    """Configuration parameters."""

    motion_max_distance_gate: int
    standstill_max_distance_gate: int
    no_one_idle_duration: int


class ParametersStatus(ParametersConfig):
    """List of current parameters."""

    max_distance_gate: int
    motion_sensitivity: list[int]
    standstill_sensitivity: list[int]


def _filter_out_private(pair: tuple[str, Any]) -> bool:
    key, _ = pair
    return bool(not key.startswith('_'))


def _value_to_atom(val: Any) -> Any:
    """Convert any kind of value to something suitable for a dictionary."""
    if isinstance(val, Mapping):
        return _container_to_dict(val)
    if isinstance(val, Sequence):
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
    return list(map(_value_to_atom, data))


def container_to_model(cls: type[_T], data: Container[Any]) -> _T:
    """Map the provided container to a dataclass."""
    return cls(**_container_to_dict(data))
