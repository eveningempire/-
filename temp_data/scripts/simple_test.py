#!/usr/bin/env python
"""
绠€鍗曟祴璇曡剼鏈?
"""

import os
import sys
import django

# 娣诲姞椤圭洰鏍圭洰褰曞埌Python璺緞
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 璁剧疆Django鐜
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.test import Client

User = get_user_model()

def main():
    print("=== 绠€鍗曟祴璇?===")
    
    # 妫€鏌ョ敤鎴?
    users = User.objects.all()
    print(f"鐢ㄦ埛鏁伴噺: {users.count()}")
    
    for user in users:
        print(f"鐢ㄦ埛: {user.username}, 瑙掕壊: {user.role}, 婵€娲? {user.is_active}")
    
    # 娴嬭瘯璁よ瘉
    user = authenticate(username='admin', password='admin123456')
    if user:
        print(f"鉁?璁よ瘉鎴愬姛: {user.username}")
    else:
        print("鉂?璁よ瘉澶辫触")
    
    # 娴嬭瘯瀹㈡埛绔?
    client = Client()
    response = client.post('/api/v1/users/login/', {
        'username': 'admin',
        'password': 'admin123456'
    })
    
    print(f"鍝嶅簲鐘舵€? {response.status_code}")
    print(f"鍝嶅簲鍐呭: {response.content.decode()}")

if __name__ == "__main__":
    main()

