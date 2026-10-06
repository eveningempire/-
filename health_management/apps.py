from __future__ import annotations

from django.apps import AppConfig


class HealthManagementConfig(AppConfig):
    """Configuration for the health_management application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "health_management"