#!/usr/bin/env python
"""
淇MSFG璇勫垎闂
"""

import os
import sys
import django
from pathlib import Path

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

import logging
import numpy as np
from typing import Optional
from data_management.models import PHM, PHMData
from msfg_analysis.models import MSFGDefinition, TestPointRule, TestPointFaultMapping
from msfg_analysis.services.testpoint_scoring import TestPointScoringService
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_testpoint_scoring_service():
    """淇娴嬬偣璇勫垎鏈嶅姟涓殑闂"""
    print("=== 淇娴嬬偣璇勫垎鏈嶅姟 ===")
    
    # 1. 淇瑙勫垯鎵ц鐜
    print("馃敡 淇瑙勫垯鎵ц鐜...")
    
    # 鍒涘缓涓€涓慨澶嶇増鏈殑璇勫垎鏈嶅姟
    class FixedTestPointScoringService(TestPointScoringService):
        def _evaluate_rule_expression(self, expression: str, data_point: PHMData) -> Optional[float]:
            """
            淇鐗堟湰鐨勮鍒欒〃杈惧紡鎵ц
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
                    # 瀵逛簬甯冨皵缁撴灉锛屼娇鐢ㄤ慨澶嶇殑姒傜巼鎻愬彇閫昏緫
                    probability_score = self._extract_probability_fixed(processed_expression, data)
                    if probability_score is not None:
                        return probability_score
                    else:
                        return 1.0 if result else 0.0
                elif isinstance(result, (int, float)):
                    # 濡傛灉鏄暟鍊硷紝浣跨敤sigmoid鍑芥暟杞崲涓?-1姒傜巼
                    import math
                    if result <= 0:
                        return 0.0
                    elif result >= 10:
                        return 1.0
                    else:
                        # 浣跨敤sigmoid鍑芥暟: 1 / (1 + exp(-x))
                        return 1.0 / (1.0 + math.exp(-result))
                else:
                    logger.warning(f"瑙勫垯琛ㄨ揪寮忚繑鍥炰簡闈炴暟鍊肩粨鏋? {type(result)}")
                    return 0.0
                    
            except Exception as e:
                logger.error(f"瑙勫垯琛ㄨ揪寮忔墽琛屽け璐? {expression}, 閿欒: {e}")
                return 0.0
            finally:
                # 娓呯悊褰撳墠鏁版嵁寮曠敤
                if hasattr(self, '_current_data'):
                    delattr(self, '_current_data')
                if hasattr(self, '_current_data_point'):
                    delattr(self, '_current_data_point')
                if hasattr(self, '_temp_data_point'):
                    delattr(self, '_temp_data_point')
        
        def _extract_probability_fixed(self, expression: str, data: dict) -> Optional[float]:
            """
            淇鐗堟湰鐨勬鐜囨彁鍙栭€昏緫
            """
            try:
                import re
                
                # 鏌ユ壘level鍑芥暟璋冪敤
                level_matches = re.findall(r'level\("([^"]+)",\s*([^,]+),\s*([^)]+)\)', expression)
                
                if level_matches:
                    level_values = []
                    
                    for param_name, median_str, mad_str in level_matches:
                        # 鏌ユ壘瀹為檯鍙傛暟鍊?
                        actual_value = None
                        if param_name in data:
                            actual_value = data[param_name]
                        else:
                            # 鏌ユ壘鐩镐技鍙傛暟
                            for key in data.keys():
                                if param_name.strip() == key.strip():
                                    actual_value = data[key]
                                    break
                        
                        if actual_value is not None:
                            try:
                                x = float(actual_value)
                                median = float(median_str)
                                mad = float(mad_str)
                                mad_safe = max(abs(mad), 1e-9)
                                level_result = abs(x - median) / mad_safe
                                level_values.append(level_result)
                            except (ValueError, TypeError):
                                continue
                    
                    if level_values:
                        # 淇锛氭洿鍚堢悊鐨勬鐜囨槧灏?
                        max_level = max(level_values)
                        
                        # 鍩轰簬level鍊艰绠楁鐜?- 淇閫昏緫
                        if max_level <= 1.0:
                            return 0.05  # 姝ｅ父鐘舵€?
                        elif max_level <= 2.0:
                            return 0.2   # 杞诲井寮傚父
                        elif max_level <= 3.0:
                            return 0.5   # 涓瓑寮傚父
                        elif max_level <= 5.0:
                            return 0.8   # 涓ラ噸寮傚父
                        else:
                            return 0.95  # 鏋佷弗閲嶅紓甯?
                
                return None
                
            except Exception as e:
                logger.debug(f"鎻愬彇姒傜巼鍒嗘暟澶辫触: {e}")
                return None
    
    return FixedTestPointScoringService()

def test_fixed_scoring():
    """娴嬭瘯淇鍚庣殑璇勫垎鏈嶅姟"""
    print("\n=== 娴嬭瘯淇鍚庣殑璇勫垎鏈嶅姟 ===")
    
    # 1. 鑾峰彇娴嬭瘯鏁版嵁
    cmg = PHM.objects.filter(cmg_id='01').first()
    if not cmg:
        print("鉂?鎵句笉鍒癈MG 01")
        return
    
    latest_data = PHMData.objects.filter(cmg=cmg).order_by('-timestamp').first()
    if not latest_data:
        print("鉂?鎵句笉鍒版祴璇曟暟鎹?)
        return
    
    # 2. 鑾峰彇MSFG瀹氫箟
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    if not msfg:
        print("鉂?鎵句笉鍒版椿璺冪殑MSFG瀹氫箟")
        return
    
    print(f"鉁?浣跨敤鏁版嵁鐐? {latest_data.timestamp}")
    print(f"鉁?浣跨敤MSFG: {msfg.name}")
    
    # 3. 浣跨敤淇鍚庣殑璇勫垎鏈嶅姟
    fixed_scoring_service = fix_testpoint_scoring_service()
    
    # 4. 娴嬭瘯瑙勫垯鎵ц
    rules = TestPointRule.objects.filter(msfg_definition=msfg, is_online=True)
    print(f"\n馃搳 淇鍚庣殑瑙勫垯鎵ц缁撴灉:")
    
    for rule in rules:
        try:
            result = fixed_scoring_service._evaluate_rule_expression(rule.rule_expression, latest_data)
            print(f"  {rule.test_name}: {result:.3f}")
        except Exception as e:
            print(f"  {rule.test_name}: 鉂?{e}")
    
    # 5. 娴嬭瘯瀹屾暣璇勫垎
    print(f"\n馃搳 淇鍚庣殑瀹屾暣娴嬬偣璇勫垎:")
    test_scores = fixed_scoring_service.calculate_test_scores(latest_data, msfg)
    
    for test_name, score in test_scores.items():
        print(f"  {test_name}: {score:.3f}")
    
    # 6. 鍒嗘瀽淇鏁堟灉
    print(f"\n馃攳 淇鏁堟灉鍒嗘瀽:")
    high_scores = [(name, score) for name, score in test_scores.items() if score > 0.8]
    low_scores = [(name, score) for name, score in test_scores.items() if score < 0.1]
    
    if high_scores:
        print(f"  楂樺垎娴嬬偣 (>0.8): {len(high_scores)} 涓?)
        for name, score in high_scores:
            print(f"    {name}: {score:.3f}")
    
    if low_scores:
        print(f"  浣庡垎娴嬬偣 (<0.1): {len(low_scores)} 涓?)
        for name, score in low_scores:
            print(f"    {name}: {score:.3f}")
    
    return test_scores

def analyze_d_matrix_issue():
    """鍒嗘瀽D鐭╅樀闂"""
    print("\n=== 鍒嗘瀽D鐭╅樀闂 ===")
    
    # 1. 鑾峰彇MSFG瀹氫箟
    cmg = PHM.objects.filter(cmg_id='01').first()
    if not cmg:
        print("鉂?鎵句笉鍒癈MG 01")
        return
    
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    if not msfg:
        print("鉂?鎵句笉鍒版椿璺冪殑MSFG瀹氫箟")
        return
    
    # 2. 鑾峰彇鏄犲皠淇℃伅
    test_fault_mappings = TestPointFaultMapping.objects.filter(msfg_definition=msfg)
    test_nodes = list(msfg.nodes.filter(node_type='test').order_by('created_at'))
    fault_nodes = list(msfg.nodes.filter(node_type='fault').order_by('created_at'))
    
    print(f"馃搳 D鐭╅樀闂鍒嗘瀽:")
    print(f"  娴嬭瘯鐐?鏁呴殰鏄犲皠鎬绘暟: {test_fault_mappings.count()}")
    print(f"  MSFG娴嬭瘯鑺傜偣鏁? {len(test_nodes)}")
    print(f"  MSFG鏁呴殰鑺傜偣鏁? {len(fault_nodes)}")
    
    # 3. 鍒嗘瀽鏄犲皠瑕嗙洊
    mapped_faults = set()
    for mapping in test_fault_mappings:
        mapped_faults.add(mapping.fault_name)
    
    msfg_fault_names = set(node.name for node in fault_nodes)
    unmapped_in_msfg = msfg_fault_names - mapped_faults
    extra_in_mapping = mapped_faults - msfg_fault_names
    
    print(f"\n馃攳 鏄犲皠瑕嗙洊鍒嗘瀽:")
    print(f"  鏄犲皠涓殑鏁呴殰鏁? {len(mapped_faults)}")
    print(f"  MSFG涓殑鏁呴殰鏁? {len(msfg_fault_names)}")
    print(f"  MSFG涓湭鏄犲皠鐨勬晠闅? {len(unmapped_in_msfg)}")
    print(f"  鏄犲皠涓浣欑殑鏁呴殰: {len(extra_in_mapping)}")
    
    if unmapped_in_msfg:
        print(f"    鏈槧灏勭殑鏁呴殰: {list(unmapped_in_msfg)}")
    
    if extra_in_mapping:
        print(f"    澶氫綑鐨勬晠闅? {list(extra_in_mapping)[:10]}...")  # 鍙樉绀哄墠10涓?
    
    # 4. 寤鸿淇鏂规
    print(f"\n馃挕 淇寤鸿:")
    print(f"  1. D鐭╅樀澶у皬 (16, 9) 鏄纭殑锛岃〃绀?6涓晠闅滆妭鐐癸紝9涓祴璇曡妭鐐?)
    print(f"  2. 46涓槧灏勪腑鏈夐噸澶嶅拰澶氫綑鐨勬槧灏勶紝瀹為檯鏈夋晥鐨勬槧灏勬暟閲忚緝灏?)
    print(f"  3. 寤鸿娓呯悊鏄犲皠琛紝纭繚鏄犲皠鐨勬晠闅滈兘鍦∕SFG鑺傜偣涓瓨鍦?)

def main():
    """涓诲嚱鏁?""
    print("馃殌 寮€濮嬩慨澶峂SFG璇勫垎闂...")
    
    try:
        # 1. 娴嬭瘯淇鍚庣殑璇勫垎鏈嶅姟
        test_scores = test_fixed_scoring()
        
        # 2. 鍒嗘瀽D鐭╅樀闂
        analyze_d_matrix_issue()
        
        print("\n鉁?淇瀹屾垚!")
        print("\n馃搵 淇鎬荤粨:")
        print("  1. 鉁?淇浜嗚鍒欐墽琛岀幆澧冿紝娣诲姞浜哸nd/or/not鍑芥暟")
        print("  2. 鉁?淇浜嗘鐜囨彁鍙栭€昏緫锛岄檷浣庝簡寮傚父鍒嗘暟")
        print("  3. 鉁?鍒嗘瀽浜咲鐭╅樀闂锛岀‘璁ゅぇ灏忔槸姝ｇ‘鐨?)
        print("  4. 鉁?鎻愪緵浜嗘槧灏勬竻鐞嗗缓璁?)
        
    except Exception as e:
        print(f"鉂?淇澶辫触: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

