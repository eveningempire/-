#!/usr/bin/env python
"""
鎵嬪姩瑙﹀彂200NM鐨勯儴浠舵彁鍙?
鍩轰簬鍘熷鍥炬暟鎹噸鏂版彁鍙栭儴浠跺苟鏇存柊MSFG閰嶇疆
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
from msfg_analysis.algorithms.msfg.component_integration import ensure_msfg_component_mappings

def manual_extract_200nm_components():
    """鎵嬪姩瑙﹀彂200NM鐨勯儴浠舵彁鍙?""
    print("馃敡 鎵嬪姩瑙﹀彂200NM鐨勯儴浠舵彁鍙?)
    print("=" * 80)
    
    try:
        # 1. 鏌ユ壘200NM鐨凜MG妯″瀷
        cmg_model = PHMModel.objects.get(model_name="200NM")
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
        
        # 3. 妫€鏌ュ師濮嬪浘鏁版嵁
        if not active_msfg.raw_graph_data:
            print("鉂?娌℃湁鍘熷鍥炬暟鎹紝鏃犳硶鎻愬彇閮ㄤ欢")
            return False
        
        print(f"鉁?鏈夊師濮嬪浘鏁版嵁")
        
        # 4. 浠庡師濮嬪浘鏁版嵁涓彁鍙栭儴浠?
        print(f"\n馃攧 浠庡師濮嬪浘鏁版嵁涓彁鍙栭儴浠?..")
        components = []
        
        raw_data = active_msfg.raw_graph_data
        if isinstance(raw_data, dict) and 'nodes' in raw_data:
            raw_nodes = raw_data['nodes']
            print(f"   鍘熷鑺傜偣鎬绘暟: {len(raw_nodes)}")
            
            for node in raw_nodes:
                node_type = str(node.get('type') or '')
                # 妫€鏌ユ槸鍚︽槸绯荤粺鑺傜偣锛堥儴浠惰妭鐐癸級
                if ('system' in node_type or 'component' in node_type) and 'root' not in node_type.lower():
                    # 鎻愬彇鑺傜偣鍚嶇О
                    name = (
                        (node.get('text') or {}).get('value') or 
                        node.get('name') or 
                        (node.get('properties') or {}).get('tableName') or 
                        node.get('id')
                    )
                    name = str(name).strip() if name else ''
                    
                    # 杩囨护鎺夋棤鏁堝悕绉?
                    if name and name.lower() not in ['root', 'system', '']:
                        components.append(name)
                        print(f"      鉁?鎻愬彇鍒伴儴浠? {name} (绫诲瀷: {node_type})")
        
        # 鍘婚噸骞舵帓搴?
        components = sorted(list(set(components)))
        print(f"\n馃搵 鎻愬彇缁撴灉:")
        print(f"   鎻愬彇鍒?{len(components)} 涓儴浠?")
        for i, comp in enumerate(components, 1):
            print(f"     {i}. {comp}")
        
        if not components:
            print("鉂?娌℃湁鎻愬彇鍒颁换浣曢儴浠?)
            return False
        
        # 5. 鏇存柊MSFG鐨刢omponent_names瀛楁
        print(f"\n馃攧 鏇存柊MSFG鐨刢omponent_names瀛楁...")
        active_msfg.component_names = components
        active_msfg.save(update_fields=['component_names', 'updated_at'])
        print(f"鉁?宸叉洿鏂癱omponent_names瀛楁")
        
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
        
        # 妫€鏌ユ祴璇曠偣-閮ㄤ欢鏄犲皠
        mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
        print(f"鉁?娴嬭瘯鐐?閮ㄤ欢鏄犲皠鏁伴噺: {mappings.count()}")
        
        # 8. 鏄剧ず鏈€缁堢粨鏋?
        print(f"\n馃帀 鎵嬪姩鎻愬彇瀹屾垚锛?)
        print(f"   閮ㄤ欢鍒楄〃:")
        for i, comp in enumerate(active_msfg.component_names, 1):
            print(f"     {i}. {comp}")
        
        return True
        
    except PHMModel.DoesNotExist:
        print("鉂?鎵句笉鍒?00NM鐨凜MG妯″瀷")
        return False
    except Exception as e:
        print(f"鉂?鎻愬彇杩囩▼涓嚭閿? {e}")
        return False

def main():
    """涓诲嚱鏁?""
    success = manual_extract_200nm_components()
    
    if success:
        print(f"\n馃帀 鎵嬪姩鎻愬彇鎴愬姛锛?)
        print("鐜板湪鍙互灏濊瘯鍦∕SFG閮ㄤ欢瀵瑰簲绠＄悊椤甸潰涓粦瀹氭槧灏勪簡銆?)
    else:
        print(f"\n鉂?鎵嬪姩鎻愬彇澶辫触锛?)
        print("璇锋鏌?")
        print("1. MSFG閰嶇疆鏄惁姝ｇ‘")
        print("2. 鍘熷鍥炬暟鎹槸鍚﹀寘鍚郴缁熻妭鐐?)
        print("3. 鏄惁闇€瑕侀噸鏂颁繚瀛楳SFG閰嶇疆")

if __name__ == "__main__":
    main()

