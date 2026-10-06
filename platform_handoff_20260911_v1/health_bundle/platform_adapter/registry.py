"""Model registry: pluggable, data-driven, hash-verified model entries.

Replacing a model means adding an artifact file plus a registry entry - the
platform Schema, core orchestration and callers never change.  Every entry
carries sha256 + qualification; the loader verifies the hash and refuses
(reports + falls back) on mismatch or absence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .schemas import COMPONENT_IDS

REGISTRY_SCHEMA_VERSION = "health-assessment-platform-registry/2.0"


@dataclass(frozen=True)
class RegistryEntry:
    head: str
    component_id: str
    model_name: str
    model_version: str
    artifact: Optional[str]          # bundle-relative path or None for built-in/reference heads
    sha256: Optional[str]
    qualification: str               # qualified | fallback | abstain | development_only_not_registered
    fallback_head: str               # head used when this entry fails
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "head": self.head,
            "component_id": self.component_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "artifact": self.artifact,
            "sha256": self.sha256,
            "qualification": self.qualification,
            "fallback_head": self.fallback_head,
            "notes": self.notes,
        }


def default_registry(model_root: Path) -> List[RegistryEntry]:
    """Registry for the frozen v2 20260910 science outcome.

    Fallback chains are explicit registry entries under synthetic head names:
    component_hi (qualified CH-2a@z5.0, six components) -> component_hi_frozen_cdPCA
    (frozen CDPCA reference; also the registered entry for lox_pump) ->
    component_hi_abstain (terminal).  fault_alarm is ABSTAIN for all components;
    localization LC-2a -> localization_abstain (terminal).
    """
    qualified_hi = ("combustion_chamber", "gas_generator", "kerosene_pipeline", "kerosene_valve", "nozzle", "oxygen_turbine")
    entries: List[RegistryEntry] = []
    for component in COMPONENT_IDS:
        if component in qualified_hi:
            artifact = Path("models") / f"component_hi_{component}_CH-2a_z5.0.joblib"
            entries.append(
                RegistryEntry(
                    head="component_hi", component_id=component,
                    model_name="p1v3_ch2_collapse_gate", model_version="CH-2a@z5.0",
                    artifact=str(artifact), sha256=_hash_if_exists(model_root / artifact),
                    qualification="qualified", fallback_head="component_hi_frozen_cdPCA",
                    notes="strict outer-OOF approved 20260910; deployment_candidate_only",
                )
            )
        else:
            entries.append(
                RegistryEntry(
                    head="component_hi", component_id=component,
                    model_name="frozen_cdPCA_mini84", model_version="external_frozen",
                    artifact=None, sha256=None,
                    qualification="fallback", fallback_head="component_hi_frozen_cdPCA",
                    notes="incumbent retained; CH candidate failed hit non-inferiority",
                )
            )
        entries.append(
            RegistryEntry(
                head="component_hi_frozen_cdPCA", component_id=component,
                model_name="frozen_cdPCA_mini84", model_version="external_frozen",
                artifact=None, sha256=None,
                qualification="fallback", fallback_head="component_hi_abstain",
                notes="frozen CDPCA score passthrough (hi_cd)",
            )
        )
        entries.append(
            RegistryEntry(
                head="fault_alarm", component_id=component,
                model_name="raw_anomaly_score_abstain", model_version="abstain_v2_20260910",
                artifact=None, sha256=None,
                qualification="abstain", fallback_head="fault_alarm_abstain",
                notes="0/7 components passed registered hard gates; anomaly_score stays the audited output",
            )
        )
        entries.append(
            RegistryEntry(
                head="localization", component_id=component,
                model_name="p1v3_lc2_supervised_zfusion", model_version="LC-2a",
                artifact=str(Path("models") / f"localization_{component}_LC-2a.joblib"),
                sha256=_hash_if_exists(model_root / Path("models") / f"localization_{component}_LC-2a.joblib"),
                qualification="development_only_not_registered", fallback_head="localization_abstain",
                notes="threshold NOT_REGISTERED; development evidence only",
            )
        )
    # terminal abstain endpoints (never fail to resolve)
    for component in COMPONENT_IDS:
        for head in ("component_hi_abstain", "fault_alarm_abstain", "localization_abstain"):
            entries.append(
                RegistryEntry(
                    head=head, component_id=component,
                    model_name="abstain", model_version="terminal",
                    artifact=None, sha256=None,
                    qualification="abstain", fallback_head=head,
                    notes="terminal fallback: no model value emitted beyond raw evidence",
                )
            )
    return entries


def _hash_if_exists(path: Path) -> Optional[str]:
    path = Path(path)
    if path.exists():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return None


class ModelRegistry:
    """Hash-verifying registry over (head, component) entries."""

    def __init__(self, entries: List[RegistryEntry], model_root: Path) -> None:
        self.model_root = Path(model_root)
        self.entries: Dict[Tuple[str, str], RegistryEntry] = {}
        for entry in entries:
            self.entries[(entry.head, entry.component_id)] = entry
        self.events: List[dict] = []

    @classmethod
    def from_json(cls, registry_path: Path, model_root: Path) -> "ModelRegistry":
        doc = json.loads(Path(registry_path).read_text(encoding="utf-8"))
        if doc.get("schema_version") != REGISTRY_SCHEMA_VERSION:
            raise ValueError(f"registry schema mismatch: {doc.get('schema_version')}")
        entries = [RegistryEntry(**item) for item in doc["entries"]]
        return cls(entries, model_root)

    def to_json(self, path: Path) -> None:
        doc = {"schema_version": REGISTRY_SCHEMA_VERSION, "entries": [entry.to_dict() for entry in self.entries.values()]}
        Path(path).write_text(json.dumps(doc, indent=2), encoding="utf-8")

    def get(self, head: str, component_id: str) -> RegistryEntry:
        return self.entries[(head, component_id)]

    def resolve(self, head: str, component_id: str) -> Tuple[RegistryEntry, List[str]]:
        """Resolve an entry to a loadable artifact, following fallbacks.

        Returns (effective_entry, event_list); events carry any hash/absence
        errors encountered so the output stays auditable.
        """
        events: List[str] = []
        seen = 0
        entry = self.get(head, component_id)
        while seen < 8:
            seen += 1
            if entry.qualification == "abstain":
                return entry, events
            if entry.artifact is None:
                return entry, events
            path = self.model_root / entry.artifact
            if not path.exists():
                events.append(f"E_ARTIFACT_MISSING:{entry.head}:{component_id}:{entry.model_version}")
                entry = self.get(entry.fallback_head, component_id)
                continue
            digest = _hash_if_exists(path)
            if entry.sha256 and digest != entry.sha256:
                events.append(f"E_HASH_MISMATCH:{entry.head}:{component_id}:{entry.model_version}")
                entry = self.get(entry.fallback_head, component_id)
                continue
            if entry.qualification in ("fallback", "development_only_not_registered", "qualified"):
                return entry, events
            events.append(f"E_NOT_QUALIFIED:{entry.head}:{component_id}:{entry.model_version}")
            entry = self.get(entry.fallback_head, component_id)
        return self.get(entry.fallback_head, component_id), events
