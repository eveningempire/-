import json
import math
from statistics import mean

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import AcceptanceTelemetry, ReleaseAssessment


DEFAULT_WEIGHTS = {"动力": 0.32, "电源": 0.26, "测控": 0.16, "导航制导与控制": 0.16, "结构": 0.10}


def _finite01(value, name):
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{name} 必须是 0 到 1 的有限数值")
    return value


def _normalise_weights(health, requested):
    raw = {key: float(requested.get(key, DEFAULT_WEIGHTS.get(key, 1.0))) for key in health}
    if any(not math.isfinite(value) or value <= 0 for value in raw.values()):
        raise ValueError("子系统权重必须为正有限数值")
    total = sum(raw.values())
    return {key: value / total for key, value in raw.items()}


def assess(payload):
    health = {str(key): _finite01(value, f"{key}健康指数") for key, value in (payload.get("subsystem_health") or {}).items()}
    if len(health) < 2:
        raise ValueError("至少需要两个子系统健康指数")
    weights = _normalise_weights(health, payload.get("subsystem_weights") or {})
    threshold = _finite01(payload.get("release_threshold", 0.85), "放行阈值")
    minimum_hi = _finite01(payload.get("minimum_subsystem_hi", 0.65), "子系统最低阈值")
    weighted_hi = sum(health[key] * weights[key] for key in health)
    rbd = math.prod(max(value, 1e-9) for value in health.values())
    rbd_equivalent = rbd ** (1 / len(health))
    system_hi = 0.65 * weighted_hi + 0.35 * rbd_equivalent
    alarm_count = max(0, int(payload.get("open_critical_alarms", 0)))
    anomaly_penalty = min(0.25, alarm_count * 0.05)
    rul_margin = _finite01(payload.get("rul_margin", 1.0), "寿命裕度")
    model_result = None
    model_error = None
    try:
        from .trained_release_adapter import predict
        power_health = health.get("动力", weighted_hi)
        control_values = [value for key, value in health.items() if key != "动力"]
        control_health = sum(control_values) / len(control_values) if control_values else weighted_hi
        model_result = predict(power_health, control_health)
        # System health is the primary engineering baseline.  The trained RF
        # contributes supporting evidence after its 0-100 input scale is
        # restored; an uncalibrated VAE-GAN score may not veto release alone.
        fused_probability = 0.75 * system_hi + 0.25 * model_result["rf_probability"]
        success_probability = max(0.0, min(1.0, fused_probability * (0.8 + 0.2 * rul_margin) - anomaly_penalty))
    except Exception as exc:
        model_error = str(exc)
        success_probability = max(0.0, min(1.0, system_hi * (0.8 + 0.2 * rul_margin) - anomaly_penalty))
    blockers = [f"{key}健康指数 {value:.3f} 低于下限 {minimum_hi:.3f}" for key, value in health.items() if value < minimum_hi]
    if alarm_count:
        blockers.append(f"存在 {alarm_count} 条未关闭严重告警")
    if success_probability < threshold:
        blockers.append(f"任务成功概率 {success_probability:.3f} 低于放行阈值 {threshold:.3f}")
    decision = "release" if not blockers else "hold"
    return {
        "subsystem_health": health,
        "subsystem_weights": {key: round(value, 6) for key, value in weights.items()},
        "weighted_health_index": round(weighted_hi, 6),
        "rbd_equivalent_health": round(rbd_equivalent, 6),
        "system_health_index": round(system_hi, 6),
        "mission_success_probability": round(success_probability, 6),
        "release_threshold": threshold, "minimum_subsystem_hi": minimum_hi,
        "decision": decision, "decision_label": "建议放行" if decision == "release" else "暂缓放行",
        "blockers": blockers,
        "algorithm_trace": {"health_fusion": "75% RBD/weighted system health + 25% calibrated-scale RF", "weight_strategy": "project baseline / operator supplied normalized weights", "reflight_model": model_result["model"] if model_result else "deterministic fallback", "vae_gan_status": "evidence_only_uncalibrated" if model_result else "runtime_fallback", "model_result": model_result, "model_error": model_error, "safety_note": "VAE-GAN缺少训练期Scaler，仅显示辅助证据；最终放行须由授权人员签署"},
    }


def _item(row):
    return {"id": str(row.id), "vehicle_id": row.vehicle_id, "mission_name": row.mission_name, "subsystem_health": row.subsystem_health, "subsystem_weights": row.subsystem_weights, "system_health_index": row.system_health_index, "mission_success_probability": row.mission_success_probability, "release_threshold": row.release_threshold, "decision": row.decision, "decision_label": "建议放行" if row.decision == "release" else "暂缓放行", "blockers": row.blockers, "algorithm_trace": row.algorithm_trace, "created_by": row.created_by, "created_at": row.created_at.isoformat()}


@csrf_exempt
def assessments(request):
    if request.method == "GET":
        return JsonResponse({"ok": True, "results": [_item(row) for row in ReleaseAssessment.objects.all()[:100]]})
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "仅支持 GET/POST"}, status=405)
    try:
        body = json.loads(request.body or b"{}")
        result = assess(body)
        row = ReleaseAssessment.objects.create(vehicle_id=str(body.get("vehicle_id") or "RLV-DEMO-01"), mission_name=str(body.get("mission_name") or "发射场放行评估"), subsystem_health=result["subsystem_health"], subsystem_weights=result["subsystem_weights"], system_health_index=result["system_health_index"], mission_success_probability=result["mission_success_probability"], release_threshold=result["release_threshold"], decision=result["decision"], blockers=result["blockers"], algorithm_trace=result["algorithm_trace"], created_by=getattr(getattr(request, "user", None), "username", ""))
        return JsonResponse({"ok": True, "assessment": {**_item(row), **result}}, status=201)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)


def metrics(request):
    telemetry = list(AcceptanceTelemetry.objects.values("anomaly_fields", "health_index"))
    releases = list(ReleaseAssessment.objects.values("decision", "mission_success_probability"))
    total = len(telemetry); alarm_count = sum(bool(row["anomaly_fields"]) for row in telemetry)
    return JsonResponse({"ok": True, "metrics": {"telemetry_samples": total, "alarm_samples": alarm_count, "alarm_rate": round(alarm_count / total, 6) if total else None, "average_health_index": round(mean(row["health_index"] for row in telemetry), 6) if total else None, "release_assessments": len(releases), "release_rate": round(sum(row["decision"] == "release" for row in releases) / len(releases), 6) if releases else None, "average_success_probability": round(mean(row["mission_success_probability"] for row in releases), 6) if releases else None, "performance_targets": {"startup_seconds": 60, "refresh_latency_seconds": 1}, "acceptance_note": "诊断率、虚警率、平均诊断时间和RUL准确率需在标注试验集上计算；无样本时不伪造数值。"}})


def model_catalog(request):
    from .trained_release_adapter import asset_status
    reflight = asset_status()
    return JsonResponse({"ok": True, "models": [
        {"id": "msfg-teams", "name": "MSFG + TEAMS-RT", "domain": "故障诊断", "status": "trained", "version": "1.0", "evidence": "已接入统一诊断接口，输出D矩阵、诊断集合与测点证据", "deployable": True},
        {"id": "pca-iforest", "name": "PCA–iForest", "domain": "异常诊断", "status": "trained", "version": "route-1.0", "evidence": "已接入统一诊断接口，基于基准窗口在线拟合PCA与Isolation Forest", "deployable": True},
        {"id": "ae-gmm", "name": "Autoencoder–GMM", "domain": "健康评估", "status": "development", "version": "1.0", "evidence": "platform_health.algorithms", "deployable": True},
        {"id": "gcn-rbd", "name": "GNN/GCN + RBD", "domain": "系统健康", "status": "development", "version": "1.0", "evidence": "platform_health.algorithms", "deployable": True},
        {"id": "health-main-rul", "name": "CNN/BiRNN/BiLSTM/BiGRU/SRNN + RF/Ada", "domain": "寿命预测", "status": "trained", "version": "health-main", "evidence": "15组训练权重、超参数、PCA/Scaler与集成器", "deployable": True},
        {"id": "vae-gan-reflight", "name": "VAE-GAN + RF 再飞预测", "domain": "再飞评估", "status": "trained" if reflight["assets_present"] else "missing_assets", "version": "health-main", "evidence": "编码器、解码器、判别器及RF分类器；运行环境：" + ("就绪" if reflight["runtime_available"] else "待安装PyTorch"), "deployable": reflight["assets_present"] and reflight["runtime_available"]},
    ]})
