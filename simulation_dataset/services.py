from __future__ import annotations
import csv
import io
import re
import zipfile
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from django.conf import settings

ARCHIVE = settings.BASE_DIR / "integrations" / "qianze_simulation_data" / "simulate_data_+1.zip"
ROOT = "simulate_data_+1/"
CATEGORY_NAMES = {
    "baseline": "正常基线", "bengqixi": "泵气蚀", "wolun": "涡轮退化", "guanlu": "管路故障",
    "zhufa": "主阀故障", "ranqi": "燃气系统", "ranshao": "燃烧故障", "penguan": "喷管故障",
    "tvc": "TVC故障", "rcs": "RCS故障", "geduo": "栅格舵故障", "kongzhiqi": "控制器故障",
    "tuoluoyi_piancha": "陀螺仪偏差", "tuoluoyi_kasi": "陀螺仪卡死",
}
NAME_RE = re.compile(r"^fc(?P<flight>\d+)(?:_t(?P<time>\d+))?(?P<processed>_P)?\.csv$")

def _safe_member(member: str) -> str:
    member = member.replace("\\", "/").lstrip("/")
    if ".." in member.split("/") or not member.startswith(ROOT): raise ValueError("invalid member")
    return member

@lru_cache(maxsize=1)
def catalog():
    groups = defaultdict(lambda: {"files": 0, "raw": 0, "processed": 0, "bytes": 0, "flights": set(), "times": set()})
    with zipfile.ZipFile(ARCHIVE) as zf:
        members = [x for x in zf.infolist() if x.filename.lower().endswith(".csv")]
        for info in members:
            parts = info.filename.split("/")
            if len(parts) != 3: continue
            category, filename = parts[1], parts[2]
            match = NAME_RE.match(filename)
            if not match: continue
            group = groups[category]; group["files"] += 1; group["bytes"] += info.file_size
            processed = bool(match.group("processed")); group["processed" if processed else "raw"] += 1
            group["flights"].add(int(match.group("flight")))
            if match.group("time"): group["times"].add(int(match.group("time")))
        categories = []
        for key, value in sorted(groups.items()):
            categories.append({"key": key, "name": CATEGORY_NAMES.get(key, key), "kind": "baseline" if key == "baseline" else "fault_degradation", "files": value["files"], "raw_files": value["raw"], "processed_files": value["processed"], "size_mb": round(value["bytes"] / 1048576, 2), "flight_counts": sorted(value["flights"]), "injection_times": sorted(value["times"])})
    return {"dataset": "simulate_data_+1", "source": "钱泽_SY2424114/一院项目/仿真数据", "storage": "zip_stream", "archive_size_mb": round(ARCHIVE.stat().st_size / 1048576, 2), "csv_files": sum(x["files"] for x in categories), "sample_pairs": sum(x["raw_files"] for x in categories), "categories": categories}

def files(category: str):
    if category not in CATEGORY_NAMES: raise ValueError("unknown category")
    rows = []
    with zipfile.ZipFile(ARCHIVE) as zf:
        for info in zf.infolist():
            prefix = f"{ROOT}{category}/"
            if not info.filename.startswith(prefix) or not info.filename.endswith(".csv"): continue
            match = NAME_RE.match(Path(info.filename).name)
            if match: rows.append({"member": info.filename, "name": Path(info.filename).name, "flight_count": int(match.group("flight")), "injection_time": int(match.group("time")) if match.group("time") else None, "data_type": "derived_parameters" if match.group("processed") else "raw_state", "size_mb": round(info.file_size / 1048576, 2)})
    return sorted(rows, key=lambda x: (x["flight_count"], x["injection_time"] or -1, x["data_type"]))

def preview(member: str, limit: int = 50):
    member = _safe_member(member); limit = max(1, min(limit, 200))
    with zipfile.ZipFile(ARCHIVE) as zf:
        info = zf.getinfo(member)
        with zf.open(info) as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")
            reader = csv.reader(text); columns = next(reader); rows = []
            fault_counts = Counter()
            for index, row in enumerate(reader):
                if index >= limit: break
                rows.append(row); fault_counts[row[-1] if row else ""] += 1
    return {"member": member, "columns": columns, "rows": rows, "preview_rows": len(rows), "file_size_mb": round(info.file_size / 1048576, 2), "fault_flag_counts_in_preview": fault_counts}
