# =========================================
# threshold_rule_miner.py
# =========================================
from __future__ import annotations
import yaml, json
from pathlib import Path
from typing import Dict, List, Tuple, Literal, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, confusion_matrix
from sklearn.model_selection import GroupKFold
from collections import OrderedDict

Metric = Literal["f1"]        # 你可扩展 gmean, youden 等
Comb   = Literal["AND", "OR"] # 规则逻辑

# ------------------------------------------------------------------
# 1. 读取 / 定义专家矩阵  (fault → {var: "+"|"–"})
# ------------------------------------------------------------------
def load_D(path: Path | str) -> Dict[str, Dict[str, str]]:
    """YAML 或 JSON，内容示例：
    BearingMosun:
      RotorMotorCurrent: "+"
      RotorVibRMS: "+"
    BreakLu:
      RotorSpeed: "-"
      FrictionTorque: "+"
    """
    p = Path(path)
    if p.suffix.lower() in {".yml", ".yaml"}:
        return yaml.safe_load(p.read_text(encoding="utf-8"))
    elif p.suffix.lower() == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    else:
        raise ValueError("只支持 YAML / JSON")


# ------------------------------------------------------------------
# 2. 单变量阈值搜索
# ------------------------------------------------------------------
def _best_threshold(
    x_pos: np.ndarray,
    x_neg: np.ndarray,
    direction: str = "+",
    metric: Metric = "f1",
    n_grid: int = 50,
) -> Tuple[float, float]:
    """返回最优阈值 τ 及指标值"""
    # 构建候选网格：在正负样本整体分布的 5%~95% 之间等距
    qs = np.linspace(5, 95, n_grid)
    grid = np.quantile(np.concatenate([x_pos, x_neg]), qs / 100.0)
    y_true = np.r_[np.ones_like(x_pos), np.zeros_like(x_neg)]

    best_tau, best_score = None, -1.0
    for tau in grid:
        if direction == "+":
            y_pred = np.r_[x_pos >= tau, x_neg >= tau]
        else:  # "-"
            y_pred = np.r_[x_pos <= tau, x_neg <= tau]

        if metric == "f1":
            score = f1_score(y_true, y_pred, zero_division=0)
        else:
            raise NotImplementedError(metric)

        if score > best_score:
            best_tau, best_score = tau, score
    return float(best_tau), float(best_score)


# ------------------------------------------------------------------
# 3. 组合规则并评估
# ------------------------------------------------------------------
class Rule:
    """一个故障类别的规则：{var: (tau, dir)} + comb"""

    def __init__(self, fault: str, thresh_map: Dict[str, Tuple[float, str]], comb: Comb):
        self.fault       = fault
        self.thresh_map  = thresh_map  # {var: (tau, "+"/"-")}
        self.comb        = comb

    # -------- 应用到一行/批量 -------------
    def __call__(self, X: pd.DataFrame) -> np.ndarray:
        conds = []
        for var, (tau, sign) in self.thresh_map.items():
            if sign == "+":
                conds.append(X[var].values >= tau)
            else:
                conds.append(X[var].values <= tau)

        if self.comb == "AND":
            mask = np.logical_and.reduce(conds)
        else:  # OR
            mask = np.logical_or.reduce(conds)
        return mask  # bool array

    # --------- 可读字符串 --------------
    def to_text(self, digits: int = 3) -> str:
        parts = []
        for var, (t, s) in self.thresh_map.items():
            op = "≥" if s == "+" else "≤"
            parts.append(f"{var} {op} {round(t, digits)}")
        glue = " ∧ " if self.comb == "AND" else " ∨ "
        return glue.join(parts)

    # --------- 方便导出 ---------------
    def to_dict(self) -> Dict:
        return {
            "fault": self.fault,
            "comb" : self.comb,
            "thresholds": {v: {"tau": tau, "dir": d} for v, (tau, d) in self.thresh_map.items()},
        }


# ------------------------------------------------------------------
# 4. 主挖掘函数
# ------------------------------------------------------------------
def mine_rules_from_D(
    D: Dict[str, Dict[str, str]],
    X: pd.DataFrame,
    y: pd.Series,
    groups: Optional[pd.Series] = None,
    metric: Metric = "f1",
    comb: Comb = "AND",
    n_grid: int = 50,
    min_support: int = 5,
    min_precision: float = 0.8,
) -> List[Rule]:
    """返回满足阈值的规则列表"""
    rules: List[Rule] = []

    # 若未给 groups，用全部样本单折验证
    splitter = GroupKFold(n_splits=5) if groups is not None else None

    for fault, var_dir in D.items():
        print(f"\n>>> Mining {fault}")
        # 提取正负样本索引
        pos_idx = y == fault
        neg_idx = y != fault
        if pos_idx.sum() < min_support:
            print(f"  - 样本过少({pos_idx.sum()}), 跳过")
            continue

        # 为该故障的每个变量求阈值
        thresh_map = OrderedDict()
        for var, sign in var_dir.items():
            x_pos = X.loc[pos_idx, var].values
            x_neg = X.loc[neg_idx, var].values
            tau, score = _best_threshold(x_pos, x_neg, sign, metric, n_grid)
            print(f"    {var} ({sign})  best {metric}={score:.3f}  τ={tau:.3f}")
            thresh_map[var] = (tau, sign)

        rule = Rule(fault, thresh_map, comb)

        # -------------- 交叉验证 --------------
        if splitter:
            y_true_all, y_pred_all = [], []
            for tr_idx, val_idx in splitter.split(X, y, groups):
                y_true_all.append((y.iloc[val_idx] == fault).values)
                y_pred_all.append(rule(X.iloc[val_idx]))
            y_true_all = np.concatenate(y_true_all)
            y_pred_all = np.concatenate(y_pred_all)
        else:  # 单折
            y_true_all = (y == fault).values
            y_pred_all = rule(X)

        prec = (y_true_all & y_pred_all).sum() / max(y_pred_all.sum(), 1)
        rec  = (y_true_all & y_pred_all).sum() / y_true_all.sum()
        f1   = f1_score(y_true_all, y_pred_all, zero_division=0)

        print(f"    --> CV precision={prec:.3f}, recall={rec:.3f}, f1={f1:.3f}")

        if y_pred_all.sum() >= min_support and prec >= min_precision:
            rules.append(rule)
            print("    ✓ rule accepted")
        else:
            print("    ✗ rule rejected (support/precision不足)")

    return rules


# ------------------------------------------------------------------
# 5. 导出
# ------------------------------------------------------------------
def export_rules(rules: List[Rule], save_path: Path | str, fmt: Literal["txt","yaml","json"]="txt"):
    p = Path(save_path)
    if fmt == "txt":
        txt = "\n\n".join([f"{r.fault}:  {r.to_text()}" for r in rules])
        p.write_text(txt, encoding="utf-8")
    elif fmt == "yaml":
        yaml.dump([r.to_dict() for r in rules], p.open("w", encoding="utf-8"), allow_unicode=True)
    elif fmt == "json":
        json.dump([r.to_dict() for r in rules], p.open("w", encoding="utf-8"), ensure_ascii=False, indent=2)
    else:
        raise ValueError(fmt)
    print(f"Rules exported to {p}")


# ------------------------------------------------------------------
# 6. 快速示例 (仅演示调用流程)
# ------------------------------------------------------------------
if __name__ == "__main__":
    # 6.1 载入特征和标签 (你自己的 DataFrame / Series)
    X = pd.read_parquet("features.parquet")   # 每行=一个窗口/文件
    y = pd.read_parquet("labels.parquet")["fault"]  # Series
    groups = pd.read_parquet("labels.parquet")["file_id"]  # 用文件名做分组

    # 6.2 读取专家矩阵
    D = load_D("D_matrix.yaml")

    # 6.3 挖掘规则
    mined_rules = mine_rules_from_D(
        D, X, y, groups=groups,
        comb="AND", min_support=5, min_precision=0.8
    )

    # 6.4 导出
    export_rules(mined_rules, "expert_threshold_rules.txt", fmt="txt")
