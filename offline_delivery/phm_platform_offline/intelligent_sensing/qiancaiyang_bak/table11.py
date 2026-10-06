import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

BASE_DIR = Path(__file__).resolve().parent
from utils import json_serialize_with_ndarray

DATA_DIR = BASE_DIR / "data"


def get_online_learning_res(group: int = 1):
    """
    获取在线学习的结果数据。

    group: int, 第几组数据, 1/2/3, 分别对应不同的在线学习结果。group1是报告中的结果
    """

    def get_mask(x):
        m = np.where(x < 0.7)
        return (x[m], m)

    data_dir = DATA_DIR / f"online_group{group}"
    pred_res_original_model = pd.read_csv(data_dir / "pred_res_original_model.csv")
    pred_res_SGD_updated = pd.read_csv(data_dir / "pred_res_SGD_updated.csv")
    pred_res_OSELM_updated = pd.read_csv(data_dir / "pred_res_OSELM_updated.csv")

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

        res_online_learning = {
            "original_model": {
                "x": masked_x_ori,
                "y": [
                    masked_x_ori,
                    pred_res_original_model["Predicted"].values[mask_ori],
                ],
                "metrics": {
                    "mae": 0.1327,
                    "rmse": 0.1567,
                },
            },
            "sgd_updated_model": {
                "x": masked_x_sgd,
                "y": [
                    masked_x_sgd,
                    pred_res_SGD_updated["Predicted"].values[mask_sgd],
                ],
                "metrics": {
                    "mae": 0.0932,
                    "rmse": 0.1014,
                },
                "improve": {
                    "mae": 0.2977,
                    "rmse": 0.3529,
                },
            },
            "oselm_updated_model": {
                "x": masked_x_oselm,
                "y": [
                    masked_x_oselm,
                    pred_res_OSELM_updated["Predicted"].values[mask_oselm],
                ],
                "metrics": {
                    "mae": 0.0686,
                    "rmse": 0.0867,
                },
                "improve": {
                    "mae": 0.4830,
                    "rmse": 0.4467,
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
