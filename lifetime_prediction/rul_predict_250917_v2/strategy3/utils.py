import collections
import logging
import pickle
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def parse_timestamp_flexible(timestamp_str):
    """
    鐏垫椿瑙ｆ瀽鏃堕棿鎴冲瓧绗︿覆锛屾敮鎸佸绉嶆牸寮?
    
    Args:
        timestamp_str: 鏃堕棿鎴冲瓧绗︿覆鎴杙andas.Timestamp
        
    Returns:
        pandas.Timestamp: 瑙ｆ瀽鍚庣殑鏃堕棿鎴?
    """
    if isinstance(timestamp_str, pd.Timestamp):
        return timestamp_str
    
    if not isinstance(timestamp_str, str):
        timestamp_str = str(timestamp_str)
    
    # 棰勫鐞嗭細鏍囧噯鍖栨椂闂存埑鏍煎紡
    timestamp_str = timestamp_str.strip()
    
    # 鏀寔鐨勬椂闂存牸寮忓垪琛紙鎸夊父瑙佺▼搴︽帓搴忥級
    formats_to_try = [
        # ISO 8601 鏍煎紡鍙樹綋
        '%Y-%m-%dT%H:%M:%S%z',           # 2018-09-11T00:00:00+00:00
        '%Y-%m-%dT%H:%M:%S.%f%z',        # 2018-09-11T00:00:00.000+00:00
        '%Y-%m-%dT%H:%M:%SZ',            # 2018-09-11T00:00:00Z
        '%Y-%m-%dT%H:%M:%S.%fZ',         # 2018-09-11T00:00:00.000Z
        '%Y-%m-%dT%H:%M:%S',             # 2018-09-11T00:00:00
        
        # 娣峰悎鏍煎紡锛堟枩鏉犳棩鏈?+ T鏃堕棿锛?
        '%Y/%m/%dT%H:%M:%S%z',           # 2018/09/11T00:00:00+00:00
        '%Y/%m/%dT%H:%M:%S.%f%z',        # 2018/09/11T00:00:00.000+00:00
        '%Y/%m/%dT%H:%M:%SZ',            # 2018/09/11T00:00:00Z
        '%Y/%m/%dT%H:%M:%S.%fZ',         # 2018/09/11T00:00:00.000Z
        '%Y/%m/%dT%H:%M:%S',             # 2018/09/11T00:00:00
        
        # 浼犵粺鏍煎紡
        '%Y/%m/%d %H:%M:%S',             # 2018/09/11 00:00:00
        '%Y-%m-%d %H:%M:%S',             # 2018-09-11 00:00:00
        '%Y/%m/%d %H:%M:%S.%f',          # 2018/09/11 00:00:00.000
        '%Y-%m-%d %H:%M:%S.%f',          # 2018-09-11 00:00:00.000
        
        # 鍙湁鏃ユ湡鐨勬牸寮?
        '%Y/%m/%d',                      # 2018/09/11
        '%Y-%m-%d',                      # 2018-09-11
    ]
    
    # 灏濊瘯鍚勭鏍煎紡
    for fmt in formats_to_try:
        try:
            return pd.to_datetime(timestamp_str, format=fmt)
        except (ValueError, TypeError):
            continue
    
    # 濡傛灉鎵€鏈夐瀹氫箟鏍煎紡閮藉け璐ワ紝灏濊瘯pandas鐨勬櫤鑳借В鏋?
    try:
        # 浣跨敤pandas鐨勬櫤鑳借В鏋愶紝鏀寔ISO8601绛夊绉嶆牸寮?
        return pd.to_datetime(timestamp_str, format='ISO8601')
    except:
        try:
            # 鏈€鍚庡皾璇曟贩鍚堟牸寮忚В鏋?
            return pd.to_datetime(timestamp_str, format='mixed')
        except:
            # 濡傛灉閮藉け璐ワ紝鎶涘嚭璇︾粏鐨勯敊璇俊鎭?
            raise ValueError(f"鏃犳硶瑙ｆ瀽鏃堕棿鎴虫牸寮? '{timestamp_str}'銆傛敮鎸佺殑鏍煎紡鍖呮嫭ISO8601銆佷紶缁熸牸寮忕瓑銆?)

from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from .model import SOM as SOM

plt.rcParams["font.sans-serif"] = "Microsoft YaHei"  # 璁剧疆姝ｅ父鏄剧ず涓枃瀛楃
plt.rcParams["axes.unicode_minus"] = False  # 璁剧疆姝ｅ父鏄剧ず璐熷彿

# 鍒涘缓logger
logger = logging.getLogger(__name__)

I_LOW_RMS_NAME = "浣庨€熺數娴佹湁鏁堝€?

# PHM鍨嬪彿閰嶇疆鏄犲皠琛紙鏀寔NM鍜孨MS涓ょ鏍煎紡锛?
_PHM_TYPE_COL_CONFIG = {
    "2NM": {
        "col_names": ["杞瓙鐢垫満鐢垫祦", "妗嗘灦鐢垫満A鐩哥數娴?, "妗嗘灦鐢垫満C鐩哥數娴?],
        "convert_ilow": ["妗嗘灦鐢垫満A鐩哥數娴?, "妗嗘灦鐢垫満C鐩哥數娴?],
    },
    "5NM": {
        "col_names": ["杞瓙鐢垫満鐢垫祦", "妗嗘灦鐢垫満鐢垫祦"],
        "convert_ilow": [],
    },
    "15NM": {
        "col_names": ["楂橀€熺數鏈虹數鍘嬫娴?, "楂橀€熺數鏈虹數娴侀仴娴?, "浣庨€熺數鏈虹數娴侀仴娴?],
        "convert_ilow": [],
    },
    "500NM": {
        "col_names": ["楂橀€熺數鏈虹數鍘?, "楂橀€熺數鏈虹數娴?, "浣庨€烝鐩哥數娴?, "浣庨€烠鐩哥數娴?],
        "convert_ilow": ["浣庨€烝鐩哥數娴?, "浣庨€烠鐩哥數娴?],
    },
}

# 鏋勫缓鍏煎NM鍜孨MS涓ょ鏍煎紡鐨勬槧灏勮〃
PHM_TYPE_COL_NAME_MAP = {}
for base_type, config in _PHM_TYPE_COL_CONFIG.items():
    PHM_TYPE_COL_NAME_MAP[base_type] = config
    PHM_TYPE_COL_NAME_MAP[base_type + "S"] = config


def fuzzy_match_cmg_type(cmg_type: str) -> str:
    """
    妯＄硦鍖归厤PHM鍨嬪彿鍚嶇О锛屼粠澶嶆潅鐨勫瀷鍙峰瓧绗︿覆涓彁鍙栨爣鍑嗗瀷鍙?
    
    鏀寔浠庝互涓嬫牸寮忎腑鎻愬彇鍨嬪彿锛?
    - "TG-15NMS" -> "15NMS"
    - "JB-500NM-V2" -> "500NM"
    - "鍗槦-15NM" -> "15NM"
    - "500NM" -> "500NM"锛堢洿鎺ュ尮閰嶏級
    - "15nm" -> "15NM"锛堝ぇ灏忓啓涓嶆晱鎰燂級
    
    Args:
        cmg_type: 鍘熷PHM鍨嬪彿瀛楃涓?
        
    Returns:
        str: 鏍囧噯鍖栧悗鐨凜MG鍨嬪彿锛堜紭鍏堣繑鍥濶MS鏍煎紡锛?
        
    Raises:
        ValueError: 濡傛灉鏃犳硶浠庡瓧绗︿覆涓瘑鍒嚭浠讳綍鏀寔鐨勫瀷鍙?
    """
    import re
    
    if not cmg_type:
        raise ValueError("PHM鍨嬪彿涓嶈兘涓虹┖")
    
    # 杞负澶у啓浠ユ敮鎸佸ぇ灏忓啓涓嶆晱鎰?
    cmg_type_upper = cmg_type.upper().strip()
    
    # 绗竴姝ワ細灏濊瘯鐩存帴鍖归厤锛堝畬鍏ㄥ尮閰嶏級
    if cmg_type_upper in PHM_TYPE_COL_NAME_MAP:
        # 浼樺厛杩斿洖NMS鏍煎紡
        if cmg_type_upper.endswith("NM") and not cmg_type_upper.endswith("NMS"):
            nms_version = cmg_type_upper + "S"
            if nms_version in PHM_TYPE_COL_NAME_MAP:
                return nms_version
        return cmg_type_upper
    
    # 绗簩姝ワ細妯＄硦鍖归厤 - 浠庡瓧绗︿覆涓彁鍙栧瀷鍙锋ā寮?
    # 鏀寔鐨勫瀷鍙锋ā寮忓垪琛紙鎸夋暟瀛楀ぇ灏忔帓搴忥紝閬垮厤璇尮閰嶏紝濡?000NM搴斾紭鍏堜簬500NM锛?
    supported_patterns = [
        '5000NMS', '5000NM',  # 5000NM绯诲垪
        '500NMS', '500NM',    # 500NM绯诲垪
        '15NMS', '15NM',      # 15NM绯诲垪
        '5NMS', '5NM',        # 5NM绯诲垪
        '2NMS', '2NM'         # 2NM绯诲垪
    ]
    
    # 灏濊瘯鍦ㄥ瓧绗︿覆涓煡鎵捐繖浜涙ā寮?
    for pattern in supported_patterns:
        # 浣跨敤姝ｅ垯琛ㄨ揪寮忓尮閰嶏紙鏀寔鍓嶅悗鏈夊垎闅旂鎴栧叾浠栧瓧绗︼級
        # 渚嬪锛歍G-15NMS銆丣B-500NM-V2銆佸崼鏄焈15NM绛?
        if re.search(r'\b' + pattern + r'\b', cmg_type_upper) or pattern in cmg_type_upper:
            logger.info(f"妯＄硦鍖归厤鎴愬姛: '{cmg_type}' -> '{pattern}'")
            return pattern
    
    # 绗笁姝ワ細灏濊瘯鎻愬彇绾暟瀛?NM/NMS妯″紡
    # 鍖归厤妯″紡锛氭暟瀛?+ NM 鎴?NMS
    # 渚嬪锛氫粠"鍨嬪彿15NM鐗堟湰2"涓彁鍙?15NM"
    number_nm_match = re.search(r'(\d+)(NMS?)\b', cmg_type_upper)
    if number_nm_match:
        extracted_type = number_nm_match.group(1) + number_nm_match.group(2)  # 濡?15NM"鎴?15NMS"
        # 楠岃瘉鎻愬彇鐨勫瀷鍙锋槸鍚﹀湪鏀寔鍒楄〃涓?
        if extracted_type in PHM_TYPE_COL_NAME_MAP:
            logger.info(f"閫氳繃姝ｅ垯鎻愬彇鎴愬姛: '{cmg_type}' -> '{extracted_type}'")
            return extracted_type
        # 濡傛灉鎻愬彇鐨勬槸NM鏍煎紡锛屽皾璇曡浆鎹负NMS
        if extracted_type.endswith("NM") and not extracted_type.endswith("NMS"):
            nms_version = extracted_type + "S"
            if nms_version in PHM_TYPE_COL_NAME_MAP:
                logger.info(f"閫氳繃姝ｅ垯鎻愬彇骞惰浆鎹? '{cmg_type}' -> '{nms_version}'")
                return nms_version
    
    # 绗洓姝ワ細灏濊瘯鍙彁鍙栨暟瀛楋紝鐒跺悗灏濊瘯鍖归厤
    # 渚嬪锛氫粠"TG-15-V2"涓彁鍙?15"锛岀劧鍚庡皾璇?5NM鍜?5NMS
    numbers = re.findall(r'\d+', cmg_type_upper)
    for num in numbers:
        # 灏濊瘯璇ユ暟瀛楃殑NMS鍜孨M鏍煎紡
        for suffix in ['NMS', 'NM']:
            candidate = num + suffix
            if candidate in PHM_TYPE_COL_NAME_MAP:
                logger.info(f"閫氳繃鏁板瓧鎻愬彇鎴愬姛: '{cmg_type}' -> '{candidate}'锛堜粠鏁板瓧 {num} 鎺ㄦ柇锛?)
                return candidate
    
    # 濡傛灉鎵€鏈夋柟娉曢兘澶辫触锛屾姏鍑鸿缁嗛敊璇?
    supported_list = ', '.join(sorted(set(PHM_TYPE_COL_NAME_MAP.keys())))
    raise ValueError(
        f"鏃犳硶璇嗗埆PHM鍨嬪彿: '{cmg_type}'銆俓n"
        f"鏀寔鐨勫瀷鍙峰寘鎷? {supported_list}\n"
        f"璇风‘淇濆瀷鍙峰悕绉板寘鍚繖浜涘叧閿瓧涔嬩竴"
    )


def normalize_cmg_type(cmg_type: str) -> str:
    """
    鏍囧噯鍖朇MG鍨嬪彿鍚嶇О锛岀粺涓€杞崲涓篘MS鏍煎紡
    
    浣跨敤妯＄硦鍖归厤绠楁硶锛岃兘澶熶粠澶嶆潅鐨勫瀷鍙峰瓧绗︿覆涓彁鍙栨爣鍑嗗瀷鍙枫€?
    鏀寔 "TG-15NMS", "JB-500NM-V2", "鍗槦-15NM" 绛夋牸寮忋€?
    
    Args:
        cmg_type: 鍘熷PHM鍨嬪彿锛屽 "500NM", "500nm", "TG-500NMS", "JB-15NM-V2"
        
    Returns:
        str: 鏍囧噯鍖栧悗鐨凜MG鍨嬪彿锛圢MS鏍煎紡锛夛紝濡?"500NMS"
        
    Raises:
        ValueError: 濡傛灉鏃犳硶璇嗗埆PHM鍨嬪彿
    """
    # 浣跨敤妯＄硦鍖归厤鍑芥暟
    return fuzzy_match_cmg_type(cmg_type)

def get_model_params(cmg_type: str, target_cols: list):
    """鑾峰彇妯″瀷鍙傛暟锛岃嚜鍔ㄥ吋瀹筃M鍜孨MS鏍煎紡"""
    normalized_type = normalize_cmg_type(cmg_type)
    base_type = normalized_type.replace("S", "") if normalized_type.endswith("S") else normalized_type
    
    model_path_nms = BASE_DIR / "strategy3" / "models" / normalized_type / "som_model.pkl"
    model_path_nm = BASE_DIR / "strategy3" / "models" / base_type / "som_model.pkl"
    
    if model_path_nms.exists():
        folder_name = normalized_type
    elif model_path_nm.exists():
        folder_name = base_type
    else:
        raise FileNotFoundError(f"鎵句笉鍒癈MG鍨嬪彿 '{cmg_type}' 鐨剆trategy3妯″瀷鏂囦欢")
    
    MODEL_PATH = BASE_DIR / "strategy3" / "models" / folder_name / "som_model.pkl"
    SCALERS_PATH = BASE_DIR / "strategy3" / "scalers" / folder_name / "scalers.pkl"
    SVD_SCALER_PATH = BASE_DIR / "strategy3" / "scalers" / folder_name / "svd_scaler.pkl"
    # 鍔犺浇褰掍竴鍖栧櫒
    scalers = pickle.load(open(SCALERS_PATH, "rb"))
    svd_scaler = pickle.load(open(SVD_SCALER_PATH, "rb"))
    # 鍔犺浇妯″瀷
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    
    params = {
        "model": model,
        "scalers": scalers,
        "svd_scaler": svd_scaler,
        "target_cols": target_cols,
    }
    return params

def y2s(y):
    return y * 365 * 24 * 60 * 60

def s2y(s):
    return s / (365 * 24 * 60 * 60)

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
        save_path = BASE_DIR / "strategy3" / "scalers" / f"scalers_{time.strftime('%Y%m%d_%H%M%S')}.pkl"
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(scalers, f)
    print(f"鏁版嵁褰掍竴鍖栧櫒宸蹭繚瀛樺埌: {save_path}")
    return scalers

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

def train_svd_scaler(svd_features_array, save_path=None):
    """璁粌濂囧紓鍊肩缉鏀惧櫒"""
    scaler = StandardScaler()
    scaler.fit(svd_features_array)
    if save_path is None:
        save_path = BASE_DIR / "strategy3" / "scalers" / f"svd_scaler_{time.strftime('%Y%m%d_%H%M%S')}.pkl"
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)
    with open(save_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"SVD鐗瑰緛褰掍竴鍖栧櫒宸蹭繚瀛樺埌: {save_path}")
    return scaler

def svd_feature_extract(mat, target_cols, scalers, svd_scaler=None):
    """SVD鍒嗚В鎻愬彇鐗瑰緛"""
    mat_scaled = scale_mat_by_scalers(mat, scalers, target_cols)
    U, sigma, VT = np.linalg.svd(mat_scaled)
    sigma, _ = reorder_sigma(sigma, U, VT)
    sigma_arr = np.array(sigma, dtype=np.float32)
    if svd_scaler is not None:
        sigma_arr = svd_scaler.transform(sigma_arr.reshape(1, -1)).flatten()
    return sigma_arr

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

class AdaptiveKalmanFilter2:
    def __init__(self, x0=0.0, P0=1.0, Q0=1e-4, R0=1.0, window_size=50):
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
                # 鍙湁绐楀彛婊′簡鎵嶇敤绐楀彛鏂瑰樊鏇存柊Q鍜孯锛屽惁鍒欑敤鍒濆鍊?
                if len(self.deltas) == self.window_size:
                    self.Q = np.var(self.deltas)
                else:
                    self.Q = self.Q0
                if len(self.residuals) == self.window_size:
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

def slope_correction(hi_ori, add_noise=True):
    """鏍规嵁鏂滅巼绗﹀彿淇 HI 搴忓垪涓殑寮傚父娉㈠姩娈?""
    # 璁＄畻璧风偣鍒板綋鍓嶇殑鏂滅巼k1锛屽綋鍓嶅埌缁堢偣鐨勬枩鐜噆2
    L = len(hi_ori)
    t = np.linspace(0, 1, L)
    hi_corrected = hi_ori.copy()
    hi_corrected[: L // 10] = np.median(hi_ori[: L // 10])
    hi_corrected[-L // 10 :] = np.median(hi_ori[-L // 10 :])
    k1 = (hi_corrected[1:-1] - hi_corrected[0]) / (t[1:-1] - t[0])
    k2 = (hi_corrected[-1] - hi_corrected[1:-1]) / (t[-1] - t[1:-1])
    k = k1 * k2  # 鏂滅巼涔樼Н锛屾甯稿簲鏄鍊硷紝璐熷€艰〃绀哄紓甯告尝鍔?
    k = np.concatenate([[0], k, [0]])  # 琛ラ綈闀垮害

    # 鏍规嵁鏂滅巼绗﹀彿淇
    anomaly_indices = np.where(k < 0)[0]
    normal_indices = np.where(k >= 0)[0]
    norm_std = np.std(hi_ori[normal_indices])
    prev_normal_idx = (
        np.argmax((normal_indices.reshape(1, -1) < anomaly_indices.reshape(-1, 1)) == 0, axis=1) - 1
    )
    hi_corrected[anomaly_indices] = hi_corrected[normal_indices[prev_normal_idx]]
    if add_noise:
        hi_corrected += np.random.randn(len(hi_corrected)) * norm_std * 0.5
    return hi_corrected

def calc_rul_weighted(
    time_start_use: str,
    time_stamps: pd.Series,
    design_life: float,
    hi: np.ndarray,
    w: float = 0.5,
    plot: bool = False,
    time_fmt="%Y/%m/%d %H:%M:%S",
):
    """鍔犳潈骞冲潎閫€鍖栭€熷害璁＄畻鍓╀綑瀵垮懡"""
    timestamp_start = parse_timestamp_flexible(time_stamps.iloc[0])
    timestamp_start_use = parse_timestamp_flexible(time_start_use)
    timestamp_end = parse_timestamp_flexible(time_stamps.iloc[-1])
    time_range = s2y((timestamp_end - timestamp_start).total_seconds())  # 鏁版嵁鏃堕棿鑼冨洿锛屽崟浣嶏細骞?
    if (timestamp_start_use - timestamp_start).total_seconds() > 0:
        raise ValueError("浣跨敤璧风偣鏃堕棿涓嶈兘鏅氫簬鏁版嵁璧风偣鏃堕棿锛岃妫€鏌ワ紒")
    if (timestamp_end - timestamp_start_use).total_seconds() >= y2s(design_life):
        raise ValueError("鏁版嵁缁堢偣鏃堕棿宸茬粡瓒呰繃璁捐瀵垮懡锛岃妫€鏌ワ紒")
    time_diff = (timestamp_end - timestamp_start).total_seconds()
    rul_theoretic = s2y(
        y2s(design_life) - (timestamp_end - timestamp_start_use).total_seconds()
    )
    degrade_rate_theoretic = design_life  # 鐞嗚閫€鍖栭€熷害, 1閫€鍖栧埌0闇€瑕佺殑骞存暟锛屽崟浣嶏細骞?
    delta_years = s2y(time_diff)
    degrade_rate_real = delta_years / (hi[0] - hi[-1] + 1e-5)  # 瀹為檯閫€鍖栭€熷害, 1閫€鍖栧埌0闇€瑕佺殑骞存暟锛屽崟浣嶏細骞?
    degrade_rate = w * degrade_rate_theoretic + (1 - w) * degrade_rate_real
    rul = w * rul_theoretic + (1 - w) * hi[-1] * degrade_rate  # 褰撳墠鐐圭殑鍓╀綑瀵垮懡锛屽崟浣嶏細骞?
    hi_high = np.clip(np.linspace(hi[-1], hi[-1] - time_range / degrade_rate_theoretic, len(hi)), 0, 1)
    hi_low = np.clip(np.linspace(hi[-1], hi[-1] - time_range / degrade_rate_real, len(hi)), 0, 1)
    if plot:
        plt.figure()
        plt.plot(np.arange(len(hi)), hi)
        t_pred = np.arange(len(hi)) + len(hi)
        plt.fill_between(t_pred, hi_low, hi_high, color="pink", alpha=0.5, label="鐞嗚/瀹為檯閫€鍖栭€熷害鍖洪棿")
        plt.ylim(-0.05, 1.05)
        plt.axhline(0, color="red", linestyle="--")
        plt.xlabel("鏃堕棿姝?)
        plt.ylabel("鍋ュ悍鎸囨暟 HI")
    return rul, hi_high, hi_low
