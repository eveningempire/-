#!/usr/bin/env python
"""
鏇存柊MSFG瀹氫箟鐨刢omponent_names瀛楁
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel
from msfg_analysis.algorithms.msfg.component_integration import extract_components_from_msfg

def update_component_names():
    print("馃敡 鏇存柊MSFG瀹氫箟鐨刢omponent_names瀛楁")
    print("=" * 60)
    
    try:
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
        
        # 鎻愬彇閮ㄤ欢鍒楄〃
        print(f"\n馃攳 鎻愬彇閮ㄤ欢鍒楄〃...")
        components = extract_components_from_msfg(msfg_definition)
        print(f"馃敡 鎻愬彇鐨勯儴浠? {len(components)} 涓?)
        for comp in components:
            print(f"  - {comp}")
        
        # 鏇存柊MSFG瀹氫箟鐨刢omponent_names瀛楁
        print(f"\n馃敡 鏇存柊MSFG瀹氫箟鐨刢omponent_names瀛楁...")
        old_components = msfg_definition.component_names or []
        print(f"  鏃ч儴浠跺垪琛? {old_components}")
        print(f"  鏂伴儴浠跺垪琛? {components}")
        
        if old_components != components:
            msfg_definition.component_names = components
            msfg_definition.save()
            print(f"鉁?鎴愬姛鏇存柊component_names瀛楁")
        else:
            print(f"鈩癸笍 component_names瀛楁宸茬粡鏄渶鏂扮殑")
        
        # 楠岃瘉鏇存柊缁撴灉
        msfg_definition.refresh_from_db()
        print(f"\n馃攳 楠岃瘉鏇存柊缁撴灉...")
        print(f"  component_names: {msfg_definition.component_names}")
        
        print("\n" + "=" * 60)
        print("鉁?鏇存柊瀹屾垚")
        
    except Exception as e:
        print(f"鉂?鏇存柊杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫洿鏂癱omponent_names瀛楁...")
    update_component_names()

