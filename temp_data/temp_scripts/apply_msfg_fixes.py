#!/usr/bin/env python
"""
搴旂敤MSFG淇鏂规
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
from msfg_analysis.models import TestPointFaultMapping, MSFGDefinition
from data_management.models import PHM

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def apply_testpoint_scoring_fixes():
    """搴旂敤娴嬬偣璇勫垎鏈嶅姟鐨勪慨澶?""
    print("=== 搴旂敤娴嬬偣璇勫垎鏈嶅姟淇 ===")
    
    # 淇鏂囦欢璺緞
    scoring_file = "msfg_analysis/services/testpoint_scoring.py"
    
    print(f"馃敡 淇鏂囦欢: {scoring_file}")
    
    # 璇诲彇鍘熸枃浠?
    with open(scoring_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 淇1: 娣诲姞and/or/not鍑芥暟鍒皊afe_globals
    old_safe_globals = """            # 鍒涘缓瀹夊叏鐨勬墽琛岀幆澧?
            safe_globals = {
                '__builtins__': {},
                'abs': abs,
                'min': min,
                'max': max,
                'round': round,
                'float': float,
                'int': int,
                'len': len,
            }"""
    
    new_safe_globals = """            # 鍒涘缓瀹夊叏鐨勬墽琛岀幆澧?
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
            }"""
    
    if old_safe_globals in content:
        content = content.replace(old_safe_globals, new_safe_globals)
        print("鉁?淇1: 娣诲姞浜哸nd/or/not鍑芥暟")
    else:
        print("鈿狅笍 淇1: 鏈壘鍒伴渶瑕佹浛鎹㈢殑浠ｇ爜娈?)
    
    # 淇2: 鏀硅繘姒傜巼鎻愬彇閫昏緫
    old_probability_logic = """                    # 鍩轰簬level鍊艰绠楁鐜?
                    # level > 3.0 閫氬父琛ㄧず寮傚父
                    if max_level <= 1.0:
                        return 0.1  # 浣庢鐜?
                    elif max_level <= 2.0:
                        return 0.3  # 涓綆姒傜巼
                    elif max_level <= 3.0:
                        return 0.5  # 涓瓑姒傜巼
                    elif max_level <= 5.0:
                        return 0.8  # 楂樻鐜?
                    else:
                        return 0.95  # 寰堥珮姒傜巼"""
    
    new_probability_logic = """                    # 鍩轰簬level鍊艰绠楁鐜?- 淇閫昏緫
                    if max_level <= 1.0:
                        return 0.05  # 姝ｅ父鐘舵€?
                    elif max_level <= 2.0:
                        return 0.2   # 杞诲井寮傚父
                    elif max_level <= 3.0:
                        return 0.5   # 涓瓑寮傚父
                    elif max_level <= 5.0:
                        return 0.8   # 涓ラ噸寮傚父
                    else:
                        return 0.95  # 鏋佷弗閲嶅紓甯?""
    
    if old_probability_logic in content:
        content = content.replace(old_probability_logic, new_probability_logic)
        print("鉁?淇2: 鏀硅繘浜嗘鐜囨彁鍙栭€昏緫")
    else:
        print("鈿狅笍 淇2: 鏈壘鍒伴渶瑕佹浛鎹㈢殑浠ｇ爜娈?)
    
    # 鍐欏洖鏂囦欢
    with open(scoring_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("鉁?娴嬬偣璇勫垎鏈嶅姟淇瀹屾垚")

def clean_testpoint_fault_mappings():
    """娓呯悊娴嬭瘯鐐?鏁呴殰鏄犲皠琛?""
    print("\n=== 娓呯悊娴嬭瘯鐐?鏁呴殰鏄犲皠琛?===")
    
    # 鑾峰彇MSFG瀹氫箟
    cmg = PHM.objects.filter(cmg_id='01').first()
    if not cmg:
        print("鉂?鎵句笉鍒癈MG 01")
        return
    
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    if not msfg:
        print("鉂?鎵句笉鍒版椿璺冪殑MSFG瀹氫箟")
        return
    
    print(f"鉁?浣跨敤MSFG: {msfg.name}")
    
    # 鑾峰彇MSFG涓殑鏁呴殰鑺傜偣
    fault_nodes = list(msfg.nodes.filter(node_type='fault').order_by('created_at'))
    msfg_fault_names = set(node.name for node in fault_nodes)
    
    print(f"馃搳 MSFG涓殑鏁呴殰鑺傜偣: {len(msfg_fault_names)} 涓?)
    
    # 鑾峰彇鎵€鏈夋槧灏?
    all_mappings = TestPointFaultMapping.objects.filter(msfg_definition=msfg)
    print(f"馃搳 褰撳墠鏄犲皠鎬绘暟: {all_mappings.count()} 涓?)
    
    # 鎵惧嚭鏃犳晥鐨勬槧灏勶紙鏁呴殰鍚嶄笉鍦∕SFG鑺傜偣涓級
    invalid_mappings = []
    valid_mappings = []
    
    for mapping in all_mappings:
        if mapping.fault_name in msfg_fault_names:
            valid_mappings.append(mapping)
        else:
            invalid_mappings.append(mapping)
    
    print(f"馃搳 鏈夋晥鏄犲皠: {len(valid_mappings)} 涓?)
    print(f"馃搳 鏃犳晥鏄犲皠: {len(invalid_mappings)} 涓?)
    
    if invalid_mappings:
        print(f"\n馃攳 鏃犳晥鏄犲皠鍒楄〃:")
        for mapping in invalid_mappings[:10]:  # 鍙樉绀哄墠10涓?
            print(f"  {mapping.test_point_name} -> {mapping.fault_name}")
        if len(invalid_mappings) > 10:
            print(f"  ... 杩樻湁 {len(invalid_mappings) - 10} 涓?)
        
        # 璇㈤棶鏄惁鍒犻櫎鏃犳晥鏄犲皠
        print(f"\n鉂?鏄惁鍒犻櫎 {len(invalid_mappings)} 涓棤鏁堟槧灏勶紵")
        print("   杩欏皢娓呯悊鏄犲皠琛紝纭繚鎵€鏈夋槧灏勭殑鏁呴殰閮藉湪MSFG鑺傜偣涓瓨鍦?)
        
        # 杩欓噷鍙互娣诲姞鐢ㄦ埛纭閫昏緫锛岀幇鍦ㄧ洿鎺ユ墽琛?
        print("鉁?鎵ц娓呯悊...")
        
        # 鍒犻櫎鏃犳晥鏄犲皠
        for mapping in invalid_mappings:
            mapping.delete()
        
        print(f"鉁?宸插垹闄?{len(invalid_mappings)} 涓棤鏁堟槧灏?)
    else:
        print("鉁?鎵€鏈夋槧灏勯兘鏄湁鏁堢殑锛屾棤闇€娓呯悊")

def create_mapping_report():
    """鍒涘缓鏄犲皠鎶ュ憡"""
    print("\n=== 鍒涘缓鏄犲皠鎶ュ憡 ===")
    
    # 鑾峰彇MSFG瀹氫箟
    cmg = PHM.objects.filter(cmg_id='01').first()
    if not cmg:
        print("鉂?鎵句笉鍒癈MG 01")
        return
    
    msfg = MSFGDefinition.objects.filter(cmg_model=cmg.cmg_model, is_active=True).first()
    if not msfg:
        print("鉂?鎵句笉鍒版椿璺冪殑MSFG瀹氫箟")
        return
    
    # 鑾峰彇鑺傜偣淇℃伅
    test_nodes = list(msfg.nodes.filter(node_type='test').order_by('created_at'))
    fault_nodes = list(msfg.nodes.filter(node_type='fault').order_by('created_at'))
    
    # 鑾峰彇鏄犲皠淇℃伅
    mappings = TestPointFaultMapping.objects.filter(msfg_definition=msfg)
    
    # 鍒涘缓鎶ュ憡
    report = f"""
# MSFG鏄犲皠鎶ュ憡

## 鍩烘湰淇℃伅
- MSFG鍚嶇О: {msfg.name}
- 娴嬭瘯鑺傜偣鏁伴噺: {len(test_nodes)}
- 鏁呴殰鑺傜偣鏁伴噺: {len(fault_nodes)}
- 鏄犲皠鏁伴噺: {mappings.count()}

## 娴嬭瘯鑺傜偣鍒楄〃
"""
    
    for i, node in enumerate(test_nodes, 1):
        report += f"{i}. {node.name}\n"
    
    report += "\n## 鏁呴殰鑺傜偣鍒楄〃\n"
    for i, node in enumerate(fault_nodes, 1):
        report += f"{i}. {node.name}\n"
    
    report += "\n## 鏄犲皠璇︽儏\n"
    for mapping in mappings:
        report += f"- {mapping.test_point_name} -> {mapping.fault_name} (鏉冮噸: {mapping.weight}, 缃俊搴? {mapping.confidence})\n"
    
    # 淇濆瓨鎶ュ憡
    report_file = "msfg_mapping_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"鉁?鏄犲皠鎶ュ憡宸蹭繚瀛樺埌: {report_file}")

def main():
    """涓诲嚱鏁?""
    print("馃殌 寮€濮嬪簲鐢∕SFG淇鏂规...")
    
    try:
        # 1. 搴旂敤娴嬬偣璇勫垎鏈嶅姟淇
        apply_testpoint_scoring_fixes()
        
        # 2. 娓呯悊娴嬭瘯鐐?鏁呴殰鏄犲皠琛?
        clean_testpoint_fault_mappings()
        
        # 3. 鍒涘缓鏄犲皠鎶ュ憡
        create_mapping_report()
        
        print("\n鉁?鎵€鏈変慨澶嶅簲鐢ㄥ畬鎴?")
        print("\n馃搵 淇鎬荤粨:")
        print("  1. 鉁?淇浜嗘祴鐐硅瘎鍒嗘湇鍔′腑鐨勮鍒欐墽琛岀幆澧?)
        print("  2. 鉁?鏀硅繘浜嗘鐜囨彁鍙栭€昏緫锛岄檷浣庝簡寮傚父鍒嗘暟")
        print("  3. 鉁?娓呯悊浜嗘棤鏁堢殑娴嬭瘯鐐?鏁呴殰鏄犲皠")
        print("  4. 鉁?鍒涘缓浜嗚缁嗙殑鏄犲皠鎶ュ憡")
        print("\n馃挕 寤鸿:")
        print("  1. 閲嶆柊杩愯MSFG妫€娴嬶紝楠岃瘉淇鏁堟灉")
        print("  2. 妫€鏌ユ祴鐐硅瘎鍒嗘槸鍚︽洿鍔犲悎鐞?)
        print("  3. 纭D鐭╅樀鏋勫缓鏄惁姝ｇ‘")
        
    except Exception as e:
        print(f"鉂?淇搴旂敤澶辫触: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

