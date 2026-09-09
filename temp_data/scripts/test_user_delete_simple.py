#!/usr/bin/env python
"""
绠€鍗曠殑鐢ㄦ埛鍒犻櫎娴嬭瘯
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
import json

User = get_user_model()

def test_user_delete():
    """娴嬭瘯鐢ㄦ埛鍒犻櫎鍔熻兘"""
    print("=" * 60)
    print("娴嬭瘯鐢ㄦ埛鍒犻櫎鍔熻兘")
    print("=" * 60)
    
    # 鍒涘缓娴嬭瘯瀹㈡埛绔?
    client = Client()
    
    # 鑾峰彇绠＄悊鍛樼敤鎴?
    admin_user = User.objects.get(username='admin')
    print(f"绠＄悊鍛樼敤鎴? {admin_user.username} (ID: {admin_user.id})")
    
    # 鑾峰彇瑕佸垹闄ょ殑娴嬭瘯鐢ㄦ埛
    test_user = User.objects.filter(role='user', username__in=['doctor1', 'user1']).first()
    if not test_user:
        print("鉂?娌℃湁鎵惧埌鍙互鍒犻櫎鐨勬祴璇曠敤鎴?)
        return
    
    print(f"娴嬭瘯鍒犻櫎鐢ㄦ埛: {test_user.username} (ID: {test_user.id})")
    
    # 鍏堢櫥褰曠鐞嗗憳
    print("\n1. 绠＄悊鍛樼櫥褰?..")
    login_response = client.post('/api/v1/users/login/', {
        'username': 'admin',
        'password': 'admin123456'
    })
    
    if login_response.status_code != 200:
        print(f"鉂?绠＄悊鍛樼櫥褰曞け璐? {login_response.status_code}")
        print(f"鍝嶅簲鍐呭: {login_response.content}")
        return
    
    print("鉁?绠＄悊鍛樼櫥褰曟垚鍔?)
    
    # 灏濊瘯鍒犻櫎鐢ㄦ埛
    print(f"\n2. 灏濊瘯鍒犻櫎鐢ㄦ埛: {test_user.username}")
    delete_url = f'/api/v1/users/users/{test_user.id}/'
    delete_response = client.delete(delete_url)
    
    print(f"鍒犻櫎璇锋眰URL: {delete_url}")
    print(f"鍒犻櫎鐘舵€佺爜: {delete_response.status_code}")
    
    if delete_response.status_code == 204:
        print("鉁?鐢ㄦ埛鍒犻櫎鎴愬姛")
        
        # 楠岃瘉鐢ㄦ埛鏄惁鐪熺殑琚垹闄や簡
        try:
            User.objects.get(pk=test_user.id)
            print("鉂?鐢ㄦ埛浠嶇劧瀛樺湪浜庢暟鎹簱涓?)
        except User.DoesNotExist:
            print("鉁?鐢ㄦ埛宸蹭粠鏁版嵁搴撲腑鍒犻櫎")
            
    elif delete_response.status_code == 403:
        print("鉂?鏉冮檺琚嫆缁?(403)")
        print(f"鍝嶅簲鍐呭: {delete_response.content}")
        
    else:
        print(f"鉂?鍒犻櫎澶辫触锛岀姸鎬佺爜: {delete_response.status_code}")
        print(f"鍝嶅簲鍐呭: {delete_response.content}")

if __name__ == '__main__':
    test_user_delete()

