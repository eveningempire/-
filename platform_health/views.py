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
        "mode": "INTEGRATION_READY_DEVELOPMENT" if service.available else "unavailable",
    })


@csrf_exempt
def evaluate(request):
    if request.method != "POST":
        return _error("仅支持 POST", 405)
    try:
        record = _body(request)
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
