"""Deployment bundle exporter (文本/14 §4 layout).

Turns a completed synthetic-contract run (``models/<VERSION>`` +
``outputs/<VERSION>``) into a self-contained, hash-sealed deployment bundle
under ``rul_prediction/deployments/<DEPLOY_VERSION>``.  The bundle carries the
model weights, the train-fitted scaler, the feature schema, a train-only
distribution summary, a sample request/response pair, its own healthcheck and
SHA256SUMS.  Everything is synthetic; no real 409 value enters a bundle.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch
import yaml

from .contract import (
    ACTIONABLE,
    CONTRACT_VERSION,
    DEPLOYMENT_MODE,
    PHYSICAL_RUL_CLAIM,
    P1_SCORE_NAME,
)
from .runtime import PlatformRuntime, sha256_file

BUNDLE_FILES = (
    "deployment_manifest.json",
    "model_state.pt",
    "scaler.npz",
    "feature_schema.json",
    "train_distribution.json",
    "config.yaml",
    "environment.json",
    "source_hashes.json",
    "sample_request.npz",
    "sample_response.jsonl",
    "healthcheck.json",
    "README.md",
)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def train_distribution_summary(
    sequences: np.ndarray,
    lengths: np.ndarray,
    rows: np.ndarray,
    feature_columns: tuple[str, ...],
) -> dict[str, Any]:
    """Per-feature statistics of the train rows in model input (scaled) space.

    Only values inside each row's valid length participate; padding tails are
    excluded.  The summary supports drift observation, never safety claims.
    """

    features: dict[str, Any] = {}
    for index, name in enumerate(feature_columns):
        values = np.concatenate(
            [sequences[row, : int(lengths[row]), index] for row in rows], axis=0
        ).astype(np.float64)
        features[name] = {
            "min": float(values.min()),
            "max": float(values.max()),
            "mean": float(values.mean()),
            "std": float(values.std()),
            "q01": float(np.quantile(values, 0.01)),
            "q99": float(np.quantile(values, 0.99)),
        }
    return {
        "space": "model_input_scaled",
        "fit_split": "train",
        "n_rows": int(len(rows)),
        "features": features,
        "note": "train-only distribution summary for drift observation; not a safety threshold",
    }


def export_bundle(
    *,
    deploy_root: Path,
    deploy_version: str,
    run_version: str,
    project_root: Path,
    fixture: Any,
    profile: str,
    score_name: str = P1_SCORE_NAME,
    extra_manifest: Mapping[str, Any] | None = None,
) -> Path:
    """Build one deployment bundle; refuses to overwrite an existing directory."""

    models_dir = project_root / "rul_prediction" / "models" / run_version
    outputs_dir = project_root / "rul_prediction" / "outputs" / run_version

    bundle_dir = Path(deploy_root) / deploy_version
    if bundle_dir.exists():
        # create-once: the overwrite refusal dominates every other check
        raise FileExistsError(f"deployment bundle directory exists: {bundle_dir}")

    model_state = models_dir / "model_state.pt"
    summary_path = outputs_dir / "run_summary.json"
    scaler_path = models_dir / "scaler.npz"
    for required in (model_state, summary_path, scaler_path):
        if not required.exists():
            raise FileNotFoundError(f"run {run_version} lacks {required.name}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if str(summary.get("status")) != "completed":
        raise ValueError(f"run {run_version} is not completed; refusing to export")

    bundle_dir.mkdir(parents=True)

    # 1) weights / scaler / schema (train-fitted assets only)
    shutil.copyfile(model_state, bundle_dir / "model_state.pt")
    shutil.copyfile(scaler_path, bundle_dir / "scaler.npz")

    feature_columns = tuple(fixture.feature_columns)
    seq_length = int(fixture.sequences.shape[1])
    schema_payload = {
        "columns": list(feature_columns),
        "seq_length": seq_length,
        "n_features": len(feature_columns),
        "sha256": summary["feature_schema_hash"],
    }
    _write_json(bundle_dir / "feature_schema.json", schema_payload)

    # 2) train-only distribution in model input space (drift observation)
    index = fixture.sample_index
    train_rows = np.where(
        index["split"].eq("train").to_numpy(bool) & index["event_observed"].to_numpy(bool)
    )[0]
    distribution = train_distribution_summary(
        fixture.sequences, fixture.lengths, train_rows, feature_columns
    )
    _write_json(bundle_dir / "train_distribution.json", distribution)

    # 3) informational config + environment + source hashes
    config_payload = {
        "model": dict(summary.get("model", {})),
        "data": dict(summary.get("fixture_config", {})),
        "training": {key: value for key, value in dict(summary.get("training", {})).items()
                     if key in {"epochs", "patience", "batch_size", "lr", "weight_decay", "amp"}},
        "run": {"seed": summary.get("seed"), "version": run_version, "device": summary.get("device")},
    }
    (bundle_dir / "config.yaml").write_text(yaml.safe_dump(config_payload, sort_keys=False), encoding="utf-8")

    from rul_prediction.evaluation.reporting import collect_environment, collect_source_hashes, utc_now

    environment = collect_environment({"deploy_version": deploy_version, "run_version": run_version})
    _write_json(bundle_dir / "environment.json", environment)
    sources = collect_source_hashes(project_root)
    _write_json(
        bundle_dir / "source_hashes.json",
        {
            "generated_at": utc_now(),
            "note": "hashes of the rul_prediction sources that built this bundle",
            "files": sources,
        },
    )

    # 4) manifest
    manifest = {
        "deployment_manifest_version": 1,
        "deploy_version": deploy_version,
        "created_at": utc_now(),
        "contract_version": CONTRACT_VERSION,
        "deployment_mode": DEPLOYMENT_MODE,
        "actionable": ACTIONABLE,
        "physical_rul_claim": PHYSICAL_RUL_CLAIM,
        "profile": profile,
        "score_name": score_name,
        "model_version": run_version,
        "model_type": str(summary.get("model", {}).get("type", "")),
        "model_config": dict(summary.get("model", {})),
        "n_components": int(summary.get("fixture_config", {}).get("n_components", 7)),
        "feature_schema": schema_payload,
        "input_space": "raw",
        "generator": {
            "label_source": summary.get("label_source"),
            "generator_version": summary.get("generator_version"),
            "fixture_sha256": summary.get("fixture_sha256"),
            "synthetic": True,
            "real_409_data_used": False,
        },
        "runtime_hints": {
            "python": environment["python"],
            "torch": environment["torch"],
            "numpy": environment["numpy"],
        },
        "notes": [
            "Scores are synthetic-contract outputs for integration and observation only.",
            "The 409 dataset remains PROXY_ONLY / NOT_RUN_TO_FAILURE / NOT_TRAINABLE_ALL_CENSORED.",
            "No HTTP/RPC contract is assumed; the stable interfaces are the Python API and the NPZ CLI.",
        ],
    }
    if extra_manifest:
        manifest.update(dict(extra_manifest))
    _write_json(bundle_dir / "deployment_manifest.json", manifest)

    # 5) sample request/response: one fixture row, raw input space, right-padded
    sample_row = int(train_rows[0]) if len(train_rows) else 0
    scaled_sample = fixture.sequences[sample_row].astype(np.float64)
    length = int(fixture.lengths[sample_row])
    center = np.asarray(fixture.scaler.center, dtype=np.float64)
    scale = np.asarray(fixture.scaler.scale, dtype=np.float64)
    raw_sample = scaled_sample * scale[None, :] + center[None, :]
    raw_padded = np.zeros_like(scaled_sample)
    raw_padded[:length] = raw_sample[:length]
    np.savez(
        bundle_dir / "sample_request.npz",
        features=raw_padded[None, ...].astype(np.float32),
        lengths=np.asarray([length], dtype=np.int64),
        sample_ids=np.asarray([f"sample_{sample_row:06d}"]),
    )

    # 6) self healthcheck + sample response (produced by the runtime itself;
    # SHA256SUMS does not exist yet, so the hash gate is exercised afterwards)
    runtime = PlatformRuntime(bundle_dir, device="cpu", _skip_hash_check=True)
    health = runtime.healthcheck()
    _write_json(bundle_dir / "healthcheck.json", health)
    response = runtime.predict(
        raw_padded[None, ...].astype(np.float32),
        np.asarray([length], dtype=np.int64),
        sample_ids=[f"sample_{sample_row:06d}"],
    )
    (bundle_dir / "sample_response.jsonl").write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in response) + "\n",
        encoding="utf-8",
    )

    # 7) README + SHA256SUMS last (sealed over every other file)
    (bundle_dir / "README.md").write_text(
        f"# {deploy_version}\n\n"
        f"Profile: **{profile}** under contract `{CONTRACT_VERSION}`.\n\n"
        f"- source run: `{run_version}` (synthetic contract fixture only)\n"
        f"- score name: `{score_name}`\n"
        f"- deployment_mode=shadow, actionable=false, physical_rul_claim=false\n"
        f"- feature count: {len(feature_columns)}; seq_length: {seq_length}; input_space: raw\n\n"
        "## Python API\n\n"
        "```python\n"
        "from rul_prediction.deployment.runtime import PlatformRuntime\n"
        f'runtime = PlatformRuntime.load("{bundle_dir}", device="cpu")\n'
        "result = runtime.predict(features, lengths, sample_ids=None)\n"
        "health = runtime.healthcheck()\n"
        "```\n\n"
        "## CLI\n\n"
        "```bash\n"
        "python -m rul_prediction.deployment.cli predict \\\n"
        f'  --bundle "{bundle_dir}" --input request.npz --output result.jsonl --format jsonl\n'
        "```\n\n"
        "All outputs are shadow scores; they are not real RUL and are not actionable.\n",
        encoding="utf-8",
    )
    _write_sha256sums(bundle_dir)
    return bundle_dir


def _write_sha256sums(bundle_dir: Path) -> None:
    lines = []
    for path in sorted(bundle_dir.iterdir()):
        if path.name == "SHA256SUMS" or not path.is_file():
            continue
        lines.append(f"{sha256_file(path)}  {path.name}")
    (bundle_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
