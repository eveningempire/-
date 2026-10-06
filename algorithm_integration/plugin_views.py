"""Stable HTTP API for discovering and running local algorithm adapters."""
from __future__ import annotations

import json
import zipfile

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from datasets.models import Dataset
from phm_backend.permissions import has_permission
from .plugin_registry import get_algorithm, list_algorithms, public_record, run_plugin, validate_parameters
from .plugin_import import install


def _access(request, permission):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "请先登录"}, status=401)
    if not has_permission(request.user, permission):
        return JsonResponse({"ok": False, "error": "当前账号无权执行此操作"}, status=403)
    return None


@require_GET
@ensure_csrf_cookie
def algorithms(request):
    denied = _access(request, "view")
    if denied:
        return denied
    category = request.GET.get("category") or None
    if category and category not in {"diagnosis", "health_assessment", "rul"}:
        return JsonResponse({"ok": False, "error": "无效 category"}, status=400)
    records, errors = list_algorithms(category)
    return JsonResponse({"ok": True, "count": len(records), "results": records, "invalid_plugins": errors})


@require_GET
def algorithm_detail(request, key):
    denied = _access(request, "view")
    if denied:
        return denied
    try:
        record = get_algorithm(key)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=404)
    return JsonResponse({"ok": True, "algorithm": public_record(record)})


@csrf_protect
@require_POST
def import_algorithm(request):
    denied = _access(request, "manage_structure")
    if denied:
        return denied
    uploaded = request.FILES.get("file")
    if uploaded is None:
        return JsonResponse({"ok": False, "error": "请选择 ZIP 算法包"}, status=400)
    try:
        record = install(uploaded)
    except (ValueError, OSError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    return JsonResponse({"ok": True, "algorithm": record}, status=201)


def _run_builtin(record, dataset, parameters):
    key = record["key"]
    if key in {"hier14", "msfg_teams_rt", "pca_iforest"}:
        from fault_diagnosis.views import _quality_for_csv, _run_algorithm, _standardize_result
        if not dataset.file.name.lower().endswith(".csv"):
            raise ValueError("故障诊断算法只接受 CSV 数据集")
        return _standardize_result(_run_algorithm(key, dataset.file.path), _quality_for_csv(dataset.file.path))
    if key in {"cdpca_ga", "ae_gmm", "gcn_rbd"}:
        if not dataset.file.name.lower().endswith(".csv"):
            raise ValueError("健康评估算法只接受 CSV 数据集")
        from datasets.services import read_rows
        from platform_health.algorithms import cdpca_ga, ae_gmm, gcn_rbd
        rows = read_rows(dataset.pk)
        if key == "gcn_rbd":
            component = cdpca_ga(rows)
            component["component_id"] = dataset.component or f"dataset_{dataset.pk}"
            result = gcn_rbd([component], [component["component_id"]])
        else:
            result = {"cdpca_ga": cdpca_ga, "ae_gmm": ae_gmm}[key](rows)
        result["algorithm"] = record["name"]
        return result
    if key in {"health_main_ensemble", "hi_linear"}:
        if not dataset.file.name.lower().endswith(".csv"):
            raise ValueError("寿命预测算法只接受 CSV 数据集")
        from django.test import RequestFactory
        from rul_service.views import predict
        payload = {**parameters, "algorithm": key, "dataset_id": dataset.pk}
        request = RequestFactory().post("/api/v1/rul/predict/", data=json.dumps(payload), content_type="application/json")
        response = predict(request)
        result = json.loads(response.content)
        if response.status_code != 200:
            raise ValueError(result.get("message", "寿命预测失败"))
        return result
    raise ValueError(f"未实现内置算法 {key}")


def _run_one(record, dataset_id, parameters):
    dataset = Dataset.objects.get(pk=dataset_id)
    if not dataset.file:
        raise ValueError("数据集没有文件")
    if record["source"] == "plugin":
        result = run_plugin(record, dataset.file.path, parameters)
        if record["category"] == "diagnosis":
            from fault_diagnosis.views import _standardize_result
            from datasets.batch_processing import inspect_file
            result = _standardize_result(result, inspect_file(dataset.file.path))
    else:
        result = _run_builtin(record, dataset, validate_parameters(record["parameters"], parameters))
    json.dumps(result, allow_nan=False)
    return {"dataset_id": dataset.pk, "algorithm": record["key"], "category": record["category"], "status": "success", "result": result}


@csrf_protect
def algorithm_run(request, key):
    denied = _access(request, "run_analysis")
    if denied:
        return denied
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "仅支持 POST"}, status=405)
    try:
        record = get_algorithm(key)
        body = json.loads(request.body.decode("utf-8") or "{}")
        if not isinstance(body, dict):
            raise ValueError("请求体必须是 JSON 对象")
        dataset_id = body.get("dataset_id")
        if dataset_id is None:
            raise ValueError("请提供 dataset_id")
        result = _run_one(record, dataset_id, body.get("parameters") or {})
        return JsonResponse({"ok": True, **result})
    except Dataset.DoesNotExist:
        return JsonResponse({"ok": False, "error": "数据集不存在"}, status=404)
    except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({"ok": False, "error": f"算法运行失败: {type(exc).__name__}: {exc}"}, status=500)


@csrf_protect
def algorithm_batch_run(request, key):
    denied = _access(request, "run_analysis")
    if denied:
        return denied
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "仅支持 POST"}, status=405)
    try:
        record = get_algorithm(key)
        body = json.loads(request.body.decode("utf-8") or "{}")
        if not isinstance(body, dict):
            raise ValueError("请求体必须是 JSON 对象")
        ids = body.get("dataset_ids")
        if not isinstance(ids, list) or not 1 <= len(ids) <= 100:
            raise ValueError("dataset_ids 必须包含 1 到 100 个数据集编号")
        parameters = body.get("parameters") or {}
        results = []
        for dataset_id in ids:
            try:
                results.append(_run_one(record, dataset_id, parameters))
            except Exception as exc:
                results.append({"dataset_id": dataset_id, "status": "failed", "error": str(exc)})
        return JsonResponse({"ok": True, "algorithm": key, "total": len(results), "success": sum(item["status"] == "success" for item in results), "failed": sum(item["status"] == "failed" for item in results), "results": results})
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
