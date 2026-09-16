"""Frozen input/output schemas for the pluggable health-assessment platform dev bundle.

schema_version is frozen at ``health-assessment-platform-dev/2.0``.  The bundle
consumes UPSTREAM-GENERATED per-window model evidence (frozen CDPCA / AE
scores), NOT raw telemetry - this is stated openly in
PLATFORM_INTEGRATION_GUIDE.md and is a hard property of the input schema.

Label/truth fields are rejected on sight (they may never enter a platform
input); see FORBIDDEN_INPUT_FIELDS.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

SCHEMA_VERSION = "health-assessment-platform-dev/2.0"

COMPONENT_IDS = (
    "lox_pump",
    "oxygen_turbine",
    "kerosene_pipeline",
    "kerosene_valve",
    "gas_generator",
    "combustion_chamber",
    "nozzle",
)

REQUIRED_INPUT_FIELDS: Tuple[str, ...] = (
    "run_id",
    "component_id",
    "window_index",
    "timestamp",
    "hi_cd",
    "hi_ae",
    "anomaly_score",
)
OPTIONAL_INPUT_FIELDS: Tuple[str, ...] = (
    "session_id",
    "reconstruction_error",
    "mahalanobis_distance",
    "single_gaussian_anomaly_score",
    "data_quality_score",
    "confidence",
)
# labels / split control / simulation parameters: never acceptable in an input
FORBIDDEN_INPUT_FIELDS: Tuple[str, ...] = (
    "hi_true",
    "truth_factor",
    "truth_factor_x",
    "truth_factor_y",
    "system_health_proxy_gt",
    "mode",
    "target_component",
    "target_label",
    "target_p",
    "active_components",
    "fault_onset",
    "fault_end",
    "fault_severity",
    "data_split",
    "split",
    "seed",
    "random_seed",
    "sensor_fault_signal",
    "sensor_fault_type",
    "sensor_fault_onset",
    "sensor_fault_end",
    "sensor_fault_magnitude",
    "health_level",
)
FLOAT_FIELDS: Tuple[str, ...] = (
    "timestamp",
    "hi_cd",
    "hi_ae",
    "anomaly_score",
    "reconstruction_error",
    "mahalanobis_distance",
    "single_gaussian_anomaly_score",
    "data_quality_score",
    "confidence",
)
HI_RANGE = (0.0, 1.0)

OUTPUT_FIELDS: Tuple[str, ...] = (
    "schema_version",
    "trace_hash",
    "session_id",
    "run_id",
    "component_id",
    "window_index",
    "timestamp",
    "component_hi",
    "component_hi_status",
    "component_hi_source",
    "anomaly_score",
    "fault_alarm_state",
    "fault_alarm_status",
    "degradation_state",
    "localization_score",
    "localization_status",
    "confidence",
    "warnings",
    "limitations",
)

ERROR_CODES: Dict[str, str] = {
    "E_SCHEMA_MISSING_FIELD": "required input field missing",
    "E_SCHEMA_FORBIDDEN_FIELD": "label/truth field present in input (rejected on sight)",
    "E_SCHEMA_TYPE": "field has a non-parseable type",
    "E_VALUE_NAN_INF": "numeric field is NaN/Inf",
    "E_VALUE_OUT_OF_RANGE": "numeric value outside the registered range",
    "E_UNKNOWN_COMPONENT": "component_id outside the seven canonical components",
    "E_DUPLICATE_WINDOW": "(session, run, component, window_index) already processed",
    "E_OUT_OF_ORDER": "timestamp not strictly increasing within (session, run, component)",
    "E_BAD_JSON": "line is not valid JSON (batch continues)",
    "E_HASH_MISMATCH": "artifact hash differs from the registry entry (fallback used)",
    "E_ARTIFACT_MISSING": "artifact file absent (fallback used)",
    "E_NOT_QUALIFIED": "model not qualified for the requested head (fallback/abstain)",
    "W_LOW_CONFIDENCE": "confidence below the warning level",
    "W_PARTIAL_COMPONENTS": "some canonical components absent from this batch",
    "W_INSUFFICIENT_HISTORY": "causal persistence not yet satisfied for this session",
}


class RecordError(Exception):
    """Per-record rejection; never crashes the batch."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def validate_input_record(record: Dict) -> Dict:
    """Validate one raw input record; raises RecordError on violation."""
    if not isinstance(record, dict):
        raise RecordError("E_SCHEMA_TYPE", "record is not a JSON object")
    forbidden = sorted(set(record) & set(FORBIDDEN_INPUT_FIELDS))
    if forbidden:
        raise RecordError("E_SCHEMA_FORBIDDEN_FIELD", ",".join(forbidden))
    missing = [field for field in REQUIRED_INPUT_FIELDS if field not in record]
    if missing:
        raise RecordError("E_SCHEMA_MISSING_FIELD", ",".join(missing))
    component = record["component_id"]
    if component not in COMPONENT_IDS:
        raise RecordError("E_UNKNOWN_COMPONENT", str(component))
    parsed: Dict = {}
    for field in ("run_id", "window_index"):
        try:
            parsed[field] = int(record[field])
        except (TypeError, ValueError):
            raise RecordError("E_SCHEMA_TYPE", field)
    parsed["component_id"] = str(component)
    parsed["session_id"] = str(record.get("session_id", "default"))
    for field in FLOAT_FIELDS:
        if field not in record:
            continue
        if record[field] is None:
            raise RecordError("E_SCHEMA_TYPE", f"{field}=null")
        try:
            value = float(record[field])
        except (TypeError, ValueError):
            raise RecordError("E_SCHEMA_TYPE", field)
        if value != value or value in (float("inf"), float("-inf")):
            raise RecordError("E_VALUE_NAN_INF", field)
        parsed[field] = value
    for field in ("hi_cd", "hi_ae"):
        if field in parsed and not (HI_RANGE[0] <= parsed[field] <= HI_RANGE[1]):
            raise RecordError("E_VALUE_OUT_OF_RANGE", f"{field}={parsed[field]}")
    return parsed
