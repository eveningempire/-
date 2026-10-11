import csv
import hashlib
import json
import platform
import time
from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from datasets.models import Dataset
from datasets.schema import column_roles
from fault_diagnosis.evaluation import FAULT_NAMES, score_windows, summarize
from fault_diagnosis.service import DiagnosisService
from fault_diagnosis.views import _run_algorithm
from simulation_demo.models import FaultWorkflowTask


class Command(BaseCommand):
    help = "Evaluate imported/generated simulation CSVs using real model outputs and separate fault truth."

    def add_arguments(self, parser):
        parser.add_argument("--algorithms", nargs="+", default=["hier14", "msfg_teams_rt", "pca_iforest"])
        parser.add_argument("--representative", action="store_true", help="All baselines plus one deterministic raw/derived pair per fault category")
        parser.add_argument("--dataset-ids", nargs="+", type=int)
        parser.add_argument("--report-dir", type=Path, required=True)
        parser.add_argument("--threads", type=int, default=4)

    def handle(self, *args, **options):
        import sklearn
        import torch
        torch.set_num_threads(options["threads"])
        algorithms = options["algorithms"]
        if any(key not in {"hier14", "msfg_teams_rt", "pca_iforest"} for key in algorithms):
            raise CommandError("Unsupported diagnosis algorithm")
        manifest = Path(settings.MEDIA_ROOT) / "datasets" / "simulate_data_+1" / "import_manifest.json"
        entries = json.loads(manifest.read_text(encoding="utf-8"))["files"]
        by_file = {entry["file"]: entry for entry in entries}
        datasets = {dataset.file.name: dataset for dataset in Dataset.objects.filter(file__in=by_file)}
        cases = []
        for filename, entry in by_file.items():
            dataset = datasets.get(filename)
            if not dataset:
                raise CommandError(f"Registered CSV missing: {filename}")
            cases.append({"dataset": dataset, "category": entry["category"], "expected_fault": FAULT_NAMES[entry["category"]],
                          "data_type": "derived" if len(entry["parameter_columns"]) == 17 else "raw",
                          "source": "customer_archive", "expected_sha256": entry["sha256"]})
        if options["representative"]:
            picked = []
            for category in FAULT_NAMES:
                category_cases = [case for case in cases if case["category"] == category]
                if category == "baseline":
                    picked.extend(category_cases)
                else:
                    for kind in ("raw", "derived"):
                        matching = sorted((case for case in category_cases if case["data_type"] == kind),
                                          key=lambda case: (case["dataset"].launch_number, case["dataset"].injection_time, case["dataset"].id))
                        picked.append(matching[0])
            cases = picked
        for task in FaultWorkflowTask.objects.filter(simulation_backend="simulink", status="completed"):
            for export in task.simulation_output.get("datasets", []):
                dataset = Dataset.objects.get(pk=export["dataset_id"])
                cases.append({"dataset": dataset, "category": next((key for key, name in FAULT_NAMES.items() if name == task.fault_mode), "baseline"),
                              "expected_fault": "正常" if task.fault_mode == "无故障" else task.fault_mode,
                              "data_type": "raw" if len(export["parameter_columns"]) == 29 else "derived",
                              "source": "new_simulink_run", "expected_sha256": None})
        if options["dataset_ids"]:
            cases = [case for case in cases if case["dataset"].id in options["dataset_ids"]]
        if not cases:
            raise CommandError("No datasets selected")
        directory = options["report_dir"].resolve()
        directory.mkdir(parents=True, exist_ok=True)
        runtime = DiagnosisService.instance() if "hier14" in algorithms else None
        provenance = {"python": platform.python_version(), "torch": torch.__version__, "sklearn": sklearn.__version__,
                      "algorithms": algorithms, "files": len(cases), "representative": options["representative"],
                      "hier14_available": runtime.available if runtime else None,
                      "training_overlap": "unknown; customer archive may overlap model training data; this is integration evaluation, not an independent holdout",
                      "truth_rule": "FaultFlag used only by scorer; homogeneous windows evaluated, transition windows omitted; no phase/maturity filtering",
                      "inference_changes": "no retraining or threshold tuning; original checkpoint preprocessing retained"}
        if runtime:
            artifact_root = runtime.predictor_path.parent / "checkpoints"
            provenance["artifacts"] = {name: hashlib.sha256((artifact_root/name).read_bytes()).hexdigest()
                                       for name in ("best_model.pth", "scaler.pkl", "deploy_meta.json") if (artifact_root/name).is_file()}
        records = []
        started = time.perf_counter()
        with (directory / "records.jsonl").open("w", encoding="utf-8") as stream:
            for index, case in enumerate(cases):
                dataset = case["dataset"]
                path = Path(dataset.file.path)
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if case["expected_sha256"] and digest != case["expected_sha256"]:
                    raise CommandError(f"Dataset #{dataset.id} differs from imported manifest")
                frame = pd.read_csv(path)
                roles = column_roles(frame.columns)
                for algorithm in algorithms:
                    record = {"dataset_id": dataset.id, "file": dataset.file.name, "sha256": digest,
                              "category": case["category"], "expected_fault": case["expected_fault"],
                              "data_type": case["data_type"], "source": case["source"], "algorithm": algorithm,
                              "rows": len(frame), "parameter_columns": roles["parameter_columns"]}
                    tick = time.perf_counter()
                    try:
                        result = _run_algorithm(algorithm, path)
                        record.update({"status": "success", "model_mode": result.get("model_mode"),
                                       "aggregate_predicted": result.get("aggregate_pred_name") or result["pred_name"],
                                       "latest_predicted": result["pred_name"], "confidence": result.get("confidence"),
                                       "windows": score_windows(frame, result, case["expected_fault"]),
                                       "input_columns_verified": roles["parameter_columns"]})
                    except Exception as exc:
                        record.update({"status": "error", "error": f"{type(exc).__name__}: {exc}", "windows": []})
                    record["seconds"] = round(time.perf_counter()-tick, 4)
                    records.append(record)
                    stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False)+"\n")
                    stream.flush()
                if (index+1) % 10 == 0 or index+1 == len(cases):
                    self.stdout.write(f"Evaluated {index+1}/{len(cases)}, elapsed {time.perf_counter()-started:.1f}s")
                    self.stdout.flush()
        summary = summarize(records)
        (directory / "summary.json").write_text(json.dumps({"provenance": provenance, "metrics": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
        with (directory / "files.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            fields = ["dataset_id", "algorithm", "data_type", "source", "expected_fault", "status", "aggregate_predicted", "latest_predicted", "confidence", "seconds", "error"]
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(records)
        self.stdout.write(json.dumps(summary, ensure_ascii=True))
        self.stdout.write(f"Report: {directory}")
