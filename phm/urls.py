from django.urls import path
from .views import capability_catalog, project_status, telemetry_ingest, telemetry_latest

urlpatterns = [
    path("status/", project_status, name="phm-status"),
    path("capabilities/", capability_catalog, name="phm-capabilities"),
    path("telemetry/ingest/", telemetry_ingest, name="telemetry-ingest"),
    path("telemetry/latest/", telemetry_latest, name="telemetry-latest"),
]
