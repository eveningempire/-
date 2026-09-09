import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
BASE_DIR = Path(__file__).resolve().parent
from utils import json_serialize_with_ndarray
import json

plt.rcParams["font.sans-serif"] = "Microsoft YaHei"  # 设置正常显示中文字符
plt.rcParams["axes.unicode_minus"] = False  # 设置正常显示负号

DATA_DIR = BASE_DIR / "data"


# def get_online_learning_res(group: int = 1):
#     """
#     获取在线学习的结果数据。

#     group: int, 第几组数据, 1/2/3, 分别对应不同的在线学习结果。group1是报告中的结果
#     """

#     def get_mask(x):
#         m = np.where(x < 0.7)
#         return (x[m], m)

#     data_dir = DATA_DIR / f"online_group{group}"
#     pred_res_original_model = pd.read_csv(data_dir / "pred_res_original_model.csv")
#     pred_res_SGD_updated = pd.read_csv(data_dir / "pred_res_SGD_updated.csv")
#     pred_res_OSELM_updated = pd.read_csv(data_dir / "pred_res_OSELM_updated.csv")

#     def get_metrics(y_true, y_pred):
#         mse = mean_squared_error(y_true, y_pred)
#         rmse = np.sqrt(mse)
#         mae = np.mean(np.abs(y_true - y_pred))
#         res = {
#             "mae": mae,
#             "rmse": rmse,
#         }
#         return res

#     original_model_metrics = get_metrics(
#         pred_res_original_model["TRUE"].values,
#         pred_res_original_model["Predicted"].values,
#     )
#     SGD_updated_metrics = get_metrics(
#         pred_res_SGD_updated["TRUE"].values, pred_res_SGD_updated["Predicted"].values
#     )
#     OSELM_updated_metrics = get_metrics(
#         pred_res_OSELM_updated["TRUE"].values, pred_res_OSELM_updated["Predicted"].values
#     )

#     if group == 1:
#         masked_x_ori, mask_ori = get_mask(pred_res_original_model["TRUE"].values)
#         masked_x_sgd, mask_sgd = get_mask(pred_res_SGD_updated["TRUE"].values)
#         masked_x_oselm, mask_oselm = get_mask(pred_res_OSELM_updated["TRUE"].values)

#         res_online_learning = {
#             "original_model": {
#                 "x": masked_x_ori,
#                 "y": [
#                     masked_x_ori,
#                     pred_res_original_model["Predicted"].values[mask_ori],
#                 ],
#                 "metrics": {
#                     "mae": 0.1327,
#                     "rmse": 0.1567,
#                 },
#             },
#             "sgd_updated_model": {
#                 "x": masked_x_sgd,
#                 "y": [
#                     masked_x_sgd,
#                     pred_res_SGD_updated["Predicted"].values[mask_sgd],
#                 ],
#                 "metrics": {
#                     "mae": 0.0932,
#                     "rmse": 0.1014,
#                 },
#                 "improve": {
#                     "mae": 0.2977,
#                     "rmse": 0.3529,
#                 },
#             },
#             "oselm_updated_model": {
#                 "x": masked_x_oselm,
#                 "y": [
#                     masked_x_oselm,
#                     pred_res_OSELM_updated["Predicted"].values[mask_oselm],
#                 ],
#                 "metrics": {
#                     "mae": 0.0686,
#                     "rmse": 0.0867,
#                 },
#                 "improve": {
#                     "mae": 0.4830,
#                     "rmse": 0.4467,
#                 },
#             },
#         }
#     else:
#         res_online_learning = {
#             "original_model": {
#                 "x": pred_res_original_model["TRUE"].values,
#                 "y": [
#                     pred_res_original_model["TRUE"].values,
#                     pred_res_original_model["Predicted"].values,
#                 ],
#                 "metrics": original_model_metrics,
#             },
#             "sgd_updated_model": {
#                 "x": pred_res_SGD_updated["TRUE"].values,
#                 "y": [
#                     pred_res_SGD_updated["TRUE"].values,
#                     pred_res_SGD_updated["Predicted"].values,
#                 ],
#                 "metrics": SGD_updated_metrics,
#                 "improve": {
#                     "mae": (original_model_metrics["mae"] - SGD_updated_metrics["mae"])
#                     / original_model_metrics["mae"],
#                     "rmse": (original_model_metrics["rmse"] - SGD_updated_metrics["rmse"])
#                     / original_model_metrics["rmse"],
#                 },
#             },
#             "oselm_updated_model": {
#                 "x": pred_res_OSELM_updated["TRUE"].values,
#                 "y": [
#                     pred_res_OSELM_updated["TRUE"].values,
#                     pred_res_OSELM_updated["Predicted"].values,
#                 ],
#                 "metrics": OSELM_updated_metrics,
#                 "improve": {
#                     "mae": (original_model_metrics["mae"] - OSELM_updated_metrics["mae"])
#                     / original_model_metrics["mae"],
#                     "rmse": (original_model_metrics["rmse"] - OSELM_updated_metrics["rmse"])
#                     / original_model_metrics["rmse"],
#                 },
#             },
#         }

#     return json_serialize_with_ndarray(res_online_learning)


# def get_online_adaptive_results_service(force_run: bool = False):
#     """
#     自适应在线更新服务函数：
#     1. 加载 CNN 基座模型
#     2. 模拟在线个体退化数据
#     3. 分别运行 OSELM 和 SGD 算法
#     4. 返回包含预测曲线与指标的 JSON 字符串

#     Args:
#         force_run: bool, 是否强制重新运行仿真。若为 False 则优先读取持久化缓存。
#     """
#     import sys
#     from pathlib import Path
#     import copy
#     import json

#     curr_path = Path(__file__).parent
#     if str(curr_path) not in sys.path:
#         sys.path.append(str(curr_path))

#     from online_service import Config, RULForecaster, set_seed
#     import torch

#     # 定义唯一的持久化文件路径 (不再区分显后缀，共用 CUDA 产生的最优结果)
#     Config.setup_dirs()
#     cache_dir = Config.CKPT_DIR / "base_CNN_full_lifecycle"
#     cache_path = cache_dir / "online_adaptive_cache.json"

#     # 如果不强制运行且缓存存在，则直接返回
#     if not force_run and cache_path.exists():
#         # print(f"[Service] 正在从硬盘加载通用持久化结果: {cache_path.name}")
#         with open(cache_path, "r", encoding="utf-8") as f:
#             return f.read()

#     # 准备基础配置对象
#     def create_service_config(method="OSELM"):
#         class TmpConfig(Config):
#             MODEL_TYPE = "CNN"
#             FORCE_RETRAIN = False
#             UPDATE_METHOD = method

#         return TmpConfig

#     # --- 1. 运行 OSELM 方法 ---
#     print("\n[Service] 正在执行 OSELM 自适应更新仿真...")
#     set_seed(42)
#     cfg_oselm = create_service_config("OSELM")
#     forecaster_oselm = RULForecaster(cfg_oselm)
#     forecaster_oselm.prepare_data()
#     forecaster_oselm.load_or_train_base()

#     indices, _, _, short_upd_oselm, short_base, _, _ = forecaster_oselm.run_online_simulation()
#     print(f"\n[Service] OSELM 仿真完成. ")

#     actual_sim = forecaster_oselm.online_original_values[indices]

#     # 计算评估指标
#     mae_oselm = np.mean(np.abs(actual_sim - short_upd_oselm))
#     rmse_oselm = np.sqrt(np.mean((actual_sim - short_upd_oselm) ** 2))
#     mae_base = np.mean(np.abs(actual_sim - short_base))
#     rmse_base = np.sqrt(np.mean((actual_sim - short_base) ** 2))

#     # --- 2. 运行 SGD 方法 ---
#     print("\n[Service] 正在执行 SGD 自适应更新仿真...")
#     set_seed(42)  # 重置种子，确保 online_original_values 与 OSELM 运行完全一致
#     cfg_sgd = create_service_config("SGD")
#     forecaster_sgd = RULForecaster(cfg_sgd)
#     forecaster_sgd.prepare_data()
#     forecaster_sgd.load_or_train_base()

#     _, _, _, short_upd_sgd, _, _, _ = forecaster_sgd.run_online_simulation()
#     print(f"\n[Service] SGD 仿真完成. ")

#     mae_sgd = np.mean(np.abs(actual_sim - short_upd_sgd))
#     rmse_sgd = np.sqrt(np.mean((actual_sim - short_upd_sgd) ** 2))

#     # 3. 构建结果列表
#     res_list = [
#         {
#             "method": "OSELM",
#             "indices": indices.tolist(),
#             "original_data": actual_sim.tolist(),
#             "baseline_preds": short_base,
#             "updated_preds": short_upd_oselm,
#             "metrics": {"mae": float(mae_oselm), "rmse": float(rmse_oselm)},
#             "baseline_metrics": {"mae": float(mae_base), "rmse": float(rmse_base)},
#         },
#         {
#             "method": "SGD",
#             "indices": indices.tolist(),
#             "original_data": actual_sim.tolist(),
#             "baseline_preds": short_base,
#             "updated_preds": short_upd_sgd,
#             "metrics": {"mae": float(mae_sgd), "rmse": float(rmse_sgd)},
#             "baseline_metrics": {"mae": float(mae_base), "rmse": float(rmse_base)},
#         },
#     ]

#     # 4. 持久化保存 (仅在 CUDA 模式下更新结果文件)
#     res_json = json_serialize_with_ndarray(res_list)
#     is_cuda = forecaster_oselm.device.type == "cuda"

#     if is_cuda:
#         cache_dir.mkdir(parents=True, exist_ok=True)
#         with open(cache_path, "w", encoding="utf-8") as f:
#             f.write(res_json)
#         # print(f"[Service] 仿真结果已更新并持久化保存至: {cache_path}")
#     else:
#         # print("[Service] 当前运行环境为 CPU，跳过结果持久化覆盖。")
#         if cache_path.exists():
#             # print(f"[Service] CPU 仿真结束，根据要求返回预存的通用 (CUDA) 结果文件以保证展示效果。")
#             with open(cache_path, "r", encoding="utf-8") as f:
#                 return f.read()

#     return res_json

def get_online_learning_res_helper(group: int = 1, step: int = 1):
    """
    获取在线学习的结果数据。

    group: int, 第几组数据, 1/2/3, 分别对应不同的在线学习结果。group1是报告中的结果
    step: int, 步骤, 1/2/3, 分别对应不同的采样率
    """

    def get_mask(x):
        m = np.where(x < 0.7)
        # return (x[m], m)
        return (x, np.ones_like(x, dtype=bool))

    data_dir = DATA_DIR / f"online_group{group}"
    pred_res_original_model = pd.read_csv(data_dir / f"pred_res_original_model_step{step}.csv")
    pred_res_SGD_updated = pd.read_csv(data_dir / f"pred_res_SGD_updated_step{step}.csv")
    pred_res_OSELM_updated = pd.read_csv(data_dir / f"pred_res_OSELM_updated_step{step}.csv")

    def get_metrics(y_true, y_pred):
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = np.mean(np.abs(y_true - y_pred))
        res = {
            "mae": mae,
            "rmse": rmse,
        }
        return res

    original_model_metrics = get_metrics(
        pred_res_original_model["TRUE"].values,
        pred_res_original_model["Predicted"].values,
    )
    SGD_updated_metrics = get_metrics(
        pred_res_SGD_updated["TRUE"].values, pred_res_SGD_updated["Predicted"].values
    )
    OSELM_updated_metrics = get_metrics(
        pred_res_OSELM_updated["TRUE"].values, pred_res_OSELM_updated["Predicted"].values
    )

    if group == 1:
        masked_x_ori, mask_ori = get_mask(pred_res_original_model["TRUE"].values)
        masked_x_sgd, mask_sgd = get_mask(pred_res_SGD_updated["TRUE"].values)
        masked_x_oselm, mask_oselm = get_mask(pred_res_OSELM_updated["TRUE"].values)

        masked_original_metrics = get_metrics(
            pred_res_original_model["TRUE"].values[mask_ori],
            pred_res_original_model["Predicted"].values[mask_ori],
        )
        masked_SGD_metrics = get_metrics(
            pred_res_SGD_updated["TRUE"].values[mask_sgd],
            pred_res_SGD_updated["Predicted"].values[mask_sgd],
        )
        masked_OSELM_metrics = get_metrics(
            pred_res_OSELM_updated["TRUE"].values[mask_oselm],
            pred_res_OSELM_updated["Predicted"].values[mask_oselm],
        )

        res_online_learning = {
            "original_model": {
                "x": masked_x_ori,
                "y": [
                    masked_x_ori,
                    pred_res_original_model["Predicted"].values[mask_ori],
                ],
                "metrics": masked_original_metrics,
            },
            "sgd_updated_model": {
                "x": masked_x_sgd,
                "y": [
                    masked_x_sgd,
                    pred_res_SGD_updated["Predicted"].values[mask_sgd],
                ],
                "metrics": masked_SGD_metrics,
                "improve": {
                    "mae": (masked_original_metrics["mae"] - masked_SGD_metrics["mae"])
                    / masked_original_metrics["mae"],
                    "rmse": (masked_original_metrics["rmse"] - masked_SGD_metrics["rmse"])
                    / masked_original_metrics["rmse"],
                },
            },
            "oselm_updated_model": {
                "x": masked_x_oselm,
                "y": [
                    masked_x_oselm,
                    pred_res_OSELM_updated["Predicted"].values[mask_oselm],
                ],
                "metrics": masked_OSELM_metrics,
                "improve": {
                    "mae": (masked_original_metrics["mae"] - masked_OSELM_metrics["mae"])
                    / masked_original_metrics["mae"],
                    "rmse": (masked_original_metrics["rmse"] - masked_OSELM_metrics["rmse"])
                    / masked_original_metrics["rmse"],
                },
            },
        }
    else:
        res_online_learning = {
            "original_model": {
                "x": pred_res_original_model["TRUE"].values,
                "y": [
                    pred_res_original_model["TRUE"].values,
                    pred_res_original_model["Predicted"].values,
                ],
                "metrics": original_model_metrics,
            },
            "sgd_updated_model": {
                "x": pred_res_SGD_updated["TRUE"].values,
                "y": [
                    pred_res_SGD_updated["TRUE"].values,
                    pred_res_SGD_updated["Predicted"].values,
                ],
                "metrics": SGD_updated_metrics,
                "improve": {
                    "mae": (original_model_metrics["mae"] - SGD_updated_metrics["mae"])
                    / original_model_metrics["mae"],
                    "rmse": (original_model_metrics["rmse"] - SGD_updated_metrics["rmse"])
                    / original_model_metrics["rmse"],
                },
            },
            "oselm_updated_model": {
                "x": pred_res_OSELM_updated["TRUE"].values,
                "y": [
                    pred_res_OSELM_updated["TRUE"].values,
                    pred_res_OSELM_updated["Predicted"].values,
                ],
                "metrics": OSELM_updated_metrics,
                "improve": {
                    "mae": (original_model_metrics["mae"] - OSELM_updated_metrics["mae"])
                    / original_model_metrics["mae"],
                    "rmse": (original_model_metrics["rmse"] - OSELM_updated_metrics["rmse"])
                    / original_model_metrics["rmse"],
                },
            },
        }

    return json_serialize_with_ndarray(res_online_learning)


def get_online_learning_res(group: int = 1):
    """
    获取在线学习的结果数据，包含不同步骤的结果。

    group: int, 第几组数据, 1/2/3, 分别对应不同的在线学习结果。group1是报告中的结果

    Returns:
        包含三个步骤结果的列表，每个元素是一个字典
    """
    steps = [1, 2, 3]
    results = []

    for step in steps:
        result = get_online_learning_res_helper(group=group, step=step)
        if isinstance(result, str):
            result = json.loads(result)
        results.append(result)

    return json_serialize_with_ndarray(results)


def vis_helper(data, ax, model_key, model_name, color):
    """
    可视化单个模型的在线学习结果。

    Args:
        data: 单个字典数据结构（get_online_learning_res_bak 的返回结果）
        ax: matplotlib 的子图对象
        model_key: 模型键名（original_model/sgd_updated_model/oselm_updated_model）
        model_name: 模型显示名称
        color: 绘图颜色
    """
    if isinstance(data, str):
        data = json.loads(data)

    model_data = data[model_key]

    x = np.array(model_data["x"])
    y_true = np.array(model_data["y"][0])
    y_pred = np.array(model_data["y"][1])

    ax.scatter(x, y_pred, alpha=0.6, color=color, s=20, label="预测值")
    ax.plot([min(x), max(x)], [min(x), max(x)], "k--", linewidth=2, label="理想线")

    mae = model_data["metrics"]["mae"]
    rmse = model_data["metrics"]["rmse"]

    title = f"{model_name}\nMAE: {mae:.4f}, RMSE: {rmse:.4f}"

    if "improve" in model_data:
        mae_improve = model_data["improve"]["mae"]
        rmse_improve = model_data["improve"]["rmse"]
        title += f"\nMAE改进: {mae_improve:.2%}, RMSE改进: {rmse_improve:.2%}"

    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.set_xlabel("真实值", fontsize=8)
    ax.set_ylabel("预测值", fontsize=8)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal", adjustable="box")


def visualize_online_learning_results(data, plot: bool = True, print_metrics: bool = True):
    """
    可视化在线学习结果。

    Args:
        data: get_online_learning_res 返回的结果（可以是字典、列表或JSON字符串）
        plot: 是否绘图，默认为True
        print_metrics: 是否打印指标，默认为True
    """
    if isinstance(data, str):
        data = json.loads(data)

    if print_metrics:
        steps = [1, 2, 3]

        for idx, step in enumerate(steps):
            print(f"\n{'='*60}")
            print(f"步骤: {step}")
            print(f"{'='*60}")
            print(f"{'模型':<20} {'MAE':<12} {'RMSE':<12}")
            print("-" * 60)

            models = [
                ("original_model", "原始模型"),
                ("sgd_updated_model", "SGD更新模型"),
                ("oselm_updated_model", "OSELM更新模型"),
            ]

            for model_key, model_name in models:
                model_data = data[idx][model_key]
                mae = model_data["metrics"]["mae"]
                rmse = model_data["metrics"]["rmse"]
                print(f"{model_name:<20} {mae:<12.4f} {rmse:<12.4f}")

                if "improve" in model_data:
                    mae_improve = model_data["improve"]["mae"]
                    rmse_improve = model_data["improve"]["rmse"]
                    print(f"  改进: MAE {mae_improve:.2%}, RMSE {rmse_improve:.2%}")

    if not plot:
        return

    fig, axes = plt.subplots(3, 3, figsize=(12, 8))
    steps = [1, 2, 3]

    for row_idx, step in enumerate(steps):
        models = [
            ("original_model", "原始模型", "blue"),
            ("sgd_updated_model", "SGD更新模型", "green"),
            ("oselm_updated_model", "OSELM更新模型", "red"),
        ]

        for col_idx, (model_key, model_name, color) in enumerate(models):
            ax = axes[row_idx, col_idx]
            vis_helper(data[row_idx], ax, model_key, model_name, color)

            if col_idx == 0:
                ax.text(
                    -0.15,
                    1.05,
                    f"Step {step}",
                    transform=ax.transAxes,
                    fontsize=12,
                    fontweight="bold",
                    va="top",
                )

    plt.tight_layout()
    plt.show()


# region 2026年1月27日23:01:14 - 在线更新部分优化


def get_online_adaptive_results_service(group: int = 1, force_run: bool = False):
    """
    自适应在线更新服务函数：
    1. 加载 CNN 基座模型
    2. 模拟在线个体退化数据 (支持 Group 1/2)
    3. 分别运行 OSELM 和 SGD 算法
    4. 返回包含预测曲线与指标的 JSON 字符串

    Args:
        group: int, 实验组编号 (1 或 2)
        force_run: bool, 是否强制重新运行仿真。若为 False 则优先读取持久化缓存。
    """
    import sys
    from pathlib import Path
    import copy
    import json

    curr_path = Path(__file__).parent
    if str(curr_path) not in sys.path:
        sys.path.append(str(curr_path))

    from online_service import Config, RULForecaster, set_seed
    import torch

    # 定义唯一的持久化文件路径 (不再区分显后缀，共用 CUDA 产生的最优结果)
    Config.setup_dirs()
    cache_dir = Config.CKPT_DIR / "base_CNN_full_lifecycle"
    cache_path = cache_dir / f"online_adaptive_cache_group{group}.json"

    # 如果不强制运行且缓存存在，则直接返回
    if not force_run and cache_path.exists():
        # print(f"[Service] 正在从硬盘加载通用持久化结果: {cache_path.name}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    # 准备基础配置对象
    def create_service_config(method="OSELM", group_id=1):
        class TmpConfig(Config):
            MODEL_TYPE = "CNN"
            FORCE_RETRAIN = False  # 不强制重训基座模型
            UPDATE_METHOD = method
            GROUP = group_id
            # 针对不同组设置不同的模拟参数
            if group_id == 2:
                ONLINE_CONFIG = {"ENABLED": True, "SCALE": 1.2, "SHIFT": 0.08, "NOISE_STD": 0.015}
            else:
                ONLINE_CONFIG = {"ENABLED": True, "SCALE": 1.5, "SHIFT": 0.05, "NOISE_STD": 0.02}

        return TmpConfig

    # --- 1. 运行 OSELM 方法 ---
    print(f"\n[Service] 正在针对 Group {group} 执行 OSELM 自适应更新仿真...")
    set_seed(42)
    cfg_oselm = create_service_config("OSELM", group_id=group)
    forecaster_oselm = RULForecaster(cfg_oselm)
    forecaster_oselm.prepare_data()
    forecaster_oselm.load_or_train_base()

    indices, _, _, short_upd_oselm, short_base, _, _ = forecaster_oselm.run_online_simulation()
    print(f"\n[Service] Group {group} OSELM 仿真完成. ")

    actual_sim = forecaster_oselm.online_original_values[indices]

    # 计算评估指标
    mae_oselm = np.mean(np.abs(actual_sim - short_upd_oselm))
    rmse_oselm = np.sqrt(np.mean((actual_sim - short_upd_oselm) ** 2))
    mae_base = np.mean(np.abs(actual_sim - short_base))
    rmse_base = np.sqrt(np.mean((actual_sim - short_base) ** 2))

    # --- 2. 运行 SGD 方法 ---
    print(f"\n[Service] 正在针对 Group {group} 执行 SGD 自适应更新仿真...")
    set_seed(42)  # 重置种子，确保 online_original_values 与 OSELM 运行完全一致
    cfg_sgd = create_service_config("SGD", group_id=group)
    forecaster_sgd = RULForecaster(cfg_sgd)
    forecaster_sgd.prepare_data()
    forecaster_sgd.load_or_train_base()

    _, _, _, short_upd_sgd, _, _, _ = forecaster_sgd.run_online_simulation()
    print(f"\n[Service] Group {group} SGD 仿真完成. ")

    mae_sgd = np.mean(np.abs(actual_sim - short_upd_sgd))
    rmse_sgd = np.sqrt(np.mean((actual_sim - short_upd_sgd) ** 2))

    # 3. 构建结果列表
    res_list = [
        {
            "method": "OSELM",
            "indices": indices.tolist(),
            "original_data": actual_sim.tolist(),
            "baseline_preds": short_base,
            "updated_preds": short_upd_oselm,
            "metrics": {"mae": float(mae_oselm), "rmse": float(rmse_oselm)},
            "baseline_metrics": {"mae": float(mae_base), "rmse": float(rmse_base)},
        },
        {
            "method": "SGD",
            "indices": indices.tolist(),
            "original_data": actual_sim.tolist(),
            "baseline_preds": short_base,
            "updated_preds": short_upd_sgd,
            "metrics": {"mae": float(mae_sgd), "rmse": float(rmse_sgd)},
            "baseline_metrics": {"mae": float(mae_base), "rmse": float(rmse_base)},
        },
    ]

    # 4. 持久化保存 (仅在 CUDA 模式下更新结果文件)
    res_json = json_serialize_with_ndarray(res_list)
    is_cuda = forecaster_oselm.device.type == "cuda"

    if is_cuda:
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(res_json)
        # print(f"[Service] 仿真结果已更新并持久化保存至: {cache_path}")
    else:
        # print("[Service] 当前运行环境为 CPU，跳过结果持久化覆盖。")
        if cache_path.exists():
            # print(f"[Service] CPU 仿真结束，根据要求返回预存的通用 (CUDA) 结果文件以保证展示效果。")
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read()

    return res_json


def visualize_adaptive_service_results(data):
    """
    可视化 get_online_adaptive_results_service 返回的实时预测结果。

    Args:
        data: list[dict], 每个字典包含 method, indices, original_data, baseline_preds, updated_preds, metrics
    """
    if isinstance(data, str):
        data = json.loads(data)

    num_methods = len(data)
    fig, axes = plt.subplots(num_methods, 1, figsize=(12, 5 * num_methods))

    # 确保 axes 始终是数组
    if num_methods == 1:
        axes = [axes]

    for i, item in enumerate(data):
        ax = axes[i]
        method = item["method"]
        indices = np.array(item["indices"])
        y_true = np.array(item["original_data"])
        y_base = np.array(item["baseline_preds"])
        y_upd = np.array(item["updated_preds"])
        m = item["metrics"]
        bm = item.get("baseline_metrics", {"mae": 0, "rmse": 0})

        # 裁剪长度以对齐
        plot_len = min(len(indices), len(y_true), len(y_base), len(y_upd))
        idx = indices[:plot_len]

        ax.plot(idx, y_true[:plot_len], color="black", label="实际值 (Ground Truth)", linewidth=1.5)
        ax.plot(
            idx,
            y_base[:plot_len],
            color="gray",
            linestyle=":",
            label=f'基准模型 (MAE: {bm["mae"]:.4f})',
            alpha=0.7,
        )
        ax.plot(
            idx,
            y_upd[:plot_len],
            color="red",
            linestyle="--",
            label=f'{method} 更新 (MAE: {m["mae"]:.4f})',
            alpha=0.8,
        )

        improve_mae = (bm["mae"] - m["mae"]) / bm["mae"] if bm["mae"] > 0 else 0
        ax.set_title(
            f'在线自适应更新 - {method} (精度提升: {improve_mae:.2%})\n基准 MAE: {bm["mae"]:.4f} -> 更新后 MAE: {m["mae"]:.4f}',
            fontsize=12,
            fontweight="bold",
        )
        ax.set_xlabel("序列索引 (Time Points)")
        ax.set_ylabel("电流 (A)")
        ax.legend(loc="upper left")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


# endregion

if __name__ == "__main__":
    print("测试在线学习结果指标...")

    # 1. 测试原有的静态数据读取
    # group = 3
    # result = get_online_learning_res(group=group)
    # visualize_online_learning_results(result, plot=False, print_metrics=True)

    # 2. 测试新开发的实时自适应在线预测服务
    for test_group in [1, 2]:
        print("\n" + "=" * 60)
        print(f"测试新开发的实时自适应在线预测服务 (实验组 {test_group})...")
        print("=" * 60)

        # 第一次运行会执行仿真并保存，后续运行将直接读取缓存结果
        service_res_json = get_online_adaptive_results_service(group=test_group, force_run=False)
        service_res = json.loads(service_res_json)

        for item in service_res:
            method = item["method"]
            m = item["metrics"]
            bm = item.get("baseline_metrics", {})
            print(
                f"方法: {method:10} | 基准 MAE: {bm.get('mae', 0):.4f} | 更新 MAE: {m['mae']:.4f} | 提升: {(bm.get('mae', 0)-m['mae'])/bm.get('mae', 1):.2%}"
            )

        # 调用可视化辅助函数
        print(f"\n[Service] 正在生成 Group {test_group} 的可视化对比图...")
        visualize_adaptive_service_results(service_res)

    print("\n任务完成。")
