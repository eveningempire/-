from django.urls import path
from .views import capability_catalog, project_status, telemetry_ingest, telemetry_latest, chain_ingest, chain_evaluate, chain_status, rules, structure, export_chain
from . import telemetry

urlpatterns = [
    path("status/", project_status, name="phm-status"),
    path("capabilities/", capability_catalog, name="phm-capabilities"),
    path("telemetry/ingest/", telemetry_ingest, name="telemetry-ingest"),
    path("telemetry/latest/", telemetry_latest, name="telemetry-latest"),
    path("chain/ingest/", chain_ingest, name="chain-ingest"),
    path("chain/evaluate/", chain_evaluate, name="chain-evaluate"),
    path("chain/status/", chain_status, name="chain-status"),
    path("acceptance/rules/", rules, name="acceptance-rules"),
    path("acceptance/structure/", structure, name="acceptance-structure"),
    path("acceptance/export/", export_chain, name="acceptance-export"),
    path('telemetry/sessions/', telemetry.sessions),
    path('telemetry/sessions/<uuid:session_id>/samples/', telemetry.samples),
    path('telemetry/sessions/<uuid:session_id>/ingest/', telemetry.ingest),
    path('telemetry/sessions/<uuid:session_id>/close/', telemetry.close),
    path('telemetry/sessions/<uuid:session_id>/export/', telemetry.export),
]
