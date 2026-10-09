from __future__ import annotations

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .service import HealthAssessmentService, PlatformUnavailable

SUPPORTED_SYSTEMS = ('控制', '动力')


def _single_method(algorithm):
    from .algorithms import ae_gmm, cdpca_ga
    if algorithm in {'fusion', 'cdpca', 'cdpca_ga', 'feature_fusion'}:
        return cdpca_ga, 'CDPCA-GA 健康评估'
    if algorithm in {'ae', 'ae_gmm', 'aegmm'}:
        return ae_gmm, 'AE-GMM 健康评估'
    raise ValueError('单机级评估 algorithm 支持 cdpca_ga、ae_gmm')


def _evaluate_component(dataset_id, method, algorithm_name, component_id=None):
    from datasets.models import Dataset
    from datasets.services import read_rows
    from .references import assessment_reference
    dataset = Dataset.objects.select_related('structure_node').get(pk=dataset_id)
    if not dataset.file or not dataset.file.name.lower().endswith('.csv'):
        raise ValueError('健康评估只接受 CSV 数据集')
    result = method(read_rows(dataset_id), **assessment_reference(dataset))
    result.update({
        'dataset_id': dataset.pk,
        'component_id': component_id or (dataset.structure_node.node_key if dataset.structure_node_id else f'component_{dataset.pk}'),
        'structure_node_id': dataset.structure_node_id,
        'structure_node_name': dataset.structure_node.name if dataset.structure_node_id else None,
        'status': 'success', 'image_url': None, 'requested_algorithm': algorithm_name,
    })
    return result


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
        if not isinstance(record, dict):
            raise ValueError('请求体必须是 JSON 对象')
        algorithm = str(record.get('algorithm', 'cdpca_ga')).lower().replace('-', '_')
        is_system = algorithm in {'gcn', 'gcn_rbd', 'system'} or bool(record.get('dataset_ids'))
        if is_system:
            dataset_ids = record.get('dataset_ids')
            if not isinstance(dataset_ids, list) or not dataset_ids:
                raise ValueError('系统级评估必须先选择至少一个数据集')
        if record.get('dataset_id') or record.get('dataset_ids'):
            from datasets.models import Dataset
            from .algorithms import gcn_rbd

            ids = record.get('dataset_ids') or [record.get('dataset_id')]
            if algorithm in {'gcn', 'gcn_rbd', 'system'}:
                method, _ = _single_method('cdpca_ga')
                algorithm_name = 'GCN + RBD 系统健康评估'
            else:
                method, algorithm_name = _single_method(algorithm)
            if is_system:
                selected_systems = set(Dataset.objects.filter(pk__in=ids).values_list('system', flat=True))
                if len(selected_systems) != 1 or not selected_systems.issubset(SUPPORTED_SYSTEMS):
                    raise ValueError('系统级评估仅支持同一控制或动力系统的数据集')
                if record.get('system') is not None and record['system'] not in selected_systems:
                    raise ValueError('选择的系统与数据集不一致')

            component_results = []
            for index, dataset_id in enumerate(ids):
                component = str(record['component_ids'][index]) if isinstance(record.get('component_ids'), list) and index < len(record['component_ids']) else None
                component_results.append(_evaluate_component(dataset_id, method, algorithm_name, component))
            if not component_results:
                raise ValueError('数据集没有可评估的数值列')
            if is_system:
                result = gcn_rbd(component_results, [item['component_id'] for item in component_results])
                result['component_results'] = component_results
                # Keep the API display name aligned with the platform algorithm catalog.
                result['algorithm'] = 'GCN + RBD 系统健康评估'
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
def batch_evaluate(request):
    if request.method != 'POST':
        return _error('仅支持 POST', 405)
    try:
        body = _body(request)
        if not isinstance(body, dict):
            raise ValueError('请求体必须是 JSON 对象')
        ids = body.get('dataset_ids')
        if not isinstance(ids, list) or not 1 <= len(ids) <= 100:
            raise ValueError('dataset_ids 必须包含 1 到 100 个数据集编号')
        if any(type(dataset_id) is not int or dataset_id < 1 for dataset_id in ids):
            raise ValueError('数据集编号必须为正整数')
        algorithm = str(body.get('algorithm', 'cdpca_ga')).lower().replace('-', '_')
        method, algorithm_name = _single_method(algorithm)
        from datasets.models import Dataset
        results = []
        for dataset_id in dict.fromkeys(ids):
            try:
                result = _evaluate_component(dataset_id, method, algorithm_name)
                json.dumps(result, allow_nan=False)
                results.append({'dataset_id': dataset_id, 'status': 'success', 'result': result})
            except Dataset.DoesNotExist:
                results.append({'dataset_id': dataset_id, 'status': 'failed', 'error': '数据集不存在'})
            except Exception as exc:
                results.append({'dataset_id': dataset_id, 'status': 'failed', 'error': str(exc)})
        successful = sum(item['status'] == 'success' for item in results)
        return JsonResponse({'ok': True, 'algorithm': algorithm, 'total': len(results),
                             'success': successful, 'failed': len(results)-successful, 'results': results})
    except (ValueError, TypeError) as exc:
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
            raise ValueError("body 需要是 JSON 数组,或包含 lines 的对象")
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
