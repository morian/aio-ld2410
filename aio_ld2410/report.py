from __future__ import annotations

from enum import IntEnum

from construct import Array, Byte, Const, Enum, FlagsEnum, If, Int16ul, Struct

from .command import OutPinLevel


class ReportType(IntEnum):
    """Type of report we get here."""

    ENGINEERING = 1
    BASIC = 2


_ReportBasic = Struct(
    'target_status' / FlagsEnum(Byte, motion=1, standstill=2),
    'motion_distance' / Int16ul,  # in centimeters
    'motion_energy' / Byte,  # in percent
    'standstill_distance' / Int16ul,  # in centimeters
    'standstill_energy' / Byte,  # in percent
    'detection_distance' / Int16ul,  # in centimeters
)

_ReportEngineering = Struct(
    'motion_max_distance_gate' / Byte,  # Gate number
    'standstill_max_distance_gate' / Byte,  # Gate number
    'motion_gate_energy' / Array(9, Byte),  # motion energy per-gate (percent)
    'standstill_gate_energy' / Array(9, Byte),  # standstill energy per-gate (percent)
    'photosensitive_value' / Byte,  # From 0 to 255
    'out_pin_status' / Enum(Byte, OutPinLevel),
)

_ReportEngineeringOrNone = If(
    lambda this: this._.type == ReportType.ENGINEERING.name,
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
