#!/usr/bin/env python
"""
娴嬭瘯MSFG娴嬬偣鈫掗儴浠垛啋鏁呴殰鐨勫畬鏁存槧灏勬彁鍙栧姛鑳?
"""
import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, PHMModel
from msfg_analysis.algorithms.msfg.auto_mapping import extract_test_component_fault_mappings, get_mapping_summary

def test_mapping_extraction():
    print("馃攳 娴嬭瘯MSFG娴嬬偣鈫掗儴浠垛啋鏁呴殰鐨勫畬鏁存槧灏勬彁鍙栧姛鑳?)
    print("=" * 80)
    
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
            
        print(f"馃搵 妫€鏌SFG: {msfg_definition}")
        print(f"  馃搳 MSFG ID: {msfg_definition.id}")
        print(f"  馃搮 鍒涘缓鏃堕棿: {msfg_definition.created_at}")
        
        # 鑾峰彇鏄犲皠鎽樿
        print(f"\n馃搳 鑾峰彇鏄犲皠鎽樿...")
        summary = get_mapping_summary(msfg_definition)
        
        if not summary:
            print("鉂?鏃犳硶鑾峰彇鏄犲皠鎽樿")
            return
        
        print(f"馃搱 鏄犲皠鍏崇郴缁熻:")
        print(f"  馃幆 娴嬭瘯鐐规暟閲? {summary['mapping_stats']['total_test_points']}")
        print(f"  馃敡 閮ㄤ欢鏄犲皠鎬绘暟: {summary['mapping_stats']['total_component_mappings']}")
        print(f"  鈿狅笍 鏁呴殰鏄犲皠鎬绘暟: {summary['mapping_stats']['total_fault_mappings']}")
        print(f"  馃搳 骞冲潎閮ㄤ欢鏄犲皠/娴嬭瘯鐐? {summary['mapping_stats']['avg_components_per_test']}")
        print(f"  馃搳 骞冲潎鏁呴殰鏄犲皠/娴嬭瘯鐐? {summary['mapping_stats']['avg_faults_per_test']}")
        
        if summary['mapping_stats']['test_with_most_components']:
            most_comp = summary['mapping_stats']['test_with_most_components']
            print(f"  馃弳 閮ㄤ欢鏄犲皠鏈€澶氱殑娴嬭瘯鐐? {most_comp['name']} ({most_comp['count']} 涓?")
        
        if summary['mapping_stats']['test_with_most_faults']:
            most_fault = summary['mapping_stats']['test_with_most_faults']
            print(f"  馃弳 鏁呴殰鏄犲皠鏈€澶氱殑娴嬭瘯鐐? {most_fault['name']} ({most_fault['count']} 涓?")
        
        # 鏄剧ず绀轰緥鏄犲皠
        print(f"\n馃搵 绀轰緥鏄犲皠鍏崇郴:")
        for test_name, mapping in summary['sample_mappings'].items():
            print(f"\n  馃幆 娴嬭瘯鐐? {test_name}")
            
            if mapping['components']:
                print(f"    馃敡 閮ㄤ欢鏄犲皠:")
                for comp_name, strength in mapping['components']:
                    print(f"      - {comp_name} (寮哄害: {strength:.4f})")
            else:
                print(f"    鈿狅笍 鏃犻儴浠舵槧灏?)
            
            if mapping['faults']:
                print(f"    鈿狅笍 鏁呴殰鏄犲皠:")
                for fault_name, strength in mapping['faults']:
                    print(f"      - {fault_name} (寮哄害: {strength:.4f})")
            else:
                print(f"    鈿狅笍 鏃犳晠闅滄槧灏?)
        
        # 鑾峰彇瀹屾暣鏄犲皠鍏崇郴
        print(f"\n馃攳 鑾峰彇瀹屾暣鏄犲皠鍏崇郴...")
        complete_mappings = extract_test_component_fault_mappings(msfg_definition)
        
        if not complete_mappings:
            print("鉂?鏃犳硶鑾峰彇瀹屾暣鏄犲皠鍏崇郴")
            return
        
        print(f"鉁?鎴愬姛鎻愬彇 {len(complete_mappings)} 涓祴璇曠偣鐨勫畬鏁存槧灏勫叧绯?)
        
        # 鏄剧ず鍓嶅嚑涓祴璇曠偣鐨勮缁嗘槧灏?
        print(f"\n馃搵 璇︾粏鏄犲皠鍏崇郴 (鍓?涓祴璇曠偣):")
        for i, (test_name, mapping) in enumerate(complete_mappings.items()):
            if i >= 5:
                break
                
            print(f"\n  馃幆 娴嬭瘯鐐?{i+1}: {test_name}")
            print(f"    馃搳 閮ㄤ欢鏄犲皠: {len(mapping['components'])} 涓?)
            print(f"    馃搳 鏁呴殰鏄犲皠: {len(mapping['faults'])} 涓?)
            
            if mapping['components']:
                print(f"    馃敡 閮ㄤ欢鍒楄〃:")
                for comp_name, strength in mapping['components'][:5]:  # 鍙樉绀哄墠5涓?
                    print(f"      - {comp_name} (寮哄害: {strength:.4f})")
                if len(mapping['components']) > 5:
                    print(f"      ... 杩樻湁 {len(mapping['components']) - 5} 涓?)
            
            if mapping['faults']:
                print(f"    鈿狅笍 鏁呴殰鍒楄〃:")
                for fault_name, strength in mapping['faults'][:5]:  # 鍙樉绀哄墠5涓?
                    print(f"      - {fault_name} (寮哄害: {strength:.4f})")
                if len(mapping['faults']) > 5:
                    print(f"      ... 杩樻湁 {len(mapping['faults']) - 5} 涓?)
        
        print("\n" + "=" * 80)
        print("鉁?鏄犲皠鎻愬彇娴嬭瘯瀹屾垚")
        
    except Exception as e:
        print(f"鉂?娴嬭瘯杩囩▼涓嚭閿? {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("馃殌 寮€濮嬫祴璇曟槧灏勬彁鍙栧姛鑳?..")
    test_mapping_extraction()



