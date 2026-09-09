#!/usr/bin/env python
"""
妫€鏌SFG淇濆瓨鏃剁殑閮ㄤ欢鎻愬彇閫昏緫
鍒嗘瀽涓轰粈涔?00NM鏃犳硶姝ｇ‘鎻愬彇閮ㄤ欢
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition, MSFGNode

def check_msfg_save_logic():
    """妫€鏌SFG淇濆瓨鏃剁殑閮ㄤ欢鎻愬彇閫昏緫"""
    print("馃攳 妫€鏌SFG淇濆瓨鏃剁殑閮ㄤ欢鎻愬彇閫昏緫")
    print("=" * 80)
    
    # 妫€鏌?00NM鍜?00NM鐨勫姣?
    for model_name in ["500NM", "200NM"]:
        print(f"\n馃搳 鍒嗘瀽 {model_name}:")
        print("-" * 60)
        
        try:
            # 1. 鏌ユ壘PHM妯″瀷
            cmg_model = PHMModel.objects.get(model_name=model_name)
            print(f"鉁?鎵惧埌PHM妯″瀷: {cmg_model.model_name} (ID: {cmg_model.id})")
            
            # 2. 鏌ユ壘娲昏穬鐨凪SFG閰嶇疆
            active_msfg = MSFGDefinition.objects.filter(
                cmg_model=cmg_model,
                is_active=True
            ).order_by('-updated_at').first()
            
            if not active_msfg:
                print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG閰嶇疆")
                continue
            
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
            
            # 6. 妯℃嫙MSFG淇濆瓨鏃剁殑閮ㄤ欢鎻愬彇閫昏緫
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
            
            # 7. 瀵规瘮鍒嗘瀽
            print(f"\n馃搳 瀵规瘮鍒嗘瀽:")
            print(f"   component_names瀛楁: {len(active_msfg.component_names) if active_msfg.component_names else 0} 涓?)
            print(f"   MSFGNode绯荤粺鑺傜偣: {system_nodes.count()} 涓?)
            print(f"   妯℃嫙鎻愬彇閮ㄤ欢: {len(components)} 涓?)
            
            if active_msfg.component_names and components:
                # 妫€鏌ユ槸鍚︿竴鑷?
                expected_components = set(active_msfg.component_names)
                actual_components = set(components)
                if expected_components == actual_components:
                    print("   鉁?閮ㄤ欢鎻愬彇涓€鑷?)
                else:
                    print("   鉂?閮ㄤ欢鎻愬彇涓嶄竴鑷?)
                    missing = expected_components - actual_components
                    extra = actual_components - expected_components
                    if missing:
                        print(f"     缂哄皯: {missing}")
                    if extra:
                        print(f"     澶氫綑: {extra}")
            
        except PHMModel.DoesNotExist:
            print(f"鉂?鎵句笉鍒癈MG妯″瀷: {model_name}")
        except Exception as e:
            print(f"鉂?鍒嗘瀽杩囩▼涓嚭閿? {e}")

def main():
    """涓诲嚱鏁?""
    check_msfg_save_logic()
    
    print(f"\n馃挕 鍒嗘瀽寤鸿:")
    print("濡傛灉200NM鐨刢omponent_names瀛楁涓虹┖锛屼絾鍘熷鍥炬暟鎹腑鏈夌郴缁熻妭鐐癸紝")
    print("璇存槑MSFG淇濆瓨鏃剁殑閮ㄤ欢鎻愬彇閫昏緫娌℃湁姝ｇ‘鎵ц銆?)
    print("鍙兘闇€瑕侀噸鏂颁繚瀛楳SFG閰嶇疆鎴栨墜鍔ㄨЕ鍙戦儴浠舵彁鍙栥€?)

if __name__ == "__main__":
    main()

