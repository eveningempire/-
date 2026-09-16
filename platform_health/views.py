from __future__ import annotations

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .service import HealthAssessmentService, PlatformUnavailable


def _body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"请求不是有效 JSON: {exc}") from exc


def _error(message, status=400):
    return JsonResponse({"ok": False, "error": message}, status=status)


def status(request):
    service = HealthAssessmentService.instance()
    return JsonResponse({
        "ok": True,
        "available": service.available,
        "bundle": str(service.bundle),
        "error": service.error,
        "runtime": service.runtime,
        "warnings": service.warnings,
        "input_kind": "upstream_window_evidence",
        "required_fields": ["run_id", "component_id", "window_index", "timestamp", "hi_cd", "hi_ae", "anomaly_score"],
        "mode": "INTEGRATION_READY_DEVELOPMENT" if service.available else "unavailable",
    })


@csrf_exempt
def evaluate(request):
    if request.method != "POST":
        return _error("仅支持 POST", 405)
    try:
        record = _body(request)
        algorithm = str(record.get('algorithm', 'cdpca_ga')).lower().replace('-', '_')
        if algorithm in {'gcn', 'gcn_rbd', 'system'}:
            dataset_ids = record.get('dataset_ids')
            if not isinstance(dataset_ids, list) or not dataset_ids:
                raise ValueError('系统级评估必须先选择至少一个数据集')
        if record.get('dataset_id') or record.get('dataset_ids'):
            from datasets.services import read_rows
            from .algorithms import ae_gmm, cdpca_ga, gcn_rbd

            ids = record.get('dataset_ids') or [record.get('dataset_id')]
            datasets_rows = [(dataset_id, read_rows(dataset_id)) for dataset_id in ids]
            if algorithm in {'fusion', 'cdpca', 'cdpca_ga', 'feature_fusion'}:
                method = cdpca_ga
                algorithm_name = 'CDPCA-GA'
            elif algorithm in {'ae', 'ae_gmm', 'aegmm'}:
                method = ae_gmm
                algorithm_name = 'AE-GMM'
            elif algorithm in {'gcn', 'gcn_rbd', 'system'}:
                method = cdpca_ga
                algorithm_name = 'GCN+RBD'
            else:
                raise ValueError('algorithm 支持 cdpca_ga、ae_gmm、gcn_rbd')

            component_results = []
            for index, (dataset_id, rows) in enumerate(datasets_rows):
                if not rows:
                    continue
                component = str(record.get('component_ids', [])[index]) if isinstance(record.get('component_ids'), list) and index < len(record.get('component_ids')) else f'component_{dataset_id}'
                item = method(rows)
                item['dataset_id'] = dataset_id
                item['component_id'] = component
                component_results.append(item)
            if not component_results:
                raise ValueError('数据集没有可评估的数值列')
            if record.get('dataset_ids') or algorithm in {'gcn', 'gcn_rbd', 'system'}:
                result = gcn_rbd(component_results, [item['component_id'] for item in component_results])
                result['component_results'] = component_results
            else:
                result = component_results[0]
            result.update({'status': 'success', 'image_url': None, 'requested_algorithm': algorithm_name})
        else:
            result = HealthAssessmentService.instance().require().process_record(record)
        return JsonResponse({"ok": True, "result": result})
    except PlatformUnavailable as exc:
        return _error(str(exc), 503)
    except Exception as exc:
        return _error(str(exc), 400)


@csrf_exempt
def batch(request):
    if request.method != "POST":
        return _error("仅支持 POST", 405)
    try:
        body = _body(request)
        lines = body.get("lines") if isinstance(body, dict) else body
        if isinstance(lines, str):
            lines = lines.splitlines()
        elif isinstance(lines, list):
            lines = [json.dumps(item, ensure_ascii=False) for item in lines]
        else:
            raise ValueError("body 需要是 JSON 数组，或包含 lines 的对象")
        service = HealthAssessmentService.instance()
        results = __import__("platform_adapter.core", fromlist=["process_jsonl"]).process_jsonl(
            lines, service.require()
        )
        return JsonResponse({"ok": True, "count": len(results), "results": results})
    except PlatformUnavailable as exc:
        return _error(str(exc), 503)
    except Exception as exc:
        return _error(str(exc), 400)


@csrf_exempt
def summary(request):
    if request.method != "POST":
        return _error("仅支持 POST", 405)
    try:
        body = _body(request)
        result = HealthAssessmentService.instance().require().session_summary(
            str(body.get("session_id", "default")), int(body.get("run_id", 0))
        )
        return JsonResponse({"ok": True, "result": result})
    except PlatformUnavailable as exc:
        return _error(str(exc), 503)
    except Exception as exc:
        return _error(str(exc), 400)


@csrf_exempt
def reset(request):
    if request.method != "POST":
        return _error("仅支持 POST", 405)
    try:
        body = _body(request)
        HealthAssessmentService.instance().require().reset(
            body.get("session_id"), body.get("run_id")
        )
        return JsonResponse({"ok": True})
    except PlatformUnavailable as exc:
        return _error(str(exc), 503)
    except Exception as exc:
        return _error(str(exc), 400)
