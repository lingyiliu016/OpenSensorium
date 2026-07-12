"""OpenSensorium — 以视觉为主、多模态并行的持续感知—主动行动通用智能体。

设计见仓库根目录 PRD.md；开发清单见 tasks/。
"""

from opensensorium.schemas import (
    CapabilityKind,
    CapabilityProfile,
    Intent,
    IntentType,
    Modality,
    PerceptionEvent,
    Timestamp,
)

__version__ = "0.0.1"

__all__ = [
    "__version__",
    "Timestamp",
    "Modality",
    "PerceptionEvent",
    "IntentType",
    "Intent",
    "CapabilityKind",
    "CapabilityProfile",
]
