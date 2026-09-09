#!/usr/bin/env python
"""
娴嬭瘯MSFG瀵煎叆鏃惰嚜鍔ㄦ洿鏂癱omponent_names鍔熻兘
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel

def test_auto_update():
    print("馃攳 娴嬭瘯MSFG瀵煎叆鏃惰嚜鍔ㄦ洿鏂癱omponent_names鍔熻兘")
    print("=" * 60)
    
    try:
        # 鑾峰彇鏈€鏂扮殑MSFG瀹氫箟
        cmg_model = PHMModel.objects.filter(is_active=True).first()
        if not cmg_model:
            print("鉂?娌℃湁鎵惧埌婵€娲荤殑PHM妯″瀷")
            return
            
        msfg_definition = MSFGDefinition.objects.filter(cmg_model=cmg_model).order_by('-created_at').first()
        if not msfg_definition:
            print("鉂?娌℃湁鎵惧埌MSFG瀹氫箟")
            return
            
        print(f"馃搵 妫€鏌MG妯″瀷: {cmg_model}")
        print(f"  鉁?MSFG: {msfg_definition}")
        print(f"  馃搳 MSFG ID: {msfg_definition.id}")
        print(f"  馃搮 鍒涘缓鏃堕棿: {msfg_definition.created_at}")
        
        # 妫€鏌SFG瀹氫箟鐨勫瓧娈?
        print(f"\n馃攳 妫€鏌SFG瀹氫箟瀛楁")
        print("=" * 40)
        
        print(f"馃搳 test_names: {len(msfg_definition.test_names or [])} 涓?)
        if msfg_definition.test_names:
            for test in msfg_definition.test_names[:5]:
                print(f"  - {test}")
        
        print(f"馃搳 component_names: {len(msfg_definition.component_names or [])} 涓?)
        if msfg_definition.component_names:
            for comp in msfg_definition.component_names:
                print(f"  - {comp}")
        else:
            print("  鈿狅笍 component_names涓虹┖锛?)
        
        print(f"馃搳 fault_names: {len(msfg_definition.fault_names or [])} 涓?)
        if msfg_definition.fault_names:
            for fault in msfg_definition.fault_names[:5]:
                print(f"  - {fault}")
        
        # 妫€鏌ヨ妭鐐规暟鎹?
        print(f"\n馃攳 妫€鏌ヨ妭鐐规暟鎹?)
        print("=" * 40)
        
        from msfg_analysis.models import MSFGNode
        nodes = MSFGNode.objects.filter(msfg_definition=msfg_definition)
        
        node_types = {}
        for node in nodes:
            node_type = node.node_type
            if node_type not in node_types:
                node_types[node_type] = []
            node_types[node_type].append(node)
        
        for node_type, node_list in node_types.items():
            print(f"  {node_type}: {len(node_list)} 涓?)
            for node in node_list[:3]:
                print(f"    - {node.name} (ID: {node.node_id})")
            if len(node_list) > 3:
                print(f"    ... 杩樻湁 {len(node_list) - 3} 涓?)
        
        # 妫€鏌ユ槸鍚︽湁component鑺傜偣
        component_nodes = node_types.get('component', [])
        if component_nodes:
            print(f"\n馃敡 鎵惧埌 {len(component_nodes)} 涓猚omponent鑺傜偣:")
            for node in component_nodes:
                print(f"  - {node.name} (ID: {node.node_id})")
        else:
            print(f"\n鈿狅笍 娌℃湁鎵惧埌component绫诲瀷鐨勮妭鐐?)
        
        print("\n" + "=" * 60)
        print("鉁?妫€鏌ュ畬鎴?)
        
        # 缁欏嚭寤鸿
        if not msfg_definition.component_names:
            print(f"\n馃挕 寤鸿:")
            print(f"  1. 閲嶆柊瀵煎叆MSFG鏁版嵁")
            print(f"  2. 鎴栬€呮墜鍔ㄨ繍琛屾洿鏂拌剼鏈? python update_component_names.py")
        
    except Exception as e:
        print(f"鉂?妫€鏌ヨ繃绋嬩腑鍑洪敊: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫祴璇曡嚜鍔ㄦ洿鏂板姛鑳?..")
    test_auto_update()

