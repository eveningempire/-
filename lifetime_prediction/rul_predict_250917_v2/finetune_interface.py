"""
妯″瀷寰皟鎺ュ彛妯″潡
鎻愪緵AE鍜孷AE妯″瀷鐨勫井璋冨姛鑳斤紝閬垮厤鐩稿瀵煎叆闂
"""
import sys
from pathlib import Path

# 纭繚褰撳墠鐩綍鍦╯ys.path涓?
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# 鍏堝鍏odel妯″潡锛堣繖浜涙ā鍧楁病鏈夌浉瀵瑰鍏ワ級
import model as ae_model
import strategy1.model as vae_model

# 鐒跺悗鎵嬪姩澶勭悊utils鐨勫鍏ワ紝閬垮厤瑙﹀彂鍏剁浉瀵瑰鍏?
import importlib.util
import numpy as np

# 鎵嬪姩鍔犺浇utils妯″潡锛岃烦杩囩浉瀵瑰鍏ラ儴鍒?
def load_utils_functions():
    """鎵嬪姩鍔犺浇utils涓渶瑕佺殑鍑芥暟锛岄伩鍏嶇浉瀵瑰鍏?""
    # 杩欓噷鎴戜滑闇€瑕佷粠utils涓彁鍙栭渶瑕佺殑鍑芥暟
    # 鐢变簬utils鏈夌浉瀵瑰鍏ラ棶棰橈紝鎴戜滑鐩存帴鍦ㄨ繖閲屽疄鐜伴渶瑕佺殑鍔熻兘
    
    # PHM绫诲瀷鏄犲皠
    PHM_TYPE_COL_NAME_MAP = {
        "500NM": ['楂橀€熺數鏈虹數鍘?, '楂橀€熺數鏈虹數娴?, '浣庨€熺數鏈虹數鍘?, '浣庨€熺數鏈虹數娴?, '妗嗘灦鐢垫祦'],
        "500NMS": ['楂橀€熺數鏈虹數鍘?, '楂橀€熺數鏈虹數娴?, '浣庨€熺數鏈虹數鍘?, '浣庨€熺數鏈虹數娴?, '妗嗘灦鐢垫祦'],
        "15NM": ['楂橀€熺數鏈虹數鍘?, '楂橀€熺數鏈虹數娴?, '浣庨€熺數鏈虹數鍘?, '浣庨€熺數鏈虹數娴?, '妗嗘灦鐢垫祦'],
        "15NMS": ['楂橀€熺數鏈虹數鍘?, '楂橀€熺數鏈虹數娴?, '浣庨€熺數鏈虹數鍘?, '浣庨€熺數鏈虹數娴?, '妗嗘灦鐢垫祦'],
    }
    
    I_LOW_RMS_NAME = "浣庨€熺數鏈虹數娴佹湁鏁堝€?
    
    return PHM_TYPE_COL_NAME_MAP, I_LOW_RMS_NAME

PHM_TYPE_COL_NAME_MAP, I_LOW_RMS_NAME = load_utils_functions()

import torch
import pandas as pd
from sklearn.preprocessing import StandardScaler
from datetime import datetime
from scipy.signal import welch


# 宸ュ叿鍑芥暟瀹炵幇
def get_device():
    """鑾峰彇璁＄畻璁惧"""
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def add_low_i_rms(df):
    """娣诲姞浣庨€熺數鏈虹數娴佹湁鏁堝€?""
    if '浣庨€熺數鏈虹數娴? in df.columns and I_LOW_RMS_NAME not in df.columns:
        # 璁＄畻RMS鍊?
        window_size = 50
        df[I_LOW_RMS_NAME] = df['浣庨€熺數鏈虹數娴?].rolling(window=window_size, min_periods=1).apply(
            lambda x: np.sqrt(np.mean(x**2))
        )
    return df


def create_windows(data, window_size=64, step=32):
    """鍒涘缓婊戝姩绐楀彛"""
    windows = []
    for i in range(0, len(data) - window_size + 1, step):
        windows.append(data[i:i+window_size])
    return np.array(windows)


def svd_feature_extract(data, window_size=64, step=32, n_components=3):
    """SVD鐗瑰緛鎻愬彇"""
    windows = create_windows(data, window_size, step)
    
    features = []
    for window in windows:
        # 瀵规瘡涓獥鍙ｈ繘琛孲VD鍒嗚В
        U, S, Vt = np.linalg.svd(window, full_matrices=False)
        # 鍙栧墠n_components涓寮傚€间綔涓虹壒寰?
        feature = S[:n_components] if len(S) >= n_components else np.pad(S, (0, n_components - len(S)))
        features.append(feature)
    
    return np.array(features)


def finetune_ae_model(
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
    alpha=0.7
):
    """
    AE妯″瀷寰皟
    
    Args:
        data_df: 鍖呭惈閬ユ祴鏁版嵁鐨凞ataFrame
        cmg_type: PHM鍨嬪彿
        model_path: 鍘熷妯″瀷璺緞
        save_path: 寰皟鍚庢ā鍨嬩繚瀛樿矾寰?
        window: 鏃堕棿绐楀彛澶у皬
        step: 婊戝姩姝ラ暱
        epochs: 璁粌杞暟
        batch_size: 鎵瑰ぇ灏?
        lr: 瀛︿範鐜?
        device: 璁＄畻璁惧
        alpha: 缁熻铻嶅悎鏉冮噸
        
    Returns:
        寰皟鍚庣殑妯″瀷瀛楀吀
    """
    # 鑾峰彇璁惧
    if device is None:
        device = get_device()
    
    # 鑾峰彇鐩爣鍒?
    cmg_target_cols = PHM_TYPE_COL_NAME_MAP.get(cmg_type.upper())
    if not cmg_target_cols:
        raise ValueError(f"鏈煡鐨凜MG鍨嬪彿: {cmg_type}")
    
    # 鏁版嵁棰勫鐞?
    data_df = add_low_i_rms(data_df)
    target_cols = cmg_target_cols + [I_LOW_RMS_NAME]
    
    # 鍒涘缓婊戝姩绐楀彛
    windows = create_windows(
        data_df[target_cols].values,
        window_size=window,
        step=step
    )
    
    # 鍔犺浇鎴栧垵濮嬪寲妯″瀷
    if model_path and Path(model_path).exists():
        checkpoint = torch.load(model_path, map_location=device)
        model = ae_model.AutoEncoder(
            input_size=len(target_cols),
            window_size=window
        ).to(device)
        model.load_state_dict(checkpoint['model_state_dict'])
        
        # 鍔犺浇鍘熷缁熻淇℃伅
        old_mean = checkpoint.get('mean', 0)
        old_std = checkpoint.get('std', 1)
    else:
        model = ae_model.AutoEncoder(
            input_size=len(target_cols),
            window_size=window
        ).to(device)
        old_mean = 0
        old_std = 1
    
    # 璁粌妯″瀷
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = torch.nn.MSELoss()
    
    # 璁＄畻鏂版暟鎹殑缁熻淇℃伅
    errors = []
    for epoch in range(epochs):
        epoch_loss = 0
        for i in range(0, len(windows), batch_size):
            batch = windows[i:i+batch_size]
            batch_tensor = torch.FloatTensor(batch).to(device)
            
            optimizer.zero_grad()
            output = model(batch_tensor)
            loss = criterion(output, batch_tensor)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
            # 璁板綍閲嶆瀯璇樊
            with torch.no_grad():
                error = torch.mean((output - batch_tensor) ** 2, dim=(1, 2))
                errors.extend(error.cpu().numpy())
    
    # 璁＄畻鏂扮殑缁熻淇℃伅
    new_mean = np.mean(errors)
    new_std = np.std(errors)
    
    # 铻嶅悎缁熻淇℃伅
    fused_mean = alpha * old_mean + (1 - alpha) * new_mean
    fused_std = alpha * old_std + (1 - alpha) * new_std
    
    # 淇濆瓨妯″瀷
    checkpoint = {
        'model_state_dict': model.state_dict(),
        'mean': fused_mean,
        'std': fused_std,
        'window_size': window,
        'input_size': len(target_cols),
        'finetuned': True,
        'finetune_date': datetime.now().strftime('%Y%m%d_%H%M%S')
    }
    
    if save_path:
        torch.save(checkpoint, save_path)
    
    return checkpoint


def finetune_vae_model(
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
    alpha=0.7
):
    """
    VAE妯″瀷寰皟
    
    Args:
        data_df: 鍖呭惈閬ユ祴鏁版嵁鐨凞ataFrame
        cmg_type: PHM鍨嬪彿
        model_path: 鍘熷妯″瀷璺緞
        save_path: 寰皟鍚庢ā鍨嬩繚瀛樿矾寰?
        window: 鏃堕棿绐楀彛澶у皬
        step: 婊戝姩姝ラ暱
        epochs: 璁粌杞暟
        batch_size: 鎵瑰ぇ灏?
        lr: 瀛︿範鐜?
        device: 璁＄畻璁惧
        quantile_level: 鍒嗕綅鏁版按骞?
        alpha: 缁熻铻嶅悎鏉冮噸
        
    Returns:
        寰皟鍚庣殑妯″瀷瀛楀吀
    """
    # 鑾峰彇璁惧
    if device is None:
        device = get_device()
    
    # 鑾峰彇鐩爣鍒?
    cmg_target_cols = PHM_TYPE_COL_NAME_MAP.get(cmg_type.upper())
    if not cmg_target_cols:
        raise ValueError(f"鏈煡鐨凜MG鍨嬪彿: {cmg_type}")
    
    # 鏁版嵁棰勫鐞?
    data_df = add_low_i_rms(data_df)
    target_cols = cmg_target_cols + [I_LOW_RMS_NAME]
    
    # SVD鐗瑰緛鎻愬彇
    data_features = svd_feature_extract(
        data_df[target_cols].values,
        window_size=window,
        step=step,
        n_components=3
    )
    
    # 鍔犺浇鎴栧垵濮嬪寲妯″瀷
    if model_path and Path(model_path).exists():
        checkpoint = torch.load(model_path, map_location=device)
        model = vae_model.VAE(
            input_dim=data_features.shape[1],
            hidden_dim=128,
            latent_dim=32
        ).to(device)
        model.load_state_dict(checkpoint['model_state_dict'])
        
        # 鍔犺浇鍘熷闃堝€?
        old_threshold = checkpoint.get('threshold', 0)
    else:
        model = vae_model.VAE(
            input_dim=data_features.shape[1],
            hidden_dim=128,
            latent_dim=32
        ).to(device)
        old_threshold = 0
    
    # 璁粌妯″瀷
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    # 璁＄畻鏂版暟鎹殑鎹熷け
    combined_errors = []
    for epoch in range(epochs):
        for i in range(0, len(data_features), batch_size):
            batch = data_features[i:i+batch_size]
            batch_tensor = torch.FloatTensor(batch).to(device)
            
            optimizer.zero_grad()
            recon_batch, mu, logvar = model(batch_tensor)
            
            # 璁＄畻閲嶆瀯璇樊鍜孠L鏁ｅ害
            recon_loss = torch.nn.functional.mse_loss(recon_batch, batch_tensor, reduction='none').sum(dim=1)
            kl_div = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp(), dim=1)
            
            loss = (recon_loss + kl_div).mean()
            loss.backward()
            optimizer.step()
            
            # 璁板綍缁勫悎璇樊
            with torch.no_grad():
                combined_error = recon_loss + kl_div
                combined_errors.extend(combined_error.cpu().numpy())
    
    # 璁＄畻鏂扮殑闃堝€?
    new_threshold = np.quantile(combined_errors, quantile_level)
    
    # 铻嶅悎闃堝€?
    fused_threshold = alpha * old_threshold + (1 - alpha) * new_threshold
    
    # 淇濆瓨妯″瀷
    checkpoint = {
        'model_state_dict': model.state_dict(),
        'threshold': fused_threshold,
        'input_dim': data_features.shape[1],
        'hidden_dim': 128,
        'latent_dim': 32,
        'finetuned': True,
        'finetune_date': datetime.now().strftime('%Y%m%d_%H%M%S')
    }
    
    if save_path:
        torch.save(checkpoint, save_path)
    
    return checkpoint


