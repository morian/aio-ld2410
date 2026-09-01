from __future__ import annotations

from enum import IntEnum

from construct import Array, Byte, Const, Enum, If, Int16ul, Struct

from .command import OutPinLevel


class ReportType(IntEnum):
    """Type of report we received."""

    #: Advanced report with per-gate values.
    ENGINEERING = 1

    #: Basic report for an easy use.
    BASIC = 2


class TargetStatus(IntEnum):
    """
    Target status.

    This field is present in reports and tells whether the target (if any)
    is static, moving or both, or tells the live status of the calibration
    process when such calibration process is being run.

    """

    NO_TARGET = 0  #: No target has been detected
    MOVING = 1  #: There is a moving target
    STATIC = 2  #: There is a static target
    STATIC_MOVING = 3  #: There is a static and moving target
    NOISE_RUNNING = 4  #: We are under the noise threshold
    NOISE_SUCCESS = 5  #: Background noise detected successfully
    NOISE_FAILED = 6  #: Background noise detection failed


_ReportBasic = Struct(
    'target_status' / Enum(Byte, TargetStatus),
    'moving_distance' / Int16ul,  # in centimeters
    'moving_energy' / Byte,  # in percent
    'static_distance' / Int16ul,  # in centimeters
    'static_energy' / Byte,  # in percent
    'detection_distance' / Int16ul,  # in centimeters
)

_ReportEngineering = Struct(
    'moving_max_distance_gate' / Byte,  # Gate number (should be 8)
    'static_max_distance_gate' / Byte,  # Gate number (should be 8)
    # moving energy per-gate (percent)
    'moving_gate_energy' / Array(lambda this: 1 + this.moving_max_distance_gate, Byte),
    # static energy per-gate (percent)
    'static_gate_energy' / Array(lambda this: 1 + this.static_max_distance_gate, Byte),
    'photosensitive_value' / Byte,  # From 0 to 255
    'out_pin_status' / Enum(Byte, OutPinLevel),
)

_ReportEngineeringOrNone = If(
    lambda this: int(this._.type) == ReportType.ENGINEERING,
    _ReportEngineering,
)

_ReportData = Struct(
    'basic' / _ReportBasic,
    'engineering' / _ReportEngineeringOrNone,
)

Report = Struct(
    'type' / Enum(Byte, ReportType),
    Const(0xAA, Byte),  # head
    'data' / _ReportData,
    Const(0x55, Byte),  # tail
    Const(0x00, Byte),  # calibration
)
