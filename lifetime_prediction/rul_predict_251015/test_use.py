from pathlib import Path

import chardet
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import predict_v3 as original_predict
import strategy1.predict_v3 as strategy1_predict
import strategy2.predict_v3 as strategy2_predict
import strategy3.predict_v3 as strategy3_predict
import utils
from strategy1.train_model import train_vae_model
from strategy2.model import IsolationForestModel
from strategy2.train_model import train_isolation_forest_model
from strategy3.model import SOM
from strategy3.train_model import train_som_model
from train_model import train_autoencoder

plt.rcParams["font.sans-serif"] = "Microsoft YaHei"  # 璁剧疆姝ｅ父鏄剧ず涓枃瀛楃
plt.rcParams["axes.unicode_minus"] = False  # 璁剧疆姝ｅ父鏄剧ず璐熷彿

if __name__ == "__main__":
    cmg_type = "2NMS"
    cmg_type_params_map = {
        "2NMS": {"time_start_use": "2020-02-04 20:09:08:000", "time_fmt": "%Y-%m-%d %H:%M:%S:%f"},
        "5NMS": {"time_start_use": "2020-02-04 20:09:08:000", "time_fmt": "%Y-%m-%d %H:%M:%S:%f"},
        "15NMS": {"time_start_use": "2018:02:04 20:09:08", "time_fmt": "%Y:%m:%d %H:%M:%S"},
        "500NMS": {"time_start_use": "2020_10_09_14:53:12", "time_fmt": "%Y_%m_%d_%H:%M:%S"},
    }
    time_start_use = cmg_type_params_map[cmg_type]["time_start_use"]
    time_fmt = cmg_type_params_map[cmg_type]["time_fmt"]
    BASE_DIR = Path(__file__).resolve().parent
    fp = BASE_DIR / "鏁版嵁澶勭悊" / cmg_type / "data.csv"

    with open(fp, "rb") as f:
        result = chardet.detect(f.readline())
        print(result)

    df = pd.read_csv(fp, encoding=result["encoding"])

    cmg_target_cols = utils.PHM_TYPE_COL_NAME_MAP.get(cmg_type, None)
    if cmg_target_cols is None:
        raise ValueError(f"鏈煡鐨刢mg_type: {cmg_type}锛屾棤娉曡幏鍙栧搴旂殑鍒楀悕锛岃妫€鏌ワ紒")

    # 鏄惁閲嶆柊璁粌妯″瀷
    if True:
        print("===>> Training Original model <<===")
        train_autoencoder(
            df,
            cmg_target_cols=cmg_target_cols,
            cmg_type=cmg_type,
            epochs=20,
            batch_size=64,
        )
        print("\n===>> Training Strategy1 model <<===")
        train_vae_model(
            df,
            cmg_target_cols=cmg_target_cols,
            cmg_type=cmg_type,
            epochs=20,
            batch_size=64,
            n_components=3,
            quantile_level=0.95,
        )
        print("\n===>> Training Strategy2 model <<===")
        train_isolation_forest_model(
            df,
            cmg_target_cols=cmg_target_cols,
            cmg_type=cmg_type,
            window_size=64,  # 鍗曚竴绐楀彛澶у皬
            step=32,  # 绐楀彛婊戝姩姝ラ暱
            n_estimators=100,
            quantile_level=0.99,
        )
        print("\n===>> Training Strategy3 model <<===")
        train_som_model(
            df,
            cmg_target_cols=cmg_target_cols,
            cmg_type=cmg_type,
            grid_size=(5, 5),  # 5x5缃戞牸锛屽嵆25涓缁忓厓
            iterations=1000,  # SOM璁粌杩唬娆℃暟
            learning_rate=0.5,  # 瀛︿範鐜?
            sigma=1.0,  # 閭诲煙鍑芥暟瀹藉害
            random_state=42,  # 闅忔満鏁扮瀛?
        )

    plt.figure(figsize=(15, 8))
    print("===>> Original predict_v3.py <<===")
    # !娉ㄦ剰锛屽綋HI鍒濆€煎皬浜庣粓鍊兼椂锛宧i_high鏄笅鐣岋紝hi_low鏄笂鐣?
    rul, hi, hi_high, hi_low = original_predict.Predictor.predict_batch(
        cmg_type=cmg_type,
        time_start_use=time_start_use,
        time_stamps=df["鏃堕棿"],
        design_life=10.0,  # 10骞磋璁″鍛?
        batch_data_df=df,
        time_fmt=time_fmt,  # 璋冩暣鏃堕棿鎴崇殑鏍煎紡锛屾敞鎰忚涓巘ime_start_use鏍煎紡涓€鑷?
    )
    plt.subplot(2, 2, 1)
    plt.plot(np.arange(len(hi)), hi)
    plt.fill_between(np.arange(len(hi)) + len(hi), hi_high, hi_low, alpha=0.3)
    plt.title(f"Original RUL: {rul:.2f} 骞?)

    print("\n===>> Strategy1 predict_v3.py <<===")
    rul, hi, hi_high, hi_low = strategy1_predict.Predictor.predict_batch(
        cmg_type=cmg_type,
        time_start_use=time_start_use,
        time_stamps=df["鏃堕棿"],
        design_life=10.0,  # 10骞磋璁″鍛?
        batch_data_df=df,
        time_fmt=time_fmt,  # 璋冩暣鏃堕棿鎴崇殑鏍煎紡锛屾敞鎰忚涓巘ime_start_use鏍煎紡涓€鑷?
    )
    plt.subplot(2, 2, 2)
    plt.plot(np.arange(len(hi)), hi)
    plt.fill_between(np.arange(len(hi)) + len(hi), hi_high, hi_low, alpha=0.3)
    plt.title(f"Strategy1 RUL: {rul:.2f} 骞?)

    print("\n===>> Strategy2 predict_v3.py <<===")
    rul, hi, hi_high, hi_low = strategy2_predict.Predictor.predict_batch(
        cmg_type=cmg_type,
        time_start_use=time_start_use,
        time_stamps=df["鏃堕棿"],
        design_life=10.0,  # 10骞磋璁″鍛?
        batch_data_df=df,
        time_fmt=time_fmt,  # 璋冩暣鏃堕棿鎴崇殑鏍煎紡锛屾敞鎰忚涓巘ime_start_use鏍煎紡涓€鑷?
    )
    plt.subplot(2, 2, 3)
    plt.plot(np.arange(len(hi)), hi)
    plt.fill_between(np.arange(len(hi)) + len(hi), hi_high, hi_low, alpha=0.3)
    plt.title(f"Strategy2 RUL: {rul:.2f} 骞?)

    print("\n===>> Strategy3 predict_v3.py <<===")
    rul, hi, hi_high, hi_low = strategy3_predict.Predictor.predict_batch(
        cmg_type=cmg_type,
        time_start_use=time_start_use,
        time_stamps=df["鏃堕棿"],
        design_life=10.0,  # 10骞磋璁″鍛?
        batch_data_df=df,
        time_fmt=time_fmt,  # 璋冩暣鏃堕棿鎴崇殑鏍煎紡锛屾敞鎰忚涓巘ime_start_use鏍煎紡涓€鑷?
    )
    plt.subplot(2, 2, 4)
    plt.plot(np.arange(len(hi)), hi)
    plt.fill_between(np.arange(len(hi)) + len(hi), hi_high, hi_low, alpha=0.3)
    plt.title(f"Strategy3 RUL: {rul:.2f} 骞?)

    plt.tight_layout()
    plt.show()

