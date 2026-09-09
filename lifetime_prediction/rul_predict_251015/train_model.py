import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler

from model import AutoEncoder, train_ae
from utils import (
    PHM_TYPE_COL_NAME_MAP,
    I_LOW_RMS_NAME,
    add_low_i_rms,
    create_windows,
    get_device,
    svd_feature_extract,
    train_scalers,
    train_sigma_scaler,
)

BASE_DIR = Path(__file__).resolve().parent


def train_autoencoder(
    data_df,
    cmg_target_cols,
    cmg_type: str,
    save_path=None,
    window=64,
    step=32,
    epochs=500,
    batch_size=16,
    lr=1e-3,
    device=None,
):
    """
    璁粌鑷紪鐮佸櫒骞朵繚瀛樻ā鍨?
    data_df: 鏁版嵁DataFrame
    save_path: 妯″瀷淇濆瓨璺緞
    target_cols: 鐩爣鍒楀悕
    鍏跺畠鍙傛暟鍚岃缁冩祦绋?
    """
    data_df, target_cols = add_low_i_rms(data_df, cmg_target_cols=cmg_target_cols)
    # 鍘熷鏁版嵁褰掍竴鍖栧櫒
    scalers = train_scalers(data_df, target_cols, save_path=BASE_DIR / "scalers" / cmg_type / "scalers.pkl")

    # 鍘熷鏁版嵁鍒嗙獥
    normal_data = data_df[target_cols].values
    normal_data_windows = create_windows(normal_data, window_size=window, step=step)

    # SVD鎻愬彇鐗瑰緛
    svd_features = []
    for nd in normal_data_windows:
        svd_features.append(svd_feature_extract(nd, target_cols, scalers))
    svd_features_array = np.vstack(svd_features, dtype=np.float32)

    # 鐗瑰緛褰掍竴鍖?
    sigma_scaler = train_sigma_scaler(
        svd_features_array, save_path=BASE_DIR / "scalers" / cmg_type / "sigma_scaler.pkl"
    )
    train_data = sigma_scaler.transform(svd_features_array)
    # ------------
    # import matplotlib.pyplot as plt

    # plt.figure()
    # plt.plot(train_data[:, 0], label="Feature 1")
    # plt.plot(train_data[:, 1], label="Feature 2")
    # plt.plot(train_data[:, 2], label="Feature 3")
    # plt.legend()
    # plt.show()
    # breakpoint()
    # ------------
    input_dim = train_data.shape[1]
    ae = AutoEncoder(input_dim=input_dim)
    if device is None:
        device = get_device()
    print(f"浣跨敤璁惧: {device}")
    train_tensor = torch.tensor(train_data, dtype=torch.float32, device=device)
    ae = train_ae(ae, train_tensor, epochs=epochs, batch_size=batch_size, lr=lr, device=device)

    with torch.no_grad():
        # 閲嶅缓杈撳嚭鍜岀紪鐮佽〃绀?
        reconstructed, encoded = ae(train_tensor)
        # 閲嶅缓璇樊
        recon_error = torch.sqrt(torch.mean((train_tensor - reconstructed) ** 2, dim=1)).cpu().numpy()
    min_idx = np.argmin(recon_error)
    base_code = encoded[min_idx].cpu().numpy().reshape(1, -1)  # 鍩哄噯缂栫爜琛ㄧず
    # 閲嶅缓璇樊鐨勫潎鍊煎拰鏍囧噯宸€佷腑浣嶆暟鍜孧AD
    recon_error_mean = np.mean(recon_error)
    recon_error_std = np.std(recon_error)
    recon_error_median = np.median(recon_error)
    recon_error_mad = np.median(np.abs(recon_error - recon_error_median)) + 1e-9  # 闃叉闄ら浂
    print(
        f"閲嶅缓璇樊: 鍧囧€?{recon_error_mean:.6f}, 鏍囧噯宸?{recon_error_std:.6f}, 涓綅鏁?{recon_error_median:.6f}, MAD {recon_error_mad:.6f}"
    )

    ae.to("cpu")  # 鏀惧埌CPU涓婁娇寰楁棤GPU鏈哄櫒涔熻兘鍔犺浇妯″瀷
    state_dict = ae.state_dict()
    if save_path is None:
        save_path = BASE_DIR / "models" / cmg_type / "ae_model.pkl"
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(
            {
                "state_dict": state_dict,
                "base_code": base_code,
                "recon_error_mean": recon_error_mean,
                "recon_error_std": recon_error_std,
                "recon_error_median": recon_error_median,
                "recon_error_mad": recon_error_mad,
            },
            f,
        )
    print(f"妯″瀷宸蹭繚瀛樺埌: {save_path}")
    return ae


if __name__ == "__main__":
    print(f"==>> BASE_DIR: {BASE_DIR}")
    cmg_type = "500NMS"
    csvs = [BASE_DIR / "鏁版嵁澶勭悊" / cmg_type / "data.csv"]
    import chardet
    encodings = []
    for csv in csvs:
        with open(csv, 'rb') as f:
            result = chardet.detect(f.readline())
            print(result)
            encodings.append(result['encoding'])
    print(encodings)
    dfs = [pd.read_csv(csv, encoding=enc) for csv, enc in zip(csvs, encodings)]
    data_df = pd.concat(dfs, ignore_index=True)

    cmg_target_cols = PHM_TYPE_COL_NAME_MAP.get(cmg_type, None)
    if cmg_target_cols is None:
        raise ValueError(f"鏈煡鐨刢mg_type: {cmg_type}锛屾棤娉曡幏鍙栧搴旂殑鍒楀悕锛岃妫€鏌ワ紒")
    train_autoencoder(
        data_df,
        cmg_target_cols=cmg_target_cols,
        cmg_type=cmg_type,
        epochs=20,
        batch_size=64,
    )

    # 绀轰緥锛氬鎸囧畾鏁版嵁鏂囦欢鍜屾ā鍨嬭繘琛屾祴璇?
    # test_autoencoder_on_file(
    #     csv_path=BASE_DIR / "鏁版嵁澶勭悊" / "merged_data_8鍙傛暟_full_0-1.csv",
    #     model_path=BASE_DIR / "models" / "ae_model.pkl",
    #     target_cols=target_cols,
    # )

