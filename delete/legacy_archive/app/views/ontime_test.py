import json
import time
import numpy as np
import pandas as pd
from flask import Blueprint, render_template, request, jsonify
from app import redis_engine
from app.config import ROAMING_DIR, FILL_MAX, WASH_ABS, TIME_RESAMPLE, WORKER_NUM
from lib.algoModule.detectAlgo.detector import wholeDetector
from lib.flaskModule.msfgModule import utils as msfg_util

# 创建蓝图
ontime_test_bp = Blueprint('ontime_test', __name__)

@ontime_test_bp.route('/ontime-test', methods=['GET', 'POST'])
def analyse_panel_init():
    return render_template("result-display.html")
@ontime_test_bp.route('/ontime-test1', methods=['GET', 'POST'])
def analyse_panel_init1():
    return render_template("result-display1.html")


@ontime_test_bp.route('/ontime-test/init-msfg-panel', methods=['GET', 'POST'])
def analyse_panel_msfg_init():
    obj = 'cmg'
    msfgConfig = json.loads(redis_engine.hget(obj, "msfg-config") or "{}").get("struct", [])
    return json.dumps(msfgConfig).replace("NaN", "null")

@ontime_test_bp.route('/ontime-test/analyse-data', methods=['GET', 'POST'])
def detect_process():  # 点击"获取结果"执行的诊断过程
    time_start = time.time()
    obj = 'cmg'
    instname = request.form.get("instname")
    editor = request.form.get("editor")
    faultNames = json.loads(redis_engine.hget(obj, "fault-name-config") or "{}")
    
    components = {k:k for k in json.loads(redis_engine.hget(obj, "components") or "{}")}
    ruleConfigs = {
        "detectType": "rule",
        "params": json.loads(redis_engine.hget(obj, "rule-config") or "[]"),
        "fnameMap": {k: v["name"] for k, v in faultNames.items()}
    }
    mlConfig = json.loads(redis_engine.hget(obj, "ml-config") or "[]")
    msfgConfig = msfg_util.from_json(redis_engine.hget(obj, "msfg-config") or "{}")
    
    # 创建核心数据诊断器。创建该诊断器时，仅使用了[配置的专家规则、数据驱动（各组件及其对应算法）]、多信号流图、创建进程数量上限、roaming文件夹路径
    wdr = wholeDetector([ruleConfigs, *[{**itm, "detectType": "ml", "component": f"{obj}@{itm.get('component', 'Unknown')}"} for itm in mlConfig]], msfgConfig, worker_num=WORKER_NUM, roaming_dir=ROAMING_DIR)
    
    # 读取数据并进行简单处理
    try:
        data = pd.read_csv(request.files.get("dataFile"), index_col=None, header=0, encoding="gbk", parse_dates=True, na_values=["--"]).fillna(method="ffill", limit=FILL_MAX).dropna(how="any", axis=0)
    except:
        try:
            request.files.get("dataFile").seek(0)
            data = pd.read_csv(request.files.get("dataFile"), index_col=None, header=0, parse_dates=True, na_values=["--"]).fillna(method="ffill", limit=FILL_MAX).dropna(how="any", axis=0)
        except:
            try:
                request.files.get("dataFile").seek(0)
                data = pd.read_csv(request.files.get("dataFile"), index_col=None, header=0, encoding="gbk", parse_dates=True, na_values=["--"]).fillna(method="ffill", limit=FILL_MAX).dropna(how="any", axis=0)
            except:
                request.files.get("dataFile").seek(0)
                data = pd.read_csv(request.files.get("dataFile"), index_col=None, header=0, parse_dates=True, na_values=["--"]).fillna(method="ffill", limit=FILL_MAX).dropna(how="any", axis=0)
    
    data.loc[:,:] = np.where(np.abs(data)<WASH_ABS, data, float("nan"))
    
    try:
        data = data  # .resample(f"{TIME_RESAMPLE}S").first()
    except Exception as e:
        data.index = np.round(data.index.values*1000000000*TIME_RESAMPLE).astype("int64")
        data.index = pd.to_datetime(data.index)
        data = data  # .resample(f"{TIME_RESAMPLE}S").first()
    
    # 引用数据诊断器自带的方法来获取当前数据的诊断结果
    res = wdr.offlineValidate(data)
    res["detectInfo"]["rule"] = [
        {**itm, "component": itm.get("component") or faultNames.get(itm["fuid"])}
        for itm in res["detectInfo"]["rule"]]
    res["compMap"] = components
    time_end = time.time()

    print('故障诊断时间', time_end-time_start)
    res["costtime"] = time_end-time_start

    # 确保有默认的数据结构
    if "detectInfo" not in res:
        res["detectInfo"] = {"rule": [], "ml": []}
    if "rule" not in res["detectInfo"]:
        res["detectInfo"]["rule"] = []
    
    resJson = json.dumps(res).replace("NaN", "null")
    
    # 更新 result222
    result222_data = {
        "state": res["state"] or 0,
        "detectInfo": res["detectInfo"],
        "costtime": res["costtime"]
    }
    redis_engine.hset(obj, "result222", json.dumps(result222_data).replace("NaN", "null"))
    
    # 更新原有的存储在Redis中的诊断结果
    redis_engine.hset(f"{obj}#{instname}", "result", resJson)
    resInst = {info["name"]: info for info in json.loads(redis_engine.hget(obj, "resultAll") or "[]")}
    
    if instname in resInst.keys():
        resInst[instname]["state"] = res["state"] or 0
        resInst[instname]["state_dd"] = res["state_dd"] or 0
        resInst[instname]["editor"] = editor
        resInst[instname]["testtime"] = round(time.time(), 2)
        resInst[instname]["fristtime"] = resInst[instname].get("fristtime") or round(time.time(), 2)
    else:
        resInst[instname] = {
            "state": res["state"] or 0,
            "state_dd": res["state_dd"] or 0,
            "editor": editor,
            "testtime": round(time.time(), 2),
            "fristtime": round(time.time(), 2),
        }

    json_to_redis = json.dumps(
        sorted(
            [{"name": k, **v} for k, v in resInst.items()],
            key=lambda itm: float(itm["state"] or 0),
            reverse=True)).replace("NaN", "null")

    redis_engine.hset(obj, "resultAll", json_to_redis)
    redis_engine.hget(obj, "result222")
    
    return resJson

@ontime_test_bp.route('/ontime-test/get-result222', methods=['POST'])
def get_result222():
    obj = 'cmg'
    result222 = redis_engine.hget(obj, "result222")
    if not result222:
        default_result = {
            "state": 0,
            "detectInfo": {
                "rule": [],
                "ml": []
            },
            "costtime": 0
        }
        return json.dumps(default_result)
    return result222

@ontime_test_bp.route('/ontime-test/get-inst-all', methods=['GET', 'POST'])
def get_inst_all():
    obj = 'cmg'
    return redis_engine.hget(obj, "resultAll") or "[]"

@ontime_test_bp.route('/ontime-test/get-inst-one', methods=['GET', 'POST'])
def get_inst_one():
    obj = 'cmg'
    instname = request.form.get("instname")
    return redis_engine.hget(f"{obj}#{instname}", "result") or "{}"
