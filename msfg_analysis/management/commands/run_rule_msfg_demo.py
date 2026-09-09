from __future__ import annotations

from typing import Dict, Any, List
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from data_management.models import PHM, PHMData
from rule_detection.service import evaluate_rules_for_data_point
from msfg_analysis.models import MSFGDefinition, MSFGAnalysisResult
from msfg_analysis.algorithms.msfg.fusion import fuse_test_to_fault, summarize_system


class Command(BaseCommand):
    help = "Run a demo pipeline: evaluate rules on recent PHM data, aggregate to test scores, fuse via MSFG, and store results."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--cmg-id", required=True, help="Target PHM ID, e.g., PHM-01")
        parser.add_argument("--limit", type=int, default=50, help="Number of recent data points to process")

    def handle(self, *args, **options):
        cmg_id: str = options["cmg_id"]
        limit: int = options["limit"]

        try:
            cmg = PHM.objects.get(cmg_id=cmg_id)
        except PHM.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"PHM {cmg_id} not found"))
            return

        msfg = (
            MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True)
            .order_by("-updated_at")
            .first()
        )
        if not msfg:
            self.stderr.write(self.style.WARNING("No active MSFGDefinition found. Proceeding without fusion."))

        # Build maps for fusion if available
        test_name_by_id: Dict[str, str] = {}
        fault_name_by_id: Dict[str, str] = {}
        edges: List[tuple[str, str]] = []
        if msfg:
            nodes = list(msfg.nodes.all())
            edges_qs = list(msfg.edges.all())
            test_name_by_id = {n.node_id: n.name for n in nodes if n.node_type == "test"}
            fault_name_by_id = {n.node_id: n.name for n in nodes if n.node_type == "fault"}
            edges = [(e.source_node.node_id, e.target_node.node_id) for e in edges_qs]

        qs = (
            PHMData.objects.filter(cmg=cmg)
            .order_by("-timestamp")[:limit]
        )
        data_points = list(qs)[::-1]  # oldest first

        self.stdout.write(self.style.SUCCESS(f"Processing {len(data_points)} points for {cmg_id}"))

        count_ok = 0
        for dp in data_points:
            # 1) Evaluate rules and persist RuleDetectionResult(s)
            rule_results = evaluate_rules_for_data_point(dp)

            # 2) Aggregate to test_scores by parameter
            # related_parameters may be empty; use rule->score as proxy
            test_scores: Dict[str, float] = {}
            for rr in rule_results:
                score = float(rr.get("score", 0.0))
                rel_params = rr.get("related_parameters") or []
                if not rel_params:
                    # If rule doesn't expose related params, skip from test mapping
                    continue
                for pname in rel_params:
                    test_scores[pname] = max(test_scores.get(pname, 0.0), score)

            fault_scores: Dict[str, float] = {}
            system_summary: Dict[str, Any] = {"overall_health": 1.0}
            if msfg and edges:
                fault_scores = fuse_test_to_fault(test_scores, edges, test_name_by_id, fault_name_by_id)
                system_summary = summarize_system(fault_scores)

            # 3) Persist MSFGAnalysisResult
            MSFGAnalysisResult.objects.create(
                data_point=dp,
                msfg_definition=msfg,
                test_results=test_scores,
                fault_results=fault_scores,
                system_results=system_summary,
                overall_health_score=float(system_summary.get("overall_health", 1.0)),
                detected_faults=[k for k, v in fault_scores.items() if v > 0.35],  # 涓庝富绠楁硶淇濇寔涓€鑷?
                analysis_details={"rule_count": len(rule_results)},
            )
            count_ok += 1

        self.stdout.write(self.style.SUCCESS(f"Done. Stored {count_ok} MSFGAnalysisResult rows."))



