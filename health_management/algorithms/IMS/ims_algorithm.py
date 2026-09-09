"""
IMS (Isolation Forest based Multi-variate Streaming) 绠楁硶瀹炵幇
鍩轰簬闅旂妫灄鐨勫鍏冩祦寮忓紓甯告娴嬬畻娉?
"""

import json
import base64
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from .BaseAlgoClass import BaseModel


class IMSModel(BaseModel):
    """IMS寮傚父妫€娴嬬畻娉曟ā鍨?""
    
    def __init__(self, index=0, name="IMS", pnames=[], component=None, config={}):
        # 璁剧疆绠楁硶鍩烘湰淇℃伅
        self._zh_name = "IMS澶氬厓娴佸紡寮傚父妫€娴?
        self._algoType = "IMS"
        self._component = component or "PHM"
        self._faultLevel = 1
        
        # 榛樿閰嶇疆
        default_config = {
            "contamination": 0.1,        # 寮傚父姣斾緥
            "n_estimators": 100,         # 闅旂鏍戞暟閲?
            "max_samples": "auto",       # 姣忔５鏍戠殑鏍锋湰鏁?
            "max_features": 1.0,         # 姣忔５鏍戠殑鐗瑰緛鏁?
            "bootstrap": False,          # 鏄惁鑷姪閲囨牱
            "random_state": 42,          # 闅忔満绉嶅瓙
            "threshold": 0.5,            # 寮傚父闃堝€?
            "scaler_type": "standard"    # 鏍囧噯鍖栫被鍨?
        }
        default_config.update(config)
        
        super().__init__(index, name, pnames, component, default_config)
        
        # IMS鐗瑰畾灞炴€?
        self.isolation_forest = None
        self.scaler = None
        self.feature_importance = None
        self.normal_scores = None
        self.threshold_value = None
        
    def to_json(self):
        """搴忓垪鍖栨ā鍨嬪弬鏁?""
        model_data = {
            "config": self.config,
            "pnames": self.pnames,
            "trained": bool(self.trained),
            "mins": self.mins.tolist() if hasattr(self, 'mins') else None,
            "maxs": self.maxs.tolist() if hasattr(self, 'maxs') else None,
            "id_const": self.id_const.tolist() if hasattr(self, 'id_const') else None,
            "id_nonconst": self.id_nonconst.tolist() if hasattr(self, 'id_nonconst') else None,
            "threshold_value": float(self.threshold_value) if self.threshold_value is not None else None,
            "feature_importance": self.feature_importance.tolist() if self.feature_importance is not None else None,
            "min_train_score": float(self.min_train_score) if getattr(self, 'min_train_score', None) is not None else None,
            "max_train_score": float(self.max_train_score) if getattr(self, 'max_train_score', None) is not None else None
        }
        
        # 搴忓垪鍖栭殧绂绘．鏋楁ā鍨嬶紙瀹屾暣瀵硅薄锛?
        if self.isolation_forest is not None:
            try:
                blob = pickle.dumps(self.isolation_forest)
                model_data["isolation_forest_blob"] = base64.b64encode(blob).decode("ascii")
            except Exception:
                pass
        
        # 搴忓垪鍖栨爣鍑嗗寲鍣紙瀹屾暣瀵硅薄锛?
        if self.scaler is not None:
            try:
                sblob = pickle.dumps(self.scaler)
                model_data["scaler_blob"] = base64.b64encode(sblob).decode("ascii")
            except Exception:
                pass
        
        return json.dumps(model_data, ensure_ascii=False, default=self._json_serializer).encode('utf-8')
    
    def _json_serializer(self, obj):
        """JSON搴忓垪鍖栬緟鍔╂柟娉曪紝澶勭悊numpy绫诲瀷"""
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, (np.integer, int)):
            return int(obj)
        if isinstance(obj, (np.floating, float)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def from_json(self, config_bytes):
        """鍙嶅簭鍒楀寲妯″瀷鍙傛暟"""
        model_data = json.loads(config_bytes.decode('utf-8'))
        
        self.config = model_data.get("config", {})
        self.pnames = model_data.get("pnames", [])
        self.trained = bool(model_data.get("trained", False))
        self.threshold_value = model_data.get("threshold_value")
        
        # 鎭㈠璁粌鍒嗘暟鑼冨洿
        self.min_train_score = model_data.get("min_train_score")
        self.max_train_score = model_data.get("max_train_score")
        
        # 鎭㈠褰掍竴鍖栧弬鏁?
        if model_data.get("mins") is not None:
            self.mins = np.array(model_data["mins"])
            self.maxs = np.array(model_data["maxs"])
            self.id_const = np.array(model_data["id_const"])
            self.id_nonconst = np.array(model_data["id_nonconst"])
        
        # 鎭㈠鐗瑰緛閲嶈鎬?
        if model_data.get("feature_importance") is not None:
            self.feature_importance = np.array(model_data["feature_importance"])
        
        # 鎭㈠闅旂妫灄妯″瀷锛堜紭鍏堜粠瀹屾暣瀵硅薄锛?
        if model_data.get("isolation_forest_blob") is not None:
            try:
                blob = base64.b64decode(model_data["isolation_forest_blob"])  # type: ignore[arg-type]
                self.isolation_forest = pickle.loads(blob)
            except Exception:
                self.isolation_forest = None
        elif model_data.get("isolation_forest") is not None:
            # 鍏煎鏃х増鏈細浠呰秴鍙傛暟锛屾敞鎰忔璺緞鍙兘缂哄皯鍐呴儴灞炴€?
            iso_data = model_data["isolation_forest"]
            try:
                self.isolation_forest = IsolationForest(
                    contamination=iso_data["contamination"],
                    n_estimators=iso_data["n_estimators"],
                    max_samples=iso_data["max_samples"],
                    max_features=iso_data["max_features"],
                    bootstrap=iso_data["bootstrap"],
                    random_state=iso_data["random_state"]
                )
            except Exception:
                self.isolation_forest = None
        
        # 鎭㈠鏍囧噯鍖栧櫒锛堜紭鍏堜粠瀹屾暣瀵硅薄锛?
        if model_data.get("scaler_blob") is not None:
            try:
                sblob = base64.b64decode(model_data["scaler_blob"])  # type: ignore[arg-type]
                self.scaler = pickle.loads(sblob)
            except Exception:
                self.scaler = None
        elif model_data.get("scaler") is not None:
            # 鍏煎鏃х増鏈細鎵嬪姩鎭㈠缁熻閲?
            scaler_data = model_data["scaler"]
            try:
                self.scaler = StandardScaler()
                if scaler_data.get("mean_") is not None:
                    self.scaler.mean_ = np.array(scaler_data["mean_"])
                    self.scaler.scale_ = np.array(scaler_data["scale_"])
                    self.scaler.var_ = np.array(scaler_data["var_"])
                    self.scaler.n_features_in_ = len(self.scaler.mean_)
            except Exception:
                self.scaler = None
    
    def fit(self, data, save=True):
        """璁粌IMS妯″瀷"""
        print(f"寮€濮嬭缁僆MS妯″瀷锛屾暟鎹舰鐘? {data.shape}")
        
        # 璋冪敤鐖剁被鐨勫熀纭€璁粌娴佺▼
        super().fit(data, save=False)
        
        # 绉婚櫎鍖呭惈NaN鐨勮
        clean_data = data[~np.isnan(data).any(axis=1)]
        if len(clean_data) == 0:
            raise ValueError("璁粌鏁版嵁鍏ㄩ儴涓篘aN")
        
        print(f"娓呯悊鍚庢暟鎹舰鐘? {clean_data.shape}")
        
        # 鏍囧噯鍖栨暟鎹?
        if self.config.get("scaler_type") == "standard":
            self.scaler = StandardScaler()
            normalized_data = self.scaler.fit_transform(clean_data)
        else:
            # 浣跨敤鐖剁被鐨勫綊涓€鍖栨柟娉?
            normalized_data = self.normalization(clean_data.copy())
        
        # 璁粌闅旂妫灄
        self.isolation_forest = IsolationForest(
            contamination=self.config.get("contamination", 0.1),
            n_estimators=self.config.get("n_estimators", 100),
            max_samples=self.config.get("max_samples", "auto"),
            max_features=self.config.get("max_features", 1.0),
            bootstrap=self.config.get("bootstrap", False),
            random_state=self.config.get("random_state", 42),
            n_jobs=-1
        )
        
        self.isolation_forest.fit(normalized_data)
        
        # 璁＄畻璁粌鏁版嵁鐨勫紓甯稿垎鏁?
        train_scores = self.isolation_forest.decision_function(normalized_data)
        self.normal_scores = train_scores
        # 淇濆瓨璁粌鍒嗘暟鑼冨洿鐢ㄤ簬褰掍竴鍖?
        try:
            self.min_train_score = float(np.min(train_scores))
            self.max_train_score = float(np.max(train_scores))
        except Exception:
            self.min_train_score = None
            self.max_train_score = None
        
        # 璁＄畻闃堝€?
        self.threshold_value = np.percentile(train_scores, 
                                          (1 - self.config.get("contamination", 0.1)) * 100)
        
        # 璁＄畻鐗瑰緛閲嶈鎬э紙鍩轰簬鏂瑰樊锛?
        self.feature_importance = np.var(normalized_data, axis=0)
        self.feature_importance = self.feature_importance / np.sum(self.feature_importance)
        
        print(f"妯″瀷璁粌瀹屾垚锛岄槇鍊? {self.threshold_value:.4f}")
        print(f"鐗瑰緛閲嶈鎬? {dict(zip(self.pnames, self.feature_importance))}")
        
        # 鏇存柊璁粌鐘舵€?
        self.trained = True
        
        if save:
            self.save_model()
        
        return True
    
    def _predict_single(self, data_frame):
        """瀵瑰崟涓暟鎹抚杩涜棰勬祴"""
        if not self.trained or self.isolation_forest is None:
            raise ValueError("妯″瀷灏氭湭璁粌")
        
        # 纭繚鏁版嵁鏍煎紡姝ｇ‘
        if isinstance(data_frame, dict):
            # 鎸夌収璁粌鏃剁殑鍙傛暟椤哄簭鎻愬彇鏁版嵁
            data_array = np.array([data_frame.get(pname, np.nan) for pname in self.pnames]).reshape(1, -1)
            #print(f"DEBUG: 杈撳叆鍙傛暟 {list(data_frame.keys())}")
            #print(f"DEBUG: 妯″瀷鍙傛暟 {self.pnames}")
            #print(f"DEBUG: 鏁版嵁褰㈢姸 {data_array.shape}")
        else:
            data_array = np.array(data_frame).reshape(1, -1)
            
        # 妫€鏌ョ淮搴﹀尮閰?
        if data_array.shape[1] != len(self.pnames):
            raise ValueError(f"杈撳叆鏁版嵁缁村害({data_array.shape[1]})涓庢ā鍨嬭缁冪淮搴?{len(self.pnames)})涓嶅尮閰?)
        
        # 妫€鏌ユ暟鎹湁鏁堟€?
        if np.isnan(data_array).all():
            return 0.0, {pname: 0.0 for pname in self.pnames}, False
        
        # 鏁版嵁棰勫鐞?
        if self.scaler is not None:
            # 澶勭悊NaN鍊?
            data_clean = data_array.copy()
            nan_mask = np.isnan(data_clean)
            if nan_mask.any():
                # 鐢ㄨ缁冩椂鐨勫潎鍊煎～鍏匩aN
                data_clean[nan_mask] = self.scaler.mean_[nan_mask[0]]
            
            normalized_data = self.scaler.transform(data_clean)
        else:
            # 浣跨敤鐖剁被鐨勫綊涓€鍖栨柟娉?
            data_clean = data_array.copy()
            nan_mask = np.isnan(data_clean)
            if nan_mask.any():
                # 鐢ㄤ腑浣嶆暟濉厖NaN
                data_clean[nan_mask] = (self.mins + self.maxs)[nan_mask[0]] / 2
            
            normalized_data = self.normalization(data_clean)
        
        # 寮傚父妫€娴?
        anomaly_score = self.isolation_forest.decision_function(normalized_data)[0]
        is_anomaly = anomaly_score < self.threshold_value
        
        # 璁＄畻鍚勫弬鏁扮殑寮傚父鍒嗘暟
        parameter_scores = {}
        if len(self.pnames) == len(data_array[0]):
            # 璁＄畻姣忎釜鍙傛暟瀵瑰紓甯哥殑璐＄尞
            base_score = anomaly_score
            for i, pname in enumerate(self.pnames):
                if not np.isnan(data_array[0, i]):
                    # 鍩轰簬鐗瑰緛閲嶈鎬у拰鍋忕绋嬪害璁＄畻鍙傛暟寮傚父鍒嗘暟
                    feature_weight = self.feature_importance[i] if self.feature_importance is not None else 1.0
                    deviation = abs(normalized_data[0, i])
                    param_score = feature_weight * deviation * (1 if is_anomaly else 0.5)
                    parameter_scores[pname] = float(param_score)
                else:
                    parameter_scores[pname] = 0.0
        
        # 灏嗗紓甯稿垎鏁拌浆鎹负0-1鑼冨洿锛堜娇鐢ㄨ缁冩椂鐨勬渶灏忓垎鏁颁綔涓哄弬鑰冿級
        if getattr(self, "min_train_score", None) is not None and self.threshold_value is not None:
            denom = float(self.threshold_value) - float(self.min_train_score)
            if abs(denom) < 1e-9:
                denom = 1.0
            normalized_score = (float(self.threshold_value) - float(anomaly_score)) / denom
            normalized_score = max(0.0, min(1.0, normalized_score))
        else:
            # 閫€鍖栭€昏緫锛氱己灏戣缁冨弬鑰冩椂锛屼粎缁欏嚭浜屽€煎寲寰楀垎
            normalized_score = 1.0 if is_anomaly else 0.0
        
        return float(normalized_score), parameter_scores, bool(is_anomaly)
    
    def singleValidate(self, dataFrames):
        """鍗曞抚鍦ㄧ嚎妫€娴?""
        if len(dataFrames) == 0:
            return 0.0, None, None
        
        # 浣跨敤鏈€鍚庝竴甯ф暟鎹繘琛屾娴?
        last_frame = dataFrames[-1]
        score, param_scores, is_anomaly = self._predict_single(last_frame)
        
        return score, None, None
    
    def validate(self, dataFrames):
        """鎵归噺绂荤嚎妫€娴?""
        if not self.trained:
            raise ValueError("妯″瀷灏氭湭璁粌")
        
        scores = []
        anomaly_list = []
        
        for i, frame in enumerate(dataFrames):
            score, _, is_anomaly = self._predict_single(frame)
            scores.append(score)
            if is_anomaly:
                anomaly_list.append(i)
        
        return anomaly_list, scores, [None, None]
    
    def onlineValidate(self, dataFrame, time_):
        """鍦ㄧ嚎妫€娴嬫帴鍙?""
        if not self.trained:
            return {
                "detectType": self._algoType,
                "result": {
                    "state": False,
                    "score": 0.0,
                    "histAnom": False,
                    "lastAnomTime": -1,
                    "component": self._component,
                    "faultLevel": self._faultLevel,
                    "parameter_scores": {},
                    "addLine": [None, None]
                }
            }
        
        # 鏇存柊鏁版嵁缂撳瓨
        self.dataStockRefresh(dataFrame, time_)
        
        # 杩涜妫€娴?
        score, parameter_scores, is_anomaly = self._predict_single(dataFrame)
        
        if is_anomaly:
            self._histAnom = True
            self._lastAnomTime = time_
        
        return {
            "detectType": self._algoType,
            "result": {
                "state": bool(is_anomaly),
                "score": float(score),
                "histAnom": bool(self._histAnom),
                "lastAnomTime": self._lastAnomTime,
                "component": self._component,
                "faultLevel": self._faultLevel,
                "parameter_scores": parameter_scores,
                "addLine": [None, None]
            }
        }


def create_ims_model(pnames, config=None):
    """鍒涘缓IMS妯″瀷鐨勫伐鍘傚嚱鏁?""
    default_config = {
        "contamination": 0.1,
        "n_estimators": 100,
        "max_samples": "auto",
        "max_features": 1.0,
        "bootstrap": False,
        "random_state": 42,
        "threshold": 0.5,
        "scaler_type": "standard"
    }
    
    if config:
        default_config.update(config)
    
    return IMSModel(
        index=1,
        name="IMS",
        pnames=pnames,
        component="PHM",
        config=default_config
    )

