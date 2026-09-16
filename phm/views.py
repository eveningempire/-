import json
import math
from collections import deque
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import AcceptanceTelemetry, AlarmRule, StructureNode, AuditEvent

_latest_external_telemetry = None
_chain_records = deque(maxlen=2000)

@csrf_exempt
def telemetry_ingest(request):
    global _latest_external_telemetry
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': '仅支持 POST'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
        required = ('pressure', 'temperature', 'attitude', 'fuel')
        if any(k not in payload for k in required):
            return JsonResponse({'ok': False, 'error': '需要 pressure、temperature、attitude、fuel'}, status=400)
        payload.update(source='external', received_at=timezone.now().isoformat())
        _latest_external_telemetry = payload
        return JsonResponse({'ok': True, 'data': payload})
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)

def telemetry_latest(request):
    return JsonResponse({'ok': True, 'available': _latest_external_telemetry is not None, 'data': _latest_external_telemetry})

CAPABILITIES = [
    {"key": "monitoring", "name": "状态监测", "status": "implemented", "endpoints": ["telemetry/ingest/", "telemetry/latest/"]},
    {"key": "diagnosis", "name": "故障诊断", "status": "implemented", "endpoints": ["/api/v1/fault-diagnosis/status/", "predict/"]},
    {"key": "health_index", "name": "健康评估/HI", "status": "implemented", "endpoints": ["/api/v1/health-assessment/status/", "evaluate/", "summary/"]},
    {"key": "rul", "name": "寿命/RUL预测", "status": "implemented", "endpoints": ["/api/v1/rul/status/", "predict/"]},
    {"key": "simulation", "name": "故障注入与仿真", "status": "implemented", "endpoints": ["/api/v1/simulation-demo/", "/api/v1/fault-diagnosis/simulate-inject/"]},
    {"key": "release_assessment", "name": "再飞可行性与发射放行评估", "status": "implemented", "endpoints": ["/api/v1/phm/release-assessments/"]},
    {"key": "model_governance", "name": "模型目录与工程状态管理", "status": "implemented", "endpoints": ["/api/v1/phm/model-catalog/"]},
    {"key": "visualization_3d", "name": "三维部件定位", "status": "implemented", "endpoints": ["/model-3d"]},
    {"key": "data_storage", "name": "数据存储与导入", "status": "available_in_legacy_module", "endpoints": ["data_management.urls"]},
    {"key": "permissions", "name": "角色与权限", "status": "implemented", "endpoints": ["/api/v1/auth/login/", "/api/v1/permissions/profile/"]},
]

def project_status(request):
    try:
        from platform_health.service import HealthAssessmentService
        health_loaded = HealthAssessmentService.instance().available
    except Exception:
        health_loaded = False
    try:
        from fault_diagnosis.service import DiagnosisService
        diagnosis_loaded = DiagnosisService.instance().available
    except Exception:
        diagnosis_loaded = False
    import os
    simulation_dir = os.environ.get("HEALTH_DATACSV_DIR", str(__import__('pathlib').Path(__file__).resolve().parent.parent / "simulate" / "datacsv"))
    simulation_loaded = os.path.isdir(simulation_dir) and any(name.endswith('.csv') for name in os.listdir(simulation_dir))
    return JsonResponse({"project": "reusable-spacecraft-phm", "stage": "integration", "algorithms_loaded": health_loaded or diagnosis_loaded, "health_assessment_loaded": health_loaded, "fault_diagnosis_loaded": diagnosis_loaded, "simulation_data_loaded": simulation_loaded})

def capability_catalog(request):
    return JsonResponse({"capabilities": CAPABILITIES, "acceptance_count": len(CAPABILITIES), "schema_version": "1.1"})


def _numeric_payload(payload):
    values = {}
    for key, value in payload.items():
        try:
            number = float(value)
            if math.isfinite(number):
                values[key] = number
        except (TypeError, ValueError):
            continue
    return values


@csrf_exempt
def chain_ingest(request):
    """统一验收链路入口：接收一条遥测并立即生成基础质量状态。"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "仅支持 POST"}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
        numeric = _numeric_payload(payload)
        if not numeric:
            return JsonResponse({"ok": False, "error": "至少需要一个有限数值遥测字段"}, status=400)
        rules = AlarmRule.objects.filter(enabled=True)
        alarms = {}
        for rule in rules:
            if rule.signal not in numeric:
                continue
            value = numeric[rule.signal]
            hit = {"gt": value > rule.threshold, "gte": value >= rule.threshold, "lt": value < rule.threshold, "lte": value <= rule.threshold, "eq": value == rule.threshold}[rule.operator]
            if hit:
                alarms[rule.signal] = {"value": value, "threshold": rule.threshold, "severity": rule.severity, "rule": rule.name}
        health = round(max(0.0, 1.0 - min(1.0, len(alarms) / max(1, len(numeric)))), 4)
        status_value = "alarm" if alarms else "normal"
        saved = AcceptanceTelemetry.objects.create(vehicle_id=str(payload.get("vehicle_id", "default")), values=payload, anomaly_fields=alarms, health_index=health, status=status_value)
        AuditEvent.objects.create(username=getattr(getattr(request, "user", None), "username", ""), action="telemetry_ingest", resource=str(saved.pk), detail={"signals": list(numeric)})
        record = {"id": saved.pk, "data": payload, "numeric": numeric, "alarms": alarms, "health_index": health, "status": status_value, "received_at": saved.received_at.isoformat()}
        _chain_records.append(record)
        return JsonResponse({"ok": True, "accepted": True, "sequence": len(_chain_records), "record": record})
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return JsonResponse({"ok": False, "error": f"无效 JSON: {exc}"}, status=400)


def chain_evaluate(request):
    """对最近遥测执行可追溯的异常、健康指数和 RUL 基线计算。"""
    rows = list(AcceptanceTelemetry.objects.order_by("received_at").values("id", "vehicle_id", "values", "anomaly_fields", "health_index", "status", "received_at"))
    if not rows:
        return JsonResponse({"ok": True, "count": 0, "results": []})
    results = []
    for idx, row in enumerate(rows):
        results.append({"sequence": idx + 1, "id": row["id"], "vehicle_id": row["vehicle_id"], "received_at": row["received_at"], "anomaly": bool(row["anomaly_fields"]), "anomaly_fields": row["anomaly_fields"], "health_index": row["health_index"], "status": row["status"]})
    hi = [item["health_index"] for item in results]
    slope = (hi[-1] - hi[0]) / max(1, len(hi) - 1)
    rul = None if slope >= 0 else round(max(0.0, (hi[-1] - 0.2) / -slope), 3)
    return JsonResponse({"ok": True, "count": len(results), "results": results, "summary": {"latest": results[-1], "rul": rul, "rul_unit": "sample_interval", "trend": "下降" if slope < 0 else "平稳或上升"}})


def chain_status(request):
    return JsonResponse({"ok": True, "available": True, "records": AcceptanceTelemetry.objects.count(), "rules": AlarmRule.objects.filter(enabled=True).count(), "stages": ["ingest", "storage", "anomaly", "health_index", "rul", "query"]})


@csrf_exempt
def rules(request):
    if request.method == "GET":
        return JsonResponse({"ok": True, "results": list(AlarmRule.objects.values())})
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "仅支持 GET/POST"}, status=405)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
        obj = AlarmRule.objects.create(name=body["name"], signal=body["signal"], operator=body.get("operator", "gt"), threshold=float(body["threshold"]), severity=body.get("severity", "warning"), description=body.get("description", ""))
        return JsonResponse({"ok": True, "rule": {"id": obj.id, "name": obj.name}} , status=201)
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)


@csrf_exempt
def structure(request):
    if request.method == "GET":
        return JsonResponse({"ok": True, "results": list(StructureNode.objects.values())})
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
        if request.method == "POST":
            obj = StructureNode.objects.create(node_key=body["node_key"], name=body["name"], node_type=body.get("node_type", "component"), properties=body.get("properties", {}))
            return JsonResponse({"ok": True, "id": obj.id}, status=201)
        if request.method == "DELETE":
            StructureNode.objects.filter(node_key=body.get("node_key")).delete()
            return JsonResponse({"ok": True})
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    return JsonResponse({"ok": False, "error": "仅支持 GET/POST/DELETE"}, status=405)


def export_chain(request):
    import csv, io
    output = io.StringIO(); writer = csv.writer(output); writer.writerow(["id", "vehicle_id", "received_at", "health_index", "status", "anomaly_fields"])
    for row in AcceptanceTelemetry.objects.order_by("received_at").values("id", "vehicle_id", "received_at", "health_index", "status", "anomaly_fields"):
        writer.writerow([row["id"], row["vehicle_id"], row["received_at"], row["health_index"], row["status"], json.dumps(row["anomaly_fields"], ensure_ascii=False)])
    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8"); response["Content-Disposition"] = 'attachment; filename="acceptance_telemetry.csv"'; return response
_latest_external_telemetry = None

@csrf_exempt
def telemetry_ingest(request):
    """接收外部实时遥测；未有外部数据时前端使用仿真流。"""
    global _latest_external_telemetry
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': '仅支持 POST'}, status=405)
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
        required = ('pressure', 'temperature', 'attitude', 'fuel')
        if any(k not in payload for k in required):
            return JsonResponse({'ok': False, 'error': '需要 pressure、temperature、attitude、fuel'}, status=400)
        payload['source'] = 'external'
        payload['received_at'] = timezone.now().isoformat()
        _latest_external_telemetry = payload
        return JsonResponse({'ok': True, 'data': payload})
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)

def telemetry_latest(request):
    return JsonResponse({'ok': True, 'available': _latest_external_telemetry is not None, 'data': _latest_external_telemetry})
