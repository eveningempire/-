import json
import math
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def estimate(values, h=100, threshold=0.2, times=None):
    v = [float(x) for x in values]
    if len(v) < 3:
        raise ValueError("至少需要 3 个有效 HI 样本,请先提供 hi 或 health_index 列。")
    if any(not math.isfinite(x) or not 0 <= x <= 1 for x in v):
        raise ValueError("HI 必须为 0 到 1 的有限数值,不会自动裁剪或转换原始遥测。")
    if not 0 < threshold < 1 or not 1 <= h <= 10000:
        raise ValueError("阈值应在 0 与 1 之间,预测范围为 1 到 10000 个样本间隔。")
    n = len(v)
    axis = [float(x) for x in times] if times is not None else list(range(n))
    if len(axis) != n or any(not math.isfinite(x) for x in axis) or any(b <= a for a, b in zip(axis, axis[1:])):
        raise ValueError('HI 时间轴必须与样本等长且严格递增')
    mean = sum(v)/n
    center = sum(axis)/n
    slope = sum((t-center)*(x-mean) for t,x in zip(axis,v))/sum((t-center)**2 for t in axis)
    fitted = [mean+slope*(t-center) for t in axis]
    total = sum((x-mean)**2 for x in v)
    r2 = None if total == 0 else 1-sum((x-y)**2 for x,y in zip(v,fitted))/total
    rul = 0 if v[-1] <= threshold else ((v[-1]-threshold)/-slope if slope < -1e-10 else None)
    forecast = [v[-1]+slope*i for i in range(h+1)]
    conclusion = ("当前 HI 已达到设定阈值。" if rul == 0 else
                  "当前趋势未下降,无法给出有限的阈值到达时间。" if rul is None else
                  f"按当前线性趋势,约 {rul:.1f} {'秒' if times is not None else '个样本间隔'}后达到阈值。")
    return dict(status="success", algorithm="线性 HI 趋势外推", development_only=True,
                rul_value=None if rul is None else round(rul,3), confidence_interval=None,
                current_hi=v[-1], slope_per_window=slope, hi_sequence=v, fitted=fitted,
                forecast=forecast, forecast_times=[axis[-1]+i for i in range(h+1)], hi_times=axis,
                threshold=threshold, r_squared=r2,
                degradation_trend="下降" if slope < -1e-10 else "平稳或上升",
                conclusion=conclusion, unit="s" if times is not None else "sample_interval",
                unit_label="秒 (s)" if times is not None else "样本间隔",
                limitation="HI 线性趋势外推;没有校准置信区间,不代表经真实寿命验证的部件剩余寿命。")

@csrf_exempt
def predict(request):
    if request.method != "POST":
        return JsonResponse({"message":"仅支持 POST"}, status=405)
    try:
        body=json.loads(request.body or b'{}')
        algorithm=body.get('algorithm', 'health_main_ensemble')
        values=body.get("hi_sequence", [])
        dataset_ids = body.get('dataset_ids')
        if dataset_ids is not None:
            if not isinstance(dataset_ids, list) or not dataset_ids:
                raise ValueError('dataset_ids 必须是非空数组')
            if len(dataset_ids) > 100:
                raise ValueError('单次最多预测 100 个数据集,请分批提交')
            results = []
            for dataset_id in dataset_ids:
                try:
                    nested = dict(body)
                    nested.pop('dataset_ids', None)
                    nested['dataset_id'] = dataset_id
                    # Reuse the single-dataset path below without duplicating
                    # model adapter logic in a second endpoint.
                    from django.test import RequestFactory
                    nested_request = RequestFactory().post('/api/v1/rul/predict/', data=json.dumps(nested), content_type='application/json')
                    result = json.loads(predict(nested_request).content)
                    results.append({'dataset_id': dataset_id, 'status': result.get('status', 'error'), 'result': result})
                except Exception as exc:
                    results.append({'dataset_id': dataset_id, 'status': 'error', 'message': str(exc)})
            return JsonResponse({'status': 'success', 'batch': True, 'total': len(results), 'success': sum(x['status'] == 'success' for x in results), 'failed': sum(x['status'] == 'error' for x in results), 'results': results})
        dataset, prepared = None, None
        component_id=str(body.get('component_id') or '14')
        if component_id not in {str(value) for value in range(1, 16)}:
            raise ValueError('部件模型编号必须为 1 到 15')
        threshold = float(body.get('threshold', .2))
        if not math.isfinite(threshold) or not 0 < threshold < 1:
            raise ValueError('HI 阈值必须为 0 与 1 之间的有限数值')
        asset_root=Path(__file__).resolve().parent.parent / 'integrations' / 'algorithm_assets' / 'models' / 'life'
        asset_dir=asset_root / component_id
        if body.get("dataset_id"):
            from datasets.models import Dataset
            from .inputs import prepare
            dataset=Dataset.objects.select_related('structure_node').get(pk=body["dataset_id"])
            prepared=prepare(dataset, component_id, asset_dir)
            values=prepared['values']
        if algorithm == 'health_main_ensemble':
            if not asset_dir.is_dir():
                raise ValueError(f'没有部件 {component_id} 的训练模型,可选 1 到 15')
            if dataset is not None:
                from .health_main_adapter import predict as trained_predict
                result=trained_predict(dataset.file.path, asset_dir, prepared=prepared)
            else:
                raise ValueError('训练模型推理需要选择至少 51 个 HI 窗口的 HI 或 P 参数数据集')
            generated = prepared['source']['method'] == 'trained_pca'
            result.update({'status':'success','unit':'s','unit_label':'秒 (s)','development_only':generated,
                           'threshold':threshold,'threshold_used_by_model':False,
                           'confidence_interval':None,
                           'limitation':'采用交付 health-main 集成模型;RUL 标签由仿真失效时刻减 Time 构建,单位为秒。新仿真数据的真实寿命精度尚未标定。' +
                           ('HI 按训练 scaler/PCA 计算并裁剪到 [0,1];裁剪比例见输入来源,与原端点未裁剪的推理不同。' if generated else '')})
        elif algorithm == 'hi_linear':
            times = prepared['times'] if prepared and prepared['source']['time_column'] else None
            result=estimate(values, int(body.get("horizon",100)), threshold, times=times)
            if prepared:
                result['hi_source'] = prepared['source']
        else:
            raise ValueError('不支持的算法')
        result["dataset_id"]=body.get("dataset_id")
        result['component_id']=component_id
        result.setdefault('data_quality', {'sample_count': len(values), 'minimum_samples': 51 if algorithm == 'health_main_ensemble' else 3, 'status': 'valid' if len(values) >= (51 if algorithm == 'health_main_ensemble' else 3) else 'insufficient'})
        return JsonResponse(result)
    except Exception as exc:
        return JsonResponse({"status":"error","message":str(exc)},status=400)

def status(request):
    root = Path(__file__).resolve().parent.parent / "integrations" / "algorithm_assets" / "models" / "life"
    models = sorted(p.name for p in root.glob("*/ensemble.pkl"))
    try:
        import torch
        runtime={"available":True,"torch":torch.__version__}
    except Exception as exc:
        runtime={"available":False,"error":str(exc)}
    return JsonResponse({"available":bool(models),"algorithm":"health-main RUL 集成模型","models":models,"asset_root":str(root),"runtime":runtime})

@csrf_exempt
def demo(request):
    return JsonResponse({"source":"内置演示","result":estimate([.98,.96,.94,.91,.88,.84,.81,.77,.73,.69,.65,.60])})
