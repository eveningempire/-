import sys
from collections import OrderedDict
from functools import partial
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import strategy3.utils as utils

# if __name__ == '__main__':
#     sys.path.insert(0, str(Path(__file__).resolve().parent))
#     import utils
# else:
#     from . import utils

plt.rcParams["font.sans-serif"] = "Microsoft YaHei"  # 璁剧疆姝ｅ父鏄剧ず涓枃瀛楃
plt.rcParams["axes.unicode_minus"] = False  # 璁剧疆姝ｅ父鏄剧ず璐熷彿


class Predictor:
    def __init__(self):
        pass

    @staticmethod
    def process_datadf(cmg_type, cmg_target_cols, data_df, window_size=64, step=64):
        """鎻愬彇鐗瑰緛"""
        data_df, target_cols = utils.add_low_i_rms(data_df, cmg_target_cols=cmg_target_cols)
        model_params = utils.get_model_params(cmg_type, target_cols=target_cols)
        data = data_df[target_cols].values
        data_windows = utils.create_windows(data, window_size=window_size, step=step)
        som_model = model_params["model"]
        svd_features_list = []
        for dw in data_windows:
            svd_feature = utils.svd_feature_extract(
                dw, model_params["target_cols"], model_params["scalers"], model_params["svd_scaler"]
            )
            svd_features_list.append(svd_feature)
        svd_features_arr = np.vstack(svd_features_list)
        
        return svd_features_arr, model_params

    @staticmethod
    def get_windowed_hi(arr, model_params, window_size=128, step=1, h=0.5, l=0.0):
        """璁＄畻绐楀彛鍖栫殑鍋ュ悍鎸囨暟 HI"""
        arr = np.asarray(arr)
        n = arr.shape[0]
        if window_size > n:
            return np.array([])  # 绐楀彛澶т簬搴忓垪闀垮害锛岃繑鍥炵┖鏁扮粍
        shape = ((n - window_size) // step + 1, window_size)
        strides = (arr.strides[0] * step, arr.strides[0])
        windows = np.lib.stride_tricks.as_strided(arr, shape=shape, strides=strides)
        # ratio = (windows > (p_mean + 3 * p_std)).sum(axis=1) / window_size  # 瓒呭嚭姝ｅ父鑼冨洿鐨勬瘮渚嬶紝0~1
        # hi = np.clip((ratio - l) / (h - l), 0, 1)  # 璁や负瓒呭嚭h鏄潖鎺変簡
        hi = [model_params["model"].compute_health_index(w) for w in windows]
        return np.array(hi)

    @staticmethod
    def slope_correction(hi_ori, add_noise=True):
        """鏍规嵁鏂滅巼绗﹀彿淇 HI 搴忓垪涓殑寮傚父娉㈠姩娈?""
        # 璁＄畻璧风偣鍒板綋鍓嶇殑鏂滅巼k1锛屽綋鍓嶅埌缁堢偣鐨勬枩鐜噆2
        L = len(hi_ori)
        t = np.linspace(0, 1, L)
        hi_corrected = hi_ori.copy()
        hi_corrected[: L // 10] = np.median(hi_ori[: L // 10])
        hi_corrected[-L // 10 :] = np.median(hi_ori[-L // 10 :])
        k1 = (hi_corrected[1:-1] - hi_corrected[0]) / (t[1:-1] - t[0])
        k2 = (hi_corrected[-1] - hi_corrected[1:-1]) / (t[-1] - t[1:-1])
        k = k1 * k2  # 鏂滅巼涔樼Н锛屾甯稿簲鏄鍊硷紝璐熷€艰〃绀哄紓甯告尝鍔?
        k = np.concatenate([[0], k, [0]])  # 琛ラ綈闀垮害

        # 鏍规嵁鏂滅巼绗﹀彿淇
        anomaly_indices = np.where(k < 0)[0]
        normal_indices = np.where(k >= 0)[0]
        norm_std = np.std(hi_ori[normal_indices])
        prev_normal_idx = (
            np.argmax((normal_indices.reshape(1, -1) < anomaly_indices.reshape(-1, 1)) == 0, axis=1) - 1
        )
        hi_corrected[anomaly_indices] = hi_corrected[normal_indices[prev_normal_idx]]
        if add_noise:
            hi_corrected += np.random.randn(len(hi_corrected)) * norm_std * 0.5
        return hi_corrected

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
        timestamp_start = pd.to_datetime(time_stamps.iloc[0], format=time_fmt)
        timestamp_start_use = pd.to_datetime(time_start_use, format=time_fmt)
        timestamp_end = pd.to_datetime(time_stamps.iloc[-1], format=time_fmt)
        time_range = utils.s2y((timestamp_end - timestamp_start).total_seconds())  # 鏁版嵁鏃堕棿鑼冨洿锛屽崟浣嶏細骞?
        if (timestamp_start_use - timestamp_start).total_seconds() > 0:
            raise ValueError("浣跨敤璧风偣鏃堕棿涓嶈兘鏅氫簬鏁版嵁璧风偣鏃堕棿锛岃妫€鏌ワ紒")
        if (timestamp_end - timestamp_start_use).total_seconds() >= utils.y2s(design_life):
            raise ValueError("鏁版嵁缁堢偣鏃堕棿宸茬粡瓒呰繃璁捐瀵垮懡锛岃妫€鏌ワ紒")
        time_diff = (timestamp_end - timestamp_start).total_seconds()
        rul_theoretic = utils.s2y(
            utils.y2s(design_life) - (timestamp_end - timestamp_start_use).total_seconds()
        )
        degrade_rate_theoretic = design_life  # 鐞嗚閫€鍖栭€熷害, 1閫€鍖栧埌0闇€瑕佺殑骞存暟锛屽崟浣嶏細骞?
        delta_years = utils.s2y(time_diff)
        degrade_rate_real = delta_years / (hi[0] - hi[-1] + 1e-5)  # 瀹為檯閫€鍖栭€熷害, 1閫€鍖栧埌0闇€瑕佺殑骞存暟锛屽崟浣嶏細骞?
        degrade_rate = w * degrade_rate_theoretic + (1 - w) * degrade_rate_real
        rul = w * rul_theoretic + (1 - w) * hi[-1] * degrade_rate  # 褰撳墠鐐圭殑鍓╀綑瀵垮懡锛屽崟浣嶏細骞?
        hi_high = np.clip(np.linspace(hi[-1], hi[-1] - time_range / degrade_rate_theoretic, len(hi)), 0, 1)
        hi_low = np.clip(np.linspace(hi[-1], hi[-1] - time_range / degrade_rate_real, len(hi)), 0, 1)
        if plot:
            plt.figure()
            plt.plot(np.arange(len(hi)), hi)
            t_pred = np.arange(len(hi)) + len(hi)
            plt.fill_between(t_pred, hi_low, hi_high, color="pink", alpha=0.5, label="鐞嗚/瀹為檯閫€鍖栭€熷害鍖洪棿")
            plt.ylim(-0.05, 1.05)
            plt.axhline(0, color="red", linestyle="--")
            plt.xlabel("鏃堕棿姝?)
            plt.ylabel("鍋ュ悍鎸囨暟 HI")
        return rul, hi_high, hi_low

    @classmethod
    def get_win_num(cls, L, w, s):
        """
        璁＄畻绐楀彛鏁?
        L: 搴忓垪闀垮害
        w: 绐楀彛澶у皬
        s: 姝ラ暱
        """
        return (L - w) // s + 1 if L >= w else 0

    @classmethod
    def get_max_pow2_step(cls, L, w, min_win_num=100):
        """
        鑾峰彇婊¤冻绐楀彛鏁颁笉灏戜簬min_win_num鐨勬渶澶?鐨勬骞傛闀?
        """
        s_max = (L - w) // (min_win_num - 1)
        if s_max < 1:
            return 1
        # 鎵句笉瓒呰繃s_max鐨勬渶澶?鐨勬骞?
        pow2 = 1
        while pow2 * 2 <= s_max:
            pow2 *= 2
        return pow2

    @classmethod
    def predict_batch(
        cls,
        cmg_type: str,
        time_start_use: str,
        time_stamps: pd.Series,
        design_life: float,
        batch_data_df: pd.DataFrame,
        window=64,
        step=64,
        alpha=0.1,
        w: float = 0.8,
        plot: bool = False,
        time_fmt: str = "%Y/%m/%d %H:%M:%S",
    ):
        cmg_target_cols = utils.PHM_TYPE_COL_NAME_MAP.get(cmg_type, None)
        if cmg_target_cols is None:
            raise ValueError(f"涓嶆敮鎸佺殑cmg_type: {cmg_type}锛岃妫€鏌ワ紒")
        # 棰勪及骞惰嚜閫傚簲璋冩暣step
        _win_num = cls.get_win_num(len(batch_data_df), window, step)
        print(f"==>> 鍘熷step={step}锛岀獥鍙ｆ暟: {_win_num}")
        win_num_thre = 512  # 鏈€灏忕獥鍙ｆ暟闃堝€?
        if _win_num < win_num_thre:
            step = cls.get_max_pow2_step(len(batch_data_df), window, min_win_num=win_num_thre)
            _win_num2 = cls.get_win_num(len(batch_data_df), window, step)
            print(f"==>> 璋冩暣step={step}锛岀獥鍙ｆ暟: {_win_num2}")
        
        # 浣跨敤SOM妯″瀷璁＄畻鍋ュ悍鎸囨暟
        all_res, model_params = cls.process_datadf(cmg_type, cmg_target_cols, batch_data_df, window, step)
        ws = len(all_res) // 100
        hi_ori = cls.get_windowed_hi(all_res, model_params, window_size=ws, step=ws)

        # 骞虫粦澶勭悊鍋ュ悍鎸囨暟
        akf = utils.AdaptiveKalmanFilter2(
            x0=hi_ori[0],
            P0=1.0,
            Q0=1e-3,
            R0=1.0,
            window_size=len(hi_ori) // 10,
        )
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
            
        rul_weighted, hi_high, hi_low = cls.calc_rul_weighted(
            time_start_use,
            time_stamps,
            design_life,
            hi_,
            w=w,
            plot=plot,
            time_fmt=time_fmt,
        )
        return rul_weighted, hi_, hi_high, hi_low


if __name__ == "__main__":
    cmg_type = "500NMS"
    fp = BASE_DIR / "鏁版嵁澶勭悊" / cmg_type / "data.csv"
    import chardet

    with open(fp, "rb") as f:
        result = chardet.detect(f.readline())
        print(result)

    df = pd.read_csv(fp, encoding=result["encoding"])

    # 浣跨敤SOM妯″瀷璁＄畻鍋ュ悍鎸囨暟骞堕娴婻UL
    rul, hi, hi_high, hi_low = Predictor.predict_batch(
        cmg_type=cmg_type,
        time_start_use="2015/02/04 20:09:08",
        time_stamps=df["鏃堕棿"],
        design_life=10.0,  # 10骞磋璁″鍛?
        batch_data_df=df,
        time_fmt="%Y/%m/%d %H:%M:%S",  # 璋冩暣鏃堕棿鎴崇殑鏍煎紡锛屾敞鎰忚涓巘ime_start_use鏍煎紡涓€鑷?
    )

    plt.figure()
    plt.plot(np.arange(len(hi)), hi)
    plt.fill_between(
        np.arange(len(hi)) + len(hi),
        hi_low,
        hi_high,
        color="pink",
        alpha=0.5,
        label="HI瓒嬪娍缃俊鍖洪棿",
    )
    plt.ylim(-0.05, 1.05)
    print(f"==>> RUL: {rul:.2f} 骞?)

    plt.show()
