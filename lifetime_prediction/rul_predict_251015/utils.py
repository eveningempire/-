import collections
import pickle
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pywt
import torch
from PyEMD import EMD
from scipy.optimize import minimize
from sklearn.preprocessing import StandardScaler

from model import AutoEncoder, SingleStageWienerModel

plt.rcParams["font.sans-serif"] = "Microsoft YaHei"  # 璁剧疆姝ｅ父鏄剧ず涓枃瀛楃
plt.rcParams["axes.unicode_minus"] = False  # 璁剧疆姝ｅ父鏄剧ず璐熷彿

BASE_DIR = Path(__file__).resolve().parent

I_LOW_RMS_NAME = "浣庨€熺數娴佹湁鏁堝€?
PHM_TYPE_COL_NAME_MAP = {
    "2NMS": {
        "col_names": ["杞瓙鐢垫満鐢垫祦", "妗嗘灦鐢垫満A鐩哥數娴?, "妗嗘灦鐢垫満C鐩哥數娴?],
        "convert_ilow": ["妗嗘灦鐢垫満A鐩哥數娴?, "妗嗘灦鐢垫満C鐩哥數娴?],
    },
    "5NMS": {
        "col_names": ["杞瓙鐢垫満鐢垫祦", "妗嗘灦鐢垫満鐢垫祦"],
        "convert_ilow": [],
    },
    "15NMS": {
        "col_names": ["楂橀€熺數鏈虹數鍘嬫娴?, "楂橀€熺數鏈虹數娴侀仴娴?, "浣庨€熺數鏈虹數娴侀仴娴?],
        "convert_ilow": [],
    },
    "500NMS": {
        "col_names": ["楂橀€熺數鏈虹數鍘?, "楂橀€熺數鏈虹數娴?, "浣庨€烝鐩哥數娴?, "浣庨€烠鐩哥數娴?],
        "convert_ilow": ["浣庨€烝鐩哥數娴?, "浣庨€烠鐩哥數娴?],
    },
}


def get_model_params(cmg_type: str, target_cols: list):
    MODEL_PATH = BASE_DIR / "models" / cmg_type / "ae_model.pkl"
    SCALERS_PATH = BASE_DIR / "scalers" / cmg_type / "scalers.pkl"
    SIGMA_SCALER_PATH = BASE_DIR / "scalers" / cmg_type / "sigma_scaler.pkl"
    # 鍔犺浇褰掍竴鍖栧櫒
    scalers = pickle.load(open(SCALERS_PATH, "rb"))
    sigma_scaler = pickle.load(open(SIGMA_SCALER_PATH, "rb"))
    # 鍔犺浇妯″瀷
    model = AutoEncoder(input_dim=len(target_cols))
    with open(MODEL_PATH, "rb") as f:
        model_pkl = pickle.load(f)
        model.load_state_dict(model_pkl["state_dict"])
        # base_code = model_pkl["base_code"]
        del model_pkl["state_dict"]
    params = {
        "model": model,
        # "base_code": base_code,
        "scalers": scalers,
        "sigma_scaler": sigma_scaler,
        "target_cols": target_cols,
        **model_pkl,
    }
    return params


def y2s(y):
    return y * 365 * 24 * 60 * 60


def s2y(s):
    return s / (365 * 24 * 60 * 60)


def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # return torch.device("cpu")


def create_windows(data, window_size=64, step=1):
    """
    灏嗘暟鎹寜婊戝姩绐楀彛閲嶇粍 shape: [num_windows, window * feature_dim]
    """
    num_samples, feature_dim = data.shape
    windows = []
    for i in range(0, num_samples - window_size + 1, step):
        window = data[i : i + window_size].reshape(-1, feature_dim)
        windows.append(window)
    return windows


def add_low_i_rms(df: pd.DataFrame, cmg_target_cols, i_low_rms_name: str = I_LOW_RMS_NAME):
    """
    杩斿洖娣诲姞浜?浣庨€熺數娴佹湁鏁堝€?鍒楃殑鏂癉ataFrame锛屽師df涓嶅彉銆?
    瑕佹眰df鍖呭惈'浣庨€烝鐩哥數娴?銆?浣庨€烠鐩哥數娴?涓ゅ垪銆?
    """
    target_cols = cmg_target_cols["col_names"]
    convert_ilow = cmg_target_cols.get("convert_ilow", None)
    if not convert_ilow:
        return df, target_cols  # 涓嶉渶瑕佽浆鎹紝鐩存帴杩斿洖鍘熸暟鎹?
    else:
        assert isinstance(convert_ilow, list) and len(convert_ilow) == 2, "convert_ilow搴斾负鍖呭惈涓ゅ垪鍚嶇О鐨勫垪琛?
        assert set(convert_ilow).issubset(set(target_cols)), "convert_ilow涓殑鍒楀繀椤诲寘鍚湪col_names涓?

    if i_low_rms_name in df.columns:
        print(f"鏁版嵁宸插寘鍚?{i_low_rms_name}'鍒楋紝鏃犻渶閲嶅娣诲姞")
        return df, target_cols
    df_copy = df.copy()
    b_phase = -(df_copy[convert_ilow[0]] + df_copy[convert_ilow[1]])
    rms = ((df_copy[convert_ilow[0]] ** 2 + b_phase**2 + df_copy[convert_ilow[1]] ** 2) / 3) ** 0.5
    df_copy[i_low_rms_name] = rms
    target_cols = [n for n in target_cols if n not in convert_ilow] + [
        i_low_rms_name
    ]  # 鐢ㄨ浆鎹㈠悗鐨勬浛鎹㈡帀鍘熸潵鐨勪袱鍒?
    return df_copy, target_cols


def scale_mat_by_scalers(mat, scalers, cols):
    """
    瀵筸at鐨勬瘡涓€鍒楀垎鍒敤瀵瑰簲scaler杩涜褰掍竴鍖?
    鍙傛暟:
        mat: numpy鏁扮粍锛宻hape=(n_samples, n_features)
        scalers: dict锛屾瘡涓壒寰佸悕瀵瑰簲涓€涓猻caler
        cols: list锛岀壒寰佸悕椤哄簭涓巑at鍒楅『搴忎竴鑷?
    杩斿洖:
        scaled_mat: numpy鏁扮粍锛屽綊涓€鍖栧悗鐨勭粨鏋?
    """
    scaled_mat = mat.copy()
    for i, col in enumerate(cols):
        scaled_mat[:, i] = scalers[col].transform(mat[:, i].reshape(-1, 1)).flatten()
    return scaled_mat


def reorder_sigma(sigma, U, VT):
    """
    鏍规嵁涓诲鍒嗛噺閲嶆帓濂囧紓鍊硷紝浣垮叾涓庤緭鍏ョ煩闃电殑鍒楁垨琛岄『搴忓搴?
    鑷姩閫傞厤瀹界煩闃碉紙n_samples < n_features锛夊拰楂樼煩闃碉紙n_samples > n_features锛?
    杩斿洖閲嶆帓鍚庣殑濂囧紓鍊煎拰瀵瑰簲鐨勪富瀵肩储寮?
    """
    # 鍒ゆ柇鏄鐭╅樀杩樻槸楂樼煩闃?
    if VT.shape[0] == sigma.shape[0]:
        # 瀹界煩闃碉紝涓诲鍒嗛噺鏉ヨ嚜VT锛堟瘡涓寮傚€煎搴斾竴鍒楋級
        main_param_indices = [np.argmax(np.abs(vec)) for vec in VT]
    else:
        # 楂樼煩闃碉紝涓诲鍒嗛噺鏉ヨ嚜U锛堟瘡涓寮傚€煎搴斾竴琛岋級
        main_param_indices = [np.argmax(np.abs(vec)) for vec in U]
    sorted_indices = np.argsort(main_param_indices)
    reordered_sigma = sigma[sorted_indices]
    reordered_main_param_indices = np.array(main_param_indices)[sorted_indices]
    return reordered_sigma, reordered_main_param_indices


def train_scalers(df, target_cols, save_path=None):
    """璁粌鏁版嵁缂╂斁鍣?""
    scalers = {}
    for col in target_cols:
        scaler = StandardScaler()
        data = df[col].values.reshape(-1, 1)
        scaler.fit(data)
        scalers[col] = scaler
        print(f"{col} scaler鍧囧€? {scaler.mean_[0]:.4f}, 鏂瑰樊: {scaler.var_[0]:.4f}")
    if save_path is None:
        save_path = BASE_DIR / "scalers" / f"scalers_{time.strftime('%Y%m%d_%H%M%S')}.pkl"
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(scalers, f)
    print(f"鏁版嵁褰掍竴鍖栧櫒宸蹭繚瀛樺埌: {save_path}")
    return scalers


def train_sigma_scaler(svd_features_array, save_path=None):
    """璁粌濂囧紓鍊肩缉鏀惧櫒"""
    scaler = StandardScaler()
    scaler.fit(svd_features_array)
    if save_path is None:
        save_path = BASE_DIR / "scalers" / f"sigma_scaler_{time.strftime('%Y%m%d_%H%M%S')}.pkl"
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"鐗瑰緛褰掍竴鍖栧櫒宸蹭繚瀛樺埌: {save_path}")
    return scaler


# FIXME
def svd_feature_extract(mat, target_cols, scalers, sigma_scaler=None):
    """SVD鍒嗚В鎻愬彇鐗瑰緛"""
    mat_scaled = scale_mat_by_scalers(mat, scalers, target_cols)
    U, sigma, VT = np.linalg.svd(mat_scaled)
    sigma, _ = reorder_sigma(sigma, U, VT)
    sigma_arr = np.array(sigma, dtype=np.float32)
    if sigma_scaler is not None:
        sigma_arr = sigma_scaler.transform(sigma_arr.reshape(1, -1)).flatten()
    return sigma_arr


def calculate_weights(data, method="linear", wmin=0.0, wmax=1.0, inv=False):
    """
    涓?-1鍖洪棿鐨勬暟鎹垎閰嶆潈閲嶏紝闈犺繎0鐨勬暟鍊兼潈閲嶆洿澶?

    :param data: 0-1鍖洪棿鍐呯殑鏁版嵁锛堝垪琛ㄦ垨鏁扮粍锛?
    :param method: 鏉冮噸璁＄畻鏂规硶
                   'linear'锛氱嚎鎬ф潈閲嶏紙1 - x锛?
                   'square'锛氬钩鏂规潈閲嶏紙(1 - x)^2锛?
                   'exponential'锛氭寚鏁版潈閲嶏紙e^(1 - x) - e^0锛屽綊涓€鍖栵級
    :wmin: 鏉冮噸鏈€灏忓€?
    :wmax: 鏉冮噸鏈€澶у€?
    :inv: 鏄惁鍙嶈浆鏉冮噸(鍙嶈浆鎴愰潬杩?鐨勬暟鍊兼潈閲嶆洿灏?
    :return: 涓庤緭鍏ユ暟鎹搴旂殑鏉冮噸鍒楄〃
    """
    data = np.array(data)

    # 纭繚鏁版嵁鍦?-1鍖洪棿鍐?
    if np.any((data < 0) | (data > 1)):
        raise ValueError("杈撳叆鏁版嵁蹇呴』鍦?-1鍖洪棿鍐?)

    if method == "linear":
        # 绾挎€ф潈閲嶏細1 - x锛?瀵瑰簲鏉冮噸1锛?瀵瑰簲鏉冮噸0
        weights = 1 - data

    elif method == "square":
        # 骞虫柟鏉冮噸锛?1 - x)^2锛岄潪绾挎€у寮洪潬杩?鐨勬潈閲?
        weights = (1 - data) ** 2

    elif method == "exponential":
        # 鎸囨暟鏉冮噸锛氭寚鏁板寮洪潬杩?鐨勬潈閲?
        weights = np.exp(1 - data) - np.exp(0)  # 纭繚0鐐规潈閲嶄负0
        weights = weights / (np.max(weights) + 1e-8)  # 褰掍竴鍖栧埌0-1鑼冨洿锛岄伩鍏嶉櫎闆堕敊璇?

    else:
        raise ValueError("涓嶆敮鎸佺殑鏉冮噸璁＄畻鏂规硶锛岃閫夋嫨'linear'銆?square'鎴?exponential'")
    if inv:
        weights = 1 - weights
    weights = wmin + weights * (wmax - wmin)
    return weights


def ema(x, px, alpha):
    return alpha * x + (1 - alpha) * px


def ema_batch(x, alpha):
    res = []
    for i in range(len(x)):
        if i == 0:
            res.append(x[i])
        else:
            res.append(ema(x[i], res[i - 1], alpha))
    return res


def euclidean_distance(x, y):
    """璁＄畻娆у紡璺濈锛歀2鑼冩暟"""
    return np.linalg.norm(x - y) + 1e-8  # 閬垮厤闄ら浂


def manhattan_distance(x, y):
    """璁＄畻鏇煎搱椤胯窛绂伙細L1鑼冩暟"""
    return np.linalg.norm(x - y, ord=1) + 1e-8  # 閬垮厤闄ら浂


def chebyshev_distance(x, y):
    """璁＄畻鍒囨瘮闆か璺濈锛氭棤绌疯寖鏁?""
    return np.linalg.norm(x - y, ord=np.inf) + 1e-8  # 閬垮厤闄ら浂


def cosine_distance(x, y):
    """璁＄畻浣欏鸡璺濈锛?鍑忓幓浣欏鸡鐩镐技搴?""
    cosine_similarity = np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y))
    return 1 - cosine_similarity + 1e-8


def mahalanobis_distance(x, y, cov_matrix=None):
    """
    璁＄畻椹皬璺濈

    鍙傛暟:
    x, y: 涓や釜鍚戦噺
    cov_matrix: 鍗忔柟宸煩闃碉紝鑻ヤ负None鍒欒嚜鍔ㄨ绠?
    """
    # 灏嗗悜閲忚浆鎹负鍒楀悜閲?
    x = np.asarray(x).reshape(-1, 1)
    y = np.asarray(y).reshape(-1, 1)

    # 璁＄畻宸€?
    delta = x - y

    # 鑻ユ湭鎻愪緵鍗忔柟宸煩闃碉紝鍒欏熀浜庤繖涓や釜鍚戦噺鎵€鍦ㄧ殑鏁版嵁闆嗚绠?
    if cov_matrix is None:
        # 杩欓噷鍋囪x鍜寉鏄潵鑷悓涓€鏁版嵁闆嗙殑鏍锋湰锛屽疄闄呭簲鐢ㄤ腑搴斾娇鐢ㄦ暣涓暟鎹泦璁＄畻
        data = np.hstack((x, y)).T
        cov_matrix = np.cov(data)

    # 璁＄畻鍗忔柟宸煩闃电殑閫嗭紙浣跨敤浼€嗗鐞嗗寮傜煩闃碉級
    inv_cov_matrix = np.linalg.pinv(cov_matrix)

    # 椹皬璺濈鍏紡
    distance = np.sqrt(np.dot(np.dot(delta.T, inv_cov_matrix), delta))

    return distance[0, 0]  # 杩斿洖鏍囬噺


def sliding_window_n_sigma(data, window_size=10, n_sigma=3):
    """
    鍩轰簬婊戝姩绐楀彛璁＄畻鏈€鏂版暟鎹偣鐨刵蟽闃堝€硷紝鏇翠晶閲嶈繎鏈熸暟鎹?

    鍙傛暟:
    data: 瀹屾暣鏁版嵁搴忓垪锛堝寘鍚巻鍙插拰鏂版暟鎹級
    window_size: 婊戝姩绐楀彛澶у皬锛堜粎鐢ㄦ渶杩憌indow_size涓暟鎹绠楃粺璁￠噺锛?

    杩斿洖:
    latest_threshold: 鏈€鏂版暟鎹偣瀵瑰簲鐨刵蟽涓婄晫闃堝€?
    """
    n = len(data)
    if n == 0:
        raise ValueError("杈撳叆鏁版嵁涓嶈兘涓虹┖")

    # 纭畾鏈€鏂扮獥鍙ｇ殑璧峰绱㈠紩锛堝彇鏈€杩憌indow_size涓暟鎹級
    start = max(0, n - window_size)
    # 绐楀彛鍖呭惈鏈€鏂扮殑鏁版嵁鐐瑰強涔嬪墠鐨勮繎鏈熸暟鎹?
    window_data = data[start:]

    # 璁＄畻绐楀彛鍐呯殑鍧囧€煎拰鏍囧噯宸紙浠呯敤杩戞湡鏁版嵁锛?
    mu = np.mean(window_data)
    sigma = np.std(window_data)

    # 璁＄畻骞惰繑鍥炴渶鏂扮殑n蟽涓婄晫闃堝€?
    return mu + n_sigma * sigma


def optimize_weights(dist_cos, dist_eu, dist_recon):
    # 灏嗕笁鍒楁寚鏍囧悎鎴愮煩闃礜脳3
    D = np.vstack([dist_cos, dist_eu, dist_recon]).T
    N = D.shape[0]

    # 涓績鍖栧鐞?
    D_centered = D - np.mean(D, axis=0)
    S = np.dot(D_centered.T, D_centered) / (N - 1)  # 鍗忔柟宸煩闃?

    # 鐩爣鍑芥暟锛氬姞鏉冩柟宸?w.T @ S @ w
    def objective(w):
        w_ = [w[0], w[1], (1 - w[0] - w[1])]  # w[2] = 1 - w[0] - w[1]
        return np.dot(w_, S @ w_)

    # 绾︽潫1锛氭潈閲嶅拰涓?
    # cons = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

    # 绾︽潫2锛氭潈閲嶉潪璐?
    bounds = [(0, 1)] * 2

    # 鍒濆鐚滄祴鍧囧垎
    w0 = np.array([1 / 3, 1 / 3])

    # 姹傝В
    res = minimize(
        objective,
        w0,
        bounds=bounds,
        method="L-BFGS-B",
        # constraints=cons,
    )

    if res.success:
        return res.x[0], res.x[1], 1 - res.x[0] - res.x[1]
    else:
        raise ValueError("浼樺寲澶辫触: " + res.message)


def optimize_weights_with_target(dist_cos, dist_eu, dist_recon, v):
    # 鎷兼帴鏁版嵁锛孨脳3鐭╅樀
    D = np.vstack([dist_cos, dist_eu, dist_recon]).T
    N = D.shape[0]

    # 鐩爣鍑芥暟锛氬姞鏉冨拰涓庡畾鍊紇鐨勫潎鏂硅宸?
    def objective(w):
        w_ = [w[0], w[1], (1 - w[0] - w[1])]
        s = D @ w_
        return np.mean((s - v) ** 2)

    # 绾︽潫鏉冮噸鍜屼负1
    # cons = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

    # 鏉冮噸闈炶礋
    bounds = [(0, 1)] * 2

    # 鍒濆鐚滄祴鍧囧垎
    w0 = np.array([1 / 3, 1 / 3])

    res = minimize(
        objective,
        w0,
        bounds=bounds,
        method="L-BFGS-B",
        tol=1e-8,
        # constraints=cons,
    )

    if res.success:
        return res.x[0], res.x[1], 1 - res.x[0] - res.x[1]
    else:
        raise ValueError("浼樺寲澶辫触: " + res.message)


def test_autoencoder_on_file(
    csv_path,
    target_cols,
    scalers,
    sigma_scaler,
    ae,
    window=64,
    step=32,
    device=None,
    norm=None,
):
    """
    瀵规寚瀹氭暟鎹枃浠惰繘琛岃嚜缂栫爜鍣ㄦ祴璇曪紝杈撳嚭閲嶅缓璇樊鍜岀紪鐮佺粨鏋溿€?
    csv_path: 鏁版嵁鏂囦欢璺緞
    model_path: 宸茶缁冩ā鍨媝kl璺緞
    target_cols: 鐩爣鍒楀悕
    """
    # 鍔犺浇鏁版嵁
    data_df = pd.read_csv(csv_path)
    new_df = add_low_i_rms(data_df)
    # 鍒嗙獥
    normal_data = new_df[target_cols].values
    normal_data_windows = create_windows(normal_data, window_size=window, step=step)
    # SVD鐗瑰緛
    svd_features = [svd_feature_extract(nd, target_cols, scalers) for nd in normal_data_windows]
    svd_features_array = np.vstack(svd_features, dtype=np.float32)
    # 鐗瑰緛褰掍竴鍖?
    test_data = sigma_scaler.transform(svd_features_array)
    if device is None:
        device = get_device()
    test_tensor = torch.tensor(test_data, dtype=torch.float32, device=device)
    ae.eval()
    with torch.no_grad():
        reconstructed, encoded = ae(test_tensor)
        if norm is not None:
            reconstructed = norm(reconstructed)
            test_tensor = norm(test_tensor)
        recon_error = torch.mean((test_tensor - reconstructed) ** 2, dim=1).cpu().numpy()
    print(f"閲嶅缓璇樊鍧囧€? {np.mean(recon_error):.6f}")
    print(f"缂栫爜缁撴灉 shape: {encoded.shape}")
    return recon_error, encoded.cpu().numpy()


def rmse(a, b, dim=None):
    return torch.sqrt(torch.mean((a - b) ** 2, dim=dim))


def l2_normalize(x, eps=1e-8):
    """瀵瑰崟涓暟鎹偣杩涜L2褰掍竴鍖栵紙鍗曚綅妯￠暱锛?""
    norm = torch.norm(x) + eps  # 璁＄畻妯￠暱锛屽姞灏忓€奸槻闄ら浂
    return x / norm


def compute_nrmse(input_tensor, recon_tensor, normalization="l2"):
    """
    璁＄畻閲嶅缓璇樊鐨凬RMSE锛堝綊涓€鍖栧潎鏂规牴璇樊锛?

    鍙傛暟:
    input_tensor: 鍘熷杈撳叆寮犻噺锛堝崟涓暟鎹偣锛?
    recon_tensor: 閲嶅缓寮犻噺锛堝崟涓暟鎹偣锛?
    normalization: 褰掍竴鍖栨柟寮?
                   - "range": 鐢ㄨ緭鍏ョ殑鍔ㄦ€佽寖鍥达紙max-min锛夊綊涓€鍖栵紙閫傚悎鏈夋槑纭墿鐞嗘剰涔夌殑鏁版嵁锛?
                   - "std": 鐢ㄨ緭鍏ョ殑鏍囧噯宸綊涓€鍖栵紙閫傚悎缁熻鐗规€хǔ瀹氱殑鏁版嵁锛?
                   - "l2": 鐢ㄨ緭鍏ョ殑L2鑼冩暟褰掍竴鍖栵紙閫傚悎鍏虫敞鍚戦噺闀垮害鐨勫満鏅級
    """
    # 璁＄畻RMSE
    rmse = torch.sqrt(torch.mean((input_tensor - recon_tensor) ** 2))

    # 閬垮厤闄ら浂
    eps = 1e-8

    # 涓嶅悓褰掍竴鍖栨柟寮?
    if normalization == "range":
        # 鐢ㄨ緭鍏ョ殑鍔ㄦ€佽寖鍥达紙max - min锛夊綊涓€鍖?
        data_range = torch.max(input_tensor) - torch.min(input_tensor)
        denominator = data_range + eps
    elif normalization == "std":
        # 鐢ㄨ緭鍏ョ殑鏍囧噯宸綊涓€鍖栵紙闇€娉ㄦ剰鍗曟暟鎹偣鏃舵棤娉曡绠楋紝杩欓噷鐢ㄧ浉閭荤偣浼拌锛?
        # 瀹炴椂鍦烘櫙涓嬪彲缁存姢涓€涓粦鍔ㄧ獥鍙ｈ绠楁爣鍑嗗樊
        denominator = torch.std(input_tensor) + eps
    elif normalization == "l2":
        # 鐢ㄨ緭鍏ョ殑L2鑼冩暟褰掍竴鍖?
        denominator = torch.norm(input_tensor, p=2) + eps
    else:
        raise ValueError("褰掍竴鍖栨柟寮忓繀椤绘槸 'range'銆?std' 鎴?'l2'")

    return (rmse / denominator).item()


def compute_rmse(input_tensor, recon_tensor):
    """
    璁＄畻閲嶅缓璇樊鐨凴MSE锛堝潎鏂规牴璇樊锛?

    鍙傛暟:
    input_tensor: 鍘熷杈撳叆寮犻噺锛堝崟涓暟鎹偣锛?
    recon_tensor: 閲嶅缓寮犻噺锛堝崟涓暟鎹偣锛?
    """
    # 璁＄畻RMSE
    rmse = torch.sqrt(torch.mean((input_tensor - recon_tensor) ** 2))
    return rmse.item() + 1e-8


class AdaptiveKalmanFilter:
    def __init__(self, x0=0.0, P0=1.0, Q0=1e-4, R0=1.0, window_size=50, median_estimate=False):
        self.x_estimate = x0
        self.P = P0
        self.Q = Q0
        self.R = R0
        self.Q0 = Q0
        self.R0 = R0
        self.estimates = []
        self.residuals = collections.deque(maxlen=window_size)
        self.deltas = collections.deque(maxlen=window_size)
        self.window_size = window_size
        self.Q_history = []
        self.R_history = []
        self.median_estimate = median_estimate

    def step(self, z, update=True):
        x_pred = self.x_estimate
        P_pred = self.P + self.Q
        K = P_pred / (P_pred + self.R)
        x_est = x_pred + K * (z - x_pred)
        P_est = (1 - K) * P_pred
        if update:
            self.x_estimate = x_est
            self.P = P_est
            self.estimates.append(x_est)
            # 鏇存柊绐楀彛
            if len(self.estimates) > 1:
                residual = z - x_est
                delta = x_est - self.estimates[-2]
                self.residuals.append(residual)
                self.deltas.append(delta)
                # 鍙湁绐楀彛婊′簡鎵嶇敤绐楀彛鏂瑰樊鏇存柊Q鍜孯锛屽惁鍒欑敤鍒濆鍊?
                if len(self.deltas) == self.window_size:
                    if self.median_estimate:
                        self.Q = np.median(np.abs(self.deltas - np.median(self.deltas))) ** 2
                    else:
                        self.Q = np.var(self.deltas)
                else:
                    self.Q = self.Q0
                if len(self.residuals) == self.window_size:
                    if self.median_estimate:
                        self.R = np.median(np.abs(self.residuals - np.median(self.residuals))) ** 2
                    else:
                        self.R = np.var(self.residuals)
                else:
                    self.R = self.R0
            self.Q_history.append(self.Q)
            self.R_history.append(self.R)
        return x_est, P_est

    def filter(self, observations):
        results = []
        for z in observations:
            x_est, P_est = self.step(z)
            results.append(x_est)
        return results


class AdaptiveKalmanFilter2:
    def __init__(self, x0=0.0, P0=1.0, Q0=1e-4, R0=1.0, window_size=50, median_estimate=False):
        self.x_estimate = x0
        self.P = P0
        self.Q = Q0
        self.R = R0
        self.Q0 = Q0
        self.R0 = R0
        self.estimates = []
        self.residuals = collections.deque(maxlen=window_size)
        self.measurements = collections.deque(maxlen=window_size)
        self.deltas = collections.deque(maxlen=window_size)
        self.window_size = window_size
        self.Q_history = []
        self.R_history = []
        self.Q_max = None
        self.R_fix = None
        self.Q_min = Q0 / 10
        self.Q_max = Q0 * 10
        self.R_min = R0 / 10
        self.R_max = R0 * 10
        self.Q_update_num = 0
        self.R_update_num = 0
        # median_estimate鍙傛暟宸茬Щ闄?

    def step(self, z, update=True):
        # 妫€鏌ヨ娴嬪€兼槸鍚︿负nan
        if np.isnan(z) or np.isinf(z):
            # 璺宠繃璇ユ鎴栫敤涓婁竴姝ヤ及璁?
            return self.x_estimate, self.P
        x_pred = self.x_estimate
        P_pred = self.P + self.Q
        # 闃叉P_pred鎴朢涓鸿礋鎴杗an
        P_pred = np.clip(P_pred, 1e-8, None)
        R_safe = np.clip(self.R, 1e-8, None)
        K = P_pred / (P_pred + R_safe)
        x_est = x_pred + K * (z - x_pred)
        if np.isnan(x_est):
            x_est = self.x_estimate
        P_est = (1 - K) * P_pred
        if update:
            self.x_estimate = x_est
            self.P = P_est
            self.estimates.append(x_est)
            # 鏇存柊绐楀彛
            if len(self.estimates) > 1:
                residual = z - x_est
                delta = x_est - self.estimates[-2]
                self.residuals.append(residual)
                self.deltas.append(delta)
                self.measurements.append(z)
                # 鍙湁绐楀彛婊′簡鎵嶇敤绐楀彛鏂瑰樊鏇存柊Q鍜孯锛屽惁鍒欑敤鍒濆鍊?
                if len(self.deltas) == self.window_size:
                    # Q: 鐢ㄦā鍨嬮娴嬪€间笌瀹為檯鐘舵€佺殑鍋忓樊鐨勬柟宸?
                    # self.Q = np.clip(np.var(self.deltas), self.Q_min, self.Q_max)
                    Q_new = np.var(self.deltas)
                    Q_new = np.clip(Q_new, 1e-6, 1e2)
                    self.Q = 0.9 * self.Q + 0.1 * Q_new
                    self.Q_update_num += 1
                    if self.Q_max is None and self.Q_update_num > self.window_size:
                        self.Q_max = np.max(self.Q_history[self.window_size :] + [self.Q])
                    # if self.Q_max is not None:
                    #     self.Q = min(self.Q, self.Q_max)
                else:
                    self.Q = self.Q0
                if len(self.measurements) == self.window_size:
                    # R: 鐢ㄦ祴閲忓€艰嚜韬殑鏂瑰樊
                    # self.R = np.clip(np.var(self.measurements), self.R_min, self.R_max)
                    R_new = np.var(self.measurements)
                    R_new = np.clip(R_new, 1e-6, 1e2)
                    self.R = 0.9 * self.R + 0.1 * R_new
                    self.R_update_num += 1
                    if self.R_fix is None and self.R_update_num > self.window_size:
                        self.R_fix = np.mean(self.R_history[self.window_size :] + [self.R])
                #     if self.R_fix is not None:
                #         self.R = self.R_fix
                # elif self.R_fix is not None:
                #     self.R = self.R_fix
                else:
                    self.R = self.R0
            self.Q_history.append(self.Q)
            self.R_history.append(self.R)
        return x_est, P_est

    def filter(self, observations):
        results = []
        for z in observations:
            x_est, P_est = self.step(z)
            results.append(x_est)
        return results


def estimate_wiener_params(W, dt=1):
    """
    浠庣淮绾宠繃绋嬫暟鎹腑浼拌mu鍜宻igma
    鍙傛暟:
        W: 缁寸撼杩囩▼鏁版嵁锛坣umpy鏁扮粍锛岄暱搴+1锛?
        dt: 鏃堕棿闂撮殧锛坱[1]-t[0]锛?
    杩斿洖:
        mu_est: 浼拌鐨勬紓绉荤郴鏁?
        sigma_est: 浼拌鐨勬墿鏁ｇ郴鏁?
        delta_W: 杩囩▼澧為噺锛堢敤浜庡悗缁垎鏋愶級
    """
    # 璁＄畻杩囩▼澧為噺锛堥暱搴锛?
    delta_W = np.diff(W)  # delta_W[i] = W[i+1] - W[i]

    # 1. 浼拌mu锛氭牱鏈潎鍊?/ dt
    mean_delta_W = np.mean(delta_W)
    mu_est = mean_delta_W / dt

    # 2. 浼拌sigma锛歴qrt(鏍锋湰鏂瑰樊 / dt)锛堢敤N-1鍋氭棤鍋忎及璁★級
    var_delta_W = np.var(delta_W, ddof=1)  # ddof=1 鈫?鏃犲亸鏂瑰樊
    sigma_est = np.sqrt(var_delta_W / dt)

    return mu_est, sigma_est, delta_W


def calculate_boundary_b(t1, x1, mu1, t2, x2, mu2, max_rul):
    """
    鏍规嵁涓や釜鏃跺埢鐨勫弬鏁拌绠楃鍚堣姹傜殑杈圭晫闃堝€糱

    鍙傛暟:
    t1, t2: 涓や釜鏃跺埢
    x1, x2: 涓や釜鏃跺埢鐨勭姸鎬佸€?
    mu1, mu2: 涓や釜鏃跺埢鐨勬紓绉荤郴鏁?

    杩斿洖:
    b: 璁＄畻寰楀埌鐨勮竟鐣岄槇鍊?
    valid: 甯冨皵鍊硷紝鎸囩ず瑙ｆ槸鍚︽湁鏁堬紙婕傜Щ鏂瑰悜鏄惁鎸囧悜杈圭晫锛?
    """
    # 璁＄畻鏃堕棿宸?
    delta_t = t2 - t1

    if not np.isclose(mu1, mu2):
        # 搴旂敤鎺ㄥ鐨勮В鏋愬叕寮?
        numerator = mu1 * mu2 * delta_t + mu2 * x1 - mu1 * x2
        denominator = mu2 - mu1
        b = numerator / denominator

        # 楠岃瘉鏈夋晥鎬э細鐘舵€侀渶鍚戣竟鐣屾紨鍖栵紙b > x1 涓?b > x2锛屽洜mu涓烘锛?
        valid1 = (b > x1) and (mu1 > 0)  # 婕傜Щ涓烘涓旇竟鐣屽湪褰撳墠鐘舵€佸墠鏂?
        valid2 = (b > x2) and (mu2 > 0)
        valid = valid1 and valid2

        if not valid:
            return 0.0, False  # 鏃犳晥瑙ｈ繑鍥?鍜孎alse

        # 璁＄畻t2鏃跺埢瀵瑰簲鐨勫墿浣欏鍛斤紙RUL锛?
        rul_t2 = (b - x2) / mu2  # 鍩轰簬鍘熷b鐨勫墿浣欏鍛?

        # 濡傛灉鍓╀綑瀵垮懡瓒呰繃max_rul锛岄噸鏂拌绠梑
        if rul_t2 > max_rul:
            # 鍩轰簬t2, x2, mu2鍜宮ax_rul璁＄畻鏂扮殑b
            b_constrained = x2 + mu2 * max_rul
            # 楠岃瘉绾︽潫瑙ｇ殑鏈夋晥鎬э紙搴旀弧瓒砨_constrained > x2涓攎u2 > 0锛?
            valid_constrained = (b_constrained > x2) and (mu2 > 0)
            return b_constrained, valid_constrained
        else:
            # 鏈秴杩噈ax_rul锛岃繑鍥炲師濮嬭В
            return b, valid

    # 澶勭悊婕傜Щ绯绘暟鐩稿悓鐨勬儏鍐?
    else:
        return 0.0, False
        # # 妫€鏌ョ姸鎬佹紨鍖栨槸鍚︾鍚堟紓绉昏秼鍔?
        # expected_x2 = x1 + mu1 * delta_t
        # if np.isclose(x2, expected_x2):
        #     # 浠绘剰婊¤冻婕傜Щ鏂瑰悜鐨刡閮芥槸鏈夋晥瑙ｏ紝杩欓噷杩斿洖涓€涓ず渚嬭В
        #     # 閫夋嫨b浣垮緱绗竴涓椂鍒荤殑鏈熸湜鍓╀綑瀵垮懡涓轰竴涓悎鐞嗗€硷紙濡?00鍗曚綅鏃堕棿锛?
        #     b = x1 + mu1 * 100
        #     valid1 = (mu1 * (b - x1)) > 0
        #     valid2 = (mu2 * (b - x2)) > 0
        #     valid = valid1 and valid2
        #     return b, valid
        # else:
        #     # 鐘舵€佹紨鍖栦笌婕傜Щ瓒嬪娍鐭涚浘锛屾棤瑙?
        #     return None, False


def median_and_index(arr):
    median_index = len(arr) // 2
    arr_array = np.array(arr)
    sorted_indices = np.argsort(arr_array)  # 杩斿洖鎺掑簭绱㈠紩
    sorted_arr = arr_array[sorted_indices]
    return sorted_arr[median_index].item(), int(sorted_indices[median_index])


def asymptotic_function(x, k=0.5, C=2, f0=1):
    """
    瀹氫箟f(0)=1涓旀笎杩涘埌2鐨勫嚱鏁?

    鍙傛暟:
    x: 杈撳叆鍊硷紙鍙互鏄崟涓暟鍊兼垨鏁扮粍锛?
    k: 鏀舵暃閫熷害鍙傛暟锛坘>0锛屽€艰秺澶ф敹鏁涜秺蹇級

    杩斿洖:
    鍑芥暟鍊糵(x)
    """
    return C + (f0 - C) * np.exp(-k * x)


def calc_b(wiener_model: SingleStageWienerModel, b0=100.0, max_rul=float("inf")):
    # if not hasattr(calc_b, "__non_valid_counter"):
    #     calc_b.__non_valid_counter = 0  # 缁欏嚱鏁扮粦瀹氫竴涓睘鎬?
    # if not hasattr(calc_b, "__last_b"):
    #     calc_b.__last_b = b0  # 鍒濆杈圭晫
    if len(wiener_model.data) < wiener_model.window_size:
        # 鍒濆杈圭晫
        # return b0
        if not wiener_model.data:
            return b0  # 濡傛灉娌℃湁鏁版嵁锛岃繑鍥炲垵濮嬭竟鐣?
        return max(wiener_model.data) * 1.5  # 杩斿洖褰撳墠鐘舵€佺殑鏈€澶у€间綔涓鸿竟鐣?

    # 鍙栧墠鍚庝袱涓崐绐楀彛鐨勪腑浣嶆暟
    half_window_1 = wiener_model.data[-wiener_model.window_size : -wiener_model.window_size // 2]
    half_window_2 = wiener_model.data[-wiener_model.window_size // 2 :]
    median_1, index_1 = median_and_index(half_window_1)
    median_2, index_2 = median_and_index(half_window_2)

    t1 = wiener_model.time[-wiener_model.window_size + index_1]
    x1 = median_1
    mu1 = wiener_model.mu_hist[-wiener_model.window_size + index_1]

    t2 = wiener_model.time[-wiener_model.window_size // 2 + index_2]
    x2 = median_2
    mu2 = wiener_model.mu_hist[-wiener_model.window_size // 2 + index_2]

    b, valid = calculate_boundary_b(t1, x1, mu1, t2, x2, mu2, max_rul=max_rul)
    valid2 = (b > max(half_window_1)) and (b > max(half_window_2))  # 杈圭晫闇€鍦ㄥ綋鍓嶇姸鎬佸墠鏂?
    if valid and valid2:
        # calc_b.__non_valid_counter = 0
        # calc_b.__last_b = b  # 鏇存柊鏈€鍚庢湁鏁堣竟鐣?
        return b
    else:
        # # 杈圭晫鏇存柊鏃犳晥鏃惰涓虹姸鎬佸仴搴凤紝澧炲ぇ鍘熸湁杈圭晫
        # calc_b.__non_valid_counter += 1  # 姣忔璋冪敤鍔?
        # # 闈炵嚎鎬у澶0
        # b0_ = calc_b.__last_b * asymptotic_function(calc_b.__non_valid_counter)
        return max(b0, max(half_window_1) * 1.5, max(half_window_2) * 1.5)  # 杩斿洖褰撳墠鐘舵€佺殑鏈€澶у€间綔涓鸿竟鐣?


def estimate_noise_std_emd(y_series, method="mad", plot=False, max_imf=10):
    """
    鐢ㄧ粡楠屾ā鎬佸垎瑙ｏ紙EMD锛変及璁″甫鍣０瓒嬪娍鏁版嵁鐨勫櫔澹版爣鍑嗗樊

    杈撳叆锛?
        y_series: 甯﹀櫔澹扮殑瓒嬪娍鏁版嵁锛坙ist 鎴?numpy array锛?
        method: 浼拌鏂规硶锛?mad'锛堟姉寮傚父鍊硷級鎴?'std'锛堢畝鍗曠洿瑙傦級锛岄粯璁?'mad'
        plot: 鏄惁鍙鍖栧垎瑙ｇ粨鏋滐紝榛樿 False
        max_imf: 鏈€澶MF鏁伴噺闄愬埗锛岄粯璁?10

    杈撳嚭锛?
        sigma_noise: 浼拌鐨勫櫔澹版爣鍑嗗樊
        noise_components: 鎵€鏈夎瑙嗕负鍣０鐨処MF鍒嗛噺涔嬪拰
    """
    # 1. 鏁版嵁棰勫鐞嗭細杞崲涓?numpy 鏁扮粍锛屽幓闄ゅ彲鑳界殑 NaN
    y = np.asarray(y_series, dtype=np.float64)
    y = y[~np.isnan(y)]  # 杩囨护缂哄け鍊?
    n = len(y)

    if n < 4:
        raise ValueError("鏁版嵁闀垮害杩囩煭锛堣嚦灏戦渶瑕?涓偣锛夛紝鏃犳硶杩涜鏈夋晥EMD鍒嗚В")

    # 2. 鎵цEMD鍒嗚В
    emd = EMD(max_imf=max_imf)
    imfs = emd(y)

    # 3. 鏂伴€昏緫锛氶櫎浜嗘渶鍚庝竴涓垎閲忓锛屽叾浣欐墍鏈塈MF閮借瑙嗕负鍣０
    if len(imfs) == 0:
        raise RuntimeError("EMD鍒嗚В鏈兘浜х敓浠讳綍IMF鍒嗛噺")

    # 鏈€鍚庝竴涓垎閲忚璁や负鏄秼鍔?缂撳彉淇″彿
    trend_component = imfs[-1]

    # 闄や簡鏈€鍚庝竴涓垎閲忓锛屽叾浣欐墍鏈塈MF閮借瑙嗕负鍣０
    noise_imfs = imfs[:-1] if len(imfs) > 1 else []

    # 灏嗘墍鏈夊櫔澹癐MF鐩稿姞寰楀埌鎬诲櫔澹板垎閲?
    noise_components = np.zeros_like(y)
    for imf in noise_imfs:
        noise_components += imf

    # 4. 鐢ㄦ寚瀹氭柟娉曚及璁″櫔澹版爣鍑嗗樊
    if len(noise_imfs) > 0:
        # 鍩轰簬鎬诲櫔澹板垎閲忎及璁″櫔澹版按骞?
        if method == "mad":
            # MAD娉曪細涓綅鏁扮粷瀵瑰亸宸?鈫?杞崲涓烘爣鍑嗗樊
            med = np.median(np.abs(noise_components - np.median(noise_components)))
            sigma_noise = med * 1.4826  # 楂樻柉鍒嗗竷杞崲绯绘暟
        elif method == "std":
            # 鏍囧噯宸硶锛氱洿鎺ヨ绠楁爣鍑嗗樊
            sigma_noise = np.std(noise_components, ddof=1)  # ddof=1 涓烘棤鍋忎及璁?
        else:
            raise ValueError("method 浠呮敮鎸?'mad' 鎴?'std'")
    else:
        # 濡傛灉娌℃湁鍣０鍒嗛噺锛堝彧鏈夎秼鍔匡級锛屽垯鍣０鏍囧噯宸负0
        sigma_noise = 0.0

    # 5. 鏁板€肩ǔ瀹氭€у鐞嗭細閬垮厤鏍囧噯宸繃灏忥紙濡傛帴杩?锛?
    sigma_noise = max(sigma_noise, 1e-10)

    # 6. 鍙鍖?
    if plot:
        plt.figure(figsize=(12, 4 + 1 * len(imfs)))

        # 鍘熷淇″彿
        plt.subplot(len(imfs) + 2, 1, 1)
        plt.plot(y, "b-", alpha=0.7, label="鍘熷淇″彿")
        plt.title("鍘熷淇″彿")
        plt.grid(True)
        plt.legend()

        # 鍚処MF鍒嗛噺
        for i, imf in enumerate(imfs):
            plt.subplot(len(imfs) + 2, 1, i + 2)
            plt.plot(imf, "g-", label=f"IMF {i+1}")
            if i < len(imfs) - 1:
                plt.gca().set_facecolor((1.0, 0.95, 0.95))  # 楂樹寒鍣０鍒嗛噺
            else:
                plt.gca().set_facecolor((0.95, 1.0, 0.95))  # 楂樹寒瓒嬪娍鍒嗛噺
            plt.title(f"IMF {i+1} (蟽={np.std(imf):.4f})")
            plt.grid(True)
            plt.legend()

        # 鍒嗙鐨勫櫔澹板拰瓒嬪娍
        plt.subplot(len(imfs) + 2, 1, len(imfs) + 2)
        plt.plot(noise_components, "r-", alpha=0.7, label="鍣０鍒嗛噺")
        plt.plot(trend_component, "g-", alpha=0.7, label="瓒嬪娍鍒嗛噺")
        plt.plot(noise_components + trend_component, "b--", alpha=0.5, label="鍣０+瓒嬪娍")
        plt.title(f"鍒嗙缁撴灉 (浼拌鍣０蟽={sigma_noise:.4f})")
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.suptitle(f"EMD鍒嗚В - 缂撳彉淇″彿妯″瀷", fontsize=14)
        plt.subplots_adjust(top=0.95)
        plt.show()

        # 鍣０鍒嗛噺鐨勫垎甯冮獙璇?
        if len(noise_imfs) > 0:
            plt.figure(figsize=(10, 4))
            plt.subplot(1, 2, 1)
            plt.plot(noise_components, "r-")
            plt.title(f"鎬诲櫔澹板垎閲?(蟽={sigma_noise:.4f})")
            plt.grid(True)

            plt.subplot(1, 2, 2)
            plt.hist(noise_components, bins=30, density=True, alpha=0.6, label="鍒嗗竷")
            x = np.linspace(-3 * sigma_noise, 3 * sigma_noise, 100)
            plt.title("鍣０鍒嗛噺鍒嗗竷楠岃瘉")
            plt.legend()
            plt.grid(True)

            plt.tight_layout()
            plt.show()

    return float(sigma_noise), noise_components


def estimate_noise_std_wavelet(
    y_series, wavelet="db4", level=3, method="mad", plot=False
):  # 鍙€?'mad' 鎴?'std'
    """
    鐢ㄥ皬娉㈠垎瑙ｄ及璁″甫鍣０瓒嬪娍鏁版嵁鐨勫櫔澹版爣鍑嗗樊
    杈撳叆锛?
        y_series: 甯﹀櫔澹扮殑瓒嬪娍鏁版嵁锛坙ist 鎴?numpy array锛?
        wavelet: 灏忔尝鍩猴紙濡?'db4', 'sym8', 'haar'锛夛紝榛樿 'db4'锛堝伐绋嬪父鐢級
        level: 灏忔尝鍒嗚В灞傛暟锛岄粯璁?3锛堥渶婊¤冻 2^level 鈮?len(y_series)锛?
        method: 浼拌鏂规硶锛?mad'锛堟姉寮傚父鍊硷級鎴?'std'锛堢畝鍗曠洿瑙傦級锛岄粯璁?'mad'
    杈撳嚭锛?
        sigma_noise: 浼拌鐨勫櫔澹版爣鍑嗗樊
        detail_coeffs: 鐢ㄤ簬浼拌鐨勬渶楂橀缁嗚妭绯绘暟锛堜緵楠岃瘉鐢級
    """
    # 1. 鏁版嵁棰勫鐞嗭細杞崲涓?numpy 鏁扮粍锛屽幓闄ゅ彲鑳界殑 NaN
    y = np.asarray(y_series, dtype=np.float64)
    y = y[~np.isnan(y)]  # 杩囨护缂哄け鍊?
    n = len(y)

    # 2. 鏍￠獙鍒嗚В灞傛暟锛氱‘淇?2^level 鈮?鏁版嵁闀垮害锛堝皬娉㈠垎瑙ｇ殑甯歌绾︽潫锛?
    max_valid_level = pywt.dwt_max_level(n, wavelet)  # 璁＄畻鏈€澶у彲琛屽眰鏁?
    level = min(level, max_valid_level)  # 鍙栬緭鍏ュ眰鏁颁笌鏈€澶у彲琛屽眰鏁扮殑杈冨皬鍊?
    if level < 1:  # 鑷冲皯鍒嗚В1灞備互鑾峰彇缁嗚妭绯绘暟
        raise ValueError(f"鏁版嵁闀垮害杩囩煭锛堝綋鍓峽len(y)}锛夛紝鏃犳硶杩涜鏈夋晥灏忔尝鍒嗚В锛岄渶澧炲姞鏁版嵁閲?)

    # 3. 灏忔尝鍒嗚В锛氳幏鍙栬繎浼肩郴鏁板拰缁嗚妭绯绘暟
    # coeffs 缁撴瀯锛歔杩戜技绯绘暟A_level, 缁嗚妭绯绘暟D_level, 缁嗚妭绯绘暟D_{level-1}, ..., 缁嗚妭绯绘暟D_1]
    coeffs = pywt.wavedec(y, wavelet=wavelet, level=level)
    A_level = coeffs[0]  # 绗?level 灞傝繎浼肩郴鏁帮紙瓒嬪娍涓诲锛?
    D_level = coeffs[1]  # 绗?level 灞傜粏鑺傜郴鏁帮紙鏈€楂橀锛屽櫔澹颁富瀵硷級鈥斺€旀牳蹇冪敤浜庝及璁?

    # 4. 鐢ㄦ寚瀹氭柟娉曚及璁″櫔澹版爣鍑嗗樊
    if method == "mad":
        # MAD 娉曪細涓綅鏁扮粷瀵瑰亸宸?鈫?杞崲涓烘爣鍑嗗樊锛堥珮鏂垎甯冧笅绯绘暟鈮?.4826锛?
        med = np.median(np.abs(D_level - np.median(D_level)))  # 涓績鍖朚AD
        sigma_noise = med * 1.4826  # 杞崲绯绘暟锛堝熀浜庨珮鏂櫔澹板亣璁撅級
    elif method == "std":
        # 鏍囧噯宸硶锛氱洿鎺ヨ绠楁渶楂橀缁嗚妭绯绘暟鐨勬爣鍑嗗樊
        sigma_noise = np.std(D_level, ddof=1)  # ddof=1 涓烘棤鍋忎及璁★紙闄や互n-1锛?
    else:
        raise ValueError("method 浠呮敮鎸?'mad' 鎴?'std'")

    # 5. 鏁板€肩ǔ瀹氭€у鐞嗭細閬垮厤鏍囧噯宸繃灏忥紙濡傛帴杩?锛?
    sigma_noise = np.clip(sigma_noise, 1e-10, np.inf)
    recon = pywt.waverec([A_level] + [None] * level, wavelet)
    # 纭繚闀垮害涓€鑷?
    if len(recon) > len(y_series):
        recon = recon[: len(y_series)]  # 鎴柇灏鹃儴
    elif len(recon) < len(y_series):
        # 鍦ㄥ熬閮ㄥ～鍏咃紙閫氬父鐢?鎴栭暅鍍忓€硷級
        pad_length = len(y_series) - len(recon)
        recon = np.pad(recon, (0, pad_length), mode="edge")
    resid = y_series - recon

    # 鍙鍖?
    if plot:
        plt.figure(figsize=(12, 8))

        # 鍘熷淇″彿涓庤秼鍔?
        plt.subplot(3, 1, 1)
        plt.plot(y, "b-", label="鍘熷淇″彿", alpha=0.5)
        plt.plot(recon, "r-", label=f"瓒嬪娍 (level={level})")
        plt.title(f"淇″彿涓庤秼鍔?(灏忔尝鍩? {wavelet})")
        plt.legend()

        # 鏈€楂橀缁嗚妭绯绘暟锛堝櫔澹帮級
        plt.subplot(3, 1, 2)
        plt.plot(D_level, "g-", label=f"鏈€楂橀缁嗚妭绯绘暟 (D{level})")
        plt.axhline(0, color="k", linestyle="--")
        plt.title(f"鍣０鎴愬垎 (浼拌鏂规硶: {method}, 蟽={sigma_noise:.4f})")
        plt.legend()

        # 缁嗚妭绯绘暟鐩存柟鍥撅紙楠岃瘉楂樻柉鎬э級
        plt.subplot(3, 1, 3)
        plt.hist(D_level, bins=30, density=True, alpha=0.6, label="缁嗚妭绯绘暟鍒嗗竷")
        plt.hist(resid, bins=30, density=True, alpha=0.6, label="娈嬪樊鍒嗗竷")
        x = np.linspace(-3 * sigma_noise, 3 * sigma_noise, 100)
        # plt.plot(x, stats.norm.pdf(x, 0, sigma_noise), "r-", label="鎷熷悎姝ｆ€佸垎甯?)
        plt.title("缁嗚妭绯绘暟鍒嗗竷楠岃瘉")
        plt.legend()

        plt.tight_layout()
        plt.show()

    return float(sigma_noise), resid  # 杩斿洖鏍囧噯宸紙float锛夊拰娈嬪樊锛堜緵楠岃瘉锛?


if __name__ == "__main__":
    data = np.random.rand(6600000, 3)  # 绀轰緥鏁版嵁
    create_windows(data, window_size=64, step=32)

