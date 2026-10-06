"""Self-contained deployment runtime for platform shadow bundles.

Loads a bundle produced by :mod:`rul_prediction.deployment.exporter`, verifies
every asset hash, then scores requests under the ``platform_shadow_contract_v1``
semantics: schema/finite/length/right-padding checks, per-sample abstain,
train-distribution drift observation (never a safety threshold), and mandatory
shadow/non-actionable/no-physical-RUL-claim markers on every record.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from .contract import (
    ABSTAIN_INFERENCE_FAILED,
    ABSTAIN_INVALID_LENGTHS,
    ABSTAIN_NON_FINITE_INPUT,
    ABSTAIN_PADDING_TAIL_VIOLATION,
    ACTIONABLE,
    CONTRACT_VERSION,
    DEPLOYMENT_MODE,
    DeploymentBatchError,
    PHYSICAL_RUL_CLAIM,
    REQUIRED_OUTPUT_FIELDS,
    STATUS_ASSET_MISMATCH,
    STATUS_EMPTY_REQUEST,
    STATUS_SCHEMA_MISMATCH,
    STATUS_UNSUPPORTED_INPUT_SPACE,
    shadow_fields,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _abstain_record(sample_id: str, status: str, warning: str, manifest: Mapping[str, Any], schema_hash: str) -> dict:
    record = {
        "sample_id": sample_id,
        "model_version": manifest["model_version"],
        "status": status,
        "raw_score": None,
        "display_score_clipped": None,
        "score_name": manifest["score_name"],
        "schema_hash": schema_hash,
        "warnings": [warning],
    }
    record.update(shadow_fields())
    return record


class PlatformRuntime:
    """Loaded, hash-verified deployment bundle ready for CPU/CUDA inference."""

    def __init__(self, bundle_dir: str | Path, device: str = "cpu", *, _skip_hash_check: bool = False):
        self.bundle_dir = Path(bundle_dir)
        self.device = torch.device(device)
        manifest_path = self.bundle_dir / "deployment_manifest.json"
        if not manifest_path.exists():
            raise DeploymentBatchError(STATUS_ASSET_MISMATCH, f"missing deployment_manifest.json in {self.bundle_dir}")
        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        sums_path = self.bundle_dir / "SHA256SUMS"
        self.asset_checks: dict[str, bool] = {}
        if not _skip_hash_check:
            if not sums_path.exists():
                raise DeploymentBatchError(STATUS_ASSET_MISMATCH, "missing SHA256SUMS")
            self._verify_hashes(sums_path)

        self.feature_columns: tuple[str, ...] = tuple(self.manifest["feature_schema"]["columns"])
        self.seq_length: int = int(self.manifest["feature_schema"]["seq_length"])
        self.n_features: int = int(self.manifest["feature_schema"]["n_features"])
        self.input_space: str = str(self.manifest["input_space"])
        if self.input_space not in ("raw", "scaled"):
            raise DeploymentBatchError(
                STATUS_UNSUPPORTED_INPUT_SPACE,
                f"manifest input_space {self.input_space!r} is neither raw nor scaled",
            )
        self.schema_hash: str = str(self.manifest["feature_schema"]["sha256"])
        self.score_name: str = str(self.manifest["score_name"])

        self.scaler_center: np.ndarray | None = None
        self.scaler_scale: np.ndarray | None = None
        scaler_path = self.bundle_dir / "scaler.npz"
        if scaler_path.exists():
            scaler = np.load(scaler_path, allow_pickle=False)
            self.scaler_center = scaler["center"].astype(np.float64)
            self.scaler_scale = scaler["scale"].astype(np.float64)
            if self.scaler_center.shape != (self.n_features,) or self.scaler_scale.shape != (self.n_features,):
                raise DeploymentBatchError(
                    STATUS_ASSET_MISMATCH,
                    f"scaler dims {self.scaler_center.shape} do not match feature count {self.n_features}",
                )
            fit_split_raw = scaler["fit_split"] if "fit_split" in scaler.files else np.asarray("train")
            fit_split = str(fit_split_raw.item() if fit_split_raw.ndim == 0 else fit_split_raw[0])
            if fit_split != "train":
                raise DeploymentBatchError(STATUS_ASSET_MISMATCH, f"bundled scaler was fit on {fit_split!r}")

        distribution_path = self.bundle_dir / "train_distribution.json"
        self.train_distribution: dict[str, Any] = (
            json.loads(distribution_path.read_text(encoding="utf-8")) if distribution_path.exists() else {}
        )

        self.model = self._build_model()

    @classmethod
    def load(cls, bundle_dir: str | Path, device: str = "cpu") -> "PlatformRuntime":
        """Stable API: verify every asset hash, then build the model."""

        return cls(bundle_dir, device=device)

    # ------------------------------------------------------------------ load
    def _verify_hashes(self, sums_path: Path) -> None:
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            expected, _, name = line.partition("  ")
            path = self.bundle_dir / name
            if not path.exists():
                raise DeploymentBatchError(STATUS_ASSET_MISMATCH, f"bundle file missing: {name}")
            actual = sha256_file(path)
            if actual != expected:
                raise DeploymentBatchError(
                    STATUS_ASSET_MISMATCH,
                    f"sha256 mismatch for {name}: expected {expected}, got {actual}",
                )
            self.asset_checks[name] = True

    def _build_model(self) -> torch.nn.Module:
        from rul_prediction.models import build_model

        config = dict(self.manifest["model_config"])
        config["type"] = self.manifest["model_type"]
        model = build_model(config, n_features=self.n_features, n_components=int(self.manifest.get("n_components", 7)))
        state_path = self.bundle_dir / "model_state.pt"
        try:
            state = torch.load(state_path, map_location="cpu", weights_only=True)
        except Exception as error:  # corrupted weights must refuse, never guess
            raise DeploymentBatchError(STATUS_ASSET_MISMATCH, f"model_state.pt unreadable: {error}") from error
        try:
            model.load_state_dict(state)
        except RuntimeError as error:
            raise DeploymentBatchError(STATUS_ASSET_MISMATCH, f"model_state.pt incompatible: {error}") from error
        model.to(self.device)
        model.eval()
        return model

    # ---------------------------------------------------------------- checks
    def _validate_common_shape(self, features: np.ndarray, lengths: np.ndarray) -> None:
        array = np.asarray(features)
        if array.ndim != 3:
            raise DeploymentBatchError(
                STATUS_SCHEMA_MISMATCH,
                f"features must be [batch, time, feature]; got shape {array.shape}",
            )
        batch, time_steps, n_feat = array.shape
        if n_feat != self.n_features:
            raise DeploymentBatchError(
                STATUS_SCHEMA_MISMATCH,
                f"feature mismatch: bundle schema expects {self.n_features} columns "
                f"{list(self.feature_columns)}, request supplies {n_feat}",
            )
        if time_steps < 1:
            raise DeploymentBatchError(STATUS_SCHEMA_MISMATCH, "time dimension must be >= 1")
        lengths_array = np.asarray(lengths)
        if lengths_array.shape != (batch,):
            raise DeploymentBatchError(
                STATUS_SCHEMA_MISMATCH,
                f"lengths must have shape ({batch},); got {lengths_array.shape}",
            )
        if batch == 0:
            raise DeploymentBatchError(STATUS_EMPTY_REQUEST, "zero-row request")

    def _scale(self, window: np.ndarray) -> np.ndarray:
        if self.input_space == "raw" and self.scaler_center is not None:
            return (window - self.scaler_center) / self.scaler_scale
        return window

    def _drift_warnings(self, scaled_window: np.ndarray) -> tuple[list[str], float]:
        """Per-feature out-of-train-range rates on the valid region (observation only)."""

        distribution = self.train_distribution.get("features") if self.train_distribution else None
        if not distribution:
            return [], 0.0
        warnings: list[str] = []
        exceeded: list[int] = []
        for index, name in enumerate(self.feature_columns):
            stats = distribution.get(name)
            if not stats:
                continue
            column = scaled_window[:, index]
            outside = int(((column < stats["min"]) | (column > stats["max"])).sum())
            if outside:
                rate = outside / column.shape[0]
                exceeded.append(index)
                warnings.append(f"drift:{name}:rate={rate:.3f}")
        total = len(exceeded) / len(self.feature_columns) if self.feature_columns else 0.0
        return warnings, total

    # --------------------------------------------------------------- predict
    def predict(
        self,
        features: np.ndarray,
        lengths: np.ndarray,
        sample_ids: Sequence[str] | None = None,
    ) -> list[dict]:
        """Score one batch; per-sample problems abstain, contract problems reject."""

        array = np.asarray(features)
        lengths_array = np.asarray(lengths)
        self._validate_common_shape(array, lengths_array)
        batch = array.shape[0]
        ids = (
            [str(value) for value in sample_ids]
            if sample_ids is not None
            else [f"sample_{index:06d}" for index in range(batch)]
        )
        if len(ids) != batch:
            raise DeploymentBatchError(
                STATUS_SCHEMA_MISMATCH,
                f"sample_ids length {len(ids)} != batch {batch}",
            )

        records: list = [None] * batch
        work: list[tuple[int, np.ndarray]] = []
        for index in range(batch):
            length = int(lengths_array[index])
            if length < 1 or length > array.shape[1]:
                records[index] = (
                    _abstain_record(
                        ids[index],
                        ABSTAIN_INVALID_LENGTHS,
                        f"lengths[{index}]={length} outside 1..{array.shape[1]}",
                        self.manifest,
                        self.schema_hash,
                    )
                )
                continue
            window = array[index, :length, :].astype(np.float64)
            if not np.isfinite(window).all():
                bad = int((~np.isfinite(window)).sum())
                records[index] = (
                    _abstain_record(
                        ids[index],
                        ABSTAIN_NON_FINITE_INPUT,
                        f"{bad} non-finite value(s) inside the valid region",
                        self.manifest,
                        self.schema_hash,
                    )
                )
                continue
            tail = array[index, length:, :]
            if tail.size and not np.all(tail == 0.0):
                records[index] = (
                    _abstain_record(
                        ids[index],
                        ABSTAIN_PADDING_TAIL_VIOLATION,
                        "padding tail beyond lengths contains non-zero values "
                        "(right-padding contract: valid history first, zeros after)",
                        self.manifest,
                        self.schema_hash,
                    )
                )
                continue
            work.append((index, window))

        if work:
            # scale each valid window, then embed into a fixed-length frame;
            # the model masks by lengths, so scaled padding tails are inert
            scaled = np.zeros((len(work), array.shape[1], self.n_features), dtype=np.float64)
            for position, (index, window) in enumerate(work):
                scaled[position, : window.shape[0]] = self._scale(window)
            scaled = scaled.astype(np.float32)
            tensor = torch.from_numpy(scaled).to(self.device)
            step_lengths = torch.tensor(
                [int(lengths_array[index]) for index, _ in work], dtype=torch.int64
            )
            with torch.no_grad():
                outputs = self.model(tensor, step_lengths)
                if isinstance(outputs, dict):
                    outputs = outputs["system"]
                outputs = outputs.detach().float().cpu().numpy()
            for position, (index, window) in enumerate(work):
                scaled_window = scaled[position, : int(lengths_array[index])].astype(np.float64)
                drift_warnings, drift_total = self._drift_warnings(scaled_window)
                raw = float(outputs[position])
                if not np.isfinite(raw):
                    records[index] = (
                        _abstain_record(
                            ids[index],
                            ABSTAIN_INFERENCE_FAILED,
                            "model produced a non-finite score",
                            self.manifest,
                            self.schema_hash,
                        )
                    )
                    continue
                warnings = list(drift_warnings)
                if drift_total > 0:
                    warnings.append(f"drift_total_features={drift_total:.3f}")
                else:
                    warnings.append("no_drift")
                records[index] = self._ok_record(ids[index], raw, warnings)
        if any(record is None for record in records):
            missing = [ids[i] for i, record in enumerate(records) if record is None]
            raise AssertionError(f"records unset for samples: {missing}")
        for record in records:
            missing = [field for field in REQUIRED_OUTPUT_FIELDS if field not in record]
            if missing:  # defensive: the contract fields are non-negotiable
                raise AssertionError(f"output record lacks contract fields: {missing}")
        return records

    def _ok_record(self, sample_id: str, raw_score: float, warnings: list[str]) -> dict:
        record = {
            "sample_id": sample_id,
            "model_version": self.manifest["model_version"],
            "status": "ok",
            "raw_score": raw_score,
            "display_score_clipped": float(min(max(raw_score, 0.0), 1.0)),
            "score_name": self.score_name,
            "schema_hash": self.schema_hash,
            "warnings": warnings,
        }
        record.update(shadow_fields())
        return record

    # ------------------------------------------------------------ healthcheck
    def healthcheck(self) -> dict:
        checks: dict[str, Any] = {
            "bundle_dir": str(self.bundle_dir),
            "asset_hashes_verified": all(self.asset_checks.values()) and bool(self.asset_checks),
            "model_type": self.manifest["model_type"],
            "model_version": self.manifest["model_version"],
            "n_features": self.n_features,
            "seq_length": self.seq_length,
            "input_space": self.input_space,
            "scaler_present": self.scaler_center is not None,
            "train_distribution_present": bool(self.train_distribution),
            "device": str(self.device),
            "torch": torch.__version__,
        }
        try:
            probe = torch.zeros((1, self.seq_length, self.n_features), device=self.device)
            probe_lengths = torch.full((1,), self.seq_length, dtype=torch.int64)
            with torch.no_grad():
                output = self.model(probe, probe_lengths)
                if isinstance(output, dict):
                    output = output["system"]
            checks["forward_probe"] = bool(torch.isfinite(output).all().item())
        except Exception as error:
            checks["forward_probe"] = False
            checks["forward_probe_error"] = str(error)
        failed = [name for name, value in checks.items() if value is False]
        status = "PASS" if not failed else "FAIL"
        return {
            "status": status,
            "failed_checks": failed,
            "contract_version": CONTRACT_VERSION,
            "deployment_mode": DEPLOYMENT_MODE,
            "actionable": ACTIONABLE,
            "physical_rul_claim": PHYSICAL_RUL_CLAIM,
            "checks": checks,
        }
