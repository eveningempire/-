import json, math
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
def estimate(v,h=100):
 v=[max(0,min(1,float(x))) for x in v]; n=len(v); m=sum(v)/n; mx=(n-1)/2; den=sum((i-mx)**2 for i in range(n)) or 1; s=sum((i-mx)*(x-m) for i,x in enumerate(v))/den; rul=h if s>=0 else max(0,(v[-1]-.2)/-s); return {'status':'success','algorithm':'baseline_health_trend_rul_v1','development_only':True,'rul_value':round(rul,3),'confidence_interval':[round(max(0,rul*.7),3),round(rul*1.3,3)],'current_hi':v[-1],'slope_per_window':round(s,6),'hi_sequence':v,'degradation_trend':'degrading' if s<0 else 'stable_or_improving'}
@csrf_exempt
def predict(request):
 try:
  b=json.loads(request.body or b'{}'); v=b.get('hi_sequence',[]); return JsonResponse(estimate(v,int(b.get('horizon',100))))
 except Exception as e:return JsonResponse({'status':'error','message':str(e)},status=400)
def status(request):return JsonResponse({'available':True,'algorithm':'baseline_health_trend_rul_v1','development_only':True})

@csrf_exempt
def demo(request):
    values=[0.98,0.96,0.94,0.91,0.88,0.84,0.81,0.77,0.73,0.69,0.65,0.60]
    return JsonResponse({'source':'内置仿真演示数据','sample_count':len(values),'result':estimate(values)})
