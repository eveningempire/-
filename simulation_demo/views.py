import json, math, csv, io, uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from datasets.models import Dataset
TASKS={}

FAULTS = {
    '动力': {'泄漏': 'pressure', '泵效率下降': 'temperature'},
    '控制': {'传感器偏置': 'attitude_error', '执行器迟滞': 'control_error'},
}

def _series(fault=None, severity=0.5):
    rows=[]
    for i in range(60):
        t=i
        pressure=1.0+0.015*math.sin(i/5)
        temperature=0.4+0.02*math.sin(i/8)
        attitude_error=0.01*math.sin(i/6)
        control_error=0.02*math.cos(i/7)
        if fault:
            subsystem, mode = fault.get('subsystem','动力'), fault.get('mode','泄漏')
            s=max(0,min(1,float(fault.get('severity',severity))))
            start=int(fault.get('start',20))
            if i>=start:
                k=(i-start+1)/max(1,60-start)
                if subsystem=='动力' and mode=='泄漏': pressure-=s*0.55*k
                elif subsystem=='动力' and mode=='泵效率下降': temperature+=s*0.5*k
                elif subsystem=='控制' and mode=='传感器偏置': attitude_error+=s*0.4
                elif subsystem=='控制': control_error+=s*0.45*k
        # HI_norm is a transparent, reproducible health indicator derived from
        # deviation against the nominal operating point (1.0 MPa, 0.4 temp,
        # zero attitude error, 0.02 control error).  1 means healthy.
        deviation = (abs(pressure-1.0)/0.6 + abs(temperature-0.4)/0.6 +
                     abs(attitude_error)/0.45 + abs(control_error-0.02)/0.45) / 4
        hi_norm = max(0.0, min(1.0, 1.0-deviation))
        rows.append({'time':t,'pressure':round(pressure,5),'temperature':round(temperature,5),'attitude_error':round(attitude_error,5),'control_error':round(control_error,5),'HI_norm':round(hi_norm,5)})
    return rows

def sample(request):
    return JsonResponse({'ok':True,'subsystems':{k:list(v) for k,v in FAULTS.items()},'data':_series()})

@csrf_exempt
def run(request):
    if request.method!='POST': return JsonResponse({'ok':False,'error':'仅支持 POST'},status=405)
    try:
        body=json.loads(request.body or '{}'); fault=body.get('fault') or body; rows=_series(fault)
        task_id=str(uuid.uuid4()); TASKS[task_id]={'status':'running','adapter':'demo'}
        out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
        d=Dataset(name=body.get('name') or f"仿真-{task_id[:8]}",source='simulation',fault_type=fault.get('mode','正常'),injection_time=fault.get('start'),launch_number=body.get('launch_number'),degradation=fault.get('severity'),system=fault.get('subsystem',''),component=body.get('component',''))
        d.file.save(f'{task_id}.csv',ContentFile(out.getvalue().encode('utf-8')),save=True)
        # derive health index from disturbance magnitude
        last=rows[-1]; deviation=abs(last['pressure']-1)+abs(last['temperature']-.4)+abs(last['attitude_error'])+abs(last['control_error'])
        hi=max(0.05,min(1,1-deviation/1.2)); seq=[max(0.05,hi+(59-i)*0.002) for i in range(12)]
        alarm=deviation>0.12
        diagnosis={'status':'demo','alarm':alarm,'fault':fault.get('mode','正常'),'subsystem':fault.get('subsystem','正常'),'confidence':round(min(0.99,0.55+deviation),3)}
        TASKS[task_id].update(status='completed',dataset_id=d.id)
        return JsonResponse({'ok':True,'task_id':task_id,'dataset_id':d.id,'status':'completed','data':rows,'summary':{'sample_count':len(rows),'health_index':round(hi,4),'alarm':alarm},'diagnosis':diagnosis,'hi_sequence':seq})
    except Exception as e: return JsonResponse({'ok':False,'error':str(e)},status=400)

def task(request,task_id): return JsonResponse(TASKS.get(task_id,{'status':'unknown'}))
