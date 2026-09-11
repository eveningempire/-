import os, json, time, datetime
import pandas as pd
import numpy as np
from multiprocessing import Process, Queue

if __name__ == '__main__':
    from ml import algoChoose
    from rule.RuleDetector import ruleEvaluator
    from msfg_detect_utils import fuse_detect_with_render
else:
    from .ml import algoChoose
    from .rule.RuleDetector import ruleEvaluator
    from .msfg_detect_utils import fuse_detect_with_render

class demoClass:
    def __init__(self):
        self.pnames = []

def _loadConfig(config):
    if config["detectType"] == "rule":
        if "params" in config.keys() and len(config["params"]) > 3:
            return ruleEvaluator(*config["params"], fnameMap=config["fnameMap"])
        else:
            return demoClass()
    else:
        mdl = algoChoose.Model(
            index = config["modelUuid"],
            name=config.get("modelName", "model"),
            config=json.loads(config.get("params", "{}")),
            pnames=config["relatParas"],
            algoname=config["modelAlgo"],
            component = config.get("component", "@")
            )
        mdl.load_model()
        return mdl

def _convertTime(faultTime):
    return datetime.datetime.fromtimestamp(time.time()+faultTime).strftime("%Y年%m月%d日 %H:%M:%D")

def _anomCount(result, n_round=5):
    if np.ndim(result) >= 2:
        result = np.max(result, axis=-1)
    return round(np.mean(np.sort(result)[-min(30, max(1, round(len(result)/10))):]), n_round)

def detectTest(fname, config, resqueue, n_round=5):
    time1 = time.time()
    ## Avoid get-Undefined-Parameter-Value Error 
    dataFrames = pd.read_csv(fname, index_col=0, header=0, encoding="gbk")
    #跟据模型的uuid来读取之前训练好的模型信息
    mdl = _loadConfig(config)
    if (not "validate" in dir(mdl)) and (not "_model" in dir(mdl)):
        return 
    if config["detectType"] == "rule":
        mdl.pnames = dataFrames.columns.values.tolist()
        time2 = time.time()
        res = mdl.validate(dataFrames.loc[:, mdl.pnames].values, dataFrames.index.values)
        time3 = time.time()
        print('[rule validation time]',time3-time2)
    else:
        res = mdl.validate(dataFrames.loc[:, mdl.pnames].values)
    if config["detectType"] == "rule":
        scoreDicts = [
            {"state": _anomCount(itm["scoreList"], n_round=n_round), **itm} 
            for itm in res[1]]
        # [{"fnames": ..., "scoreList": ..., "descript": ...}, ...]
        return ["RULE",scoreDicts]
        resqueue.put(["RULE", scoreDicts])
        time4 = time.time()
        print('[work run time]',time4-time1)
    
        
def _d_s_combine(scores, eps=1e-5, n_round=5):
    scores = np.array(scores, dtype="float32")
    if len(scores) == 1:
        return scores[0]
    return np.round(np.min(scores, axis=0),n_round)  # 重复时取最小
    #prob_a = np.prod((1-eps)*scores + eps, axis=0)
    #prob_b = np.prod((1-eps)*(1-scores) + eps, axis=0)
    #return 1 / (1 - prob_b/prob_a)

def _fuse_rule_ml(ruleScore, mlScore, eps=1e-5, n_round=5):
    if ruleScore is None:
        return np.around(np.where(~np.isnan(mlScore), mlScore, 0), n_round)
    elif mlScore is None:
        return np.around(np.where(~np.isnan(ruleScore), ruleScore, 0), n_round)
    else:
        mlScore = np.where(~np.isnan(mlScore), mlScore, 0)
        ruleScore = np.where(~np.isnan(ruleScore), ruleScore, 0)
        sim = np.exp(mlScore*(np.log(mlScore+eps)-np.log(ruleScore+eps)) + \
            (1-mlScore)*(np.log(1-mlScore+eps)-np.log(1-ruleScore+eps)))
        res = sim*(mlScore*ruleScore)**0.5 + (1-sim)*(1-((1-mlScore)*(1-ruleScore))**0.5)
        return np.around(np.where(~np.isnan(res), res, mlScore), n_round)

def _simplify_time_series(time_series_data, n_max=1000):
    step = round(len(time_series_data)/n_max)
    if step < 2:
        return [float(v) for v in time_series_data]
    else:
        time_series_data = np.append(time_series_data, np.zeros((-len(time_series_data))%step))
        return [float(v) for v in np.reshape(time_series_data, (-1, step)).max(axis=-1)]

def _convert_time(faultTime):
    return datetime.datetime.fromtimestamp(time.time()+faultTime).strftime("%Y年%m月%d日 %H:%M:%D")

class wholeDetector:
    def __init__(self, configs, msfgConfig, worker_num=3, roaming_dir=r"./static/roaming", n_round=5):
        self._worker_num = worker_num
        self._modelConfigs = configs
        self._n_round=n_round
        self._msfgConfig = msfgConfig
        #D_mat, struct, testLoc, faultLoc, sysmap, testName, faultName, _, ConnIds
        self._roaming_dir = roaming_dir
        self._pnames = set()
        for mdl_config in configs:
            # print(mdl_config)
            self._pnames |= set(mdl_config.get("pnames", mdl_config.get("relatParas", [])) or _loadConfig(mdl_config).pnames)
        self._pnames = sorted(set(self._pnames))

    def fit(self, dataFrames, save=False):
        ## Avoid get-Undefined-Parameter-Value Error 
        dataFrames.loc[:, list(set(self._pnames)-set(dataFrames.columns.values.tolist()))] = float("nan")
        for mdl in self._models:
            if not "fit" in dir(mdl):
                continue
            mdl.fit(dataFrames.loc[:, mdl.pnames], save=save)

    def onlineValidate(self, dataFrame, time_):
        result = []
        for mdl in self._models:
            res = mdl.onlineValidate([
                dataFrame.get(p, float("nan")) for p in mdl.pnames
                ], time_)
            if isinstance(res, list):
                result.extend(res)
            else:
                result.append(res)
        return result

    def offlineValidate(self, dataFrames):
        #该诊断器初始化中的modelConfig包含了需要检验的专家规则和需要验证的数据驱动模型
        #根据worker数量上限创建n个进程分别验证 核心函数为detectTest（接受配置任务和数据，并返回结果）
        time1 = time.time()
        fname = os.path.join(self._roaming_dir, f"roaming_data_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv")
        workers_on = 0
        Workers = [None for _ in range(self._worker_num)]
        try:
            time_ = pd.to_datetime(dataFrames.index).values.astype("float64")*1e-9
        except Exception as e:
            time_ = np.arange(dataFrames.shape[0])
        dataFrames.index = time_
        self._pnames = list(set(self._pnames) | set(dataFrames.columns.values.tolist()))
        dataFrames.loc[:, list(set(self._pnames)-set(dataFrames.columns.values.tolist()))] = float("nan")
        dataFrames.loc[:, list(set(self._pnames))].to_csv(fname, encoding="gbk")
        print("[INFO] Preprocessing of detect stage is finished")
        detectRuleResult = []; faultRuleRes = {}; paraRuleRes = {}
        detectMLResult = []; paraMLRes = {}
        
        resqueue = Queue()
        toDoList = self._modelConfigs.copy()
        
        config = toDoList.pop(0)
        res = detectTest(fname, config, resqueue, self._n_round)
        time1 = time.time()
        if res[0] == "RULE":
            detectRuleResult = res[1]
            for info in detectRuleResult:
                if info["fname"] in faultRuleRes.keys():
                    faultRuleRes[info["fname"]] = np.maximum(faultRuleRes[info["fname"]], info["scoreList"])  # 重复涉及同一故障取最大
                else:
                    faultRuleRes[info["fname"]] = np.array(info["scoreList"], dtype="float32")
                for pname in info["descript"][-1]["value"].split(","):
                    if not pname:
                        continue
                    if pname in paraRuleRes.keys():
                        paraRuleRes[pname].append(info["scoreList"])
                    else:
                        paraRuleRes[pname] = [info["scoreList"]]
            faultRuleRes = {k: v.tolist() for k, v in faultRuleRes.items()}
            paraRuleRes = {k: np.min(v, axis=0) for k, v in paraRuleRes.items()}  # 重复涉及同一参数取最小?

        print("[INFO] Basic Stage of Test is finished")#,time3-time2,time2-time1)
        time2  = time.time()
        paraMLRes = {k: _d_s_combine(v, n_round=self._n_round) for k,v in paraMLRes.items()}
        paraRes = {
            k:_simplify_time_series(_fuse_rule_ml(paraRuleRes.get(k), paraMLRes.get(k), n_round=self._n_round))
            for k in set(paraMLRes.keys())|set(paraRuleRes.keys())}
        paraRuleRes_ = {
            k:_simplify_time_series(paraRuleRes[k])
            for k in set(paraRuleRes.keys())}
        faultRes = {k:_simplify_time_series(v) for k,v in faultRuleRes.items()}

        dataFrames = {
            str(k): _simplify_time_series(v)
            for k, v in zip(dataFrames.columns.values, dataFrames.values.T)}
        timeData = list(map(_convert_time, _simplify_time_series(time_)))
        D_mat, struct, testLoc, faultLoc, sysmap, testName, faultName, _, ConnIds = self._msfgConfig
        p_test_ = np.array([faultRes.get(tn, paraRuleRes_.get(tn, [0 for _ in timeData])) for tn in testName], dtype="float32").T
        f_test = np.array([faultRes.get(fn, [0 for _ in timeData]) for fn in faultName], dtype="float32").T
        time3 =  time.time()
        
        detectMsfgResult_, sysData_ = fuse_detect_with_render(p_test_, f_test, D_mat, struct, testLoc, faultLoc,
                                                            sysmap, ConnIds, eps=1e-9, n_round=self._n_round)
        p_test = np.array([faultRes.get(tn, paraRes.get(tn, [0 for _ in timeData])) for tn in testName], dtype="float32").T
        #detectMsfgResult, sysData = fuse_detect_with_render(p_test, f_test, D_mat, struct, testLoc, faultLoc,
        #                                                    sysmap, ConnIds, eps=1e-9, n_round=self._n_round)
        sysData = sysData_
        time4  = time.time()
        pnames = sorted(paraRes.keys())
        systemData_ = sorted([
                {"name": k, "state": _anomCount(v["proba"], n_round=self._n_round),
                 "fuzzy_state": _anomCount(v["fuzzy_proba"],n_round=self._n_round),
                 "stateRange": v["proba"], "fuzzy_stateRange": v["fuzzy_proba"]}
                for k,v in sysData_.items()], key=lambda itm: itm.get("state", 0), reverse=True)
        
        systemData = sorted([
                {"name": k, "state": _anomCount(v["proba"], n_round=self._n_round),
                 "fuzzy_state": _anomCount(v["fuzzy_proba"], n_round=self._n_round),
                 "stateRange": v["proba"], "fuzzy_stateRange": v["fuzzy_proba"]}
                for k,v in sysData.items()], key=lambda itm: itm.get("state", 0), reverse=True)
        print("[INFO] Fault Location via MSFG is finished")
        result = {
            "detectInfo": {
                "rule": sorted(detectRuleResult, key=lambda itm: itm.get("state", 0), reverse=True),
                "ml": sorted(detectMLResult, key=lambda itm: itm.get("state", 0), reverse=True),
                "mfsg": detectMsfgResult_,
                "mfsg_dd": detectMsfgResult_,
            },
            "systemData": systemData_,
            "systemData_dd": systemData_,
            "state": round(1 - float(np.prod([1-v["state"] for v in systemData_])), self._n_round),
            "state_dd": round(1 - float(np.prod([1-v["state"] for v in systemData])), self._n_round),
            "stateRange": [round(1 - float(np.prod([1-v["stateRange"][i] for v in systemData_])), self._n_round)
                           for i, _ in  enumerate(timeData)],
            "timeData": timeData,
            "pnames": pnames,
            "paraData": dataFrames,
        }
        print("[INFO] Detection Stage of Test is finished")
        time5  = time.time()
        print('D矩阵推理加渲染',time4-time3)
        try:
            os.remove(fname)
        except:
            print(f"[WARN] Fail to delete the roaming file: {fname}")
            
        return result

if __name__ == '__main__':
    fname = r'D:\Users\baoding\Desktop\test.csv'
    config = {
        'detectType': 'rule', 'params': [[['>', ['%', ['Para', '左机轮刹车给定', 0, 0], 0.5], 0.01],
                                                ['>', ['%', ['Para', '右机轮刹车给定', 0, 0], 0.5], 0.01]], [], [0, 1],
                                               {'Para': {'左机轮刹车给定': {'frameMax': 0, 'timeMax': 0, 'value': [],
                                                                            'time': []},
                                                         '右机轮刹车给定': {'frameMax': 0, 'timeMax': 0, 'value': [],
                                                                            'time': []}},
                                                'Fault': {'node-1-186': {'state': None, 'score': 0},
                                                          'node-1-201': {'state': None, 'score': 0}}, 'Crease': {},
                                                'MMM': {}, 'PreCond': {}, 'Trigger': {}, '[]': {}, '<>': {}, '{}': {}},
                                               ['node-1-186', 'node-1-201'], [0, 1], [
                                                   [{'name': '故障名称', 'value': '左刹车电磁阀异常'},
                                                    {'name': '涉及部件', 'value': '左刹车电控装置'},
                                                    {'name': '规则表达式', 'value': '左机轮刹车给定 % 0.5 > 0.01'},
                                                    {'name': '故障等级', 'value': 1},
                                                    {'name': '预案描述', 'value': '检查左刹车电磁阀电磁环境'},
                                                    {'name': '相关参数', 'value': '左机轮刹车给定'}],
                                                   [{'name': '故障名称', 'value': '右刹车电磁阀异常'},
                                                    {'name': '涉及部件', 'value': '右刹车电控装置'},
                                                    {'name': '规则表达式', 'value': '右机轮刹车给定 % 0.5 > 0.01'},
                                                    {'name': '故障等级', 'value': 1},
                                                    {'name': '预案描述', 'value': '检查右刹车电磁阀电磁环境'},
                                                    {'name': '相关参数', 'value': '右机轮刹车给定'}]],
                                               ['右机轮刹车液压压力', '右机轮刹车给定', '右机轮速度',
                                                '左机轮刹车液压压力', '左机轮刹车给定', '左机轮速度']],
              'fnameMap': {'node-1-268': '刹车液压控制单元异常', 'node-1-182': '右轮刹车压力异常',
                           'node-1-178': '刹车壳形变', 'node-1-176': '密封圈异常', 'node-1-172': '左刹车压力液压异常',
                           'node-1-4': '刹车壳形变', 'node-1-2': '密封圈异常', 'node-1-207': '右刹车单元压力异常',
                           'node-1-210': '右刹车液压电机异常', 'node-1-201': '右刹车电磁阀异常',
                           'node-1-203': '塑封油管漏油', 'node-1-192': '左刹车单元压力异常',
                           'node-1-195': '左刹车液压电机异常', 'node-1-186': '左刹车电磁阀异常',
                           'node-1-188': '塑封油管漏油'}}
    resqueue = Queue()
    detectTest(fname, config, resqueue)
    print(resqueue.get_nowait())
