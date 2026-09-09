#!/usr/bin/env python
"""
娴嬭瘯娴嬭瘯鐐?閮ㄤ欢鏄犲皠绠＄悊鍔熻兘
"""

import os
import sys
import django
import json

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM, PHMModel
from msfg_analysis.models import MSFGDefinition, MSFGNode, TestPointComponentMapping

def test_component_mappings():
    """娴嬭瘯娴嬭瘯鐐?閮ㄤ欢鏄犲皠绠＄悊鍔熻兘"""
    print("寮€濮嬫祴璇曟祴璇曠偣-閮ㄤ欢鏄犲皠绠＄悊鍔熻兘...")
    
    try:
        # 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
        active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
        if not active_msfg:
            print("鉂?鏈壘鍒版椿璺冪殑MSFG瀹氫箟")
            return False
        
        print(f"鉁?浣跨敤娲昏穬鐨凪SFG: {active_msfg.name}")
        
        # 鑾峰彇MSFG鑺傜偣
        test_nodes = list(active_msfg.nodes.filter(node_type='test').order_by('created_at'))
        fault_nodes = list(active_msfg.nodes.filter(node_type='fault').order_by('created_at'))
        
        print(f"娴嬭瘯鐐规暟閲? {len(test_nodes)}")
        print(f"鏁呴殰鐐规暟閲? {len(fault_nodes)}")
        
        # 鎵撳嵃娴嬭瘯鐐瑰悕绉?
        print("\n娴嬭瘯鐐瑰悕绉?")
        for i, node in enumerate(test_nodes):
            print(f"  {i}: {node.name}")
        
        # 鎵撳嵃鏁呴殰鐐瑰悕绉帮紙浣滀负閮ㄤ欢锛?
        print("\n鏁呴殰鐐瑰悕绉帮紙浣滀负閮ㄤ欢锛?")
        for i, node in enumerate(fault_nodes):
            print(f"  {i}: {node.name}")
        
        # 鍒涘缓涓€浜涙祴璇曟槧灏?
        test_mappings = [
            {
                'test_point': test_nodes[0].name if test_nodes else '娴嬭瘯鐐?',
                'component': fault_nodes[0].name if fault_nodes else '鏁呴殰鐐?',
                'mapping_type': 'one_to_one',
                'weight': 1.0,
                'description': '娴嬭瘯鏄犲皠1'
            },
            {
                'test_point': test_nodes[1].name if len(test_nodes) > 1 else '娴嬭瘯鐐?',
                'component': fault_nodes[1].name if len(fault_nodes) > 1 else '鏁呴殰鐐?',
                'mapping_type': 'one_to_many',
                'weight': 0.8,
                'description': '娴嬭瘯鏄犲皠2'
            }
        ]
        
        print(f"\n鍒涘缓娴嬭瘯鏄犲皠...")
        
        # 鍒犻櫎鐜版湁鏄犲皠
        TestPointComponentMapping.objects.filter(msfg_definition=active_msfg).delete()
        
        # 鍒涘缓鏂版槧灏?
        created_mappings = []
        for mapping_data in test_mappings:
            mapping = TestPointComponentMapping.objects.create(
                msfg_definition=active_msfg,
                test_point_name=mapping_data['test_point'],
                component_name=mapping_data['component'],
                mapping_type=mapping_data['mapping_type'],
                weight=mapping_data['weight'],
                description=mapping_data['description']
            )
            created_mappings.append(mapping)
            print(f"鉁?鍒涘缓鏄犲皠: {mapping.test_point_name} -> {mapping.component_name}")
        
        # 楠岃瘉鏄犲皠
        saved_mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
        print(f"\n淇濆瓨鐨勬槧灏勬暟閲? {saved_mappings.count()}")
        
        for mapping in saved_mappings:
            print(f"  {mapping.test_point_name} -> {mapping.component_name} ({mapping.mapping_type}, 鏉冮噸: {mapping.weight})")
        
        # 娴嬭瘯API鏍煎紡
        api_mappings = []
        for mapping in saved_mappings:
            api_mappings.append({
                'id': mapping.id,
                'test_point': mapping.test_point_name,
                'component': mapping.component_name,
                'mapping_type': mapping.mapping_type,
                'weight': mapping.weight,
                'description': mapping.description
            })
        
        print(f"\nAPI鏍煎紡鏄犲皠:")
        for mapping in api_mappings:
            print(f"  {mapping['test_point']} -> {mapping['component']} ({mapping['mapping_type']}, 鏉冮噸: {mapping['weight']})")
        
        print(f"\n馃帀 娴嬭瘯鐐?閮ㄤ欢鏄犲皠绠＄悊鍔熻兘娴嬭瘯瀹屾垚锛?)
        return True
        
    except Exception as e:
        print(f"鉂?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_component_mappings()
    if success:
        print("\n馃帀 鎵€鏈夋祴璇曢€氳繃锛佹祴璇曠偣-閮ㄤ欢鏄犲皠绠＄悊鍔熻兘姝ｅ父宸ヤ綔")
    else:
        print("\n鉂?娴嬭瘯澶辫触锛岄渶瑕佹鏌ラ棶棰?)

