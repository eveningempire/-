"""
改进版阈值规则挖掘器（基于专家单调性先验）

特性：
- 支持指标选择：F1、Youden、G-mean
- 单变量最优阈值扫描（等分位网格）
- 每个故障自动评估 AND/OR 组合策略，择优
- 可限制每条规则的变量数（Top-K）
- K 折稳定性校验（阈值方差过大则剔除该变量）
- 结果导出为 JSON/YAML（与后端 import_mined_rules 命令结构兼容）

输入：
- 专家矩阵 D（fault → { var: "+"|"-" }），YAML/JSON
- 特征矩阵 X（pandas DataFrame，列名为变量名）
- 标签 y（pandas Series，值为故障名称字符串）

用法（示例）：
python delete/IMS/threshold_rule_miner.py \
  --D D_matrix.yaml \
  --features features.parquet \
  --labels labels.parquet \
  --out mined_rules.yaml \
  --metric f1 --kfold 5 --topk 3 --min-support 5 --min-precision 0.8 --auto-comb
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold


Metric = Literal["f1", "youden", "gmean"]
Comb = Literal["AND", "OR"]


def _safe_float_array(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr, dtype=float)
    return np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)


def load_D(path: Path | str) -> Dict[str, Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"D matrix not found: {path}")
    if p.suffix.lower() in {".yml", ".yaml"}:
        return yaml.safe_load(p.read_text(encoding="utf-8"))
    elif p.suffix.lower() == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    else:
        raise ValueError("只支持 YAML / JSON 的 D 矩阵文件")


def _score_binary(y_true: np.ndarray, y_pred: np.ndarray, metric: Metric) -> float:
    y_true = (y_true > 0).astype(int)
    y_pred = (y_pred > 0).astype(int)
    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    if metric == "f1":
        return f1_score(y_true, y_pred, zero_division=0)
    elif metric == "youden":
        # Youden's J = TPR - FPR
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        return tpr - fpr
    elif metric == "gmean":
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        return float(np.sqrt(max(tpr, 0.0) * max(tnr, 0.0)))
    else:
        raise ValueError(metric)


def _best_threshold(
    x_pos: np.ndarray,
    x_neg: np.ndarray,
    direction: str = "+",
    metric: Metric = "f1",
    n_grid: int = 50,
) -> Tuple[float, float]:
    """返回使指定 metric 最大的阈值 tau 及得分。
    网格基于整体分布 5%~95% 等分位。
    """
    x_pos = _safe_float_array(x_pos)
    x_neg = _safe_float_array(x_neg)
    grid = np.quantile(np.concatenate([x_pos, x_neg]), np.linspace(0.05, 0.95, n_grid))
    y_true = np.r_[np.ones_like(x_pos), np.zeros_like(x_neg)]

    best_tau, best_score = None, -1.0
    for tau in grid:
        if direction == "+":
            y_pred = np.r_[x_pos >= tau, x_neg >= tau]
        else:
            y_pred = np.r_[x_pos <= tau, x_neg <= tau]
        score = _score_binary(y_true, y_pred, metric)
        if score > best_score:
            best_tau, best_score = float(tau), float(score)
    # 极端情形回退
    if best_tau is None:
        best_tau = float(np.median(grid)) if grid.size else 0.0
        best_score = 0.0
    return best_tau, best_score


def _pick_topk_vars(
    X: pd.DataFrame,
    y_binary: np.ndarray,
    var_dir: Dict[str, str],
    metric: Metric,
    topk: int,
    n_grid: int,
) -> List[Tuple[str, float, str, float]]:
    """按单变量得分排序，选前 topk。
    返回 [(var, tau, dir, score), ...]。
    """
    pos = y_binary == 1
    neg = ~pos
    candidates: List[Tuple[str, float, str, float]] = []
    for var, sign in var_dir.items():
        if var not in X.columns:
            continue
        tau, sc = _best_threshold(X.loc[pos, var].values, X.loc[neg, var].values, sign, metric, n_grid)
        candidates.append((var, tau, sign, sc))
    candidates.sort(key=lambda t: t[3], reverse=True)
    return candidates[: max(1, topk)] if topk else candidates


def _kfold_stability(
    X: pd.DataFrame,
    y_binary: np.ndarray,
    var: str,
    direction: str,
    metric: Metric,
    n_grid: int,
    kfold: int,
    max_tau_cv_ratio: float,
) -> Optional[float]:
    """K 折上阈值方差/均值比控制稳定性。返回稳定阈值均值（不稳定则 None）。"""
    if kfold <= 1:
        pos = y_binary == 1
        neg = ~pos
        tau, _ = _best_threshold(X.loc[pos, var].values, X.loc[neg, var].values, direction, metric, n_grid)
        return float(tau)

    skf = StratifiedKFold(n_splits=kfold, shuffle=True, random_state=42)
    taus: List[float] = []
    for tr_idx, _ in skf.split(X, y_binary):
        x_tr = X.iloc[tr_idx]
        y_tr = y_binary[tr_idx]
        pos = y_tr == 1
        neg = ~pos
        tau, _ = _best_threshold(x_tr.loc[pos, var].values, x_tr.loc[neg, var].values, direction, metric, n_grid)
        taus.append(float(tau))
    taus = np.asarray(taus, dtype=float)
    mu = float(np.mean(taus))
    sd = float(np.std(taus))
    if mu == 0.0:
        return None
    if sd / abs(mu) > max_tau_cv_ratio:
        return None
    return mu


@dataclass
class Rule:
    fault: str
    thresholds: Dict[str, Dict[str, float | str]]  # var -> {tau, dir}
    comb: Comb

    def to_dict(self) -> Dict[str, Any]:
        return {"fault": self.fault, "comb": self.comb, "thresholds": self.thresholds}


def _eval_combination(
    X: pd.DataFrame,
    y_binary: np.ndarray,
    thresh_list: List[Tuple[str, float, str, float]],
    comb: Comb,
    metric: Metric,
) -> Tuple[float, np.ndarray]:
    """基于一组 (var, tau, dir) 在整集上生成布尔预测并计算得分。"""
    if not thresh_list:
        return -1.0, np.zeros(len(X), dtype=bool)
    masks: List[np.ndarray] = []
    for var, tau, sign, _ in thresh_list:
        if sign == "+":
            masks.append((X[var].values >= tau))
        else:
            masks.append((X[var].values <= tau))
    if comb == "AND":
        y_pred = np.logical_and.reduce(masks)
    else:
        y_pred = np.logical_or.reduce(masks)
    score = _score_binary(y_binary.astype(int), y_pred.astype(int), metric)
    return float(score), y_pred


def mine_rules(
    D: Dict[str, Dict[str, str]],
    X: pd.DataFrame,
    y: pd.Series,
    *,
    metric: Metric = "f1",
    n_grid: int = 50,
    topk: int = 3,
    kfold: int = 5,
    max_tau_cv_ratio: float = 0.25,
    min_support: int = 5,
    min_precision: float = 0.8,
    auto_comb: bool = True,
) -> List[Rule]:
    """主挖掘函数：按故障类别生成规则列表。"""
    if not isinstance(X, pd.DataFrame):
        raise TypeError("X 必须是 pandas.DataFrame")
    if not isinstance(y, (pd.Series, pd.Categorical)):
        raise TypeError("y 必须是 pandas.Series")

    rules: List[Rule] = []
    for fault, var_dir in D.items():
        # 二值化标签
        y_bin = (y.astype(str).values == str(fault))
        if int(np.sum(y_bin)) < max(1, min_support):
            # 正样本太少，跳过
            continue

        # 变量 Top-K 预选
        prelim = _pick_topk_vars(X, y_bin, var_dir, metric, topk, n_grid)
        if not prelim:
            continue

        # K 折稳定性校验并微调 tau
        stable: List[Tuple[str, float, str, float]] = []
        for var, tau, sign, sc in prelim:
            if var not in X.columns:
                continue
            tau_cv = _kfold_stability(X, y_bin, var, sign, metric, n_grid, kfold, max_tau_cv_ratio)
            if tau_cv is None:
                continue
            stable.append((var, float(tau_cv), sign, sc))
        if not stable:
            continue

        # AND/OR 自动比较
        comb_candidates: List[Comb] = ["AND", "OR"] if auto_comb else ["AND"]
        best_comb, best_score, best_pred = "AND", -1.0, None
        for comb in comb_candidates:
            sc, pred = _eval_combination(X, y_bin, stable, comb, metric)
            if sc > best_score:
                best_comb, best_score, best_pred = comb, sc, pred

        if best_pred is None:
            continue

        # 支持度与精度过滤
        support = int(np.sum(best_pred))
        precision = float(np.sum(best_pred & y_bin) / max(1, support))
        if support < min_support or precision < min_precision:
            continue

        thresholds = {var: {"tau": float(tau), "dir": sign} for (var, tau, sign, _) in stable}
        rules.append(Rule(fault=fault, thresholds=thresholds, comb=best_comb))

    return rules


def export_rules(rules: List[Rule], save_path: Path | str) -> None:
    p = Path(save_path)
    data = [r.to_dict() for r in rules]
    if p.suffix.lower() in {".yml", ".yaml"}:
        yaml.safe_dump(data, p.open("w", encoding="utf-8"), allow_unicode=True, sort_keys=False)
    elif p.suffix.lower() == ".json":
        json.dump(data, p.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)
    else:
        # 默认 YAML
        yaml.safe_dump(data, p.open("w", encoding="utf-8"), allow_unicode=True, sort_keys=False)
    print(f"[OK] 规则已导出：{p}")


def main() -> None:
    ap = argparse.ArgumentParser(description="改进版阈值规则挖掘器")
    ap.add_argument("--D", type=str, required=True, help="专家矩阵 D (yaml/json)")
    ap.add_argument("--features", type=str, required=True, help="特征表 (parquet/csv)")
    ap.add_argument("--labels", type=str, required=True, help="标签表 (parquet/csv)，需包含列 'fault'")
    ap.add_argument("--out", type=str, required=True, help="导出路径 (yaml/json)")
    ap.add_argument("--metric", type=str, default="f1", choices=["f1", "youden", "gmean"], help="评价指标")
    ap.add_argument("--n-grid", type=int, default=50, help="阈值网格大小")
    ap.add_argument("--topk", type=int, default=3, help="每条规则最多变量数（0 表示不限制）")
    ap.add_argument("--kfold", type=int, default=5, help="K 折稳定性校验折数（<=1 关闭）")
    ap.add_argument("--max-tau-cv-ratio", type=float, default=0.25, help="阈值方差/均值容忍度")
    ap.add_argument("--min-support", type=int, default=5, help="最小触发支持度")
    ap.add_argument("--min-precision", type=float, default=0.8, help="最小精度")
    ap.add_argument("--auto-comb", action="store_true", help="在 AND 与 OR 间自动选择")

    args = ap.parse_args()

    D = load_D(args.D)

    fpath = Path(args.features)
    if fpath.suffix.lower() == ".parquet":
        X = pd.read_parquet(fpath)
    else:
        X = pd.read_csv(fpath)

    lpath = Path(args.labels)
    if lpath.suffix.lower() == ".parquet":
        ydf = pd.read_parquet(lpath)
    else:
        ydf = pd.read_csv(lpath)
    if "fault" not in ydf.columns:
        raise ValueError("labels 文件中必须包含列 'fault'（字符串类别）")

    rules = mine_rules(
        D,
        X=X,
        y=ydf["fault"],
        metric=args.metric, n_grid=args.n_grid, topk=args.topk,
        kfold=args.kfold, max_tau_cv_ratio=args.max_tau_cv_ratio,
        min_support=args.min_support, min_precision=args.min_precision,
        auto_comb=bool(args.auto_comb),
    )

    export_rules(rules, args.out)


if __name__ == "__main__":
    main()


