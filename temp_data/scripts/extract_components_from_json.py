#!/usr/bin/env python
"""
浠嶫SON閰嶇疆鏂囦欢涓纭彁鍙栭儴浠?
鍩轰簬澶氫俊鍙锋祦鍥鹃厤缃?json鏂囦欢鎻愬彇閮ㄤ欢骞舵洿鏂?00NM鐨凪SFG閰嶇疆
"""

import os
import sys
import django
import json

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition, MSFGNode, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.component_integration import ensure_msfg_component_mappings

def extract_components_from_json():
    """浠嶫SON閰嶇疆鏂囦欢涓彁鍙栭儴浠?""
    print("馃敡 浠嶫SON閰嶇疆鏂囦欢涓彁鍙栭儴浠?)
    print("=" * 80)
    
    try:
        # 1. 璇诲彇JSON閰嶇疆鏂囦欢
        json_file_path = "澶氫俊鍙锋祦鍥鹃厤缃?json"
        if not os.path.exists(json_file_path):
            print(f"鉂?鎵句笉鍒版枃浠? {json_file_path}")
            return False
        
        print(f"鉁?鎵惧埌閰嶇疆鏂囦欢: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 2. 浠嶴ystemData涓彁鍙栭儴浠?
        print(f"\n馃攧 浠嶴ystemData涓彁鍙栭儴浠?..")
        components = []
        
        if 'SystemData' in config_data:
            system_data = config_data['SystemData']
            print(f"   鎵惧埌 {len(system_data)} 涓郴缁熸暟鎹」")
            
            for system_item in system_data:
                if 'data' in system_item and 'nodes' in system_item['data']:
                    nodes = system_item['data']['nodes']
                    print(f"   绯荤粺 {system_item.get('system_id', 'unknown')} 鏈?{len(nodes)} 涓妭鐐?)
                    
                    for node in nodes:
                        node_type = node.get('type', '')
                        # 鏌ユ壘subsystem-node绫诲瀷鐨勮妭鐐?
                        if node_type == 'subsystem-node':
                            # 浠巔roperties.tableName涓彁鍙栭儴浠跺悕绉?
                            properties = node.get('properties', {})
                            table_name = properties.get('tableName', '')
                            
                            if table_name and table_name.strip():
                                components.append(table_name.strip())
                                print(f"      鉁?鎻愬彇鍒伴儴浠? {table_name}")
        
        # 鍘婚噸骞舵帓搴?
        components = sorted(list(set(components)))
        print(f"\n馃搵 鎻愬彇缁撴灉:")
        print(f"   鎻愬彇鍒?{len(components)} 涓敮涓€閮ㄤ欢:")
        for i, comp in enumerate(components, 1):
            print(f"     {i}. {comp}")
        
        if not components:
            print("鉂?娌℃湁鎻愬彇鍒颁换浣曢儴浠?)
            return False
        
        # 3. 鏌ユ壘200NM鐨凜MG妯″瀷鍜孧SFG閰嶇疆
        cmg_model = PHMModel.objects.get(model_name="200NM")
        print(f"\n鉁?鎵惧埌PHM妯″瀷: {cmg_model.model_name} (ID: {cmg_model.id})")
        
        active_msfg = MSFGDefinition.objects.filter(
            cmg_model=cmg_model,
            is_active=True
        ).order_by('-updated_at').first()
        
        if not active_msfg:
            print("鉂?娌℃湁鎵惧埌200NM鐨勬椿璺僊SFG閰嶇疆")
            return False
        
        print(f"鉁?鎵惧埌娲昏穬MSFG: {active_msfg.name} (ID: {active_msfg.id})")
        
        # 4. 鏇存柊MSFG鐨刢omponent_names瀛楁
        print(f"\n馃攧 鏇存柊MSFG鐨刢omponent_names瀛楁...")
        active_msfg.component_names = components
        active_msfg.save(update_fields=['component_names', 'updated_at'])
        print(f"鉁?宸叉洿鏂癱omponent_names瀛楁")
        
        # 5. 鍒涘缓绯荤粺鑺傜偣
        print(f"\n馃攧 鍒涘缓绯荤粺鑺傜偣...")
        
        # 鍏堝垹闄ょ幇鏈夌殑绯荤粺鑺傜偣
        existing_system_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='system'
        )
        if existing_system_nodes.exists():
            existing_system_nodes.delete()
            print(f"   宸插垹闄?{existing_system_nodes.count()} 涓幇鏈夌郴缁熻妭鐐?)
        
        # 鍒涘缓鏂扮殑绯荤粺鑺傜偣
        created_nodes = 0
        for i, component_name in enumerate(components):
            # 涓烘瘡涓儴浠跺垱寤轰竴涓郴缁熻妭鐐?
            node = MSFGNode.objects.create(
                node_id=f"system_{i+1}_{component_name}",
                msfg_definition=active_msfg,
                name=component_name,
                node_type='system',
                position_x=100 + (i % 5) * 200,  # 绠€鍗曠殑甯冨眬
                position_y=100 + (i // 5) * 150,
                properties={'tableName': component_name}
            )
            created_nodes += 1
            print(f"   鉁?鍒涘缓绯荤粺鑺傜偣: {component_name}")
        
        print(f"鉁?鎴愬姛鍒涘缓 {created_nodes} 涓郴缁熻妭鐐?)
        
        # 6. 閲嶆柊杩愯閮ㄤ欢鏄犲皠
        print(f"\n馃攧 閲嶆柊杩愯閮ㄤ欢鏄犲皠...")
        try:
            ensure_msfg_component_mappings(active_msfg)
            print(f"鉁?閮ㄤ欢鏄犲皠鏇存柊瀹屾垚")
        except Exception as e:
            print(f"鉂?閮ㄤ欢鏄犲皠鏇存柊澶辫触: {e}")
            return False
        
        # 7. 楠岃瘉缁撴灉
        print(f"\n馃攳 楠岃瘉缁撴灉...")
        
        # 妫€鏌omponent_names瀛楁
        active_msfg.refresh_from_db()
        if active_msfg.component_names:
            print(f"鉁?component_names瀛楁宸叉洿鏂? {len(active_msfg.component_names)} 涓儴浠?)
        else:
            print("鉂?component_names瀛楁浠嶄负绌?)
            return False
        
        # 妫€鏌ョ郴缁熻妭鐐?
        system_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='system'
        )
        print(f"鉁?绯荤粺鑺傜偣鏁伴噺: {system_nodes.count()}")
        
        # 妫€鏌ユ祴璇曠偣-閮ㄤ欢鏄犲皠
        mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
        print(f"鉁?娴嬭瘯鐐?閮ㄤ欢鏄犲皠鏁伴噺: {mappings.count()}")
        
        # 8. 鏄剧ず鏈€缁堢粨鏋?
        print(f"\n馃帀 鎻愬彇瀹屾垚锛?)
        print(f"   浠嶫SON鏂囦欢鎻愬彇鐨勯儴浠?")
        for i, comp in enumerate(active_msfg.component_names, 1):
            print(f"     {i}. {comp}")
        
        return True
        
    except PHMModel.DoesNotExist:
        print("鉂?鎵句笉鍒?00NM鐨凜MG妯″瀷")
        return False
    except Exception as e:
        print(f"鉂?鎻愬彇杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """涓诲嚱鏁?""
    success = extract_components_from_json()
    
    if success:
        print(f"\n馃帀 鎻愬彇鎴愬姛锛?)
        print("鐜板湪鍙互灏濊瘯鍦∕SFG閮ㄤ欢瀵瑰簲绠＄悊椤甸潰涓粦瀹氭槧灏勪簡銆?)
        print("寤鸿杩愯浠ヤ笅鍛戒护鏉ラ獙璇佺粨鏋?")
        print("python scripts/check_msfg_save_logic.py")
    else:
        print(f"\n鉂?鎻愬彇澶辫触锛?)
        print("璇锋鏌?")
        print("1. JSON閰嶇疆鏂囦欢鏄惁瀛樺湪")
        print("2. 閰嶇疆鏂囦欢鏍煎紡鏄惁姝ｇ‘")
        print("3. 200NM鐨凪SFG閰嶇疆鏄惁瀛樺湪")

if __name__ == "__main__":
    main()

