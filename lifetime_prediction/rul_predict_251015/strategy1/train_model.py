import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import strategy1.utils as utils
from strategy1.model import VAE, train_vae
from strategy1.utils import (
    PHM_TYPE_COL_NAME_MAP,
    add_low_i_rms,
    create_windows,
    get_device,
    svd_feature_extract,
    train_scalers,
    train_sigma_scaler,
)

BASE_DIR = Path(__file__).resolve().parent.parent

def train_vae_model(
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
    n_components=3,
    quantile_level=0.95,
):
    """
    璁粌VAE妯″瀷骞朵繚瀛樻ā鍨?    data_df: 鏁版嵁DataFrame
    save_path: 妯″瀷淇濆瓨璺緞
    cmg_target_cols: 鐩爣鍒楀悕鏄犲皠
    cmg_type: PHM绫诲瀷
    鍏跺畠鍙傛暟鍚岃缁冩祦绋?    """
    data_df, target_cols = add_low_i_rms(data_df, cmg_target_cols=cmg_target_cols)
    # 鍘熷鏁版嵁褰掍竴鍖栧櫒
    scalers = train_scalers(data_df, target_cols, save_path=BASE_DIR / "strategy1" / "scalers" / cmg_type / "scalers.pkl")

    # 鍘熷鏁版嵁鍒嗙獥
    normal_data = data_df[target_cols].values
    normal_data_windows = create_windows(normal_data, window_size=window, step=step)

    # SVD鎻愬彇鐗瑰緛
    svd_features = []
    for nd in tqdm(normal_data_windows, desc="SVD鐗瑰緛鎻愬彇"):
        svd_features.append(svd_feature_extract(nd, target_cols, scalers))
    svd_features_array = np.vstack(svd_features, dtype=np.float32)

    # SVD鐗瑰緛褰掍竴鍖?    svd_scaler = train_sigma_scaler(
        svd_features_array, save_path=BASE_DIR / "strategy1" / "scalers" / cmg_type / "svd_scaler.pkl"
    )
    train_data = svd_scaler.transform(svd_features_array)

    input_dim = train_data.shape[1]
    vae = VAE(input_dim=input_dim)
    if device is None:
        device = get_device()
    print(f"浣跨敤璁惧: {device}")
    train_tensor = torch.tensor(train_data, dtype=torch.float32, device=device)
    vae = train_vae(vae, train_tensor, epochs=epochs, batch_size=batch_size, lr=lr, device=device)

    with torch.no_grad():
        # 閲嶅缓杈撳嚭鍜岀紪鐮佽〃绀?        recon_x, mu, log_var = vae(train_tensor)
        # 璁＄畻缁煎悎璇樊 (閲嶅缓璇樊 + KL鏁ｅ害)
        recon_error_per_sample = torch.mean((train_tensor - recon_x) ** 2, dim=1)
        kld_per_sample = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp(), dim=1)
        combined_error = (recon_error_per_sample + kld_per_sample).cpu().numpy()

    # 璁＄畻鍒嗕綅鏁伴槇鍊?    combined_error_quantile_95 = np.percentile(combined_error, quantile_level * 100)
    print(f"缁煎悎璇樊 {quantile_level*100:.0f}% 鍒嗕綅鏁? {combined_error_quantile_95:.6f}")

    vae.to("cpu")  # 鏀惧埌CPU涓婁娇寰楁棤GPU鏈哄櫒涔熻兘鍔犺浇妯″瀷
    state_dict = vae.state_dict()
    if save_path is None:
        save_path = BASE_DIR / "strategy1" / "models" / cmg_type / "vae_model.pkl"
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(
            {
                "state_dict": state_dict,
                "combined_error_quantile_95": combined_error_quantile_95,
            },
            f,
        )
    print(f"妯″瀷宸蹭繚瀛樺埌: {save_path}")
    return vae


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
    train_vae_model(
        data_df,
        cmg_target_cols=cmg_target_cols,
        cmg_type=cmg_type,
        epochs=20,
        batch_size=64,
        n_components=3,
        quantile_level=0.95,
    )
