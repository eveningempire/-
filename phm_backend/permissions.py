from __future__ import annotations

from rest_framework.permissions import BasePermission


ROLE_PERMISSIONS = {
    "admin": {"view", "manage_users", "manage_structure", "submit_simulation", "run_analysis", "publish"},
    "engineer": {"view", "manage_structure", "submit_simulation", "run_analysis", "publish"},
    "operator": {"view", "submit_simulation", "run_analysis"},
    "viewer": {"view"},
}


def user_role(user):
    if not user or not user.is_authenticated:
        return "anonymous"
    if user.is_superuser or user.is_staff or user.groups.filter(name="PHM-管理员").exists():
        return "admin"
    for group_name, role in (("PHM-工程师", "engineer"), ("PHM-操作员", "operator"), ("PHM-查看者", "viewer")):
        if user.groups.filter(name=group_name).exists():
            return role
    return "viewer"


def has_permission(user, permission):
    return permission in ROLE_PERMISSIONS.get(user_role(user), set())


class PHMAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class PHMRolePermission(BasePermission):
    required_permission = "view"

    def has_permission(self, request, view):
        return has_permission(request.user, getattr(view, "required_permission", self.required_permission))
