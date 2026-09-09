# -*- coding: utf-8 -*-
# ims_pipeline.py
import os
import glob
import json
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any, Iterable, Tuple

import numpy as np
import pandas as pd

# --- 兼容你的工程结构（优先当前目录，其次 support/） ---
try:
    from ims0 import Model
except ImportError:
    from ims0 import Model

try:
    from test_utils import calcul_acc
except ImportError:
    from support.test_utils import calcul_acc


# =========================
# 配置对象（在代码里直接定义）
# =========================
@dataclass
class IMSConfig:
    # 训练
    train_dir: Optional[str] = None                     # 训练目录（读取其中所有 CSV）
    cols: List[str] = field(default_factory=list)       # 训练/测试使用的列（空则自动推断数值列，排除 label）
    exclude: List[str] = field(default_factory=list)    # 要排除的列（编码/类别）
    step: int = 1                                       # 行重采样步长：每 step 取 1 行
    nlimit: int = 5                                     # 缺失向前填充上限

    # 模型
    model_path: str = "ims_model.json"                  # 模型保存/载入路径

    # 测试通用
    use_model_cols_only: bool = True                    # 测试时强制使用模型训练时的列集合

    # 逐帧在线测试
    online_print_every: int = 50                        # 每多少帧打印一次
    online_threshold: float = 0.5                       # 在线判断是否异常的阈值（若模型内部没给二值化）


# =========================
# 内部工具函数
# =========================
def _read_csv_smart(path: str, nlimit: int = 5) -> pd.DataFrame:
    """优先 gbk，再退回默认；首列为时间戳索引；适度缺失处理。"""
    try:
        df = pd.read_csv(path, index_col=0, encoding="gbk")
    except Exception:
        df = pd.read_csv(path, index_col=0)
    # 轻量缺失处理：向前填充不超过 nlimit 个
    if nlimit and nlimit > 0:
        df = df.fillna(method="ffill", limit=nlimit)
    # 丢掉完全空的列
    df = df.dropna(axis=1, how="all")
    return df


def _infer_numeric_cols(df: pd.DataFrame) -> List[str]:
    exclude = {"label"}
    return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]


def _select_cols(df: pd.DataFrame, cols: List[str], exclude: List[str]) -> List[str]:
    if cols:
        keep = [c for c in cols if c in df.columns]
    else:
        keep = _infer_numeric_cols(df)
    if exclude:
        ex = set(exclude)
        keep = [c for c in keep if c not in ex]
    if not keep:
        raise ValueError("没有可用于训练/测试的数值型列，请检查配置中的 cols/exclude 或数据。")
    return keep


def _stack_train_arrays(csv_paths: List[str], keep_cols: List[str], step: int, nlimit: int) -> np.ndarray:
    arrs = []
    for p in csv_paths:
        df = _read_csv_smart(p, nlimit=nlimit)
        # 保证列存在（缺失列填 NaN）
        missing = [c for c in keep_cols if c not in df.columns]
        for c in missing:
            df[c] = np.nan
        arr = df.loc[::step, keep_cols].values.astype("float32")
        arrs.append(arr)
    X = np.vstack(arrs)
    # 去掉全 NaN 的样本
    X = X[(~np.isnan(X)).any(axis=1)]
    return X


# =========================
# 主流程封装
# =========================
class IMSPipeline:
    def __init__(self, cfg: IMSConfig):
        self.cfg = cfg
        self._model: Optional[Model] = None

    # ---------- 模型 I/O ----------
    def _ensure_model(self) -> Model:
        if self._model is None:
            # 如果已有模型文件，按文件恢复；否则构造空模型（训练时会覆盖）
            if os.path.exists(self.cfg.model_path):
                m = Model(pnames=[])
                with open(self.cfg.model_path, "rb") as f:
                    m.from_json(f.read())
                m.trained = True
                self._model = m
            else:
                self._model = Model(pnames=[])
        return self._model

    def save_model(self) -> None:
        m = self._ensure_model()
        model_dir = os.path.dirname(self.cfg.model_path)
        if model_dir:  # 非空才建
            os.makedirs(model_dir, exist_ok=True)
        with open(self.cfg.model_path, "wb") as f:
            f.write(m.to_json())

    def load_model(self) -> Model:
        m = Model(pnames=[])
        with open(self.cfg.model_path, "rb") as f:
            m.from_json(f.read())
        m.trained = True
        self._model = m
        return m

    # ---------- 训练 ----------
    def fit(self) -> Dict[str, Any]:
        if not self.cfg.train_dir:
            raise ValueError("请在 IMSConfig.train_dir 指定训练数据目录。")
        csvs = sorted(glob.glob(os.path.join(self.cfg.train_dir, "*.csv")))
        if not csvs:
            raise FileNotFoundError(f"训练目录未找到 CSV：{self.cfg.train_dir}")

        # 用第一份文件确定列集合
        first = _read_csv_smart(csvs[0], nlimit=self.cfg.nlimit)
        keep_cols = _select_cols(first, self.cfg.cols, self.cfg.exclude)

        train_X = _stack_train_arrays(csvs, keep_cols, self.cfg.step, self.cfg.nlimit)

        # 训练
        m = Model(pnames=keep_cols)
        m.fit(train_X, save=False)
        self._model = m
        self.save_model()

        return {
            "n_files": len(csvs),
            "n_samples": int(train_X.shape[0]),
            "n_features": int(train_X.shape[1]),
            "pnames": list(keep_cols),
            "model_path": self.cfg.model_path,
        }

    # ---------- 离线测试 ----------
    def test_offline_old(
            self,
            test_file: str,
            out_scores: Optional[str] = None,
            override_cols: Optional[List[str]] = None,
            override_exclude: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        m = self._ensure_model()
        df = _read_csv_smart(test_file, nlimit=self.cfg.nlimit)

        # 列管理：默认使用训练时的列；若显式覆盖，则严格校验一致性
        pnames = m.pnames.tolist() if hasattr(m.pnames, "tolist") else list(m.pnames)
        if not pnames:
            pnames = _select_cols(df, override_cols or self.cfg.cols, override_exclude or self.cfg.exclude)
            m.pnames = pnames

        if self.cfg.use_model_cols_only:
            if override_cols or override_exclude:
                want = _select_cols(df, override_cols or [], override_exclude or [])
                if set(want) != set(pnames):
                    raise ValueError(f"测试列与模型训练列不一致。\n模型列: {pnames}\n期望列: {want}")
            else:
                missing = [c for c in pnames if c not in df.columns]
                if missing:
                    raise ValueError(f"测试文件缺少模型所需列：{missing}")

        # 采样 + 数组
        Xdf = df.loc[::self.cfg.step, pnames]
        X = Xdf.values.astype("float32")
        ts = df.index[::self.cfg.step]

        # 模型验证（连续分数 + 阈值）
        ablist, scores, supp, per_scores, global_scores  = m.validate(X)  # scores 为 0~1 连续分数
        # supp 结构: [ list(zip(subData, supData)), ["下阈值","上阈值"] ]
        suppData, suppLabel = supp
        # 还原为数组: 形状 [n_params, 2, n_frames]
        low_high = []
        for pid in range(len(pnames)):
            low, high = suppData[pid]  # low=list(len=n_frames), high=list(len=n_frames)
            low_high.append([low, high])
        low_high = np.array(low_high, dtype="float32")  # [P, 2, T]

        # —— 构建“带表头”的长表：时间戳、分数、是否异常、每维值/上下阈/越界标记
        is_anom = np.zeros(len(scores), dtype=int)
        is_anom[ablist] = 1

        out_dict = {
            "timestamp": ts.astype(str),
            "score": np.asarray(scores, dtype="float32"),
            "is_anom": is_anom,
        }
        # 逐维展开：value / low / high / viol
        for pid, pn in enumerate(pnames):
            val = X[:, pid]
            low = low_high[pid, 0, :]
            high = low_high[pid, 1, :]
            viol = (val < low) | (val > high)
            out_dict[f"{pn}"] = val
            out_dict[f"{pn}_low"] = low
            out_dict[f"{pn}_high"] = high
            out_dict[f"{pn}_viol"] = viol.astype(int)

        # （可选）标签
        if "label" in df.columns:
            out_dict["label"] = df.loc[::self.cfg.step, "label"].values.astype("float32")

        # 保存 CSV —— 显式包含表头
        if out_scores:
            out_df = pd.DataFrame(out_dict)
            # 确保目录存在
            out_dir = os.path.dirname(out_scores)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            out_df.to_csv(out_scores, index=False)  # index=False => 第一列不是索引；带 header
            print(f"[OK] 已保存分数（含表头、阈值与越界列）：{out_scores}")

        # 性能指标
        metrics = None
        if "label" in out_dict:
            metrics = calcul_acc(out_dict["score"], out_dict["label"])
            print("[Metrics] ", metrics)

        return {
            "ablist": ablist,
            "scores": scores,
            "supp": supp,
            "metrics": metrics,
            "n_samples": len(scores),
            "pnames": pnames,
        }

    # ---------- 离线测试 ----------
    def test_offline(
            self,
            test_file: str,
            out_scores: Optional[str] = None,
            override_cols: Optional[List[str]] = None,
            override_exclude: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        m = self._ensure_model()
        df = _read_csv_smart(test_file, nlimit=self.cfg.nlimit)

        # 列管理：默认使用训练时的列；若显式覆盖，则严格校验一致性
        pnames = m.pnames.tolist() if hasattr(m.pnames, "tolist") else list(m.pnames)
        if not pnames:
            pnames = _select_cols(df, override_cols or self.cfg.cols, override_exclude or self.cfg.exclude)
            m.pnames = pnames

        if self.cfg.use_model_cols_only:
            if override_cols or override_exclude:
                want = _select_cols(df, override_cols or [], override_exclude or [])
                if set(want) != set(pnames):
                    raise ValueError(f"测试列与模型训练列不一致。\n模型列: {pnames}\n期望列: {want}")
            else:
                missing = [c for c in pnames if c not in df.columns]
                if missing:
                    raise ValueError(f"测试文件缺少模型所需列：{missing}")

        # 采样 + 数组
        Xdf = df.loc[::self.cfg.step, pnames]
        X = Xdf.values.astype("float32")
        ts = df.index[::self.cfg.step]

        # ---- 调用 validate，兼容新旧两种返回签名 ----
        # 期望的新接口: ablist, global_raw_seq, supp, per_scores_raw, global_scores_raw
        # 旧接口: ablist, global_raw_seq, supp
        got_per_scores = False
        try:
            ablist, global_raw_seq, supp, per_scores_raw, global_scores_raw = m.validate(X)
            # 有些实现里 global_raw_seq 就是 global_scores_raw，这里取 global_scores_raw 优先
            global_raw_seq = np.asarray(global_scores_raw, dtype=float).reshape(-1)
            per_scores_raw = np.asarray(per_scores_raw, dtype=float)  # (T, M)
            got_per_scores = True
        except ValueError:
            # 老版本，无逐维分数；回退：逐帧 single_validate(inner=True)
            ablist, global_raw_seq, supp = m.validate(X)
            global_raw_seq = np.asarray(global_raw_seq, dtype=float).reshape(-1)
        except TypeError:
            # 某些实现抛 TypeError，这里也回退
            ablist, global_raw_seq, supp = m.validate(X)
            global_raw_seq = np.asarray(global_raw_seq, dtype=float).reshape(-1)

        # ---- 从 supp 提取上下阈（原结构：[(low_list, high_list), ...], ["下阈值","上阈值"]）----
        suppData, suppLabel = supp
        # 组装成 [P, 2, T]
        low_high = []
        for pid in range(len(pnames)):
            low, high = suppData[pid]
            low_high.append([low, high])
        low_high = np.array(low_high, dtype="float32")  # [P, 2, T]
        # 仅需要“上阈” -> [T, P]
        upper_thresholds = low_high[:, 1, :].T  # (T, P)

        # ---- 如果还没有 per-dim 分数，则用 single_validate(inner=True) 逐帧补齐 ----
        if not got_per_scores:
            per_list = []
            # 也顺便确保 upper_thresholds 与逐帧挑选一致（validate 的上阈已足够使用，通常无需改）
            for v in X:
                # 你前面已经把 single_validate 改成返回: global_raw, per_vec, global_flag, sub, sup
                try:
                    g_raw, per_vec, g_flag, sub, sup = m.single_validate(v, inner=True)
                    per_list.append(np.asarray(per_vec, dtype=float))
                except Exception:
                    # 老到只返回 (score, sub, sup) 的版本，这里退化：没有 per-dim 分数，只能用越界0/1占位
                    _, _, sup = m.single_validate(v, inner=True)
                    # 用一个近似：与上/下阈的相对距离不可得，则置零（不建议，尽快升级 single_validate）
                    per_list.append(np.zeros(len(pnames), dtype=float))
            per_scores_raw = np.vstack(per_list)  # (T, M)

        # ---- 截断到 0-1（作为你要的“标志位分数”）----
        global_score = np.clip(global_raw_seq, 0.0, 1.0)  # (T,)
        per_channel_scores = np.clip(per_scores_raw, 0.0, 1.0)  # (T, M)

        # —— 构建“带表头”的落盘（可选）
        if out_scores:
            out = {
                "timestamp": ts.astype(str),
                "global_score": global_score,  # 0-1
            }
            # 各维度分数（0-1）与上阈
            for j, pn in enumerate(pnames):
                out[f"{pn}_score"] = per_channel_scores[:, j]
                out[f"{pn}_high"] = upper_thresholds[:, j]
                out[pn] = X[:, j]  # 原始值，便于对照
            out_df = pd.DataFrame(out)
            out_dir = os.path.dirname(out_scores)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            out_df.to_csv(out_scores, index=False)
            print(f"[OK] 已保存离线结果（含全局分/各维分/上阈）：{out_scores}")

        # （可选）评估
        metrics = None
        if "label" in df.columns:
            y = df.loc[::self.cfg.step, "label"].values.astype("float32")
            metrics = calcul_acc(global_score, y)
            print("[Metrics] ", metrics)

        return {
            "pnames": pnames,
            "timestamps": ts.astype(str).tolist(),
            "global_score": global_score.tolist(),  # (T,)
            "per_channel_scores": per_channel_scores.tolist(),  # (T,M)
            "upper_thresholds": upper_thresholds.tolist(),  # (T,M)
            "ablist": list(map(int, ablist)),
            "metrics": metrics,
            "n_samples": int(len(global_score)),
        }

    # ---------- 在线逐帧测试 ----------
    def test_online(
        self,
        test_file: str,
        callback: Optional[Callable[[int, Any, float, bool], None]] = None,
        override_cols: Optional[List[str]] = None,
        override_exclude: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        逐帧在线检测。callback(i, ts, score, is_anom) 可用于把结果推给上层系统（日志/消息队列/可视化）。
        """
        m = self._ensure_model()
        df = _read_csv_smart(test_file, nlimit=self.cfg.nlimit)

        pnames = m.pnames.tolist() if hasattr(m.pnames, "tolist") else list(m.pnames)
        if not pnames:
            pnames = _select_cols(df, override_cols or self.cfg.cols, override_exclude or self.cfg.exclude)
            m.pnames = pnames

        if self.cfg.use_model_cols_only:
            if override_cols or override_exclude:
                want = _select_cols(df, override_cols or [], override_exclude or [])
                if set(want) != set(pnames):
                    raise ValueError(f"测试列与模型训练列不一致。\n模型列: {pnames}\n期望列: {want}")
            else:
                missing = [c for c in pnames if c not in df.columns]
                if missing:
                    raise ValueError(f"测试文件缺少模型所需列：{missing}")

        scores: List[float] = []
        anomalies: List[int] = []
        th = float(self.cfg.online_threshold)

        # 逐行
        for i, (ts, row) in enumerate(df[pnames].iterrows()):
            v = row.values.astype("float32")
            score, sub, sup = m.single_validate(v, inner=False)
            s = float(score)
            is_anom = s >= th
            scores.append(s)
            if is_anom:
                anomalies.append(i)

            # 默认简单打印；若提供 callback 则交给上层系统处理
            if callback:
                callback(i, ts, s, is_anom)
            else:
                if (i % max(1, self.cfg.online_print_every)) == 0:
                    print(f"[{i}] ts={ts}  score={s:.3f}  anom={int(is_anom)}")

        return {"ablist": anomalies, "scores": scores, "pnames": pnames, "n_samples": len(scores)}

    def plot_offline(
            self,
            test_file: str,
            out_dir: str = "./Figure_dspot/custom",
            override_cols: Optional[List[str]] = None,
            override_exclude: Optional[List[str]] = None,
    ) -> None:
        """
        直接用当前模型对 test_file 画图（一参一图），不重新训练。
        输出目录形如 ./Figure_dspot/custom/<param>.png
        """
        # 延迟导入绘图库，避免服务器无 DISPLAY 环境报错
        import os
        import numpy as np
        import pandas as pd
        from matplotlib import pyplot as plt
        from matplotlib.font_manager import FontProperties

        # 尝试与原库一致的字体设置（允许失败）
        try:
            plt.rc("font", family="Times New Roman", size=16)
            plt.rcParams["font.sans-serif"] = "SimHei"
            plt.rcParams["axes.unicode_minus"] = False
            FONT = FontProperties(fname=os.path.join(".", "support", "simhei.ttf"), size=16)
        except Exception:
            FONT = None

        m = self._ensure_model()
        df = _read_csv_smart(test_file, nlimit=self.cfg.nlimit)

        pnames = m.pnames.tolist() if hasattr(m.pnames, "tolist") else list(m.pnames)
        if not pnames:
            pnames = _select_cols(df, override_cols or self.cfg.cols, override_exclude or self.cfg.exclude)
            m.pnames = pnames

        if self.cfg.use_model_cols_only:
            if override_cols or override_exclude:
                want = _select_cols(df, override_cols or [], override_exclude or [])
                if set(want) != set(pnames):
                    raise ValueError(f"测试列与模型训练列不一致。\n模型列: {pnames}\n期望列: {want}")
            else:
                missing = [c for c in pnames if c not in df.columns]
                if missing:
                    raise ValueError(f"测试文件缺少模型所需列：{missing}")

        X = df.loc[::self.cfg.step, pnames].values.astype("float32")
        ts = np.arange(X.shape[0])
        label = df.loc[::self.cfg.step, "label"].values.astype("float32") if "label" in df.columns else None

        ablist, scores, supp, global_scores, per_scores = m.validate(X)
        suppData, suppLabel = supp  # 与 test_utils 保持一致
        suppData = np.array(suppData, dtype="float32")  # [P, 2, T] after transpose logic below

        # 目标输出目录
        os.makedirs(out_dir, exist_ok=True)

        # 逐参绘图
        for pid, pn in enumerate(pnames):
            plt.figure(figsize=(12, 10))
            # 参数曲线
            plt.plot(ts, X[:, pid], linewidth=1.0, label="参数值")

            # 异常帧标记
            if len(ablist):
                plt.scatter(np.array(ablist), X[ablist, pid], marker="o", c="r", label="异常帧")

            # 阈值线（上下）
            if suppLabel is not None:
                # 注意：validate 返回的结构与 test_utils 一致：[(low_list, high_list), ...]
                low, high = suppData[pid]
                plt.plot(ts, high, "--", linewidth=1.0, label=suppLabel[1])
                plt.plot(ts, low, "--", linewidth=1.0, label=suppLabel[0])

            # 异常区背景
            if label is not None:
                # 在 realLabel >= 0.5 的区间填充底色
                import numpy as np
                arr = np.array(label)
                plt.fill_between(ts, np.nanmin(X[:, pid]) if np.isfinite(X[:, pid]).any() else 0,
                                 np.nanmax(X[:, pid]) if np.isfinite(X[:, pid]).any() else 1,
                                 where=(arr >= 0.5), alpha=0.3, color="r")

            # 图例字体
            leg = plt.legend()
            if leg is not None and FONT is not None:
                for t in leg.get_texts():
                    t.set_fontproperties(FONT)
            plt.tight_layout()
            plt.savefig(os.path.join(out_dir, f"{pn}.png"))
            plt.close()

        print(f"[OK] 已输出图像到：{out_dir}")

    def test_online_array(
            self,
            X: np.ndarray,
            timestamps: Optional[Iterable[Any]] = None,
            callback: Optional[Callable[[int, Any, float, bool], None]] = None,
    ) -> Dict[str, Any]:
        """
        在线逐帧检测（无文件路径；直接给 array）。
        参数:
            X: np.ndarray, shape = [T, M]，按模型训练时的列顺序排列
            timestamps: 可选，同步的时间索引（长度 T），不传则用 0..T-1
            callback: 可选，callback(i, ts, global_score(0-1), is_anom)

        返回:
            {
              "pnames": List[str],
              "global_score": List[float],        # (T,) 截断到 0-1
              "per_channel_scores": List[List],   # (T,M) 截断到 0-1
              "upper_thresholds": List[List],     # (T,M) 每帧每维上阈
              "ablist": List[int],                # 异常帧索引（基于 online_threshold）
              "n_samples": int
            }
        """
        import numpy as np

        m = self._ensure_model()
        if not isinstance(X, np.ndarray):
            X = np.asarray(X, dtype="float32")
        else:
            X = X.astype("float32", copy=False)

        T, M = X.shape
        pnames = m.pnames.tolist() if hasattr(m.pnames, "tolist") else list(m.pnames)
        if not pnames or len(pnames) != M:
            raise ValueError(f"输入通道数({M})与模型通道数({len(pnames)})不一致，或模型未设置 pnames。")

        if timestamps is None:
            timestamps = np.arange(T)
        else:
            # 转成列表，确保可多次遍历
            timestamps = list(timestamps)
            if len(timestamps) != T:
                raise ValueError("timestamps 长度必须与 X 的长度一致。")

        glob_scores = []
        per_scores_all = []
        upper_all = []
        anomalies = []
        th = float(self.cfg.online_threshold)

        for i in range(T):
            v = X[i, :]
            # 期望新版 single_validate: global_raw, per_vec, global_flag, sub, sup
            try:
                g_raw, per_vec, g_flag, sub, sup = m.single_validate(v, inner=False)
                g_clip = float(min(max(g_raw, 0.0), 1.0))  # 总分截断到 0-1
                per_clip = np.clip(np.asarray(per_vec, dtype=float), 0.0, 1.0)
                upper = np.asarray(sup, dtype=float)
            except Exception:
                # 老接口回退 (score, sub, sup) —— 无逐维分数则置 0
                score, sub, sup = m.single_validate(v, inner=False)
                g_clip = float(min(max(float(score), 0.0), 1.0))
                per_clip = np.zeros(M, dtype=float)
                upper = np.asarray(sup, dtype=float)

            glob_scores.append(g_clip)
            per_scores_all.append(per_clip)
            upper_all.append(upper)

            is_anom = g_clip >= th
            if is_anom:
                anomalies.append(i)

            if callback:
                callback(i, timestamps[i], g_clip, is_anom)
            else:
                if (i % max(1, self.cfg.online_print_every)) == 0:
                    print(f"[{i}] ts={timestamps[i]}  global={g_clip:.3f}  anom={int(is_anom)}")

        glob_scores = np.asarray(glob_scores, dtype=float)  # (T,)
        per_scores_all = np.vstack(per_scores_all)  # (T,M)
        upper_all = np.vstack(upper_all)  # (T,M)

        return {
            "pnames": pnames,
            "global_score": glob_scores.tolist(),  # 0-1 截断
            "per_channel_scores": per_scores_all.tolist(),  # 0-1 截断
            "upper_thresholds": upper_all.tolist(),  # 上阈
            "ablist": anomalies,
            "n_samples": int(T),
        }


if __name__ == '__main__':
    # 1) 定义参数
    cfg = IMSConfig(
        train_dir=r"C:\Users\megan\Desktop\IMS\Health",  # 训练目录（多个CSV）
        cols=["高速转速", "低速转速", "高速电机电压", "高速固紧端轴温", "高速滑动端轴温", "高速电机电流", "低速A相电流","低速C相电流"],  # 留空=自动选数值列（排除 label）；或指明 ['Vxm','Vym','Vzm', ...]
        exclude=[],  # 排除编码/状态位等
        step=1,  # 每5行取1行
        nlimit=5,  # 缺失向前填充上限
        model_path="./ims.json",  # 模型保存路径
        use_model_cols_only=True,
        online_print_every=100,
        online_threshold=0.5,
    )

    pipe = IMSPipeline(cfg)

    # 1) 训练
    #info = pipe.fit()

    # 2) 离线测试 + 导出“带表头”的富 CSV（含每维值/阈值/越界）
    res = pipe.test_offline(
        test_file="./TestData.csv",
        out_scores="./scores_with_thresholds.csv"
    )

    # 3) 直接出图（不重训）
    pipe.plot_offline(
        test_file="./TestData.csv",
        out_dir="./custom_case"
    )


    #res_on = pipe.test_online(
    #    test_file="./data/test.csv",
    #    callback=on_each
    #)
    #print("在线异常帧数：", len(res_on["ablist"]))
