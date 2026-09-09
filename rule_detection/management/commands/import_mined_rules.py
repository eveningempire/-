from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from django.core.management.base import BaseCommand, CommandError

from data_management.models import PHMModel
from rule_detection.models import FaultDefinition, RuleDefinition


def _load_rules(path: Path) -> List[Dict[str, Any]]:
    """Load mined rules file. Expect JSON/YAML list with schema:
    [
      {
        "fault": "BreakLu",
        "comb": "AND" | "OR",
        "thresholds": { "VarA": {"tau": 1.23, "dir": "+"}, ... }
      }, ...
    ]
    """
    if not path.exists():
        raise CommandError(f"Rules file not found: {path}")
    if path.suffix.lower() in {".yml", ".yaml"}:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise CommandError("Unsupported file type. Use .json or .yaml")

    if not isinstance(data, list):
        raise CommandError("Rules file must be a list of rule objects")
    return data


def _build_expression(rule_obj: Dict[str, Any]) -> str:
    """Convert mined rule to platform expression string.

    E.g., thresholds: {A:{tau:2.0,dir:"+"}, B:{tau:1.0,dir:"-"}}, comb=AND 鈫?
          "(A >= 2.0) and (B <= 1.0)"
    """
    comb = str(rule_obj.get("comb", "AND")).upper()
    glue = " and " if comb == "AND" else " or "
    parts: List[str] = []
    thresholds: Dict[str, Dict[str, Any]] = rule_obj.get("thresholds") or {}
    for var, cfg in thresholds.items():
        try:
            tau = float(cfg.get("tau"))
        except Exception:
            continue
        direction = str(cfg.get("dir", "+"))
        op = ">=" if direction == "+" else "<="
        parts.append(f"({var} {op} {tau:.6g})")
    return glue.join(parts) if parts else ""


class Command(BaseCommand):
    help = "Import mined rules (YAML/JSON) into RuleDefinition/FaultDefinition for a PHM model."

    def add_arguments(self, parser):
        parser.add_argument("--cmg-model-id", type=int, required=True, help="Target PHMModel ID")
        parser.add_argument("--file", type=str, required=True, help="Path to mined rules file (.json/.yaml)")
        parser.add_argument("--rule-id-prefix", type=str, default="MINE", help="Prefix for generated rule_id")
        parser.add_argument("--fault-level", type=int, default=2, help="Default fault level if not provided")
        parser.add_argument("--set-online", action="store_true", help="Mark imported rules as online")
        parser.add_argument("--purge-data-driven", action="store_true", help="Remove existing data_driven rules for this PHM model before import")

    def handle(self, *args, **options):
        cmg_model_id = options["cmg_model_id"]
        file_path = Path(options["file"]).expanduser().resolve()
        rule_id_prefix = str(options["rule_id_prefix"]).strip()
        default_fault_level = int(options["fault_level"])
        set_online: bool = bool(options["set_online"]) or False
        purge_old: bool = bool(options["purge_data_driven"]) or False

        try:
            cmg_model = PHMModel.objects.get(id=cmg_model_id)
        except PHMModel.DoesNotExist:
            raise CommandError(f"PHMModel {cmg_model_id} not found")

        rules = _load_rules(file_path)

        if purge_old:
            deleted, _ = RuleDefinition.objects.filter(cmg_model=cmg_model, source="data_driven").delete()
            self.stdout.write(self.style.WARNING(f"Purged {deleted} existing data_driven rules"))

        created_count = 0
        updated_count = 0
        idx_counter: Dict[str, int] = {}

        for obj in rules:
            fault_name = str(obj.get("fault") or "").strip()
            if not fault_name:
                self.stderr.write("Skip rule without fault name")
                continue

            # Fault definition
            fault_level = int(obj.get("fault_level", default_fault_level))
            component = str(obj.get("component") or "").strip()
            fault_def, _ = FaultDefinition.objects.get_or_create(
                cmg_model=cmg_model,
                fault_name=fault_name,
                defaults={
                    "fault_level": fault_level,
                    "component": component,
                    "description": f"Imported from {file_path.name}",
                },
            )
            # Update level/component if provided
            changed = False
            if fault_def.fault_level != fault_level:
                fault_def.fault_level = fault_level
                changed = True
            if component and fault_def.component != component:
                fault_def.component = component
                changed = True
            if changed:
                fault_def.save()

            # Build expression
            expr = _build_expression(obj)
            if not expr:
                self.stderr.write(f"Skip empty expression for fault {fault_name}")
                continue

            # related params
            related_params = list((obj.get("thresholds") or {}).keys())

            # Unique rule_id per fault
            idx_counter[fault_name] = idx_counter.get(fault_name, 0) + 1
            rule_id = f"{rule_id_prefix}_{fault_name}_{idx_counter[fault_name]}"

            # Upsert RuleDefinition by (cmg_model, rule_id)
            rd, created = RuleDefinition.objects.update_or_create(
                cmg_model=cmg_model,
                rule_id=rule_id,
                defaults={
                    "fault_definition": fault_def,
                    "rule_expression": expr,
                    "source": "data_driven",
                    "plan_description": obj.get("plan_description", ""),
                    "is_online": bool(set_online),
                    "is_new": True,
                    "is_editable": True,
                    "related_parameters": related_params,
                    "compiled_rule": None,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Imported rules: created={created_count}, updated={updated_count} (model={cmg_model.model_name})"
        ))



