"""Unified ModelAdapter interface and the concrete v2 adapters.

Every adapter implements ``load / validate_input / infer / reset``.  Adapters
are causal, per-session isolated (state keyed by (session, run, component))
and never read labels.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional

import joblib
import numpy as np
import pandas as pd

from .schemas import RecordError, validate_input_record


class ModelAdapter(ABC):
    """Contract every pluggable model fulfils (goal v2 section 12)."""

    head: str = ""
    model_name: str = ""
    model_version: str = ""

    @abstractmethod
    def load(self, path: Optional[Path]) -> None: ...

    @abstractmethod
    def infer(self, record: Dict) -> Dict:
        """Return this head's contribution for one validated input record."""

    @abstractmethod
    def reset(self, session_key: Optional[tuple] = None) -> None:
        """Clear causal state (all sessions when session_key is None)."""


def session_key_of(record: Dict) -> tuple:
    return (str(record.get("session_id", "default")), int(record["run_id"]), str(record["component_id"]))


class CH2ComponentHiAdapter(ModelAdapter):
    """component_hi for qualified components (CH-2a@z5.0 joblib artifact)."""

    head = "component_hi"
    model_name = "p1v3_ch2_collapse_gate"
    model_version = "CH-2a@z5.0"

    def __init__(self, component_id: str) -> None:
        self.component_id = component_id
        self.model: Optional[object] = None

    def load(self, path: Optional[Path]) -> None:
        if path is None:
            raise ValueError("CH2ComponentHiAdapter requires an artifact path")
        self.model = joblib.load(Path(path))

    def infer(self, record: Dict) -> Dict:
        if self.model is None:
            raise RecordError("E_ARTIFACT_MISSING", "component_hi model not loaded")
        frame = pd.DataFrame([record])
        value = float(np.clip(self.model.apply(frame)[0], 0.0, 1.0))
        return {"component_hi": value, "component_hi_source": f"p1v3:{self.model_version}", "component_hi_status": "qualified"}

    def reset(self, session_key: Optional[tuple] = None) -> None:
        return None  # stateless


class FrozenCDPCAReferenceAdapter(ModelAdapter):
    """component_hi fallback for lox_pump: the frozen CDPCA score passes through."""

    head = "component_hi"
    model_name = "frozen_cdPCA_mini84"
    model_version = "external_frozen"

    def __init__(self, component_id: str) -> None:
        self.component_id = component_id

    def load(self, path: Optional[Path]) -> None:
        return None

    def infer(self, record: Dict) -> Dict:
        value = float(record["hi_cd"])
        return {"component_hi": value, "component_hi_source": "frozen_cdPCA_mini84", "component_hi_status": "fallback"}

    def reset(self, session_key: Optional[tuple] = None) -> None:
        return None


class AbstainAdapter(ModelAdapter):
    """fault_alarm terminal abstain: raw anomaly_score only, never an alarm."""

    head = "fault_alarm"
    model_name = "raw_anomaly_score_abstain"
    model_version = "abstain_v2_20260910"

    def load(self, path: Optional[Path]) -> None:
        return None

    def infer(self, record: Dict) -> Dict:
        return {"anomaly_score": float(record["anomaly_score"]), "fault_alarm_state": False, "fault_alarm_status": "abstain_failed_gates"}

    def reset(self, session_key: Optional[tuple] = None) -> None:
        return None


class LocalizationLC2Adapter(ModelAdapter):
    """localization z-fusion scorer (LC-2a); thresholds NOT_REGISTERED."""

    head = "localization"
    model_name = "p1v3_lc2_supervised_zfusion"
    model_version = "LC-2a"

    def __init__(self, component_id: str) -> None:
        self.component_id = component_id
        self.model: Optional[object] = None

    def load(self, path: Optional[Path]) -> None:
        if path is None:
            raise ValueError("LocalizationLC2Adapter requires an artifact path")
        self.model = joblib.load(Path(path))

    def infer(self, record: Dict) -> Dict:
        if self.model is None:
            raise RecordError("E_ARTIFACT_MISSING", "localization model not loaded")
        frame = pd.DataFrame([record])
        score = float(self.model.window_score(frame)[0])
        return {"localization_score": score, "localization_status": "development_only_not_registered"}

    def reset(self, session_key: Optional[tuple] = None) -> None:
        return None


class NoOpAdapter(ModelAdapter):
    """Terminal abstain: emits nothing (heads handle the missing contribution)."""

    def __init__(self, head: str = "") -> None:
        self.head = head

    def load(self, path: Optional[Path]) -> None:
        return None

    def infer(self, record: Dict) -> Dict:
        return {}

    def reset(self, session_key: Optional[tuple] = None) -> None:
        return None


class AdapterFactory:
    """Builds adapters from registry entries; the extension point for replacements."""

    def __init__(self, model_root: Path) -> None:
        self.model_root = Path(model_root)

    def build(self, entry):
        component_id = entry.component_id
        if entry.model_name == "p1v3_ch2_collapse_gate":
            adapter = CH2ComponentHiAdapter(component_id)
        elif entry.model_name == "frozen_cdPCA_mini84":
            adapter = FrozenCDPCAReferenceAdapter(component_id)
        elif entry.model_name == "raw_anomaly_score_abstain":
            adapter = AbstainAdapter()
        elif entry.model_name == "p1v3_lc2_supervised_zfusion":
            adapter = LocalizationLC2Adapter(component_id)
        elif entry.model_name == "abstain":
            adapter = NoOpAdapter(head=entry.head)
        else:
            raise ValueError(f"unknown model in registry: {entry.model_name}")
        adapter.load(self.model_root / entry.artifact if entry.artifact else None)
        return adapter
