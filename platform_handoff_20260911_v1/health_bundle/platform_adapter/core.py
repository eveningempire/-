"""Multi-head orchestration core: schema validation -> registry-resolved
adapters -> causal policy -> output records.  Algorithm-agnostic by design:
replacing a model touches only the registry + artifact files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .adapters import AdapterFactory, ModelAdapter, session_key_of
from .policy import DegradationPolicy
from .provenance import Provenance, load_bundle_provenance
from .registry import ModelRegistry
from .schemas import (
    COMPONENT_IDS,
    SCHEMA_VERSION,
    OUTPUT_FIELDS,
    RecordError,
    validate_input_record,
)

BUNDLE_VERSION = "platform_integration_modular_dev_v2_20260910"
HEADS = ("component_hi", "fault_alarm", "localization")

LIMITATIONS = [
    "DEVELOPMENT bundle: INTEGRATION_READY_DEVELOPMENT only; safety_qualified=false; formal_p1_frozen=false; p4_gate_open=false",
    "system_hi_proxy is the transparent weakest-link min(component_hi) proxy - not a physical safety margin and not an RUL",
    "input is upstream per-window model evidence (frozen CDPCA/AE scores), not raw telemetry",
    "fault_alarm head is ABSTAIN (registered hard gates not met); raw anomaly_score is the audited evidence",
    "localization thresholds are NOT_REGISTERED (development evidence only)",
]


class HealthAssessmentCore:
    """Head orchestration over a validated JSONL record stream."""

    def __init__(self, registry: ModelRegistry, *, provenance: Optional[Provenance] = None, factory: Optional[AdapterFactory] = None) -> None:
        self.registry = registry
        self.factory = factory or AdapterFactory(registry.model_root)
        self.provenance = provenance
        self.policy = DegradationPolicy()
        self.adapters: Dict[tuple, ModelAdapter] = {}
        self.seen_windows: set = set()
        self.components_seen: set = set()
        self._load_adapters()

    def _load_adapters(self) -> None:
        for head in HEADS:
            for component in COMPONENT_IDS:
                entry, events = self.registry.resolve(head, component)
                for event in events:
                    self.registry.events.append(event)
                self.adapters[(head, component)] = self.factory.build(entry)

    # -- replacement drill support -------------------------------------------
    def swap_adapter(self, head: str, component_id: str, adapter: ModelAdapter) -> None:
        """Hot-swap one adapter (used by the model-replacement drill and by new
        model versions registered in the registry).  Schema and callers unchanged."""
        self.adapters[(head, component_id)] = adapter

    # -- stream handling ------------------------------------------------------
    def process_record(self, raw: Dict) -> Dict:
        record = validate_input_record(raw)
        key = session_key_of(record)
        window_key = (key, int(record["window_index"]))
        if window_key in self.seen_windows:
            raise RecordError("E_DUPLICATE_WINDOW", str(window_key))
        self.policy.check_order(key, float(record["timestamp"]))
        self.seen_windows.add(window_key)
        self.components_seen.add(str(record["component_id"]))

        component = str(record["component_id"])
        output: Dict = {
            "schema_version": SCHEMA_VERSION,
            "session_id": record["session_id"],
            "run_id": record["run_id"],
            "component_id": component,
            "window_index": record["window_index"],
            "timestamp": record["timestamp"],
            "warnings": [],
            "limitations": list(LIMITATIONS),
        }
        for head in HEADS:
            adapter = self.adapters[(head, component)]
            contribution = adapter.infer(record)
            output.update(contribution)
        if "component_hi" not in output:
            # abstain fallback must never silently emit a healthy value
            raise RecordError("E_NOT_QUALIFIED", "no component_hi source resolved")
        policy_result = self.policy.step(key, float(output["component_hi"]), record.get("confidence"))
        output["degradation_state"] = policy_result["degradation_state"]
        output["warnings"] = policy_result["warnings"] + output.get("warnings", [])
        if self.provenance is not None:
            output["trace_hash"] = self.provenance.record_trace(record)
        else:
            from .provenance import input_trace_hash

            output["trace_hash"] = input_trace_hash(record)
        return {field: output.get(field) for field in OUTPUT_FIELDS}

    def session_summary(self, session_id: str, run_id: int) -> Dict:
        """Weakest-link proxy over the components seen in this (session, run)."""
        return {
            "schema_version": SCHEMA_VERSION,
            "session_id": session_id,
            "run_id": run_id,
            "summary_type": "system_hi_proxy_weakest_link_min_component_hi",
            "proxy_name": "system_hi_proxy (weakest-link min(component_hi); NOT a physical safety margin, NOT an RUL)",
            "components_covered": sorted(self.components_seen),
            "components_missing": sorted(set(COMPONENT_IDS) - self.components_seen),
            "warnings": ["W_PARTIAL_COMPONENTS"] if len(self.components_seen) < len(COMPONENT_IDS) else [],
            "limitations": list(LIMITATIONS),
        }

    def reset(self, session_id: Optional[str] = None, run_id: Optional[int] = None) -> None:
        if session_id is None and run_id is None:
            self.policy.reset()
            self.seen_windows.clear()
            self.components_seen.clear()
            return
        prefix = (str(session_id), int(run_id))
        for key in [k for k in list(self.policy._order) if k[:2] == prefix]:
            for store in (self.policy._enter_run, self.policy._exit_run, self.policy._alarm, self.policy._order):
                store.pop(key, None)
        for window_key in [k for k in list(self.seen_windows) if k[0][:2] == prefix]:
            self.seen_windows.discard(window_key)


def process_jsonl(lines: List[str], core: HealthAssessmentCore) -> List[Dict]:
    """Process JSONL lines; bad lines yield error records and never crash the batch."""
    outputs: List[Dict] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            raw = json.loads(stripped)
        except json.JSONDecodeError as error:
            outputs.append({"schema_version": SCHEMA_VERSION, "error": "E_BAD_JSON", "detail": str(error)[:120], "warnings": [], "limitations": list(LIMITATIONS)})
            continue
        if isinstance(raw, dict) and raw.get("action") == "reset":
            core.reset(raw.get("session_id"), raw.get("run_id"))
            outputs.append({"schema_version": SCHEMA_VERSION, "action": "reset", "warnings": [], "limitations": list(LIMITATIONS)})
            continue
        if isinstance(raw, dict) and raw.get("action") == "summary":
            outputs.append(core.session_summary(str(raw.get("session_id", "default")), int(raw.get("run_id", 0))))
            continue
        try:
            outputs.append(core.process_record(raw))
        except RecordError as error:
            outputs.append({"schema_version": SCHEMA_VERSION, "error": error.code, "detail": error.detail[:160], "warnings": [], "limitations": list(LIMITATIONS)})
    return outputs
