#!/usr/bin/env python
"""
妫€鏌SFG鏁版嵁
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel

def check_msfg_data():
    print("馃攳 妫€鏌SFG鏁版嵁")
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
        
        print(f"馃搳 fault_names: {len(msfg_definition.fault_names or [])} 涓?)
        if msfg_definition.fault_names:
            for fault in msfg_definition.fault_names[:5]:
                print(f"  - {fault}")
        
        print("\n" + "=" * 60)
        print("鉁?妫€鏌ュ畬鎴?)
        
    except Exception as e:
        print(f"鉂?妫€鏌ヨ繃绋嬩腑鍑洪敊: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫鏌SFG鏁版嵁...")
    check_msfg_data()

