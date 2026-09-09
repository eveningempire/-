import json
import pickle
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reconstruct import reconstruct_rearranged_signal, run_real_data_experiment
from scipy.fftpack import fft, ifft
from scipy.interpolate import interp1d
from scipy.signal import decimate
from scipy.spatial.distance import cosine

plt.rcParams["font.sans-serif"] = "Microsoft YaHei"  # 设置正常显示中文字符
plt.rcParams["axes.unicode_minus"] = False  # 设置正常显示负号


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# 常量定义
MIN_MAGNITUDE = 2e-15  # 最小幅度值，用于对数坐标和填充


def json_serialize_with_ndarray(obj, indent: int = 4) -> str:
    """
    序列化包含 numpy 数组的任意 Python 对象为 JSON 字符串
    核心：自动将 ndarray 转为列表（tolist()），兼容字典、列表、元组等嵌套结构

    Args:
        obj: 待序列化的对象（可包含 ndarray、字典、列表、基本类型等）
        indent: JSON 缩进，美化输出（默认4）

    Returns:
        str: 序列化后的 JSON 字符串

    Raises:
        TypeError: 遇到无法序列化的类型（非 ndarray/基础类型/容器类型）
    """

    def _serialize_handler(item):
        # 处理 numpy 数组：转为列表
        if isinstance(item, np.ndarray):
            return item.tolist()
        # 处理 numpy 数值类型（如 np.int64、np.float32）：转为 Python 原生类型
        elif isinstance(item, (np.integer, np.floating)):
            return item.item()
        # 处理元组：转为列表（JSON 不支持元组，统一转列表）
        elif isinstance(item, tuple):
            return list(item)
        # 处理字典：递归遍历键值对
        elif isinstance(item, dict):
            return {k: _serialize_handler(v) for k, v in item.items()}
        # 处理列表/集合：递归遍历元素
        elif isinstance(item, (list, set)):
            return [_serialize_handler(elem) for elem in item]
        # 处理 None/布尔/字符串/原生数值：直接返回
        elif item is None or isinstance(item, (bool, str, int, float)):
            return item
        # 其他不支持的类型：抛出异常
        else:
            raise TypeError(f"无法序列化的类型: {type(item)} (值: {item})")

    # 调用 json.dumps，使用自定义处理器
    return json.dumps(obj, default=_serialize_handler, indent=indent, ensure_ascii=False)


# 表9-随机采样-旧版
def get_random_sampling_res_bak(group: int = 1):
    """
    获取随机采样的结果数据。

    group: int, 第几组数据, 1/2/3, 分别对应不同的随机采样结果。group1是报告中的结果
    """
    assert group in [1, 2, 3], "group参数必须是1/2/3之一。"
    start_idx = (group - 1) * 10
    with open(DATA_DIR / "data_08_i_sampled_arr.pkl", "rb") as f:
        data_08_i_sampled_arr = pickle.load(f)

    def freq_domain_interpolate(signal, f_down, f_up):
        """
        将一个低采样率信号上采样到目标采样率。
        """
        N = len(signal)
        # 计算上采样倍数
        k = f_up // f_down

        # 步骤 1: FFT
        X = fft(signal)

        # 步骤 2: 频域补零
        # 创建一个新的、更长的复数数组
        X_up = np.zeros(k * N, dtype=np.complex128)
        # 将原始频谱的正频率部分复制到新频谱的前半部分
        X_up[: N // 2] = X[: N // 2]
        # 将原始频谱的负频率部分复制到新频谱的后半部分
        X_up[-N // 2 :] = X[-N // 2 :]

        # 步骤 3: IFFT
        signal_up = ifft(X_up).real

        # 步骤 4: 幅度修正
        signal_up = signal_up * k

        return signal_up

    # 计算频域相似度
    def calculate_similarity(mag1, mag2):
        """
        计算两个频谱的余弦相似度。
        """
        return 1 - cosine(mag1, mag2)

    fs_low = 4
    fs_target = 16
    test_signal_low = data_08_i_sampled_arr[
        start_idx + np.arange(3)
    ].flatten()  # 取前3个周期的采样信号进行测试
    test_signal_up = freq_domain_interpolate(test_signal_low, fs_low, fs_target)
    # 为不同采样率信号构建时间轴
    t_down = np.linspace(0, len(test_signal_low) / fs_low, len(test_signal_low), endpoint=False)
    t_up = np.linspace(0, len(test_signal_low) / fs_low, len(test_signal_up), endpoint=False)

    # 构建不同采样率的信号（在相同时间长度内包含更多周期）
    # 构建8Hz采样信号（6个周期）
    test_signal_8hz = data_08_i_sampled_arr[start_idx + np.arange(6)].flatten()
    # 对8Hz信号进行频域上采样到16Hz
    test_signal_8hz_up = freq_domain_interpolate(test_signal_8hz, 8, 16)
    t_8hz = np.linspace(0, len(test_signal_8hz) / 8, len(test_signal_8hz), endpoint=False)
    t_8hz_up = np.linspace(0, len(test_signal_8hz) / 8, len(test_signal_8hz_up), endpoint=False)

    freq_8hz_up = np.fft.fftfreq(len(test_signal_8hz_up), d=1 / 16)
    freq_4hz_up = np.fft.fftfreq(len(test_signal_up), d=1 / 16)

    mag_4hz = np.abs(fft(test_signal_low))
    mag_8hz = np.abs(fft(test_signal_8hz))
    mag_8hz_up = np.abs(fft(test_signal_8hz_up))
    mag_4hz_up = np.abs(fft(test_signal_up))

    # 对mag_4hz补0到mag_4hz_up的长度
    mag_4hz_padded = np.zeros_like(mag_4hz_up)
    mag_4hz_padded[: len(mag_4hz) // 2] = mag_4hz[: len(mag_4hz) // 2]
    mag_8hz_padded = np.zeros_like(mag_8hz_up)
    mag_8hz_padded[: len(mag_8hz) // 2] = mag_8hz[: len(mag_8hz) // 2]

    # 计算4Hz vs 4Hz up的频域相似度
    similarity_4hz = calculate_similarity(
        mag_4hz_padded[: len(mag_4hz_padded) // 2], mag_4hz_up[: len(mag_4hz_up) // 2]
    )
    print(f"4Hz原始信号 vs 4Hz→16Hz上采样 频域相似度: {similarity_4hz:.4f}")

    # 计算8Hz vs 8Hz up的频域相似度
    similarity_8hz = calculate_similarity(
        mag_8hz_padded[: len(mag_8hz_padded) // 2], mag_8hz_up[: len(mag_8hz_up) // 2]
    )
    print(f"8Hz原始信号 vs 8Hz→16Hz上采样 频域相似度: {similarity_8hz:.4f}")

    time_mask_4Hz = np.where(t_down < 10)
    time_mask_4Hz_up = np.where(t_up < 10)
    time_mask_8Hz = np.where(t_8hz < 10)
    time_mask_8Hz_up = np.where(t_8hz_up < 10)
    res_data_random_sampling = {
        "4Hz": {
            "time_domain": {
                "x1": t_up[time_mask_4Hz_up],
                "y1": test_signal_up[time_mask_4Hz_up],
                "x2": t_down[time_mask_4Hz],
                "y2": test_signal_low[time_mask_4Hz],
            },
            "freq_domain": {
                "x": {"value": freq_4hz_up[: len(freq_4hz_up) // 2], "label": "频率"},
                "y1": {
                    "value": mag_4hz_padded[: len(mag_4hz_padded) // 2],
                    "label": "4Hz原始频谱",
                },
                "y2": {"value": mag_4hz_up[: len(mag_4hz_up) // 2], "label": "频域上采样到16Hz频谱"},
                "similarity": similarity_4hz,
            },
        },
        "8Hz": {
            "time_domain": {
                "x1": t_8hz_up[time_mask_8Hz_up],
                "y1": test_signal_8hz_up[time_mask_8Hz_up],
                "x2": t_8hz[time_mask_8Hz],
                "y2": test_signal_8hz[time_mask_8Hz],
            },
            "freq_domain": {
                "x": {"value": freq_8hz_up[: len(freq_8hz_up) // 2], "label": "频率"},
                "y1": {
                    "value": mag_8hz_padded[: len(mag_8hz_padded) // 2],
                    "label": "8Hz原始频谱",
                },
                "y2": {"value": mag_8hz_up[: len(mag_8hz_up) // 2], "label": "频域上采样到16Hz频谱"},
                "similarity": similarity_8hz,
            },
        },
    }
    return json_serialize_with_ndarray(res_data_random_sampling)


# 表9-欠采样-旧版
def get_low_sampling_res_bak(group: int = 1):
    """
    获取低采样率的结果数据。

    group: int, 第几组数据, 1/2/3, 分别对应不同的低采样率结果。group1是报告中的结果
    """
    assert group in [1, 2, 3], "group参数必须是1/2/3之一。"
    configs = {
        1: {
            "dc_val": 1.3,
            "freqs": [11.3, 23.7, 37.1],
            "amps": [1.0, 0.9, 0.8],
            "phases": [np.pi / 5, np.pi / 4, np.pi / 3],
        },
        2: {
            "dc_val": 1.6,
            "freqs": [21.3, 13.7, 47.1],
            "amps": [1.0, 0.9, 0.8],
            "phases": [np.pi / 6, np.pi / 4, np.pi / 2],
        },
        3: {
            "dc_val": 1.9,
            "freqs": [31.3, 3.7, 27.1],
            "amps": [1.0, 0.9, 0.8],
            "phases": [np.pi / 3, np.pi / 4, np.pi / 5],
        },
    }
    config = configs[group]
    (
        downsampled_t,
        uniform_downsampled_signal_with_dc,
        t,
        signal,
        final_reconstructed_signal,
        freqs_original,
        fft_original,
        freqs_final_reconstructed,
        fft_final_reconstructed,
        recon_metrics,
    ) = reconstruct_rearranged_signal(config["dc_val"], config["freqs"], config["amps"], config["phases"])
    res_data_under_sampling = [
        {
            "x1": {
                "value": downsampled_t[np.where(downsampled_t < 10)],
                "label": "时间",
            },
            "y1": {
                "value": uniform_downsampled_signal_with_dc[np.where(downsampled_t < 10)],
                "title": "欠采样结果",
            },
            "x2": {
                "value": t[np.where(t < 10)],
                "label": "时间",
            },
            "y2": {
                "value": signal[np.where(t < 10)],
                "title": "原始信号",
            },
        },
        {
            "x": {
                "value": t[np.where((t > 5) & (t < 8))],
                "title": "时间",
            },
            "y1": {
                "value": signal[np.where((t > 5) & (t < 8))],
                "title": "原始信号详情",
            },
            "y2": {
                "value": final_reconstructed_signal[np.where((t > 5) & (t < 8))],
                "title": "重建信号详情",
            },
            "recon_metrics": recon_metrics,
        },
        {
            "x1": {
                "value": freqs_original,
                "label": "原始信号频率",
            },
            "y1": {
                "value": fft_original,
                "title": "原始信号频谱",
            },
            "x2": {
                "value": freqs_final_reconstructed,
                "label": "重建信号频谱",
            },
            "y2": {
                "value": fft_final_reconstructed,
                "title": "重建信号频谱",
            },
        },
    ]
    return json_serialize_with_ndarray(res_data_under_sampling)


# region 2026年1月16日17:08:22 - 在真实数据上验证随机采样率对齐的效果

def resample_data(low_rate_data, low_rate_time, high_rate_time, method="linear"):
    """
    插值函数，将低采样率数据插值到高采样率。

    参数:
        low_rate_data (array-like): 低采样率数据。
        low_rate_time (array-like): 低采样率数据对应的时间点。
        high_rate_time (array-like): 高采样率时间点。
        method (str): 插值方法，可选 'linear'（线性插值）、'cubic'（三次样条插值）或 'freq'（频域插值）。

    返回:
        high_rate_data (np.ndarray): 高采样率插值后的数据。
    """
    if method not in ["linear", "cubic", "freq"]:
        raise ValueError("method 参数必须是 'linear', 'cubic' 或 'freq'")

    if method in ["linear", "cubic"]:
        # 创建插值函数
        interpolator = interp1d(low_rate_time, low_rate_data, kind=method, fill_value="extrapolate")
        # 在高采样率时间点上插值
        high_rate_data = interpolator(high_rate_time)
    elif method == "freq":
        # 计算采样率
        f_down = 1 / (low_rate_time[1] - low_rate_time[0])  # 低采样率
        f_up = 1 / (high_rate_time[1] - high_rate_time[0])  # 高采样率
        N = len(low_rate_data)
        k = int(f_up // f_down)  # 计算上采样倍数

        # 步骤 1: FFT
        X = fft(low_rate_data)

        # 步骤 2: 频域补零
        X_up = np.zeros(k * N, dtype=np.complex128)
        X_up[: N // 2] = X[: N // 2]
        X_up[-N // 2 :] = X[-N // 2 :]

        # 步骤 3: IFFT
        high_rate_data = ifft(X_up).real

        # 步骤 4: 幅度修正
        high_rate_data = high_rate_data * k

    return high_rate_data


def compare_resample_methods(
    ori_data, ds_data, t_ori, t_ds, methods=None, plot_seconds=3.0, fs_ds=None, fs_ori=20.0, plot=False
):
    """
    比较不同重采样方法（'linear'、'cubic'、'freq'）的效果：
    - 对每种方法进行插值
    - 计算并打印指标（使用已有的 metrics_compute）
    - 如果 plot=True，绘制原始与各方法对齐后的对比图（前若干秒）

    返回:
        dict: 每种方法的对齐结果和指标
    """
    if methods is None:
        methods = ["linear", "cubic", "freq"]

    results = {}
    for m in methods:
        aligned = resample_data(ds_data, t_ds, t_ori, method=m)
        # 确保长度与原始数据一致
        if len(aligned) != len(ori_data):
            if len(aligned) > len(ori_data):
                aligned = aligned[: len(ori_data)]
            else:
                aligned = np.pad(aligned, (0, len(ori_data) - len(aligned)), "constant")

        metrics = metrics_compute(ori_data, aligned, fs_ds=fs_ds, fs_ori=fs_ori)
        results[m] = {"original": ori_data, "aligned": aligned, "metrics": metrics}

        print(f"Method={m}:")
        for k, v in metrics.items():
            print(f"  {k}: {v:.6f}")

    # 如果 plot=True，绘图：比较原始信号与各方法结果（前 plot_seconds 秒）
    if plot:
        time_mask = t_ori < plot_seconds

        # 时域对比图：3*1 子图
        fig1, axes1 = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
        fig1.suptitle("时间域重采样方法对比")
        for i, m in enumerate(methods):
            axes1[i].plot(t_ori[time_mask], ori_data[time_mask], label="原始", color="r", linestyle="--", alpha=0.7)
            axes1[i].plot(
                t_ori[time_mask], results[m]["aligned"][time_mask], label=f"aligned-{m}", linestyle="-", color="b"
            )
            axes1[i].set_ylabel("信号幅值")
            axes1[i].legend()
            axes1[i].grid()
            if i == 2:
                axes1[i].set_xlabel("时间 (秒)")

        # 频域对比图：3*1 子图
        fig2, axes2 = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
        fig2.suptitle("频域重采样方法对比")
        freq_ori = np.fft.fftfreq(len(ori_data), d=t_ori[1] - t_ori[0])
        mag_ori = np.abs(fft(ori_data))
        
        # 计算显示的频率范围（显示到 2 倍 Nyquist 频率）
        nyquist_freq = fs_ds / 2
        freq_half_idx = len(freq_ori) // 2
        # 找到接近 2 倍 Nyquist 频率的索引
        freq_display_mask = freq_ori[:freq_half_idx] <= nyquist_freq * 2
        freq_display = freq_ori[:freq_half_idx][freq_display_mask]
        
        # 将原始信号高于 Nyquist 频率的部分幅值设为 0
        mag_ori_copy = mag_ori.copy()
        high_freq_mask = np.abs(freq_ori) >= nyquist_freq
        mag_ori_copy[high_freq_mask] = MIN_MAGNITUDE

        for i, m in enumerate(methods):
            aligned = results[m]["aligned"]
            freq_aligned = np.fft.fftfreq(len(aligned), d=t_ori[1] - t_ori[0])
            mag_aligned = np.abs(fft(aligned))
            
            # 只显示到 2 倍 Nyquist 频率的范围
            mag_ori_display = mag_ori_copy[:freq_half_idx][freq_display_mask]
            mag_aligned_display = mag_aligned[:len(freq_aligned) // 2][:len(freq_display)]
            
            axes2[i].plot(
                freq_display,
                mag_ori_display,
                label=f"原始 ({fs_ori}Hz)",
                linestyle="--",
                color="r",
                alpha=0.7,
            )
            axes2[i].plot(
                freq_display,
                mag_aligned_display,
                label=f"aligned-{m}",
                linestyle="-",
                color="b",
            )
            axes2[i].set_ylabel("幅度")
            axes2[i].legend()
            axes2[i].grid()
            axes2[i].set_yscale("log")
            axes2[i].set_ylim(MIN_MAGNITUDE / 2, 1e3)
            if i == 2:
                axes2[i].set_xlabel("频率 (Hz)")

        plt.tight_layout()
        plt.show()

    # 对 metrics 进行归一化：每个 metric 除以所有方法中该 metric 的最小值
    if results:
        # 获取所有 metrics 键
        metric_keys = list(results[next(iter(results))]["metrics"].keys())
        for key in metric_keys:
            # 收集所有方法该 metric 的值
            values = [results[m]["metrics"][key] for m in methods]
            min_val = min(values)
            # 归一化
            for m in methods:
                results[m]["metrics"][key] /= min_val

        # 使用归一化后的结果计算综合指标
        for m in methods:
            normalized_dtw_time = results[m]["metrics"]["dtw_time"]
            normalized_dtw_freq = results[m]["metrics"]["dtw_frequency"]
            results[m]["metrics"]["combined_metric"] = (normalized_dtw_time + normalized_dtw_freq) / 2

    return results


def dtw_distance(x, y):
    """
    计算两个一维序列的 DTW 距离（欧氏距离）
    参数:
        x, y: 1D array-like, 输入序列
    返回:
        float: DTW 距离（值越小越相似）
    """
    x, y = np.array(x), np.array(y)
    n, m = len(x), len(y)

    # 初始化代价矩阵 (n+1) x (m+1)
    dtw_matrix = np.full((n + 1, m + 1), np.inf)
    dtw_matrix[0, 0] = 0

    # 动态规划填充
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = abs(x[i - 1] - y[j - 1])  # 局部距离
            # 累积最小代价
            dtw_matrix[i, j] = cost + min(
                dtw_matrix[i - 1, j], dtw_matrix[i, j - 1], dtw_matrix[i - 1, j - 1]  # 插入  # 删除  # 匹配
            )

    return dtw_matrix[n, m]


def dtw_distance_fast(x, y, window=50):
    """
    带Sakoe-Chiba窗口约束的DTW
    window: 允许的最大时间偏移（通常取序列长度的1-5%）
    """
    x, y = np.array(x), np.array(y)
    n, m = len(x), len(y)

    # 初始化代价矩阵
    dtw = np.full((n + 1, m + 1), np.inf)
    dtw[0, 0] = 0

    # 仅在窗口内计算
    for i in range(1, n + 1):
        j_start = max(1, i - window)
        j_end = min(m + 1, i + window + 1)
        for j in range(j_start, j_end):
            cost = abs(x[i - 1] - y[j - 1])
            dtw[i, j] = cost + min(dtw[i - 1, j], dtw[i, j - 1], dtw[i - 1, j - 1])

    return dtw[n, m]


def metrics_compute(original_data, aligned_data, fs_ds=None, fs_ori=20.0):
    """
    计算对齐后数据与原始数据的误差指标。

    参数:
        original_data (array-like): 原始高采样率数据。
        aligned_data (array-like): 对齐后的高采样率数据。
        fs_ds (float): 降采样后的采样率，用于计算频域阈值。
        fs_ori (float): 原始采样率，用于计算频率轴。
    返回:
        dict: 包含 MAE, RMSE, MAPE, DTW 距离, 频域相似度和 SSIM 的字典。
    """
    # # 时间域误差指标
    # mae = mean_absolute_error(original_data, aligned_data)
    # rmse = np.sqrt(mean_squared_error(original_data, aligned_data))
    # mape = np.mean(np.abs((original_data - aligned_data) / original_data)) * 100

    # DTW 距离
    dtw_dist = dtw_distance_fast(original_data, aligned_data)

    # 计算频谱
    fft_original = np.abs(fft(original_data))
    fft_aligned = np.abs(fft(aligned_data))

    # 对齐频谱长度（补零）
    max_len = max(len(fft_original), len(fft_aligned))
    fft_original_padded = np.zeros(max_len)
    fft_aligned_padded = np.zeros(max_len)
    fft_original_padded[: len(fft_original)] = fft_original
    fft_aligned_padded[: len(fft_aligned)] = fft_aligned

    # 计算频域相似度
    if fs_ds is not None:
        # 计算阈值频率：降采样后的 Nyquist 频率
        threshold_freq = fs_ds / 2
        freq = np.fft.fftfreq(max_len, d=1 / fs_ori)
        # 将原始信号频谱中高于阈值的部分设为0
        high_freq_mask = np.abs(freq) >= threshold_freq
        fft_original_padded[high_freq_mask] = 0
    dtw_freq = dtw_distance_fast(fft_original_padded[: max_len // 2], fft_aligned_padded[: max_len // 2])

    return {
        # "MAE": mae,
        # "RMSE": rmse,
        # "MAPE": mape,
        "dtw_time": dtw_dist,
        "dtw_frequency": dtw_freq,
    }


def downsample_data(data, factor, method="mean"):
    """
    对数据进行降采样。

    参数:
        data (array-like): 原始数据。
        factor (int): 降采样因子，表示每隔多少个点取一个点。
        method (str): 降采样方法，可选 'mean'（块平均）、'decimate'（抗混叠滤波降采样）或 'uniform'（等距取点）。

    返回:
        downsampled_data (np.ndarray): 降采样后的数据。
    """
    if factor < 1 or not isinstance(factor, int):
        raise ValueError("降采样因子 factor 必须是大于等于 1 的整数。")

    if method == "mean":
        # 块平均降采样
        n = len(data) // factor  # 计算降采样后的长度
        downsampled_data = np.mean(data[: n * factor].reshape(-1, factor), axis=1)
    elif method == "decimate":
        # 使用抗混叠滤波器的降采样
        downsampled_data = decimate(data, factor, ftype="iir", zero_phase=True)
    elif method == "uniform":
        # 等距取点降采样
        downsampled_data = data[::factor]
    else:
        raise ValueError("method 参数必须是 'mean', 'decimate' 或 'uniform'。")

    return downsampled_data


# 表9-随机采样-新版，在真实数据上验证随机采样率对齐的效果
def get_random_sampling_res(group: int = 1):
    """
    在真实数据上验证随机采样率对齐的效果。
    group: int, 第几组数据, 1/2/3/4, 分别对应:
        - 1/2/3: 文件夹"data/table9展示数据/"中的不同的数据文件(data1.csv, data2.csv, data3.csv)
        - 4: 1Hz真实数据(real_data_1Hz.csv)，降采样到0.25Hz后对齐

    返回:
        str: 包含对齐结果和指标的 JSON 字符串。
        
        注意，这里的评价指标换成了时域、频域的 DTW 距离，越小代表越相似。DTW距离进行了归一化处理(统一除以最好的指标。因此最好的是1，其他都大于1)，并且以时域、频域归一化后指标的平均值作为综合指标，此指标越小代表越相似。

        返回数据格式与旧版有些许不同。
    """
    assert group in [1, 2, 3, 4, 11, 12], "group参数必须是1/2/3/4/11/12之一。"

    if group == 11:
        return get_fast_slow_reconstruction_res()
    
    if group == 12:
        return get_intermittent_reconstruction_res()
    
    if group == 4:
        return test_real_data_1hz(plot=False)
    
    # 采样率设置
    fs_ori = 20.0  # 原始信号采样率 (Hz)
    ds_factor = 4  # 降采样因子
    fs_ds = fs_ori / ds_factor  # 降采样后的采样率 (Hz)
    
    ori_data = pd.read_csv(DATA_DIR / f"table9展示数据/data{group}.csv", header=None).values.flatten()  # {fs_ori}Hz
    ds_data = downsample_data(ori_data, factor=ds_factor, method="uniform")

    plot_seconds = len(ori_data) / fs_ori  # 全部时长
    results = compare_resample_methods(
        ori_data,
        ds_data,
        np.linspace(0, len(ori_data) / fs_ori, len(ori_data), endpoint=False),
        np.linspace(0, len(ds_data) / fs_ds, len(ds_data), endpoint=False),
        methods=["linear", "cubic", "freq"],
        plot_seconds=plot_seconds,
        fs_ds=fs_ds,
        fs_ori=fs_ori,
        plot=False,
    )

    # 重新组织成 line160 的形式
    t_ori = np.linspace(0, len(ori_data) / fs_ori, len(ori_data), endpoint=False)
    t_ds = np.linspace(0, len(ds_data) / fs_ds, len(ds_data), endpoint=False)

    time_mask_ori = np.where(t_ori < plot_seconds)
    time_mask_ds = np.where(t_ds < plot_seconds)

    freq_ori = np.fft.fftfreq(len(ori_data), d=1 / fs_ori)
    # 计算 fs_ds Hz 采样率对应的 Nyquist 频率索引 (fs_ds/2 Hz)
    mag_ds_full = np.abs(fft(ds_data))
    # 计算 ds_data 的频率轴
    freq_ds = np.fft.fftfreq(len(ds_data), d=1 / fs_ds)
    # 使用频谱的前半部分（FFT结果是对称的）
    nyquist_idx = len(mag_ds_full) // 2
    # 定义频率掩码，使用 0:2*Nyquist_idx 作为频率范围
    freq_mask = slice(0, 2 * nyquist_idx)

    res_data_comparison = {}
    for m in results.keys():
        aligned = results[m]["aligned"]
        mag_aligned = np.abs(fft(aligned))
        
        # 计算对齐后数据的频率轴
        freq_aligned = np.fft.fftfreq(len(aligned), d=1 / fs_ori)
        
        # 将降采样频谱插值到对齐后数据的频率轴上
        from scipy.interpolate import interp1d
        # 创建降采样频谱的插值函数（只使用正频率部分）
        freq_ds_positive = freq_ds[:nyquist_idx]
        mag_ds_positive = mag_ds_full[:nyquist_idx]
        # 插值到对齐后数据的频率轴上
        interp_func = interp1d(freq_ds_positive, mag_ds_positive, kind='linear', bounds_error=False, fill_value=MIN_MAGNITUDE)
        mag_ds_interpolated = interp_func(freq_aligned[:2 * nyquist_idx])

        res_data_comparison[m] = {
            "time_domain": {
                "x1": t_ori[time_mask_ori],
                "y1": aligned[time_mask_ori],
                "x2": t_ds[time_mask_ds],
                "y2": ds_data[time_mask_ds],
                "x3": t_ori[time_mask_ori],
                "y3": ori_data[time_mask_ori],
                "similarity": results[m]["metrics"]["dtw_time"],
            },
            "freq_domain": {
                "x": {"value": freq_aligned[freq_mask], "label": "频率"},
                "y1": {
                    "value": mag_ds_interpolated,
                    "label": f"{fs_ds}Hz原始频谱",
                },
                "y2": {
                    "value": mag_aligned[freq_mask],
                    "label": f"{m}对齐到{fs_ori}Hz频谱",
                },
                "similarity": results[m]["metrics"]["dtw_frequency"],
            },
            "combined_similarity": results[m]["metrics"]["combined_metric"],
        }

    return json_serialize_with_ndarray(res_data_comparison)


def plot_align_results(json_str: str):
    """
    可视化 random_sampling_align 的输出结果。
    """
    data = json.loads(json_str)
    methods = list(data.keys())

    # 创建 3x2 的子图布局
    fig, axes = plt.subplots(len(methods), 2, figsize=(16, 4 * len(methods)))
    fig.suptitle("不同重采样对齐方法验证结果 (真实数据)", fontsize=16)

    for i, m in enumerate(methods):
        method_data = data[m]

        # 1. 时域图
        ax_time = axes[i, 0]
        td = method_data["time_domain"]
        ax_time.plot(td["x3"], td["y3"], label="原始信号 (20Hz)", color="black", linestyle=":", alpha=0.4)
        ax_time.plot(td["x1"], td["y1"], label=f"{m} 对齐后 (20Hz)", alpha=0.8, color="C0")
        ax_time.scatter(td["x2"], td["y2"], label="5Hz 输入点", color="red", s=15, zorder=5)
        ax_time.set_title(f"{m} 时域对比 (DTW Time: {td['similarity']:.4f})")
        ax_time.set_xlabel("时间 (s)")
        ax_time.set_ylabel("幅值")
        ax_time.legend()
        ax_time.grid(True, linestyle=":", alpha=0.6)

        # 2. 频域图
        ax_freq = axes[i, 1]
        fd = method_data["freq_domain"]
        ax_freq.plot(fd["x"]["value"], fd["y1"]["value"], label=fd["y1"]["label"], alpha=0.5, color="gray")
        ax_freq.plot(fd["x"]["value"], fd["y2"]["value"], label=fd["y2"]["label"], linestyle="--", color="C1")
        ax_freq.set_yscale("log")  # 改为对数坐标
        ax_freq.set_title(f"{m} 频域对比 (DTW Freq: {fd['similarity']:.4f})")
        ax_freq.set_xlabel("频率 (Hz)")
        ax_freq.set_ylabel("幅度 (Log)")
        ax_freq.set_ylim(MIN_MAGNITUDE / 2, 1e3)
        ax_freq.legend()
        ax_freq.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

# endregion


# region 2026年1月19日10点55分 - 在真实数据上验证低采样率重建的效果

# 表9-欠采样-新版，在真实数据上验证低采样率重建的效果
def get_low_sampling_res(group: int = 1, pct: float = 0.30, do_compensation: bool = True, plot: bool = False):
    """
    获取低采样率的结果数据。

    group: int, 第几组数据, 1/2/3/4, 分别对应不同的低采样率结果:
        - 1/2/3: 文件夹"data/table9展示数据/"中的不同的数据文件(data1.csv, data2.csv, data3.csv)，group1是报告中的结果
        - 4: 8Hz真实数据(real_data_8Hz.csv)，降采样到1Hz后重建
    pct: float, 中间部分的比例，默认0.30，即取中间30%的数据进行重建。
    do_compensation: bool, 是否进行残差补偿，默认True。
    plot: bool, 是否绘制时域和频域图，默认False。
    """
    assert group in [1, 2, 3, 4], "group参数必须是1/2/3/4之一。"
    
    if group == 4:
        return test_real_data_8hz_low_sampling(pct=1.0, do_compensation=True, plot=False)
    
    csv_path = DATA_DIR / f"table10展示数据/data{group}.csv"
    ori_data = pd.read_csv(csv_path, header=None).values.flatten()

    n = len(ori_data)
    margin = (1 - pct) / 2
    start = int(n * margin)
    end = int(n * (1 - margin))
    ori_data = ori_data[start:end]

    fs_original = 20  # 原始采样率
    downsample_factor = 5  # 降采样因子
    fs_low = fs_original // downsample_factor  # 降采样后的采样率

    ds_data = downsample_data(ori_data, factor=downsample_factor, method="uniform")

    configs = {
        'signal_data': ds_data,
        'target_fs': fs_low,
        'samples_to_use': 0,
        'fs_high': fs_original,
        'M': 100,
        'method': "bpdn",
        'theoretical_freqs': [3.33, 3.34, 6.67],
        'plot_steps': plot,
        'do_compensation': do_compensation
    }

    # 执行重建
    recon_signal, recon_info = run_real_data_experiment(**configs)

    t_ori = np.linspace(0, len(ori_data) / fs_original, len(ori_data), endpoint=False)
    t_ds = np.linspace(0, len(ds_data) / fs_low, len(ds_data), endpoint=False)
    
    # 计算一些基本指标供返回使用
    # metrics = metrics_compute(ori_data, recon_signal, fs_ds=fs_low, fs_ori=fs_original)
    
    # 计算 RMSE, MAE, Cosine Similarity (与旧版 reconstruct_rearranged_signal 保持一致)
    rmse = np.sqrt(np.mean((ori_data - recon_signal) ** 2))
    mae = np.mean(np.abs(ori_data - recon_signal))
    cos_sim = np.dot(ori_data, recon_signal) / (
        np.linalg.norm(ori_data) * np.linalg.norm(recon_signal)
    )

    # 提取评估指标，剔除大型复数数组（保持与旧版一致，只保留标量指标，避免序列化问题）
    display_metrics = {
        "rmse": float(rmse),
        "mae": float(mae),
        "cos_sim": float(cos_sim),
        # "ratio": float(recon_info.get("ratio", 0)),
        # "dtw_time": float(metrics["dtw_time"]),
        # "dtw_frequency": float(metrics["dtw_frequency"]),
        # "combined_similarity": float((metrics["dtw_time"] + metrics["dtw_frequency"]) / 2)
    }

    if plot:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 原始信号时域
        axes[0, 0].plot(t_ori, ori_data)
        axes[0, 0].set_title(f"原始信号 - 时域 ({fs_original}Hz)")
        axes[0, 0].set_xlabel("时间 (s)")
        axes[0, 0].grid(True)

        # 原始信号频谱
        freq_ori_plot = np.fft.fftfreq(len(ori_data), d=1/fs_original)
        mag_ori_plot = np.abs(fft(ori_data))
        axes[0, 1].plot(freq_ori_plot[:len(freq_ori_plot)//2], mag_ori_plot[:len(mag_ori_plot)//2])
        axes[0, 1].set_title("原始信号 - 频谱")
        axes[0, 1].set_xlabel("频率 (Hz)")
        axes[0, 1].set_yscale("log")
        axes[0, 1].grid(True)

        # 降采样信号时域
        axes[1, 0].plot(t_ds, ds_data, color='orange')
        axes[1, 0].set_title(f"降采样信号 - 时域 ({fs_low}Hz)")
        axes[1, 0].set_xlabel("时间 (s)")
        axes[1, 0].grid(True)

        # 降采样信号频谱
        freq_ds_plot = np.fft.fftfreq(len(ds_data), d=1/fs_low)
        mag_ds_plot = np.abs(fft(ds_data))
        axes[1, 1].plot(freq_ds_plot[:len(freq_ds_plot)//2], mag_ds_plot[:len(mag_ds_plot)//2], color='orange')
        axes[1, 1].set_title("降采样信号 - 频谱")
        axes[1, 1].set_xlabel("频率 (Hz)")
        axes[1, 1].set_yscale("log")
        axes[1, 1].grid(True)

        plt.tight_layout()
        plt.show()

    # 3. 组织返回数据，参考 get_low_sampling_res_bak 的结构 (Line 240)
    freq_ori = np.fft.fftfreq(len(ori_data), d=1 / fs_original)
    fft_ori = np.abs(fft(ori_data))
    
    freq_recon = np.fft.fftfreq(len(recon_signal), d=1 / fs_original)
    fft_recon = np.abs(fft(recon_signal))
    
    # 选取一段“详情”展示，这里取总时长的 1/4 到 3/4 处
    n_t = len(t_ori)
    detail_mask = slice(n_t // 4, 3 * n_t // 4)
    # detail_mask = slice(None, None)  # 展示全部内容

    res_data_under_sampling = [
        {
            "x1": {
                "value": t_ds,
                "label": "时间",
            },
            "y1": {
                "value": ds_data,
                "title": "欠采样结果",
            },
            "x2": {
                "value": t_ori,
                "label": "时间",
            },
            "y2": {
                "value": ori_data,
                "title": "原始信号",
            },
        },
        {
            "x": {
                "value": t_ori[detail_mask],
                "title": "时间",
            },
            "y1": {
                "value": ori_data[detail_mask],
                "title": "原始信号详情",
            },
            "y2": {
                "value": recon_signal[detail_mask],
                "title": "重建信号详情",
            },
            "recon_metrics": display_metrics,
        },
        {
            "x1": {
                "value": freq_ori[: len(freq_ori) // 2],
                "label": "原始信号频率",
            },
            "y1": {
                "value": fft_ori[: len(fft_ori) // 2],
                "title": "原始信号频谱",
            },
            "x2": {
                "value": freq_recon[: len(freq_recon) // 2],
                "label": "重建信号频率",
            },
            "y2": {
                "value": fft_recon[: len(fft_recon) // 2],
                "title": "重建信号频谱",
            },
        },
    ]

    return json_serialize_with_ndarray(res_data_under_sampling)


def plot_low_sampling_results(json_str: str):
    """
    可视化 get_low_sampling_res 的输出结果。
    """
    res_data = json.loads(json_str)

    # 创建 3x1 的布局
    fig, axes = plt.subplots(3, 1, figsize=(12, 18))
    fig.suptitle("低采样率重建验证结果 (真实数据)", fontsize=16)

    # 1. 整体时域对比图 (对应 res_data[0])
    ax0 = axes[0]
    d0 = res_data[0]
    ax0.plot(d0["x2"]["value"], d0["y2"]["value"], label=d0["y2"]["title"], color="black", alpha=0.3, linestyle=":")
    ax0.scatter(d0["x1"]["value"], d0["y1"]["value"], label=d0["y1"]["title"], color="red", s=10)
    ax0.set_title("原始信号 vs 欠采样观测点")
    ax0.set_xlabel("时间 (s)")
    ax0.set_ylabel("幅值")
    ax0.legend()
    ax0.grid(True, linestyle=":", alpha=0.6)

    # 2. 时域重建详情图 (对应 res_data[1])
    ax1 = axes[1]
    d1 = res_data[1]
    metrics = d1["recon_metrics"]
    metrics_str = (
        f"RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, CosSim: {metrics['cos_sim']:.4f}\n"
        # f"DTW Time: {metrics['dtw_time']:.4f}, DTW Freq: {metrics['dtw_frequency']:.4f}, Ratio: {metrics['ratio']:.4%}"
    )

    ax1.plot(d1["x"]["value"], d1["y1"]["value"], label=d1["y1"]["title"], color="gray", alpha=0.5)
    ax1.plot(d1["x"]["value"], d1["y2"]["value"], label=d1["y2"]["title"], color="blue", linewidth=1.5)
    ax1.set_title(f"重建详情对比\n({metrics_str})")
    ax1.set_xlabel("时间 (s)")
    ax1.set_ylabel("幅值")
    ax1.legend()
    ax1.grid(True, linestyle=":", alpha=0.6)

    # 3. 频域对比图 (对应 res_data[2])
    ax2 = axes[2]
    d2 = res_data[2]
    ax2.plot(d2["x1"]["value"], d2["y1"]["value"], label=d2["y1"]["title"], color="gray", alpha=0.5)
    ax2.plot(d2["x2"]["value"], d2["y2"]["value"], label=d2["y2"]["title"], color="red", linestyle="--")
    ax2.set_yscale("log")
    ax2.set_title("频谱对比 (Log Scale)")
    ax2.set_xlabel("频率 (Hz)")
    ax2.set_ylabel("幅度")
    ax2.legend()
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

# endregion


# region 2026年1月26日17:39:58 - 0.25Hz --(采样率对齐)--> 1Hz --(压缩感知)--> 8Hz 流程
def test_real_data_1hz(plot=False):
    """
    在真实1Hz数据上验证随机采样率对齐效果：
    - 读取1Hz真实数据
    - 降采样到0.2Hz
    - 使用不同方法对齐回1Hz
    - 比较对齐效果
    """
    # 读取1Hz真实数据
    csv_path = DATA_DIR / "real_data_1Hz.csv"
    ori_data = pd.read_csv(csv_path, header=None).values.flatten()
    
    fs_original = 1.0  # 原始采样率
    downsample_factor = 4  # 降采样因子，从1Hz降到0.25Hz
    fs_low = fs_original / downsample_factor  # 降采样后的采样率
    
    # 降采样到0.2Hz
    ds_data = downsample_data(ori_data, factor=downsample_factor, method="uniform")
    
    # 创建时间轴
    t_ori = np.linspace(0, len(ori_data) / fs_original, len(ori_data), endpoint=False)
    t_ds = np.linspace(0, len(ds_data) / fs_low, len(ds_data), endpoint=False)
    
    # 计算总时长，用于绘图
    plot_seconds = len(ori_data) / fs_original
    
    # 使用compare_resample_methods函数比较不同方法
    results = compare_resample_methods(
        ori_data,
        ds_data,
        t_ori,
        t_ds,
        methods=["linear", "cubic", "freq"],
        plot_seconds=plot_seconds,
        fs_ds=fs_low,
        fs_ori=fs_original,
        plot=plot,
    )
    
    # 重新组织结果，以便返回或可视化
    res_data_comparison = {}
    
    # 计算频谱
    mag_ds_full = np.abs(fft(ds_data))
    # 计算 ds_data 的频率轴
    freq_ds = np.fft.fftfreq(len(ds_data), d=1 / fs_low)
    # 使用频谱的前半部分（FFT结果是对称的）
    nyquist_idx = len(mag_ds_full) // 2
    # 定义频率掩码，使用 0:2*Nyquist_idx 作为频率范围
    freq_mask = slice(0, 2 * nyquist_idx)
    
    for m in results.keys():
        aligned = results[m]["aligned"]
        mag_aligned = np.abs(fft(aligned))
        
        # 计算对齐后数据的频率轴
        freq_aligned = np.fft.fftfreq(len(aligned), d=1 / fs_original)
        
        # 将降采样频谱插值到对齐后数据的频率轴上
        from scipy.interpolate import interp1d
        # 创建降采样频谱的插值函数（只使用正频率部分）
        freq_ds_positive = freq_ds[:nyquist_idx]
        mag_ds_positive = mag_ds_full[:nyquist_idx]
        # 插值到对齐后数据的频率轴上
        interp_func = interp1d(freq_ds_positive, mag_ds_positive, kind='linear', bounds_error=False, fill_value=MIN_MAGNITUDE)
        mag_ds_interpolated = interp_func(freq_aligned[:2 * nyquist_idx])
        
        # 创建时间掩码（与 get_random_sampling_res 保持一致）
        time_mask_ori = np.where(t_ori < plot_seconds)
        time_mask_ds = np.where(t_ds < plot_seconds)
        
        res_data_comparison[m] = {
            "time_domain": {
                "x1": t_ori[time_mask_ori],
                "y1": aligned[time_mask_ori],
                "x2": t_ds[time_mask_ds],
                "y2": ds_data[time_mask_ds],
                "x3": t_ori[time_mask_ori],
                "y3": ori_data[time_mask_ori],
                "similarity": results[m]["metrics"]["dtw_time"],
            },
            "freq_domain": {
                "x": {"value": freq_aligned[freq_mask], "label": "频率"},
                "y1": {
                    "value": mag_ds_interpolated,
                    "label": f"{fs_low}Hz原始频谱",
                },
                "y2": {
                    "value": mag_aligned[freq_mask],
                    "label": f"{m}对齐到{fs_original}Hz频谱",
                },
                "similarity": results[m]["metrics"]["dtw_frequency"],
            },
            "combined_similarity": results[m]["metrics"]["combined_metric"],
        }
    
    return json_serialize_with_ndarray(res_data_comparison)


def test_real_data_8hz_low_sampling(pct: float = 0.30, do_compensation: bool = True, plot: bool = False):
    """
    在真实8Hz数据上验证低采样率重建效果：
    - 读取8Hz真实数据
    - 降采样到1Hz (factor=8)
    - 使用run_real_data_experiment进行重建到8Hz
    - 比较原始数据与重建数据的效果
    
    Args:
        pct: float, 中间部分的比例，默认0.30，即取中间30%的数据进行重建。
        do_compensation: bool, 是否进行残差补偿，默认True。
        plot: bool, 是否绘制时域和频域图，默认False。
    """
    # 读取8Hz真实数据
    csv_path = DATA_DIR / "real_data_8Hz.csv"
    ori_data = pd.read_csv(csv_path, header=None).values.flatten()
    
    # 截取中间部分
    n = len(ori_data)
    margin = (1 - pct) / 2
    start = int(n * margin)
    end = int(n * (1 - margin))
    ori_data = ori_data[start:end]
    
    fs_original = 8  # 原始采样率
    downsample_factor = 8  # 降采样因子
    fs_low = fs_original // downsample_factor  # 降采样后的采样率 (1Hz)
    
    # 降采样到1Hz
    ds_data = downsample_data(ori_data, factor=downsample_factor, method="uniform")
    
    # 配置重建参数
    configs = {
        'signal_data': ds_data,
        'target_fs': fs_low,
        'samples_to_use': 0,
        'fs_high': fs_original,
        'M': 100,
        'method': "bpdn",
        'theoretical_freqs': [2.504, 3.343, 1.856],  # 根据实际情况调整理论频率
        'plot_steps': plot,
        'do_compensation': do_compensation
    }
    
    # 执行重建
    recon_signal, recon_info = run_real_data_experiment(**configs)
    
    # 调整重建信号长度以匹配原始数据长度
    if len(recon_signal) > len(ori_data):
        recon_signal = recon_signal[:len(ori_data)]
    elif len(recon_signal) < len(ori_data):
        recon_signal = np.pad(recon_signal, (0, len(ori_data) - len(recon_signal)), 'constant')
    
    # 创建时间轴
    t_ori = np.linspace(0, len(ori_data) / fs_original, len(ori_data), endpoint=False)
    t_ds = np.linspace(0, len(ds_data) / fs_low, len(ds_data), endpoint=False)
    
    # 计算评估指标
    rmse = np.sqrt(np.mean((ori_data - recon_signal) ** 2))
    mae = np.mean(np.abs(ori_data - recon_signal))
    cos_sim = np.dot(ori_data, recon_signal) / (
        np.linalg.norm(ori_data) * np.linalg.norm(recon_signal)
    )
    
    display_metrics = {
        "rmse": float(rmse),
        "mae": float(mae),
        "cos_sim": float(cos_sim),
    }
    
    if plot:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 原始信号时域
        axes[0, 0].plot(t_ori, ori_data)
        axes[0, 0].set_title(f"原始信号 - 时域 ({fs_original}Hz)")
        axes[0, 0].set_xlabel("时间 (s)")
        axes[0, 0].grid(True)
        
        # 原始信号频谱
        freq_ori_plot = np.fft.fftfreq(len(ori_data), d=1/fs_original)
        mag_ori_plot = np.abs(fft(ori_data))
        axes[0, 1].plot(freq_ori_plot[:len(freq_ori_plot)//2], mag_ori_plot[:len(mag_ori_plot)//2])
        axes[0, 1].set_title("原始信号 - 频谱")
        axes[0, 1].set_xlabel("频率 (Hz)")
        axes[0, 1].set_yscale("log")
        axes[0, 1].grid(True)
        
        # 降采样信号时域
        axes[1, 0].plot(t_ds, ds_data, color='orange')
        axes[1, 0].set_title(f"降采样信号 - 时域 ({fs_low}Hz)")
        axes[1, 0].set_xlabel("时间 (s)")
        axes[1, 0].grid(True)
        
        # 降采样信号频谱
        freq_ds_plot = np.fft.fftfreq(len(ds_data), d=1/fs_low)
        mag_ds_plot = np.abs(fft(ds_data))
        axes[1, 1].plot(freq_ds_plot[:len(freq_ds_plot)//2], mag_ds_plot[:len(mag_ds_plot)//2], color='orange')
        axes[1, 1].set_title("降采样信号 - 频谱")
        axes[1, 1].set_xlabel("频率 (Hz)")
        axes[1, 1].set_yscale("log")
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.show()
    
    # 组织返回数据，参考 get_low_sampling_res 的结构
    freq_ori = np.fft.fftfreq(len(ori_data), d=1 / fs_original)
    fft_ori = np.abs(fft(ori_data))
    
    freq_recon = np.fft.fftfreq(len(recon_signal), d=1 / fs_original)
    fft_recon = np.abs(fft(recon_signal))
    
    # 选取一段"详情"展示，这里取总时长的 1/4 到 3/4 处
    n_t = len(t_ori)
    detail_mask = slice(n_t // 4, 3 * n_t // 4)
    
    res_data_under_sampling = [
        {
            "x1": {
                "value": t_ds,
                "label": "时间",
            },
            "y1": {
                "value": ds_data,
                "title": "欠采样结果",
            },
            "x2": {
                "value": t_ori,
                "label": "时间",
            },
            "y2": {
                "value": ori_data,
                "title": "原始信号",
            },
        },
        {
            "x": {
                "value": t_ori[detail_mask],
                "title": "时间",
            },
            "y1": {
                "value": ori_data[detail_mask],
                "title": "原始信号详情",
            },
            "y2": {
                "value": recon_signal[detail_mask],
                "title": "重建信号详情",
            },
            "y3": {
                "value": recon_signal,
                "title": "重建信号",
            },
            "recon_metrics": display_metrics,
        },
        {
            "x1": {
                "value": freq_ori[: len(freq_ori) // 2],
                "label": "原始信号频率",
            },
            "y1": {
                "value": fft_ori[: len(fft_ori) // 2],
                "title": "原始信号频谱",
            },
            "x2": {
                "value": freq_recon[: len(freq_recon) // 2],
                "label": "重建信号频率",
            },
            "y2": {
                "value": fft_recon[: len(fft_recon) // 2],
                "title": "重建信号频谱",
            },
        },
    ]
    
    return json_serialize_with_ndarray(res_data_under_sampling)


def plot_1hz_results(json_str: str, method: str = None, pct: float = 0.30, save: bool = False, save_dir: str = None):
    """
    可视化 1Hz 真实数据的验证结果，包含四个部分：
    1. 降采样后的数据（原数据曲线 + 降采样点）
    2. 恢复后的数据（原数据曲线 + 恢复后曲线 + 降采样点）
    3. 整体局部放大图（原数据曲线 + 恢复后曲线 + 降采样点）
    4. 频谱图（整体对比）
    
    Args:
        json_str: test_real_data_1hz 返回的 JSON 字符串
        method: 要显示的方法名称，如果为 None 则使用第一个方法
        pct: 局部显示的比例，默认 0.30
        save: 是否保存图片，默认 False
        save_dir: 保存图片的目录，如果为 None 则使用当前目录
    """
    data = json.loads(json_str)
    methods = list(data.keys())
    
    # 如果没有指定方法，使用第一个方法
    if method is None:
        method = methods[0]
    elif method not in methods:
        raise ValueError(f"方法 '{method}' 不存在，可选的方法有: {methods}")
    
    # 获取数据
    td = data[method]["time_domain"]
    fd = data[method]["freq_domain"]
    
    # 设置保存目录
    if save_dir is None:
        save_dir = BASE_DIR
    
    # 1. 图1：降采样后的数据
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(td["x3"], td["y3"], label="原始信号", color="black", linestyle=":", alpha=0.6)
    ax1.scatter(td["x2"], td["y2"], label="降采样点", color="red", s=30, zorder=5)
    ax1.set_title("降采样后的数据")
    ax1.set_xlabel("时间 (s)")
    ax1.set_ylabel("幅值")
    ax1.legend()
    ax1.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    if save:
        save_path = Path(save_dir) / f"1hz_{method}_downsampled.png"
        fig1.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存: {save_path}")
    plt.show()
    
    # 2. 图2：恢复后的数据
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.plot(td["x3"], td["y3"], label="原始信号", color="black", linestyle=":", alpha=0.6)
    ax2.plot(td["x1"], td["y1"], label=f"恢复后", alpha=0.8, color="C0")
    ax2.scatter(td["x2"], td["y2"], label="降采样点", color="red", s=30, zorder=5)
    ax2.set_title(f"恢复后的数据")
    ax2.set_xlabel("时间 (s)")
    ax2.set_ylabel("幅值")
    ax2.legend()
    ax2.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    if save:
        save_path = Path(save_dir) / f"1hz_{method}_recovered.png"
        fig2.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存: {save_path}")
    plt.show()
    
    # 3. 图3：整体局部放大图
    fig3, ax3 = plt.subplots(figsize=(12, 6))
    
    # 计算局部显示的范围
    total_len = len(td["x3"])
    start_idx = int(total_len * (0.5 - pct / 2))
    end_idx = int(total_len * (0.5 + pct / 2))
    
    # 提取局部数据
    x_local = td["x3"][start_idx:end_idx]
    y3_local = td["y3"][start_idx:end_idx]
    y1_local = td["y1"][start_idx:end_idx]
    
    # 提取局部降采样点
    x2_array = np.array(td["x2"])
    ds_mask = (x2_array >= x_local[0]) & (x2_array <= x_local[-1])
    x_ds_local = x2_array[ds_mask]
    y_ds_local = np.array(td["y2"])[ds_mask]
    
    ax3.plot(x_local, y3_local, label="原始信号", color="black", linestyle=":", alpha=0.6)
    ax3.plot(x_local, y1_local, label=f"恢复后", alpha=0.9, color="C0")
    ax3.scatter(x_ds_local, y_ds_local, label="降采样点", color="red", s=30, zorder=5)
    ax3.set_title(f"整体局部放大 (中间 {pct*100:.0f}%)")
    ax3.set_xlabel("时间 (s)")
    ax3.set_ylabel("幅值")
    ax3.legend()
    ax3.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    if save:
        save_path = Path(save_dir) / f"1hz_{method}_zoomed.png"
        fig3.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存: {save_path}")
    plt.show()
    
    # 4. 图4：频谱图（整体对比）
    fig4, ax4 = plt.subplots(figsize=(12, 6))
    ax4.plot(fd["x"]["value"], fd["y1"]["value"], label=fd["y1"]["label"], alpha=0.5, color="gray")
    ax4.plot(fd["x"]["value"], fd["y2"]["value"], label=fd["y2"]["label"], linestyle="--", color="C1")
    ax4.set_title(f"频谱对比")
    ax4.set_xlabel("频率 (Hz)")
    ax4.set_ylabel("幅度 (Log)")
    ax4.set_yscale("log")
    ax4.set_ylim(MIN_MAGNITUDE / 2, 1e3)
    ax4.legend()
    ax4.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    if save:
        save_path = Path(save_dir) / f"1hz_{method}_frequency.png"
        fig4.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存: {save_path}")
    plt.show()


def plot_8hz_low_sampling_results(json_str: str, pct: float = 0.30, save: bool = False, save_dir: str = None):
    """
    可视化 8Hz 真实数据的低采样率重建结果，包含四个部分：
    1. 降采样后的数据（原数据曲线 + 降采样点）
    2. 重建后的数据（原数据曲线 + 重建后曲线 + 降采样点）
    3. 整体局部放大图（原数据曲线 + 重建后曲线 + 降采样点）
    4. 频谱图（整体对比）
    
    Args:
        json_str: test_real_data_8hz_low_sampling 返回的 JSON 字符串
        pct: 局部显示的比例，默认 0.30
        save: 是否保存图片，默认 False
        save_dir: 保存图片的目录，如果为 None 则使用当前目录
    """
    data = json.loads(json_str)
    
    # 获取数据
    # data[0]: 欠采样结果 vs 原始信号
    # data[1]: 原始信号详情 vs 重建信号详情
    # data[2]: 原始信号频谱 vs 重建信号频谱
    
    d0 = data[0]  # 欠采样结果
    d1 = data[1]  # 重建详情
    d2 = data[2]  # 频谱对比
    
    # 设置保存目录
    if save_dir is None:
        save_dir = BASE_DIR
    
    # 1. 图1：降采样后的数据
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(d0["x2"]["value"], d0["y2"]["value"], label="原始信号 (8Hz)", color="black", linestyle=":", alpha=0.6)
    ax1.scatter(d0["x1"]["value"], d0["y1"]["value"], label="降采样点 (1Hz)", color="red", s=30, zorder=5)
    ax1.set_title("降采样后的数据 (8Hz -> 1Hz)")
    ax1.set_xlabel("时间 (s)")
    ax1.set_ylabel("幅值")
    ax1.legend()
    ax1.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    if save:
        save_path = Path(save_dir) / "8hz_low_sampling_downsampled.png"
        fig1.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存: {save_path}")
    plt.show()
    
    # 2. 图2：重建后的数据
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    ax2.plot(d0["x2"]["value"], d0["y2"]["value"], label="原始信号 (8Hz)", color="black", linestyle=":", alpha=0.6)
    ax2.plot(d0["x2"]["value"], d1["y3"]["value"], label="重建信号 (8Hz)", alpha=0.8, color="C0")
    ax2.scatter(d0["x1"]["value"], d0["y1"]["value"], label="降采样点 (1Hz)", color="red", s=30, zorder=5)
    ax2.set_title("重建后的数据 (1Hz -> 8Hz)")
    ax2.set_xlabel("时间 (s)")
    ax2.set_ylabel("幅值")
    ax2.legend()
    ax2.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    if save:
        save_path = Path(save_dir) / "8hz_low_sampling_recovered.png"
        fig2.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存: {save_path}")
    plt.show()
    
    # 3. 图3：整体局部放大图
    fig3, ax3 = plt.subplots(figsize=(12, 6))
    
    # 计算局部显示的范围
    total_len = len(d1["x"]["value"])
    start_idx = int(total_len * (0.5 - pct / 2))
    end_idx = int(total_len * (0.5 + pct / 2))
    
    # 提取局部数据
    x_local = d1["x"]["value"][start_idx:end_idx]
    y1_local = d1["y1"]["value"][start_idx:end_idx]
    y2_local = d1["y2"]["value"][start_idx:end_idx]
    
    # 提取局部降采样点
    x1_array = np.array(d0["x1"]["value"])
    y1_array = np.array(d0["y1"]["value"])
    ds_mask = (x1_array >= x_local[0]) & (x1_array <= x_local[-1])
    x_ds_local = x1_array[ds_mask]
    y_ds_local = y1_array[ds_mask]
    
    ax3.plot(x_local, y1_local, label="原始信号 (8Hz)", color="black", linestyle=":", alpha=0.6)
    ax3.plot(x_local, y2_local, label="重建信号 (8Hz)", alpha=0.9, color="C0")
    ax3.scatter(x_ds_local, y_ds_local, label="降采样点 (1Hz)", color="red", s=30, zorder=5)
    
    # 显示重建指标
    metrics = d1["recon_metrics"]
    metrics_str = f"RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, CosSim: {metrics['cos_sim']:.4f}"
    ax3.set_title(f"整体局部放大\n{metrics_str}")
    ax3.set_xlabel("时间 (s)")
    ax3.set_ylabel("幅值")
    ax3.legend()
    ax3.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    if save:
        save_path = Path(save_dir) / "8hz_low_sampling_zoomed.png"
        fig3.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存: {save_path}")
    plt.show()
    
    # 4. 图4：频谱图（整体对比）
    fig4, ax4 = plt.subplots(figsize=(12, 6))
    ax4.plot(d2["x1"]["value"], d2["y1"]["value"], label=d2["y1"]["title"], alpha=0.5, color="gray")
    ax4.plot(d2["x2"]["value"], d2["y2"]["value"], label=d2["y2"]["title"], linestyle="--", color="C1")
    ax4.set_title("频谱对比")
    ax4.set_xlabel("频率 (Hz)")
    ax4.set_ylabel("幅度 (Log)")
    ax4.set_yscale("log")
    ax4.legend()
    ax4.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    if save:
        save_path = Path(save_dir) / "8hz_low_sampling_frequency.png"
        fig4.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存: {save_path}")
    plt.show()
# endregion


# region 2026年1月27日03:26:13 - 时快时慢数据

# 这里定义演示数据的默认配置，方便统一修改
FAST_SLOW_DEFAULTS = {
    "start_time": "2017-02-05 13:39:10",
    "segments": [
        {"duration": 120, "freq": 1.0},   # 高频观测段 (2分钟)
        {"duration": 3480, "freq": 1/64}  # 稀疏采样段 (58分钟)
    ],
    "ref_duration": 120  # 用于提取先验频谱的参考时长
}

INTERMITTENT_DEFAULTS = {
    "start_time": "2017-02-05 13:39:10",
    "segments": [
        {"duration": 120, "freq": 1.0},
        {"duration": 480, "freq": 1/64},
        {"duration": 2400, "freq": 0.0},
        {"duration": 600, "freq": 1/64}
    ]
}

def get_fast_slow_reconstruction_res(segments=None, start_time_str=None):
    """
    时快时慢采样数据的重建接口。
    
    Args:
        segments: List[dict], 可选，分段配置如 [{"duration": 120, "freq": 1.0}, ...]
        start_time_str: str, 可选，起始时间字符串
    """
    from reconstruction_engine import SignalReconstructor
    
    # 优先使用传入参数，否则使用默认值
    segments = segments or FAST_SLOW_DEFAULTS["segments"]
    start_time_str = start_time_str or FAST_SLOW_DEFAULTS["start_time"]
    ref_limit = FAST_SLOW_DEFAULTS["ref_duration"]

    # 1. 加载数据
    try:
        df_ref = pd.read_csv(DATA_DIR / "fast-slow_reference_1hz.csv")
        df_obs = pd.read_csv(DATA_DIR / "fast-slow.csv")
    except Exception as e:
        return json.dumps({"error": f"Data files not found: {str(e)}"})
        
    y_ref = df_ref['value'].values.astype(np.float32)
    t_ref = np.arange(len(y_ref)).astype(np.float32)
    
    y_obs = df_obs['value'].values.astype(np.float32)
    # 动态解析起始时间，不再硬编码
    base_time = pd.to_datetime(start_time_str)
    t_obs = (pd.to_datetime(df_obs['timestamp']) - base_time).dt.total_seconds().values.astype(np.float32)
    
    # 2. 执行重建逻辑
    engine_all = SignalReconstructor()
    y_linear = engine_all.linear_reconstruct(t_obs, y_obs, t_ref)
    y_cubic = engine_all.cubic_reconstruct(t_obs, y_obs, t_ref)
    
    # 引导式重建：分析各段采样频率，自动选择最佳指纹参考段
    max_f = -1.0
    best_dur_start = 0
    best_dur_end = segments[0]["duration"]
    
    curr_t = 0
    for seg in segments:
        if seg["freq"] > max_f:
            max_f = seg["freq"]
            best_dur_start = curr_t
            best_dur_end = curr_t + seg["duration"]
        curr_t += seg["duration"]
        
    ref_mask = (t_obs >= best_dur_start) & (t_obs < best_dur_end)
    if not np.any(ref_mask):
        engine_guided = SignalReconstructor(y_obs, t_obs) # 保底
    else:
        engine_guided = SignalReconstructor(y_obs[ref_mask], t_obs[ref_mask])
    
    y_guided = np.zeros_like(t_ref)
    curr_t = 0
    total_t = t_ref[-1] - t_ref[0]
    for seg in segments:
        dur, freq = seg["duration"], seg["freq"]
        end_t = curr_t + dur
        
        # 确定目标点范围
        mask_t_ref = (t_ref >= curr_t) & (t_ref < end_t)
        if not np.any(mask_t_ref): continue
        t_target_seg = t_ref[mask_t_ref]
        
        # 自适应窗口：宽窗观测确保跨越空洞点的关联
        margin = max(60.0, total_t * 0.15)
        mask_t_obs = (t_obs >= curr_t - margin) & (t_obs <= end_t + margin)
        
        if not np.any(mask_t_obs): mask_t_obs = np.ones(len(y_obs), dtype=bool)

        if freq >= 1.0:
            y_guided[mask_t_ref] = engine_guided.linear_reconstruct(t_obs[mask_t_obs], y_obs[mask_t_obs], t_target_seg)
        else:
            y_guided[mask_t_ref] = engine_guided.guided_spectral_reconstruct(t_obs[mask_t_obs], y_obs[mask_t_obs], t_target_seg)
        curr_t = end_t

    # 3. 构造返回结构 (Key 使用英文)
    methods_map = {"Linear": y_linear, "Cubic": y_cubic, "Guided": y_guided}
    results = {}
    
    for name, y_rec in methods_map.items():
        metrics = metrics_compute(y_ref, y_rec, fs_ds=None, fs_ori=1.0)
        results[name] = {
            "reference": {"time": t_ref, "value": y_ref},
            "observation": {"time": t_obs, "value": y_obs},
            "reconstruction": {"time": t_ref, "value": y_rec},
            "metrics": {
                "RMSE": float(np.sqrt(np.mean((y_ref - y_rec)**2))),
                "DTW": float(metrics['dtw_time'])
            }
        }
        
    return json_serialize_with_ndarray(results)

def get_intermittent_reconstruction_res(segments=None, start_time_str=None):
    """
    时有时无（带大空洞）采样数据的重建接口。
    
    Args:
        segments: List[dict], 可选，分段配置
        start_time_str: str, 可选，起始时间字符串
    """
    from reconstruction_engine import SignalReconstructor
    
    # 优先使用传入参数，否则使用默认值
    segments = segments or INTERMITTENT_DEFAULTS["segments"]
    start_time_str = start_time_str or INTERMITTENT_DEFAULTS["start_time"]

    # 1. 加载数据 (对应 test-20260126-2.py 生成的文件)
    try:
        df_ref = pd.read_csv(DATA_DIR / "intermittent_reference_1hz.csv")
        df_obs = pd.read_csv(DATA_DIR / "intermittent.csv")
    except Exception as e:
        return json.dumps({"error": f"Intermittent data files not found: {str(e)}"})
        
    y_ref = df_ref['value'].values.astype(np.float32)
    t_ref = np.arange(len(y_ref)).astype(np.float32)
    
    y_obs = df_obs['value'].values.astype(np.float32)
    base_time = pd.to_datetime(start_time_str)
    t_obs = (pd.to_datetime(df_obs['timestamp']) - base_time).dt.total_seconds().values.astype(np.float32)
    
    # 2. 执行自适应重建逻辑
    
    # 策略 1: 寻找最佳频谱参考段
    max_f = -1.0
    best_dur_start = 0
    best_dur_end = segments[0]["duration"]
    
    curr_t = 0
    for seg in segments:
        if seg["freq"] > max_f:
            max_f = seg["freq"]
            best_dur_start = curr_t
            best_dur_end = curr_t + seg["duration"]
        curr_t += seg["duration"]
        
    ref_mask = (t_obs >= best_dur_start) & (t_obs < best_dur_end)
    if not np.any(ref_mask) or np.sum(ref_mask) < 2:
        engine_guided = SignalReconstructor(y_obs, t_obs) 
    else:
        engine_guided = SignalReconstructor(y_obs[ref_mask], t_obs[ref_mask])
    
    # 对比方法
    engine_base = SignalReconstructor()
    y_linear = engine_base.linear_reconstruct(t_obs, y_obs, t_ref)
    y_cubic = engine_base.cubic_reconstruct(t_obs, y_obs, t_ref)
    
    y_guided = np.zeros_like(t_ref)
    curr_t = 0
    total_duration = t_ref[-1] - t_ref[0]
    
    for seg in segments:
        dur, freq = seg["duration"], seg["freq"]
        end_t = curr_t + dur
        
        # 目标范围
        mask_t_ref = (t_ref >= curr_t) & (t_ref < end_t)
        if not np.any(mask_t_ref): continue
        t_target_seg = t_ref[mask_t_ref]
        
        # 策略 2: 自适应宽窗观测 (覆盖空洞边界)
        margin = max(60.0, total_duration * 0.15)
        mask_t_obs = (t_obs >= curr_t - margin) & (t_obs <= end_t + margin)
        
        if np.sum(mask_t_obs) < 2: mask_t_obs = np.ones(len(y_obs), dtype=bool)

        if freq >= 1.0:
            y_guided[mask_t_ref] = engine_guided.linear_reconstruct(t_obs[mask_t_obs], y_obs[mask_t_obs], t_target_seg)
        else:
            y_guided[mask_t_ref] = engine_guided.guided_spectral_reconstruct(t_obs[mask_t_obs], y_obs[mask_t_obs], t_target_seg)
        curr_t = end_t

    # 3. 构造返回结构
    methods_map = {"Linear": y_linear, "Cubic": y_cubic, "Guided": y_guided}
    results = {}
    
    for name, y_rec in methods_map.items():
        metrics = metrics_compute(y_ref, y_rec, fs_ds=None, fs_ori=1.0)
        results[name] = {
            "reference": {"time": t_ref, "value": y_ref},
            "observation": {"time": t_obs, "value": y_obs},
            "reconstruction": {"time": t_ref, "value": y_rec},
            "metrics": {
                "RMSE": float(np.sqrt(np.mean((y_ref - y_rec)**2))),
                "DTW": float(metrics['dtw_time'])
            }
        }
        
    return json_serialize_with_ndarray(results)

# endregion

if __name__ == "__main__":
    # print("=" * 60)
    # print("测试0: 8Hz真实数据低采样率重建验证")
    # print("=" * 60)
    # res_json_8hz = test_real_data_8hz_low_sampling(pct=1.0, do_compensation=True, plot=False)
    # plot_8hz_low_sampling_results(res_json_8hz, pct=0.30, save=True, save_dir='figs/8Hz')
    
    # print("\n" + "=" * 60)
    # print("测试1: 1Hz真实数据验证")
    # print("=" * 60)
    # res_json_1hz = test_real_data_1hz(plot=False)
    # # print(f"==>> res_json_1hz: {res_json_1hz}")
    # plot_1hz_results(res_json_1hz, pct=0.30, method="freq", save=True, save_dir='figs/1Hz')
    
    # print("\n" + "=" * 60)
    # print("测试2: 20Hz真实数据验证")
    # print("=" * 60)
    # res_json_20hz_1 = get_random_sampling_res(group=4)
    # plot_align_results(res_json_20hz_1)
    
    print("\n" + "=" * 60)
    print("测试6: 时快时慢数据重建接口 (新)")
    print("=" * 60)
    res_json_fs = get_fast_slow_reconstruction_res()
    # 打印简要指标验证
    res_dict = json.loads(res_json_fs)
    for method in res_dict:
        m = res_dict[method]['metrics']
        print(f"[{method}] RMSE: {m['RMSE']:.4f}, DTW: {m['DTW']:.2f}")

    print("\n" + "=" * 60)
    print("测试7: 时有时无数据重建接口（带大空洞）")
    print("=" * 60)
    res_json_inter = get_intermittent_reconstruction_res()
    res_dict_inter = json.loads(res_json_inter)
    for method in res_dict_inter:
        m = res_dict_inter[method]['metrics']
        print(f"[{method}] RMSE: {m['RMSE']:.4f}, DTW: {m['DTW']:.2f}")

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)
