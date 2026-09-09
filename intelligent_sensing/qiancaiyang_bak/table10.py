import json
import sys
from pathlib import Path

from utils import json_serialize_with_ndarray

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from year1 import get_all_predict_result


# 表10-有限传感信息测试
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
    }

    return json_serialize_with_ndarray(res_limited_sensing)
