from __future__ import annotations

from .exceptions import (
    AioLd2410Error,
    CommandContextError,
    CommandError,
    CommandParamError,
    CommandReplyError,
    CommandStatusError,
    ConnectionClosedError,
    ModuleRestartedError,
)
from .ld2410 import LD2410
from .models import (
    AuxiliaryControlConfig,
    AuxiliaryControlStatus,
    ConfigModeStatus,
    FirmwareVersion,
    GateSensitivityConfig,
    ParametersConfig,
    ParametersStatus,
    ReportBasicStatus,
    ReportEngineeringStatus,
    ReportStatus,
)
from .protocol import (
    AuxiliaryControl,
    BaudRateIndex,
    OutPinLevel,
    ResolutionIndex,
    TargetStatus,
)
from .version import version

__version__ = version
__all__ = [
    'AioLd2410Error',
    'AuxiliaryControl',
    'AuxiliaryControlConfig',
    'AuxiliaryControlStatus',
    'BaudRateIndex',
    'CommandError',
    'CommandContextError',
    'CommandParamError',
    'CommandReplyError',
    'CommandStatusError',
    'ConfigModeStatus',
    'ConnectionClosedError',
    'FirmwareVersion',
    'GateSensitivityConfig',
    'LD2410',
    'ModuleRestartedError',
    'OutPinLevel',
    'ParametersConfig',
    'ParametersStatus',
    'ReportBasicStatus',
    'ReportEngineeringStatus',
    'ReportStatus',
    'ResolutionIndex',
    'TargetStatus',
    'version',
]
