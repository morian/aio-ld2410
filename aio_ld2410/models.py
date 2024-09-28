from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Any, TypeVar, TypedDict

import dacite
from construct import Container, EnumIntegerString

from .protocol import AuxiliaryControl, OutPinLevel, TargetStatus

_T = TypeVar('_T')


@dataclass
class AuxiliaryControlStatus:
    """
    Status of the auxiliary controls for the ``OUT`` pin.

    See Also:
        :meth:`.LD2410.get_auxiliary_controls`

    """

    #: Determines when the ``OUT`` pin is high with sensitivity.
    control: AuxiliaryControl

    #: Photo-sensitivity threshold value (from 0 to 255).
    threshold: int

    #: Default value for ``OUT`` when not triggered.
    default: OutPinLevel


class AuxiliaryControlConfig(TypedDict, total=True):
    """
    Configuration of the auxiliary controls for the ``OUT`` pin.

    This class is used to parse keyword arguments from :meth:`.LD2410.set_auxiliary_controls`.

    See Also:
        - :meth:`.LD2410.set_auxiliary_controls`
        - :class:`AuxiliaryControlStatus`

    """

    #: Determines when the ``OUT`` pin is high with sensitivity.
    control: AuxiliaryControl

    #: Photo-sensitivity threshold value (from 0 to 255).
    threshold: int

    #: Default value for ``OUT`` when not triggered.
    default: OutPinLevel


@dataclass(frozen=True)
class ConfigModeStatus:
    """
    Values received when entering the configuration mode.

    See Also:
        :meth:`.LD2410.configure`

    """

    #: Version of the communication protocol.
    protocol_version: int

    #: Size of the device's internal read buffer (in bytes).
    buffer_size: int


@dataclass(frozen=True)
class FirmwareVersion:
    """
    Describes a firmware version.

    See Also:
        :meth:`.LD2410.get_firmware_version`.

    """

    type: int  #: Firmware type (documentation says it is 0).
    major: int  #: Major firmware version.
    minor: int  #: Minor firmware version.
    revision: int  #: Firmware revision (should be read as hex).

    def __str__(self) -> str:
        """Get a textual representation of the firmware version."""
        return f'{self.major}.{self.minor:02d}.{self.revision:08x}'


class GateSensitivityConfig(TypedDict, total=True):
    """
    Set current sensitivity values for a specific gate.

    This class is used to parse keyword arguments from :meth:`.LD2410.set_gate_sensitivity`.

    See Also:
        :meth:`.LD2410.set_gate_sensitivity`.

    """

    #: Gate to set (value form 0 to 8, can be 0xFFFF for broadcast to all gates).
    distance_gate: int

    #: Motion sensitivity (in percent, from 0 to 100).
    motion_sensitivity: int  # percent

    #: Stationary sensitivity (in percent, from 0 to 100).
    standstill_sensitivity: int  # percent


class ParametersConfig(TypedDict, total=True):
    """
    Standard configuration parameters.

    This class is used to parse keyword arguments from :meth:`.LD2410.set_parameters`.

    See Also:
        :meth:`.LD2410.set_parameters`.

    """

    #: Furthest gate to consider for motion detection (from 2 to 8).
    motion_max_distance_gate: int

    #: Furthest gate to consider for stationary detection (from 2 to 8).
    standstill_max_distance_gate: int

    #: How long to keep detecting a presence after the person moved away (0 to 65535 seconds).
    no_one_idle_duration: int


@dataclass
class ParametersStatus:
    """
    Status of current standard parameters.

    See Also:
        - :class:`ParametersConfig`
        - :meth:`.LD2410.get_parameters`.

    """

    #: Furthest configurable gate number (should be 8).
    max_distance_gate: int

    #: Furthest configured gate number for motion detection.
    motion_max_distance_gate: int

    #: Array of motion sensitivities for each gate (9 elements, percentage).
    motion_sensitivity: Sequence[int]

    #: Furthest configured gate number for stationary detection.
    standstill_max_distance_gate: int

    #: Array of stationary sensitivities for each gate (9 elements, percentage).
    standstill_sensitivity: Sequence[int]

    #: How long the sensor keeps detecting a presence after the person moved away (seconds).
    no_one_idle_duration: int


@dataclass
class ReportBasicStatus:
    """
    Basic part of the :class:`ReportStatus`.

    See Also:
        :class:`ReportStatus`

    """

    #: Detection status flags of the target (if any).
    target_status: TargetStatus

    #: When detected in motion, at which distance (in centimeters).
    motion_distance: int

    #: Motion energy of the target (in percent, from 0 to 100).
    motion_energy: int

    #: When detected stationary, at which distance (in centimeters).
    standstill_distance: int

    #: Stationary energy of the target (in percent, from 0 to 100).
    standstill_energy: int  # in percent

    #: Detection distance (in centimeters).
    detection_distance: int


@dataclass
class ReportEngineeringStatus:
    """
    Engineering part of the :class:`ReportStatus`.

    See Also:
        - :class:`ParametersStatus`
        - :class:`ReportStatus`

    """

    #: Furthest configured gate number for motion detection.
    motion_max_distance_gate: int

    #: Furthest configured gate number for stationary detection.
    standstill_max_distance_gate: int

    #: Array of motion energies for each gate (9 elements, percentage).
    motion_gate_energy: Sequence[int]

    #: Array of stationary energies for each gate (9 elements, percentage).
    standstill_gate_energy: Sequence[int]

    #: Photo-sensor value (from 0 to 255).
    photosensitive_value: int

    #: Current status of the ``OUT`` pin.
    out_pin_status: OutPinLevel


@dataclass
class ReportStatus:
    """
    Structure of a report received from the device.

    See Also:
        - :meth:`.LD2410.get_last_report`
        - :meth:`.LD2410.get_next_report`
        - :meth:`.LD2410.get_reports`
        - :meth:`.LD2410.set_engineering_mode`

    """

    #: Basic part of the report (always set).
    basic: ReportBasicStatus

    #: Engineering part of the report (only in engineering mode), :obj:`None` otherwise.
    engineering: ReportEngineeringStatus | None


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
    return list(map(_value_to_atom, data))


# Ensure that all enumeration types we use are simply casted.
_dacite_config = dacite.Config(cast=[IntEnum, IntFlag])


def container_to_model(data_class: type[_T], data: Container[Any]) -> _T:
    """Map the provided container to a model using :mod:`dacite`."""
    return dacite.from_dict(
        data_class=data_class,
        data=_container_to_dict(data),
        config=_dacite_config,
    )
