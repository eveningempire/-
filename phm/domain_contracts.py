"""算法接入契约；只定义输入输出，不包含算法实现。"""
from dataclasses import dataclass, field
from typing import Any

@dataclass
class TelemetryBatch:
    vehicle_id: str
    timestamp: str
    signals: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class DiagnosisResult:
    status: str = "not_implemented"
    fault_modes: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class HealthAssessment:
    status: str = "not_implemented"
    health_index: float | None = None
    confidence: float | None = None

@dataclass
class RulPrediction:
    status: str = "not_implemented"
    remaining_life: float | None = None
    unit: str | None = None
    interval: tuple[float, float] | None = None
