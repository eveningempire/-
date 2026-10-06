"""Resolve simulate CSV paths for Linux / Windows deployments."""

from __future__ import annotations

import os

_HEALTH_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_datacsv_dir() -> str:
    env = os.environ.get("HEALTH_DATACSV_DIR")
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    candidate = os.path.join(_HEALTH_ROOT, "simulate", "datacsv")
    if os.path.isdir(candidate):
        return candidate
    return r"D:\pythonpro\datacsv"


def get_scope_csv_path() -> str:
    return os.path.join(get_datacsv_dir(), "scope_data.csv")


def get_p_values_csv_path() -> str:
    return os.path.join(get_datacsv_dir(), "P_values.csv")


def get_algorithm_config_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "algorithm_config.json")
