from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .permissions import ROLE_PERMISSIONS, user_role, has_permission

User = get_user_model()

class LoginView(APIView):
    permission_classes = []
    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)
        if not user or not user.is_active:
            return Response({"detail": "用户名或密码错误"}, status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        return Response({"username": user.username, "role": user_role(user)})

class LogoutView(APIView):
    permission_classes = []
    def post(self, request):
        logout(request)
        return Response({"detail": "已退出登录"})


class PermissionProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = user_role(request.user)
        return Response({"username": request.user.username, "role": role, "permissions": sorted(ROLE_PERMISSIONS.get(role, set()))})


class RoleCatalogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"roles": [{"key": key, "permissions": sorted(value)} for key, value in ROLE_PERMISSIONS.items()]})


class GroupRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not has_permission(request.user, "manage_users"):
            return Response({"detail": "只有管理员可以调整角色"}, status=status.HTTP_403_FORBIDDEN)
        user_id, role = request.data.get("user_id"), request.data.get("role")
        if role not in {"admin", "viewer"}:
            return Response({"detail": "不支持的角色"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            target = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"detail": "用户不存在"}, status=status.HTTP_404_NOT_FOUND)
        target.groups.remove(*Group.objects.filter(name__startswith="PHM-"))
        if role == "admin":
            target.is_staff = True
        else:
            target.is_staff = False
        target.save(update_fields=["is_staff"])
        if role != "admin":
            group, _ = Group.objects.get_or_create(name="PHM-查看者")
            target.groups.add(group)
        return Response({"user_id": target.id, "role": role})
