#!/usr/bin/env python
"""
妫€鏌?5NM鐨勫綋鍓嶇姸鎬?
鍒嗘瀽15NM鐨凪SFG閰嶇疆鍜岄儴浠舵彁鍙栨儏鍐?
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition, MSFGNode, TestPointComponentMapping

def check_15nm_status():
    """妫€鏌?5NM鐨勫綋鍓嶇姸鎬?""
    print("馃攳 妫€鏌?5NM鐨勫綋鍓嶇姸鎬?)
    print("=" * 80)
    
    try:
        # 1. 鏌ユ壘15NM鐨凜MG妯″瀷
        cmg_model = PHMModel.objects.get(model_name="15NM")
        print(f"鉁?鎵惧埌PHM妯″瀷: {cmg_model.model_name} (ID: {cmg_model.id})")
        
        # 2. 鏌ユ壘娲昏穬鐨凪SFG閰嶇疆
        active_msfg = MSFGDefinition.objects.filter(
            cmg_model=cmg_model,
            is_active=True
        ).order_by('-updated_at').first()
        
        if not active_msfg:
            print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG閰嶇疆")
            return False
        
        print(f"鉁?鎵惧埌娲昏穬MSFG: {active_msfg.name} (ID: {active_msfg.id})")
        print(f"   鍒涘缓鏃堕棿: {active_msfg.created_at}")
        print(f"   鏇存柊鏃堕棿: {active_msfg.updated_at}")
        
        # 3. 妫€鏌omponent_names瀛楁
        print(f"\n馃搵 component_names瀛楁:")
        if active_msfg.component_names:
            print(f"   鉁?鏈夐儴浠跺垪琛? {len(active_msfg.component_names)} 涓?)
            for i, comp in enumerate(active_msfg.component_names, 1):
                print(f"     {i}. {comp}")
        else:
            print("   鉂?component_names瀛楁涓虹┖")
        
        # 4. 妫€鏌ュ師濮嬪浘鏁版嵁涓殑绯荤粺鑺傜偣
        print(f"\n馃敡 鍘熷鍥炬暟鎹腑鐨勭郴缁熻妭鐐?")
        if active_msfg.raw_graph_data:
            raw_data = active_msfg.raw_graph_data
            if isinstance(raw_data, dict) and 'nodes' in raw_data:
                raw_nodes = raw_data['nodes']
                print(f"   鍘熷鑺傜偣鎬绘暟: {len(raw_nodes)}")
                
                # 鍒嗘瀽绯荤粺鑺傜偣
                system_nodes_raw = []
                for node in raw_nodes:
                    node_type = str(node.get('type', '')).lower()
                    if 'system' in node_type and 'root' not in node_type:
                        system_nodes_raw.append(node)
                
                print(f"   绯荤粺鑺傜偣鏁伴噺: {len(system_nodes_raw)}")
                for node in system_nodes_raw:
                    node_type = node.get('type', '')
                    node_name = (
                        (node.get('text') or {}).get('value') or 
                        node.get('name') or 
                        (node.get('properties') or {}).get('tableName') or 
                        node.get('id')
                    )
                    print(f"      - 绫诲瀷: {node_type}, 鍚嶇О: '{node_name}'")
            else:
                print("   鉂?鍘熷鍥炬暟鎹牸寮忎笉姝ｇ‘")
        else:
            print("   鉂?娌℃湁鍘熷鍥炬暟鎹?)
        
        # 5. 妫€鏌SFGNode琛ㄤ腑鐨勭郴缁熻妭鐐?
        print(f"\n馃敡 MSFGNode琛ㄤ腑鐨勭郴缁熻妭鐐?")
        system_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='system'
        ).exclude(name__in=['root', 'system', ''])
        
        print(f"   绯荤粺鑺傜偣鏁伴噺: {system_nodes.count()}")
        for node in system_nodes:
            print(f"      - ID: {node.node_id}, 鍚嶇О: '{node.name}'")
        
        # 6. 妫€鏌ユ祴璇曠偣-閮ㄤ欢鏄犲皠
        print(f"\n馃敆 娴嬭瘯鐐?閮ㄤ欢鏄犲皠:")
        mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
        print(f"   鏄犲皠鏁伴噺: {mappings.count()}")
        
        if mappings.exists():
            print("   鏄犲皠鍒楄〃:")
            for mapping in mappings:
                print(f"      - 娴嬭瘯鐐? '{mapping.test_point_name}' 鈫?閮ㄤ欢: '{mapping.component_name}'")
        else:
            print("   鉂?娌℃湁娴嬭瘯鐐?閮ㄤ欢鏄犲皠")
        
        # 7. 妯℃嫙MSFG淇濆瓨鏃剁殑閮ㄤ欢鎻愬彇閫昏緫
        print(f"\n馃攧 妯℃嫙MSFG淇濆瓨鏃剁殑閮ㄤ欢鎻愬彇閫昏緫:")
        components = []
        
        # 浠庡師濮嬪浘鏁版嵁涓彁鍙栵紙妯℃嫙淇濆瓨鏃剁殑閫昏緫锛?
        if active_msfg.raw_graph_data:
            raw_data = active_msfg.raw_graph_data
            if isinstance(raw_data, dict) and 'nodes' in raw_data:
                raw_nodes = raw_data['nodes']
                for node in raw_nodes:
                    node_type = str(node.get('type') or '')
                    if ('system' in node_type or 'component' in node_type) and 'root' not in node_type.lower():
                        name = (
                            (node.get('text') or {}).get('value') or 
                            node.get('name') or 
                            (node.get('properties') or {}).get('tableName') or 
                            node.get('id')
                        )
                        name = str(name).strip() if name else ''
                        if name and name.lower() not in ['root', 'system', '']:
                            components.append(name)
        
        # 鍘婚噸骞舵帓搴?
        components = sorted(list(set(components)))
        print(f"   妯℃嫙鎻愬彇鐨勯儴浠舵暟閲? {len(components)}")
        for i, comp in enumerate(components, 1):
            print(f"     {i}. {comp}")
        
        # 8. 瀵规瘮鍒嗘瀽
        print(f"\n馃搳 瀵规瘮鍒嗘瀽:")
        print(f"   component_names瀛楁: {len(active_msfg.component_names) if active_msfg.component_names else 0} 涓?)
        print(f"   MSFGNode绯荤粺鑺傜偣: {system_nodes.count()} 涓?)
        print(f"   妯℃嫙鎻愬彇閮ㄤ欢: {len(components)} 涓?)
        print(f"   娴嬭瘯鐐?閮ㄤ欢鏄犲皠: {mappings.count()} 涓?)
        
        # 9. 闂璇婃柇
        print(f"\n馃攳 闂璇婃柇:")
        if not active_msfg.component_names:
            print("   鉂?闂1: component_names瀛楁涓虹┖")
        if system_nodes.count() == 0:
            print("   鉂?闂2: 娌℃湁绯荤粺鑺傜偣")
        if len(components) == 0:
            print("   鉂?闂3: 鏃犳硶浠庡師濮嬪浘鏁版嵁鎻愬彇閮ㄤ欢")
        if mappings.count() == 0:
            print("   鈿狅笍 娉ㄦ剰: 娌℃湁娴嬭瘯鐐?閮ㄤ欢鏄犲皠锛堣繖鏄甯哥殑锛屽洜涓烘偍鎻愬埌娌℃湁缁戝畾娴嬬偣瑙勫垯锛?)
        
        if active_msfg.component_names and system_nodes.count() > 0:
            print("   鉁?15NM閰嶇疆鍩烘湰姝ｅ父")
        else:
            print("   鉂?15NM閰嶇疆闇€瑕佷慨澶?)
        
        return True
        
    except PHMModel.DoesNotExist:
        print("鉂?鎵句笉鍒?5NM鐨凜MG妯″瀷")
        return False
    except Exception as e:
        print(f"鉂?妫€鏌ヨ繃绋嬩腑鍑洪敊: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """涓诲嚱鏁?""
    check_15nm_status()

if __name__ == "__main__":
    main()

