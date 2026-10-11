"""Streaming helpers for importing and validating large PHM data files.

The functions in this module deliberately use the Python standard library (and
openpyxl's read-only mode for XLSX) so they are usable in the offline delivery.
They inspect a file without loading all rows into memory and return a stable
report that can be consumed by the UI and by later algorithm stages.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from itertools import chain
from pathlib import Path
from typing import Any, Iterable, Iterator

from .schema import column_roles


SUPPORTED_SUFFIXES = {".csv", ".json", ".jsonl", ".ndjson", ".xlsx"}
MAX_COLUMNS = 500
SAMPLE_ROWS = 20


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _infer_metadata(name: str, columns: list[str]) -> dict[str, str]:
    """Infer useful PHM labels while keeping explicit user metadata optional."""
    text = f"{name} {' '.join(columns)}".lower()
    result: dict[str, str] = {}
    system_terms = {
        "推进": "推进系统", "propulsion": "推进系统", "动力": "动力系统",
        "power": "电源系统", "电源": "电源系统", "热控": "热控系统",
        "thermal": "热控系统", "姿态": "姿态控制系统", "attitude": "姿态控制系统",
    }
    for term, label in system_terms.items():
        if term in text:
            result["system"] = label
            break
    component_terms = {
        "pressure": "压力测点", "temperature": "温度测点", "pump": "泵",
        "valve": "阀门", "battery": "蓄电池", "涡轮": "涡轮", "泵": "泵",
        "阀": "阀门", "传感器": "传感器",
    }
    for term, label in component_terms.items():
        if term in text:
            result["component"] = label
            break
    fault_terms = {
        "leak": "泄漏", "泄漏": "泄漏", "pressure_drop": "压力下降",
        "温升": "温度升高", "overheat": "温度升高", "偏置": "传感器偏置",
        "fault": "故障数据", "故障": "故障数据",
    }
    for term, label in fault_terms.items():
        if term in text:
            result["fault_type"] = label
            break
    return result


def _csv_rows(path: Path) -> tuple[list[str], Iterator[dict[str, Any]]]:
    handle = path.open("r", encoding="utf-8-sig", newline="")
    sample = handle.read(8192)
    handle.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(handle, dialect=dialect)
    columns = [(_text(x) or f"column_{i + 1}") for i, x in enumerate(reader.fieldnames or [])]
    if len(columns) > MAX_COLUMNS:
        handle.close()
        raise ValueError(f"列数超过上限 {MAX_COLUMNS}")

    def iterator() -> Iterator[dict[str, Any]]:
        try:
            for row in reader:
                yield {columns[i]: row.get(reader.fieldnames[i]) if reader.fieldnames else None for i in range(len(columns))}
        finally:
            handle.close()
    return columns, iterator()


def _json_rows(path: Path) -> tuple[list[str], Iterator[dict[str, Any]]]:
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        def lines() -> Iterator[dict[str, Any]]:
            with path.open("r", encoding="utf-8-sig") as handle:
                for line_number, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError(f"第 {line_number} 行不是对象")
                    yield value
        iterator = lines()
        first = next(iterator, None)
        if first is None:
            return [], iter(())
        columns = list(first)[:MAX_COLUMNS]
        return columns, chain([first], iterator)
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if isinstance(value, dict):
        value = value.get("rows", value.get("data", [value]))
    if not isinstance(value, list):
        raise ValueError("JSON 顶层必须是对象数组")
    rows = (row for row in value if isinstance(row, dict))
    first = next(rows, None)
    if first is None:
        return [], iter(())
    columns = list(first)[:MAX_COLUMNS]
    return columns, chain([first], rows)


def _xlsx_rows(path: Path) -> tuple[list[str], Iterator[dict[str, Any]]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ValueError("XLSX 读取依赖 openpyxl,当前运行环境未安装") from exc
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    row_iter = sheet.iter_rows(values_only=True)
    header = next(row_iter, None)
    columns = [_text(value) or f"column_{i + 1}" for i, value in enumerate(header or ())]
    if len(columns) > MAX_COLUMNS:
        workbook.close()
        raise ValueError(f"列数超过上限 {MAX_COLUMNS}")

    def iterator() -> Iterator[dict[str, Any]]:
        try:
            for values in row_iter:
                yield {columns[i]: values[i] if i < len(values) else None for i in range(len(columns))}
        finally:
            workbook.close()
    return columns, iterator()


def iter_rows(path: str | Path) -> tuple[list[str], Iterator[dict[str, Any]]]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return _csv_rows(file_path)
    if suffix in {".json", ".jsonl", ".ndjson"}:
        return _json_rows(file_path)
    if suffix == ".xlsx":
        return _xlsx_rows(file_path)
    raise ValueError(f"不支持的文件格式 {suffix or '(无扩展名)'}，支持 CSV、JSON、JSONL、XLSX")


def inspect_file(path: str | Path, *, display_name: str | None = None) -> dict[str, Any]:
    """Return a bounded-memory quality and classification report."""
    file_path = Path(path)
    columns, rows = iter_rows(file_path)
    roles = column_roles(columns)
    time_column, label_column = roles['time_column'], roles['fault_flag_column']
    time_start = time_end = previous_time = first_fault_time = None
    time_order_errors = label_errors = 0
    fault_counts = Counter()
    missing = Counter()
    invalid = Counter()
    numeric = Counter()
    sample: list[dict[str, Any]] = []
    row_count = 0
    for row in rows:
        row_count += 1
        if len(sample) < SAMPLE_ROWS:
            sample.append(row)
        for column in columns:
            value = row.get(column)
            if _text(value) == "":
                missing[column] += 1
            elif _finite_number(value):
                numeric[column] += 1
            elif column.lower() not in {"name", "label", "fault", "fault_type", "system", "component"}:
                invalid[column] += 1
        time_value = None
        if time_column and _finite_number(row.get(time_column)):
            time_value = float(row[time_column])
            if previous_time is not None and time_value <= previous_time:
                time_order_errors += 1
            if time_start is None:
                time_start = time_value
            time_end = previous_time = time_value
        if label_column:
            value = row.get(label_column)
            if _finite_number(value) and float(value) in (0, 1):
                flag = int(float(value))
                fault_counts[str(flag)] += 1
                if flag == 1 and first_fault_time is None and time_value is not None:
                    first_fault_time = time_value
            else:
                label_errors += 1
    numeric_columns = [column for column in columns if numeric[column] > 0]
    missing_total = sum(missing.values())
    invalid_total = sum(invalid.values())
    quality = "error" if row_count == 0 or not columns else "warning" if missing_total or invalid_total or time_order_errors or label_errors else "valid"
    return {
        "file_name": display_name or file_path.name,
        "format": file_path.suffix.lower().lstrip("."),
        "size_bytes": file_path.stat().st_size,
        "row_count": row_count,
        "columns": columns,
        "numeric_columns": numeric_columns,
        **roles,
        "numeric_parameter_columns": [column for column in roles['parameter_columns'] if column in numeric_columns],
        "time_summary": {"start": time_start, "end": time_end, "non_increasing_count": time_order_errors},
        "fault_label_summary": {"counts": dict(fault_counts), "first_fault_time": first_fault_time, "invalid_count": label_errors},
        "missing_values": dict(missing),
        "invalid_values": dict(invalid),
        "missing_value_count": missing_total,
        "invalid_value_count": invalid_total,
        "quality_status": quality,
        "quality_message": "可用于算法处理" if quality == "valid" else "存在缺失、非数值字段、时间顺序或标签问题，请复核" if quality == "warning" else "文件为空或没有表头",
        "inferred_metadata": _infer_metadata(display_name or file_path.name, columns),
        "sample": sample,
    }
