from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from threading import Lock

from django.conf import settings


class DiagnosisService:
    _instance = None
    _lock = Lock()

    def __init__(self):
        configured_root = os.environ.get("HEALTH_MAIN_DIR")
        if configured_root:
            self.root = Path(configured_root)
        else:
            # Support both the source-tree layout (health-main beside the
            # project) and the self-contained offline delivery layout
            # (health-main inside the project directory).
            candidates = [
                settings.BASE_DIR / "health-main",
                settings.BASE_DIR.parent / "health-main",
                settings.BASE_DIR.parent.parent / "health-main",
            ]
            self.root = next((path for path in candidates if path.exists()), candidates[0])
        self.repo = Path(os.environ.get("HIER14_REPO", settings.BASE_DIR / "integrations" / "algorithm_assets" / "hier14_repo"))
        self.predictor_path = self.root / "backend" / "algotest" / "hier14" / "predictor.py"
        self.error = None
        self.predictor = None
        self._load()

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _load(self):
        if not self.predictor_path.exists():
            self.error = f"Hier14 预测器不存在: {self.predictor_path}"
            return
        try:
            # predictor imports the training repository's ``src`` package.
            # Put the extracted repository on sys.path before loading it.
            if self.repo.exists() and str(self.repo) not in sys.path:
                sys.path.insert(0, str(self.repo))
            # predictor.py resolves its own repository from HIER14_REPO.  Keep
            # the extracted in-project source as the default so deployments do
            # not depend on the developer's original checkout path.
            if self.repo.exists():
                os.environ.setdefault("HIER14_REPO", str(self.repo))
            spec = importlib.util.spec_from_file_location("health_main_hier14_predictor", self.predictor_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            # Load the real runtime at service startup so /status reflects
            # missing weights/dependencies immediately instead of failing on
            # the first user prediction.
            if hasattr(module, "_load_runtime"):
                module._load_runtime()
            self.predictor = module
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"

    @property
    def available(self):
        return self.predictor is not None

    def predict(self, csv_path):
        if not self.predictor:
            raise RuntimeError(self.error or "Hier14 模型未加载")
        # Reject incompatible data without replacing the trained model or poisoning later requests.
        result = self.predictor.predict_scope_csv(str(csv_path))
        result["model_mode"] = "trained-hier14"
        result["model_source"] = str(self.predictor_path)
        aggregate = result.get("aggregate_pred_name") or result.get("pred_name")
        probabilities = result.get("aggregate_class_probs") or result.get("class_probs") or []
        result["confidence"] = next((item["prob"] for item in probabilities if item["name"] == aggregate), None)
        result["latest_confidence"] = next((item["prob"] for item in result.get("class_probs", [])
                                            if item["name"] == result.get("pred_name")), None)
        return result
