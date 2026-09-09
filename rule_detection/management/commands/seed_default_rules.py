from __future__ import annotations

from typing import Dict, List, Any, Optional
from collections import defaultdict
import math

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from data_management.models import PHMModel, PHMData
from rule_detection.models import FaultDefinition, RuleDefinition


def is_number(x: Any) -> bool:
    try:
        float(x)
        return True
    except Exception:
        return False


class Command(BaseCommand):
    help = "Seed default expert rules for PHM models based on recent data statistics (mean+3sigma bounds)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--cmg-model-id", type=int, help="Target PHMModel ID; omit to seed for all models")
        parser.add_argument("--window", type=int, default=500, help="Recent data window size per PHM model")
        parser.add_argument("--num-params", type=int, default=6, help="Maximum number of parameters to create rules for")
        parser.add_argument("--sigma", type=float, default=3.0, help="Sigma multiplier for high threshold rule")

    def handle(self, *args, **options):
        cmg_model_id: Optional[int] = options.get("cmg_model_id")
        window: int = options["window"]
        num_params: int = options["num_params"]
        sigma: float = options["sigma"]

        models = list(PHMModel.objects.all()) if not cmg_model_id else [PHMModel.objects.get(id=cmg_model_id)]
        total_rules = 0
        for model in models:
            # Gather recent data across all PHMs of this model
            qs = (
                PHMData.objects.filter(cmg__cmg_model=model)
                .order_by("-timestamp")[:window]
            )
            rows = list(qs)
            if not rows:
                self.stdout.write(self.style.WARNING(f"No data for {model.model_name}; skip"))
                continue

            # Collect numeric series per parameter
            series: Dict[str, List[float]] = defaultdict(list)
            for dp in rows:
                data = dp.data or {}
                for k, v in data.items():
                    if is_number(v):
                        try:
                            series[k].append(float(v))
                        except Exception:
                            continue

            if not series:
                self.stdout.write(self.style.WARNING(f"No numeric parameters for {model.model_name}; skip"))
                continue

            # Rank parameters by variance
            stats: List[tuple[str, float, float, float]] = []  # (name, mean, std, var)
            for k, vals in series.items():
                if len(vals) < 10:
                    continue
                m = sum(vals) / len(vals)
                var = sum((x - m) ** 2 for x in vals) / max(1, len(vals) - 1)
                std = math.sqrt(var)
                stats.append((k, m, std, var))

            stats.sort(key=lambda t: t[3], reverse=True)
            chosen = stats[:num_params]
            if not chosen:
                self.stdout.write(self.style.WARNING(f"No sufficient variance parameters for {model.model_name}; skip"))
                continue

            with transaction.atomic():
                created = 0
                for idx, (pname, mean, std, var) in enumerate(chosen, start=1):
                    high = mean + sigma * std
                    fault_name = f"{pname}瓒婁笂闄?
                    fault_def, _ = FaultDefinition.objects.get_or_create(
                        cmg_model=model,
                        fault_name=fault_name,
                        defaults={
                            "fault_level": 2,
                            "component": "",
                            "description": f"榛樿瑙勫垯: {pname} > {high:.3f}",
                        },
                    )
                    rule_id = f"P_HIGH_{idx:02d}"
                    RuleDefinition.objects.update_or_create(
                        cmg_model=model,
                        rule_id=rule_id,
                        defaults={
                            "fault_definition": fault_def,
                            "rule_expression": f"{pname} > {high:.6f}",
                            "source": "expert",
                            "plan_description": f"{pname}瓒呰繃闃堝€?{high:.3f}",
                            "is_online": True,
                            "is_new": False,
                            "is_editable": True,
                            "related_parameters": [pname],
                        },
                    )
                    created += 1

                total_rules += created
                self.stdout.write(self.style.SUCCESS(f"Seeded {created} rules for {model.model_name}"))

        self.stdout.write(self.style.SUCCESS(f"Completed. Total rules seeded: {total_rules}"))



