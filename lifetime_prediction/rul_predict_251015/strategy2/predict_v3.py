import sys
from collections import OrderedDict
from functools import partial
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import strategy2.utils as utils
from strategy2.model import IsolationForestModel
from strategy2.utils import (
    DynamicThreshold,
    calc_rul_weighted,
    create_windows,
    extract_svd_features,
    slope_correction,
)

plt.rcParams["font.sans-serif"] = "Microsoft YaHei"  # 璁剧疆姝ｅ父鏄剧ず涓枃瀛楃
plt.rcParams["axes.unicode_minus"] = False  # 璁剧疆姝ｅ父鏄剧ず璐熷彿


class Predictor:
    def __init__(self):
        pass

    @staticmethod
    def process_datadf(cmg_type, cmg_target_cols, data_df, window_size=64, step=32):
        """鎻愬彇鐗瑰緛骞惰幏鍙栧绔嬫．鏋楀紓甯稿垎鏁?""
        data_df, target_cols = utils.add_low_i_rms(data_df, cmg_target_cols=cmg_target_cols)
        model_params = utils.get_model_params(cmg_type, target_cols=target_cols)

        # 鑾峰彇绐楀彛閰嶇疆
        windows_config = model_params.get("windows_config", {"window_size": window_size, "step": step})

        # 浣跨敤閰嶇疆涓殑绐楀彛澶у皬鍜屾闀?
        window_size = windows_config.get("window_size", window_size)
        step = windows_config.get("step", step)

        # 鍘熷鏁版嵁
        data = data_df[target_cols].values

        # 鍗曚竴绐楀彛澶勭悊
        data_windows = utils.create_windows(data, window_size=window_size, step=step)

        # 鎻愬彇SVD鐗瑰緛
        svd_features = utils.extract_svd_features(data_windows, target_cols, model_params["scalers"])

        # 褰掍竴鍖栫壒寰?
        scaled_features = model_params["svd_scaler"].transform(svd_features)

        # 璁＄畻寮傚父鍒嗘暟
        model = model_params["model"]
        anomaly_scores = model.get_anomaly_score(scaled_features)

        return anomaly_scores, model_params

    @staticmethod
    def calculate_hi_with_dynamic_threshold(
        anomaly_scores, window_size=100, percentile=99, initial_threshold=None
    ):
        """浣跨敤鍔ㄦ€侀槇鍊艰绠楀仴搴锋寚鏁?""
        # 鍒涘缓鍔ㄦ€侀槇鍊煎璞?
        dynamic_thresholder = DynamicThreshold(window_size=window_size, percentile=percentile)

        # 濡傛灉鎻愪緵浜嗗垵濮嬮槇鍊硷紝浣跨敤瀹冩潵鍒濆鍖?
        if initial_threshold is not None:
            for _ in range(window_size):
                dynamic_thresholder.update(0)  # 娣诲姞铏氭嫙鍊兼潵濉厖绐楀彛
            dynamic_thresholder.thresholds[-1] = initial_threshold  # 璁剧疆鍒濆闃堝€?

        hi_values = []
        thresholds = []

        for score in anomaly_scores:
            # 鏇存柊闃堝€?
            threshold = dynamic_thresholder.update(score)
            thresholds.append(threshold)

            # 璁＄畻鍋ュ悍鎸囨暟锛? - 褰掍竴鍖栧紓甯稿垎鏁帮級
            # 濡傛灉鍒嗘暟瓒呰繃闃堝€硷紝璁や负鏄紓甯?
            if score > threshold:
                hi_value = 1.0 - min(score / threshold, 1.0)  # 闃叉璐熷€?
            else:
                hi_value = 1.0

            hi_values.append(hi_value)

        return np.array(hi_values), np.array(thresholds)

    @staticmethod
    def slope_correction(hi_ori, add_noise=True):
        """鏍规嵁鏂滅巼绗﹀彿淇 HI 搴忓垪涓殑寮傚父娉㈠姩娈?""
        return slope_correction(hi_ori, add_noise=add_noise)

    @staticmethod
    def calc_rul_weighted(
        time_start_use: str,
        time_stamps: pd.Series,
        design_life: float,
        hi: np.ndarray,
        w: float = 0.5,
        plot: bool = False,
        time_fmt="%Y/%m/%d %H:%M:%S",
    ):
        """鍔犳潈骞冲潎閫€鍖栭€熷害璁＄畻鍓╀綑瀵垮懡"""
        return calc_rul_weighted(time_start_use, time_stamps, design_life, hi, w, plot, time_fmt)

    @classmethod
    def predict_batch(
        cls,
        cmg_type: str,
        time_start_use: str,
        time_stamps: pd.Series,
        design_life: float,
        batch_data_df: pd.DataFrame,
        window_size=64,  # 绐楀彛澶у皬
        step=32,  # 绐楀彛婊戝姩姝ラ暱
        alpha=0.1,  # EMA骞虫粦鍙傛暟
        dynamic_window=100,  # 鍔ㄦ€侀槇鍊肩獥鍙ｅぇ灏?
        dynamic_percentile=99,  # 鍔ㄦ€侀槇鍊煎垎浣嶆暟
        w: float = 0.8,  # 鐞嗚/瀹為檯閫€鍖栭€熷害鍔犳潈绯绘暟
        plot: bool = False,
        time_fmt: str = "%Y/%m/%d %H:%M:%S",
    ):
        """鎵归噺棰勬祴RUL"""
        cmg_target_cols = utils.PHM_TYPE_COL_NAME_MAP.get(cmg_type, None)
        if cmg_target_cols is None:
            raise ValueError(f"涓嶆敮鎸佺殑cmg_type: {cmg_type}锛岃妫€鏌ワ紒")

        # 鑾峰彇寮傚父鍒嗘暟
        anomaly_scores, model_params = cls.process_datadf(
            cmg_type, cmg_target_cols, batch_data_df, window_size, step
        )

        # 浣跨敤妯″瀷涓繚瀛樼殑闃堝€间綔涓哄垵濮嬪€?
        initial_threshold = model_params.get("anomaly_threshold", None)

        # 浣跨敤鍔ㄦ€侀槇鍊艰绠楀仴搴锋寚鏁?
        hi_ori, thresholds = cls.calculate_hi_with_dynamic_threshold(
            anomaly_scores,
            window_size=dynamic_window,
            percentile=dynamic_percentile,
            initial_threshold=initial_threshold,
        )
        akf = utils.AdaptiveKalmanFilter2(
            x0=hi_ori[0],
            P0=1.0,
            Q0=1e-3,
            R0=1.0,
            window_size=len(hi_ori) // 10,
            # median_estimate=True,
        )
        # 骞虫粦澶勭悊
        process_pipeline = OrderedDict(
            {
                "骞虫粦 HI-ema": partial(utils.ema_batch, alpha=alpha),
                "骞虫粦 HI-correct": partial(cls.slope_correction, add_noise=False),
                "骞虫粦 HI-akf": akf.filter,
            }
        )

        hi_ = hi_ori.copy()
        for _, func in process_pipeline.items():
            hi_proc = func(hi_)
            hi_ = np.array(hi_proc)

        # 璁＄畻RUL
        rul_weighted, hi_high, hi_low = cls.calc_rul_weighted(
            time_start_use,
            time_stamps,
            design_life,
            hi_,
            w=w,
            plot=plot,
            time_fmt=time_fmt,
        )

        # 鍙€夛細杩斿洖鍔ㄦ€侀槇鍊间俊鎭互渚跨粯鍥?
        extra_info = {
            "anomaly_scores": anomaly_scores,
            "thresholds": thresholds,
        }

        return rul_weighted, hi_, hi_high, hi_low


if __name__ == "__main__":
    cmg_type = "500NMS"
    BASE_DIR = Path(__file__).resolve().parent.parent
    fp = BASE_DIR / "鏁版嵁澶勭悊" / cmg_type / "data.csv"
    import chardet

    with open(fp, "rb") as f:
        result = chardet.detect(f.readline())
        print(result)

    df = pd.read_csv(fp, encoding=result["encoding"])[:3196]

    rul, hi, hi_high, hi_low = Predictor.predict_batch(
        cmg_type=cmg_type,
        time_start_use="2015/02/04 20:09:08",
        time_stamps=df["鏃堕棿"],
        design_life=10.0,  # 10骞磋璁″鍛?
        batch_data_df=df,
        window_size=64,  # 绐楀彛澶у皬
        step=32,  # 绐楀彛婊戝姩姝ラ暱
        dynamic_window=10,  # 鍔ㄦ€侀槇鍊肩獥鍙ｅぇ灏?
        dynamic_percentile=99,  # 鍔ㄦ€侀槇鍊煎垎浣嶆暟
        time_fmt="%Y/%m/%d %H:%M:%S",  # 璋冩暣鏃堕棿鎴崇殑鏍煎紡锛屾敞鎰忚涓巘ime_start_use鏍煎紡涓€鑷?
        w=0.8,  # 鐞嗚/瀹為檯閫€鍖栭€熷害鏉冮噸
    )

    # 缁樺埗鍋ュ悍鎸囨暟鍜岄娴?
    plt.figure(figsize=(12, 8))
    plt.plot(np.arange(len(hi)), hi, label="鍋ュ悍鎸囨暟(HI)")
    plt.fill_between(
        np.arange(len(hi)) + len(hi),
        hi_low,
        hi_high,
        color="pink",
        alpha=0.5,
        label="HI瓒嬪娍缃俊鍖洪棿",
    )
    plt.ylim(-0.05, 1.05)
    plt.xlabel("鏃堕棿姝?)
    plt.ylabel("鍋ュ悍鎸囨暟 HI")
    plt.legend()
    plt.title(f"鍋ュ悍鎸囨暟涓庤秼鍔块娴?(RUL: {rul:.2f} 骞?")

    print(f"==>> RUL: {rul:.2f} 骞?)
    plt.show()

