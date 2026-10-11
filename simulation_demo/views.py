import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from phm_backend.permissions import has_permission
from .models import FaultWorkflowTask
from .simulink import fault_catalog, runtime_status, validate_parameters
from .worker import enqueue_task
from .project_archive import archive_status
from .python_proxy import proxy_status


def _access(request, permission="view"):
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "请先登录"}, status=401)
    if not has_permission(request.user, permission):
        return JsonResponse({"ok": False, "error": "没有提交仿真任务的权限"}, status=403)


def _task(task):
    return {"id": str(task.id), "name": task.name, "mode": task.mode,
            "subsystem": task.subsystem, "fault_mode": task.fault_mode,
            "injection_time": task.injection_time, "end_time": task.end_time,
            "flight_count": task.flight_count, "simulation_backend": task.simulation_backend,
            "status": task.status, "current_stage": task.current_stage,
            "dataset_id": task.dataset_id, "latest_result": task.latest_result,
            "simulation_output": task.simulation_output,
            "created_at": task.created_at, "updated_at": task.updated_at}


def _create(body):
    return FaultWorkflowTask.objects.create(**validate_parameters(body), status="ready", current_stage="ready")


@require_GET
def sample(request):
    denied = _access(request)
    if denied:
        return denied
    return JsonResponse({"ok": True, "subsystems": fault_catalog(), "runtime": runtime_status(), "proxy": proxy_status(), "archive": archive_status(),
                         "limits": {"duration": 480, "flight_count_min": 0, "flight_count_max": 20},
                         "can_submit": has_permission(request.user, "submit_simulation")})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def workflows(request):
    denied = _access(request, "view" if request.method == "GET" else "submit_simulation")
    if denied:
        return denied
    if request.method == "GET":
        tasks = FaultWorkflowTask.objects.order_by("-created_at")[:50]
        results = []
        for task in tasks:
            item = _task(task)
            item.pop("simulation_output")
            results.append(item)
        return JsonResponse({"ok": True, "results": results})
    try:
        task = _create(json.loads(request.body or "{}"))
        return JsonResponse({"ok": True, "task": _task(task)}, status=201)
    except (ValueError, TypeError, OverflowError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)


@csrf_exempt
@require_POST
def workflow_generate(request, task_id):
    denied = _access(request, "submit_simulation")
    if denied:
        return denied
    try:
        task = FaultWorkflowTask.objects.get(pk=task_id)
    except FaultWorkflowTask.DoesNotExist:
        return JsonResponse({"ok": False, "error": "任务不存在"}, status=404)
    if task.simulation_backend not in ("simulink", "project_archive", "python_proxy"):
        return JsonResponse({"ok": False, "error": "历史演示任务不能传入一院模型，请创建新任务"}, status=409)
    if task.status in ("queued", "running", "completed"):
        return JsonResponse({"ok": True, "task": _task(task)}, status=200 if task.status == "completed" else 202)
    runtime = (archive_status() if task.simulation_backend == "project_archive" else
               proxy_status() if task.simulation_backend == "python_proxy" else runtime_status())
    if not runtime["available"]:
        task.status = "failed"
        task.current_stage = "runtime_unavailable"
        task.latest_result = {"error": runtime["error"]}
        task.save(update_fields=["status", "current_stage", "latest_result", "updated_at"])
        return JsonResponse({"ok": False, "error": runtime["error"], "task": _task(task), "runtime": runtime}, status=503)
    try:
        enqueue_task(task)
    except Exception as exc:
        task.refresh_from_db()
        return JsonResponse({"ok": False, "error": str(exc), "task": _task(task)}, status=503)
    task.refresh_from_db()
    return JsonResponse({"ok": True, "task": _task(task)}, status=202)


@csrf_exempt
@require_POST
def workflow_sample(request, task_id):
    denied = _access(request, "submit_simulation")
    if denied:
        return denied
    return JsonResponse({"ok": False, "error": "仿真结果由 Simulink 求解生成，请使用 generate 接口启动任务"}, status=409)


@require_GET
def workflow_detail(request, task_id):
    denied = _access(request)
    if denied:
        return denied
    try:
        task = FaultWorkflowTask.objects.get(pk=task_id)
        after = max(0, int(request.GET.get("after", 0)))
    except (FaultWorkflowTask.DoesNotExist, ValueError):
        return JsonResponse({"ok": False, "error": "任务不存在或参数无效"}, status=404)
    events = list(task.events.filter(sequence__gt=after).values(
        "sequence", "timestamp", "stage", "event_type", "payload", "created_at")[:500])
    return JsonResponse({"ok": True, "task": _task(task), "events": events})


@csrf_exempt
@require_POST
def run(request):
    denied = _access(request, "submit_simulation")
    if denied:
        return denied
    try:
        body = json.loads(request.body or "{}")
        if isinstance(body, dict) and "fault" in body:
            fault = body["fault"]
            if not isinstance(fault, dict):
                raise ValueError("fault 必须包含子系统、故障类型和注入时间")
            body = {**body, **fault}
            if "mode" in fault:
                body["fault_mode"] = fault["mode"]
                body["mode"] = "offline"
            if "start" in fault:
                body["injection_time"] = fault["start"]
            if "end" in fault:
                body["end_time"] = fault["end"]
        task = _create(body)
    except (ValueError, TypeError, OverflowError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    return workflow_generate(request, task.id)


def task(request, task_id):
    return workflow_detail(request, task_id)


@csrf_exempt
@require_POST
def configure_matlab(request):
    denied = _access(request, 'manage_structure')
    if denied:
        return denied
    try:
        from .matlab_runtime import save_root
        body = json.loads(request.body or '{}')
        save_root(body.get('matlab_root'))
        return JsonResponse({'ok': True, 'runtime': runtime_status()})
    except (ValueError, TypeError, OSError) as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
