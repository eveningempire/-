import json
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

_latest_external_telemetry = None

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
    {"key": "monitoring", "name": "状态监测", "status": "placeholder"},
    {"key": "diagnosis", "name": "故障诊断", "status": "placeholder"},
    {"key": "health_index", "name": "健康评估/HI", "status": "placeholder"},
    {"key": "rul", "name": "寿命/RUL预测", "status": "placeholder"},
    {"key": "simulation", "name": "故障注入与仿真", "status": "placeholder"},
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
    return JsonResponse({"capabilities": CAPABILITIES})
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
