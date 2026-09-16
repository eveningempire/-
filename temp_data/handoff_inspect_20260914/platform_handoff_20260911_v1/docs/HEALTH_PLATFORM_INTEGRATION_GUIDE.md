# PLATFORM INTEGRATION GUIDE (dev bundle, schema health-assessment-platform-dev/2.0)

## What this bundle actually consumes (read this first)
The models inside consume UPSTREAM-GENERATED per-window model evidence - the
frozen CDPCA component score (hi_cd) and the frozen AE evidence columns
(hi_ae, anomaly_score, reconstruction_error). This is NOT a raw-telemetry
end-to-end service. Upstream must run the frozen CDPCA/AE models first and
stream their per-window outputs here.

## Input (JSONL; one window record per line)
```json
{"run_id": 9001, "session_id": "line1", "component_id": "lox_pump",
 "window_index": 5, "timestamp": 154.9,
 "hi_cd": 0.96, "hi_ae": 1.0, "anomaly_score": -7.5,
 "reconstruction_error": 0.0004, "confidence": 0.97}
```
- required: run_id, component_id, window_index, timestamp, hi_cd, hi_ae, anomaly_score
- optional: session_id (multi-session isolation), reconstruction_error,
  mahalanobis_distance, single_gaussian_anomaly_score, data_quality_score, confidence
- hi_cd/hi_ae must be within [0, 1]; numbers must be finite.
- Control records: {"action": "summary", "session_id", "run_id"} emits the
  weakest-link proxy summary; {"action": "reset", ...} clears session state.

## Forbidden input fields (rejected on sight, E_SCHEMA_FORBIDDEN_FIELD)
hi_true, truth_factor*, system_health_proxy_gt, mode, target_component,
active_components, fault_onset/fault_end/fault_severity, data_split/split,
seed/random_seed, sensor_fault_*, health_level - labels and simulation
parameters may never enter a platform input.

## Output (JSONL; one record per input line)
component_hi (+status qualified/fallback/abstain + source version),
anomaly_score (raw, audited), fault_alarm_state (currently always false with
fault_alarm_status=abstain_failed_gates), degradation_state (causal registered
rule 0.80/0.80/3win, session-isolated), localization_score (status
development_only_not_registered), confidence warnings, limitations,
trace_hash (schema+config+model+input bound). Summary records add
system_hi_proxy = min(component_hi) explicitly labelled
"weakest-link proxy; NOT a physical safety margin; NOT an RUL".

## Honest status (frozen; do not edit downstream)
release_status=INTEGRATION_READY_DEVELOPMENT; safety_qualified=false;
formal_p1_frozen=false; p4_gate_open=false. The fault alarm head FAILED its
registered hard gates (0/7 components) and is ABSTAIN; the localization head
has no registered thresholds. These states are inherited from the strict
outer-OOF evidence in science_metrics/.

## Error codes
E_SCHEMA_MISSING_FIELD, E_SCHEMA_FORBIDDEN_FIELD, E_SCHEMA_TYPE,
E_VALUE_NAN_INF, E_VALUE_OUT_OF_RANGE, E_UNKNOWN_COMPONENT,
E_DUPLICATE_WINDOW, E_OUT_OF_ORDER, E_BAD_JSON, E_HASH_MISMATCH,
E_ARTIFACT_MISSING, E_NOT_QUALIFIED, W_LOW_CONFIDENCE, W_PARTIAL_COMPONENTS,
W_INSUFFICIENT_HISTORY. Per-record errors never crash a batch: the offending
line yields one error record and the rest of the batch continues.

## Running
```
python -m platform_adapter.cli --bundle . --input examples/input_smoke.jsonl --output out.jsonl
python -m platform_adapter.cli --bundle . --smoke
python -m platform_adapter.cli --bundle . --replace-drill
```
Requires python 3.11+ with joblib/numpy/pandas/scikit-learn.
