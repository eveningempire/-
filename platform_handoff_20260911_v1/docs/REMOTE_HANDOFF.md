# RUL remote handoff — integrated locally 2026-09-10

> The remote return is now merged into the canonical local project. Current
> merge details and verification are recorded in
> `文本/15_本地远程融合说明_20260910.md` and
> `rul_prediction/outputs/rul_local_remote_merge_v1_20260910/IMPLEMENTATION_REPORT.md`.
> Canonical paths are `datasets/`, `health_assessment/`, `rul_prediction/`,
> and `文本/`; the extracted nested `20jd/` tree is only staging and is no
> longer authoritative. This merge is not a scientific approval of returned
> RUL results, and the 409-data supervised-training gate remains closed.

## Current state

RUL-G1 was implemented by GLM and reviewed by codex.  The original G1 evidence
is retained under `rul_prediction/outputs/rul_g1_data_adapter_v1_20260909/`.
Codex found and fixed two material adapter issues before packaging:

1. historical HI values are now preserved across the BiLSTM sequence instead
   of repeating the current HI at every time step;
2. HI files now reject duplicate keys, mixed splits within one run, incomplete
   manifest coverage, and cross-component contamination.

The reviewed audit is under
`rul_prediction/outputs/rul_r1_review_v1_20260909/`.  RUL tests pass 53/53;
the combined local suite passed 191 tests with eight unrelated warnings from
the concurrently changing local health-assessment system-candidate code.

## Critical scientific blocker

The current 409-run data has zero observed failures and no registered failure
threshold.  It is not legal to perform ordinary MSE/MAE RUL training on it.
The next remote task may implement and smoke-test BiLSTM/LSTM infrastructure on
synthetic contract fixtures, but must not present a trained real-data RUL model
until codex registers a proxy-label contract or run-to-failure data is supplied.

## Snapshot boundary

The remote package intentionally does not contain the mutable local
`health_assessment` source tree.  It contains only these frozen inputs in their
expected relative locations:

- `health_assessment/outputs/experiments/frozen_external/manifest_with_split.csv`;
- seven CDPCA-GA and seven AE-GMM component prediction CSVs;
- the corresponding two `run_summary.json` files;
- the selected 409 telemetry and ground-truth files in the separate data archive.

Do not regenerate or edit this snapshot.  Its hashes are recorded in the G1/R1
audit artifacts and the remote package manifest.

## Source ownership and Git collaboration

The returned remote RUL work was integrated into the canonical local tree on
2026-09-10. From the Git baseline onward, the private central Git repository
is authoritative for source, configuration, tests, and documentation. Remote
RUL work uses short-lived `feature/rul-*` branches; local data-generation work
uses `local/data-*` branches. `health_assessment/`, `RLVsim/`, and original
`datasets/` remain locally owned and outside remote-agent edit scope.

Large datasets, checkpoints, model/output trees, and return archives remain
outside normal Git history. They are transferred as immutable versioned
artifacts with SHA-256 manifests. See
`文本/16_Git版本管理与本地远程协作说明_20260911.md`.

## Current next gate

The remote baseline, architecture ablations, and returned R2/n2 runs are now
present locally, but presence is not scientific acceptance. The next gates
are (1) audit the returned R2/n2 multi-seed evidence, (2) register and pilot a
run-to-failure lifecycle data contract, and (3) integrate the existing health
and RUL bundles into the platform in strictly non-actionable shadow mode.
Transformer/KAN complexity must not be treated as progress toward physical RUL
until the data/label gate is open.
