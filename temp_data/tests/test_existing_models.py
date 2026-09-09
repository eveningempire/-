#!/usr/bin/env python
"""
娴嬭瘯鐜版湁妯″瀷閰嶇疆锛屾鏌ユ槸鍚︽湁鍙敤鐨勬娴嬫ā鍨?
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from data_management.models import PHM, PHMModel
from health_management.models import IMSModel
from rule_detection.models import RuleDefinition
from msfg_analysis.models import MSFGDefinition


def check_existing_setup():
    """妫€鏌ョ幇鏈夌殑妯″瀷閰嶇疆"""
    print("=== 妫€鏌ョ幇鏈夋ā鍨嬮厤缃?===")
    
    # 妫€鏌MG妯″瀷
    cmg_models = PHMModel.objects.filter(is_active=True)
    print(f"\n娲昏穬鐨凜MG妯″瀷: {cmg_models.count()} 涓?)
    for model in cmg_models:
        print(f"  - {model.model_name}: {model.description}")
    
    # 妫€鏌MG瀹炰緥
    cmgs = PHM.objects.filter(enabled=True)
    print(f"\n鍚敤鐨凜MG瀹炰緥: {cmgs.count()} 涓?)
    for cmg in cmgs:
        print(f"  - {cmg.cmg_id} ({cmg.name}): 鍨嬪彿 {cmg.cmg_model.model_name}")
    
    # 妫€鏌ユ瘡涓狢MG妯″瀷鐨勬娴嬮厤缃?
    print(f"\n=== 妫€娴嬫ā鍨嬮厤缃?===")
    for cmg_model in cmg_models:
        print(f"\nPHM妯″瀷: {cmg_model.model_name}")
        
        # IMS妯″瀷
        ims_models = IMSModel.objects.filter(cmg_model=cmg_model)
        active_ims = ims_models.filter(is_active=True)
        print(f"  IMS妯″瀷: 鎬绘暟 {ims_models.count()}, 婵€娲?{active_ims.count()}")
        for ims in active_ims:
            print(f"    鉁?{ims.name} (闃堝€? {ims.threshold})")
        
        # 瑙勫垯
        rules = RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True)
        print(f"  瑙勫垯: {rules.count()} 涓湪绾胯鍒?)
        for rule in rules[:3]:  # 鍙樉绀哄墠3涓?
            print(f"    鉁?{rule.rule_id}: {rule.rule_expression}")
        if rules.count() > 3:
            print(f"    ... 杩樻湁 {rules.count() - 3} 涓鍒?)
        
        # MSFG
        msfgs = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True)
        print(f"  MSFG: {msfgs.count()} 涓縺娲诲浘")
        for msfg in msfgs:
            print(f"    鉁?{msfg.name}")
    
    return cmg_models.count() > 0, cmgs.count() > 0


def recommend_test_cmg():
    """鎺ㄨ崘鐢ㄤ簬娴嬭瘯鐨凜MG"""
    print(f"\n=== 娴嬭瘯寤鸿 ===")
    
    # 鎵惧埌鏈夊畬鏁存娴嬮厤缃殑PHM
    suitable_cmgs = []
    
    for cmg in PHM.objects.filter(enabled=True):
        cmg_model = cmg.cmg_model
        
        # 妫€鏌ユ槸鍚︽湁婵€娲荤殑IMS妯″瀷
        has_ims = IMSModel.objects.filter(cmg_model=cmg_model, is_active=True).exists()
        
        # 妫€鏌ユ槸鍚︽湁鍦ㄧ嚎瑙勫垯
        has_rules = RuleDefinition.objects.filter(cmg_model=cmg_model, is_online=True).exists()
        
        # 妫€鏌ユ槸鍚︽湁婵€娲荤殑MSFG
        has_msfg = MSFGDefinition.objects.filter(cmg_model=cmg_model, is_active=True).exists()
        
        suitable_cmgs.append({
            'cmg': cmg,
            'has_ims': has_ims,
            'has_rules': has_rules,
            'has_msfg': has_msfg,
            'score': sum([has_ims, has_rules, has_msfg])
        })
    
    # 鎸夐厤缃畬鏁村害鎺掑簭
    suitable_cmgs.sort(key=lambda x: x['score'], reverse=True)
    
    if suitable_cmgs:
        print("鎺ㄨ崘鐢ㄤ簬娴嬭瘯鐨凜MG锛堟寜妫€娴嬮厤缃畬鏁村害鎺掑簭锛夛細")
        for item in suitable_cmgs[:3]:  # 鏄剧ず鍓?涓?
            cmg = item['cmg']
            print(f"  {cmg.cmg_id} ({cmg.name}):")
            print(f"    IMS: {'鉁? if item['has_ims'] else '鉁?}")
            print(f"    瑙勫垯: {'鉁? if item['has_rules'] else '鉁?}")
            print(f"    MSFG: {'鉁? if item['has_msfg'] else '鉁?}")
            print(f"    閰嶇疆瀹屾暣搴? {item['score']}/3")
        
        best_cmg = suitable_cmgs[0]['cmg']
        print(f"\n鏈€浣虫祴璇旵MG: {best_cmg.cmg_id}")
        return best_cmg
    else:
        print("娌℃湁鎵惧埌鍚堥€傜殑娴嬭瘯PHM")
        return None


def main():
    """涓诲嚱鏁?""
    try:
        has_models, has_cmgs = check_existing_setup()
        
        if not has_models:
            print("\n鈿狅笍 娌℃湁鎵惧埌娲昏穬鐨凜MG妯″瀷")
            return False
        
        if not has_cmgs:
            print("\n鈿狅笍 娌℃湁鎵惧埌鍚敤鐨凜MG瀹炰緥")
            return False
        
        recommended_cmg = recommend_test_cmg()
        
        if recommended_cmg:
            print(f"\n鉁?绯荤粺妫€鏌ュ畬鎴愶紝鍙互浣跨敤PHM '{recommended_cmg.cmg_id}' 杩涜鏂囦欢涓婁紶娴嬭瘯")
            print(f"   鍦ㄥ墠绔€夋嫨璇MG杩涜鏂囦欢涓婁紶锛岀郴缁熷皢鑷姩浣跨敤瀵瑰簲鐨勬娴嬫ā鍨?)
        else:
            print(f"\n鉂?娌℃湁鎵惧埌鍏锋湁瀹屾暣妫€娴嬮厤缃殑PHM")
        
        return True
        
    except Exception as e:
        print(f"妫€鏌ヨ繃绋嬩腑鍑洪敊: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

