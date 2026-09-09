"""
Adapter for legacy IMS (cluster-radius based) detector saved as joblib.

This adapter loads a legacy IMSDetector (joblib-saved dict) and exposes
an onlineValidate(dataFrame, time_) method compatible with current pipeline.
"""
from __future__ import annotations

import os
import tempfile
from typing import Dict, List

import joblib  # type: ignore
import numpy as np


class _LegacyIMSDetector:
    """Minimal loader compatible with delete/IMS/IMS.py IMSDetector.save format.

    That class saved only self.__dict__ via joblib.dump, so we just need
    an object to hold attributes.
    """

    def __init__(self) -> None:
        pass

    @classmethod
    def load_from_file(cls, path: str) -> "_LegacyIMSDetector":
        obj = cls.__new__(cls)
        obj.__dict__.update(joblib.load(path))  # type: ignore
        return obj

    def predict(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Best-effort prediction using stored attributes.

        This expects the saved detector to have attributes created by the
        original implementation (e.g., _mu, _sigma, _kmeans, _cluster_radii,
        _max_train_dist, _max_train_dim). If any are missing, we fallback to
        zeros.
        """
        # Required attributes
        mu = getattr(self, "_mu", None)
        sigma = getattr(self, "_sigma", None)
        kmeans = getattr(self, "_kmeans", None)
        radii = getattr(self, "_cluster_radii", None)
        max_dist = float(getattr(self, "_max_train_dist", 1.0) or 1.0)
        max_dim = getattr(self, "_max_train_dim", None)

        if mu is None or sigma is None or kmeans is None or radii is None or max_dim is None:
            # Fallback: zeros
            n = X.shape[0]
            d = X.shape[1]
            return np.zeros((n,), dtype=float), np.zeros((n, d), dtype=float)

        Xn = (X - mu) / (sigma + 1e-12)
        centers = kmeans.cluster_centers_

        overall: list[float] = []
        per_dim: list[np.ndarray] = []
        for xi in Xn:
            dists = np.linalg.norm(centers - xi, axis=1)
            idx = int(np.argmin(dists))
            center = centers[idx]
            radius = radii[idx]
            delta = np.abs(xi - center) - radius
            contrib = np.where(delta > 0, delta, 0.0)
            dist = np.linalg.norm(contrib)
            overall.append(np.clip(dist / max_dist, 0.0, 1.0))
            per_dim.append(np.clip(contrib / (max_dim + 1e-12), 0.0, 1.0))
        return np.asarray(overall), np.vstack(per_dim)


class IMSKMeansAdapter:
    """Adapter exposing onlineValidate compatible with current IMS service."""

    def __init__(self, pnames: List[str], model_bytes: bytes, threshold: float = 0.5) -> None:
        self.pnames = pnames
        self.threshold = float(threshold)

        # Persist bytes to temp file for joblib
        fd, path = tempfile.mkstemp(prefix="legacy_ims_", suffix=".joblib")
        os.close(fd)
        with open(path, "wb") as f:
            f.write(model_bytes)
        try:
            self.detector = _LegacyIMSDetector.load_from_file(path)
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    def onlineValidate(self, dataFrame: Dict[str, float], time_: float) -> Dict[str, object]:
        # Arrange single frame
        x = np.array([[dataFrame.get(p, np.nan) for p in self.pnames]], dtype=float)
        
        # 浼樺寲锛氳褰曠己澶卞弬鏁扮殑鏁伴噺
        nan_count = np.isnan(x).sum()
        total_params = len(self.pnames)
        
        # Fill NaN with zero (best-effort) to avoid propagation
        if np.isnan(x).any():
            x = np.nan_to_num(x, nan=0.0)
        
        overall, per_dim = self.detector.predict(x)
        raw_score = float(overall[0] if overall.size > 0 else 0.0)
        
        # 浼樺寲绛栫暐1: 濡傛灉缂哄け鍙傛暟杩囧锛?30%锛夛紝闄嶄綆缃俊搴?
        if nan_count > total_params * 0.3:
            raw_score = raw_score * 0.5  # 闄嶄綆鍒嗘暟
        
        # 浼樺寲绛栫暐2: 璁＄畻鍙傛暟绾у埆鐨勫紓甯镐竴鑷存€?
        # 鍙湁褰撳涓弬鏁板悓鏃跺紓甯告椂鎵嶆彁楂樼疆淇″害
        param_anomaly_count = 0
        param_anomaly_threshold = 0.3  # 鍙傛暟绾у埆鐨勫紓甯搁槇鍊?
        if per_dim.size > 0:
            for i in range(len(self.pnames)):
                if per_dim[0, i] > param_anomaly_threshold:
                    param_anomaly_count += 1
        
        # 濡傛灉鍙湁灏戞暟鍙傛暟寮傚父锛?20%鍙傛暟锛夛紝鍙兘鏄紶鎰熷櫒鍣０锛岄檷浣庡垎鏁?
        anomaly_ratio = param_anomaly_count / total_params if total_params > 0 else 0
        if anomaly_ratio < 0.2:
            raw_score = raw_score * 0.7  # 闄嶄綆鍒嗘暟
        
        # 搴旂敤闃堝€煎垽鏂?
        score = raw_score
        is_anomaly = bool(score >= self.threshold)
        parameter_scores = {p: float(per_dim[0, i]) for i, p in enumerate(self.pnames)} if per_dim.size else {}
        
        return {
            "detectType": "IMS_KMEANS",
            "result": {
                "state": is_anomaly,
                "score": score,
                "histAnom": False,
                "lastAnomTime": time_,
                "component": "PHM",
                "faultLevel": 1,
                "parameter_scores": parameter_scores,
                "detection_details": {
                    "raw_score": raw_score,
                    "nan_count": int(nan_count),
                    "param_anomaly_count": param_anomaly_count,
                    "param_anomaly_ratio": anomaly_ratio,
                    "adjustments_applied": nan_count > 0 or anomaly_ratio < 0.2
                },
                "addLine": [None, None],
            },
        }



