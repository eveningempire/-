#!/usr/bin/env python
"""
MSFG閮ㄤ欢淇鑴氭湰
鐢ㄤ簬閲嶆柊鎻愬彇鍜屽悓姝SFG閮ㄤ欢锛岃В鍐抽儴浠舵彁鍙栭棶棰?
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
from msfg_analysis.algorithms.msfg.component_integration import (
    extract_components_from_msfg, 
    ensure_msfg_component_mappings,
    sync_msfg_component_definitions
)

def fix_msfg_components(cmg_model_name, force_rebuild=False):
    """淇鎸囧畾PHM妯″瀷鐨凪SFG閮ㄤ欢鎻愬彇闂"""
    print(f"\n馃敡 淇PHM妯″瀷: {cmg_model_name}")
    print("=" * 60)
    
    try:
        # 1. 鏌ユ壘PHM妯″瀷
        cmg_model = PHMModel.objects.get(model_name=cmg_model_name)
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
        
        # 3. 閲嶆柊鎻愬彇閮ㄤ欢鍚嶇О
        print(f"\n馃攧 閲嶆柊鎻愬彇閮ㄤ欢鍚嶇О...")
        
        # 浠嶮SFGNode琛ㄤ腑鎻愬彇绯荤粺鑺傜偣鍚嶇О
        system_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='system'
        ).exclude(name__in=['root', 'system', ''])
        
        component_names = []
        for node in system_nodes:
            if node.name and node.name.strip():
                component_names.append(node.name.strip())
        
        # 鍘婚噸骞舵帓搴?
        component_names = sorted(list(set(component_names)))
        
        print(f"   浠庣郴缁熻妭鐐规彁鍙栧埌 {len(component_names)} 涓儴浠?")
        for comp in component_names:
            print(f"      - {comp}")
        
        # 4. 鏇存柊MSFG鐨刢omponent_names瀛楁
        if component_names:
            active_msfg.component_names = component_names
            active_msfg.save(update_fields=['component_names', 'updated_at'])
            print(f"鉁?宸叉洿鏂癕SFG鐨刢omponent_names瀛楁")
        else:
            print("鈿狅笍 娌℃湁鎻愬彇鍒伴儴浠跺悕绉帮紝璺宠繃鏇存柊")
        
        # 5. 閲嶆柊杩愯閮ㄤ欢鏄犲皠
        print(f"\n馃攧 閲嶆柊杩愯閮ㄤ欢鏄犲皠...")
        try:
            ensure_msfg_component_mappings(active_msfg)
            print(f"鉁?閮ㄤ欢鏄犲皠鏇存柊瀹屾垚")
        except Exception as e:
            print(f"鉂?閮ㄤ欢鏄犲皠鏇存柊澶辫触: {e}")
            return False
        
        # 6. 鍚屾閮ㄤ欢瀹氫箟鍒拌鍒欐娴嬫ā鍧?
        print(f"\n馃攧 鍚屾閮ㄤ欢瀹氫箟...")
        try:
            sync_result = sync_msfg_component_definitions(cmg_model)
            print(f"鉁?閮ㄤ欢瀹氫箟鍚屾瀹屾垚: {sync_result}")
        except Exception as e:
            print(f"鉂?閮ㄤ欢瀹氫箟鍚屾澶辫触: {e}")
        
        # 7. 楠岃瘉淇缁撴灉
        print(f"\n馃攳 楠岃瘉淇缁撴灉...")
        try:
            extracted_components = extract_components_from_msfg(active_msfg)
            if extracted_components:
                print(f"鉁?淇鎴愬姛锛佺幇鍦ㄥ彲浠ユ彁鍙栧埌 {len(extracted_components)} 涓儴浠?")
                for comp in extracted_components:
                    print(f"      - {comp}")
                return True
            else:
                print("鉂?淇鍚庝粛鏃犳硶鎻愬彇鍒伴儴浠?)
                return False
        except Exception as e:
            print(f"鉂?楠岃瘉澶辫触: {e}")
            return False
        
    except PHMModel.DoesNotExist:
        print(f"鉂?鎵句笉鍒癈MG妯″瀷: {cmg_model_name}")
        return False
    except Exception as e:
        print(f"鉂?淇杩囩▼涓嚭閿? {e}")
        return False

def main():
    """涓诲嚱鏁?""
    print("馃敡 MSFG閮ㄤ欢淇宸ュ叿")
    print("=" * 60)
    
    # 淇200NM
    success = fix_msfg_components("Test")
    
    if success:
        print(f"\n馃帀 淇瀹屾垚锛?)
        print("鐜板湪鍙互灏濊瘯鍦∕SFG閮ㄤ欢瀵瑰簲绠＄悊椤甸潰涓粦瀹氭槧灏勪簡銆?)
    else:
        print(f"\n鉂?淇澶辫触锛?)
        print("璇锋鏌?")
        print("1. MSFG閰嶇疆鏄惁姝ｇ‘")
        print("2. 绯荤粺鑺傜偣鏄惁姝ｇ‘璁剧疆")
        print("3. 鏄惁闇€瑕侀噸鏂颁繚瀛楳SFG閰嶇疆")

if __name__ == "__main__":
    main()

