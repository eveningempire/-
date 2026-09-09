"""
Deprecated placeholder IMS algorithm. This module is intentionally left in
place to avoid import errors; the real implementation is in
health_management/algorithms/IMS and is invoked via ims_service/ims_worker.
"""

from __future__ import annotations

from typing import List, Dict, Any


def detect_anomalies(data_matrix: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    raise NotImplementedError("Use health_management.ims_service with real IMS models instead")