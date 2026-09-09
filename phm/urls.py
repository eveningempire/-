from django.urls import path
from .views import capability_catalog, project_status

urlpatterns = [
    path("status/", project_status, name="phm-status"),
    path("capabilities/", capability_catalog, name="phm-capabilities"),
]
