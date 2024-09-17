from __future__ import annotations

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


def container_to_dataclass(cls: type[_T], data: Container[Any]) -> _T:
    """Map the provided container to a dataclass."""
    # TODO: maybe we have an issue here with nested containers.
    d = dict(filter(_filter_out_private, data.items()))
    return cls(**d)
