"""Remaining useful life prediction contracts and implementations.

The first project stage intentionally exposes only data/label/split contracts.
Model and training code is added only after these contracts have been reviewed.
"""

from .contracts import (
    PHYSICAL_LABEL_SOURCE,
    PROXY_LABEL_SOURCE,
    RULContract,
    assert_no_forbidden_features,
)

__all__ = [
    "PHYSICAL_LABEL_SOURCE",
    "PROXY_LABEL_SOURCE",
    "RULContract",
    "assert_no_forbidden_features",
]
