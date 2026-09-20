from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth import authenticate, login, logout
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .permissions import ROLE_PERMISSIONS, PERMISSION_LABELS, user_role, has_permission, effective_permissions
from phm.models import UserPermissionProfile

User = get_user_model()

@method_decorator(csrf_exempt, name="dispatch")
class LoginView(APIView):
    permission_classes = []
    authentication_classes = []
    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        user = authenticate(request, username=username, password=password)
        if not user or not user.is_active:
            return Response({"detail": "用户名或密码错误"}, status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        role = user_role(user)
        return Response({"username": user.username, "role": role, "role_label": "管理员" if role == "admin" else "用户"})

@method_decorator(csrf_exempt, name="dispatch")
class LogoutView(APIView):
    permission_classes = []
    authentication_classes = []
    def post(self, request):
        logout(request)
        return Response({"detail": "已退出登录"})


class PermissionProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = user_role(request.user)
        return Response({"username": request.user.username, "role": role, "permissions": sorted(effective_permissions(request.user))})


class RoleCatalogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = []
        if has_permission(request.user, "manage_users"):
            users = [{"id": user.id, "username": user.username, "role": user_role(user),
                      "permissions": sorted(effective_permissions(user))}
                     for user in User.objects.filter(is_active=True).order_by("username")]
        return Response({
            "permission_catalog": [{"key": key, "label": label} for key, label in PERMISSION_LABELS.items()],
            "roles": [{"key": key, "permissions": sorted(value),
                       "permission_labels": [PERMISSION_LABELS[p] for p in sorted(value)]}
                      for key, value in ROLE_PERMISSIONS.items()],
            "users": users,
        })


class GroupRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not has_permission(request.user, "manage_users"):
            return Response({"detail": "只有管理员可以调整角色"}, status=status.HTTP_403_FORBIDDEN)
        user_id, role = request.data.get("user_id"), request.data.get("role", "viewer")
        if role not in {"admin", "viewer"}:
            return Response({"detail": "不支持的角色"}, status=status.HTTP_400_BAD_REQUEST)
        if not user_id:
            username, password = request.data.get("username"), request.data.get("password")
            if not username or not password:
                return Response({"detail": "创建查看者需要用户名和密码"}, status=status.HTTP_400_BAD_REQUEST)
            if User.objects.filter(username=username).exists():
                return Response({"detail": "用户名已存在"}, status=status.HTTP_400_BAD_REQUEST)
            target = User.objects.create_user(username=username, password=password, is_active=True)
            user_id = target.id
        else:
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
        requested = request.data.get("permissions")
        if requested is not None:
            if not isinstance(requested, list):
                return Response({"detail": "权限必须是列表"}, status=status.HTTP_400_BAD_REQUEST)
            invalid = set(requested) - set(PERMISSION_LABELS)
            if invalid:
                return Response({"detail": f"存在无效权限：{', '.join(sorted(invalid))}"}, status=status.HTTP_400_BAD_REQUEST)
            profile, _ = UserPermissionProfile.objects.get_or_create(user=target)
            profile.permissions = [] if role == "admin" else sorted(set(requested) | {"view"})
            profile.save(update_fields=["permissions", "updated_at"])
        return Response({"user_id": target.id, "role": role, "permissions": sorted(effective_permissions(target))})
