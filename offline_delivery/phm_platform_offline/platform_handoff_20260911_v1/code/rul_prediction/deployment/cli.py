"""File-based deployment CLI: NPZ requests in, shadow JSONL/CSV out.

Subcommands:
  predict     score one request NPZ against one bundle
  healthcheck load a bundle and print its health report

The CLI deliberately assumes no HTTP/RPC contract: the platform integrates via
files or the Python API.  Request NPZ keys: ``features`` float32
[batch, time, feature] (history in time order, right-padded), ``lengths``
int64 [batch], optional ``sample_ids`` strings, optional ``input_space`` which
must equal the manifest value when present (it is never guessed).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

from rul_prediction.deployment.contract import (
    DeploymentBatchError,
    OPTIONAL_NPZ_KEYS,
    REQUIRED_NPZ_KEYS,
    STATUS_SCHEMA_MISMATCH,
    STATUS_TARGET_COLUMN_IN_REQUEST,
    STATUS_UNSUPPORTED_INPUT_SPACE,
    TARGET_LIKE_KEYS,
)
from rul_prediction.deployment.runtime import PlatformRuntime

OUTPUT_FIELDS = (
    "sample_id",
    "model_version",
    "contract_version",
    "status",
    "raw_score",
    "display_score_clipped",
    "score_name",
    "deployment_mode",
    "actionable",
    "physical_rul_claim",
    "schema_hash",
    "warnings",
    "abstain_reason",
)


def load_request(path: str | Path) -> tuple[np.ndarray, np.ndarray, list[str] | None, str | None, list[str] | None]:
    archive = np.load(path, allow_pickle=False)
    missing = [key for key in REQUIRED_NPZ_KEYS if key not in archive.files]
    if missing:
        raise DeploymentBatchError(STATUS_SCHEMA_MISMATCH, f"request NPZ lacks keys: {missing}")
    smuggled = sorted(TARGET_LIKE_KEYS.intersection(archive.files))
    if smuggled:
        raise DeploymentBatchError(
            STATUS_TARGET_COLUMN_IN_REQUEST,
            "shadow requests must never contain supervision columns: "
            f"{smuggled}; a bundle scores features only",
        )
    unknown = sorted(set(archive.files) - set(REQUIRED_NPZ_KEYS) - set(OPTIONAL_NPZ_KEYS))
    if unknown:
        raise DeploymentBatchError(
            STATUS_SCHEMA_MISMATCH,
            f"request NPZ carries unexpected keys: {unknown} (allowed: features, lengths, "
            "sample_ids, input_space, feature_columns)",
        )
    features = archive["features"]
    lengths = archive["lengths"]
    sample_ids = [str(value) for value in archive["sample_ids"]] if "sample_ids" in archive.files else None
    input_space = str(archive["input_space"][0]) if "input_space" in archive.files else None
    feature_columns = (
        [str(value) for value in archive["feature_columns"]]
        if "feature_columns" in archive.files
        else None
    )
    return features, lengths, sample_ids, input_space, feature_columns


def write_outputs(records: list[dict], output_path: Path, output_format: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for record in records:
        row = {field: record.get(field) for field in OUTPUT_FIELDS}
        row["warnings"] = ";".join(record.get("warnings") or [])
        if row["status"] in ("ok",):
            row["abstain_reason"] = ""
        else:
            row["abstain_reason"] = row["status"]
        rows.append(row)
    if output_format == "jsonl":
        with open(output_path, "w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    elif output_format == "csv":
        with open(output_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(OUTPUT_FIELDS))
            writer.writeheader()
            writer.writerows(rows)
    else:
        raise ValueError(f"unsupported output format: {output_format}")


def cmd_predict(args: argparse.Namespace) -> int:
    features, lengths, sample_ids, input_space, feature_columns = load_request(args.input)
    runtime = PlatformRuntime.load(args.bundle, device=args.device)
    if input_space is not None and input_space != runtime.input_space:
        raise DeploymentBatchError(
            STATUS_UNSUPPORTED_INPUT_SPACE,
            f"request declares input_space={input_space!r} but the bundle manifest declares "
            f"{runtime.input_space!r}; input space is never guessed",
        )
    if feature_columns is not None and list(feature_columns) != list(runtime.feature_columns):
        raise DeploymentBatchError(
            STATUS_SCHEMA_MISMATCH,
            "request feature_columns do not match the bundle schema exactly "
            f"(request={feature_columns}, bundle={list(runtime.feature_columns)}); "
            "refusing to reorder or reshape",
        )
    records = runtime.predict(features, lengths, sample_ids=sample_ids)
    output_path = Path(args.output)
    write_outputs(records, output_path, args.format)
    n_ok = sum(1 for record in records if record["status"] == "ok")
    n_abstained = len(records) - n_ok
    print(
        f"[deploy] bundle={args.bundle} samples={len(records)} ok={n_ok} "
        f"abstained={n_abstained} -> {output_path}"
    )
    return 0 if n_abstained == 0 else 3


def cmd_healthcheck(args: argparse.Namespace) -> int:
    runtime = PlatformRuntime.load(args.bundle, device=args.device)
    health = runtime.healthcheck()
    print(json.dumps(health, ensure_ascii=False, indent=2))
    return 0 if health["status"] == "PASS" else 4


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rul-deploy", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    predict = sub.add_parser("predict", help="score a request NPZ against a bundle")
    predict.add_argument("--bundle", required=True)
    predict.add_argument("--input", required=True, help="request .npz (features, lengths[, sample_ids])")
    predict.add_argument("--output", required=True, help="output .jsonl or .csv path")
    predict.add_argument("--format", default="jsonl", choices=["jsonl", "csv"])
    predict.add_argument("--device", default="cpu")
    predict.set_defaults(func=cmd_predict)

    health = sub.add_parser("healthcheck", help="load a bundle and print its health report")
    health.add_argument("--bundle", required=True)
    health.add_argument("--device", default="cpu")
    health.set_defaults(func=cmd_healthcheck)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except DeploymentBatchError as error:
        print(
            json.dumps(
                {
                    "rejected": True,
                    "status": error.status,
                    "detail": error.detail,
                    "deployment_mode": "shadow",
                    "actionable": False,
                    "physical_rul_claim": False,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
