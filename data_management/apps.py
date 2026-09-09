from __future__ import annotations

from django.apps import AppConfig


class DataManagementConfig(AppConfig):
    """Configuration for the data_management application.

    This app contains models and views for importing and serving raw PHM data.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "data_management"
