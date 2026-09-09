from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
from django.conf import settings

ROOT = settings.BASE_DIR / "integrations" / "wujiaxin"

def _json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return default

@lru_cache(maxsize=1)
def fmeca_records():
    return _json(ROOT / "knowledge" / "fmeca.json", [])

def node_catalog():
    result = []
    for path in sorted((ROOT / "knowledge" / "nodebaseinfo").glob("*.json")):
        records = _json(path, [])
        attrs = {item.get("baseinfo"): item.get("attribute") for item in records if "baseinfo" in item}
        flight = next((item.get("attributevalue") for item in records if item.get("consumerinfo") == "已飞行次数"), None)
        result.append({"code": path.stem, "name": attrs.get("产品名称", path.stem), "manufacturer": attrs.get("生产厂家"), "flight_count": flight})
    return result

def node_detail(code: str):
    safe_code = "".join(c for c in code if c.isalnum() or c in "_-")
    base = _json(ROOT / "knowledge" / "nodebaseinfo" / f"{safe_code}.json", [])
    life = _json(ROOT / "knowledge" / "nodelife" / f"{safe_code}.json", [])
    return {"code": safe_code, "base_info": base, "life_info": life}

def asset_catalog():
    extensions = {"model": {".pt", ".pkl"}, "simulation": {".slx", ".mat", ".csv"}, "algorithm": {".py"}}
    groups = {}
    for key, suffixes in extensions.items():
        files = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix.lower() in suffixes]
        groups[key] = {"count": len(files), "size_mb": round(sum(p.stat().st_size for p in files) / 1048576, 2), "files": [str(p.relative_to(ROOT)).replace("\\", "/") for p in files]}
    return groups

def integration_summary():
    assets = asset_catalog()
    return {"source": "吴嘉欣_SY2424110", "mode": "adapter", "fmeca_count": len(fmeca_records()), "component_count": len(node_catalog()), "model_count": assets["model"]["count"], "simulation_count": assets["simulation"]["count"], "algorithm_reference_count": assets["algorithm"]["count"]}
