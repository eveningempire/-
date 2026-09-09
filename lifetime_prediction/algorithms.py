"""
瀵垮懡棰勬祴绠楁硶妯″潡

璇ユā鍧楀寘鍚鍛介娴嬬殑鏍稿績绠楁硶閫昏緫锛屽寘鎷暟鎹澶勭悊銆佺壒寰佹彁鍙栧拰RUL棰勬祴銆?
浣跨敤Predictor.predict_batch绫昏繘琛屽疄闄呯殑瀵垮懡棰勬祴銆?
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
import sys
import os

# 瀵煎叆鏂扮増rul_predict妯″潡涓殑Predictor
from .rul_predict_250917_v2.predict_v3 import Predictor
# 瀵煎叆涓変釜绛栫暐绠楁硶
from .rul_predict_250917_v2.strategy1.predict_v3 import Predictor as Strategy1Predictor
from .rul_predict_250917_v2.strategy2.predict_v3 import Predictor as Strategy2Predictor
from .rul_predict_250917_v2.strategy3.predict_v3 import Predictor as Strategy3Predictor

logger = logging.getLogger(__name__)

# 绠楁硶閫夋嫨甯搁噺
ALGORITHM_CHOICES = {
    'strategy0': {
        'name': '鑷紪鐮佸櫒缃戠粶3sigma绠楁硶',
        'description': '鍩轰簬鑷紪鐮佸櫒鐨勫紓甯告娴嬬畻娉曪紝浣跨敤3sigma瑙勫垯杩涜鍋ュ悍鎸囨暟璁＄畻',
        'predictor_class': Predictor
    },
    'strategy1': {
        'name': '鍙樺垎鐢熸垚缃戠粶鍥涘垎浣嶈窛绠楁硶', 
        'description': '鍩轰簬鍙樺垎鑷紪鐮佸櫒(VAE)鐨勭敓鎴愭ā鍨嬶紝浣跨敤鍥涘垎浣嶈窛杩涜寮傚父妫€娴?,
        'predictor_class': Strategy1Predictor
    },
    'strategy2': {
        'name': '瀛ょ珛妫灄鑱氬悎妯″瀷鍔ㄦ€侀槇鍊肩畻娉?,
        'description': '鍩轰簬瀛ょ珛妫灄鐨勫紓甯告娴嬫ā鍨嬶紝浣跨敤鍔ㄦ€侀槇鍊艰繘琛屽仴搴疯瘎浼?,
        'predictor_class': Strategy2Predictor
    },
    'strategy3': {
        'name': '鑷粍缁囨槧灏勭綉缁滈┈姘忚窛绂荤畻娉?,
        'description': '鍩轰簬鑷粍缁囨槧灏?SOM)缃戠粶锛屼娇鐢ㄩ┈姘忚窛绂昏繘琛屽仴搴锋寚鏁拌绠?,
        'predictor_class': Strategy3Predictor
    }
}

def get_available_algorithms():
    """鑾峰彇鍙敤鐨勭畻娉曞垪琛?""
    return [
        {
            'key': key,
            'name': info['name'],
            'description': info['description']
        }
        for key, info in ALGORITHM_CHOICES.items()
    ]


class LifetimePredictionAlgorithm:
    """瀵垮懡棰勬祴绠楁硶鍩虹被"""
    
    def __init__(self, window_size: int = 64):
        self.window_size = window_size
        # 鏂扮畻娉曚細鏍规嵁PHM绫诲瀷鑷姩澶勭悊瀛楁鏄犲皠锛屾棤闇€棰勫畾涔塺equired_telemetry
    
    def _parse_timestamp_flexible(self, timestamp_str: str):
        """
        鐏垫椿瑙ｆ瀽鏃堕棿鎴冲瓧绗︿覆锛屾敮鎸佸绉嶆牸寮?
        
        Args:
            timestamp_str: 鏃堕棿鎴冲瓧绗︿覆
            
        Returns:
            pandas.Timestamp: 瑙ｆ瀽鍚庣殑鏃堕棿鎴?
        """
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

    def validate_data(self, data: List[Dict]) -> bool:
        """楠岃瘉杈撳叆鏁版嵁鐨勬湁鏁堟€э紙鏂扮増绠楁硶浼氳嚜鍔ㄥ鐞嗛仴娴嬮噺瀛楁鏄犲皠锛?""
        if len(data) < self.window_size:
            logger.warning(f"鏁版嵁闀垮害涓嶈冻: {len(data)} < {self.window_size}")
            return False
        
        # 妫€鏌ュ熀鏈暟鎹粨鏋?
        if not data:
            return False
            
        # 妫€鏌ユ暟鎹褰曟槸鍚﹀寘鍚玠ata瀛楁
        first_record = data[0]
        if 'data' not in first_record or not first_record['data']:
            logger.warning("鏁版嵁璁板綍缂哄皯data瀛楁鎴杁ata涓虹┖")
            return False
        
        return True
    
    def extract_features(self, data: List[Dict]) -> np.ndarray:
        """浠庣獥鍙ｆ暟鎹腑鎻愬彇鐗瑰緛"""
        if not self.validate_data(data):
            raise ValueError("杈撳叆鏁版嵁楠岃瘉澶辫触")
        
        # 鎻愬彇鏈€杩戠殑window_size鏉¤褰?
        window_data = data[-self.window_size:]
        
        # 鏋勫缓鐗瑰緛鐭╅樀
        features = []
        for record in window_data:
            record_features = []
            for telemetry in self.required_telemetry:
                value = record['data'].get(telemetry, 0.0)
                record_features.append(float(value))
            features.append(record_features)
        
        return np.array(features)
    
    def predict_rul(self, features: np.ndarray) -> Tuple[float, float]:
        """
        棰勬祴RUL鍊?
        
        Args:
            features: 鐗瑰緛鐭╅樀锛屽舰鐘朵负 (window_size, n_features)
            
        Returns:
            rul_value: RUL棰勬祴鍊?
            confidence: 棰勬祴缃俊搴?
        """
        # 绠€鍗曠殑鐗瑰緛缁熻浣滀负鍗犱綅绗︾畻娉?
        # 瀹為檯搴旂敤涓繖閲屽簲璇ヤ娇鐢ㄨ缁冨ソ鐨勬満鍣ㄥ涔犳ā鍨?
        
        # 璁＄畻姣忎釜閬ユ祴閲忕殑缁熻鐗瑰緛
        mean_values = np.mean(features, axis=0)
        std_values = np.std(features, axis=0)
        max_values = np.max(features, axis=0)
        min_values = np.min(features, axis=0)
        
        # 绠€鍗曠殑RUL璁＄畻閫昏緫锛堢ず渚嬶級
        # 鍩轰簬鐢靛帇鍜岀數娴佺殑绋冲畾鎬ф潵浼扮畻鍓╀綑瀵垮懡
        voltage_stability = 1.0 / (1.0 + std_values[0])  # 鐢靛帇绋冲畾鎬?
        current_stability = 1.0 / (1.0 + std_values[1])  # 鐢垫祦绋冲畾鎬?
        
        # 鍩轰簬鐢靛帇鍜岀數娴佺殑骞冲潎鍊?
        voltage_factor = max(0.1, min(1.0, mean_values[0] / 100.0))  # 鐢靛帇鍥犲瓙
        current_factor = max(0.1, min(1.0, mean_values[1] / 10.0))   # 鐢垫祦鍥犲瓙
        
        # 璁＄畻RUL鍊硷紙灏忔椂涓哄崟浣嶏級
        base_rul = 1000.0  # 鍩虹瀵垮懡1000灏忔椂
        rul_value = base_rul * voltage_stability * current_stability * voltage_factor * current_factor
        
        # 璁＄畻缃俊搴︼紙鍩轰簬鏁版嵁璐ㄩ噺锛?
        data_quality = np.mean([voltage_stability, current_stability])
        confidence = min(0.95, max(0.5, data_quality))
        
        return rul_value, confidence
    
    def predict(self, data: List[Dict], design_life: float, start_time: str, cmg_model_name: str = "500NM", algorithm: str = "strategy0") -> Dict:
        """
        鎵ц瀹屾暣鐨勫鍛介娴嬫祦绋?
        
        Args:
            data: 鍘熷鏁版嵁鍒楄〃
            design_life: 璁捐瀵垮懡锛堝勾锛?
            start_time: 寮€濮嬭瘯鐢ㄦ椂闂达紙YYYY/MM/DD HH:mm:ss鏍煎紡锛?
            cmg_model_name: PHM鍨嬪彿鍚嶇О锛岀敤浜庨€夋嫨瀵瑰簲鐨勯娴嬫ā鍨?
            algorithm: 绠楁硶閫夋嫨锛坰trategy0/strategy1/strategy2/strategy3锛?
            
        Returns:
            棰勬祴缁撴灉瀛楀吀
        """
        try:
            # 娣诲姞鍙傛暟杩借釜鏃ュ織
            logger.info(f"[鍙傛暟杩借釜] Algorithm灞傛帴鏀跺埌鐨勫弬鏁?- design_life: {design_life} (绫诲瀷: {type(design_life)}), start_time: {start_time}, cmg_model_name: {cmg_model_name}, algorithm: {algorithm}")
            
            # 楠岃瘉绠楁硶閫夋嫨
            if algorithm not in ALGORITHM_CHOICES:
                logger.warning(f"鏈煡鐨勭畻娉曢€夋嫨: {algorithm}锛屼娇鐢ㄩ粯璁ょ畻娉?strategy0")
                algorithm = "strategy0"
            
            # 鑾峰彇瀵瑰簲鐨勯娴嬪櫒绫?
            predictor_class = ALGORITHM_CHOICES[algorithm]['predictor_class']
            algorithm_name = ALGORITHM_CHOICES[algorithm]['name']
            logger.info(f"浣跨敤绠楁硶: {algorithm_name}")
            
            # 澶勭悊寮€濮嬭瘯鐢ㄦ椂闂达紝濡傛灉鐢ㄦ埛鏈～鍐欑簿鍑嗙殑灏忔椂鍒嗙锛岃嚜鍔ㄨˉ鍏ㄤ负01:01:01
            if start_time:
                if len(start_time.split(' ')) == 1:  # 鍙湁鏃ユ湡锛屾病鏈夋椂闂?
                    start_time = f"{start_time} 01:01:01"
                elif len(start_time.split(' ')[1].split(':')) < 3:  # 鏃堕棿涓嶅畬鏁?
                    time_part = start_time.split(' ')[1]
                    if len(time_part.split(':')) == 2:  # 鍙湁灏忔椂鍜屽垎閽?
                        start_time = f"{start_time.split(' ')[0]} {time_part}:01"
                    elif len(time_part.split(':')) == 1:  # 鍙湁灏忔椂
                        start_time = f"{start_time.split(' ')[0]} {time_part}:01:01"
                
                # 纭繚鏃堕棿鏍煎紡鏍囧噯鍖栵紝娣诲姞鏃跺尯淇℃伅
                if 'T' in start_time:
                    # 宸茬粡鏄疘SO鏍煎紡锛岀‘淇濇湁鏃跺尯淇℃伅
                    if not (start_time.endswith('Z') or '+' in start_time or '-' in start_time[-6:]):
                        start_time = start_time.replace(' ', 'T') + '+00:00'
                else:
                    # 杞崲涓篒SO鏍煎紡
                    start_time = start_time.replace(' ', 'T') + '+00:00'
            
            # 灏嗘暟鎹浆鎹负DataFrame鏍煎紡锛堣鏂扮畻娉曡嚜鍔ㄥ鐞嗗瓧娈垫槧灏勶級
            df_data = []
            time_stamps = []
            
            for record in data:
                record_data = record.get('data', {})
                # 鐩存帴浣跨敤鍘熷鏁版嵁锛岃鏂扮畻娉曡嚜鍔ㄥ鐞嗗瓧娈垫槧灏勫拰璁＄畻
                df_data.append(record_data)
                
                # 澶勭悊鏃堕棿鎴虫牸寮?- 鏀寔澶氱鏍煎紡鐨勬櫤鑳借В鏋?
                timestamp = record.get('timestamp', '')
                if isinstance(timestamp, str):
                    # 濡傛灉鏄瓧绗︿覆锛屽皾璇曞绉嶆牸寮忚В鏋?
                    try:
                        parsed_time = self._parse_timestamp_flexible(timestamp)
                        time_stamps.append(parsed_time)
                    except Exception as e:
                        logger.warning(f"鏃堕棿鎴宠В鏋愬け璐? {timestamp}, 閿欒: {e}")
                        # 浣跨敤褰撳墠鏃堕棿浣滀负榛樿鍊?
                        time_stamps.append(pd.Timestamp.now())
                else:
                    # 濡傛灉宸茬粡鏄痙atetime瀵硅薄锛岀洿鎺ヤ娇鐢?
                    time_stamps.append(timestamp)
            
            # 鍒涘缓DataFrame锛堝寘鍚墍鏈夊師濮嬮仴娴嬫暟鎹級
            batch_data_df = pd.DataFrame(df_data)
            time_stamps_series = pd.Series(time_stamps)
            
            # 浣跨敤閫夋嫨鐨勭畻娉曡繘琛岄娴?
            logger.info(f"寮€濮嬩娇鐢▄algorithm_name}杩涜棰勬祴锛孋MG鍨嬪彿: {cmg_model_name}")
            
            # 妫€娴嬫椂闂存牸寮忥紝鏅鸿兘閫夋嫨鍚堥€傜殑time_fmt
            sample_timestamp = str(time_stamps_series.iloc[0]) if len(time_stamps_series) > 0 else ""
            if 'T' in sample_timestamp:
                # ISO鏍煎紡鏃堕棿锛屼娇鐢╝uto鏍煎紡璁﹑andas鑷姩瑙ｆ瀽
                time_fmt_to_use = "auto"  # 璁﹑redict_v3浣跨敤鏅鸿兘瑙ｆ瀽
                logger.info(f"妫€娴嬪埌ISO鏍煎紡鏃堕棿鎴? {sample_timestamp}锛屼娇鐢ㄨ嚜鍔ㄨВ鏋愭ā寮?)
            else:
                # 浼犵粺鏍煎紡鏃堕棿
                time_fmt_to_use = "%Y/%m/%d %H:%M:%S"
                logger.info(f"妫€娴嬪埌浼犵粺鏍煎紡鏃堕棿鎴? {sample_timestamp}锛屼娇鐢ㄦ爣鍑嗘牸寮?)
            
            logger.info(f"[鍙傛暟杩借釜] 浼犻€掔粰{algorithm}绠楁硶鐨勫弬鏁?- time_start_use: {start_time}, design_life: {design_life}, time_fmt: {time_fmt_to_use}")
            logger.info(f"[鏃堕棿鎴充俊鎭痌 瑙ｆ瀽浜?{len(time_stamps)} 涓椂闂存埑锛岀ず渚? {sample_timestamp}")
            
            # 鏍规嵁娴嬭瘯鏂囦欢涓殑鏍囧噯璋冪敤鏂瑰紡锛屾墍鏈夌畻娉曢兘浣跨敤鐩稿悓鐨勫熀纭€鍙傛暟
            # 鍚勭畻娉曚細鏍规嵁鑷繁鐨勫疄鐜拌嚜鍔ㄥ鐞嗗弬鏁板樊寮?
            rul_pred, hi_sequence, hi_high, hi_low = predictor_class.predict_batch(
                cmg_type=cmg_model_name,
                time_start_use=start_time,
                time_stamps=time_stamps_series,
                design_life=design_life,
                batch_data_df=batch_data_df,
                time_fmt=time_fmt_to_use
            )
            
            # 鏋勫缓缁撴灉 - 鍖呭惈RUL鍊笺€佸仴搴疯秼鍔垮簭鍒楀拰缃俊鍖洪棿
            result = {
                'rul_value': round(rul_pred, 2),  # 绠楁硶杩斿洖鐨勫墿浣欎娇鐢ㄥ鍛?
                'hi_sequence': hi_sequence.tolist() if hasattr(hi_sequence, 'tolist') else list(hi_sequence),  # 鍋ュ悍瓒嬪娍搴忓垪
                'confidence_upper': hi_high.tolist() if hasattr(hi_high, 'tolist') else list(hi_high),  # 缃俊鍖洪棿涓婄晫
                'confidence_lower': hi_low.tolist() if hasattr(hi_low, 'tolist') else list(hi_low),   # 缃俊鍖洪棿涓嬬晫
                'prediction_time': datetime.now().isoformat(),  # 棰勬祴鎵ц鏃堕棿
                'design_life': design_life,  # 鐢ㄦ埛杈撳叆鐨勮璁″鍛?
                'start_time': start_time,  # 鐢ㄦ埛杈撳叆鐨勫紑濮嬫椂闂?
                'algorithm_version': 'v2.0',  # 鏍囪绠楁硶鐗堟湰
                'algorithm': algorithm,  # 浣跨敤鐨勭畻娉曟爣璇?
                'algorithm_name': algorithm_name,  # 浣跨敤鐨勭畻娉曞悕绉?
                'status': 'success'
            }
            
            logger.info(f"瀵垮懡棰勬祴瀹屾垚: RUL={rul_pred:.2f}, 璁捐瀵垮懡={design_life}骞? 寮€濮嬫椂闂?{start_time}")
            return result
            
        except Exception as e:
            logger.error(f"瀵垮懡棰勬祴澶辫触: {str(e)}")
            return {
                'rul_value': 0.0,
                'prediction_time': datetime.now().isoformat(),
                'error': str(e),
                'status': 'error'
            }


class AdvancedLifetimePredictionAlgorithm(LifetimePredictionAlgorithm):
    """楂樼骇瀵垮懡棰勬祴绠楁硶锛堥鐣欐帴鍙ｏ級"""
    
    def __init__(self, model_path: Optional[str] = None, window_size: int = 64):
        super().__init__(window_size)
        self.model_path = model_path
        self.model = None
        
    def load_model(self, model_path: str):
        """鍔犺浇棰勮缁冩ā鍨嬶紙棰勭暀鎺ュ彛锛?""
        # 杩欓噷鍙互鍔犺浇瀹為檯鐨勬満鍣ㄥ涔犳ā鍨?
        # 渚嬪锛歴elf.model = joblib.load(model_path)
        logger.info(f"鍔犺浇妯″瀷: {model_path}")
        
    def predict_rul(self, features: np.ndarray) -> Tuple[float, float]:
        """浣跨敤鍔犺浇鐨勬ā鍨嬭繘琛岄娴嬶紙棰勭暀鎺ュ彛锛?""
        if self.model is not None:
            # 浣跨敤瀹為檯妯″瀷杩涜棰勬祴
            # rul_value = self.model.predict(features.reshape(1, -1))[0]
            pass
        
        # 鍥為€€鍒板熀纭€绠楁硶
        return super().predict_rul(features)

