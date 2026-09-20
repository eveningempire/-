from __future__ import annotations

from rest_framework.permissions import BasePermission
from django.core.exceptions import ObjectDoesNotExist


ROLE_PERMISSIONS = {
    "admin": {"view", "manage_users", "manage_structure", "submit_simulation", "run_analysis", "publish"},
    "viewer": {"view"},
}

PERMISSION_LABELS = {
    "view": "查看平台",
    "manage_users": "用户权限管理",
    "manage_structure": "项目结构与数据管理",
    "submit_simulation": "提交仿真任务",
    "run_analysis": "运行诊断与评估",
    "publish": "发布分析结果",
}


def user_role(user):
    if not user or not user.is_authenticated:
        return "anonymous"
    if user.is_superuser or user.is_staff or user.groups.filter(name="PHM-管理员").exists():
        return "admin"
    for group_name, role in (("PHM-查看者", "viewer"),):
        if user.groups.filter(name=group_name).exists():
            return role
    return "viewer"


def has_permission(user, permission):
    role = user_role(user)
    if role == "admin":
        return permission in ROLE_PERMISSIONS["admin"]
    assigned = assigned_permissions(user)
    return permission in (ROLE_PERMISSIONS.get(role, set()) | assigned)


def assigned_permissions(user):
    try:
        profile = user.phm_permission_profile
    except (AttributeError, ObjectDoesNotExist):
        return set()
    return set(profile.permissions or [])


def effective_permissions(user):
    role = user_role(user)
    if role == "admin":
        return set(ROLE_PERMISSIONS["admin"])
    return set(ROLE_PERMISSIONS.get(role, set())) | assigned_permissions(user)


class PHMAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class PHMRolePermission(BasePermission):
    required_permission = "view"

    def has_permission(self, request, view):
        return has_permission(request.user, getattr(view, "required_permission", self.required_permission))
