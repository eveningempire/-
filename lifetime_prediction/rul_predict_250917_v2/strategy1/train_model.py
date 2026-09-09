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
from .model import VAE, train_vae, vae_loss_function
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

def finetune_model(
    data_df,
    cmg_type: str,
    model_path=None,
    save_path=None,
    window=64,
    step=32,
    epochs=50,
    batch_size=16,
    lr=1e-4,
    device=None,
    quantile_level=0.95,
):
    """
    澧為噺璁粌锛堝井璋冿級宸叉湁鐨刅AE妯″瀷

    鍙傛暟:
        data_df: 鏂版暟鎹瓺ataFrame
        cmg_type: PHM绫诲瀷
        model_path: 宸茶缁冩ā鍨嬬殑璺緞锛屽鏋滀笉鎻愪緵锛屽皢鏍规嵁cmg_type鑷姩鏌ユ壘
        save_path: 寰皟鍚庢ā鍨嬩繚瀛樿矾寰勶紝榛樿涓哄師妯″瀷璺緞
        window: 绐楀彛澶у皬
        step: 姝ラ暱
        epochs: 寰皟璁粌杞暟锛岄€氬父姣斿垵濮嬭缁冨皯
        batch_size: 鎵瑰ぇ灏?        lr: 瀛︿範鐜囷紝閫氬父姣斿垵濮嬭缁冨皬
        device: 璁＄畻璁惧
        quantile_level: 閲忓寲姘村钩锛岀敤浜庣‘瀹氶槇鍊?
    杩斿洖:
        寰皟鍚庣殑妯″瀷
    """
    # 濡傛灉鏈彁渚沵odel_path锛屽垯鏍规嵁cmg_type鑷姩纭畾
    if model_path is None:
        model_path = BASE_DIR / "strategy1" / "models" / cmg_type / "vae_model.pkl"

    # 纭繚model_path鏄疨ath瀵硅薄
    if not isinstance(model_path, Path):
        model_path = Path(model_path)

    # 妫€鏌ユā鍨嬫槸鍚﹀瓨鍦?    if not model_path.exists():
        raise FileNotFoundError(f"鎵句笉鍒版ā鍨嬫枃浠? {model_path}")

    with open(model_path, "rb") as f:
        model_dict = pickle.load(f)

    # 鍑嗗鏂版暟鎹?    cmg_target_cols = PHM_TYPE_COL_NAME_MAP.get(cmg_type, None)
    if cmg_target_cols is None:
        raise ValueError(f"鏈煡鐨刢mg_type: {cmg_type}锛屾棤娉曡幏鍙栧搴旂殑鍒楀悕锛岃妫€鏌ワ紒")
    data_df, target_cols = add_low_i_rms(data_df, cmg_target_cols=cmg_target_cols)

    # 鍔犺浇宸叉湁鐨勬爣鍑嗗寲鍣?    scaler_path = BASE_DIR / "strategy1" / "scalers" / cmg_type / "scalers.pkl"
    with open(scaler_path, "rb") as f:
        scalers = pickle.load(f)

    # 鏁版嵁鍒嗙獥
    normal_data = data_df[target_cols].values
    normal_data_windows = create_windows(normal_data, window_size=window, step=step)

    # SVD鐗瑰緛鎻愬彇
    svd_features = []
    for nd in tqdm(normal_data_windows, desc="SVD鐗瑰緛鎻愬彇"):
        svd_features.append(svd_feature_extract(nd, target_cols, scalers))
    svd_features_array = np.vstack(svd_features, dtype=np.float32)

    # 鐗瑰緛鏍囧噯鍖?    svd_scaler_path = BASE_DIR / "strategy1" / "scalers" / cmg_type / "svd_scaler.pkl"
    with open(svd_scaler_path, "rb") as f:
        svd_scaler = pickle.load(f)

    train_data = svd_scaler.transform(svd_features_array)

    # 閲嶅缓妯″瀷骞跺姞杞戒箣鍓嶇殑鏉冮噸
    input_dim = train_data.shape[1]
    vae = VAE(input_dim=input_dim)
    vae.load_state_dict(model_dict["state_dict"])

    # 寮€濮嬪井璋冭缁?    if device is None:
        device = get_device()
    print(f"浣跨敤璁惧: {device}")
    print(f"寮€濮嬪井璋冭缁冿紝浣跨敤{len(train_data)}涓牱鏈?..")
    train_tensor = torch.tensor(train_data, dtype=torch.float32, device=device)
    vae = train_vae(vae, train_tensor, epochs=epochs, batch_size=batch_size, lr=lr, device=device)

    with torch.no_grad():
        # 閲嶅缓杈撳嚭鍜岀紪鐮佽〃绀?        recon_x, mu, log_var = vae(train_tensor)
        # 璁＄畻缁煎悎璇樊 (閲嶅缓璇樊 + KL鏁ｅ害)
        recon_error_per_sample = torch.mean((train_tensor - recon_x) ** 2, dim=1)
        kld_per_sample = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp(), dim=1)
        combined_error = (recon_error_per_sample + kld_per_sample).cpu().numpy()

    # 璁＄畻鍒嗕綅鏁伴槇鍊?    combined_error_quantile = np.percentile(combined_error, quantile_level * 100)
    print(f"寰皟鍚庣患鍚堣宸?{quantile_level*100:.0f}% 鍒嗕綅鏁? {combined_error_quantile:.6f}")

    # 鍙€夛細鍚堝苟鍘熸湁闃堝€煎拰鏂伴槇鍊?    # 杩欓噷浣跨敤绠€鍗曞姞鏉冨钩鍧囷紝鍙互鏍规嵁闇€瑕佽皟鏁?    if "combined_error_quantile_95" in model_dict:
        alpha = 0.7  # 鍘熸湁鏁版嵁鏉冮噸
        combined_error_quantile = alpha * model_dict["combined_error_quantile_95"] + (1 - alpha) * combined_error_quantile

    # 淇濆瓨妯″瀷锛岄粯璁よ鐩栧師妯″瀷
    if save_path is None:
        save_path = model_path

    if not isinstance(save_path, Path):
        save_path = Path(save_path)

    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)

    vae.to("cpu")  # 鏀惧埌CPU涓婁娇寰楁棤GPU鏈哄櫒涔熻兘鍔犺浇妯″瀷
    state_dict = vae.state_dict()

    with open(save_path, "wb") as f:
        pickle.dump(
            {
                "state_dict": state_dict,
                "combined_error_quantile_95": combined_error_quantile,
                "finetuned": True,  # 鏍囪涓哄凡寰皟妯″瀷
                "finetune_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            f,
        )
    print(f"寰皟鍚庣殑妯″瀷宸蹭繚瀛樺埌: {save_path}")
    return vae


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
    cmg_type = "5000NMS"
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
    
    # 榛樿琛屼负锛氫粠澶村紑濮嬭缁冩ā鍨?    train_vae_model(
        data_df,
        cmg_target_cols=cmg_target_cols,
        cmg_type=cmg_type,
        epochs=20,
        batch_size=64,
        n_components=3,
        quantile_level=0.95,
    )
    
    # 绀轰緥锛氬閲忚缁?寰皟宸叉湁妯″瀷
    # 娉ㄩ噴锛氬疄闄呬娇鐢ㄦ椂锛宒ata_df搴旇鏄柊鏀堕泦鐨勬暟鎹?    # 杩欓噷涓烘紨绀猴紝鎴戜滑浣跨敤鍚屼竴浠芥暟鎹繘琛屽井璋?    model_path = BASE_DIR / "strategy1" / "models" / cmg_type / "vae_model.pkl"
    if model_path.exists():
        print("\n=====================")
        print("寮€濮嬪井璋冨凡鏈夋ā鍨?..")
        print("=====================\n")
        # 寰皟绀轰緥锛氳緝灏戠殑杞暟锛岃緝灏忕殑瀛︿範鐜?        finetune_model(
            data_df,
            cmg_type=cmg_type,
            epochs=10,  # 寰皟杞暟灏戜簬鍒濆璁粌
            batch_size=64,
            lr=5e-5,  # 寰皟瀛︿範鐜囧皬浜庡垵濮嬭缁?            quantile_level=0.95,
        )
        print("\n寰皟瀹屾垚锛?)
