#!/usr/bin/env python
"""
娴嬭瘯鐢ㄦ埛鍒犻櫎鏉冮檺闂
"""

import os
import sys
import django

# 璁剧疆Django鐜
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.views import CustomIsAuthenticated, UserViewSet
from rest_framework.test import APIRequestFactory
from rest_framework.permissions import BasePermission
import logging

# 璁剧疆鏃ュ織
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

User = get_user_model()

def test_user_permissions():
    """娴嬭瘯鐢ㄦ埛鏉冮檺"""
    print("=" * 60)
    print("娴嬭瘯鐢ㄦ埛鍒犻櫎鏉冮檺闂")
    print("=" * 60)
    
    # 鍒涘缓娴嬭瘯鐢ㄦ埛
    try:
        # 鑾峰彇鎴栧垱寤虹鐞嗗憳鐢ㄦ埛
        admin_user, created = User.objects.get_or_create(
            username='admin_test',
            defaults={
                'email': 'admin@test.com',
                'role': User.Role.ADMIN,
                'is_active': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            print(f"鍒涘缓绠＄悊鍛樼敤鎴? {admin_user.username}")
        else:
            print(f"浣跨敤鐜版湁绠＄悊鍛樼敤鎴? {admin_user.username}")
        
        # 鑾峰彇鎴栧垱寤烘櫘閫氱敤鎴?
        normal_user, created = User.objects.get_or_create(
            username='user_test',
            defaults={
                'email': 'user@test.com',
                'role': User.Role.USER,
                'is_active': True
            }
        )
        if created:
            normal_user.set_password('user123')
            normal_user.save()
            print(f"鍒涘缓鏅€氱敤鎴? {normal_user.username}")
        else:
            print(f"浣跨敤鐜版湁鏅€氱敤鎴? {normal_user.username}")
        
        # 鑾峰彇鎴栧垱寤鸿鍒犻櫎鐨勭敤鎴?
        target_user, created = User.objects.get_or_create(
            username='delete_test',
            defaults={
                'email': 'delete@test.com',
                'role': User.Role.USER,
                'is_active': True
            }
        )
        if created:
            target_user.set_password('delete123')
            target_user.save()
            print(f"鍒涘缓鐩爣鐢ㄦ埛: {target_user.username}")
        else:
            print(f"浣跨敤鐜版湁鐩爣鐢ㄦ埛: {target_user.username}")
        
    except Exception as e:
        print(f"鍒涘缓娴嬭瘯鐢ㄦ埛澶辫触: {e}")
        return
    
    # 鍒涘缓API璇锋眰宸ュ巶
    factory = APIRequestFactory()
    
    # 娴嬭瘯鏉冮檺绫?
    permission_class = CustomIsAuthenticated()
    
    print("\n" + "=" * 40)
    print("娴嬭瘯鏉冮檺妫€鏌?)
    print("=" * 40)
    
    # 娴嬭瘯绠＄悊鍛樻潈闄?
    print(f"\n1. 娴嬭瘯绠＄悊鍛樻潈闄?(鐢ㄦ埛: {admin_user.username}, 瑙掕壊: {admin_user.role})")
    
    # 鍒涘缓妯℃嫙璇锋眰
    request = factory.delete(f'/api/v1/users/users/{target_user.id}/')
    request.user = admin_user
    
    # 娴嬭瘯has_permission
    has_perm = permission_class.has_permission(request, None)
    print(f"   has_permission: {has_perm}")
    
    # 娴嬭瘯has_object_permission
    has_obj_perm = permission_class.has_object_permission(request, None, target_user)
    print(f"   has_object_permission: {has_obj_perm}")
    
    # 娴嬭瘯鏅€氱敤鎴锋潈闄?
    print(f"\n2. 娴嬭瘯鏅€氱敤鎴锋潈闄?(鐢ㄦ埛: {normal_user.username}, 瑙掕壊: {normal_user.role})")
    
    request = factory.delete(f'/api/v1/users/users/{target_user.id}/')
    request.user = normal_user
    
    # 娴嬭瘯has_permission
    has_perm = permission_class.has_permission(request, None)
    print(f"   has_permission: {has_perm}")
    
    # 娴嬭瘯has_object_permission
    has_obj_perm = permission_class.has_object_permission(request, None, target_user)
    print(f"   has_object_permission: {has_obj_perm}")
    
    # 娴嬭瘯瑙嗗浘闆嗘潈闄?
    print("\n" + "=" * 40)
    print("娴嬭瘯瑙嗗浘闆嗘潈闄?)
    print("=" * 40)
    
    viewset = UserViewSet()
    viewset.action = 'destroy'
    
    # 娴嬭瘯绠＄悊鍛樺垹闄ょ敤鎴?
    print(f"\n3. 娴嬭瘯绠＄悊鍛樺垹闄ょ敤鎴?)
    try:
        request = factory.delete(f'/api/v1/users/users/{target_user.id}/')
        request.user = admin_user
        viewset.request = request
        
        # 娴嬭瘯get_object
        obj = viewset.get_object()
        print(f"   get_object鎴愬姛: {obj.username}")
        
        # 娴嬭瘯perform_destroy
        viewset.perform_destroy(target_user)
        print("   perform_destroy鎴愬姛")
        
        # 閲嶆柊鍒涘缓鐩爣鐢ㄦ埛鐢ㄤ簬鍚庣画娴嬭瘯
        target_user = User.objects.create(
            username='delete_test',
            email='delete@test.com',
            role=User.Role.USER,
            is_active=True
        )
        target_user.set_password('delete123')
        target_user.save()
        print(f"   閲嶆柊鍒涘缓鐩爣鐢ㄦ埛: {target_user.username}")
        
    except Exception as e:
        print(f"   绠＄悊鍛樺垹闄ょ敤鎴峰け璐? {e}")
    
    # 娴嬭瘯鏅€氱敤鎴峰垹闄ょ敤鎴?
    print(f"\n4. 娴嬭瘯鏅€氱敤鎴峰垹闄ょ敤鎴?)
    try:
        request = factory.delete(f'/api/v1/users/users/{target_user.id}/')
        request.user = normal_user
        viewset.request = request
        
        # 娴嬭瘯get_object
        obj = viewset.get_object()
        print(f"   get_object鎴愬姛: {obj.username}")
        
        # 娴嬭瘯perform_destroy
        viewset.perform_destroy(target_user)
        print("   perform_destroy鎴愬姛")
        
    except Exception as e:
        print(f"   鏅€氱敤鎴峰垹闄ょ敤鎴峰け璐? {e}")
    
    print("\n" + "=" * 40)
    print("娴嬭瘯瀹屾垚")
    print("=" * 40)

if __name__ == '__main__':
    test_user_permissions()

