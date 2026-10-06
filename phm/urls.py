from django.urls import path
from .views import capability_catalog, project_status, telemetry_ingest, telemetry_latest, chain_ingest, chain_evaluate, chain_status, rules, export_chain
from . import telemetry
from . import fault_replay, structure_api
from . import release_assessment

urlpatterns = [
    path("status/", project_status, name="phm-status"),
    path("capabilities/", capability_catalog, name="phm-capabilities"),
    path("telemetry/ingest/", telemetry_ingest, name="telemetry-ingest"),
    path("telemetry/latest/", telemetry_latest, name="telemetry-latest"),
    path("chain/ingest/", chain_ingest, name="chain-ingest"),
    path("chain/evaluate/", chain_evaluate, name="chain-evaluate"),
    path("chain/status/", chain_status, name="chain-status"),
    path("acceptance/rules/", rules, name="acceptance-rules"),
    path("acceptance/structure/", structure_api.structure_collection, name="acceptance-structure"),
    path("acceptance/structure/<int:node_id>/", structure_api.structure_detail, name="acceptance-structure-detail"),
    path("acceptance/export/", export_chain, name="acceptance-export"),
    path('telemetry/sessions/', telemetry.sessions),
    path('telemetry/sessions/<uuid:session_id>/samples/', telemetry.samples),
    path('telemetry/sessions/<uuid:session_id>/ingest/', telemetry.ingest),
    path('telemetry/sessions/<uuid:session_id>/close/', telemetry.close),
    path('telemetry/sessions/<uuid:session_id>/monitoring/', telemetry.monitoring),
    path('telemetry/sessions/<uuid:session_id>/alarms/', telemetry.alarms),
    path('telemetry/sessions/<uuid:session_id>/export/', telemetry.export),
    path('fault-events/', fault_replay.events, name='fault-events'),
    path('fault-events/<uuid:event_id>/', fault_replay.event_detail, name='fault-event-detail'),
    path('fault-events/<uuid:event_id>/replays/', fault_replay.create_replay, name='fault-replay-create'),
    path('fault-replays/<uuid:replay_id>/', fault_replay.replay_control, name='fault-replay-control'),
    path('release-assessments/', release_assessment.assessments, name='release-assessments'),
    path('model-catalog/', release_assessment.model_catalog, name='model-catalog'),
]
