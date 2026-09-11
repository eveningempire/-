"""Lazy bridge to the read-only platform handoff bundle."""

from __future__ import annotations

import importlib
import sys
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
            parent = str(self.bundle)
            if parent not in sys.path:
                sys.path.insert(0, parent)
            registry_mod = importlib.import_module("platform_adapter.registry")
            core_mod = importlib.import_module("platform_adapter.core")
            provenance_mod = importlib.import_module("platform_adapter.provenance")
            schemas_mod = importlib.import_module("platform_adapter.schemas")
            registry = registry_mod.ModelRegistry.from_json(
                self.bundle / "model_registry.json", model_root=self.bundle
            )
            provenance = provenance_mod.load_bundle_provenance(
                self.bundle, schemas_mod.SCHEMA_VERSION, core_mod.BUNDLE_VERSION
            )
            self.core = core_mod.HealthAssessmentCore(registry, provenance=provenance)
        except Exception as exc:  # dependency/model failures are reported by status API
            self.error = f"{type(exc).__name__}: {exc}"

    @property
    def available(self):
        return self.core is not None

    def require(self):
        if not self.core:
            raise PlatformUnavailable(self.error or "platform adapter unavailable")
        return self.core
