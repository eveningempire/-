"""Bundle builder: assemble the self-contained pluggable platform dev bundle.

Layout (inside <version>/bundle/):
  platform_adapter/            standalone package (relative imports only)
  models/                      joblib artifacts (13)
  model_registry.json          registry with sha256 per artifact
  examples/input_smoke.jsonl   normal + bad-input examples
  PLATFORM_INTEGRATION_GUIDE.md / MODEL_REPLACEMENT_GUIDE.md
  SMOKE_TEST.ps1               non-interactive smoke (normal/bad-input/replace)
  run_smoke.py                 python fallback for the smoke commands
  science_metrics/             strict OOF evidence copied read-only
  IMPLEMENTATION_REPORT.md / run_summary.json / MANIFEST.sha256

The bundle zip + .sha256 land next to the bundle directory.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .registry import ModelRegistry, default_registry
from .schemas import SCHEMA_VERSION

BUNDLE_VERSION = "platform_integration_modular_dev_v2_20260910"
CSV_ENCODING = "utf-8"

PLATFORM_INTEGRATION_GUIDE = """# PLATFORM INTEGRATION GUIDE (dev bundle, schema health-assessment-platform-dev/2.0)

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
"""

MODEL_REPLACEMENT_GUIDE = """# MODEL REPLACEMENT GUIDE (no Schema/core/caller changes - ever)

## Contract
A model is pluggable iff it ships (1) an artifact file under models/, (2) one
model_registry.json entry under a (head, component) key with sha256,
qualification and fallback_head. The Schema (schemas.py), the orchestration
(core.py) and every caller stay untouched.

## Steps (example: new component_hi model for gas_generator)
1. Drop the artifact: models/component_hi_gas_generator_<NEW>.joblib
2. Edit model_registry.json - replace the component_hi/gas_generator entry:
   {"head": "component_hi", "component_id": "gas_generator",
    "model_name": "<your-model>", "model_version": "<semver>",
    "artifact": "models/component_hi_gas_generator_<NEW>.joblib",
    "sha256": "<file sha256>", "qualification": "qualified",
    "fallback_head": "component_hi_frozen_cdPCA"}
3. Add an adapter class for <your-model> in platform_adapter/adapters.py and
   one branch in AdapterFactory.build (the ONLY code edit, additive only).
4. Run: python -m platform_adapter.cli --bundle . --replace-drill
   The drill re-runs the same client input through the new model, proves the
   schema/output shape is unchanged, and proves a corrupted sha256 refuses the
   artifact and engages the registered fallback.

## Qualification honesty
Only set qualification="qualified" when strict outer-OOF evidence (fold-fit
models, frozen thresholds, bootstrap gates) supports it. Anything else must be
fallback / development_only_not_registered / abstain. The platform never
silently outputs a healthy value for a head that abstains.
"""


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_bundle(root: Path, output_dir: Path | None = None) -> dict:
    root = Path(root)
    output_dir = Path(output_dir) if output_dir else root / "health_assessment" / "outputs" / "improvements" / BUNDLE_VERSION
    if output_dir.exists():
        raise FileExistsError(f"bundle version directory already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    bundle = output_dir / "bundle"
    (bundle / "platform_adapter").mkdir(parents=True)
    (bundle / "models").mkdir()
    (bundle / "examples").mkdir()
    (bundle / "science_metrics").mkdir()
    started = time.time()

    # 1) code: copy the platform package (relative imports => standalone)
    package_src = root / "health_assessment" / "platform_adapter_v2"
    for module in sorted(package_src.glob("*.py")):
        shutil.copy2(module, bundle / "platform_adapter" / module.name)
    (bundle / "platform_adapter" / "__init__.py").write_text(
        '"""Pluggable health-assessment platform adapter (development bundle).\n\nSchema health-assessment-platform-dev/2.0; registry-driven; honest abstain states.\n"""\n',
        encoding="utf-8",
    )
    (bundle / "run_smoke.py").write_text(
        '"""Python fallback for SMOKE_TEST.ps1: runs the three bundle smokes."""\n'
        "import subprocess, sys\n"
        "cmds = [\n"
        '    [sys.executable, "-m", "platform_adapter.cli", "--bundle", ".", "--smoke"],\n'
        '    [sys.executable, "-m", "platform_adapter.cli", "--bundle", ".", "--input", "examples/input_smoke.jsonl"],\n'
        '    [sys.executable, "-m", "platform_adapter.cli", "--bundle", ".", "--replace-drill"],\n'
        "]\n"
        "for cmd in cmds:\n"
        "    result = subprocess.run(cmd, cwd=__import__('pathlib').Path(__file__).parent)\n"
        "    if result.returncode != 0:\n"
        "        sys.exit(result.returncode)\n"
        "print('BUNDLE_SMOKE_ALL_PASS')\n",
        encoding="utf-8",
    )

    # 2) models: copy artifacts
    model_src = root / "health_assessment" / "models" / "improvements" / "p1_component_decision_v3_model_improved_v2_20260910_attempt2"
    copied = 0
    for artifact in sorted(model_src.glob("*.joblib")):
        shutil.copy2(artifact, bundle / "models" / artifact.name)
        copied += 1

    # 3) registry with real hashes from the bundle layout
    registry = ModelRegistry(default_registry(bundle), model_root=bundle)
    registry.to_json(bundle / "model_registry.json")

    # 4) examples
    example_lines = [
        {"run_id": 9001, "session_id": "example", "component_id": "lox_pump", "window_index": 0, "timestamp": 144.9, "hi_cd": 0.96, "hi_ae": 1.0, "anomaly_score": -7.5, "reconstruction_error": 0.0004, "confidence": 0.97},
        {"run_id": 9001, "session_id": "example", "component_id": "lox_pump", "window_index": 1, "timestamp": 146.9, "hi_cd": 0.95, "hi_ae": 1.0, "anomaly_score": -7.2, "confidence": 0.96},
        {"run_id": 9001, "session_id": "example", "component_id": "gas_generator", "window_index": 0, "timestamp": 144.9, "hi_cd": 0.52, "hi_ae": 0.99, "anomaly_score": -6.1, "confidence": 0.95},
        {"run_id": 9001, "session_id": "example", "component_id": "gas_generator", "window_index": 1, "timestamp": 146.9, "hi_cd": 0.50, "hi_ae": 0.99, "anomaly_score": -6.0, "confidence": 0.95},
        "this-line-is-not-json",
        {"run_id": 9001, "session_id": "example", "component_id": "lox_pump", "window_index": 2, "timestamp": 148.9, "hi_cd": 0.31, "hi_true": 0.42},
        {"run_id": 9001, "session_id": "example", "component_id": "mystery_part", "window_index": 0, "timestamp": 148.9, "hi_cd": 0.9, "hi_ae": 1.0, "anomaly_score": 0.1},
        {"action": "summary", "session_id": "example", "run_id": 9001},
    ]
    (bundle / "examples" / "input_smoke.jsonl").write_text(
        "\n".join(line if isinstance(line, str) else json.dumps(line) for line in example_lines) + "\n",
        encoding=CSV_ENCODING,
    )

    # 5) guides + smoke script
    (bundle / "PLATFORM_INTEGRATION_GUIDE.md").write_text(PLATFORM_INTEGRATION_GUIDE, encoding="utf-8")
    (bundle / "MODEL_REPLACEMENT_GUIDE.md").write_text(MODEL_REPLACEMENT_GUIDE, encoding="utf-8")
    (bundle / "SMOKE_TEST.ps1").write_text(
        "# Non-interactive bundle smoke: normal input, bad input, model replacement.\n"
        "$ErrorActionPreference = 'Stop'\n"
        "$python = if ($env:PYTHON) { $env:PYTHON } else { 'python' }\n"
        "Set-Location -Path $PSScriptRoot\n"
        "& $python -m platform_adapter.cli --bundle . --smoke\n"
        "if ($LASTEXITCODE -ne 0) { exit 1 }\n"
        "& $python -m platform_adapter.cli --bundle . --input examples/input_smoke.jsonl --output out_smoke.jsonl\n"
        "if ($LASTEXITCODE -ne 0) { exit 1 }\n"
        "$out = Get-Content out_smoke.jsonl | ForEach-Object { $_ | ConvertFrom-Json }\n"
        "$has_hi = @($out | Where-Object { $_.component_hi -ne $null }).Count -ge 4\n"
        "$has_bad_json = @($out | Where-Object { $_.error -eq 'E_BAD_JSON' }).Count -eq 1\n"
        "$has_forbidden = @($out | Where-Object { $_.error -eq 'E_SCHEMA_FORBIDDEN_FIELD' }).Count -eq 1\n"
        "$has_unknown = @($out | Where-Object { $_.error -eq 'E_UNKNOWN_COMPONENT' }).Count -eq 1\n"
        "$has_summary = @($out | Where-Object { $_.summary_type }).Count -eq 1\n"
        "if (-not ($has_hi -and $has_bad_json -and $has_forbidden -and $has_unknown -and $has_summary)) { exit 2 }\n"
        "& $python -m platform_adapter.cli --bundle . --replace-drill\n"
        "if ($LASTEXITCODE -ne 0) { exit 3 }\n"
        "Write-Host 'BUNDLE_SMOKE_ALL_PASS'\n",
        encoding="utf-8",
    )

    # 6) science metrics (read-only copies of the strict evidence)
    science_sources = {
        "p1_v3_candidates_v2_20260910_attempt2": (
            "fault_alarm_outer_metrics.csv", "component_hi_outer_upgrade.csv",
            "localization_outer_metrics.csv", "localization_top1_bootstrap.csv",
            "inner_selection_2A_all.csv", "inner_selection_2B_all.csv", "inner_selection_2C_all.csv",
        ),
        "p1_component_decision_v3_model_improved_v2_20260910_attempt2": (
            "component_hi_oof_bootstrap_ci.csv", "component_hi_healthy_fa.csv", "component_chosen_table.csv",
        ),
        "p1_v3_strict_baseline_v2_20260910": (
            "fault_alarm_baseline_metrics.csv", "component_hi_baseline_metrics.csv",
            "localization_baseline_metrics.csv", "strict_baseline_diagnostics.csv", "LOCKED_EXPERIMENT_PLAN.yaml",
        ),
    }
    improvements_root = root / "health_assessment" / "outputs" / "improvements"
    for version, files in science_sources.items():
        target_dir = bundle / "science_metrics" / version
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            src = improvements_root / version / name
            if src.exists():
                shutil.copy2(src, target_dir / name)

    # 7) run summary + manifest
    file_hashes: Dict[str, str] = {}
    for path in sorted(bundle.rglob("*")):
        if path.is_file():
            file_hashes[str(path.relative_to(bundle)).replace("\\", "/")] = _sha(path)
    manifest_lines = [f"{digest}  {name}" for name, digest in sorted(file_hashes.items())]
    (bundle / "MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding=CSV_ENCODING)

    summary = {
        "version": BUNDLE_VERSION,
        "task_id": "STAGE4/5 PLUGGABLE PLATFORM DEV BUNDLE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": SCHEMA_VERSION,
        "bundle_dir": str(bundle.relative_to(root)).replace("\\", "/"),
        "release_status": "INTEGRATION_READY_DEVELOPMENT",
        "safety_qualified": False,
        "formal_p1_frozen": False,
        "p4_gate_open": False,
        "p6_gate_open": False,
        "status_inherited": "DEVELOPMENT_ONLY_WITH_FAILED_GATES (fault_alarm 0/7 hard gates; localization NOT_REGISTERED)",
        "files": len(file_hashes),
        "model_artifacts": copied,
        "bundle_build_elapsed_sec": round(time.time() - started, 1),
        "test_discipline": {"test_data_accessed": False, "test_predictions_inspected": False, "test_evaluation_count": 0},
    }
    (output_dir / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
