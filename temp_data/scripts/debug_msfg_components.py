#!/usr/bin/env python
"""
MSFG閮ㄤ欢鎻愬彇璇婃柇鑴氭湰
鐢ㄤ簬璇婃柇涓嶅悓PHM妯″瀷鐨凪SFG閮ㄤ欢鎻愬彇闂
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
from msfg_analysis.algorithms.msfg.component_integration import extract_components_from_msfg

def diagnose_msfg_components(cmg_model_name):
    """璇婃柇鎸囧畾PHM妯″瀷鐨凪SFG閮ㄤ欢鎻愬彇闂"""
    print(f"\n馃攳 璇婃柇PHM妯″瀷: {cmg_model_name}")
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
            return
        
        print(f"鉁?鎵惧埌娲昏穬MSFG: {active_msfg.name} (ID: {active_msfg.id})")
        print(f"   鍒涘缓鏃堕棿: {active_msfg.created_at}")
        print(f"   鏇存柊鏃堕棿: {active_msfg.updated_at}")
        
        # 3. 妫€鏌SFG鐨刢omponent_names瀛楁
        print(f"\n馃搵 MSFG.component_names瀛楁:")
        if active_msfg.component_names:
            print(f"   鉁?鏈夐儴浠跺垪琛? {active_msfg.component_names}")
        else:
            print("   鉂?component_names瀛楁涓虹┖")
        
        # 4. 妫€鏌SFGNode琛ㄤ腑鐨勭郴缁熻妭鐐?
        print(f"\n馃敡 MSFGNode琛ㄤ腑鐨勭郴缁熻妭鐐?")
        system_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='system'
        ).exclude(name__in=['root', 'system', ''])
        
        if system_nodes.exists():
            print(f"   鉁?鎵惧埌 {system_nodes.count()} 涓郴缁熻妭鐐?")
            for node in system_nodes:
                print(f"      - {node.name} (ID: {node.node_id})")
        else:
            print("   鉂?娌℃湁鎵惧埌绯荤粺鑺傜偣")
        
        # 5. 妫€鏌ユ祴璇曠偣-閮ㄤ欢鏄犲皠
        print(f"\n馃敆 娴嬭瘯鐐?閮ㄤ欢鏄犲皠:")
        mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
        if mappings.exists():
            print(f"   鉁?鎵惧埌 {mappings.count()} 涓槧灏?")
            for mapping in mappings:
                print(f"      - {mapping.test_point_name} 鈫?{mapping.component_name}")
        else:
            print("   鉂?娌℃湁鎵惧埌娴嬭瘯鐐?閮ㄤ欢鏄犲皠")
        
        # 6. 浣跨敤extract_components_from_msfg鍑芥暟鎻愬彇閮ㄤ欢
        print(f"\n馃攳 浣跨敤extract_components_from_msfg鍑芥暟鎻愬彇閮ㄤ欢:")
        try:
            extracted_components = extract_components_from_msfg(active_msfg)
            if extracted_components:
                print(f"   鉁?鎻愬彇鍒?{len(extracted_components)} 涓儴浠?")
                for comp in extracted_components:
                    print(f"      - {comp}")
            else:
                print("   鉂?娌℃湁鎻愬彇鍒颁换浣曢儴浠?)
        except Exception as e:
            print(f"   鉂?鎻愬彇閮ㄤ欢鏃跺嚭閿? {e}")
        
        # 7. 妫€鏌ユ祴璇曠偣鍜屾晠闅滅偣
        print(f"\n馃搳 MSFG涓殑娴嬭瘯鐐瑰拰鏁呴殰鐐?")
        test_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='test'
        )
        fault_nodes = MSFGNode.objects.filter(
            msfg_definition=active_msfg,
            node_type='fault'
        )
        
        print(f"   娴嬭瘯鐐? {test_nodes.count()} 涓?)
        if test_nodes.exists():
            for node in test_nodes[:5]:  # 鍙樉绀哄墠5涓?
                print(f"      - {node.name}")
            if test_nodes.count() > 5:
                print(f"      ... 杩樻湁 {test_nodes.count() - 5} 涓?)
        
        print(f"   鏁呴殰鐐? {fault_nodes.count()} 涓?)
        if fault_nodes.exists():
            for node in fault_nodes[:5]:  # 鍙樉绀哄墠5涓?
                print(f"      - {node.name}")
            if fault_nodes.count() > 5:
                print(f"      ... 杩樻湁 {fault_nodes.count() - 5} 涓?)
        
        # 8. 寤鸿
        print(f"\n馃挕 璇婃柇寤鸿:")
        if not active_msfg.component_names:
            print("   1. MSFG鐨刢omponent_names瀛楁涓虹┖锛屽缓璁噸鏂颁繚瀛楳SFG閰嶇疆")
        if not system_nodes.exists():
            print("   2. 娌℃湁鎵惧埌绯荤粺鑺傜偣锛屾鏌SFG缂栬緫鍣ㄤ腑鐨勭郴缁熻妭鐐硅缃?)
        if not mappings.exists():
            print("   3. 娌℃湁娴嬭瘯鐐?閮ㄤ欢鏄犲皠锛屽缓璁繍琛岃嚜鍔ㄦ槧灏?)
        if not extracted_components:
            print("   4. 鏃犳硶鎻愬彇鍒伴儴浠讹紝鍙兘闇€瑕侀噸鏂伴厤缃甅SFG缁撴瀯")
        
    except PHMModel.DoesNotExist:
        print(f"鉂?鎵句笉鍒癈MG妯″瀷: {cmg_model_name}")
    except Exception as e:
        print(f"鉂?璇婃柇杩囩▼涓嚭閿? {e}")

def main():
    """涓诲嚱鏁?""
    print("馃敡 MSFG閮ㄤ欢鎻愬彇璇婃柇宸ュ叿")
    print("=" * 60)
    
    # 璇婃柇500NM鍜?00NM
    diagnose_msfg_components("500NM")
    diagnose_msfg_components("200NM")
    
    print(f"\n馃幆 璇婃柇瀹屾垚锛?)
    print("濡傛灉200NM鐨勯儴浠舵彁鍙栨湁闂锛岃妫€鏌?")
    print("1. MSFG閰嶇疆鏄惁姝ｇ‘淇濆瓨")
    print("2. 绯荤粺鑺傜偣鏄惁姝ｇ‘璁剧疆")
    print("3. 鏄惁闇€瑕侀噸鏂拌繍琛岃嚜鍔ㄦ槧灏?)

if __name__ == "__main__":
    main()

