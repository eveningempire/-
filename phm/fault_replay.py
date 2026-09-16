import json
import math
import hashlib
import csv
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .models import FaultEvent, FaultReplay, TelemetrySession
from datasets.models import Dataset


ASSET_SCENARIOS = {
    "m1": ("磨损退化一级", "轴承与转动部件", "warning"),
    "m2": ("磨损退化二级", "轴承与转动部件", "warning"),
    "m3": ("磨损退化三级", "轴承与转动部件", "critical"),
    "r1": ("润滑退化一级", "润滑与摩擦副", "warning"),
    "r2": ("润滑退化二级", "润滑与摩擦副", "warning"),
    "r3": ("润滑退化三级", "润滑与摩擦副", "critical"),
    "z1": ("综合退化一级", "电机与控制链路", "warning"),
    "z2": ("综合退化二级", "电机与控制链路", "warning"),
    "z3": ("综合退化三级", "电机与控制链路", "critical"),
}


def _asset_directory():
    return Path(settings.BASE_DIR) / "frontend" / "public" / "simulation-data"


def _ensure_asset_events():
    """Import the bundled 500-point simulation curves once for fault replay."""
    directory = _asset_directory()
    if not directory.exists():
        return 0
    User = get_user_model()
    owner = User.objects.filter(is_superuser=True).order_by("id").first() or User.objects.order_by("id").first()
    if owner is None:
        owner = User.objects.create_user(username="simulation-assets", password=None)
    created = 0
    for path in sorted(directory.glob("plot_??_ds20.json")):
        code = path.stem.replace("plot_", "").replace("_ds20", "")
        if code not in ASSET_SCENARIOS:
            continue
        source_key = f"simulation-asset:{path.name}"
        if FaultEvent.objects.filter(diagnosis__source_key=source_key).exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        times, currents, voltages = payload.get("days_short", []), payload.get("I", []), payload.get("V", [])
        count = min(len(times), len(currents), len(voltages))
        if count < 2:
            continue
        name, target, severity = ASSET_SCENARIOS[code]
        normalized_times = [round(float(times[i]), 6) for i in range(count)]
        with transaction.atomic():
            session = TelemetrySession.objects.create(
                name=f"仿真资产 · {name}", created_by=owner,
                token_hash=hashlib.sha256(source_key.encode()).hexdigest(),
                columns=["time", "current", "voltage"],
            )
            session.samples.bulk_create([
                session.samples.model(session=session, values={
                    "time": normalized_times[i],
                    "current": round(float(currents[i]), 8),
                    "voltage": round(float(voltages[i]), 8),
                }) for i in range(count)
            ], batch_size=500)
            FaultEvent.objects.create(
                session=session, name=name, severity=severity, isolation_target=target,
                start_time=normalized_times[0], end_time=normalized_times[-1],
                diagnosis={"source_key": source_key, "source_file": path.name,
                           "source_csv": payload.get("csv") or path.name, "sample_count": count,
                           "downsample": payload.get("downsample", 20), "asset_code": code},
            )
            created += 1
    return created


def _ensure_dataset_events():
    """Expose data-management CSV datasets as replayable persisted events."""
    created = 0
    User = get_user_model()
    owner = User.objects.filter(is_superuser=True).order_by("id").first() or User.objects.order_by("id").first()
    if owner is None:
        owner = User.objects.create_user(username="dataset-assets", password=None)
    for dataset in Dataset.objects.exclude(file="").order_by("id"):
        source_key = f"dataset:{dataset.pk}"
        if FaultEvent.objects.filter(diagnosis__source_key=source_key).exists():
            continue
        try:
            with dataset.file.open("rb") as raw:
                import io
                with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
                    reader = csv.DictReader(text)
                    fields = reader.fieldnames or []
                    rows = list(reader)
            if not rows:
                continue
            time_field = next((f for f in fields if str(f).lower() in {"time", "timestamp", "t"}), None)
            columns = ["time"] + [f for f in fields if f != time_field]
            values = []
            for index, row in enumerate(rows):
                try:
                    time_value = float(row.get(time_field)) if time_field else float(index)
                except (TypeError, ValueError):
                    time_value = float(index)
                sample = {"time": time_value}
                for field in fields:
                    if field == time_field:
                        continue
                    try:
                        sample[field] = float(row[field])
                    except (TypeError, ValueError):
                        continue
                if len(sample) > 1:
                    values.append(sample)
            if len(values) < 2:
                continue
            with transaction.atomic():
                session = TelemetrySession.objects.create(
                    name=f"数据管理 · {dataset.name}", created_by=owner,
                    token_hash=hashlib.sha256(source_key.encode()).hexdigest(), columns=columns,
                )
                session.samples.bulk_create([
                    session.samples.model(session=session, values=item) for item in values
                ], batch_size=500)
                FaultEvent.objects.create(
                    session=session, name=dataset.name or f"数据集 {dataset.pk}",
                    severity="critical" if dataset.fault_type else "warning",
                    isolation_target=dataset.component or dataset.system or "",
                    start_time=values[0]["time"], end_time=values[-1]["time"],
                    diagnosis={"source_key": source_key, "dataset_id": dataset.pk,
                               "source_csv": dataset.name, "sample_count": len(values),
                               "system": dataset.system, "component": dataset.component,
                               "fault_type": dataset.fault_type},
                )
                created += 1
        except (OSError, UnicodeError, ValueError, csv.Error):
            continue
    return created


def _event(x):
    return {"id": str(x.id), "session_id": str(x.session_id), "alarm_id": x.alarm_id,
            "name": x.name, "severity": x.severity, "isolation_target": x.isolation_target,
            "start_time": x.start_time, "end_time": x.end_time, "diagnosis": x.diagnosis,
            "dataset_id": (x.diagnosis or {}).get("dataset_id"),
            "source_type": "data-management" if (x.diagnosis or {}).get("dataset_id") else "unknown",
            "created_at": x.created_at}


def _replay(x):
    return {"id": str(x.id), "event_id": str(x.event_id), "window_start": x.window_start,
            "window_end": x.window_end, "current_time": x.current_time,
            "speed": x.speed, "state": x.state, "updated_at": x.updated_at}


def _number(value, name):
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} 必须是有限数值") from exc
    if not math.isfinite(value):
        raise ValueError(f"{name} 必须是有限数值")
    return value


def _curve(event, start, end):
    rows = [sample.values for sample in event.session.samples.order_by("id")
            if isinstance(sample.values.get("time"), (int, float)) and start <= sample.values["time"] <= end]
    columns = event.session.columns or (list(rows[0]) if rows else [])
    series = {key: [[row["time"], row[key]] for row in rows if isinstance(row.get(key), (int, float))]
              for key in columns if key != "time"}
    return {"columns": columns, "rows": rows, "series": series, "count": len(rows)}


@csrf_exempt
def events(request):
    if request.method == "GET":
        try:
            _ensure_dataset_events()
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            # Existing dataset-backed events remain usable if an optional CSV is malformed.
            pass
        # Replay is deliberately limited to datasets registered in 数据管理.
        # This prevents bundled demo curves and realtime-only events from being
        # presented as project database replay sources.
        dataset_ids = set(str(value) for value in Dataset.objects.values_list("id", flat=True))
        query = FaultEvent.objects.select_related("session", "alarm").order_by("-created_at")
        query = [event for event in query if str((event.diagnosis or {}).get("dataset_id")) in dataset_ids]
        if request.GET.get("session_id"):
            query = [event for event in query if str(event.session_id) == request.GET["session_id"]]
        results = [_event(x) for x in query[:500]]
        return JsonResponse({"ok": True, "count": len(results), "results": results})
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "仅支持 GET/POST"}, status=405)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
        session = TelemetrySession.objects.get(pk=body["session_id"])
        start = _number(body["start_time"], "start_time")
        end = _number(body.get("end_time", start), "end_time")
        if end < start:
            raise ValueError("end_time 不能早于 start_time")
        event = FaultEvent.objects.create(session=session, name=body["name"],
            severity=body.get("severity", "warning"), isolation_target=body.get("isolation_target", ""),
            start_time=start, end_time=end, diagnosis=body.get("diagnosis", {}))
        return JsonResponse({"ok": True, "event": _event(event)}, status=201)
    except (KeyError, ValueError, TypeError, json.JSONDecodeError, TelemetrySession.DoesNotExist) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)


def event_detail(request, event_id):
    event = get_object_or_404(FaultEvent.objects.select_related("session", "alarm"), pk=event_id)
    try:
        start = _number(request.GET.get("start", event.start_time), "start")
        end = _number(request.GET.get("end", event.end_time if event.end_time is not None else event.start_time), "end")
        if end < start:
            raise ValueError("end 不能早于 start")
        return JsonResponse({"ok": True, "event": _event(event), "curve": _curve(event, start, end)})
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)


@csrf_exempt
def create_replay(request, event_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "仅支持 POST"}, status=405)
    event = get_object_or_404(FaultEvent, pk=event_id)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
        start = _number(body.get("start", event.start_time), "start")
        end = _number(body.get("end", event.end_time if event.end_time is not None else event.start_time), "end")
        speed = _number(body.get("speed", 1), "speed")
        if end < start or not 0.1 <= speed <= 100:
            raise ValueError("时间窗口无效，倍速必须在 0.1 到 100 之间")
        replay = FaultReplay.objects.create(event=event, window_start=start, window_end=end, current_time=start, speed=speed)
        return JsonResponse({"ok": True, "replay": _replay(replay), "curve": _curve(event, start, end)}, status=201)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)


@csrf_exempt
def replay_control(request, replay_id):
    replay = get_object_or_404(FaultReplay.objects.select_related("event__session"), pk=replay_id)
    if request.method == "GET":
        return JsonResponse({"ok": True, "replay": _replay(replay), "curve": _curve(replay.event, replay.window_start, replay.current_time)})
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "仅支持 GET/POST"}, status=405)
    try:
        body, action = json.loads(request.body.decode("utf-8") or "{}"), None
        action = body.get("action")
        if action == "play": replay.state = "playing"
        elif action == "pause": replay.state = "paused"
        elif action == "restart": replay.current_time, replay.state = replay.window_start, "paused"
        elif action == "seek": replay.current_time = min(replay.window_end, max(replay.window_start, _number(body.get("time"), "time")))
        elif action == "speed":
            speed = _number(body.get("speed"), "speed")
            if not 0.1 <= speed <= 100: raise ValueError("倍速必须在 0.1 到 100 之间")
            replay.speed = speed
        elif action == "tick":
            if replay.state == "playing":
                elapsed = _number(body.get("elapsed", 1), "elapsed")
                if elapsed < 0: raise ValueError("elapsed 不能为负数")
                replay.current_time = min(replay.window_end, replay.current_time + elapsed * replay.speed)
                if replay.current_time >= replay.window_end: replay.state = "finished"
        else: raise ValueError("action 支持 play、pause、restart、seek、speed、tick")
        replay.save()
        return JsonResponse({"ok": True, "replay": _replay(replay), "curve": _curve(replay.event, replay.window_start, replay.current_time)})
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
