#!/usr/bin/env python
"""
娴嬭瘯瑙勫垯璇硶瑙ｆ瀽
婕旂ずPHM瑙勫垯妫€娴嬬粍浠舵敮鎸佺殑鍚勭鍑芥暟鍜岃娉?
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from rule_detection.algorithms.rule.advanced_rule_parser import AdvancedRuleParser

def test_rule_syntax():
    """娴嬭瘯瑙勫垯璇硶瑙ｆ瀽"""
    print("=" * 80)
    print("PHM瑙勫垯妫€娴嬬粍浠惰娉曡В鏋愭祴璇?)
    print("=" * 80)
    
    # 瀹氫箟娴嬭瘯鍙傛暟鍜屾晠闅滃悕绉?
    parameter_names = [
        "娓╁害", "鍘嬪姏", "杞€?, "鐢垫祦", "鐢靛帇", "鎸姩", "娴侀噺", "娑蹭綅"
    ]
    
    fault_names = [
        "杩囩儹鏁呴殰", "鍘嬪姏寮傚父", "杞€熻繃楂?, "鐢垫祦杩囧ぇ", "鎸姩寮傚父", "娴侀噺涓嶈冻"
    ]
    
    # 鍒涘缓瑙ｆ瀽鍣?
    parser = AdvancedRuleParser(parameter_names, fault_names)
    
    # 娴嬭瘯鐢ㄤ緥
    test_cases = [
        # 1. 鍩虹鍙傛暟璁块棶
        {
            "name": "鍩虹鍙傛暟璁块棶",
            "rule": 'Para("娓╁害") > 80',
            "description": "娓╁害瓒呰繃80搴?
        },
        
        # 2. 閫昏緫杩愮畻
        {
            "name": "閫昏緫杩愮畻",
            "rule": 'Para("娓╁害") > 80 and Para("鍘嬪姏") > 100',
            "description": "娓╁害瓒呰繃80搴︿笖鍘嬪姏瓒呰繃100"
        },
        
        # 3. 缁熻鍑芥暟
        {
            "name": "缁熻鍑芥暟 - 鏈€澶у€?,
            "rule": 'Max(Para("娓╁害"), 10, 0) > 85',
            "description": "10甯у唴娓╁害鏈€澶у€艰秴杩?5搴?
        },
        
        {
            "name": "缁熻鍑芥暟 - 骞冲潎鍊?,
            "rule": 'Mean(Para("鍘嬪姏"), 5, 1) > 120',
            "description": "5绉掑唴鍘嬪姏骞冲潎鍊艰秴杩?20"
        },
        
        # 4. 瓒嬪娍鍒嗘瀽
        {
            "name": "瓒嬪娍鍒嗘瀽 - 澧為暱",
            "rule": 'Increase(Para("娓╁害"), 10, 0)',
            "description": "娓╁害鍦?0甯у唴鎸佺画澧為暱"
        },
        
        {
            "name": "瓒嬪娍鍒嗘瀽 - 涓嬮檷",
            "rule": 'Decrease(Para("鍘嬪姏"), 5, 1)',
            "description": "鍘嬪姏鍦?绉掑唴鎸佺画涓嬮檷"
        },
        
        # 5. 鏃跺簭鏉′欢
        {
            "name": "鏃跺簭鏉′欢 - 鎸佺画",
            "rule": '[](Para("娓╁害") > 80, 10)',
            "description": "娓╁害瓒呰繃80搴︽寔缁?0绉?
        },
        
        {
            "name": "鏃跺簭鏉′欢 - 浠绘剰",
            "rule": '<>(Para("鍘嬪姏") > 100, 5)',
            "description": "鍘嬪姏鍦?绉掑唴浠绘剰鏃跺埢瓒呰繃100"
        },
        
        {
            "name": "鏃跺簭鏉′欢 - 閮ㄥ垎",
            "rule": '{}(Para("杞€?) > 1000, 10, 5)',
            "description": "杞€熷湪10甯у唴鏈?甯ц秴杩?000"
        },
        
        # 6. 鏉′欢鎺у埗
        {
            "name": "鍓嶇疆鏉′欢",
            "rule": 'PreCond(Para("娓╁害") > 80, 5, Para("鍘嬪姏") > 100)',
            "description": "娓╁害瓒呰繃80搴﹀悗锛屽欢鏃?绉掓鏌ュ帇鍔涙槸鍚﹁秴杩?00"
        },
        
        {
            "name": "瑙﹀彂鍣?,
            "rule": 'Trigger(Para("娓╁害") > 90, 10, Para("娓╁害") < 70)',
            "description": "娓╁害瓒呰繃90搴﹁Е鍙戯紝寤舵椂10绉掑悗妫€鏌ユ俯搴︽槸鍚︿綆浜?0搴?
        },
        
        # 7. 鏁呴殰寮曠敤
        {
            "name": "鏁呴殰寮曠敤",
            "rule": 'Fault("杩囩儹鏁呴殰")',
            "description": "寮曠敤杩囩儹鏁呴殰瀹氫箟"
        },
        
        # 8. 鏁板鍑芥暟
        {
            "name": "鏁板鍑芥暟",
            "rule": 'abs(Para("鎸姩")) > 10',
            "description": "鎸姩缁濆鍊艰秴杩?0"
        },
        
        # 9. 澶嶆潅缁勫悎
        {
            "name": "澶嶆潅缁勫悎瑙勫垯",
            "rule": '(Para("娓╁害") > 80 and Para("鍘嬪姏") > 100) or Fault("鍘嗗彶鏁呴殰")',
            "description": "娓╁害瓒呰繃80搴︿笖鍘嬪姏瓒呰繃100锛屾垨鑰呭巻鍙叉晠闅滃瓨鍦?
        },
        
        # 10. 宓屽鍑芥暟
        {
            "name": "宓屽鍑芥暟",
            "rule": 'Mean(Max(Para("娓╁害"), 5, 0), 10, 0) > 85',
            "description": "5甯у唴娓╁害鏈€澶у€煎湪10甯у唴鐨勫钩鍧囧€艰秴杩?5搴?
        },
        
        # 11. 涓枃杩愮畻绗?
        {
            "name": "涓枃杩愮畻绗?,
            "rule": 'Para("娓╁害") 澶т簬 80 骞朵笖 Para("鍘嬪姏") 灏忎簬 100',
            "description": "浣跨敤涓枃杩愮畻绗︼細娓╁害澶т簬80骞朵笖鍘嬪姏灏忎簬100"
        },
        
        # 12. 鏃堕棿鍑芥暟
        {
            "name": "鏃堕棿鍑芥暟",
            "rule": 'Time("娓╁害") > 1000000',
            "description": "娓╁害鏃堕棿鎴冲ぇ浜?000000"
        }
    ]
    
    # 鎵ц娴嬭瘯
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   鎻忚堪: {test_case['description']}")
        print(f"   瑙勫垯: {test_case['rule']}")
        
        try:
            # 瑙ｆ瀽瑙勫垯
            result = parser.parse(test_case['rule'])
            
            print(f"   瑙ｆ瀽缁撴灉:")
            print(f"   - 琛ㄨ揪寮? {result.expression}")
            print(f"   - 鐩稿叧鍙傛暟: {list(result.related_parameters)}")
            print(f"   - 鐩稿叧鏁呴殰: {list(result.related_faults)}")
            print(f"   - 閿欒鏁? {result.error_count}")
            print(f"   - 璀﹀憡鏁? {result.warning_count}")
            
            if result.log_messages:
                print(f"   - 鏃ュ織娑堟伅:")
                for msg in result.log_messages:
                    print(f"     {msg['type']}: {msg['message']}")
            
            if result.error_count == 0:
                print(f"   鉁?瑙ｆ瀽鎴愬姛")
            else:
                print(f"   鉂?瑙ｆ瀽澶辫触")
                
        except Exception as e:
            print(f"   鉂?瑙ｆ瀽寮傚父: {str(e)}")
        
        print("-" * 60)
    
    # 娴嬭瘯閿欒鎯呭喌
    print(f"\n閿欒鎯呭喌娴嬭瘯:")
    error_cases = [
        {
            "name": "鏈煡鍙傛暟",
            "rule": 'Para("鏈煡鍙傛暟") > 80',
            "expected": "搴旇浜х敓璀﹀憡"
        },
        {
            "name": "璇硶閿欒",
            "rule": 'Para("娓╁害" > 80',
            "expected": "搴旇浜х敓閿欒锛堟嫭鍙蜂笉鍖归厤锛?
        },
        {
            "name": "鏈煡鍑芥暟",
            "rule": 'UnknownFunc("娓╁害") > 80',
            "expected": "搴旇浜х敓璀﹀憡锛堟湭鐭ュ嚱鏁帮級"
        }
    ]
    
    for i, error_case in enumerate(error_cases, 1):
        print(f"\n閿欒娴嬭瘯 {i}: {error_case['name']}")
        print(f"   瑙勫垯: {error_case['rule']}")
        print(f"   棰勬湡: {error_case['expected']}")
        
        try:
            result = parser.parse(error_case['rule'])
            print(f"   瀹為檯缁撴灉:")
            print(f"   - 閿欒鏁? {result.error_count}")
            print(f"   - 璀﹀憡鏁? {result.warning_count}")
            
            if result.log_messages:
                for msg in result.log_messages:
                    print(f"   - {msg['type']}: {msg['message']}")
                    
        except Exception as e:
            print(f"   鉂?瑙ｆ瀽寮傚父: {str(e)}")
    
    print(f"\n" + "=" * 80)
    print("娴嬭瘯瀹屾垚锛?)
    print("=" * 80)
    
    print(f"\n鏀寔鐨勫嚱鏁版€荤粨:")
    print(f"1. 鍙傛暟璁块棶: Para(), Time()")
    print(f"2. 缁熻鍑芥暟: Max(), Min(), Mean()")
    print(f"3. 瓒嬪娍鍒嗘瀽: Increase(), Decrease()")
    print(f"4. 鏃跺簭鏉′欢: [](鎸佺画), <>(浠绘剰), {}(閮ㄥ垎)")
    print(f"5. 鏉′欢鎺у埗: PreCond(), Trigger()")
    print(f"6. 鏁呴殰寮曠敤: Fault()")
    print(f"7. 鏁板鍑芥暟: abs(), sin(), cos(), log(), exp() 绛?)
    print(f"8. 閫昏緫杩愮畻: and, or, not, xor")
    print(f"9. 姣旇緝杩愮畻: >, <, >=, <=, ==, !=")
    print(f"10. 绠楁湳杩愮畻: +, -, *, /, **, //, %")

if __name__ == "__main__":
    test_rule_syntax()

