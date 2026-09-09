import json
import pickle
from pathlib import Path

import numpy as np
from reconstruct import reconstruct_rearranged_signal
from scipy.fftpack import fft, ifft
from scipy.spatial.distance import cosine

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


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


# 表9-随机采样
def get_random_sampling_res(group: int = 1):
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


# 表9-欠采样
def get_low_sampling_res(group: int = 1):
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
                "title": "原始信号",
            },
            "y2": {
                "value": final_reconstructed_signal[np.where((t > 5) & (t < 8))],
                "title": "重建信号",
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
