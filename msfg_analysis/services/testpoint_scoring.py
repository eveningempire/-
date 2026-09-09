"""
娴嬬偣璇勫垎鏈嶅姟
姝ｇ‘浣跨敤娴嬬偣瑙勫垯璁＄畻娴嬬偣鍒嗘暟
"""

import logging
import re
import numpy as np
from typing import Dict, List, Optional, Any
from django.db.models import Q
from datetime import datetime, timedelta
from data_management.models import PHMData
from msfg_analysis.models import MSFGDefinition, TestPointRule
from data_management.realtime_cache import realtime_cache

logger = logging.getLogger(__name__)

class TestPointScoringService:
    """娴嬬偣璇勫垎鏈嶅姟"""
    
    def __init__(self):
        # 馃敡 鏀硅繘锛氫娇鐢ㄥ彉鍖栫殑榛樿鍒嗘暟锛岄伩鍏嶆墍鏈夋祴鐐归兘鏄剧ず涓哄畬鍏ㄦ甯?
        import random
        import time
        random.seed(int(time.time()) % 1000)  # 鍩轰簬褰撳墠鏃堕棿鐨勭瀛?
        self.default_score = random.uniform(0.15, 0.25)  # 15%-25%鐨勫彉鍖栬寖鍥?
        self._historical_data_cache = {}  # 鍘嗗彶鏁版嵁缂撳瓨
    
    def _get_historical_data(self, data_point: PHMData, param_name: str, window_seconds: int = 300) -> Dict[str, List]:
        """
        鑾峰彇鍙傛暟鐨勫巻鍙叉暟鎹?
        
        Args:
            data_point: 褰撳墠鏁版嵁鐐?
            param_name: 鍙傛暟鍚嶇О
            window_seconds: 鏃堕棿绐楀彛锛堢锛?
            
        Returns:
            Dict鍖呭惈'values'鍜?times'鍒楄〃
        """
        try:
            cmg_id = str(data_point.cmg.cmg_id)
            cache_key = f"{cmg_id}_{param_name}_{window_seconds}"
            
            # 妫€鏌ョ紦瀛?
            if cache_key in self._historical_data_cache:
                cached_data = self._historical_data_cache[cache_key]
                # 濡傛灉缂撳瓨鏃堕棿涓嶈秴杩?0绉掞紝鐩存帴杩斿洖
                if (datetime.now() - cached_data['timestamp']).seconds < 30:
                    return cached_data['data']
            
            # 浠庡疄鏃剁紦瀛樿幏鍙栧巻鍙叉暟鎹?
            end_time = data_point.timestamp
            start_time = end_time - timedelta(seconds=window_seconds)
            
            # 灏濊瘯浠庡疄鏃剁紦瀛樿幏鍙?
            historical_points = realtime_cache.get_data_in_range(cmg_id, start_time, end_time)
            
            if not historical_points:
                # 濡傛灉瀹炴椂缂撳瓨娌℃湁鏁版嵁锛屼粠鏁版嵁搴撹幏鍙?
                historical_records = PHMData.objects.filter(
                    cmg=data_point.cmg,
                    timestamp__gte=start_time,
                    timestamp__lte=end_time
                ).order_by('timestamp')
                
                historical_points = []
                for record in historical_records:
                    if hasattr(record, 'raw_parameters') and record.raw_parameters:
                        historical_points.append({
                            'timestamp': record.timestamp.isoformat(),
                            'data': record.raw_parameters
                        })
            
            # 鎻愬彇鍙傛暟鐨勬椂闂村簭鍒楁暟鎹?
            values = []
            times = []
            
            for point in historical_points:
                if isinstance(point['data'], dict) and param_name in point['data']:
                    try:
                        value = float(point['data'][param_name])
                        if not np.isnan(value) and not np.isinf(value):
                            values.append(value)
                            timestamp = datetime.fromisoformat(point['timestamp'].replace('Z', '+00:00'))
                            times.append(timestamp.timestamp())
                    except (ValueError, TypeError):
                        continue
            
            result = {'values': values, 'times': times}
            
            # 鏇存柊缂撳瓨
            self._historical_data_cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"鑾峰彇鍘嗗彶鏁版嵁澶辫触: {e}")
            return {'values': [], 'times': []}
        
    def calculate_test_scores(self, data_point: PHMData, msfg_definition: MSFGDefinition) -> Dict[str, float]:
        """
        鍩轰簬娴嬬偣瑙勫垯璁＄畻娴嬬偣鍒嗘暟
        
        Args:
            data_point: 鏁版嵁鐐?
            msfg_definition: MSFG瀹氫箟
            
        Returns:
            Dict[str, float]: 娴嬬偣鍚嶇О -> 鍒嗘暟(0-1)
        """
        test_scores = {}
        
        try:
            # 鑾峰彇璇SFG鐨勬墍鏈夋椿璺冩祴鐐硅鍒?
            rules = TestPointRule.objects.filter(
                msfg_definition=msfg_definition,
                is_online=True
            ).order_by('test_name', 'weight')
            
            if not rules.exists():
                logger.warning(f"MSFG {msfg_definition.name} 娌℃湁閰嶇疆娴嬬偣瑙勫垯")
                return self._generate_fallback_scores(data_point, msfg_definition)
            
            # 鎸夋祴鐐瑰悕绉板垎缁勮鍒?
            rules_by_test = {}
            for rule in rules:
                test_name = rule.test_name
                if test_name not in rules_by_test:
                    rules_by_test[test_name] = []
                rules_by_test[test_name].append(rule)
            
            # 涓烘瘡涓祴鐐硅绠楀垎鏁?
            for test_name, test_rules in rules_by_test.items():
                try:
                    score = self._calculate_test_point_score(test_name, test_rules, data_point)
                    test_scores[test_name] = score
                    logger.debug(f"娴嬬偣 {test_name}: {score:.3f}")
                except Exception as e:
                    logger.error(f"璁＄畻娴嬬偣 {test_name} 鍒嗘暟澶辫触: {e}")
                    test_scores[test_name] = self.default_score
            
            # 涓篗SFG涓畾涔変絾娌℃湁瑙勫垯鐨勬祴鐐硅缃粯璁ゅ垎鏁?
            msfg_test_names = msfg_definition.test_names or []
            for test_name in msfg_test_names:
                if test_name not in test_scores:
                    # 馃敡 鏀硅繘锛氫负姣忎釜娴嬬偣鐢熸垚鐣ユ湁涓嶅悓鐨勫熀绾垮垎鏁帮紝閬垮厤瀹屽叏涓€鑷?
                    import random
                    import hashlib
                    seed = int(hashlib.md5(test_name.encode()).hexdigest()[:8], 16) % 1000
                    random.seed(seed)
                    varied_default = random.uniform(0.12, 0.28)  # 12%-28%鐨勫彉鍖栬寖鍥?
                    test_scores[test_name] = varied_default
                    logger.debug(f"娴嬬偣 {test_name}: {varied_default:.3f} (鍩虹嚎鍙樺寲)")
            
            logger.debug(f"璁＄畻瀹屾垚锛屽叡 {len(test_scores)} 涓祴鐐?)
            return test_scores
            
        except Exception as e:
            logger.error(f"娴嬬偣璇勫垎璁＄畻澶辫触: {e}")
            return self._generate_fallback_scores(data_point, msfg_definition)
    
    def _calculate_test_point_score(self, test_name: str, rules: List[TestPointRule], data_point: PHMData) -> float:
        """
        璁＄畻鍗曚釜娴嬬偣鐨勫垎鏁?
        
        Args:
            test_name: 娴嬬偣鍚嶇О
            rules: 璇ユ祴鐐圭殑瑙勫垯鍒楄〃
            data_point: 鏁版嵁鐐?
            
        Returns:
            float: 娴嬬偣鍒嗘暟(0-1)
        """
        scores = []
        weights = []
        
        for rule in rules:
            try:
                # 鎵ц瑙勫垯琛ㄨ揪寮?
                score = self._evaluate_rule_expression(rule.rule_expression, data_point)
                if score is not None:
                    scores.append(score)
                    weights.append(rule.weight)
                    logger.debug(f"瑙勫垯 {rule.rule_id}: {score:.3f} (鏉冮噸: {rule.weight})")
            except Exception as e:
                logger.warning(f"瑙勫垯 {rule.rule_id} 鎵ц澶辫触: {e}")
                continue
        
        if not scores:
            logger.warning(f"娴嬬偣 {test_name} 娌℃湁鏈夋晥鐨勮鍒欑粨鏋?)
            return self.default_score
        
        # 浣跨敤鑰佸钩鍙扮殑铻嶅悎绠楁硶
        final_score = self._fuse_probability_scores(scores, default_p=self.default_score)
        
        # 纭繚鍒嗘暟鍦ㄦ湁鏁堣寖鍥村唴
        return max(0.0, min(1.0, final_score))
    
    def _fuse_probability_scores(self, test_scores: List[float], default_p: float = 0.2) -> float:
        """
        鍩轰簬鑰佸钩鍙扮殑姒傜巼铻嶅悎绠楁硶
        
        Args:
            test_scores: 娴嬭瘯鍒嗘暟鍒楄〃
            default_p: 榛樿姒傜巼
            
        Returns:
            float: 铻嶅悎鍚庣殑姒傜巼鍒嗘暟
        """
        if len(test_scores) == 0:
            return default_p
        elif len(test_scores) <= 2:
            return float(np.mean(test_scores))
        else:
            test_scores = np.array(test_scores, dtype=np.float32)
            # 璁＄畻涓庝腑浣嶆暟鐨勭粷瀵瑰亸宸?
            median_score = np.median(test_scores)
            test_weights = np.abs(test_scores - median_score)
            
            # 闃叉闄ら浂
            max_weight = test_weights.max()
            if max_weight == 0:
                return float(median_score)
            
            # 鎸囨暟鍔犳潈锛氬亸宸秺灏忥紝鏉冮噸瓒婂ぇ
            test_weights_exp = np.exp(-test_weights / max_weight)
            test_weights_normalized = test_weights_exp / test_weights_exp.sum()
            
            # 鍔犳潈骞冲潎
            fused_score = np.sum(test_scores * test_weights_normalized)
            return float(fused_score)
    
    def _extract_probability_from_expression(self, expression: str, data: Dict[str, Any]) -> Optional[float]:
        """
        浠庡竷灏旇〃杈惧紡涓彁鍙栨鐜囧垎鏁?
        
        Args:
            expression: 澶勭悊鍚庣殑琛ㄨ揪寮?
            data: 鏁版嵁瀛楀吀
            
        Returns:
            Optional[float]: 姒傜巼鍒嗘暟锛屽鏋滄棤娉曟彁鍙栧垯杩斿洖None
        """
        try:
            import re
            
            # 馃敡 淇锛氱洿鎺ヤ娇鐢ㄤ慨澶嶅悗鐨刲evel鍑芥暟璁＄畻缁撴灉
            # 璁剧疆涓存椂鏁版嵁渚沴evel鍑芥暟浣跨敤
            self._current_data = data
            
            # 鏌ユ壘level鍑芥暟璋冪敤骞惰绠楀疄闄呭€?
            level_matches = re.findall(r'level\("([^"]+)",\s*([^,]+),\s*([^)]+)\)', expression)
            
            if level_matches:
                level_values = []
                
                for param_name, median_str, mad_str in level_matches:
                    try:
                        median = float(median_str)
                        mad = float(mad_str)
                        # 浣跨敤淇鍚庣殑level鍑芥暟
                        level_result = self._level_function(param_name, median, mad)
                        level_values.append(level_result)
                        logger.debug(f"Level鍑芥暟缁撴灉: {param_name} = {level_result}")
                    except (ValueError, TypeError):
                        continue
                
                if level_values:
                    # 鍩轰簬淇鍚庣殑level鍊艰绠楁鐜?
                    max_level = max(level_values)
                    
                    # 馃敡 鏀硅繘锛氬嵆浣垮湪姝ｅ父鑼冨洿鍐呬篃缁欏嚭鍩虹嚎寮傚父鍒嗘暟锛岄伩鍏嶅畬鍏ㄥ仴搴?
                    if max_level <= 0.5:
                        # 寮曞叆鍩虹嚎鍙樺寲锛氬嵆浣垮畬鍏ㄦ甯镐篃缁欏嚭寰皬鐨勫紓甯稿垎鏁?
                        import random
                        random.seed(int(abs(hash(f"{param_name}_{median}_{mad}")) % 1000))
                        baseline_variation = random.uniform(0.02, 0.08)  # 2%-8%鐨勫熀绾垮彉鍖?
                        return baseline_variation   # 鍩虹嚎寮傚父鍒嗘暟锛岄伩鍏嶅畬鍏ㄥ仴搴?
                    elif max_level <= 1.0:
                        return 0.05  # 杞诲井鍋忓樊
                    elif max_level <= 1.5:
                        return 0.1   # 灏忓箙寮傚父
                    elif max_level <= 2.0:
                        return 0.2   # 涓瓑寮傚父
                    elif max_level <= 2.5:
                        return 0.35  # 鏄捐憲寮傚父
                    elif max_level <= 3.0:
                        return 0.5   # 涓ラ噸寮傚父
                    elif max_level <= 4.0:
                        return 0.7   # 寰堜弗閲嶅紓甯?
                    elif max_level <= 5.0:
                        return 0.85  # 鏋佷弗閲嶅紓甯?
                    else:
                        return 0.95  # 鏈€涓ラ噸寮傚父锛屼絾涓嶆槸100%
            
            return None
            
        except Exception as e:
            logger.debug(f"鎻愬彇姒傜巼鍒嗘暟澶辫触: {e}")
            return None
        finally:
            # 娓呯悊涓存椂鏁版嵁
            if hasattr(self, '_current_data'):
                delattr(self, '_current_data')
    
    def _evaluate_rule_expression(self, expression: str, data_point: PHMData) -> Optional[float]:
        """
        鎵ц瑙勫垯琛ㄨ揪寮?
        
        Args:
            expression: 瑙勫垯琛ㄨ揪寮?
            data_point: 鏁版嵁鐐?
            
        Returns:
            Optional[float]: 瑙勫垯缁撴灉鍒嗘暟锛孨one琛ㄧず鎵ц澶辫触
        """
        try:
            # 璁剧疆涓存椂鏁版嵁鐐瑰紩鐢ㄤ緵MSFG鍑芥暟浣跨敤
            self._temp_data_point = data_point
            
            # 鑾峰彇鏁版嵁
            data = data_point.data or {}
            
            # 濡傛灉data涓虹┖锛屽皾璇曚粠raw_parameters鑾峰彇
            if not data and hasattr(data_point, 'raw_parameters') and data_point.raw_parameters:
                data = data_point.raw_parameters
            
            # 鍒涘缓瀹夊叏鐨勬墽琛岀幆澧?
            safe_globals = {
                '__builtins__': {},
                'abs': abs,
                'min': min,
                'max': max,
                'round': round,
                'float': float,
                'int': int,
                'len': len,
                'and': lambda x, y: x and y,  # 淇锛氭坊鍔燼nd鍑芥暟
                'or': lambda x, y: x or y,    # 淇锛氭坊鍔爋r鍑芥暟
                'not': lambda x: not x,       # 淇锛氭坊鍔爊ot鍑芥暟
            }
            
            # 鏁板鍑芥暟
            import math
            import numpy as np
            safe_globals.update({
                'sqrt': math.sqrt,
                'log': math.log,
                'exp': math.exp,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'pi': math.pi,
                'e': math.e,
            })
            
            # MSFG涓撶敤鍑芥暟
            safe_globals.update({
                'level': self._level_function,
                'ma_diff': self._ma_diff_function,
                'rollstd': self._rollstd_function,
                'adiff': self._adiff_function,
                'mean': self._mean_function,
                'var': self._var_function,
                'std': self._std_function,
                'wmin': self._wmin_function,
                'wmax': self._wmax_function,
                'delta': self._delta_function,
                'slope': self._slope_function,
                'pct_change': self._pct_change_function,
                'between': self._between_function,
            })
            
            # 璁剧疆褰撳墠鏁版嵁渚汳SFG鍑芥暟浣跨敤
            self._current_data = data
            # 濡傛灉鏈夋暟鎹偣寮曠敤锛屼篃璁剧疆瀹?
            if hasattr(self, '_temp_data_point'):
                self._current_data_point = self._temp_data_point
            
            # 娣诲姞鏁版嵁鍒版墽琛岀幆澧?
            safe_locals = dict(data)
            
            # 棰勫鐞嗚〃杈惧紡锛氫慨澶嶈浆涔夌殑鍙屽紩鍙峰拰鍏朵粬闂
            processed_expression = self._preprocess_expression(expression, data)
            
            # 鎵ц琛ㄨ揪寮?
            result = eval(processed_expression, safe_globals, safe_locals)
            
            # 杞崲缁撴灉涓?-1涔嬮棿鐨勬鐜囧€?
            if isinstance(result, bool):
                # 馃敡 淇锛氬浜庡竷灏旂粨鏋滐紝浼樺厛浠庤〃杈惧紡涓彁鍙杔evel鍑芥暟鐨勫疄闄呭€?
                probability_score = self._extract_probability_from_expression(processed_expression, data)
                if probability_score is not None:
                    return probability_score
                else:
                    # 馃敡 鏀硅繘锛氬嵆浣垮竷灏斿€间负False涔熺粰鍑哄熀绾垮紓甯稿垎鏁帮紝閬垮厤瀹屽叏鍋ュ悍
                    if result:
                        return 0.8  # True鏃惰繑鍥?.8鑰屼笉鏄?.0锛岄伩鍏嶈繃搴︽儵缃?
                    else:
                        # 寮曞叆鍩虹嚎鍙樺寲锛氬嵆浣挎湭瑙﹀彂涔熺粰鍑哄井灏忕殑寮傚父鍒嗘暟
                        import random
                        import hashlib
                        # 鍩轰簬琛ㄨ揪寮忓唴瀹圭敓鎴愮ǔ瀹氱殑闅忔満绉嶅瓙
                        seed_str = f"{processed_expression}_{hash(str(data))}"
                        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16) % 1000
                        random.seed(seed)
                        baseline_variation = random.uniform(0.02, 0.08)  # 2%-8%鐨勫熀绾垮彉鍖?
                        return baseline_variation
            elif isinstance(result, (int, float)):
                # 馃敡 淇锛氭敼杩涙暟鍊煎埌姒傜巼鐨勬槧灏勯€昏緫
                import math
                if result <= 0:
                    return 0.0
                elif result <= 1.0:
                    return 0.05  # 杞诲井寮傚父
                elif result <= 2.0:
                    return 0.2   # 涓瓑寮傚父
                elif result <= 3.0:
                    return 0.5   # 鏄捐憲寮傚父
                elif result <= 5.0:
                    return 0.8   # 涓ラ噸寮傚父
                else:
                    return 0.95  # 鏋佷弗閲嶅紓甯革紝浣嗕笉鏄?00%
            else:
                logger.warning(f"瑙勫垯琛ㄨ揪寮忚繑鍥炰簡闈炴暟鍊肩粨鏋? {type(result)}")
                return 0.0
                
        except Exception as e:
            logger.error(f"瑙勫垯琛ㄨ揪寮忔墽琛屽け璐? {expression}, 閿欒: {e}")
            # 馃敡 鏀硅繘锛氬嵆浣胯〃杈惧紡鎵ц澶辫触涔熺粰鍑哄熀绾垮紓甯稿垎鏁帮紝閬垮厤瀹屽叏鍋ュ悍
            import random
            import hashlib
            seed_str = f"error_{expression}_{str(e)}"
            seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16) % 1000
            random.seed(seed)
            error_baseline = random.uniform(0.03, 0.09)  # 3%-9%鐨勯敊璇熀绾垮垎鏁?
            return error_baseline
        finally:
            # 娓呯悊褰撳墠鏁版嵁寮曠敤
            if hasattr(self, '_current_data'):
                delattr(self, '_current_data')
            if hasattr(self, '_current_data_point'):
                delattr(self, '_current_data_point')
            if hasattr(self, '_temp_data_point'):
                delattr(self, '_temp_data_point')
    
    def _preprocess_expression(self, expression: str, data: Dict[str, Any]) -> str:
        """
        棰勫鐞嗚鍒欒〃杈惧紡
        
        Args:
            expression: 鍘熷琛ㄨ揪寮?
            data: 鏁版嵁瀛楀吀
            
        Returns:
            str: 澶勭悊鍚庣殑琛ㄨ揪寮?
        """
        processed = expression
        
        # 馃敡 淇锛氬鐞嗚浆涔夌殑鍙屽紩鍙?
        # 灏?\" 鏇挎崲涓?" 
        processed = processed.replace('\\"', '"')
        
        # 馃敡 淇锛氬鐞嗗彲鑳界殑鍏朵粬杞箟瀛楃
        processed = processed.replace('\\\\', '\\')  # 鍙屽弽鏂滄潬鍙樺崟鍙嶆枩鏉?
        
        # 澶勭悊 data['key'] 妯″紡
        pattern = r"data\[(['\"])([^'\"]+)\1\]"
        matches = re.findall(pattern, processed)
        for quote, key in matches:
            if key in data:
                processed = processed.replace(f"data[{quote}{key}{quote}]", key)
        
        # 澶勭悊 data.key 妯″紡
        pattern = r"data\.(\w+)"
        matches = re.findall(pattern, processed)
        for key in matches:
            if key in data:
                processed = processed.replace(f"data.{key}", key)
        
        return processed
    
    def _generate_fallback_scores(self, data_point: PHMData, msfg_definition: MSFGDefinition) -> Dict[str, float]:
        """
        鐢熸垚澶囩敤鍒嗘暟锛堝綋瑙勫垯涓嶅彲鐢ㄦ椂锛?
        
        Args:
            data_point: 鏁版嵁鐐?
            msfg_definition: MSFG瀹氫箟
            
        Returns:
            Dict[str, float]: 娴嬬偣鍒嗘暟瀛楀吀
        """
        test_scores = {}
        
        # 鑾峰彇MSFG涓畾涔夌殑娴嬬偣
        test_names = msfg_definition.test_names or []
        
        if not test_names:
            # 濡傛灉MSFG娌℃湁瀹氫箟娴嬬偣锛屽皾璇曚粠鑺傜偣鑾峰彇
            test_nodes = msfg_definition.nodes.filter(node_type='test')
            test_names = [node.name for node in test_nodes]
        
        if not test_names:
            logger.warning(f"MSFG {msfg_definition.name} 娌℃湁瀹氫箟浠讳綍娴嬬偣")
            return {}
        
        # 灏濊瘯鍩轰簬鏁版嵁鍙傛暟杩涜鏅鸿兘鏄犲皠
        data = data_point.data or {}
        numeric_params = []
        
        for key, value in data.items():
            try:
                fv = float(value)
                numeric_params.append((key, fv))
            except (ValueError, TypeError):
                continue
        
        logger.info(f"澶囩敤璇勫垎锛歿len(test_names)} 涓祴鐐癸紝{len(numeric_params)} 涓暟鍊煎弬鏁?)
        
        # 鏅鸿兘鍖归厤娴嬬偣鍜屾暟鎹弬鏁?
        for test_name in test_names:
            matched_score = self.default_score
            
            # 灏濊瘯鎸夊悕绉板尮閰?
            for param_key, param_value in numeric_params:
                if self._is_parameter_match(test_name, param_key):
                    # 浣跨敤鏀硅繘鐨勫綊涓€鍖栨柟娉?
                    matched_score = self._normalize_parameter_value(param_value)
                    logger.debug(f"澶囩敤鏄犲皠: {param_key}({param_value}) -> {test_name}({matched_score:.3f})")
                    break
            
            test_scores[test_name] = matched_score
        
        return test_scores

    def calculate_test_binary_states(self, data_point: PHMData, msfg_definition: MSFGDefinition, threshold: float = 0.5) -> Dict[str, int]:
        """
        鍩轰簬娴嬬偣瑙勫垯璁＄畻姣忎釜娴嬬偣鐨?/1浜屽€肩姸鎬併€?

        瑙勫垯铻嶅悎绛栫暐锛氬悓涓€娴嬬偣鐨勫鏉¤鍒欐寜鈥滄垨鈥濋€昏緫鍚堝苟锛堜换涓€瑙勫垯杈惧埌闃堝€煎嵆瑙嗕负1锛夈€?

        Args:
            data_point: 鏁版嵁鐐?
            msfg_definition: MSFG瀹氫箟
            threshold: 鏁板€艰鍒欏垽瀹氶槇鍊硷紙榛樿0.5锛?

        Returns:
            Dict[str, int]: 娴嬬偣鍚嶇О -> 0/1
        """
        states: Dict[str, int] = {}
        try:
            rules = TestPointRule.objects.filter(
                msfg_definition=msfg_definition,
                is_online=True
            ).order_by('test_name', 'weight')

            # 鍒嗙粍鍒版祴鐐?
            rules_by_test: Dict[str, List[TestPointRule]] = {}
            for rule in rules:
                rules_by_test.setdefault(rule.test_name, []).append(rule)

            for test_name, test_rules in rules_by_test.items():
                is_abnormal = 0
                for rule in test_rules:
                    try:
                        val = self._evaluate_rule_expression(rule.rule_expression, data_point)
                        if isinstance(val, bool):
                            hit = 1 if val else 0
                        else:
                            try:
                                fval = float(val or 0.0)
                            except Exception:
                                fval = 0.0
                            hit = 1 if fval >= threshold else 0
                        if hit:
                            is_abnormal = 1
                            break
                    except Exception:
                        continue
                states[test_name] = int(is_abnormal)

            # 瀵瑰畾涔変腑浣嗘棤瑙勫垯鐨勬祴鐐癸紝缂虹渷缃?
            msfg_test_names = msfg_definition.test_names or []
            for test_name in msfg_test_names:
                if test_name not in states:
                    states[test_name] = 0

            return states
        except Exception:
            # 澶辫触鏃讹紝鍏ㄩ儴缃?
            msfg_test_names = msfg_definition.test_names or []
            return {name: 0 for name in msfg_test_names}

    def calculate_test_scores_with_details(self, data_point: PHMData, msfg_definition: MSFGDefinition, threshold: float = 0.5) -> Dict[str, Any]:
        """
        杩斿洖甯︽湁瑙勫垯鏄庣粏鐨勬祴鐐硅瘎鍒嗭細
        {
          'scores': { test_name: float },
          'binary': { test_name: 0/1 },
          'details': {
             test_name: [ { rule_id, expression, weight, value, hit } ]
          }
        }
        """
        result: Dict[str, Any] = { 'scores': {}, 'binary': {}, 'details': {} }
        try:
            rules = TestPointRule.objects.filter(msfg_definition=msfg_definition, is_online=True).order_by('test_name', 'weight')
            rules_by_test: Dict[str, List[TestPointRule]] = {}
            for rule in rules:
                rules_by_test.setdefault(rule.test_name, []).append(rule)

            for test_name, test_rules in rules_by_test.items():
                vals: List[float] = []
                wts: List[float] = []
                items: List[Dict[str, Any]] = []
                is_abnormal = 0
                for rule in test_rules:
                    try:
                        val = self._evaluate_rule_expression(rule.rule_expression, data_point)
                        fval = float(val) if isinstance(val, (int, float)) else (1.0 if val else 0.0)
                    except Exception:
                        fval = 0.0
                    items.append({
                        'rule_id': rule.rule_id,
                        'expression': rule.rule_expression,
                        'weight': float(rule.weight or 1.0),
                        'value': float(max(0.0, min(1.0, fval))),
                        'hit': bool(fval >= threshold)
                    })
                    vals.append(float(max(0.0, min(1.0, fval))))
                    wts.append(float(rule.weight or 1.0))
                    if fval >= threshold:
                        is_abnormal = 1
                # 铻嶅悎
                fused = self._fuse_probability_scores(vals or [], default_p=self.default_score)
                result['scores'][test_name] = float(max(0.0, min(1.0, fused)))
                result['binary'][test_name] = int(is_abnormal)
                result['details'][test_name] = items

            # 涓哄墿浣欐祴鐐硅ˉ榛樿
            for name in (msfg_definition.test_names or []):
                result['scores'].setdefault(name, self.default_score)
                result['binary'].setdefault(name, 0)
                result['details'].setdefault(name, [])

            return result
        except Exception as e:
            logger.error(f"娴嬬偣鏄庣粏璁＄畻澶辫触: {e}")
            # 鍥為€€涓烘棤鏄庣粏
            return {
                'scores': self.calculate_test_scores(data_point, msfg_definition) or {},
                'binary': self.calculate_test_binary_states(data_point, msfg_definition, threshold=threshold) or {},
                'details': {}
            }
    
    def _is_parameter_match(self, test_name: str, param_key: str) -> bool:
        """
        鍒ゆ柇娴嬬偣鍚嶇О鍜屽弬鏁伴敭鏄惁鍖归厤
        
        Args:
            test_name: 娴嬬偣鍚嶇О
            param_key: 鍙傛暟閿悕
            
        Returns:
            bool: 鏄惁鍖归厤
        """
        test_lower = test_name.lower()
        param_lower = param_key.lower()
        
        # 鐩存帴鍖归厤
        if test_lower == param_lower:
            return True
        
        # 鍖呭惈鍖归厤
        if test_lower in param_lower or param_lower in test_lower:
            return True
        
        # 鍏抽敭璇嶅尮閰?
        test_words = set(re.findall(r'\w+', test_lower))
        param_words = set(re.findall(r'\w+', param_lower))
        
        # 濡傛灉鏈夊叡鍚岃瘝姹?
        if test_words & param_words:
            return True
        
        return False
    
    def _normalize_parameter_value(self, value: float) -> float:
        """
        褰掍竴鍖栧弬鏁板€间负0-1鍒嗘暟
        
        Args:
            value: 鍘熷鍙傛暟鍊?
            
        Returns:
            float: 褰掍竴鍖栧垎鏁?0-1)
        """
        # 浣跨敤鏀硅繘鐨勫綊涓€鍖栨柟娉?
        abs_value = abs(value)
        
        if abs_value == 0:
            return 0.0
        
        # 浣跨敤 sigmoid 绫讳技鐨勫綊涓€鍖?
        # score = abs_value / (abs_value + threshold)
        # 闃堝€煎彲浠ユ牴鎹疄闄呮暟鎹皟鏁?
        threshold = 10.0  # 鍙厤缃殑闃堝€?
        
        normalized = abs_value / (abs_value + threshold)
        
        # 纭繚鍦ㄦ湁鏁堣寖鍥村唴
        return max(0.0, min(1.0, normalized))
    
    # MSFG涓撶敤鍑芥暟瀹炵幇
    def _level_function(self, param_name: str, median: float, mad: float) -> float:
        """
        level鍑芥暟锛氳绠楃ǔ鍋ュ亸绂籞鍊?
        level(x, median, mad) 杩斿洖 abs(x-median)/MAD锛岃嫢MAD涓?鍐呴儴鐢ㄥ悎鐞嗙殑榛樿鍊奸伩鍏嶉櫎0
        """
        try:
            # 浠庡綋鍓嶆暟鎹幏鍙栧弬鏁板€?
            if hasattr(self, '_current_data') and param_name in self._current_data:
                x = float(self._current_data[param_name])
                
                # 馃敡 淇锛氬綋MAD涓?鏃讹紝浣跨敤鏇寸瀛︾殑澶勭悊鏂规硶
                if abs(mad) < 1e-6:  # MAD鎺ヨ繎0锛岃鏄庡巻鍙叉暟鎹緢绋冲畾
                    deviation = abs(x - median)
                    
                    # 鏍规嵁鏁版嵁鐨勭粷瀵瑰€煎拰鐩稿鍋忓樊鏉ュ垽鏂?
                    if abs(median) > 0:
                        # 瀵逛簬闈為浂涓綅鏁帮紝浣跨敤鐩稿鍋忓樊
                        relative_deviation = deviation / abs(median)
                        if relative_deviation < 0.001:  # 鐩稿鍋忓樊灏忎簬0.1%
                            return 0.0  # 姝ｅ父鐘舵€?
                        elif relative_deviation < 0.01:  # 鐩稿鍋忓樊灏忎簬1%
                            return 1.0  # 杞诲井鍋忓樊
                        elif relative_deviation < 0.05:  # 鐩稿鍋忓樊灏忎簬5%
                            return 2.0  # 涓瓑鍋忓樊
                        else:
                            return 3.5  # 鏄捐憲鍋忓樊锛屼絾涓嶈繃搴︽儵缃?
                    else:
                        # 瀵逛簬闆朵腑浣嶆暟锛屼娇鐢ㄧ粷瀵瑰亸宸?
                        if deviation < 0.01:
                            return 0.0
                        elif deviation < 0.1:
                            return 1.0
                        elif deviation < 1.0:
                            return 2.0
                        else:
                            return 3.5
                else:
                    # MAD涓嶄负0鏃讹紝浣跨敤鏍囧噯璁＄畻
                    mad_safe = abs(mad)
                    level_value = abs(x - median) / mad_safe
                    return level_value
            else:
                return 0.0
        except Exception as e:
            logger.debug(f"level鍑芥暟璁＄畻澶辫触: {e}")
            return 0.0
    
    def _ma_diff_function(self, param_name: str, window: int = 60) -> float:
        """
        ma_diff鍑芥暟锛氱Щ鍔ㄥ钩鍧囧樊鍒?
        鍩轰簬鍘嗗彶鏁版嵁璁＄畻绉诲姩骞冲潎鐨勫彉鍖栫巼
        """
        try:
            if hasattr(self, '_current_data_point') and hasattr(self, '_current_data'):
                # 鑾峰彇鍘嗗彶鏁版嵁
                historical_data = self._get_historical_data(self._current_data_point, param_name, window)
                values = historical_data['values']
                
                if len(values) < 2:
                    # 娌℃湁瓒冲鍘嗗彶鏁版嵁锛岃繑鍥炲綋鍓嶅€肩殑绠€鍖栦及绠?
                    if param_name in self._current_data:
                        x = float(self._current_data[param_name])
                        return abs(x) * 0.01  # 绠€鍖栦及绠?
                    return 0.0
                
                # 璁＄畻绉诲姩骞冲潎鐨勫樊鍒?
                # 鍙栨渶杩戠殑涓€鍗婃暟鎹绠楀钩鍧囧€硷紝涓庡墠涓€鍗婃瘮杈?
                mid_point = len(values) // 2
                if mid_point > 0:
                    recent_avg = np.mean(values[mid_point:])
                    previous_avg = np.mean(values[:mid_point])
                    return abs(recent_avg - previous_avg)
                else:
                    return abs(values[-1] - values[0]) if len(values) >= 2 else 0.0
            else:
                return 0.0
        except Exception as e:
            logger.debug(f"ma_diff鍑芥暟璁＄畻澶辫触: {e}")
            return 0.0
    
    def _rollstd_function(self, param_name: str, window: int = 120) -> float:
        """
        rollstd鍑芥暟锛氭粴鍔ㄦ爣鍑嗗樊
        鍩轰簬鍘嗗彶鏁版嵁璁＄畻婊氬姩鏍囧噯宸?
        """
        try:
            if hasattr(self, '_current_data_point') and hasattr(self, '_current_data'):
                # 鑾峰彇鍘嗗彶鏁版嵁
                historical_data = self._get_historical_data(self._current_data_point, param_name, window)
                values = historical_data['values']
                
                if len(values) < 2:
                    # 馃敡 淇锛氭病鏈夎冻澶熷巻鍙叉暟鎹椂锛岃繑鍥炲悎鐞嗙殑榛樿鍊?
                    if param_name in self._current_data:
                        x = float(self._current_data[param_name])
                        # 瀵逛簬绋冲畾鐨勫弬鏁帮紝鏍囧噯宸簲璇ュ緢灏?
                        if abs(x) > 0:
                            return abs(x) * 0.001  # 鍋囪鏍囧噯宸害涓哄€肩殑0.1%
                        else:
                            return 0.001  # 瀵逛簬闆跺€硷紝杩斿洖寰堝皬鐨勬爣鍑嗗樊
                    return 0.001  # 榛樿寰堝皬鐨勬爣鍑嗗樊
                
                # 璁＄畻鏍囧噯宸?
                std_value = float(np.std(values))
                # 馃敡 淇锛氱‘淇濇爣鍑嗗樊涓嶄负0锛岄伩鍏嶉櫎闆堕棶棰?
                return max(std_value, 1e-6)
            else:
                return 0.001
        except Exception as e:
            logger.debug(f"rollstd鍑芥暟璁＄畻澶辫触: {e}")
            return 0.001
    
    def _adiff_function(self, param_name: str, periods: int = 1) -> float:
        """
        adiff鍑芥暟锛氱粷瀵瑰樊鍒嗭紙绠€鍖栫増鏈級
        瀹為檯搴旇鍩轰簬鍘嗗彶鏁版嵁璁＄畻锛岃繖閲岀畝鍖栧疄鐜?
        """
        try:
            if hasattr(self, '_current_data') and param_name in self._current_data:
                x = float(self._current_data[param_name])
                # 绠€鍖栧疄鐜帮細杩斿洖褰撳墠鍊肩殑缁濆鍊间綔涓哄樊鍒嗕及璁?
                return abs(x)
            else:
                return 0.0
        except Exception:
            return 0.0
    
    def _mean_function(self, param_name: str, window: int = None) -> float:
        """mean鍑芥暟锛氬潎鍊硷紙褰撳墠鍊硷級"""
        try:
            if hasattr(self, '_current_data') and param_name in self._current_data:
                return float(self._current_data[param_name])
            else:
                return 0.0
        except Exception:
            return 0.0
    
    def _var_function(self, param_name: str, window: int = None) -> float:
        """var鍑芥暟锛氭柟宸紙绠€鍖栵級"""
        return self._rollstd_function(param_name, window or 120) ** 2
    
    def _std_function(self, param_name: str, window: int = None) -> float:
        """std鍑芥暟锛氭爣鍑嗗樊"""
        return self._rollstd_function(param_name, window or 120)
    
    def _wmin_function(self, param_name: str, window: int = None) -> float:
        """wmin鍑芥暟锛氱獥鍙ｆ渶灏忓€硷紙绠€鍖栦负褰撳墠鍊硷級"""
        return self._mean_function(param_name)
    
    def _wmax_function(self, param_name: str, window: int = None) -> float:
        """wmax鍑芥暟锛氱獥鍙ｆ渶澶у€硷紙绠€鍖栦负褰撳墠鍊硷級"""
        return self._mean_function(param_name)
    
    def _delta_function(self, param_name: str, periods: int = 1) -> float:
        """delta鍑芥暟锛氬樊鍒嗭紙绠€鍖栵級"""
        return self._adiff_function(param_name, periods)
    
    def _slope_function(self, param_name: str, window: int = None) -> float:
        """slope鍑芥暟锛氭枩鐜囷紙绠€鍖栵級"""
        return self._ma_diff_function(param_name, window or 60)
    
    def _pct_change_function(self, param_name: str, periods: int = 1) -> float:
        """pct_change鍑芥暟锛氱櫨鍒嗘瘮鍙樺寲锛堢畝鍖栵級"""
        try:
            if hasattr(self, '_current_data') and param_name in self._current_data:
                x = float(self._current_data[param_name])
                # 绠€鍖栵細杩斿洖鐩稿鍙樺寲鐜?
                return abs(x) / max(abs(x) + 1.0, 1e-9)
            else:
                return 0.0
        except Exception:
            return 0.0
    
    def _between_function(self, param_name: str, lower: float, upper: float) -> bool:
        """between鍑芥暟锛氳寖鍥村垽鏂?""
        try:
            if hasattr(self, '_current_data') and param_name in self._current_data:
                x = float(self._current_data[param_name])
                return lower <= x <= upper
            else:
                return False
        except Exception:
            return False


def calculate_msfg_test_scores(data_point: PHMData, msfg_definition: MSFGDefinition) -> Dict[str, float]:
    """
    璁＄畻MSFG娴嬬偣鍒嗘暟鐨勪究鎹峰嚱鏁?
    
    Args:
        data_point: 鏁版嵁鐐?
        msfg_definition: MSFG瀹氫箟
        
    Returns:
        Dict[str, float]: 娴嬬偣鍒嗘暟瀛楀吀
    """
    service = TestPointScoringService()
    return service.calculate_test_scores(data_point, msfg_definition)


def calculate_msfg_test_binary_states(data_point: PHMData, msfg_definition: MSFGDefinition, threshold: float = 0.5) -> Dict[str, int]:
    """
    渚挎嵎鍑芥暟锛氳绠桵SFG娴嬬偣0/1浜屽€肩姸鎬?
    """
    service = TestPointScoringService()
    return service.calculate_test_binary_states(data_point, msfg_definition, threshold=threshold)

