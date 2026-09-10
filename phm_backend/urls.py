"""
URL configuration for the 航天器PHM backend.

This module routes incoming HTTP requests to the appropriate views. API
endpoints are grouped by application 鈥?data management, health management
and user management 鈥?and exposed at versioned paths (e.g. /api/v1/). You
can adjust the URL prefixes to suit your deployment architecture.
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from .permission_views import PermissionProfileView, RoleCatalogView, GroupRoleView

urlpatterns = [
    path("api/v1/phm/", include("phm.urls")),
    path("api/v1/integrations/wujiaxin/", include("wujiaxin_integration.urls")),
    path("api/v1/simulation-dataset/", include("simulation_dataset.urls")),
    path("api/v1/permissions/profile/", PermissionProfileView.as_view()),
    path("api/v1/permissions/roles/", RoleCatalogView.as_view()),
    path("api/v1/permissions/assign-role/", GroupRoleView.as_view()),
    path("admin/", admin.site.urls),
    # Favicon route to prevent 404 errors
    path("favicon.ico", RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    path("", TemplateView.as_view(template_name="index.html"), name="frontend"),
    path("<path:path>", TemplateView.as_view(template_name="index.html"), name="frontend-route"),
    # API version 1 endpoints
] + (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else [])
