from django.http import JsonResponse

CAPABILITIES = [
    {"key": "monitoring", "name": "状态监测", "status": "placeholder"},
    {"key": "diagnosis", "name": "故障诊断", "status": "placeholder"},
    {"key": "health_index", "name": "健康评估/HI", "status": "placeholder"},
    {"key": "rul", "name": "寿命/RUL预测", "status": "placeholder"},
    {"key": "simulation", "name": "故障注入与仿真", "status": "placeholder"},
]

def project_status(request):
    return JsonResponse({"project": "reusable-spacecraft-phm", "stage": "scaffold", "algorithms_loaded": False, "simulation_data_loaded": False})

def capability_catalog(request):
    return JsonResponse({"capabilities": CAPABILITIES})
