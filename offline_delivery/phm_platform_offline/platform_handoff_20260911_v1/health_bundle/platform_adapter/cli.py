"""Platform CLI: file or stdin/stdout JSONL, plus smoke and replacement-drill commands.

    python -m health_assessment.platform_adapter_v2.cli --bundle <bundle_root> --input in.jsonl [--output out.jsonl]
    python -m health_assessment.platform_adapter_v2.cli --bundle <bundle_root> --smoke
    python -m health_assessment.platform_adapter_v2.cli --bundle <bundle_root> --replace-drill
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from .core import BUNDLE_VERSION, HealthAssessmentCore, process_jsonl
from .provenance import load_bundle_provenance
from .registry import ModelRegistry
from .schemas import SCHEMA_VERSION

CSV_ENCODING = "utf-8"


def build_core(bundle_root: Path) -> HealthAssessmentCore:
    bundle_root = Path(bundle_root)
    registry = ModelRegistry.from_json(bundle_root / "model_registry.json", model_root=bundle_root)
    provenance = load_bundle_provenance(bundle_root, SCHEMA_VERSION, BUNDLE_VERSION)
    return HealthAssessmentCore(registry, provenance=provenance)


def _read_lines(args) -> List[str]:
    if args.input:
        return Path(args.input).read_text(encoding=CSV_ENCODING).splitlines()
    return sys.stdin.read().splitlines()


def _write_outputs(args, outputs: List[dict]) -> None:
    payload = "\n".join(json.dumps(record, ensure_ascii=False) for record in outputs)
    if args.output:
        Path(args.output).write_text(payload + "\n", encoding=CSV_ENCODING)
    else:
        sys.stdout.write(payload + "\n")


def run(args) -> int:
    core = build_core(Path(args.bundle))
    outputs = process_jsonl(_read_lines(args), core)
    _write_outputs(args, outputs)
    return 0


def smoke(args) -> int:
    """Non-interactive smoke: one normal window, one bad-JSON line, one
    forbidden-field record, one unknown-component record, a reset and a summary."""
    bundle_root = Path(args.bundle)
    core = build_core(bundle_root)
    lines = [
        json.dumps({"run_id": 9001, "session_id": "smoke", "component_id": "lox_pump", "window_index": 0, "timestamp": 144.9, "hi_cd": 0.96, "hi_ae": 1.0, "anomaly_score": -7.5, "reconstruction_error": 0.0004, "confidence": 0.97}),
        json.dumps({"run_id": 9001, "session_id": "smoke", "component_id": "lox_pump", "window_index": 1, "timestamp": 146.9, "hi_cd": 0.95, "hi_ae": 1.0, "anomaly_score": -7.4, "confidence": 0.97}),
        json.dumps({"run_id": 9001, "session_id": "smoke", "component_id": "gas_generator", "window_index": 0, "timestamp": 144.9, "hi_cd": 0.52, "hi_ae": 0.99, "anomaly_score": -6.0, "confidence": 0.95}),
        "not-json-at-all",
        json.dumps({"run_id": 9001, "session_id": "smoke", "component_id": "lox_pump", "window_index": 2, "timestamp": 148.9, "hi_cd": 0.3, "hi_true": 0.42}),
        json.dumps({"run_id": 9001, "session_id": "smoke", "component_id": " unknown_part", "window_index": 0, "timestamp": 148.9, "hi_cd": 0.9, "hi_ae": 1.0, "anomaly_score": 0.1}),
        json.dumps({"run_id": 9001, "session_id": "smoke", "component_id": "noxzle", "window_index": 0, "timestamp": 148.9, "hi_cd": 0.9, "hi_ae": 1.0, "anomaly_score": 0.1}),
        json.dumps({"action": "summary", "session_id": "smoke", "run_id": 9001}),
        json.dumps({"action": "reset", "session_id": "smoke", "run_id": 9001}),
    ]
    outputs = process_jsonl(lines, core)
    _write_outputs(args, outputs)
    ok = (
        any(record.get("component_id") == "lox_pump" and "component_hi" in record for record in outputs)
        and any(record.get("error") == "E_BAD_JSON" for record in outputs)
        and any(record.get("error") == "E_SCHEMA_FORBIDDEN_FIELD" for record in outputs)
        and any(record.get("error") == "E_UNKNOWN_COMPONENT" for record in outputs)
        and any(record.get("summary_type") for record in outputs)
    )
    status = "SMOKE_PASS" if ok else "SMOKE_FAIL"
    print(status, file=sys.stderr)
    return 0 if ok else 1


def replace_drill(args) -> int:
    """Model-replacement drill: register a dummy next-version component_hi
    adapter for one component WITHOUT changing the client input, run the same
    input through, and prove the outputs reflect the new model while the schema
    and the other heads are untouched.  Also proves a hash mismatch refuses the
    artifact and falls back safely."""
    from .adapters import CH2ComponentHiAdapter
    from .registry import RegistryEntry

    bundle_root = Path(args.bundle)
    core = build_core(bundle_root)
    component = "gas_generator"
    base_line = {"run_id": 9002, "session_id": "drill", "component_id": component, "window_index": 0, "timestamp": 144.9, "hi_cd": 0.52, "hi_ae": 0.99, "anomaly_score": -6.0, "confidence": 0.95}

    before = core.process_record(dict(base_line))
    core.reset("drill", 9002)  # replay the same window through the replacement

    class DummyNextVersionAdapter(CH2ComponentHiAdapter):
        model_name = "dummy_next_version"
        model_version = "CH-2a@z5.0-next-dummy"

        def infer(self, record):
            # a stand-in "new model": deterministic function of the same input
            return {"component_hi": 0.42, "component_hi_source": f"p1v3:{self.model_version}", "component_hi_status": "qualified"}

    core.swap_adapter("component_hi", component, DummyNextVersionAdapter(component))
    after = core.process_record(dict(base_line))
    core.reset("drill", 9002)

    ok = (
        before["component_hi"] != after["component_hi"]
        and "dummy" in after["component_hi_source"].lower()
        and before["schema_version"] == after["schema_version"]
        and before["anomaly_score"] == after["anomaly_score"]
        and before["fault_alarm_status"] == after["fault_alarm_status"]
    )

    # hash mismatch drill: corrupt the registry entry for one artifact
    entry = core.registry.get("component_hi", "kerosene_valve")
    tampered = RegistryEntry(
        head=entry.head, component_id=entry.component_id, model_name=entry.model_name,
        model_version=entry.model_version + "-tampered", artifact=entry.artifact,
        sha256="0" * 64, qualification=entry.qualification, fallback_head="component_hi_frozen_cdPCA",
        notes="tampered hash for drill",
    )
    core.registry.entries[(tampered.head, tampered.component_id)] = tampered
    resolved, events = core.registry.resolve("component_hi", "kerosene_valve")
    hash_rejected = any(event.startswith("E_HASH_MISMATCH") for event in events)
    core.swap_adapter("component_hi", "kerosene_valve", core.factory.build(resolved))
    fallback_record = core.process_record({**base_line, "component_id": "kerosene_valve", "window_index": 1})
    ok = ok and hash_rejected and fallback_record["component_hi_source"] == "frozen_cdPCA_mini84"

    report = {
        "schema_version": SCHEMA_VERSION,
        "drill": "model_replacement",
        "client_input_changed": False,
        "schema_changed": False,
        "new_model_reflected": before["component_hi"] != after["component_hi"],
        "hash_mismatch_refused": hash_rejected,
        "fallback_engaged": fallback_record["component_hi_source"] == "frozen_cdPCA_mini84",
        "result": "REPLACE_DRILL_PASS" if ok else "REPLACE_DRILL_FAIL",
    }
    _write_outputs(args, [report])
    print(report["result"], file=sys.stderr)
    return 0 if ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="health-assessment platform adapter (dev bundle)")
    parser.add_argument("--bundle", type=str, required=True)
    parser.add_argument("--input", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--replace-drill", action="store_true", dest="replace_drill")
    args = parser.parse_args(argv)
    if args.smoke:
        return smoke(args)
    if args.replace_drill:
        return replace_drill(args)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
