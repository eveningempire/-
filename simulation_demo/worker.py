"""Run blocking MATLAB work outside the HTTP request process."""
import subprocess
import sys

from django.conf import settings
from django.utils import timezone

from .models import FaultWorkflowTask
from .simulink import output_dir, run_task


def enqueue_task(task):
    claimed = FaultWorkflowTask.objects.filter(pk=task.pk, status__in=["ready", "failed", "created"]).update(
        status="queued", current_stage="queued", latest_result={}, updated_at=timezone.now())
    if not claimed:
        return False
    try:
        directory = output_dir(task)
        directory.mkdir(parents=True, exist_ok=True)
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        with (directory / "worker.log").open("ab") as log:
            subprocess.Popen(
                [sys.executable, str(settings.BASE_DIR / "manage.py"), "run_simulink_task", str(task.id)],
                cwd=str(settings.BASE_DIR), stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                creationflags=flags, close_fds=True,
            )
    except Exception as exc:
        FaultWorkflowTask.objects.filter(pk=task.pk, status="queued").update(
            status="failed", current_stage="failed", latest_result={"error": str(exc)}, updated_at=timezone.now())
        raise
    return True


def execute_task(task_id):
    claimed = FaultWorkflowTask.objects.filter(pk=task_id, status="queued", simulation_backend__in=["simulink", "project_archive", "python_proxy"]).update(
        status="running", current_stage="preparing", updated_at=timezone.now())
    if not claimed:
        return False
    task = FaultWorkflowTask.objects.get(pk=task_id)

    def stage(name):
        FaultWorkflowTask.objects.filter(pk=task_id).update(current_stage=name, updated_at=timezone.now())

    try:
        if task.simulation_backend == "project_archive":
            from .project_archive import run_task as import_archive
            import_archive(task, on_stage=stage)
        elif task.simulation_backend == "python_proxy":
            from .python_proxy import run_task as run_proxy
            run_proxy(task, on_stage=stage)
        else:
            run_task(task, on_stage=stage)
    except Exception as exc:
        FaultWorkflowTask.objects.filter(pk=task_id).update(
            status="failed", current_stage="failed", latest_result={"error": str(exc)}, updated_at=timezone.now())
        raise
    return True
