"""
URL configuration for the data_management app.

Defines RESTful API endpoints for PHMs, data import sessions and data
records. The endpoints are registered under the /api/v1/data/ prefix in
the project level URL conf.
"""

from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import (
    PHMTypeViewSet,
    SatelliteViewSet,
    PHMModelViewSet,
    PHMViewSet,
    ImportSessionViewSet,
    PHMDataViewSet,
    TCPIngestViewSet,
    SystemConfigViewSet,
    TimelineDataView,
    DetectionOverviewView,
    RealtimeDetectionView,
)


router = DefaultRouter()
router.register(r"cmg-types", PHMTypeViewSet, basename="cmgtype")
router.register(r"satellites", SatelliteViewSet, basename="satellite")
router.register(r"cmg-models", PHMModelViewSet, basename="cmgmodel")
router.register(r"cmgs", PHMViewSet, basename="cmg")
router.register(r"import-sessions", ImportSessionViewSet, basename="importsession")
router.register(r"data", PHMDataViewSet, basename="cmgdata")
router.register(r"tcp-ingest", TCPIngestViewSet, basename="tcpingest")
router.register(r"system-config", SystemConfigViewSet, basename="systemconfig")


urlpatterns = router.urls + [
    path("data/timeline/", TimelineDataView.as_view(), name="data-timeline"),
    path("detection-overview/", DetectionOverviewView.as_view(), name="detection-overview"),
    path("realtime-detection/", RealtimeDetectionView.as_view(), name="realtime-detection"),
]
