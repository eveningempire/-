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
        self.root = Path(os.environ.get("HEALTH_MAIN_DIR", settings.BASE_DIR.parent.parent / "health-main"))
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
            spec = importlib.util.spec_from_file_location("health_main_hier14_predictor", self.predictor_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            self.predictor = module
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"

    @property
    def available(self):
        return self.predictor is not None

    def predict(self, csv_path):
        if not self.predictor:
            raise RuntimeError(self.error or "诊断模型不可用")
        return self.predictor.predict_scope_csv(str(csv_path))
