"""Validation and normalization for large batches of algorithm parameter files."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

SUPPORTED_PARAMETER_SUFFIXES = {'.csv', '.json', '.jsonl', '.ndjson', '.yaml', '.yml'}


def _load(path: Path) -> Any:
    suffix = path.suffix.lower()
    if suffix == '.csv':
        with path.open('r', encoding='utf-8-sig', newline='') as handle:
            return list(csv.DictReader(handle))
    if suffix in {'.jsonl', '.ndjson'}:
        with path.open('r', encoding='utf-8-sig') as handle:
            return [json.loads(line) for line in handle if line.strip()]
    if suffix in {'.yaml', '.yml'}:
        try:
            import yaml
        except ImportError as exc:
            raise ValueError('YAML 参数文件需要 PyYAML,当前环境未安装') from exc
        with path.open('r', encoding='utf-8-sig') as handle:
            return yaml.safe_load(handle)
    with path.open('r', encoding='utf-8-sig') as handle:
        return json.load(handle)


def _flatten(value: Any, prefix: str = '') -> dict[str, Any]:
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            name = f'{prefix}.{key}' if prefix else str(key)
            output.update(_flatten(item, name))
        return output
    return {prefix: value}


def validate(path: str | Path, *, filename: str | None = None) -> dict[str, Any]:
    file_path = Path(path)
    if file_path.suffix.lower() not in SUPPORTED_PARAMETER_SUFFIXES:
        raise ValueError(f'不支持的参数文件格式: {file_path.suffix or "无扩展名"}')
    payload = _load(file_path)
    records = payload if isinstance(payload, list) else payload.get('parameters', payload.get('data', payload)) if isinstance(payload, dict) else payload
    if isinstance(records, dict): records = [records]
    if not isinstance(records, list) or not records:
        raise ValueError('参数文件必须包含一个对象或对象数组')
    normalized = []
    errors = []
    for row_index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            errors.append({'row': row_index, 'field': '', 'message': '记录不是对象'})
            continue
        flat = _flatten(record)
        clean = {}
        for key, value in flat.items():
            key = key.strip()
            if not key:
                errors.append({'row': row_index, 'field': '', 'message': '参数名为空'})
                continue
            if value in (None, ''):
                errors.append({'row': row_index, 'field': key, 'message': '参数值为空'})
                continue
            if isinstance(value, str):
                value = value.strip()
                if value.lower() in {'true', 'false'}: value = value.lower() == 'true'
                else:
                    try: value = float(value) if '.' in value else int(value)
                    except ValueError: pass
            if isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isfinite(float(value)):
                errors.append({'row': row_index, 'field': key, 'message': '数值必须是有限值'})
                continue
            # Generic safety limits catch accidental unit/scale mistakes while
            # allowing physical parameter files to define their own ranges later.
            if isinstance(value, (int, float)) and not isinstance(value, bool) and abs(float(value)) > 1e12:
                errors.append({'row': row_index, 'field': key, 'message': '数值超出通用范围 ±1e12'})
                continue
            clean[key] = value
        normalized.append(clean)
    status = 'valid' if not errors else 'warning'
    return {'file_name': filename or file_path.name, 'format': file_path.suffix.lower().lstrip('.'), 'record_count': len(records), 'parameter_count': len({k for row in normalized for k in row}), 'status': status, 'errors': errors, 'normalized': normalized[:100], 'truncated': len(normalized) > 100}
