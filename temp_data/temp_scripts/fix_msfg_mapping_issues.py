#!/usr/bin/env python
"""
淇MSFG娴嬬偣-閮ㄤ欢鏄犲皠闂
1. 淇MSFG瀹氫箟涓殑component_names瀛楁
2. 淇鑺傜偣鍒嗙被闂
3. 鍒涘缓姝ｇ‘鐨勬祴璇曠偣-閮ㄤ欢鏄犲皠
4. 澶勭悊寰幆寮曠敤闂
"""

import os
import sys
import django
import logging
from typing import Dict, List, Any

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping, MSFGNode, MSFGEdge
from msfg_analysis.algorithms.msfg.component_integration import get_active_msfg_for_cmg_model

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_msfg_component_names():
    """淇MSFG瀹氫箟涓殑component_names瀛楁"""
    print("馃敡 淇MSFG瀹氫箟涓殑component_names瀛楁")
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 澶勭悊PHM妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            print(f"  鉂?娌℃湁婵€娲荤殑MSFG瀹氫箟")
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 浠庤妭鐐逛腑鎻愬彇鏈夋剰涔夌殑閮ㄤ欢鍚嶇О
        component_names = extract_meaningful_components(active_msfg)
        
        if component_names:
            # 鏇存柊MSFG瀹氫箟鐨刢omponent_names瀛楁
            active_msfg.component_names = component_names
            active_msfg.save()
            print(f"  鉁?鏇存柊component_names: {component_names}")
        else:
            print(f"  鈿狅笍  娌℃湁鎵惧埌鏈夋剰涔夌殑閮ㄤ欢鍚嶇О")

def extract_meaningful_components(msfg_definition):
    """浠嶮SFG鑺傜偣涓彁鍙栨湁鎰忎箟鐨勯儴浠跺悕绉?""
    components = set()
    
    # 浠庢晠闅滆妭鐐逛腑鎻愬彇閮ㄤ欢鍚嶇О
    fault_nodes = MSFGNode.objects.filter(
        msfg_definition=msfg_definition,
        node_type='fault'
    )
    
    for node in fault_nodes:
        if node.name and node.name.strip():
            # 浠庢晠闅滃悕绉颁腑鎻愬彇閮ㄤ欢淇℃伅
            component = extract_component_from_fault_name(node.name)
            if component:
                components.add(component)
    
    # 浠庣郴缁熻妭鐐逛腑鎻愬彇閮ㄤ欢鍚嶇О锛堟帓闄ょ┖鍚嶇О锛?
    system_nodes = MSFGNode.objects.filter(
        msfg_definition=msfg_definition,
        node_type='system'
    ).exclude(name__in=['', 'root', 'system'])
    
    for node in system_nodes:
        if node.name and node.name.strip():
            components.add(node.name.strip())
    
    return sorted(list(components))

def extract_component_from_fault_name(fault_name):
    """浠庢晠闅滃悕绉颁腑鎻愬彇閮ㄤ欢鍚嶇О"""
    fault_lower = fault_name.lower()
    
    # 瀹氫箟閮ㄤ欢鍏抽敭璇嶆槧灏?
    component_keywords = {
        '鐢垫簮绯荤粺': ['鐢垫簮', '鐢靛帇', 'v', '渚涚數', '鐢靛姏', '29v', '100v', '12v'],
        '鐢垫満绯荤粺': ['鐢垫満', '椹揪', 'motor', '杞€?, '閫熷害', 'rpm', '椹卞姩'],
        '杞存壙绯荤粺': ['杞存壙', '杞存俯', '娓╁害', 'bearing', '鍥虹揣绔?, '婊戝姩绔?],
        '鎺у埗绯荤粺': ['鎺у埗', 'control', '妗嗘灦', '澹虫俯', '鎺у埗鍣?],
        '浼犳劅鍣ㄧ郴缁?: ['浼犳劅', 'sensor', '妫€娴?, '閬ユ祴', '浣嶇疆'],
        '閫氫俊绯荤粺': ['1553', '鎺ュ彛', '閫氫俊', '鎬荤嚎', 'spi'],
        '鏃嬪彉绯荤粺': ['鏃嬪彉', '瑙ｈ皟', '鏃嬭浆鍙樺帇鍣?],
        '鐢垫祦閲囨牱绯荤粺': ['鐢垫祦', 'current', 'a', '閲囨牱']
    }
    
    for component_name, keywords in component_keywords.items():
        if any(keyword in fault_lower for keyword in keywords):
            return component_name
    
    return None

def create_intelligent_mappings():
    """鍒涘缓鏅鸿兘鐨勬祴璇曠偣-閮ㄤ欢鏄犲皠"""
    print("\n馃椇锔? 鍒涘缓鏅鸿兘鐨勬祴璇曠偣-閮ㄤ欢鏄犲皠")
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 澶勭悊PHM妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 鍒犻櫎鐜版湁鏄犲皠
        existing_mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
        if existing_mappings.exists():
            existing_mappings.delete()
            print(f"  馃棏锔? 鍒犻櫎浜?{existing_mappings.count()} 涓幇鏈夋槧灏?)
        
        # 鑾峰彇娴嬭瘯鐐瑰悕绉?
        test_names = active_msfg.test_names or []
        component_names = active_msfg.component_names or []
        
        if not component_names:
            print(f"  鈿狅笍  娌℃湁鍙敤鐨勯儴浠跺悕绉帮紝璺宠繃鏄犲皠鍒涘缓")
            continue
        
        print(f"  馃搳 娴嬭瘯鐐? {len(test_names)} 涓?)
        print(f"  馃敡 閮ㄤ欢: {len(component_names)} 涓?)
        
        # 鍒涘缓鏅鸿兘鏄犲皠
        created_count = 0
        for test_name in test_names:
            # 涓烘瘡涓祴璇曠偣鎵惧埌鏈€鍖归厤鐨勯儴浠?
            best_component = find_best_component_for_test(test_name, component_names)
            
            if best_component:
                # 鍒涘缓鏄犲皠
                TestPointComponentMapping.objects.create(
                    msfg_definition=active_msfg,
                    test_point_name=test_name,
                    component_name=best_component,
                    mapping_type='one_to_one',
                    weight=1.0,
                    component_type=get_component_type(best_component),
                    importance_weight=1.0,
                    is_critical=is_critical_test(test_name),
                    description=f'鏅鸿兘鏄犲皠: {test_name} -> {best_component}'
                )
                created_count += 1
                print(f"  鉁?{test_name} -> {best_component}")
        
        print(f"  馃搱 鎴愬姛鍒涘缓浜?{created_count} 涓槧灏?)

def find_best_component_for_test(test_name, component_names):
    """涓烘祴璇曠偣鎵惧埌鏈€鍖归厤鐨勯儴浠?""
    test_lower = test_name.lower()
    
    # 瀹氫箟娴嬭瘯鐐瑰埌閮ㄤ欢鐨勬槧灏勮鍒?
    mapping_rules = {
        '鐢垫簮绯荤粺': ['12v', '100v', '鐢靛帇', '鐢垫簮', '寮€鍏充俊鍙?],
        '鐢垫満绯荤粺': ['鐢垫満', '杞€?, '閫熷害', 'rpm', '椹卞姩'],
        '杞存壙绯荤粺': ['杞存俯', '娓╁害', '鍥虹揣绔?, '婊戝姩绔?],
        '鎺у埗绯荤粺': ['鎺у埗', '妗嗘灦', '澹虫俯'],
        '浼犳劅鍣ㄧ郴缁?: ['浣嶇疆', '閬ユ祴', '浼犳劅'],
        '鐢垫祦閲囨牱绯荤粺': ['鐢垫祦', '閲囨牱']
    }
    
    # 璁＄畻鍖归厤鍒嗘暟
    best_component = None
    best_score = 0
    
    for component in component_names:
        score = 0
        
        # 妫€鏌ユ槸鍚︽湁鐩存帴鐨勬槧灏勮鍒?
        if component in mapping_rules:
            keywords = mapping_rules[component]
            for keyword in keywords:
                if keyword in test_lower:
                    score += 2
        
        # 妫€鏌ュ悕绉扮浉浼煎害
        if component.lower() in test_lower or test_lower in component.lower():
            score += 1
        
        # 妫€鏌ュ叧閿瘝鍖归厤
        test_words = set(test_lower.split())
        component_words = set(component.lower().split())
        common_words = test_words & component_words
        score += len(common_words)
        
        if score > best_score:
            best_score = score
            best_component = component
    
    return best_component if best_score > 0 else component_names[0] if component_names else None

def get_component_type(component_name):
    """鏍规嵁閮ㄤ欢鍚嶇О鑾峰彇閮ㄤ欢绫诲瀷"""
    name_lower = component_name.lower()
    
    if any(keyword in name_lower for keyword in ['鐢垫満', 'motor']):
        return 'motor'
    elif any(keyword in name_lower for keyword in ['杞存壙', 'bearing']):
        return 'bearing'
    elif any(keyword in name_lower for keyword in ['鎺у埗', 'control']):
        return 'control'
    elif any(keyword in name_lower for keyword in ['鐢垫簮', 'power']):
        return 'power'
    elif any(keyword in name_lower for keyword in ['浼犳劅', 'sensor']):
        return 'sensor'
    else:
        return 'other'

def is_critical_test(test_name):
    """鍒ゆ柇娴嬭瘯鐐规槸鍚︿负鍏抽敭娴嬭瘯鐐?""
    critical_keywords = ['杞存俯', '娓╁害', '鐢垫祦', '鐢靛帇', '杞€?]
    test_lower = test_name.lower()
    
    return any(keyword in test_lower for keyword in critical_keywords)

def verify_mappings():
    """楠岃瘉鍒涘缓鐨勬槧灏?""
    print("\n鉁?楠岃瘉鍒涘缓鐨勬槧灏?)
    
    cmg_models = PHMModel.objects.all()
    
    for cmg_model in cmg_models:
        print(f"\n馃搵 楠岃瘉PHM妯″瀷: {cmg_model.model_name}")
        
        active_msfg = get_active_msfg_for_cmg_model(cmg_model)
        if not active_msfg:
            continue
        
        print(f"  鉁?MSFG: {active_msfg.name}")
        
        # 妫€鏌ユ槧灏勬暟閲?
        mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
        print(f"  馃搳 鏄犲皠鏁伴噺: {mappings.count()}")
        
        if mappings.exists():
            # 缁熻鏄犲皠鎯呭喌
            test_points = set()
            components = set()
            for mapping in mappings:
                test_points.add(mapping.test_point_name)
                components.add(mapping.component_name)
            
            print(f"  馃攳 鏄犲皠鐨勬祴璇曠偣: {len(test_points)} 涓?)
            print(f"  馃敡 鏄犲皠鐨勯儴浠? {len(components)} 涓?)
            
            # 鏄剧ず鏄犲皠璇︽儏
            for mapping in mappings[:5]:  # 鏄剧ず鍓?涓?
                print(f"    {mapping.test_point_name} -> {mapping.component_name} ({mapping.component_type})")
            
            # 妫€鏌ヨ鐩栫巼
            test_names = active_msfg.test_names or []
            mapped_tests = len(test_points)
            total_tests = len(test_names)
            
            if total_tests > 0:
                coverage = (mapped_tests / total_tests) * 100
                print(f"  馃搱 娴嬭瘯鐐硅鐩栫巼: {coverage:.1f}% ({mapped_tests}/{total_tests})")

def main():
    """涓诲嚱鏁?""
    print("馃殌 寮€濮嬩慨澶峂SFG娴嬬偣-閮ㄤ欢鏄犲皠闂")
    
    # 1. 淇MSFG瀹氫箟涓殑component_names瀛楁
    fix_msfg_component_names()
    
    # 2. 鍒涘缓鏅鸿兘鐨勬祴璇曠偣-閮ㄤ欢鏄犲皠
    create_intelligent_mappings()
    
    # 3. 楠岃瘉鍒涘缓鐨勬槧灏?
    verify_mappings()
    
    print("\n" + "=" * 60)
    print("鉁?淇瀹屾垚")
    print("=" * 60)

if __name__ == "__main__":
    main()

