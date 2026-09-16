"""Lazy bridge to the read-only platform handoff bundle."""

from __future__ import annotations

import importlib
import sys
import warnings
from pathlib import Path
from threading import Lock

from django.conf import settings


class PlatformUnavailable(RuntimeError):
    pass


class HealthAssessmentService:
    _instance = None
    _lock = Lock()

    def __init__(self):
        self.bundle = Path(settings.PHM_PLATFORM_HANDOFF_DIR) / "health_bundle"
        self.core = None
        self.error = None
        self.warnings = []
        self.runtime = {}
        self._load()

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _load(self):
        if not settings.PHM_HEALTH_ASSESSMENT_ENABLED:
            self.error = "health assessment integration is disabled"
            return
        if not (self.bundle / "model_registry.json").exists():
            self.error = f"bundle not found: {self.bundle}"
            return
        try:
            import joblib
            import numpy
            import sklearn
            import scipy
            self.runtime = {
                "python": sys.version.split()[0],
                "joblib": joblib.__version__,
                "numpy": numpy.__version__,
                "scikit_learn": sklearn.__version__,
                "scipy": scipy.__version__,
                "model_scikit_learn": "1.9.0",
            }
            if sklearn.__version__ != "1.9.0":
                self.warnings.append(
                    "模型由 scikit-learn 1.9.0 生成；当前运行时版本不同。"
                    "推理已通过冒烟测试，但正式部署应升级至 Python 3.11+ 并使用匹配版本。"
                )
            parent = str(self.bundle)
            if parent not in sys.path:
                sys.path.insert(0, parent)
            registry_mod = importlib.import_module("platform_adapter.registry")
            core_mod = importlib.import_module("platform_adapter.core")
            provenance_mod = importlib.import_module("platform_adapter.provenance")
            schemas_mod = importlib.import_module("platform_adapter.schemas")
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                registry = registry_mod.ModelRegistry.from_json(
                    self.bundle / "model_registry.json", model_root=self.bundle
                )
                provenance = provenance_mod.load_bundle_provenance(
                    self.bundle, schemas_mod.SCHEMA_VERSION, core_mod.BUNDLE_VERSION
                )
                self.core = core_mod.HealthAssessmentCore(registry, provenance=provenance)
                self.warnings.extend(str(item.message) for item in caught)
        except Exception as exc:  # dependency/model failures are reported by status API
            self.error = f"{type(exc).__name__}: {exc}"

    @property
    def available(self):
        return self.core is not None

    def require(self):
        if not self.core:
            raise PlatformUnavailable(self.error or "platform adapter unavailable")
        return self.core
