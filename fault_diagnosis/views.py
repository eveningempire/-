from __future__ import annotations

import json
import tempfile
from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .service import DiagnosisService
from .matlab_bridge import MatlabBridge
from .route_algorithms import msfg_teams_rt, pca_iforest


def _quality_for_csv(csv_path):
    """Attach a bounded quality report before an algorithm is allowed to decide."""
    from datasets.batch_processing import inspect_file
    report = inspect_file(csv_path)
    if report['row_count'] == 0 or not report['numeric_columns']:
        raise ValueError('数据质量不合格:文件为空或没有可用数值信号')
    return report


def _standardize_result(result, quality):
    label = result.get('aggregate_pred_name') or result.get('pred_name') or '未知'
    confidence = result.get('confidence')
    if label in {'正常', '正常状态'}:
        decision = 'normal'
    elif label in {'未知', '不确定', '诊断不确定'} or confidence is not None and float(confidence) < 0.55:
        decision = 'uncertain'
    else:
        decision = 'abnormal'
    result['decision'] = decision
    result['decision_label'] = {'normal': '正常', 'abnormal': '异常', 'uncertain': '诊断不确定'}[decision]
    result['decision_rule'] = '按算法输出类别与置信度判定;置信度低于 0.55 时标记为诊断不确定'
    result['data_quality'] = {key: quality[key] for key in ('row_count', 'columns', 'numeric_columns', 'missing_value_count', 'invalid_value_count', 'quality_status', 'quality_message')}
    return result


def status(request):
    service = DiagnosisService.instance()
    return JsonResponse({"ok": True, "available": service.available, "model": "Hier14", "source": str(service.predictor_path), "error": service.error})


@csrf_exempt
def predict(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "仅支持 POST"}, status=405)
    algorithm = "unknown"
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
                quality = _quality_for_csv(csv_path)
                result = _standardize_result(_run_algorithm(algorithm, csv_path), quality)
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
            quality = _quality_for_csv(csv_path)
            result = _standardize_result(_run_algorithm(algorithm, csv_path), quality)
        return JsonResponse({"ok": True, "model": result.get("algorithm", algorithm), "result": result})
    except Exception as exc:
        return JsonResponse({"ok": False, "error": str(exc), "model": algorithm or "unknown"}, status=503)


@csrf_exempt
def batch_predict(request):
    """Run one diagnosis algorithm over many stored datasets.

    The endpoint is intentionally synchronous and bounded (200 datasets) so it
    remains deployable without Redis/Celery in the offline package. Callers can
    submit chunks for larger campaigns and receive a per-dataset error list.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': '仅支持 POST'}, status=405)
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
        ids = body.get('dataset_ids')
        if not isinstance(ids, list) or not ids:
            return JsonResponse({'ok': False, 'error': 'dataset_ids 必须是非空数组'}, status=400)
        if len(ids) > 200:
            return JsonResponse({'ok': False, 'error': '单次最多诊断 200 个数据集,请分批提交'}, status=400)
        algorithm = body.get('algorithm', 'hier14')
        from datasets.models import Dataset
        output = []
        for dataset_id in ids:
            item = {'dataset_id': dataset_id}
            try:
                dataset = Dataset.objects.get(pk=dataset_id)
                quality = _quality_for_csv(dataset.file.path)
                item.update({'status': 'success', 'result': _standardize_result(_run_algorithm(algorithm, dataset.file.path), quality)})
            except Dataset.DoesNotExist:
                item.update({'status': 'failed', 'error': '数据集不存在'})
            except Exception as exc:
                item.update({'status': 'failed', 'error': str(exc)})
            output.append(item)
        return JsonResponse({'ok': True, 'algorithm': algorithm, 'total': len(output), 'success': sum(x['status'] == 'success' for x in output), 'failed': sum(x['status'] == 'failed' for x in output), 'results': output})
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)


def _run_algorithm(algorithm, csv_path):
    if algorithm == "hier14":
        result = DiagnosisService.instance().predict(csv_path); result.setdefault("algorithm", "Hier14"); return result
    if algorithm == "msfg_teams_rt": return msfg_teams_rt(csv_path)
    if algorithm == "pca_iforest": return pca_iforest(csv_path)
    raise ValueError("未知诊断算法,可选 hier14、msfg_teams_rt、pca_iforest")

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
