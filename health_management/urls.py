"""
URL configuration for the health_management app.

Registers viewsets for rules, diagnosis graphs and various result types.
These endpoints are nested under /api/v1/health/ in the project URL conf.
"""

from rest_framework.routers import DefaultRouter

from .views import (
    RuleViewSet,
    DiagnosisGraphViewSet,
    AnomalyResultViewSet,
    RuleResultViewSet,
    DiagnosisResultViewSet,
    HealthEvaluationViewSet,
    LifePredictionViewSet,
    IMSModelViewSet,
    IMSDetectionResultViewSet,
)


router = DefaultRouter()
router.register(r"rules", RuleViewSet, basename="rule")
router.register(r"diagnosis-graphs", DiagnosisGraphViewSet, basename="diagnosisgraph")
router.register(r"anomalies", AnomalyResultViewSet, basename="anomalyresult")
router.register(r"rule-results", RuleResultViewSet, basename="ruleresult")
router.register(r"diagnosis-results", DiagnosisResultViewSet, basename="diagnosisresult")
router.register(r"evaluations", HealthEvaluationViewSet, basename="healthevaluation")
router.register(r"life-predictions", LifePredictionViewSet, basename="lifeprediction")
router.register(r"ims-models", IMSModelViewSet, basename="imsmodel")
router.register(r"ims-results", IMSDetectionResultViewSet, basename="imsresult")


urlpatterns = router.urls