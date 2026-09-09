import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import strategy3.utils as utils
from .model import SOM


def train_som_model(
    data_df,
    cmg_target_cols,
    cmg_type: str,
    save_path=None,
    window=64,
    step=32,
    grid_size=(5, 5),  # SOM缃戞牸澶у皬
    iterations=1000,  # SOM璁粌杩唬娆℃暟
    learning_rate=0.5,  # SOM瀛︿範鐜?
    sigma=1.0,  # SOM閭诲煙鍑芥暟鍒濆瀹藉害
    random_state=42,  # 闅忔満鏁扮瀛?
):
    """
    璁粌SOM妯″瀷骞朵繚瀛樻ā鍨?
    data_df: 鏁版嵁DataFrame
    save_path: 妯″瀷淇濆瓨璺緞
    cmg_target_cols: 鐩爣鍒楀悕鏄犲皠
    cmg_type: PHM绫诲瀷
    鍏跺畠鍙傛暟鍚岃缁冩祦绋?
    """
    data_df, target_cols = utils.add_low_i_rms(data_df, cmg_target_cols=cmg_target_cols)
    # 鍘熷鏁版嵁褰掍竴鍖栧櫒
    scalers = utils.train_scalers(
        data_df, target_cols, save_path=BASE_DIR / "strategy3" / "scalers" / cmg_type / "scalers.pkl"
    )

    # 鍘熷鏁版嵁鍒嗙獥
    normal_data = data_df[target_cols].values
    normal_data_windows = utils.create_windows(normal_data, window_size=window, step=step)

    # SVD鎻愬彇鐗瑰緛
    svd_features = []
    for nd in tqdm(normal_data_windows, desc="SVD鐗瑰緛鎻愬彇"):
        svd_features.append(utils.svd_feature_extract(nd, target_cols, scalers))
    svd_features_array = np.vstack(svd_features)

    # SVD鐗瑰緛褰掍竴鍖?
    svd_scaler = utils.train_svd_scaler(
        svd_features_array, save_path=BASE_DIR / "strategy3" / "scalers" / cmg_type / "svd_scaler.pkl"
    )
    train_data = svd_scaler.transform(svd_features_array)

    # 璁粌SOM妯″瀷
    print(f"寮€濮嬭缁僑OM妯″瀷锛岀綉鏍煎ぇ灏忥細{grid_size}锛岃凯浠ｆ鏁帮細{iterations}")
    input_dim = train_data.shape[1]
    som_model = SOM(
        grid_size=grid_size,
        input_dim=input_dim,
        learning_rate=learning_rate,
        sigma=sigma,
        random_state=random_state,
    )
    som_model.fit(train_data, iterations=iterations)

    # 淇濆瓨妯″瀷
    if save_path is None:
        save_path = BASE_DIR / "strategy3" / "models" / cmg_type / "som_model.pkl"
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(som_model, f)
    print(f"妯″瀷宸蹭繚瀛樺埌: {save_path}")

    # 杈撳嚭涓€浜汼OM妯″瀷鐨勫叧閿俊鎭?
    print(f"SOM妯″瀷璁粌瀹屾垚锛屾甯告牱鏈殑鏈€澶ч┈姘忚窛绂婚槇鍊? {som_model.max_mahalanobis_dist:.6f}")
    print(f"SOM绁炵粡鍏冩縺娲绘儏鍐? {som_model.neuron_activations}")

    return som_model


if __name__ == "__main__":
    print(f"==>> BASE_DIR: {BASE_DIR}")
    cmg_type = "500NM"
    csvs = [BASE_DIR / "鏁版嵁澶勭悊" / cmg_type / "data.csv"]
    import chardet

    encodings = []
    for csv in csvs:
        with open(csv, "rb") as f:
            result = chardet.detect(f.readline())
            print(result)
            encodings.append(result["encoding"])
    print(encodings)
    dfs = [pd.read_csv(csv, encoding=enc) for csv, enc in zip(csvs, encodings)]
    data_df = pd.concat(dfs, ignore_index=True)

    cmg_target_cols = utils.PHM_TYPE_COL_NAME_MAP.get(cmg_type, None)
    if cmg_target_cols is None:
        raise ValueError(f"鏈煡鐨刢mg_type: {cmg_type}锛屾棤娉曡幏鍙栧搴旂殑鍒楀悕锛岃妫€鏌ワ紒")

    # 璁粌SOM妯″瀷
    train_som_model(
        data_df,
        cmg_target_cols=cmg_target_cols,
        cmg_type=cmg_type,
        grid_size=(5, 5),  # 5x5缃戞牸锛屽嵆25涓缁忓厓
        iterations=1000,  # SOM璁粌杩唬娆℃暟
        learning_rate=0.5,  # 瀛︿範鐜?
        sigma=1.0,  # 閭诲煙鍑芥暟瀹藉害
        random_state=42,  # 闅忔満鏁扮瀛?
    )

