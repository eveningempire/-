#!/usr/bin/env python
"""
娣卞叆鍒嗘瀽MSFG璁＄畻閫昏緫涓殑鍏抽敭闂
"""

import os
import sys
import django

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import MSFGDefinition, MSFGNode, MSFGEdge, TestPointComponentMapping
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion
import numpy as np

def analyze_msfg_calculation_issue():
    """鍒嗘瀽MSFG璁＄畻閫昏緫涓殑鍏抽敭闂"""
    print("=== MSFG璁＄畻閫昏緫鍏抽敭闂鍒嗘瀽 ===")
    
    # 1. 鑾峰彇娲昏穬鐨凪SFG瀹氫箟
    active_msfg = MSFGDefinition.objects.filter(is_active=True).first()
    if not active_msfg:
        print("鉂?娌℃湁鎵惧埌娲昏穬鐨凪SFG瀹氫箟")
        return False
    
    print(f"鉁?娲昏穬MSFG: {active_msfg.name}")
    
    # 2. 鍒嗘瀽MSFG缁撴瀯
    test_nodes = list(MSFGNode.objects.filter(
        msfg_definition=active_msfg,
        node_type='test'
    ).order_by('name'))
    
    fault_nodes = list(MSFGNode.objects.filter(
        msfg_definition=active_msfg,
        node_type='fault'
    ).order_by('name'))
    
    edges = list(MSFGEdge.objects.filter(msfg_definition=active_msfg))
    
    # 3. 鍒嗘瀽鍏抽敭闂锛氱己灏戞晠闅滅偣鍒伴儴浠剁殑鏄犲皠
    print(f"\n馃毃 鍏抽敭闂1: 缂哄皯鏁呴殰鐐瑰埌閮ㄤ欢鐨勬槧灏?)
    print(f"   褰撳墠MSFG缁撴瀯: 娴嬭瘯鐐?-> 鏁呴殰鐐?)
    print(f"   闇€瑕佺殑缁撴瀯: 娴嬭瘯鐐?-> 鏁呴殰鐐?-> 閮ㄤ欢")
    print(f"   闂: 娌℃湁寤虹珛鏁呴殰鐐瑰埌閮ㄤ欢鐨勬槧灏勫叧绯?)
    
    # 4. 鍒嗘瀽褰撳墠鐨勮绠楅€昏緫缂洪櫡
    print(f"\n馃攳 褰撳墠璁＄畻閫昏緫鍒嗘瀽:")
    
    # 鑾峰彇娴嬭瘯鐐?閮ㄤ欢鏄犲皠
    mappings = TestPointComponentMapping.objects.filter(msfg_definition=active_msfg)
    
    print(f"   娴嬭瘯鐐?閮ㄤ欢鏄犲皠鏁伴噺: {mappings.count()}")
    for mapping in mappings:
        print(f"     {mapping.test_point_name} -> {mapping.component_name}")
    
    # 5. 鍒嗘瀽璁＄畻閫昏緫涓殑闂
    print(f"\n鉂?璁＄畻閫昏緫闂:")
    
    # 闂1: 娴嬭瘯鐐圭洿鎺ユ槧灏勫埌閮ㄤ欢锛岃烦杩囦簡鏁呴殰鐐?
    print(f"   闂1: 娴嬭瘯鐐圭洿鎺ユ槧灏勫埌閮ㄤ欢锛岃烦杩囦簡鏁呴殰鐐圭殑鎺ㄧ悊杩囩▼")
    print(f"   杩欒繚鍙嶄簡MSFG鐨勫熀鏈師鐞嗭細娴嬭瘯鐐?-> 鏁呴殰鐐?-> 閮ㄤ欢")
    
    # 闂2: 缂哄皯鏁呴殰姒傜巼鍒伴儴浠跺仴搴峰害鐨勮浆鎹?
    print(f"   闂2: 缂哄皯鏁呴殰姒傜巼鍒伴儴浠跺仴搴峰害鐨勭瀛﹁浆鎹?)
    print(f"   搴旇: 鏁呴殰姒傜巼 -> 閮ㄤ欢鏁呴殰姒傜巼 -> 閮ㄤ欢鍋ュ悍搴?)
    
    # 闂3: 閮ㄤ欢鏉ユ簮涓嶄竴鑷?
    print(f"   闂3: 閮ㄤ欢鏉ユ簮涓嶄竴鑷村鑷磋绠楅敊璇?)
    
    # 6. 鍒嗘瀽姝ｇ‘鐨凪SFG璁＄畻娴佺▼
    print(f"\n鉁?姝ｇ‘鐨凪SFG璁＄畻娴佺▼搴旇鏄?")
    print(f"   姝ラ1: 娴嬭瘯鐐瑰垎鏁?-> 鏁呴殰姒傜巼 (閫氳繃D鐭╅樀)")
    print(f"   姝ラ2: 鏁呴殰姒傜巼 -> 閮ㄤ欢鏁呴殰姒傜巼 (閫氳繃鏁呴殰-閮ㄤ欢鏄犲皠)")
    print(f"   姝ラ3: 閮ㄤ欢鏁呴殰姒傜巼 -> 閮ㄤ欢鍋ュ悍搴?(鍋ュ悍搴?= 1 - 鏁呴殰姒傜巼)")
    print(f"   姝ラ4: 閮ㄤ欢鍋ュ悍搴?-> 绯荤粺鍋ュ悍搴?(鍔犳潈骞冲潎)")
    
    # 7. 鍒嗘瀽褰撳墠瀹炵幇鐨勯棶棰?
    print(f"\n馃敡 褰撳墠瀹炵幇鐨勯棶棰?")
    
    # 妫€鏌dvanced_fusion.py涓殑閫昏緫
    print(f"   1. AdvancedMSFGFusion.calculate_component_health() 鏂规硶:")
    print(f"      - 杈撳叆: fault_prob, fuzzy_prob, fault_nodes, component_mappings")
    print(f"      - 闂: component_mappings 搴旇鏄?鏁呴殰鍚?>閮ㄤ欢鍚?鐨勬槧灏?)
    print(f"      - 褰撳墠: 瀹為檯鏄?娴嬭瘯鐐瑰悕->閮ㄤ欢鍚?鐨勬槧灏?)
    
    # 8. 鍒嗘瀽MSFG璁捐闂
    print(f"\n馃彈锔?MSFG璁捐闂:")
    
    # 妫€鏌ユ槸鍚︽湁鏁呴殰鐐瑰埌閮ㄤ欢鐨勬槧灏?
    print(f"   1. 缂哄皯鏁呴殰鐐瑰埌閮ㄤ欢鐨勬槧灏勮〃")
    print(f"   2. 绯荤粺鑺傜偣锛堥儴浠讹級鏁伴噺涓?锛岃鏄嶮SFG缂栬緫鍣ㄦ病鏈夋纭繚瀛橀儴浠朵俊鎭?)
    print(f"   3. component_names瀛楁涓庡疄闄呯殑MSFG缁撴瀯涓嶄竴鑷?)
    
    # 9. 寤鸿鐨勪慨澶嶆柟妗?
    print(f"\n馃挕 淇鏂规:")
    print(f"   鏂规1: 淇敼MSFG缂栬緫鍣紝娣诲姞鏁呴殰鐐瑰埌閮ㄤ欢鐨勬槧灏?)
    print(f"   鏂规2: 淇敼璁＄畻閫昏緫锛屽缓绔嬫祴璇曠偣->鏁呴殰鐐?>閮ㄤ欢鐨勫畬鏁存槧灏勯摼")
    print(f"   鏂规3: 缁熶竴閮ㄤ欢鏉ユ簮锛岀‘淇滿SFG缁撴瀯涓庢槧灏勮〃涓€鑷?)
    
    # 10. 鍏蜂綋鐨勪慨澶嶆楠?
    print(f"\n馃敡 鍏蜂綋淇姝ラ:")
    print(f"   姝ラ1: 鍦∕SFG缂栬緫鍣ㄤ腑娣诲姞鏁呴殰鐐瑰埌閮ㄤ欢鐨勮繛鎺?)
    print(f"   姝ラ2: 鍒涘缓FaultComponentMapping妯″瀷")
    print(f"   姝ラ3: 淇敼AdvancedMSFGFusion.calculate_component_health()鏂规硶")
    print(f"   姝ラ4: 鏇存柊閮ㄤ欢鎻愬彇閫昏緫")
    
    # 11. 楠岃瘉褰撳墠璁＄畻鏄惁鏈夋晥
    print(f"\n馃М 楠岃瘉褰撳墠璁＄畻鏈夋晥鎬?")
    
    if test_nodes and fault_nodes and mappings.exists():
        # 鍒涘缓妯℃嫙鏁版嵁
        test_scores = {node.name: [0.5] for node in test_nodes}
        
        # 鏋勫缓D鐭╅樀
        fusion = AdvancedMSFGFusion()
        D_matrix, test_name_to_idx, fault_name_to_idx = fusion.build_d_matrix(
            test_nodes, fault_nodes, edges
        )
        
        print(f"   D鐭╅樀褰㈢姸: {D_matrix.shape}")
        print(f"   娴嬭瘯鐐规暟閲? {len(test_nodes)}")
        print(f"   鏁呴殰鐐规暟閲? {len(fault_nodes)}")
        
        # 妫€鏌鐭╅樀鏄惁鏈夋晥
        if D_matrix.nnz > 0:
            print(f"   鉁?D鐭╅樀鏈夋晥锛屽寘鍚?{D_matrix.nnz} 涓潪闆跺厓绱?)
        else:
            print(f"   鉂?D鐭╅樀涓虹┖锛屾病鏈夋祴璇曠偣鍒版晠闅滅偣鐨勮繛鎺?)
        
        # 妫€鏌ラ儴浠舵槧灏勬槸鍚︽湁鏁?
        component_mappings = {}
        for mapping in mappings:
            component_name = mapping.component_name
            if component_name not in component_mappings:
                component_mappings[component_name] = []
            # 杩欓噷鏈夐棶棰橈細搴旇鏄犲皠鏁呴殰鐐癸紝鑰屼笉鏄祴璇曠偣
            component_mappings[component_name].append(mapping.test_point_name)
        
        print(f"   閮ㄤ欢鏄犲皠: {component_mappings}")
        
        if component_mappings:
            print(f"   鈿狅笍 褰撳墠鏄犲皠閫昏緫鏈夎锛氭祴璇曠偣鐩存帴鏄犲皠鍒伴儴浠?)
        else:
            print(f"   鉂?娌℃湁鏈夋晥鐨勯儴浠舵槧灏?)
    else:
        print(f"   鉂?MSFG缁撴瀯涓嶅畬鏁达紝鏃犳硶楠岃瘉璁＄畻")
    
    return True

if __name__ == "__main__":
    analyze_msfg_calculation_issue()

