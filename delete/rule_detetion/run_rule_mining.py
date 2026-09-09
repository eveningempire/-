#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从本目录的 D 矩阵与 CSV 数据集中挖掘阈值规则，并导出为可直接导入平台的 YAML/JSON。

数据约定（可按参数覆盖）：
- D 矩阵：delete/rule_detetion/8.7_D-Matrix.xls
- 正常样本：delete/rule_detetion/normal/Health_processed_signals.csv
- 故障样本：delete/rule_detetion/fault_data/*.csv  （文件名前缀为故障名）

变量命名：
- 若 D 矩阵中的变量名与 CSV 列名不同，可通过 --d2csv-map 指定 YAML/JSON 映射：
  { D变量名: CSV列名, ... }
- 若导出的规则变量名需要转换为平台运行时变量名，可通过 --csv2platform-map 指定映射：
  { CSV列名或D变量名: 平台变量名, ... }

导出的规则结构与后端 import_mined_rules 管理命令兼容：
  - fault: 故障名
  - comb: AND|OR
  - thresholds: { var: { tau: float, dir: "+"|"-" } }
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

# 同目录引入挖掘核心
from threshold_rule_miner import mine_rules_from_D  # type: ignore


def _read_text_map(path: Optional[str]) -> Dict[str, str]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"映射文件不存在: {path}")
    if p.suffix.lower() in {".yml", ".yaml"}:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    elif p.suffix.lower() == ".json":
        return json.loads(p.read_text(encoding="utf-8")) or {}
    else:
        raise ValueError("映射文件仅支持 .yaml/.yml/.json")


def _load_D_from_excel(path: str) -> Dict[str, Dict[str, str]]:
    """尽量鲁棒地从 Excel 读取 D 矩阵。
    期望形如：行=故障名，列=变量名，单元格值为 '+' 或 '-' 或空。
    """
    xls = pd.read_excel(path, sheet_name=0, header=0)
    df = xls.copy()
    # 尝试定位故障列：
    # 如果第一列不含正负号且像是名字列，则视作故障列
    first_col = df.columns[0]
    def _has_pm(series: pd.Series) -> bool:
        vals = series.astype(str).str.strip()
        return vals.isin(["+", "-", "+1", "-1", "1", "-1"]).any()

    # 变量列候选：包含正负号的列
    var_cols = [c for c in df.columns if _has_pm(df[c])]
    if not var_cols:
        # 回退：除第一列以外都当作变量列
        var_cols = list(df.columns[1:])
    # 故障名列
    if first_col not in var_cols:
        fault_names = df[first_col].astype(str).str.strip().tolist()
        mat = df[var_cols]
    else:
        # 第一列本身也是变量列时，尝试用索引作为故障名
        df = df.reset_index().rename(columns={"index": "fault"})
        fault_names = [str(v) for v in range(len(df))]
        mat = df[var_cols]

    D: Dict[str, Dict[str, str]] = {}
    for i, fault in enumerate(fault_names):
        row = mat.iloc[i]
        obj: Dict[str, str] = {}
        for col in var_cols:
            val = str(row[col]).strip()
            if val in {"+", "+1", "1"}:
                obj[col] = "+"
            elif val in {"-", "-1"}:
                obj[col] = "-"
        if obj:
            D[str(fault)] = obj
    if not D:
        raise ValueError("Excel 中未解析出有效的 D 矩阵（仅支持 '+'/'-' 标记）")
    return D


def _read_csv_lenient(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding="gbk")
    except Exception:
        return pd.read_csv(path)


def _infer_fault_from_filename(path: Path) -> str:
    name = path.stem
    return name.split("_")[0]


def _auto_map_d_to_csv(d_vars: List[str], sample_columns: List[str]) -> Dict[str, str]:
    """基于简单启发式从 CSV 列名中自动为 D 变量寻找对应列。
    规则：
    - 忽略大小写、空格、下划线等；
    - 先做完全相等匹配；否则做包含/被包含匹配；再做最长公共子串长度>3 的近似匹配；
    - 一对一贪心选取，避免重复命中。
    """
    import re
    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())

    scols = list(sample_columns)
    ncols = [norm(c) for c in scols]
    used = set()
    mapping: Dict[str, str] = {}
    for dv in d_vars:
        ndv = norm(dv)
        # 1) exact
        for j, nc in enumerate(ncols):
            if j in used:
                continue
            if nc == ndv:
                mapping[dv] = scols[j]
                used.add(j)
                break
        if dv in mapping:
            continue
        # 2) contains
        best_j, best_len = None, 0
        for j, nc in enumerate(ncols):
            if j in used:
                continue
            if ndv and (ndv in nc or nc in ndv):
                l = min(len(ndv), len(nc))
                if l > best_len:
                    best_len, best_j = l, j
        if best_j is not None:
            mapping[dv] = scols[best_j]
            used.add(best_j)
            continue
        # 3) rough lcs > 3
        def lcs(a: str, b: str) -> int:
            dp = [[0]*(len(b)+1) for _ in range(len(a)+1)]
            best = 0
            for i in range(1, len(a)+1):
                for k in range(1, len(b)+1):
                    if a[i-1] == b[k-1]:
                        dp[i][k] = dp[i-1][k-1] + 1
                        best = max(best, dp[i][k])
            return best
        best_j, best_s = None, 0
        for j, nc in enumerate(ncols):
            if j in used:
                continue
            s = lcs(ndv, nc)
            if s > best_s:
                best_s, best_j = s, j
        if best_j is not None and best_s >= 4:
            mapping[dv] = scols[best_j]
            used.add(best_j)
    return mapping


def build_dataset(
    normal_csv: str,
    fault_dir: str,
    d2csv_map: Dict[str, str],
    *,
    sample_stride: int = 20,
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """将 normal + fault_data CSV 打包为 X/y/groups。
    - 逐行采样（每 sample_stride 取一行），标签为文件对应的故障名/Normal，groups 为文件名。
    - 仅保留 D→CSV 映射后的列；若映射为空，则使用 CSV 与 D 的交集列。
    """
    all_rows: List[pd.DataFrame] = []
    labels: List[str] = []
    groups: List[str] = []

    # 收集变量名（基于映射）。如未提供映射，尝试自动映射。
    mapped_vars = set(d2csv_map.values()) if d2csv_map else None

    # Normal
    ndf = _read_csv_lenient(normal_csv)
    if not d2csv_map:
        # 自动构建 D→CSV 映射（从 normal 列名与 D 变量推断）
        # D 变量暂时未知，这里先不裁剪，留到后续对齐时再处理
        pass
    else:
        if mapped_vars:
            ndf = ndf[[c for c in ndf.columns if c in mapped_vars]]
    # 采样
    ndf_s = ndf.iloc[::max(1, sample_stride)].reset_index(drop=True)
    all_rows.append(ndf_s)
    labels += ["Normal"] * len(ndf_s)
    groups += [Path(normal_csv).stem] * len(ndf_s)

    # Faults
    fpaths = sorted(Path(fault_dir).glob("*.csv"))
    for fp in fpaths:
        df = _read_csv_lenient(str(fp))
        if d2csv_map and mapped_vars:
            df = df[[c for c in df.columns if c in mapped_vars]]
        df_s = df.iloc[::max(1, sample_stride)].reset_index(drop=True)
        all_rows.append(df_s)
        fault_name = _infer_fault_from_filename(fp)
        labels += [fault_name] * len(df_s)
        groups += [fp.stem] * len(df_s)

    # 对齐列（取并集缺失填 0）
    cols = sorted({c for df in all_rows for c in df.columns})
    aligned = [df.reindex(columns=cols).fillna(0.0) for df in all_rows]
    X_csv = pd.concat(aligned, axis=0, ignore_index=True)

    X = X_csv
    # 若提供了 D→CSV 映射，则将列名改回 D 变量名；否则尝试自动映射
    if d2csv_map:
        inv = {v: k for k, v in d2csv_map.items()}
        X = X.rename(columns=inv)
    else:
        # 自动映射：取所有列名做样本，按照 D 的变量名推断映射
        # 注意：此函数在 main 中拿到 D 后再次对齐
        pass

    y = pd.Series(labels, name="fault")
    g = pd.Series(groups, name="file_id")
    return X, y, g


def apply_output_name_mapping(rules: List[Dict[str, Any]], name_map: Dict[str, str]) -> List[Dict[str, Any]]:
    if not name_map:
        return rules
    remapped: List[Dict[str, Any]] = []
    for r in rules:
        th_new: Dict[str, Any] = {}
        for var, cfg in (r.get("thresholds") or {}).items():
            target = name_map.get(var, var)
            th_new[target] = dict(cfg)
        r2 = dict(r)
        r2["thresholds"] = th_new
        remapped.append(r2)
    return remapped


def main() -> None:
    ap = argparse.ArgumentParser(description="从本目录数据集挖掘规则并导出")
    ap.add_argument("--D", type=str, default=str(Path("delete/rule_detetion/8.7_D-Matrix.xls")), help="D 矩阵路径（可为 .xls/.xlsx/.yaml/.json）")
    ap.add_argument("--normal", type=str, default=str(Path("delete/rule_detetion/normal/Health_processed_signals.csv")), help="正常数据 CSV")
    ap.add_argument("--fault-dir", type=str, default=str(Path("delete/rule_detetion/fault_data")), help="故障数据目录（内含 *.csv）")
    ap.add_argument("--out", type=str, default=str(Path("delete/rule_detetion/mined_rules.yaml")), help="导出规则文件（.yaml/.json）")
    ap.add_argument("--d2csv-map", type=str, default="", help="D 变量名 → CSV 列名 映射文件（.yaml/.json，可选）")
    ap.add_argument("--csv2platform-map", type=str, default="", help="CSV/D 变量名 → 平台变量名 映射文件（.yaml/.json，可选）")
    ap.add_argument("--metric", type=str, default="f1", choices=["f1", "youden", "gmean"], help="评估指标")
    ap.add_argument("--comb", type=str, default="AND", choices=["AND", "OR"], help="默认组合（与 D 单调方向结合）")
    ap.add_argument("--auto-comb", action="store_true", help="为每个故障在 AND 与 OR 间自动选择更优组合")
    ap.add_argument("--n-grid", type=int, default=50, help="阈值网格大小")
    ap.add_argument("--sample-stride", type=int, default=20, help="行采样步长（每 N 行取 1 行）")
    ap.add_argument("--min-support", type=int, default=5, help="最小触发数")
    ap.add_argument("--min-precision", type=float, default=0.8, help="最小精度")

    args = ap.parse_args()

    # 读取 D：支持 Excel 或 YAML/JSON
    D_path = Path(args.D)
    if D_path.suffix.lower() in {".xls", ".xlsx"}:
        D = _load_D_from_excel(str(D_path))
    elif D_path.suffix.lower() in {".yml", ".yaml"}:
        D = yaml.safe_load(D_path.read_text(encoding="utf-8"))
    elif D_path.suffix.lower() == ".json":
        D = json.loads(D_path.read_text(encoding="utf-8"))
    else:
        raise ValueError("D 文件仅支持 .xls/.xlsx/.yaml/.yml/.json")

    d2csv_map = _read_text_map(args.d2csv_map)
    csv2plat_map = _read_text_map(args.csv2platform_map)

    # 构建数据集（逐行采样）
    X, y, groups = build_dataset(
        normal_csv=args.normal,
        fault_dir=args.fault_dir,
        d2csv_map=d2csv_map,
        sample_stride=max(1, int(args.sample_stride)),
    )

    # 与 D 对齐：仅保留 D 中出现的变量（存在于 X 的列）。
    d_vars = sorted({v for vars_ in D.values() for v in vars_.keys()})
    keep = [c for c in d_vars if c in X.columns]
    if not keep:
        # 尝试自动映射 D→CSV：基于 normal 与任一故障文件的列名样本
        sample_cols = set()
        try:
            sample_cols.update(_read_csv_lenient(args.normal).columns.tolist())  # type: ignore[name-defined]
        except Exception:
            pass
        try:
            any_fault = next(iter(sorted(Path(args.fault_dir).glob("*.csv"))))  # type: ignore[name-defined]
            sample_cols.update(_read_csv_lenient(str(any_fault)).columns.tolist())
        except Exception:
            pass
        auto_map = _auto_map_d_to_csv(d_vars, sorted(sample_cols)) if sample_cols else {}
        if auto_map:
            inv = {v: k for k, v in auto_map.items()}
            X = X.rename(columns=inv)
            keep = [c for c in d_vars if c in X.columns]
        if not keep:
            raise ValueError("X 与 D 无公共变量，且自动映射失败；请提供 --d2csv-map")
    X = X[keep]

    # 挖掘
    if args.auto_comb:
        # 分别用 AND/OR 生成候选，然后逐故障选择更优
        rules_and = mine_rules_from_D(
            D=D, X=X, y=y, groups=groups, metric=args.metric, comb="AND",
            n_grid=int(args.n_grid), min_support=int(args.min_support), min_precision=float(args.min_precision)
        )
        rules_or = mine_rules_from_D(
            D=D, X=X, y=y, groups=groups, metric=args.metric, comb="OR",
            n_grid=int(args.n_grid), min_support=int(args.min_support), min_precision=float(args.min_precision)
        )

        # 评估函数
        def score_rule(rule_obj) -> float:
            fault = getattr(rule_obj, "fault", None) or rule_obj.get("fault")  # type: ignore[union-attr]
            comb = getattr(rule_obj, "comb", None) or rule_obj.get("comb")    # type: ignore[union-attr]
            # 阈值
            thresh_map = getattr(rule_obj, "thresh_map", None)
            if thresh_map is None:
                thresh_map = rule_obj.get("thresholds")  # type: ignore[union-attr]
                # thresholds 字典形式：var -> {tau, dir}
                thresh_map = {k: (float(v.get("tau", 0.0)), str(v.get("dir", "+"))) for k, v in (thresh_map or {}).items()}
            # 生成预测
            masks = []
            for var, val in thresh_map.items():
                if isinstance(val, tuple) and len(val) == 2:
                    tau, direc = float(val[0]), str(val[1])
                else:
                    tau, direc = float(val[0]), str(val[1])  # 容错
                if var not in X.columns:
                    continue
                if direc == "+":
                    masks.append(X[var].values >= tau)
                else:
                    masks.append(X[var].values <= tau)
            if not masks:
                return -1.0
            y_pred = np.logical_and.reduce(masks) if comb == "AND" else np.logical_or.reduce(masks)
            y_true = (y.values.astype(str) == str(fault))
            # 使用与 miner 相同指标
            # 本地实现指标
            def _metric_score(metric: str) -> float:
                m = metric.lower()
                yt = y_true.astype(int)
                yp = y_pred.astype(int)
                tp = int(np.sum((yt == 1) & (yp == 1)))
                tn = int(np.sum((yt == 0) & (yp == 0)))
                fp = int(np.sum((yt == 0) & (yp == 1)))
                fn = int(np.sum((yt == 1) & (yp == 0)))
                if m == "f1":
                    from sklearn.metrics import f1_score as _skf1  # type: ignore
                    return float(_skf1(yt, yp, zero_division=0))
                if m == "youden":
                    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
                    return float(tpr - fpr)
                if m == "gmean":
                    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                    tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0
                    return float(np.sqrt(max(tpr, 0.0) * max(tnr, 0.0)))
                return 0.0
            return _metric_score(args.metric)

        # 合并：按故障挑更优（若只在一侧存在，取存在者）
        by_fault: Dict[str, Any] = {}
        for r in rules_and:
            by_fault[getattr(r, "fault")] = (r, score_rule(r))
        for r in rules_or:
            f = getattr(r, "fault")
            sc = score_rule(r)
            if f not in by_fault or sc > by_fault[f][1]:
                by_fault[f] = (r, sc)
        rules = [v[0] for v in by_fault.values()]
    else:
        rules = mine_rules_from_D(
            D=D,
            X=X,
            y=y,
            groups=groups,
            metric=args.metric,
            comb=args.comb,
            n_grid=int(args.n_grid),
            min_support=int(args.min_support),
            min_precision=float(args.min_precision),
        )

    # 导出前可按需要将变量名映射到平台名
    rules_dicts = [r.to_dict() for r in rules]
    if csv2plat_map:
        rules_dicts = apply_output_name_mapping(rules_dicts, csv2plat_map)

    # 保存（保持 export_rules 的行为一致）
    out_path = Path(args.out)
    if out_path.suffix.lower() in {".yml", ".yaml"}:
        yaml.safe_dump(rules_dicts, out_path.open("w", encoding="utf-8"), allow_unicode=True, sort_keys=False)
    elif out_path.suffix.lower() == ".json":
        json.dump(rules_dicts, out_path.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)
    else:
        yaml.safe_dump(rules_dicts, out_path.open("w", encoding="utf-8"), allow_unicode=True, sort_keys=False)

    print(f"[OK] 已导出规则：{out_path}  （共 {len(rules_dicts)} 条）")


if __name__ == "__main__":
    main()


