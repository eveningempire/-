#!/usr/bin/env python
"""
娴嬭瘯璁块棶璁板綍鍔熻兘
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

User = get_user_model()

def test_access_records():
    """娴嬭瘯璁块棶璁板綍鍔熻兘"""
    print("=== 娴嬭瘯璁块棶璁板綍鍔熻兘 ===")
    
    # 鍒涘缓娴嬭瘯鐢ㄦ埛
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'role': User.Role.USER
        }
    )
    
    if created:
        print(f"鍒涘缓娴嬭瘯鐢ㄦ埛: {user.username}")
    else:
        print(f"浣跨敤鐜版湁鐢ㄦ埛: {user.username}")
    
    # 鍒涘缓瀹㈡埛绔?
    client = Client(HTTP_HOST='localhost:8000')
    
    # 妯℃嫙璁块棶涓嶅悓椤甸潰
    pages = [
        '/',
        '/data-import',
        '/data-records',
        '/cmg-detail',
        '/user-management'
    ]
    
    print("\n妯℃嫙璁块棶椤甸潰...")
    for page in pages:
        try:
            response = client.get(page)
            print(f"璁块棶 {page}: {response.status_code}")
        except Exception as e:
            print(f"璁块棶 {page}: 閿欒 - {e}")
    
    # 妫€鏌ヨ闂褰?
    from users.models import UserAccessRecord
    
    print(f"\n璁块棶璁板綍鎬绘暟: {UserAccessRecord.objects.count()}")
    
    # 鏄剧ず鏈€杩戠殑璁块棶璁板綍
    recent_records = UserAccessRecord.objects.all()[:5]
    print("\n鏈€杩戠殑璁块棶璁板綍:")
    for record in recent_records:
        print(f"  - {record.user.username} 璁块棶浜?{record.page_visited} 鍦?{record.access_time}")
    
    # 娴嬭瘯API绔偣
    print("\n娴嬭瘯API绔偣...")
    
    # 鑾峰彇璁块棶璁板綍鍒楄〃
    try:
        response = client.get('/api/v1/users/access-records/')
        print(f"璁块棶璁板綍API: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"API杩斿洖璁板綍鏁? {len(data.get('results', []))}")
    except Exception as e:
        print(f"API娴嬭瘯閿欒: {e}")
    
    print("\n=== 娴嬭瘯瀹屾垚 ===")

if __name__ == '__main__':
    test_access_records()

