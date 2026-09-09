import pickle
import sys
from pathlib import Path

import chardet
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import strategy2.utils as utils
from strategy2.utils import (
    PHM_TYPE_COL_NAME_MAP,
    add_low_i_rms,
    train_scalers,
    train_svd_features_scaler,
)

BASE_DIR = Path(__file__).resolve().parent.parent

class IsolationForestModel:
    def __init__(self, n_estimators=100, contamination='auto', random_state=0, **kwargs):
        """
        鍒濆鍖栧绔嬫．鏋楁ā鍨?
        """
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            **kwargs
        )
        
    def fit(self, X):
        """
        璁粌瀛ょ珛妫灄妯″瀷
        """
        self.model.fit(X)
        return self
        
    def get_anomaly_score(self, X):
        """
        鑾峰彇寮傚父鍒嗘暟锛堝綊涓€鍖栧埌0-1鍖洪棿锛?琛ㄧず鏈€寮傚父锛?
        """
        # score_samples杩斿洖鐨勬槸鍘熷寮傚父鍒嗘暟鐨勮礋鏁帮紝鍊艰秺灏忚〃绀鸿秺寮傚父
        raw_scores = self.model.score_samples(X)
        # 瀵瑰垎鏁板彇璐熸暟锛屼娇寰楀垎鏁拌秺澶ц〃绀鸿秺寮傚父
        negative_scores = -raw_scores
        
        # 濡傛灉鎴戜滑鏈夎冻澶熺殑鏍锋湰锛屽彲浠ョ敤min-max褰掍竴鍖?
        if len(negative_scores) > 1:
            min_score = np.min(negative_scores)
            max_score = np.max(negative_scores)
            if max_score > min_score:
                normalized_scores = (negative_scores - min_score) / (max_score - min_score)
                return normalized_scores
        
        # 濡傛灉鍙湁涓€涓牱鏈垨鎵€鏈夋牱鏈垎鏁扮浉鍚岋紝浣跨敤鎸囨暟鍙樻崲灏嗗垎鏁版槧灏勫埌[0,1]
        return 1 - np.exp(-negative_scores)

def save_model(model, save_path, **kwargs):
    """
    淇濆瓨妯″瀷鍜岀浉鍏冲弬鏁?
    """
    save_dict = {
        "model": model,
        **kwargs
    }
    
    # 纭繚鐩綍瀛樺湪
    save_path = Path(save_path)
    if not save_path.parent.exists():
        save_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(save_path, 'wb') as f:
        pickle.dump(save_dict, f)
    
    print(f"妯″瀷宸蹭繚瀛樺埌: {save_path}")

def train_isolation_forest_model(
    data_df,
    cmg_target_cols,
    cmg_type: str,
    save_path=None,
    window_size=64,  # 鍗曚竴绐楀彛澶у皬
    step=32,  # 绐楀彛婊戝姩姝ラ暱
    n_estimators=100,  # 瀛ょ珛妫灄鏍戠殑鏁伴噺
    contamination='auto',  # 瀛ょ珛妫灄寮傚父姣斾緥
    quantile_level=0.99,  # 寮傚父鍒嗘暟闃堝€煎垎浣嶆暟
):
    """
    璁粌瀛ょ珛妫灄妯″瀷骞朵繚瀛樻ā鍨?
    data_df: 鏁版嵁DataFrame
    save_path: 妯″瀷淇濆瓨璺緞
    cmg_target_cols: 鐩爣鍒楀悕鏄犲皠
    cmg_type: PHM绫诲瀷
    鍏跺畠鍙傛暟鍚岃缁冩祦绋?
    """
    print(f"姝ｅ湪璁粌{cmg_type}绫诲瀷鐨勫绔嬫．鏋楁ā鍨?..")
    
    # 娣诲姞浣庨€熺數娴佹湁鏁堝€?
    data_df, target_cols = add_low_i_rms(data_df, cmg_target_cols=cmg_target_cols)
    
    # 璁粌鍘熷鏁版嵁褰掍竴鍖栧櫒
    scalers = train_scalers(data_df, target_cols, save_path=BASE_DIR / "strategy2" / "scalers" / cmg_type / "scalers.pkl")
    
    # 鍘熷鏁版嵁
    normal_data = data_df[target_cols].values
    
    # 鍗曚竴绐楀彛鍒掑垎
    print(f"浣跨敤绐楀彛澶у皬: {window_size}锛屾闀? {step}")
    normal_data_windows = utils.create_windows(normal_data, window_size=window_size, step=step)
    
    # SVD鐗瑰緛鎻愬彇
    print(f"寮€濮嬫彁鍙朣VD鐗瑰緛...")
    svd_features = utils.extract_svd_features(
        normal_data_windows, target_cols, scalers
    )
    
    # 鐗瑰緛鏍囧噯鍖?
    print(f"SVD鐗瑰緛褰㈢姸: {svd_features.shape}")
    svd_scaler = train_svd_features_scaler(
        svd_features, save_path=BASE_DIR / "strategy2" / "scalers" / cmg_type / "svd_scaler.pkl"
    )
    
    # 褰掍竴鍖栫壒寰?
    scaled_features = svd_scaler.transform(svd_features)
    
    # 璁粌瀛ょ珛妫灄妯″瀷
    print(f"寮€濮嬭缁冨绔嬫．鏋楁ā鍨?..")
    isof_model = IsolationForestModel(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=42,
    )
    
    # 璁粌妯″瀷
    isof_model.fit(scaled_features)
    
    # 璁＄畻璁粌闆嗕笂鐨勫紓甯稿垎鏁?
    anomaly_scores = isof_model.get_anomaly_score(scaled_features)
    
    # 璁＄畻鍒嗕綅鏁伴槇鍊?
    threshold = np.percentile(anomaly_scores, quantile_level * 100)
    
    # 杈撳嚭寮傚父鍒嗘暟缁熻淇℃伅
    print(f"璁粌闆嗗紓甯稿垎鏁扮粺璁?")
    print(f"  鏈€灏忓€? {np.min(anomaly_scores):.4f}")
    print(f"  鏈€澶у€? {np.max(anomaly_scores):.4f}")
    print(f"  鍧囧€? {np.mean(anomaly_scores):.4f}")
    print(f"  鏍囧噯宸? {np.std(anomaly_scores):.4f}")
    print(f"  {quantile_level*100}%鍒嗕綅鏁? {threshold:.4f}")
    
    # 淇濆瓨閰嶇疆淇℃伅
    windows_config = {
        "window_size": window_size,
        "step": step,
    }
    
    # 淇濆瓨妯″瀷
    if save_path is None:
        save_path = BASE_DIR / "strategy2" / "models" / cmg_type / "isof_model.pkl"
    
    save_model(
        isof_model,
        save_path,
        anomaly_threshold=threshold,
        windows_config=windows_config,
    )
    
    return isof_model, threshold

if __name__ == "__main__":
    print(f"==>> BASE_DIR: {BASE_DIR}")
    cmg_type = "500NM"
    csvs = [BASE_DIR / "鏁版嵁澶勭悊" / cmg_type / "data.csv"]
    
    # 妫€娴嬬紪鐮?
    encodings = []
    for csv in csvs:
        with open(csv, 'rb') as f:
            result = chardet.detect(f.readline())
            print(result)
            encodings.append(result['encoding'])
    print(encodings)
    
    # 璇诲彇鏁版嵁
    dfs = [pd.read_csv(csv, encoding=enc) for csv, enc in zip(csvs, encodings)]
    data_df = pd.concat(dfs, ignore_index=True)
    
    # 鑾峰彇PHM绫诲瀷瀵瑰簲鐨勭洰鏍囧垪
    cmg_target_cols = PHM_TYPE_COL_NAME_MAP.get(cmg_type, None)
    if cmg_target_cols is None:
        raise ValueError(f"鏈煡鐨刢mg_type: {cmg_type}锛屾棤娉曡幏鍙栧搴旂殑鍒楀悕锛岃妫€鏌ワ紒")
    
    # 璁粌妯″瀷
    train_isolation_forest_model(
        data_df,
        cmg_target_cols=cmg_target_cols,
        cmg_type=cmg_type,
        window_size=64,  # 鍗曚竴绐楀彛澶у皬
        step=32,  # 绐楀彛婊戝姩姝ラ暱
        n_estimators=100,
        quantile_level=0.99,
    )
