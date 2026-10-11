"""Shared roles for telemetry CSV columns; labels never become model inputs."""
from __future__ import annotations

import re


def normalized_column(column: str) -> str:
    return re.sub(r"[\s_\-]+", "", str(column)).casefold()


def column_role(column: str) -> str:
    name = normalized_column(column)
    if name in {"time", "timestamp", "t", "时间", "时间戳"}:
        return "timestamp"
    if name == "faultflag":
        return "fault_label"
    return "parameter"


def column_roles(columns) -> dict:
    columns = list(columns)
    return {
        "time_column": next((name for name in columns if column_role(name) == "timestamp"), None),
        "fault_flag_column": next((name for name in columns if column_role(name) == "fault_label"), None),
        "parameter_columns": [name for name in columns if column_role(name) == "parameter"],
        "column_roles": {name: column_role(name) for name in columns},
    }


def timestamp_value(row: dict, fallback):
    column = next((name for name in row if column_role(name) == "timestamp"), None)
    return float(row[column]) if column is not None else fallback
