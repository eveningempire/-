#!/usr/bin/env python
"""
鏈€缁堟祴璇曡鍒欑紪杈戝櫒鐨凜SRF淇
"""

import os
import sys
import django
from pathlib import Path

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

import logging
import json
from django.test import Client
from django.contrib.auth import get_user_model
from data_management.models import PHMModel

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rule_editor_apis():
    """娴嬭瘯瑙勫垯缂栬緫鍣ㄧ殑鎵€鏈堿PI绔偣"""
    logger.info("馃殌 娴嬭瘯瑙勫垯缂栬緫鍣ˋPI绔偣...")
    
    # 鍒涘缓娴嬭瘯瀹㈡埛绔?
    client = Client()
    
    # 鍒涘缓娴嬭瘯鐢ㄦ埛
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        logger.info("鉁?鍒涘缓娴嬭瘯鐢ㄦ埛")
    
    # 鐧诲綍鐢ㄦ埛
    login_success = client.login(username='testuser', password='testpass123')
    if not login_success:
        logger.error("鉂?鐢ㄦ埛鐧诲綍澶辫触")
        return False
    
    logger.info("鉁?鐢ㄦ埛鐧诲綍鎴愬姛")
    
    # 鑾峰彇鎴栧垱寤篊MG妯″瀷
    cmg_model, created = PHMModel.objects.get_or_create(
        model_name='娴嬭瘯妯″瀷',
        defaults={'description': '鐢ㄤ簬娴嬭瘯鐨凜MG妯″瀷'}
    )
    if created:
        logger.info("鉁?鍒涘缓娴嬭瘯PHM妯″瀷")
    
    # 鑾峰彇CSRF token
    response = client.get('/api/v1/rules/editor/editor/')
    if response.status_code != 200:
        logger.error(f"鉂?鑾峰彇瑙勫垯缂栬緫鍣ㄩ〉闈㈠け璐? {response.status_code}")
        return False
    
    # 浠庡搷搴斾腑鎻愬彇CSRF token
    content = response.content.decode('utf-8')
    if 'var csrfToken =' not in content:
        logger.error("鉂?椤甸潰涓湭鎵惧埌CSRF token")
        return False
    
    # 鎻愬彇CSRF token鍊?
    import re
    csrf_match = re.search(r"var csrfToken = '([^']+)'", content)
    if not csrf_match:
        logger.error("鉂?鏃犳硶鎻愬彇CSRF token鍊?)
        return False
    
    csrf_token = csrf_match.group(1)
    logger.info(f"鉁?鑾峰彇鍒癈SRF token: {csrf_token[:10]}...")
    
    # 娴嬭瘯1: get-config API
    logger.info("馃攧 娴嬭瘯get-config API...")
    response = client.post('/api/v1/rules/editor/get-config/', 
                          data=json.dumps({'cmg_model_id': cmg_model.id}),
                          content_type='application/json',
                          HTTP_X_CSRFTOKEN=csrf_token,
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    if response.status_code == 200:
        logger.info("鉁?get-config API娴嬭瘯閫氳繃")
    else:
        logger.error(f"鉂?get-config API娴嬭瘯澶辫触: {response.status_code}")
        logger.error(f"鍝嶅簲鍐呭: {response.content.decode()}")
        return False
    
    # 娴嬭瘯2: init-all-rule API
    logger.info("馃攧 娴嬭瘯init-all-rule API...")
    response = client.post('/api/v1/rules/editor/init-all-rule/', 
                          data=json.dumps({'cmg_model_id': cmg_model.id}),
                          content_type='application/json',
                          HTTP_X_CSRFTOKEN=csrf_token,
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    if response.status_code == 200:
        logger.info("鉁?init-all-rule API娴嬭瘯閫氳繃")
    else:
        logger.error(f"鉂?init-all-rule API娴嬭瘯澶辫触: {response.status_code}")
        logger.error(f"鍝嶅簲鍐呭: {response.content.decode()}")
        return False
    
    # 娴嬭瘯3: config-rule API
    logger.info("馃攧 娴嬭瘯config-rule API...")
    test_rules = [
        {
            'showId': 'TEST_RULE_001',
            'ruleExpress': 'temperature > 50',
            'faultName': '娓╁害杩囬珮',
            'faultLevel': 2,
            'component': '鍐峰嵈绯荤粺',
            'source': 'expert',
            'planDescript': '妫€鏌ュ喎鍗寸郴缁?,
            'ruleOnline': True,
            'isNew': True,
            'editable': True
        }
    ]
    
    response = client.post('/api/v1/rules/editor/config-rule/', 
                          data=json.dumps({
                              'cmg_model_id': cmg_model.id,
                              'tableData': json.dumps(test_rules)
                          }),
                          content_type='application/json',
                          HTTP_X_CSRFTOKEN=csrf_token,
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    
    if response.status_code == 200:
        logger.info("鉁?config-rule API娴嬭瘯閫氳繃")
    else:
        logger.error(f"鉂?config-rule API娴嬭瘯澶辫触: {response.status_code}")
        logger.error(f"鍝嶅簲鍐呭: {response.content.decode()}")
        return False
    
    return True

def cleanup_test_data():
    """娓呯悊娴嬭瘯鏁版嵁"""
    logger.info("\n馃Ч 娓呯悊娴嬭瘯鏁版嵁...")
    
    try:
        # 鍒犻櫎娴嬭瘯鐢ㄦ埛
        User = get_user_model()
        deleted_users = User.objects.filter(username='testuser').delete()[0]
        logger.info(f"鉁?鍒犻櫎浜?{deleted_users} 涓祴璇曠敤鎴?)
        
        # 鍒犻櫎娴嬭瘯PHM妯″瀷
        deleted_models = PHMModel.objects.filter(model_name='娴嬭瘯妯″瀷').delete()[0]
        logger.info(f"鉁?鍒犻櫎浜?{deleted_models} 涓祴璇旵MG妯″瀷")
        
    except Exception as e:
        logger.warning(f"鈿狅笍 娓呯悊娴嬭瘯鏁版嵁鏃跺嚭閿? {e}")

def main():
    """涓诲嚱鏁?""
    logger.info("馃殌 寮€濮嬭鍒欑紪杈戝櫒鏈€缁堟祴璇?..")
    
    try:
        # 娴嬭瘯瑙勫垯缂栬緫鍣ˋPI
        success = test_rule_editor_apis()
        
        if success:
            logger.info("\n馃搳 娴嬭瘯缁撴灉: 鎵€鏈堿PI娴嬭瘯閫氳繃!")
            logger.info("馃帀 瑙勫垯缂栬緫鍣–SRF淇瀹屽叏鎴愬姛!")
        else:
            logger.error("\n鉂?娴嬭瘯澶辫触!")
            return False
        
    except Exception as e:
        logger.error(f"鉂?娴嬭瘯澶辫触: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 娓呯悊娴嬭瘯鏁版嵁
        cleanup_test_data()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

