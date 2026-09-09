#!/usr/bin/env python
"""
娴嬭瘯CSRF token鏄惁姝ｇ‘浼犻€掑埌妯℃澘
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
from django.test import Client
from django.contrib.auth import get_user_model

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_csrf_token_in_template():
    """娴嬭瘯CSRF token鏄惁姝ｇ‘浼犻€掑埌妯℃澘"""
    logger.info("馃殌 娴嬭瘯CSRF token鏄惁姝ｇ‘浼犻€掑埌妯℃澘...")
    
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
    
    # 鑾峰彇瑙勫垯缂栬緫鍣ㄩ〉闈?
    response = client.get('/api/v1/rules/editor/editor/')
    if response.status_code != 200:
        logger.error(f"鉂?鑾峰彇瑙勫垯缂栬緫鍣ㄩ〉闈㈠け璐? {response.status_code}")
        return False
    
    logger.info("鉁?鑾峰彇瑙勫垯缂栬緫鍣ㄩ〉闈㈡垚鍔?)
    
    # 妫€鏌ュ搷搴斿唴瀹逛腑鏄惁鍖呭惈CSRF token
    content = response.content.decode('utf-8')
    
    # 妫€鏌ユ槸鍚﹀寘鍚獵SRF token鍙橀噺
    if '{{ csrf_token }}' in content:
        logger.warning("鈿狅笍 妯℃澘涓粛鐒跺寘鍚獵SRF token鍙橀噺锛屽彲鑳芥病鏈夋纭覆鏌?)
        return False
    
    # 妫€鏌ユ槸鍚﹀寘鍚疄闄呯殑CSRF token鍊?
    if 'var csrfToken =' in content and 'csrfToken = \'\'' not in content:
        logger.info("鉁?CSRF token宸叉纭紶閫掑埌妯℃澘")
        return True
    else:
        logger.error("鉂?CSRF token鏈纭紶閫掑埌妯℃澘")
        return False

def cleanup_test_data():
    """娓呯悊娴嬭瘯鏁版嵁"""
    logger.info("\n馃Ч 娓呯悊娴嬭瘯鏁版嵁...")
    
    try:
        # 鍒犻櫎娴嬭瘯鐢ㄦ埛
        User = get_user_model()
        deleted_users = User.objects.filter(username='testuser').delete()[0]
        logger.info(f"鉁?鍒犻櫎浜?{deleted_users} 涓祴璇曠敤鎴?)
        
    except Exception as e:
        logger.warning(f"鈿狅笍 娓呯悊娴嬭瘯鏁版嵁鏃跺嚭閿? {e}")

def main():
    """涓诲嚱鏁?""
    logger.info("馃殌 寮€濮婥SRF token浼犻€掓祴璇?..")
    
    try:
        # 娴嬭瘯CSRF token浼犻€?
        success = test_csrf_token_in_template()
        
        if success:
            logger.info("\n馃搳 娴嬭瘯缁撴灉: CSRF token浼犻€掓甯?")
            logger.info("馃帀 瑙勫垯缂栬緫鍣–SRF淇鎴愬姛!")
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

