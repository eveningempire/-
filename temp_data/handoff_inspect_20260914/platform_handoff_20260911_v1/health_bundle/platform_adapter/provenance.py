"""Provenance: schema/config/model/input trace hashing (no local paths leaked)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional


def _short(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def input_trace_hash(parsed_record: Dict) -> str:
    canonical = json.dumps(parsed_record, sort_keys=True, separators=(",", ":"))
    return _short(canonical)


class Provenance:
    """Bundle-level provenance bound into every output record."""

    def __init__(self, *, schema_version: str, bundle_version: str, config: Dict, registry_hashes: Dict[str, str]) -> None:
        self.schema_version = schema_version
        self.bundle_version = bundle_version
        self.config_hash = _short(json.dumps(config, sort_keys=True))
        self.registry_hashes = dict(registry_hashes)
        self.combined = _short(json.dumps({"schema": schema_version, "bundle": bundle_version, "config": config, "models": registry_hashes}, sort_keys=True))

    def record_trace(self, parsed_record: Dict) -> str:
        return _short(json.dumps({"bundle": self.combined, "input": input_trace_hash(parsed_record)}, sort_keys=True))

    def to_dict(self) -> Dict:
        return {
            "schema_version": self.schema_version,
            "bundle_version": self.bundle_version,
            "config_hash": self.config_hash,
            "model_hashes": {key: value[:16] for key, value in self.registry_hashes.items()},
            "provenance_hash": self.combined,
        }


def load_bundle_provenance(bundle_root: Path, schema_version: str, bundle_version: str) -> Provenance:
    """Build provenance from the bundle's registry file (hashes verified by the caller)."""
    registry_path = Path(bundle_root) / "model_registry.json"
    doc = json.loads(registry_path.read_text(encoding="utf-8"))
    registry_hashes = {
        f"{entry['head']}:{entry['component_id']}:{entry['model_version']}": entry.get("sha256") or "builtin"
        for entry in doc.get("entries", [])
    }
    config = {"schema_version": schema_version, "registry_schema": doc.get("schema_version"), "entry_count": len(doc.get("entries", []))}
    return Provenance(schema_version=schema_version, bundle_version=bundle_version, config=config, registry_hashes=registry_hashes)
