#!/usr/bin/env python
"""
鍚屾MSFG閮ㄤ欢瀹氫箟锛岃В鍐崇晫闈㈡樉绀轰笉涓€鑷寸殑闂
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.db import transaction
from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.component_integration import extract_components_from_msfg

def sync_msfg_components():
    """鍚屾MSFG閮ㄤ欢瀹氫箟"""
    print("=== 鍚屾MSFG閮ㄤ欢瀹氫箟 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    print(f"   PHM妯″瀷: {active_msfg.cmg_model.model_name}")
    
    # 2. 鑾峰彇褰撳墠鐘舵€?
    print(f"\n馃搳 褰撳墠鐘舵€?")
    
    # 浠嶮SFG缁撴瀯涓彁鍙栫殑閮ㄤ欢锛堟渶鏉冨▉鐨勬潵婧愶級
    extracted_components = extract_components_from_msfg(active_msfg)
    print(f"   浠嶮SFG缁撴瀯鎻愬彇鐨勯儴浠? {extracted_components}")
    
    # 褰撳墠component_names涓殑閮ㄤ欢
    current_component_names = active_msfg.component_names or []
    print(f"   褰撳墠component_names涓殑閮ㄤ欢: {current_component_names}")
    
    # 褰撳墠鏄犲皠涓殑閮ㄤ欢
    current_mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    mapped_components = set()
    for mapping in current_mappings:
        mapped_components.add(mapping.component_name)
    print(f"   褰撳墠鏄犲皠涓殑閮ㄤ欢: {list(mapped_components)}")
    
    # 3. 鍚屾绛栫暐
    print(f"\n馃攧 鍚屾绛栫暐:")
    print(f"   1. 浣跨敤 extract_components_from_msfg 鍑芥暟鐨勭粨鏋滀綔涓烘潈濞佹潵婧?)
    print(f"   2. 鏇存柊 MSFG.component_names 瀛楁")
    print(f"   3. 娓呯悊涓嶅湪鏉冨▉鍒楄〃涓殑鏄犲皠")
    print(f"   4. 涓烘湭鏄犲皠鐨勬祴璇曠偣鍒涘缓榛樿鏄犲皠")
    
    # 4. 鎵ц鍚屾
    try:
        with transaction.atomic():
            # 鏇存柊component_names
            active_msfg.component_names = extracted_components
            active_msfg.save()
            print(f"   鉁?宸叉洿鏂?component_names: {extracted_components}")
            
            # 娓呯悊涓嶅湪鏉冨▉鍒楄〃涓殑鏄犲皠
            invalid_mappings = current_mappings.exclude(component_name__in=extracted_components)
            deleted_count = invalid_mappings.count()
            invalid_mappings.delete()
            if deleted_count > 0:
                print(f"   鉁?宸插垹闄?{deleted_count} 涓棤鏁堟槧灏?)
            
            # 涓烘湭鏄犲皠鐨勬祴璇曠偣鍒涘缓榛樿鏄犲皠
            test_names = active_msfg.test_names or []
            existing_mapped_tests = set(
                current_mappings.values_list('test_point_name', flat=True)
            )
            
            unmapped_tests = [test for test in test_names if test not in existing_mapped_tests]
            
            if unmapped_tests and extracted_components:
                # 涓烘湭鏄犲皠鐨勬祴璇曠偣鍒涘缓榛樿鏄犲皠
                default_component = extracted_components[0]  # 浣跨敤绗竴涓儴浠朵綔涓洪粯璁?
                
                for test_name in unmapped_tests:
                    TestPointComponentMapping.objects.create(
                        msfg_definition=active_msfg,
                        test_point_name=test_name,
                        component_name=default_component,
                        mapping_type='one_to_one',
                        weight=1.0,
                        component_type='other',
                        importance_weight=1.0,
                        is_critical=False,
                        description=f'鑷姩鍒涘缓鐨勯粯璁ゆ槧灏?
                    )
                
                print(f"   鉁?宸蹭负 {len(unmapped_tests)} 涓祴璇曠偣鍒涘缓榛樿鏄犲皠鍒?{default_component}")
        
        print(f"\n鉁?鍚屾瀹屾垚!")
        
        # 5. 楠岃瘉缁撴灉
        print(f"\n馃搵 鍚屾鍚庣殑鐘舵€?")
        active_msfg.refresh_from_db()
        print(f"   component_names: {active_msfg.component_names}")
        
        final_mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
        print(f"   鏄犲皠鏁伴噺: {final_mappings.count()}")
        for mapping in final_mappings:
            print(f"     {mapping.test_point_name} -> {mapping.component_name}")
        
        return True
        
    except Exception as e:
        print(f"鉂?鍚屾澶辫触: {e}")
        return False

if __name__ == "__main__":
    sync_msfg_components()

