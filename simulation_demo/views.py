import csv, io, json, math
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datasets.models import Dataset
from .models import FaultWorkflowEvent, FaultWorkflowTask

FAULTS={"动力":{"泄漏":"pressure","泵效率下降":"temperature"},"电源":{"母线欠压":"bus_voltage","电池容量衰减":"battery_capacity"},"控制":{"传感器偏置":"attitude_error","执行器迟滞":"control_error"}}
NOMINAL={"pressure":1.0,"temperature":.4,"bus_voltage":1.0,"battery_capacity":1.0,"attitude_error":0.0,"control_error":.02}
THRESHOLDS={"pressure":.12,"temperature":.12,"bus_voltage":.10,"battery_capacity":.10,"attitude_error":.08,"control_error":.09}
AMPLITUDES={"pressure":.35,"temperature":.3,"bus_voltage":.3,"battery_capacity":.25,"attitude_error":.25,"control_error":.25}

def _series(fault=None,count=120):
 rows=[]; fault=fault or {}; start=int(fault.get("start",40)); severity=float(fault.get("severity",.6)); mode=fault.get("mode","泄漏")
 for i in range(count):
  row={"time":i,"pressure":1+.015*math.sin(i/5),"temperature":.4+.02*math.sin(i/8),"bus_voltage":1+.008*math.sin(i/9),"battery_capacity":1-.0002*i,"attitude_error":.01*math.sin(i/6),"control_error":.02*math.cos(i/7)}
  if fault and i>=start:
   p=(i-start+1)/max(1,count-start)
   if mode=="泄漏": row["pressure"]-=severity*.65*p
   elif mode=="泵效率下降": row["temperature"]+=severity*.55*p
   elif mode=="母线欠压": row["bus_voltage"]-=severity*.5*p
   elif mode=="电池容量衰减": row["battery_capacity"]-=severity*.45*p
   elif mode=="传感器偏置": row["attitude_error"]+=severity*.4
   else: row["control_error"]+=severity*.45*p
  d=(abs(row["pressure"]-1)/.6+abs(row["temperature"]-.4)/.6+abs(row["bus_voltage"]-1)/.5+abs(row["battery_capacity"]-1)/.5+abs(row["attitude_error"])/.45+abs(row["control_error"]-.02)/.45)/6
  row["HI_norm"]=max(0,min(1,1-d)); rows.append({k:round(v,5) if isinstance(v,float) else v for k,v in row.items()})
 return rows

def _analyse(task,row,injected):
 signal=FAULTS[task.subsystem][task.fault_mode]; deviation=abs(float(row[signal])-NOMINAL[signal]); alarm=injected and deviation>=THRESHOLDS[signal]
 isolation={"泄漏":"推进剂供给与压力链路","泵效率下降":"动力泵及温控链路","母线欠压":"主电源母线与配电链路","电池容量衰减":"蓄电池组与充放电链路","传感器偏置":"姿态传感器链路","执行器迟滞":"控制执行机构"}[task.fault_mode]
 hi=float(row["HI_norm"]); rul=round(max(0,(hi-.2)/max(.001,task.severity*.01)),2) if alarm else None
 return {"injected":injected,"alarm":{"triggered":alarm,"signal":signal,"value":row[signal],"severity":task.severity},"diagnosis":{"fault":task.fault_mode if alarm else "正常","subsystem":task.subsystem,"confidence":round(min(.99,.55+deviation),3) if alarm else 0},"isolation":{"target":isolation if alarm else None,"status":"isolated" if alarm else "normal"},"health":{"component_hi":hi,"status":"degraded" if alarm else "healthy"},"rul":{"value":rul,"unit":"sample_interval","status":"estimated" if alarm else "not_triggered"},"notification":{"published":alarm,"topic":"fault.workflow","message":f"{task.subsystem}-{task.fault_mode} 已诊断并隔离" if alarm else "运行正常"}}

def _task(task): return {"id":str(task.id),"name":task.name,"mode":task.mode,"subsystem":task.subsystem,"fault_mode":task.fault_mode,"severity":task.severity,"injection_time":task.injection_time,"status":task.status,"current_stage":task.current_stage,"dataset_id":task.dataset_id,"latest_result":task.latest_result}
def sample(request): return JsonResponse({"ok":True,"subsystems":{k:list(v) for k,v in FAULTS.items()},"data":_series()})

@csrf_exempt
def workflows(request):
 if request.method=="GET": return JsonResponse({"ok":True,"results":[_task(x) for x in FaultWorkflowTask.objects.order_by("-created_at")[:100]]})
 try:
  b=json.loads(request.body or "{}"); t=FaultWorkflowTask.objects.create(name=b.get("name") or "故障注入任务",mode=b.get("mode","offline"),subsystem=b.get("subsystem","动力"),fault_mode=b.get("fault_mode","泄漏"),severity=float(b.get("severity",.6)),injection_time=float(b.get("injection_time",40)),status="ready",current_stage="ready"); return JsonResponse({"ok":True,"task":_task(t)},status=201)
 except Exception as e: return JsonResponse({"ok":False,"error":str(e)},status=400)

@csrf_exempt
def workflow_generate(request,task_id):
 try:
  t=FaultWorkflowTask.objects.get(pk=task_id); rows=_series({"subsystem":t.subsystem,"mode":t.fault_mode,"severity":t.severity,"start":t.injection_time}); out=io.StringIO(); w=csv.DictWriter(out,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
  d=Dataset(name=t.name,source="simulation",fault_type=t.fault_mode,injection_time=t.injection_time,degradation=t.severity,system=t.subsystem); d.file.save(f"fault-workflow-{t.id}.csv",ContentFile(out.getvalue().encode()),save=True)
  t.dataset_id=d.id;t.status="completed";t.current_stage="published";t.latest_result=_analyse(t,rows[-1],True);t.save();return JsonResponse({"ok":True,"task":_task(t),"dataset_id":d.id,"preview":rows[-20:],"result":t.latest_result})
 except Exception as e:return JsonResponse({"ok":False,"error":str(e)},status=400)

@csrf_exempt
def workflow_sample(request,task_id):
 try:
  t=FaultWorkflowTask.objects.get(pk=task_id);b=json.loads(request.body or "{}");seq=t.events.count()+1;ts=float(b.get("timestamp",seq-1));values=dict(b.get("values") or {});cleared=bool(b.get("clear_fault",False));injected=ts>=t.injection_time and not cleared
  if injected:
   signal=FAULTS[t.subsystem][t.fault_mode];direction=-1 if t.fault_mode in ("泄漏","母线欠压","电池容量衰减") else 1;values[signal]=float(values.get(signal,NOMINAL[signal]))+direction*t.severity*AMPLITUDES[signal]
  row={"time":ts,**{k:float(values.get(k,v)) for k,v in NOMINAL.items()}};d=(abs(row["pressure"]-1)/.6+abs(row["temperature"]-.4)/.6+abs(row["bus_voltage"]-1)/.5+abs(row["battery_capacity"]-1)/.5+abs(row["attitude_error"])/.45+abs(row["control_error"]-.02)/.45)/6;row["HI_norm"]=max(0,min(1,1-d));result=_analyse(t,row,injected);stage="cleared" if cleared else "published" if result["alarm"]["triggered"] else "monitoring"
  if cleared: result["clearance"]={"cleared":True,"restored":True,"message":"故障已清除，信号恢复正常监测范围"}
  event=FaultWorkflowEvent.objects.create(task=t,sequence=seq,timestamp=ts,stage=stage,event_type="fault_cleared" if cleared else "sample_processed",payload={"sample":row,"result":result});t.status="cleared" if cleared else "running";t.current_stage=stage;t.latest_result=result;t.save();return JsonResponse({"ok":True,"event":{"sequence":event.sequence,"timestamp":ts,"stage":stage,"sample":row,"result":result}})
 except Exception as e:return JsonResponse({"ok":False,"error":str(e)},status=400)

def workflow_detail(request,task_id):
 try:
  t=FaultWorkflowTask.objects.get(pk=task_id);after=int(request.GET.get("after",0));events=list(t.events.filter(sequence__gt=after).values("sequence","timestamp","stage","event_type","payload","created_at")[:500]);return JsonResponse({"ok":True,"task":_task(t),"events":events})
 except FaultWorkflowTask.DoesNotExist:return JsonResponse({"ok":False,"error":"任务不存在"},status=404)

@csrf_exempt
def run(request):
 if request.method!="POST":return JsonResponse({"ok":False,"error":"仅支持 POST"},status=405)
 b=json.loads(request.body or "{}");f=b.get("fault") or b;t=FaultWorkflowTask.objects.create(name=b.get("name") or "仿真故障数据集",mode="offline",subsystem=f.get("subsystem","动力"),fault_mode=f.get("mode","泄漏"),severity=float(f.get("severity",.6)),injection_time=float(f.get("start",40)),status="ready");return workflow_generate(request,t.id)
def task(request,task_id):return workflow_detail(request,task_id)
