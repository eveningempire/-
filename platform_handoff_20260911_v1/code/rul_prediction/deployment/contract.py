"""Platform shadow contract constants (文本/14, ``platform_shadow_contract_v1``).

Every inference output of a deployment bundle must carry these semantics:
``deployment_mode="shadow"``, ``actionable=false``,
``physical_rul_claim=false``.  P1 (synthetic contract candidate) scores are
named ``synthetic_contract_rul_normalized``; P2 (409 LOX shadow) scores are
named ``synthetic_proxy_score`` and must never be presented as real RUL.
"""

from __future__ import annotations

CONTRACT_VERSION = "platform_shadow_contract_v1"

DEPLOYMENT_MODE = "shadow"
ACTIONABLE = False
PHYSICAL_RUL_CLAIM = False

P1_SCORE_NAME = "synthetic_contract_rul_normalized"
P2_SCORE_NAME = "synthetic_proxy_score"

INPUT_SPACE_RAW = "raw"
INPUT_SPACE_SCALED = "scaled"
SUPPORTED_INPUT_SPACES = (INPUT_SPACE_RAW, INPUT_SPACE_SCALED)

# batch-level rejections (contract or asset problem: refuse the whole batch)
STATUS_SCHEMA_MISMATCH = "MODEL_NOT_APPLIED_SCHEMA_MISMATCH"
STATUS_TARGET_COLUMN_IN_REQUEST = "TARGET_COLUMN_IN_REQUEST"
STATUS_ASSET_MISMATCH = "BUNDLE_ASSET_MISMATCH"
STATUS_UNSUPPORTED_INPUT_SPACE = "UNSUPPORTED_INPUT_SPACE"
STATUS_EMPTY_REQUEST = "EMPTY_REQUEST"
STATUS_FEATURE_DIM_MISMATCH = "MODEL_NOT_APPLIED_SCHEMA_MISMATCH"

# per-sample abstains (one bad sample never blocks the others)
STATUS_OK = "ok"
ABSTAIN_NON_FINITE_INPUT = "ABSTAIN_NON_FINITE_INPUT"
ABSTAIN_INVALID_LENGTHS = "ABSTAIN_INVALID_LENGTHS"
ABSTAIN_PADDING_TAIL_VIOLATION = "ABSTAIN_PADDING_TAIL_VIOLATION"
ABSTAIN_INFERENCE_FAILED = "ABSTAIN_INFERENCE_FAILED"

ABSTAIN_STATUSES = frozenset(
    {
        ABSTAIN_NON_FINITE_INPUT,
        ABSTAIN_INVALID_LENGTHS,
        ABSTAIN_PADDING_TAIL_VIOLATION,
        ABSTAIN_INFERENCE_FAILED,
    }
)

REQUIRED_OUTPUT_FIELDS = (
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
)

# request NPZ keys that would smuggle supervision into a shadow deployment
TARGET_LIKE_KEYS = frozenset(
    {
        "target",
        "targets",
        "rul",
        "label",
        "labels",
        "y",
        "system_rul",
        "component_rul",
        "truth",
        "ground_truth",
        "hi_true",
    }
)

REQUIRED_NPZ_KEYS = ("features", "lengths")
OPTIONAL_NPZ_KEYS = ("sample_ids", "input_space", "feature_columns")

# Batched and single-row inference take different BLAS/GEMM reduction paths,
# so batch-vs-per-sample equality is defined up to this recorded float
# tolerance (bitwise equality is only guaranteed for identical batch shapes).
BATCH_PER_SAMPLE_TOLERANCE = {"rtol": 1e-4, "atol": 1e-6}


class DeploymentBatchError(RuntimeError):
    """Contract/asset-level rejection: the whole batch is refused, no scores."""

    def __init__(self, status: str, detail: str = ""):
        self.status = status
        self.detail = detail
        super().__init__(f"{status}: {detail}" if detail else status)


def shadow_fields() -> dict:
    """The mandatory shadow semantics shared by every output record."""

    return {
        "contract_version": CONTRACT_VERSION,
        "deployment_mode": DEPLOYMENT_MODE,
        "actionable": ACTIONABLE,
        "physical_rul_claim": PHYSICAL_RUL_CLAIM,
    }
