import json
import math
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def estimate(values, h=100, threshold=0.2):
    v = [float(x) for x in values]
    if len(v) < 3:
        raise ValueError("至少需要 3 个有效 HI 样本，请先提供 hi 或 health_index 列。")
    if any(not math.isfinite(x) or not 0 <= x <= 1 for x in v):
        raise ValueError("HI 必须为 0 到 1 的有限数值，不会自动裁剪或转换原始遥测。")
    if not 0 < threshold < 1 or not 1 <= h <= 10000:
        raise ValueError("阈值应在 0 与 1 之间，预测范围为 1 到 10000 个样本间隔。")
    n = len(v)
    mean = sum(v)/n
    center = (n-1)/2
    slope = sum((i-center)*(x-mean) for i,x in enumerate(v))/sum((i-center)**2 for i in range(n))
    fitted = [mean+slope*(i-center) for i in range(n)]
    total = sum((x-mean)**2 for x in v)
    r2 = None if total == 0 else 1-sum((x-y)**2 for x,y in zip(v,fitted))/total
    rul = 0 if v[-1] <= threshold else ((v[-1]-threshold)/-slope if slope < -1e-10 else None)
    forecast = [v[-1]+slope*i for i in range(h+1)]
    conclusion = ("当前 HI 已达到设定阈值。" if rul == 0 else
                  "当前趋势未下降，无法给出有限的阈值到达时间。" if rul is None else
                  f"按当前线性趋势，约 {rul:.1f} 个样本间隔后达到阈值。")
    return dict(status="success", algorithm="线性 HI 趋势外推", development_only=True,
                rul_value=None if rul is None else round(rul,3), confidence_interval=None,
                current_hi=v[-1], slope_per_window=slope, hi_sequence=v, fitted=fitted,
                forecast=forecast, threshold=threshold, r_squared=r2,
                degradation_trend="下降" if slope < -1e-10 else "平稳或上升",
                conclusion=conclusion, unit="样本间隔",
                limitation="基线趋势估计，非训练 RUL 模型；没有校准置信区间。样本间隔不等于发射次数或小时。")

@csrf_exempt
def predict(request):
    if request.method != "POST":
        return JsonResponse({"message":"仅支持 POST"}, status=405)
    try:
        body=json.loads(request.body or b'{}')
        if body.get('algorithm', 'hi_linear') != 'hi_linear':
            raise ValueError('此接口当前支持 hi_linear；训练模型需先确认部件与 HI 预处理来源，不能仅凭 HI_norm 列名自动选用。')
        values=body.get("hi_sequence", [])
        if body.get("dataset_id"):
            from datasets.services import read_rows
            rows=read_rows(body["dataset_id"])
            keys=[k for k in rows[0] if k.strip().lower() in ("hi_norm","hi","health_index","health","健康指数")] if rows else []
            if not keys:
                raise ValueError("该 CSV 没有健康指数列（HI_norm / hi / health_index）。原始压力、温度和时间不能直接换算寿命；请先生成有依据的 HI 数据集。")
            values=[row[keys[0]] for row in rows]
        result=estimate(values, int(body.get("horizon",100)), float(body.get("threshold",.2)))
        result["dataset_id"]=body.get("dataset_id")
        return JsonResponse(result)
    except Exception as exc:
        return JsonResponse({"status":"error","message":str(exc)},status=400)

def status(request):
    root = Path(__file__).resolve().parent.parent / "integrations" / "algorithm_assets" / "rul" / "life"
    models = sorted(p.name for p in root.glob("*/ensemble.pkl"))
    return JsonResponse({"available":True,"algorithm":"health-main RUL 集成资产 + HI趋势基线","models":models,"asset_root":str(root)})

@csrf_exempt
def demo(request):
    return JsonResponse({"source":"内置演示","result":estimate([.98,.96,.94,.91,.88,.84,.81,.77,.73,.69,.65,.60])})
