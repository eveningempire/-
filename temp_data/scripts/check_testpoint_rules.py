#!/usr/bin/env python
"""
妫€鏌ユ祴鐐硅鍒欏瓨鍌ㄦ儏鍐电殑鑴氭湰
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from msfg_analysis.models import TestPointRule, MSFGDefinition
from data_management.models import PHMModel, PHMData

def main():
    print("=" * 60)
    print("娴嬬偣瑙勫垯瀛樺偍鎯呭喌妫€鏌?)
    print("=" * 60)
    
    # 1. 妫€鏌MG妯″瀷
    print("\n1. PHM妯″瀷:")
    cmg_models = PHMModel.objects.all()
    print(f"   鎬绘暟: {cmg_models.count()}")
    for model in cmg_models:
        print(f"   - {model.model_name} (ID: {model.id})")
    
    # 2. 妫€鏌SFG瀹氫箟
    print("\n2. MSFG瀹氫箟:")
    msfg_defs = MSFGDefinition.objects.all()
    print(f"   鎬绘暟: {msfg_defs.count()}")
    for msfg in msfg_defs:
        print(f"   - {msfg.name} (ID: {msfg.id}, 婵€娲? {msfg.is_active}, PHM: {msfg.cmg_model.model_name})")
    
    # 3. 妫€鏌ユ祴鐐硅鍒?
    print("\n3. 娴嬬偣瑙勫垯:")
    rules = TestPointRule.objects.all()
    print(f"   鎬绘暟: {rules.count()}")
    
    if rules.count() > 0:
        print("\n   璇︾粏淇℃伅:")
        for i, rule in enumerate(rules[:5], 1):  # 鍙樉绀哄墠5鏉?
            print(f"\n   瑙勫垯 {i}:")
            print(f"     娴嬬偣鍚? {rule.test_name}")
            print(f"     瑙勫垯ID: {rule.rule_id}")
            print(f"     琛ㄨ揪寮? {repr(rule.rule_expression)}")
            print(f"     琛ㄨ揪寮忛暱搴? {len(rule.rule_expression)}")
            print(f"     MSFG: {rule.msfg_definition}")
            print(f"     PHM妯″瀷: {rule.cmg_model}")
            print(f"     鏉冮噸: {rule.weight}")
            print(f"     婵€娲? {rule.is_online}")
            
            # 妫€鏌ヨ〃杈惧紡涓殑鐗规畩瀛楃
            if '\\' in rule.rule_expression:
                print(f"     鈿狅笍  琛ㄨ揪寮忓寘鍚弽鏂滄潬")
            if '"' in rule.rule_expression:
                print(f"     鉁?琛ㄨ揪寮忓寘鍚弻寮曞彿")
    else:
        print("   娌℃湁鎵惧埌娴嬬偣瑙勫垯")
    
    # 4. 妫€鏌ユ縺娲荤殑MSFG瀵瑰簲鐨勮鍒?
    print("\n4. 婵€娲籑SFG鐨勬祴鐐硅鍒?")
    active_msfgs = MSFGDefinition.objects.filter(is_active=True)
    for msfg in active_msfgs:
        print(f"\n   MSFG: {msfg.name} (ID: {msfg.id})")
        msfg_rules = TestPointRule.objects.filter(msfg_definition=msfg, is_online=True)
        print(f"   婵€娲昏鍒欐暟: {msfg_rules.count()}")
        
        for rule in msfg_rules[:3]:  # 鏄剧ず鍓?鏉¤鍒?
            print(f"     - {rule.test_name}: {rule.rule_expression[:50]}...")
    
    # 5. 妫€鏌MGData鏍锋湰
    print("\n5. PHMData鏍锋湰:")
    sample_data = PHMData.objects.first()
    if sample_data:
        print(f"   鎵惧埌鏁版嵁鐐?ID: {sample_data.id}")
        print(f"   PHM: {sample_data.cmg}")
        print(f"   鏃堕棿鎴? {sample_data.timestamp}")
        if hasattr(sample_data, 'raw_parameters') and sample_data.raw_parameters:
            params = sample_data.raw_parameters
            print(f"   鍙傛暟鏁伴噺: {len(params) if isinstance(params, dict) else 'N/A'}")
            if isinstance(params, dict):
                # 鏄剧ず鍓嶅嚑涓弬鏁板悕
                param_names = list(params.keys())[:5]
                print(f"   鍙傛暟绀轰緥: {param_names}")
                
                # 妫€鏌ユ槸鍚︽湁涓枃鍙傛暟鍚?
                chinese_params = [name for name in params.keys() if any('\u4e00' <= char <= '\u9fff' for char in name)]
                if chinese_params:
                    print(f"   涓枃鍙傛暟绀轰緥: {chinese_params[:3]}")
    else:
        print("   娌℃湁鎵惧埌PHMData鏁版嵁")
    
    print("\n" + "=" * 60)
    print("妫€鏌ュ畬鎴?)
    print("=" * 60)

if __name__ == "__main__":
    main()

