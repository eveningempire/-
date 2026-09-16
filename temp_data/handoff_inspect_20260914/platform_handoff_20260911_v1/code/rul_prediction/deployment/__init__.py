"""Deployment package: platform shadow bundles (文本/14)."""

from rul_prediction.deployment.contract import (
    CONTRACT_VERSION,
    DEPLOYMENT_MODE,
    DeploymentBatchError,
)
from rul_prediction.deployment.runtime import PlatformRuntime

__all__ = [
    "CONTRACT_VERSION",
    "DEPLOYMENT_MODE",
    "DeploymentBatchError",
    "PlatformRuntime",
]
