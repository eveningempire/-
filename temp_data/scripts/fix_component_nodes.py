#!/usr/bin/env python
"""
淇閮ㄤ欢鑺傜偣鍚嶇О闂
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge
from django.db import transaction

def fix_component_nodes():
    """淇閮ㄤ欢鑺傜偣鍚嶇О闂"""
    print("=== 淇閮ㄤ欢鑺傜偣鍚嶇О闂 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    
    # 2. 鑾峰彇姝ｇ‘鐨勯儴浠跺悕绉板垪琛?
    component_names = active_msfg.component_names or []
    print(f"馃搵 姝ｇ‘鐨勯儴浠跺悕绉? {component_names}")
    
    if not component_names:
        print("鉂?娌℃湁閮ㄤ欢鍚嶇О鍒楄〃")
        return False
    
    # 3. 鑾峰彇鎵€鏈夐儴浠惰妭鐐?
    component_nodes = MSFGNode.objects.filter(
        msfg_definition=active_msfg,
        node_type='system'
    ).exclude(name__in=component_names)  # 鎺掗櫎宸茬粡鏈夋纭悕绉扮殑鑺傜偣
    
    print(f"馃敡 闇€瑕佷慨澶嶇殑閮ㄤ欢鑺傜偣鏁伴噺: {component_nodes.count()}")
    
    # 4. 淇閮ㄤ欢鑺傜偣鍚嶇О
    try:
        with transaction.atomic():
            fixed_count = 0
            
            # 鑾峰彇鎵€鏈夐渶瑕佷慨澶嶇殑閮ㄤ欢鑺傜偣
            nodes_to_fix = list(component_nodes)
            
            # 涓烘瘡涓儴浠惰妭鐐瑰垎閰嶆纭殑鍚嶇О
            for i, node in enumerate(nodes_to_fix):
                if i < len(component_names):
                    old_name = node.name
                    new_name = component_names[i]
                    
                    print(f"   淇鑺傜偣 {node.id}: '{old_name}' -> '{new_name}'")
                    
                    node.name = new_name
                    node.save()
                    fixed_count += 1
                else:
                    print(f"   鈿狅笍 鑺傜偣 {node.id} 娌℃湁瀵瑰簲鐨勯儴浠跺悕绉帮紝璺宠繃")
            
            print(f"\n鉁?淇瀹屾垚! 淇浜?{fixed_count} 涓儴浠惰妭鐐?)
            
    except Exception as e:
        print(f"鉂?淇澶辫触: {e}")
        return False
    
    # 5. 楠岃瘉淇缁撴灉
    print(f"\n馃攳 楠岃瘉淇缁撴灉:")
    
    # 妫€鏌ヤ慨澶嶅悗鐨勯儴浠惰妭鐐?
    fixed_component_nodes = MSFGNode.objects.filter(
        msfg_definition=active_msfg,
        node_type='system'
    )
    
    print(f"   淇鍚庣殑閮ㄤ欢鑺傜偣:")
    for node in fixed_component_nodes:
        print(f"     ID: {node.id}, 鍚嶇О: '{node.name}'")
    
    # 妫€鏌ユ槸鍚︽墍鏈夐儴浠跺悕绉伴兘鏈夊搴旂殑鑺傜偣
    node_names = set(fixed_component_nodes.values_list('name', flat=True))
    missing_components = set(component_names) - node_names
    
    if missing_components:
        print(f"   鈿狅笍 缂哄皯閮ㄤ欢鑺傜偣: {missing_components}")
    else:
        print(f"   鉁?鎵€鏈夐儴浠跺悕绉伴兘鏈夊搴旂殑鑺傜偣")
    
    return True

def test_auto_mapping_after_fix():
    """淇鍚庢祴璇曡嚜鍔ㄦ槧灏?""
    print(f"\n馃И 淇鍚庢祴璇曡嚜鍔ㄦ槧灏?")
    
    try:
        from msfg_analysis.algorithms.msfg.auto_mapping import auto_extract_msfg_mappings
        
        # 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
        active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
        
        # 娴嬭瘯鑷姩鏄犲皠
        mappings = auto_extract_msfg_mappings(active_msfg)
        
        print(f"   鑷姩鏄犲皠缁撴灉: {len(mappings)} 涓祴璇曠偣")
        
        if mappings:
            print(f"   鏄犲皠绀轰緥:")
            for i, (test_name, component_mappings) in enumerate(mappings.items()):
                if i >= 5:  # 鍙樉绀哄墠5涓?
                    break
                print(f"     {test_name} -> {component_mappings[:3]}")  # 鍙樉绀哄墠3涓儴浠?
        
        return True
        
    except Exception as e:
        print(f"   鉂?鑷姩鏄犲皠娴嬭瘯澶辫触: {e}")
        return False

if __name__ == "__main__":
    if fix_component_nodes():
        test_auto_mapping_after_fix()

