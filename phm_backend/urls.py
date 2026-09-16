"""
URL configuration for the 航天器PHM backend.

This module routes incoming HTTP requests to the appropriate views. API
endpoints are grouped by application (data management, health management
and user management) and exposed at versioned paths (e.g. /api/v1/). You
can adjust the URL prefixes to suit your deployment architecture.
"""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import RedirectView
from .permission_views import PermissionProfileView, RoleCatalogView, GroupRoleView, LoginView, LogoutView


def frontend(request, path=""):
    """Read Vite's current entry file per request so rebuilt hashes never go stale."""
    index_path = settings.BASE_DIR / "frontend" / "dist" / "index.html"
    if not index_path.is_file():
        return HttpResponse("前端尚未构建，请先运行 npm run build。", status=503, content_type="text/plain; charset=utf-8")
    response = HttpResponse(index_path.read_bytes(), content_type="text/html; charset=utf-8")
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

urlpatterns = [
    path("api/v1/phm/", include("phm.urls")),
    path("api/v1/integrations/algorithm-assets/", include("algorithm_integration.urls")),
    path("api/v1/simulation-dataset/", include("simulation_dataset.urls")),
    path("api/v1/health-assessment/", include("platform_health.urls")),
    path("api/v1/fault-diagnosis/", include("fault_diagnosis.urls")),
    path("api/v1/rul/", include("rul_service.urls")),
    path("api/v1/simulation-demo/", include("simulation_demo.urls")),
    path("api/v1/datasets/", include("datasets.urls")),
    path("api/v1/knowledge/", include("fault_models.urls")),
    path("api/v1/permissions/profile/", PermissionProfileView.as_view()),
    path("api/v1/permissions/roles/", RoleCatalogView.as_view()),
    path("api/v1/permissions/assign-role/", GroupRoleView.as_view()),
    path("api/v1/auth/login/", LoginView.as_view()),
    path("api/v1/auth/logout/", LogoutView.as_view()),
    path("admin/", admin.site.urls),
    # Favicon route to prevent 404 errors
    path("favicon.ico", RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    path("", frontend, name="frontend"),
    path("<path:path>", frontend, name="frontend-route"),
    # API version 1 endpoints
] + (static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) if settings.DEBUG else [])

