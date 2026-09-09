#!/usr/bin/env python
"""
淇200NM鐨凪SFG鑺傜偣鏁版嵁
浠?00NM澶嶅埗绯荤粺鑺傜偣鍒?00NM
"""

import os
import sys
import django
import uuid

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHMModel
from msfg_analysis.models import MSFGDefinition, MSFGNode

def fix_200nm_msfg_nodes():
    """淇200NM鐨凪SFG鑺傜偣鏁版嵁"""
    print("馃敡 淇200NM鐨凪SFG鑺傜偣鏁版嵁")
    print("=" * 80)
    
    try:
        # 1. 鏌ユ壘500NM鍜?00NM鐨凜MG妯″瀷
        cmg_model_500nm = PHMModel.objects.get(model_name="500NM")
        cmg_model_200nm = PHMModel.objects.get(model_name="200NM")
        print(f"鉁?鎵惧埌500NM妯″瀷: {cmg_model_500nm.model_name} (ID: {cmg_model_500nm.id})")
        print(f"鉁?鎵惧埌200NM妯″瀷: {cmg_model_200nm.model_name} (ID: {cmg_model_200nm.id})")
        
        # 2. 鏌ユ壘娲昏穬鐨凪SFG閰嶇疆
        msfg_500nm = MSFGDefinition.objects.filter(
            cmg_model=cmg_model_500nm,
            is_active=True
        ).order_by('-updated_at').first()
        
        msfg_200nm = MSFGDefinition.objects.filter(
            cmg_model=cmg_model_200nm,
            is_active=True
        ).order_by('-updated_at').first()
        
        if not msfg_500nm:
            print("鉂?娌℃湁鎵惧埌500NM鐨勬椿璺僊SFG閰嶇疆")
            return False
        
        if not msfg_200nm:
            print("鉂?娌℃湁鎵惧埌200NM鐨勬椿璺僊SFG閰嶇疆")
            return False
        
        print(f"鉁?鎵惧埌500NM MSFG: {msfg_500nm.name} (ID: {msfg_500nm.id})")
        print(f"鉁?鎵惧埌200NM MSFG: {msfg_200nm.name} (ID: {msfg_200nm.id})")
        
        # 3. 鑾峰彇500NM鐨勭郴缁熻妭鐐?
        system_nodes_500nm = MSFGNode.objects.filter(
            msfg_definition=msfg_500nm,
            node_type='system'
        ).exclude(name__in=['root', 'system', ''])
        
        print(f"\n馃搵 500NM鐨勭郴缁熻妭鐐?({system_nodes_500nm.count()} 涓?:")
        for node in system_nodes_500nm:
            print(f"   - {node.name}")
        
        if not system_nodes_500nm.exists():
            print("鉂?500NM娌℃湁绯荤粺鑺傜偣锛屾棤娉曞鍒?)
            return False
        
        # 4. 妫€鏌?00NM鏄惁宸叉湁绯荤粺鑺傜偣
        existing_nodes_200nm = MSFGNode.objects.filter(
            msfg_definition=msfg_200nm,
            node_type='system'
        )
        
        if existing_nodes_200nm.exists():
            print(f"\n鈿狅笍 200NM宸叉湁 {existing_nodes_200nm.count()} 涓郴缁熻妭鐐?)
            response = input("鏄惁鍒犻櫎鐜版湁鑺傜偣骞堕噸鏂板鍒讹紵(y/N): ")
            if response.lower() != 'y':
                print("鉂?鐢ㄦ埛鍙栨秷鎿嶄綔")
                return False
            
            # 鍒犻櫎鐜版湁鑺傜偣
            existing_nodes_200nm.delete()
            print("鉁?宸插垹闄ょ幇鏈夌郴缁熻妭鐐?)
        
        # 5. 澶嶅埗绯荤粺鑺傜偣鍒?00NM
        print(f"\n馃攧 澶嶅埗绯荤粺鑺傜偣鍒?00NM...")
        copied_count = 0
        
        for node_500nm in system_nodes_500nm:
            # 鍒涘缓鏂扮殑鑺傜偣ID
            new_node_id = str(uuid.uuid4())
            
            # 澶嶅埗鑺傜偣
            new_node = MSFGNode.objects.create(
                node_id=new_node_id,
                msfg_definition=msfg_200nm,
                name=node_500nm.name,
                node_type=node_500nm.node_type,
                position_x=node_500nm.position_x,
                position_y=node_500nm.position_y,
                properties=node_500nm.properties
            )
            
            copied_count += 1
            print(f"   鉁?澶嶅埗鑺傜偣: {node_500nm.name}")
        
        print(f"鉁?鎴愬姛澶嶅埗 {copied_count} 涓郴缁熻妭鐐?)
        
        # 6. 澶嶅埗component_names瀛楁
        print(f"\n馃攧 澶嶅埗component_names瀛楁...")
        if msfg_500nm.component_names:
            msfg_200nm.component_names = msfg_500nm.component_names
            msfg_200nm.save(update_fields=['component_names', 'updated_at'])
            print(f"鉁?宸插鍒禼omponent_names瀛楁: {len(msfg_500nm.component_names)} 涓儴浠?)
        else:
            print("鈿狅笍 500NM鐨刢omponent_names瀛楁涓虹┖")
        
        # 7. 楠岃瘉缁撴灉
        print(f"\n馃攳 楠岃瘉缁撴灉...")
        
        # 妫€鏌?00NM鐨勭郴缁熻妭鐐?
        system_nodes_200nm = MSFGNode.objects.filter(
            msfg_definition=msfg_200nm,
            node_type='system'
        ).exclude(name__in=['root', 'system', ''])
        
        print(f"鉁?200NM绯荤粺鑺傜偣鏁伴噺: {system_nodes_200nm.count()}")
        for node in system_nodes_200nm:
            print(f"   - {node.name}")
        
        # 妫€鏌omponent_names瀛楁
        msfg_200nm.refresh_from_db()
        if msfg_200nm.component_names:
            print(f"鉁?200NM component_names瀛楁: {len(msfg_200nm.component_names)} 涓儴浠?)
        else:
            print("鉂?200NM component_names瀛楁浠嶄负绌?)
        
        # 8. 鏄剧ず鏈€缁堢粨鏋?
        print(f"\n馃帀 淇瀹屾垚锛?)
        print(f"   澶嶅埗鐨勭郴缁熻妭鐐? {copied_count} 涓?)
        print(f"   澶嶅埗鐨勯儴浠跺垪琛? {len(msfg_200nm.component_names) if msfg_200nm.component_names else 0} 涓?)
        
        return True
        
    except PHMModel.DoesNotExist as e:
        print(f"鉂?鎵句笉鍒癈MG妯″瀷: {e}")
        return False
    except Exception as e:
        print(f"鉂?淇杩囩▼涓嚭閿? {e}")
        return False

def main():
    """涓诲嚱鏁?""
    success = fix_200nm_msfg_nodes()
    
    if success:
        print(f"\n馃帀 淇鎴愬姛锛?)
        print("鐜板湪鍙互灏濊瘯鍦∕SFG閮ㄤ欢瀵瑰簲绠＄悊椤甸潰涓粦瀹氭槧灏勪簡銆?)
        print("寤鸿杩愯浠ヤ笅鍛戒护鏉ラ獙璇佷慨澶嶇粨鏋?")
        print("python scripts/check_msfg_save_logic.py")
    else:
        print(f"\n鉂?淇澶辫触锛?)
        print("璇锋鏌?")
        print("1. 500NM鐨凪SFG閰嶇疆鏄惁姝ｇ‘")
        print("2. 200NM鐨凪SFG閰嶇疆鏄惁瀛樺湪")
        print("3. 鏁版嵁搴撹繛鎺ユ槸鍚︽甯?)

if __name__ == "__main__":
    main()

