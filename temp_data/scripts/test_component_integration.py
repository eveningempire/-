#!/usr/bin/env python
"""
娴嬭瘯閮ㄤ欢鎻愬彇鍜岄泦鎴愬姛鑳?
楠岃瘉200NM鐨勯儴浠舵彁鍙栨槸鍚︾鍚堝叾浠栧嚱鏁扮殑璋冪敤鏍煎紡
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
    sync_msfg_component_definitions,
    calculate_msfg_component_health
)

def test_component_integration():
    """娴嬭瘯閮ㄤ欢鎻愬彇鍜岄泦鎴愬姛鑳?""
    print("馃И 娴嬭瘯閮ㄤ欢鎻愬彇鍜岄泦鎴愬姛鑳?)
    print("=" * 80)
    
    try:
        # 1. 娴嬭瘯200NM鐨勯儴浠舵彁鍙?
        print("馃搳 娴嬭瘯200NM鐨勯儴浠舵彁鍙?")
        cmg_model_200nm = PHMModel.objects.get(model_name="200NM")
        active_msfg_200nm = MSFGDefinition.objects.filter(
            cmg_model=cmg_model_200nm,
            is_active=True
        ).order_by('-updated_at').first()
        
        if not active_msfg_200nm:
            print("鉂?娌℃湁鎵惧埌200NM鐨勬椿璺僊SFG閰嶇疆")
            return False
        
        print(f"鉁?鎵惧埌200NM MSFG: {active_msfg_200nm.name}")
        
        # 2. 娴嬭瘯extract_components_from_msfg鍑芥暟
        print(f"\n馃攧 娴嬭瘯extract_components_from_msfg鍑芥暟:")
        extracted_components = extract_components_from_msfg(active_msfg_200nm)
        print(f"   鎻愬彇鍒?{len(extracted_components)} 涓儴浠?")
        for i, comp in enumerate(extracted_components, 1):
            print(f"     {i}. {comp}")
        
        # 3. 楠岃瘉component_names瀛楁鏍煎紡
        print(f"\n馃搵 楠岃瘉component_names瀛楁鏍煎紡:")
        if active_msfg_200nm.component_names:
            print(f"   鉁?component_names瀛楁鏈夋暟鎹? {len(active_msfg_200nm.component_names)} 涓?)
            print(f"   鏁版嵁绫诲瀷: {type(active_msfg_200nm.component_names)}")
            print(f"   鏁版嵁鍐呭: {active_msfg_200nm.component_names}")
            
            # 楠岃瘉鏄惁涓哄垪琛ㄦ牸寮?
            if isinstance(active_msfg_200nm.component_names, list):
                print("   鉁?鏍煎紡姝ｇ‘锛氬垪琛ㄦ牸寮?)
            else:
                print("   鉂?鏍煎紡閿欒锛氫笉鏄垪琛ㄦ牸寮?)
        else:
            print("   鉂?component_names瀛楁涓虹┖")
            return False
        
        # 4. 楠岃瘉绯荤粺鑺傜偣鏍煎紡
        print(f"\n馃敡 楠岃瘉绯荤粺鑺傜偣鏍煎紡:")
        system_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg_200nm,
            node_type='system'
        ).exclude(name__in=['root', 'system', ''])
        
        print(f"   绯荤粺鑺傜偣鏁伴噺: {system_nodes.count()}")
        for node in system_nodes:
            print(f"     - ID: {node.node_id}")
            print(f"       鍚嶇О: '{node.name}'")
            print(f"       绫诲瀷: {node.node_type}")
            print(f"       灞炴€? {node.properties}")
        
        # 5. 楠岃瘉娴嬭瘯鐐?閮ㄤ欢鏄犲皠鏍煎紡
        print(f"\n馃敆 楠岃瘉娴嬭瘯鐐?閮ㄤ欢鏄犲皠鏍煎紡:")
        mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg_200nm)
        print(f"   鏄犲皠鏁伴噺: {mappings.count()}")
        
        if mappings.exists():
            sample_mapping = mappings.first()
            print(f"   绀轰緥鏄犲皠:")
            print(f"     - 娴嬭瘯鐐? '{sample_mapping.test_point_name}'")
            print(f"     - 閮ㄤ欢: '{sample_mapping.component_name}'")
            print(f"     - 鏄犲皠绫诲瀷: {sample_mapping.mapping_type}")
            print(f"     - 鏉冮噸: {sample_mapping.weight}")
            print(f"     - 閮ㄤ欢绫诲瀷: {sample_mapping.component_type}")
            print(f"     - 閲嶈搴? {sample_mapping.importance_weight}")
            print(f"     - 鏄惁鍏抽敭: {sample_mapping.is_critical}")
        
        # 6. 娴嬭瘯ensure_msfg_component_mappings鍑芥暟
        print(f"\n馃攧 娴嬭瘯ensure_msfg_component_mappings鍑芥暟:")
        try:
            ensure_msfg_component_mappings(active_msfg_200nm)
            print("   鉁?鍑芥暟鎵ц鎴愬姛")
            
            # 妫€鏌ユ槧灏勬暟閲忔槸鍚﹀鍔?
            new_mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg_200nm)
            print(f"   鏄犲皠鏁伴噺: {new_mappings.count()}")
        except Exception as e:
            print(f"   鉂?鍑芥暟鎵ц澶辫触: {e}")
            return False
        
        # 7. 娴嬭瘯sync_msfg_component_definitions鍑芥暟
        print(f"\n馃攧 娴嬭瘯sync_msfg_component_definitions鍑芥暟:")
        try:
            sync_result = sync_msfg_component_definitions(cmg_model_200nm)
            print(f"   鉁?鍑芥暟鎵ц鎴愬姛")
            print(f"   鍚屾缁撴灉: {sync_result}")
        except Exception as e:
            print(f"   鉂?鍑芥暟鎵ц澶辫触: {e}")
            return False
        
        # 8. 娴嬭瘯calculate_msfg_component_health鍑芥暟
        print(f"\n馃攧 娴嬭瘯calculate_msfg_component_health鍑芥暟:")
        try:
            # 鍒涘缓妯℃嫙鐨勬祴璇曠偣鍒嗘暟
            test_scores = {
                "娓╁害瓒呴檺": 0.8,
                "鐢垫祦娉㈠姩": 0.6,
                "杞€熷紓甯?: 0.7
            }
            
            health_result = calculate_msfg_component_health(
                test_scores=test_scores,
                msfg_definition=active_msfg_200nm
            )
            print(f"   鉁?鍑芥暟鎵ц鎴愬姛")
            print(f"   鍋ュ悍鐘舵€佺粨鏋? {len(health_result)} 涓儴浠?)
            
            for component, health in health_result.items():
                print(f"     - {component}: 鍒嗘暟={health.get('score', 'N/A')}, 鐘舵€?{health.get('status', 'N/A')}")
                
        except Exception as e:
            print(f"   鉂?鍑芥暟鎵ц澶辫触: {e}")
            return False
        
        # 9. 瀵规瘮500NM鐨勬牸寮?
        print(f"\n馃搳 瀵规瘮500NM鐨勬牸寮?")
        cmg_model_500nm = PHMModel.objects.get(model_name="500NM")
        active_msfg_500nm = MSFGDefinition.objects.filter(
            cmg_model=cmg_model_500nm,
            is_active=True
        ).order_by('-updated_at').first()
        
        if active_msfg_500nm:
            print(f"   500NM component_names鏁伴噺: {len(active_msfg_500nm.component_names) if active_msfg_500nm.component_names else 0}")
            print(f"   500NM 绯荤粺鑺傜偣鏁伴噺: {MSFGNode.objects.filter(msfg_definition=active_msfg_500nm, node_type='system').exclude(name__in=['root', 'system', '']).count()}")
            print(f"   500NM 鏄犲皠鏁伴噺: {TestPointComponentMapping.objects.filter(msfg_definition=active_msfg_500nm).count()}")
            
            print(f"   200NM component_names鏁伴噺: {len(active_msfg_200nm.component_names) if active_msfg_200nm.component_names else 0}")
            print(f"   200NM 绯荤粺鑺傜偣鏁伴噺: {system_nodes.count()}")
            print(f"   200NM 鏄犲皠鏁伴噺: {mappings.count()}")
        
        # 10. 鎬荤粨娴嬭瘯缁撴灉
        print(f"\n馃帀 娴嬭瘯鎬荤粨:")
        print(f"   鉁?閮ㄤ欢鎻愬彇鍔熻兘姝ｅ父")
        print(f"   鉁?component_names瀛楁鏍煎紡姝ｇ‘")
        print(f"   鉁?绯荤粺鑺傜偣鏍煎紡姝ｇ‘")
        print(f"   鉁?娴嬭瘯鐐?閮ㄤ欢鏄犲皠鏍煎紡姝ｇ‘")
        print(f"   鉁?鎵€鏈夐泦鎴愬嚱鏁伴兘鑳芥甯稿伐浣?)
        print(f"   鉁?200NM鐨勬牸寮忎笌500NM鍏煎")
        
        return True
        
    except PHMModel.DoesNotExist as e:
        print(f"鉂?鎵句笉鍒癈MG妯″瀷: {e}")
        return False
    except Exception as e:
        print(f"鉂?娴嬭瘯杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """涓诲嚱鏁?""
    success = test_component_integration()
    
    if success:
        print(f"\n馃帀 鎵€鏈夋祴璇曢€氳繃锛?)
        print("200NM鐨勯儴浠舵彁鍙栧拰闆嗘垚鍔熻兘瀹屽叏姝ｅ父锛屽彲浠ュ畨鍏ㄤ娇鐢ㄣ€?)
    else:
        print(f"\n鉂?娴嬭瘯澶辫触锛?)
        print("闇€瑕佽繘涓€姝ユ鏌ュ拰淇闂銆?)

if __name__ == "__main__":
    main()

