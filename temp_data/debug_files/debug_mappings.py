#!/usr/bin/env python
"""
璋冭瘯MSFG鏄犲皠闂鐨勮剼鏈?
"""
import os
import sys

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')

import django
django.setup()

from msfg_analysis.models import MSFGDefinition, TestPointComponentMapping, MSFGNode

def debug_msfg_mappings():
    print("=== MSFG鏄犲皠璋冭瘯淇℃伅 ===\n")
    
    try:
        # 1. 妫€鏌SFG瀹氫箟
        msfgs = MSFGDefinition.objects.all()
        print(f"鎬籑SFG瀹氫箟鏁伴噺: {msfgs.count()}")
        
        for msfg in msfgs[:3]:  # 鍙鏌ュ墠3涓?
            print(f"\n--- MSFG: {msfg.name} (ID: {msfg.id}) ---")
            print(f"鍒涘缓鏃堕棿: {msfg.created_at}")
            print(f"Test names: {msfg.test_names}")
            print(f"Component names: {msfg.component_names}")
            print(f"Fault names: {msfg.fault_names}")
            
            # 妫€鏌ヨ妭鐐规暟鎹?
            nodes = MSFGNode.objects.filter(msfg_definition=msfg)
            test_nodes = nodes.filter(node_type__icontains='test')
            system_nodes = nodes.filter(node_type='system')
            fault_nodes = nodes.filter(node_type='fault')
            
            print(f"鏁版嵁搴撲腑鑺傜偣鎬绘暟: {nodes.count()}")
            print(f"娴嬭瘯鑺傜偣鏁? {test_nodes.count()}")
            print(f"绯荤粺鑺傜偣鏁? {system_nodes.count()}")
            print(f"鏁呴殰鑺傜偣鏁? {fault_nodes.count()}")
            
            if test_nodes.exists():
                print("娴嬭瘯鑺傜偣鍚嶇О:", [node.name for node in test_nodes[:5]])
            if system_nodes.exists():
                print("绯荤粺鑺傜偣鍚嶇О:", [node.name for node in system_nodes[:5]])
            if fault_nodes.exists():
                print("鏁呴殰鑺傜偣鍚嶇О:", [node.name for node in fault_nodes[:5]])
            
            # 妫€鏌ョ幇鏈夋槧灏?
            mappings = TestPointComponentMapping.objects.filter(msfg_definition=msfg)
            print(f"鐜版湁鏄犲皠鏁伴噺: {mappings.count()}")
            
            if mappings.exists():
                for mapping in mappings[:5]:
                    print(f"  鏄犲皠: {mapping.test_point_name} 鈫?{mapping.component_name}")
    
        # 2. 妫€鏌ユ€绘槧灏勬暟閲?
        total_mappings = TestPointComponentMapping.objects.count()
        print(f"\n鎬绘槧灏勬暟閲? {total_mappings}")
        
    except Exception as e:
        print(f"閿欒: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_msfg_mappings()

