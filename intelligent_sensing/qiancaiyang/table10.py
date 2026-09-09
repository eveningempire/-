import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from utils import json_serialize_with_ndarray

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from ganzhi.year1 import get_all_predict_result


# 表10-有限传感信息测试
# 2026年1月19日15点25分 - 有限传感信息添加RUL预测结果展示
def get_limited_sensing_res(group: int = 1):
    """
    获取有限传感信息测试的结果数据。

    group: int, 第几组数据, 1/2/3, 分别对应不同的有限传感信息测试结果。group1是报告中的结果

    这里复用的year1.table4/5的结果
    """
    assert group in [1, 2, 3], "group参数必须是1/2/3之一。"
    exp = "0" + str(group + 14)  # 实验编号015/016/017
    all_res = json.loads(get_all_predict_result(exp))
    mae_limited = round(all_res["base"]["metrics"]["mae"], 4)
    mae_augmented = round(all_res["fusion_b_k"]["metrics"]["mae"], 4)
    mae_ratio_improve = round((mae_limited - mae_augmented) / mae_limited, 4)
    rmse_limited = round(all_res["base"]["metrics"]["rmse"], 4)
    rmse_augmented = round(all_res["fusion_b_k"]["metrics"]["rmse"], 4)
    rmse_ratio_improve = round((rmse_limited - rmse_augmented) / rmse_limited, 4)

    # 获取隐参数
    mu = all_res["fusion_u_v"]["hps"]["mu"]
    nu = all_res["fusion_u_v"]["hps"]["nu"]

    # 获取 raw_data
    raw_data = all_res["raw_data"]

    res_limited_sensing = {
        "limited_channel_num": 3,  # fixed
        "augmented_channel_num": 5,  # fixed
        "gain_ratio": 0.6667,  # fixed
        "metrics": {
            "mae": {
                "limited": mae_limited,
                "augmented": mae_augmented,
                "ratio_improve": mae_ratio_improve,
            },
            "rmse": {
                "limited": rmse_limited,
                "augmented": rmse_augmented,
                "ratio_improve": rmse_ratio_improve,
            },
        },
        "hps": {  # 只提供mu和nu这一组隐参数
            "mu": mu,
            "nu": nu,
        },
        "raw_data": raw_data,
        "rul_results": {
            "base": {
                "true": all_res["base"]["true_labels"],
                "pred": all_res["base"]["pred_labels"],
            },
            "fusion_u_v": {
                "true": all_res["fusion_u_v"]["true_labels"],
                "pred": all_res["fusion_u_v"]["pred_labels"],
            },
        },
    }

    return json_serialize_with_ndarray(res_limited_sensing)


def plot_limited_sensing_res(res_json):
    """
    对 get_limited_sensing_res 的返回结果进行可视化。
    展示：
    1. 隐参数 mu/nu 变化曲线
    2. MAE/RMSE 指标对比条形图
    3. Base vs Fusion 方法的 RUL 预测效果对比
    """
    res = json.loads(res_json)
    metrics = res["metrics"]
    hps = res["hps"]
    rul_res = res.get("rul_results", {})

    # 提取 mu 和 nu 的值
    mu = np.array(hps["mu"]).flatten()
    nu = np.array(hps["nu"]).flatten()

    fig, axs = plt.subplots(3, 2, figsize=(12, 15))

    # 1. 第一行：绘制 mu 和 nu
    axs[0, 0].plot(mu, label="mu", marker="o", markersize=2, color="blue", alpha=0.6)
    axs[0, 0].set_title("Hyperparameter: mu")
    axs[0, 0].set_ylabel("Value")
    axs[0, 0].legend()
    axs[0, 0].grid(True)

    axs[0, 1].plot(nu, label="nu", marker="s", markersize=2, color="green", alpha=0.6)
    axs[0, 1].set_title("Hyperparameter: nu")
    axs[0, 1].set_ylabel("Value")
    axs[0, 1].legend()
    axs[0, 1].grid(True)

    # 2. 第二行：MAE 和 RMSE 指标对比
    categories = ["Limited (3 Ch)", "Augmented (5 Ch)"]
    mae_values = [metrics["mae"]["limited"], metrics["mae"]["augmented"]]
    axs[1, 0].bar(categories, mae_values, color=["gray", "blue"], alpha=0.7)
    axs[1, 0].set_title(f"MAE Comparison (Improve: {metrics['mae']['ratio_improve']:.2%})")
    axs[1, 0].set_ylabel("MAE Value")

    rmse_values = [metrics["rmse"]["limited"], metrics["rmse"]["augmented"]]
    axs[1, 1].bar(categories, rmse_values, color=["gray", "green"], alpha=0.7)
    axs[1, 1].set_title(f"RMSE Comparison (Improve: {metrics['rmse']['ratio_improve']:.2%})")
    axs[1, 1].set_ylabel("RMSE Value")

    # 3. 第三行：RUL 预测效果对比
    if rul_res:
        # Base (3 Ch)
        base_true = np.array(rul_res["base"]["true"]).flatten()
        base_pred = np.array(rul_res["base"]["pred"]).flatten()
        axs[2, 0].plot(base_true, label="True RUL", color="black", alpha=0.5)
        axs[2, 0].plot(base_pred, label="Base Pred", color="red", linestyle="--")
        axs[2, 0].set_title("RUL Prediction: Base (3 Channels)")
        axs[2, 0].legend()
        axs[2, 0].grid(True, linestyle=":")

        # Fusion (5 Ch)
        fusion_true = np.array(rul_res["fusion_u_v"]["true"]).flatten()
        fusion_pred = np.array(rul_res["fusion_u_v"]["pred"]).flatten()
        axs[2, 1].plot(fusion_true, label="True RUL", color="black", alpha=0.5)
        axs[2, 1].plot(fusion_pred, label="Fusion Pred", color="blue", linestyle="--")
        axs[2, 1].set_title("RUL Prediction: Fusion (5 Channels)")
        axs[2, 1].legend()
        axs[2, 1].grid(True, linestyle=":")

    plt.tight_layout()
    plt.show()


def plot_all_predict_res(res_json):
    """
    对 get_all_predict_result 的返回结果进行可视化，展示多个模型（base, fusion_b_k, fusion_u_v）的真实值与预测值对比图。
    """
    all_res = json.loads(res_json)
    # 动态获取存在的 key，过滤掉非预测结果的 key
    methods = [k for k in all_res.keys() if isinstance(all_res[k], dict) and "true_labels" in all_res[k]]

    fig, axs = plt.subplots(len(methods), 1, figsize=(10, 4 * len(methods)), sharex=True)
    if len(methods) == 1:
        axs = [axs]

    for i, method in enumerate(methods):
        true_labels = np.array(all_res[method]["true_labels"]).flatten()
        pred_labels = np.array(all_res[method]["pred_labels"]).flatten()
        m = all_res[method]["metrics"]

        axs[i].plot(true_labels, label="True Labels", color="black", alpha=0.5, linewidth=2)
        axs[i].plot(pred_labels, label=f"{method} Predictions", color="red", linestyle="--", alpha=0.8)
        axs[i].set_title(f"Method: {method} | MAE: {m.get('mae', 0):.4f}, RMSE: {m.get('rmse', 0):.4f}")
        axs[i].legend()
        axs[i].grid(True, linestyle=":", alpha=0.6)

    plt.xlabel("Sample Point")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # 1. 测试并可视化有限传感信息结果 (table 10 数据)
    print("Plotting limited sensing results...")
    res_limited = get_limited_sensing_res(group=1)
    plot_limited_sensing_res(res_limited)
