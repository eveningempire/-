from __future__ import annotations

import json
import tempfile
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .service import DiagnosisService
from .matlab_bridge import MatlabBridge
from .route_algorithms import msfg_teams_rt, pca_iforest


def status(request):
    service = DiagnosisService.instance()
    return JsonResponse({"ok": True, "available": service.available, "model": "Hier14", "source": str(service.predictor_path), "error": service.error})


@csrf_exempt
def predict(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "仅支持 POST"}, status=405)
    try:
        algorithm = request.POST.get("algorithm", "hier14") if request.FILES.get("file") else None
        if request.FILES.get("file"):
            uploaded = request.FILES["file"]
            if not uploaded.name.lower().endswith(".csv"):
                return JsonResponse({"ok": False, "error": "只支持 CSV 文件"}, status=400)
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
                for chunk in uploaded.chunks():
                    tmp.write(chunk)
                csv_path = Path(tmp.name)
            try:
                result = _run_algorithm(algorithm, csv_path)
            finally:
                csv_path.unlink(missing_ok=True)
        else:
            body = json.loads(request.body.decode("utf-8") or "{}")
            algorithm = body.get("algorithm", "hier14")
            if body.get('dataset_id'):
                from datasets.services import path_for
                csv_path = path_for(body['dataset_id'])
            else: csv_path = body.get("csv_path")
            if not csv_path:
                return JsonResponse({"ok": False, "error": "请上传 CSV 文件或提供 csv_path"}, status=400)
            result = _run_algorithm(algorithm, csv_path)
        return JsonResponse({"ok": True, "model": result.get("algorithm", algorithm), "result": result})
    except Exception as exc:
        return JsonResponse({"ok": False, "error": str(exc), "model": algorithm or "unknown"}, status=503)


def _run_algorithm(algorithm, csv_path):
    if algorithm == "hier14":
        result = DiagnosisService.instance().predict(csv_path); result.setdefault("algorithm", "Hier14"); return result
    if algorithm == "msfg_teams_rt": return msfg_teams_rt(csv_path)
    if algorithm == "pca_iforest": return pca_iforest(csv_path)
    raise ValueError("未知诊断算法，可选 hier14、msfg_teams_rt、pca_iforest")

@csrf_exempt
def simulate_inject(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': '仅支持 POST'}, status=405)
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
        bridge = MatlabBridge()
        out = Path(__file__).resolve().parent.parent / 'media' / 'matlab_runs'
        out.mkdir(parents=True, exist_ok=True)
        result = bridge.run(out, body.get('fault'))
        return JsonResponse({'ok': True, 'output_dir': str(out), 'stdout': result.stdout[-4000:]})
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=503)
