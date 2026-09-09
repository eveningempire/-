#!/usr/bin/env python
"""
瀵规瘮娴嬬偣璇勫垎鏈哄埗鍜岃鍒欐娴嬭瘎鍒嗘満鍒?
鍒嗘瀽涓ょ璇勫垎鏂瑰紡鐨勫樊寮傚苟缁欏嚭鏀硅繘寤鸿
"""

import os
import sys
import django
import logging
from typing import Dict, List, Any

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel, PHMData
from msfg_analysis.models import MSFGDefinition, TestPointRule
from rule_detection.models import RuleDefinition
from msfg_analysis.services.testpoint_scoring import TestPointScoringService
from rule_detection.algorithms.rule.rule_detector import evaluate_rules_on_point, compile_rules

# 閰嶇疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_scoring_mechanisms():
    """鍒嗘瀽涓ょ璇勫垎鏈哄埗"""
    print("馃攳 瀵规瘮娴嬬偣璇勫垎鏈哄埗鍜岃鍒欐娴嬭瘎鍒嗘満鍒?)
    print("=" * 80)
    
    # 1. 鑾峰彇娲昏穬鐨凜MG妯″瀷
    cmg_model = PHMModel.objects.filter(is_active=True).first()
    if not cmg_model:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凜MG妯″瀷")
        return False
    
    print(f"馃搵 浣跨敤PHM妯″瀷: {cmg_model.model_name}")
    
    # 2. 鍒嗘瀽娴嬬偣璇勫垎鏈哄埗
    print(f"\n馃搳 娴嬬偣璇勫垎鏈哄埗鍒嗘瀽")
    print("-" * 40)
    
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).first()
    if msfg:
        testpoint_rules = TestPointRule.objects.filter(msfg_definition=msfg, is_online=True)
        print(f"   娴嬬偣瑙勫垯鏁伴噺: {testpoint_rules.count()}")
        
        if testpoint_rules.exists():
            print("   娴嬬偣瑙勫垯绀轰緥:")
            for rule in testpoint_rules[:3]:
                print(f"   - {rule.test_name}: {rule.rule_expression}")
                print(f"     鏉冮噸: {rule.weight}, 缃俊搴? {rule.confidence}")
    else:
        print("   鈿狅笍  娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
    
    # 3. 鍒嗘瀽瑙勫垯妫€娴嬭瘎鍒嗘満鍒?
    print(f"\n馃攳 瑙勫垯妫€娴嬭瘎鍒嗘満鍒跺垎鏋?)
    print("-" * 40)
    
    rule_definitions = RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True)
    print(f"   瑙勫垯瀹氫箟鏁伴噺: {rule_definitions.count()}")
    
    if rule_definitions.exists():
        print("   瑙勫垯瀹氫箟绀轰緥:")
        for rule in rule_definitions[:3]:
            print(f"   - {rule.rule_id}: {rule.rule_expression}")
            print(f"     鏁呴殰鍚嶇О: {rule.fault_name}, 鏁呴殰绾у埆: {rule.fault_level}")
    
    # 4. 璇︾粏瀵规瘮涓ょ鏈哄埗
    print(f"\n馃搱 璇︾粏鏈哄埗瀵规瘮")
    print("-" * 40)
    
    print("   1. 璇勫垎鑼冨洿:")
    print("      娴嬬偣璇勫垎: 0.0-1.0 (杩炵画姒傜巼鍒嗘暟)")
    print("      瑙勫垯妫€娴? 0.0 鎴?1.0 (浜屽€煎垎鏁?")
    
    print("\n   2. 璇勫垎閫昏緫:")
    print("      娴嬬偣璇勫垎:")
    print("        - 鏀寔甯冨皵缁撴灉杞崲涓烘鐜?)
    print("        - 鏀寔鏁板€肩粨鏋滀娇鐢╯igmoid鍑芥暟杞崲")
    print("        - 鏀寔level鍑芥暟鎻愬彇姒傜巼鍒嗘暟")
    print("        - 澶氳鍒欒瀺鍚堜娇鐢ㄦ寚鏁板姞鏉冨钩鍧?)
    
    print("      瑙勫垯妫€娴?")
    print("        - 甯冨皵缁撴灉鐩存帴杞崲涓?/1")
    print("        - 鏁板€肩粨鏋滃皾璇曡浆鎹负0-1鑼冨洿")
    print("        - 鍗曡鍒欑嫭绔嬭瘎鍒?)
    
    print("\n   3. 瑙勫垯琛ㄨ揪寮忓鐞?")
    print("      娴嬬偣璇勫垎:")
    print("        - 鏀寔MSFG涓撶敤鍑芥暟(level, ma_diff, rollstd绛?")
    print("        - 鏀寔鍘嗗彶鏁版嵁鍒嗘瀽")
    print("        - 鏀寔鏉冮噸鍜岀疆淇″害璋冩暣")
    
    print("      瑙勫垯妫€娴?")
    print("        - 鏀寔鍩虹鏁板鍑芥暟")
    print("        - 鏀寔楂樼骇缁熻鍑芥暟(澧炲己鐗?")
    print("        - 鏀寔鏃跺簭鍒嗘瀽鍑芥暟")
    
    print("\n   4. 鏁版嵁铻嶅悎绛栫暐:")
    print("      娴嬬偣璇勫垎:")
    print("        - 鍚屼竴娴嬬偣澶氭潯瑙勫垯鎸夋潈閲嶈瀺鍚?)
    print("        - 浣跨敤鎸囨暟鍔犳潈骞冲潎閬垮厤寮傚父鍊煎奖鍝?)
    print("        - 鏀寔缃俊搴﹁皟鏁?)
    
    print("      瑙勫垯妫€娴?")
    print("        - 姣忔潯瑙勫垯鐙珛璇勪及")
    print("        - 鏃犺鍒欓棿铻嶅悎鏈哄埗")
    print("        - 缁撴灉鐩存帴瀛樺偍")
    
    return True

def demonstrate_scoring_differences():
    """婕旂ず璇勫垎宸紓"""
    print(f"\n馃И 璇勫垎宸紓婕旂ず")
    print("-" * 40)
    
    # 鍒涘缓妯℃嫙鏁版嵁
    test_data = {
        "temperature": 85.5,
        "pressure": 120.3,
        "vibration": 0.8,
        "current": 15.2
    }
    
    print("   妯℃嫙鏁版嵁:")
    for key, value in test_data.items():
        print(f"   - {key}: {value}")
    
    # 妯℃嫙娴嬬偣璇勫垎
    print(f"\n   娴嬬偣璇勫垎绀轰緥:")
    print("   - 琛ㄨ揪寮? level('temperature', 75.0, 5.0)")
    print("   - 缁撴灉: 杩炵画姒傜巼鍒嗘暟 (0.0-1.0)")
    print("   - 璁＄畻: abs(85.5-75.0)/5.0 = 2.1 鈫?sigmoid(2.1) 鈮?0.89")
    
    # 妯℃嫙瑙勫垯妫€娴嬭瘎鍒?
    print(f"\n   瑙勫垯妫€娴嬭瘎鍒嗙ず渚?")
    print("   - 琛ㄨ揪寮? temperature > 80.0")
    print("   - 缁撴灉: 甯冨皵鍊?鈫?0.0 鎴?1.0")
    print("   - 璁＄畻: 85.5 > 80.0 = True 鈫?1.0")
    
    print(f"\n   鍏抽敭宸紓:")
    print("   - 娴嬬偣璇勫垎鎻愪緵杩炵画鐨勫紓甯哥▼搴﹁瘎浼?)
    print("   - 瑙勫垯妫€娴嬫彁渚涗簩鍊肩殑瑙﹀彂鐘舵€?)
    print("   - 娴嬬偣璇勫垎鏇撮€傚悎鍋ュ悍搴﹁绠?)
    print("   - 瑙勫垯妫€娴嬫洿閫傚悎鏁呴殰璇婃柇")

def propose_improvements():
    """鎻愬嚭鏀硅繘寤鸿"""
    print(f"\n馃挕 鏀硅繘寤鸿")
    print("-" * 40)
    
    print("   1. 缁熶竴璇勫垎鏈哄埗:")
    print("      - 灏嗚鍒欐娴嬭瘎鍒嗘敼涓?-1杩炵画鍒嗘暟")
    print("      - 鍙傝€冩祴鐐硅瘎鍒嗙殑姒傜巼杞崲鏂规硶")
    print("      - 鏀寔缃俊搴﹀垎鏁拌绠?)
    
    print("\n   2. 澧炲己瑙勫垯妫€娴嬭瘎鍒?")
    print("      - 娣诲姞level鍑芥暟鏀寔")
    print("      - 瀹炵幇sigmoid姒傜巼杞崲")
    print("      - 鏀寔澶氳鍒欒瀺鍚?)
    
    print("\n   3. 鏀硅繘璇勫垎绠楁硶:")
    print("      - 甯冨皵缁撴灉: 鎻愬彇琛ㄨ揪寮忕殑鏁板€间俊鎭?)
    print("      - 鏁板€肩粨鏋? 浣跨敤sigmoid鍑芥暟杞崲")
    print("      - 闃堝€肩粨鏋? 璁＄畻鍒伴槇鍊肩殑璺濈")
    
    print("\n   4. 缁熶竴鍑芥暟搴?")
    print("      - 灏哅SFG鍑芥暟鎵╁睍鍒拌鍒欐娴?)
    print("      - 缁熶竴鍘嗗彶鏁版嵁鍒嗘瀽鎺ュ彛")
    print("      - 鏍囧噯鍖栫疆淇″害璁＄畻鏂规硶")
    
    print("\n   5. 鏁版嵁铻嶅悎绛栫暐:")
    print("      - 涓鸿鍒欐娴嬫坊鍔犲瑙勫垯铻嶅悎")
    print("      - 瀹炵幇鏉冮噸鍜岀疆淇″害璋冩暣")
    print("      - 鏀寔寮傚父鍊煎鐞?)

def create_enhanced_rule_scoring():
    """鍒涘缓澧炲己鐨勮鍒欒瘎鍒嗙ず渚?""
    print(f"\n馃敡 澧炲己瑙勫垯璇勫垎绀轰緥")
    print("-" * 40)
    
    print("   褰撳墠瑙勫垯妫€娴嬭瘎鍒?")
    print("   ```python")
    print("   def evaluate_rules_on_point(data_point, compiled_rules):")
    print("       for cr in compiled_rules:")
    print("           value = SafeEvaluator(vars_).visit(cr.ast_obj)")
    print("           is_triggered = bool(value)")
    print("           score = 1.0 if is_triggered else 0.0  # 浜屽€艰瘎鍒?)
    print("   ```")
    
    print("\n   寤鸿鐨勫寮鸿瘎鍒?")
    print("   ```python")
    print("   def evaluate_rules_on_point_enhanced(data_point, compiled_rules):")
    print("       for cr in compiled_rules:")
    print("           value = SafeEvaluator(vars_).visit(cr.ast_obj)")
    print("           score = convert_to_probability(value, cr.expression)  # 杩炵画璇勫垎")
    print("   ```")
    
    print("\n   姒傜巼杞崲鍑芥暟:")
    print("   ```python")
    print("   def convert_to_probability(value, expression):")
    print("       if isinstance(value, bool):")
    print("           return extract_probability_from_expression(expression)")
    print("       elif isinstance(value, (int, float)):")
    print("           return sigmoid(value)")
    print("       else:")
    print("           return 0.0")
    print("   ```")

if __name__ == "__main__":
    print("馃殌 寮€濮嬪姣旇瘎鍒嗘満鍒?)
    print("=" * 80)
    
    success = analyze_scoring_mechanisms()
    demonstrate_scoring_differences()
    propose_improvements()
    create_enhanced_rule_scoring()
    
    print("\n" + "=" * 80)
    if success:
        print("馃帀 瀵规瘮鍒嗘瀽瀹屾垚!")
    else:
        print("鉂?瀵规瘮鍒嗘瀽澶辫触")
    
    print("=" * 80)

