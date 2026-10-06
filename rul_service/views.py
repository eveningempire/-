import json
import math
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

HEALTH_MAIN_COMPONENT_NAMES = {
    '1': '液氧泵', '2': '液氧涡轮', '3': '煤油管路', '4': '煤油阀门',
    '5': '燃气发生器', '6': '燃烧室', '7': '喷管', '8': 'TVC',
    '9': 'RCS', '10': '栅格舵', '11': '传感器', '12': '液氧管路',
    '13': '液氧阀门', '14': '煤油泵',
}


def _component_matches_dataset(dataset, component_id):
    """Validate a selected health-main model against an explicit PBS link.

    Legacy datasets without a PBS link remain runnable and are called out in
    the UI; an explicit but different link must not silently use another
    component's weights.
    """
    if not dataset.structure_node_id:
        return True
    expected = HEALTH_MAIN_COMPONENT_NAMES.get(str(component_id))
    if not expected:
        return True
    aliases = {'氧涡轮': '液氧涡轮'}
    actual = aliases.get((dataset.structure_node.name or '').strip(), (dataset.structure_node.name or '').strip())
    return actual == expected

def estimate(values, h=100, threshold=0.2):
    v = [float(x) for x in values]
    if len(v) < 3:
        raise ValueError("至少需要 3 个有效 HI 样本,请先提供 hi 或 health_index 列。")
    if any(not math.isfinite(x) or not 0 <= x <= 1 for x in v):
        raise ValueError("HI 必须为 0 到 1 的有限数值,不会自动裁剪或转换原始遥测。")
    if not 0 < threshold < 1 or not 1 <= h <= 10000:
        raise ValueError("阈值应在 0 与 1 之间,预测范围为 1 到 10000 个样本间隔。")
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
                  "当前趋势未下降,无法给出有限的阈值到达时间。" if rul is None else
                  f"按当前线性趋势,约 {rul:.1f} 个样本间隔后达到阈值。")
    return dict(status="success", algorithm="线性 HI 趋势外推", development_only=True,
                rul_value=None if rul is None else round(rul,3), confidence_interval=None,
                current_hi=v[-1], slope_per_window=slope, hi_sequence=v, fitted=fitted,
                forecast=forecast, threshold=threshold, r_squared=r2,
                degradation_trend="下降" if slope < -1e-10 else "平稳或上升",
                conclusion=conclusion, unit="sample_interval", unit_label="样本间隔",
                limitation="基线趋势估计,非训练 RUL 模型;没有校准置信区间。样本间隔不等于发射次数或小时。")

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
        if body.get("dataset_id"):
            from datasets.services import read_rows
            rows=read_rows(body["dataset_id"])
            keys=[k for k in rows[0] if k.strip().lower() in ("hi_norm","hi","health_index","health","健康指数")] if rows else []
            if not keys:
                raise ValueError("该 CSV 没有健康指数列(HI_norm / hi / health_index)。原始压力、温度和时间不能直接换算寿命;请先生成有依据的 HI 数据集。")
            values=[row[keys[0]] for row in rows]
        if algorithm == 'health_main_ensemble':
            component_id=str(body.get('component_id') or '14')
            asset_root=Path(__file__).resolve().parent.parent / 'integrations' / 'algorithm_assets' / 'models' / 'life'
            asset_dir=asset_root / component_id
            if not asset_dir.is_dir():
                raise ValueError(f'没有部件 {component_id} 的训练模型,可选 1 到 15')
            if body.get("dataset_id"):
                from datasets.models import Dataset
                dataset=Dataset.objects.get(pk=body["dataset_id"])
                if not _component_matches_dataset(dataset, component_id):
                    actual = dataset.structure_node.name if dataset.structure_node_id else '未关联'
                    expected = HEALTH_MAIN_COMPONENT_NAMES.get(component_id, f'模型 {component_id}')
                    raise ValueError(f'数据集已关联 PBS 部件“{actual}”,与所选寿命模型“{expected}”不一致;请先核对部件映射')
                from .health_main_adapter import predict as trained_predict
                result=trained_predict(dataset.file.path, asset_dir)
            else:
                raise ValueError('训练模型推理需要选择包含至少 51 行 HI 的数据集')
            result.update({'status':'success','unit':'h','unit_label':'小时 (h)','development_only':False,'threshold':float(body.get('threshold',.2)),'confidence_interval':None,'limitation':'采用项目组已训练的 health-main 集成模型;输出单位按交付模型定义为小时 (h)。'})
        elif algorithm == 'hi_linear':
            result=estimate(values, int(body.get("horizon",100)), float(body.get("threshold",.2)))
        else:
            raise ValueError('不支持的算法')
        result["dataset_id"]=body.get("dataset_id")
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
