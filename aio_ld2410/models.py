from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Any, TypeVar, TypedDict

import dacite
from construct import Container, EnumIntegerString

from .protocol import LightControl, OutPinLevel, TargetStatus

_T = TypeVar('_T')


@dataclass
class LightControlStatus:
    """
    Status of the light controls for the ``OUT`` pin.

    See Also:
        :meth:`.LD2410.get_light_control`

    """

    #: Determines when the ``OUT`` pin is high with sensitivity.
    control: LightControl

    #: Photo-sensitivity threshold value (from 0 to 255).
    threshold: int

    #: Default value for ``OUT`` when not triggered.
    default: OutPinLevel


class LightControlConfig(TypedDict, total=True):
    """
    Configuration of the light controls for the ``OUT`` pin.

    This class is used to parse keyword arguments from :meth:`.LD2410.set_light_control`.

    See Also:
        - :meth:`.LD2410.set_light_control`
        - :class:`LightControlStatus`

    """

    #: Determines when the ``OUT`` pin is high with sensitivity.
    control: LightControl

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
    minor: int  #: Minor firmware version (should read as hex).
    revision: int  #: Firmware revision (should be read as hex).

    def __str__(self) -> str:
        """Get a textual representation of the firmware version."""
        return f'{self.major}.{self.minor:02x}.{self.revision:08x}'


class GateSensitivityConfig(TypedDict, total=True):
    """
    Set current sensitivity values for a specific gate.

    This class is used to parse keyword arguments from :meth:`.LD2410.set_gate_sensitivity`.

    See Also:
        :meth:`.LD2410.set_gate_sensitivity`.

    """

    #: Gate to set (value from 0 to 8, can be 0xFFFF for broadcast to all gates).
    distance_gate: int

    #: Moving energy threshold (in percent, from 0 to 100).
    moving_threshold: int  # percent

    #: Static energy threshold (in percent, from 0 to 100).
    static_threshold: int  # percent


class ParametersConfig(TypedDict, total=True):
    """
    Standard configuration parameters.

    This class is used to parse keyword arguments from :meth:`.LD2410.set_parameters`.

    See Also:
        :meth:`.LD2410.set_parameters`.

    """

    #: Farthest gate to consider for moving detection (from 2 to 8).
    moving_max_distance_gate: int

    #: Farthest gate to consider for static detection (from 2 to 8).
    static_max_distance_gate: int

    #: How long to keep detecting a presence after the person moved away (0 to 65535 seconds).
    presence_timeout: int


@dataclass
class ParametersStatus:
    """
    Status of current standard parameters.

    See Also:
        - :class:`ParametersConfig`
        - :meth:`.LD2410.get_parameters`.

    """

    #: Farthest configurable gate number (should be 8).
    max_distance_gate: int

    #: Farthest configured gate number for moving detection.
    moving_max_distance_gate: int

    #: Array of moving energy thresholds for each gate (9 elements, percentage).
    moving_threshold: Sequence[int]

    #: Farthest configured gate number for static detection.
    static_max_distance_gate: int

    #: Array of static energy thresholds for each gate (9 elements, percentage).
    static_threshold: Sequence[int]

    #: How long the sensor keeps detecting a presence after the person moved away (seconds).
    presence_timeout: int


@dataclass
class ReportBasicStatus:
    """
    Basic part of the :class:`ReportStatus`.

    See Also:
        :class:`ReportStatus`

    """

    #: Detection status flags of the target (if any).
    target_status: TargetStatus

    #: When detected moving, at which distance (in centimeters).
    moving_distance: int

    #: Energy of the moving target (in percent, from 0 to 100).
    moving_energy: int

    #: When detected static, at which distance (in centimeters).
    static_distance: int

    #: Energy of the static target (in percent, from 0 to 100).
    static_energy: int  # in percent

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

    #: Farthest configured gate number for moving detection.
    moving_max_distance_gate: int

    #: Farthest configured gate number for static detection.
    static_max_distance_gate: int

    #: Array of moving energies for each gate (9 elements, percentage).
    moving_gate_energy: Sequence[int]

    #: Array of static energies for each gate (9 elements, percentage).
    static_gate_energy: Sequence[int]

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
