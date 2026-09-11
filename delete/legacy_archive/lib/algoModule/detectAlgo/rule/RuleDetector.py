from .FuncBase import getResult
from .RuleParse import ruleParse
import re, math, json
from typing import Dict, List

KEY_DEFAULT = {
    "showId": "showId", "ruleExpress": "ruleExpress",
    "faultName": "faultName", "faultLevel": "faultLevel",
    "planDescript": "planDescript",
    "isNew": "isNew", "component": "component", "editable": "editable",
    "ruleOnline": "ruleOnline"
    }

class ruleConvertor:
    def __init__(self, pnames={}, keyMap=None, descriptMap=None):
        if isinstance(pnames, List):
            pnames = {k: "未知系统" for k in pnames}
        self.pnames = list(pnames.keys())
        self.pnameDict = pnames
        if isinstance(keyMap, Dict):
            self.keyMap = {**KEY_DEFAULT, **keyMap}
        else:
            self.keyMap = KEY_DEFAULT
        if isinstance(descriptMap, Dict):
            self.descriptMap = {k: v if isinstance(v, Dict) else {"name": v, "default": ""} for k,v in descriptMap.items()}
        else:
            self.descriptMap = {
                self.keyMap["faultName"]: {"name": "故障名称", "default": ""},
                self.keyMap["component"]: {"name": "涉及部件", "default": []},
                self.keyMap["ruleExpress"]: {"name": "规则表达式", "default": ""},
                self.keyMap["faultLevel"]: {"name": "故障等级", "default": 1},
                self.keyMap["planDescript"]: {"name": "预案描述", "default": ""},
                }

    def _searchComponent(self, p):
        return self.pnameDict[p]

    def _getComponent(self, relatPara, how="max"):
        components = {}
        for p in relatPara:
            components[self._searchComponent(p)] = components.get(self._searchComponent(p), 0) + 1
        if how == "max":
            return max(components.keys(), key=components.get)
        elif len(str(how).split(".")) < 3 and str(how).replace(".", "").isnumeric():
            thres = max(components.values)*min(max(0, float(how)), 1)
            return sorted([comp for comp in sorted(components.keys(), reverse=True) if components[p] >= thres], key=components.get, reverse=True)
        else:
            return sorted(sorted(components.keys(), reverse=True), key=components.get, reverse=True)

    def _check_rule(self, rulesInfo, comp_how="all"):
        result = []; checkPass = True
        faultCircle = {}
        faults = [itm.get(self.keyMap["faultName"], "") for itm in rulesInfo if itm.get(self.keyMap["faultName"], "").replace(" ","")]
        log_info = [{} for _ in faults]
        for ruleId, ruleInfo in enumerate(rulesInfo):
            if ruleInfo.get(self.keyMap["editable"], True) or ruleInfo.get(self.keyMap["isNew"], True):
                err_num = 0; warn_num = 0; log_item = []
                if ruleInfo.get(self.keyMap["ruleExpress"], "").replace(" ",""):
                    rp = ruleParse(pnames=self.pnames, fnames=faults)
                    rp.convert(ruleInfo[self.keyMap["ruleExpress"]])
                    fnames = list(rp.relatFault)
                    for fname in fnames:
                        fnameId = faults.index(fname)
                        if fnameId == ruleId:
                            err_num += 1
                            log_item.append({"type": "error", "text": "规则表达式不得涉及规则本身的故障名"})
                        else:
                            if ruleId in faultCircle.keys():
                                faultCircle[ruleId].append(fnameId)
                            else:
                                faultCircle[ruleId] = [fnameId]
                            if fnameId in faultCircle.keys():
                                if ruleId in faultCircle[fnameId]:
                                    err_num += 1
                                    log_item.append({"type": "error", "text": f"故障与故障{faults[fnameId]}存在闭环"})
                                faultCircle[ruleId].extend(faultCircle[fnameId])
                    log_item.extend(rp.log)
                    err_num += rp.error
                    warn_num += rp.warning
                else:
                    err_num += 1
                    log_item.append({"type": "error", "text": "规则表达式缺失"})
                if faults[ruleId] in faults[:ruleId]:
                    warn_num += 1
                    rulePreId = faults.index(faults[ruleId])
                    log_item.append({"type": "warn", "text": f"故障名与规则{rulePreId}重复"})
                if len(faults[ruleId]) > 25:
                    warn_num += 1
                    log_item.append({"type": "warn", "text": "故障名过长"})
                if len(ruleInfo.get(self.keyMap["planDescript"], "")) > 500:
                    warn_num += 1
                    log_item.append({"type": "warn", "text": "预案描述过长"})

                log_info[ruleId] = {"error": err_num, "warn": warn_num, "info": log_item}

                if err_num == 0:
                    ruleInfo[self.keyMap["editable"]] = False
                    ruleInfo[self.keyMap["isNew"]] = False
                    ruleInfo[self.keyMap["component"]] = self._getComponent(rp.relatPara.keys(), comp_how)
                    ruleInfo["_rule_inner_relat_fault"] = fnames
                    ruleInfo["_rule_inner_log"] = log_info[ruleId]
                else:
                    checkPass = False
                    ruleInfo[self.keyMap["editable"]] = True
                    ruleInfo[self.keyMap["isNew"]] = True
                    ruleInfo[self.keyMap["ruleOnline"]] = False
                    ruleInfo["_rule_inner_log"] = log_info[ruleId]
            else:
                if faults[ruleId] in faults[:ruleId]:
                    err_num += 1
                    rulePreId = faults.index(faults[ruleId])
                    log_item.append({"type": "error", "text": "故障名与规则{rulePreId}重复"})
                for relatFaultName in ruleInfo[self.keyMap["relatFault"]]:
                    if relatFaultName not in faults:
                        err_num += 1
                        log_item.append({"type": "error", "text": "故障名{relatFaultName}未出现"})
                for fname in ruleInfo["_rule_inner_relat_fault"]:
                    fnameId = faults.index(fname)
                    if fnameId == ruleId:
                        err_num += 1
                        log_item.append({"type": "error", "text": "规则表达式不得涉及规则故障名"})
                    else:
                        if ruleId in faultCircle.keys():
                            faultCircle[ruleId].append(fnameId)
                        else:
                            faultCircle[ruleId] = [fnameId]
                        if fnameId in faultCircle.keys():
                            if ruleId in faultCircle[fnameId]:
                                err_num += 1
                                log_item.append({"type": "error", "text": "故障与故障{faults[fnameId]}存在闭环"})
                            faultCircle[ruleId].extend(faultCircle[fnameId])
                log_info[ruleId] = ruleInfo.get("_rule_inner_log", {"error": 0, "warn": 0, "info": []})
                log_info[ruleId]["error"] += err_num
                ruleInfo["_rule_inner_log"] = log_info[ruleId]
                if log_info[ruleId]["error"]:
                    checkPass = False
                    ruleInfo[self.keyMap["editable"]] = True
                    ruleInfo[self.keyMap["ruleOnline"]] = False
                else:
                    ruleInfo[self.keyMap["editable"]] = False
                ruleInfo[self.keyMap["isNew"]] = False
            result.append(ruleInfo)
        return checkPass, log_info, result

    def _config_rule(self, rulesInfo):
        rule, seqOrder, ruleOrder, data, fnames, rulesOnlineId, descript, pnames = self._convert_rule(rulesInfo)
        return json.dumps([rule, seqOrder, ruleOrder, data, fnames, rulesOnlineId, descript, pnames]), rulesInfo

    def _set_description(self, ruleInfo):
        return [{"name": v.get("name", k), "value": ruleInfo.get(k, v.get("default", ""))} for k, v in self.descriptMap.items()]

    def _convert_rule(self, rulesInfo):
        rule = []; seqOrder = []; ruleOrder = []
        data = {
            "Para": {}, "Fault": {},
            "Crease": {}, "MMM": {},
            "PreCond": {}, "Trigger": {},
            "[]": {}, "<>": {}, "{}": {},
            }
        rulesOnlineId = [ruleId for ruleId, ruleInfo in enumerate(rulesInfo) if ruleInfo.get(self.keyMap["ruleOnline"], True)]
        rulesInfo = [rulesInfo[ruleId] for ruleId in rulesOnlineId]
        faults = [ruleInfo[self.keyMap["faultName"]] for ruleInfo in rulesInfo]

        faultCircle = {}; descript = []
        for ruleId, ruleInfo in enumerate(rulesInfo):
            rp = ruleParse(pnames=self.pnames,fnames=faults)
            data["Fault"][faults[ruleId]] = {"state": None, "score": 0}
            result = rp.convert(ruleInfo[self.keyMap["ruleExpress"]])
            relatPara = sorted(rp.relatPara.keys())
            descript.append(self._set_description(ruleInfo)+[{"name": "相关参数", "value": ",".join(relatPara)}])

            rule.append(result)
            for funcInfo in rp.seqOrder:
                if not funcInfo in seqOrder:
                    seqOrder.append(funcInfo)
            for para in rp.relatPara.keys():
                if para in data["Para"].keys():
                    data["Para"][para]["frameMax"] = max(data["Para"][para]["frameMax"], rp.relatPara[para][0])
                    data["Para"][para]["timeMax"] = max(data["Para"][para]["timeMax"], rp.relatPara[para][1])
                else:
                    data["Para"][para] = {"frameMax": rp.relatPara[para][0], "timeMax": rp.relatPara[para][1], "value":[], "time":[]}
            for funcName, seqInfo in rp.seqs.items():
                if funcName in ["Time"]:
                    for para, subInfo in seqInfo.items():
                        _, subCount = subInfo
                        if para in data["Para"].keys():
                            data["Para"][para]["frameMax"] = max(data["Para"][para]["frameMax"], subCount[0][0])
                            data["Para"][para]["timeMax"] = max(data["Para"][para]["timeMax"], subCount[0][1])
                        else:
                           data["Para"][para] = {"frameMax": subCount[0][0], "timeMax": subCount[0][1], "value":[], "time":[]}
                elif funcName in ["Max", "Min", "Mean"]:
                    for subExpress, subInfo in seqInfo.items():
                        subTree, subCount = subInfo
                        if subExpress in data["MMM"].keys():
                            data["MMM"][subExpress]["frameMax"] = max(data["MMM"][subExpress]["frameMax"], subCount[0][0])
                            data["MMM"][subExpress]["timeMax"] = max(data["MMM"][subExpress]["timeMax"], subCount[0][1])
                        else:
                           data["MMM"][subExpress] = {"convertedRule": subTree[0], "frameMax": subCount[0][0],
                                                                              "timeMax": subCount[0][1], "value":[], "time":[]}
                elif funcName in ["Increase", "Decrease"]:
                    for subExpress, subInfo in seqInfo.items():
                        subTree, subCount = subInfo
                        if subExpress in data["Crease"].keys():
                            data["Crease"][subExpress]["frameMax"] = max(data["Crease"][subExpress]["frameMax"], subCount[0][0])
                            data["Crease"][subExpress]["timeMax"] = max(data["Crease"][subExpress]["timeMax"], subCount[0][1])
                        else:
                           data["Crease"][subExpress] = {"convertedRule": subTree[0], "frameMax": subCount[0][0],
                                                                              "timeMax": subCount[0][1], "value":[], "time":[], "prevalue": None,
                                                                              "lastDecTime":None, "lastIncTime": None}
                elif funcName in ["[]"]:
                    for subExpress, subInfo in seqInfo.items():
                        subTree,  _ = subInfo
                        data["[]"][subExpress] = {"convertedRule": subTree, "lastTime": None, "lastFalseTime": None}
                elif funcName in ["<>"]:
                    for subExpress, subInfo in seqInfo.items():
                        subTree, _ = subInfo
                        data["<>"][subExpress] = {"convertedRule": subTree, "lastTime": None,  "lastTrueTime": None}
                elif funcName in ["{}"]:
                    for subExpress, subInfo in seqInfo.items():
                        subTree, subCount = subInfo
                        if subExpress in data["{}"].keys():
                            data["{}"][subExpress]["frameMax"] = max(data["{}"][subExpress]["frameMax"], subCount[0])
                        else:
                           data["{}"][subExpress] = {"convertedRule": subTree, "frameMax": subCount[0], "time": [], "value": [], "score": []}
                elif funcName in ["PreCond"]:
                    for subExpress, subInfo in seqInfo.items():
                        subTree, _ = subInfo
                        data["PreCond"][subExpress] = {"convertedRule": subTree[0], "validedTime": None, "state": None}
                elif funcName in ["Trigger"]:
                    for subExpress, subInfo in seqInfo.items():
                        subTree, _ = subInfo
                        data["Trigger"][subExpress] = {"convertedRule": subTree[0], "cancelRule": subTree[1], "timeMax": subCount[0],
                                                                            "trigTime": -1, "state": None}
            for fname in rp.relatFault:
                fnameId = faults.index(fname)
                if ruleId in faultCircle.keys():
                    faultCircle[ruleId].append(fnameId) # ruleId 需要先算 fnameId
                else:
                    faultCircle[ruleId] = [fnameId]
                if fnameId in faultCircle.keys():
                    faultCircle[ruleId].extend(faultCircle[fnameId]) # 队列中需要先算的在后，后算的在后

        # 根据fnames的依赖性确定规则判断顺序
        faultDependance = [[ruleId]+faultCircle[ruleId] for ruleId in faultCircle.keys()]
        for faultDepend in sorted(faultDependance, key=lambda faultDep: -len(faultDep)):
            if faultDepend[0] in ruleOrder:
                ruleOrder.extend(faultDepend[::-1])
        ruleOrder.extend(sorted(set(range(len(rulesInfo)))-set(ruleOrder)))
        return rule, seqOrder, ruleOrder, data, faults, rulesOnlineId, descript, sorted(self.pnames)

def _wash_desc(ds, fnameMap):
    for itmId, itm in enumerate(ds):
        if itm["name"] == "故障名称":
            ds[itmId]["value"] = fnameMap.get(itm["value"], itm["value"])
        return ds

class ruleEvaluator:
    def __init__(self, rule, seqOrder, ruleOrder, data, fnames, rulesOnlineId, descript=[], pnames=[], fnameMap=None):
        # rule, seqOrder, data, fnames, rulesOnlineId, descript
        self.pnames = pnames
        self.rule = rule
        self.seqOrder = seqOrder
        self.ruleOrder = ruleOrder
        self.data = data
        self.fnames = fnames
        self.descript = descript
        if isinstance(fnameMap, Dict):
            self.fnameMap = fnameMap
            self.descript = [_wash_desc(ds, fnameMap) for ds in descript]
        else:
            self.fnameMap = {}

        
    def validate(self, dataFrames, time_):
        resultList = [[] for i in range(len(self.rule))]; scoreList = [[] for i in range(len(self.rule))]
        for frame, dataFrame in enumerate(dataFrames):
            self.data["actualTime"] = time_[frame]
            for paraId, para in enumerate(self.pnames):
                if not para in self.data["Para"].keys():
                    self.data["Para"][para] = {"value": [], "time": []}
                self.data["Para"][para]["value"].append(dataFrame[paraId])
                self.data["Para"][para]["time"].append(time_[frame])
            for funcName, seqName in self.seqOrder:
                if funcName in ["Max", "Min", "Mean"]:
                    value_, _ = getResult(self.data, self.data["MMM"][seqName]["convertedRule"])
                    if not math.isnan(value_):
                        self.data["MMM"][seqName]["time"].append(time_[frame])
                        self.data["MMM"][seqName]["value"].append(value_)
                elif funcName in ["Increase", "Decrease"]:
                    value_, _ = getResult(self.data, self.data["Crease"][seqName]["convertedRule"])
                    if math.isnan(value_):
                        continue
                    if not self.data["Crease"][seqName]["prevalue"] is None:
                        self.data["Crease"][seqName]["time"].append(time_[frame])
                        self.data["Crease"][seqName]["value"].append(value_)
                        if value_ > self.data["Crease"][seqName]["prevalue"]:
                            self.data["Crease"][seqName]["lastIncTime"] = time_[frame]
                        elif value_ < self.data["Crease"][seqName]["prevalue"]:
                            self.data["Crease"][seqName]["lastDecTime"] = time_[frame]

                    self.data["Crease"][seqName]["prevalue"] = value_
                elif funcName in ["[]"]:
                    value_, _ = getResult(self.data, self.data["[]"][seqName]["convertedRule"])
                    if value_ is None:
                        continue
                    if not value_:
                        self.data["[]"][seqName]["lastFalseTime"] = time_[frame]
                    self.data["[]"][seqName]["lastTime"] = time_[frame]
                elif funcName in ["<>"]:
                    value_, _ = getResult(self.data, self.data["<>"][seqName]["convertedRule"])
                    if value_ is None:
                        continue
                    if value_:
                        self.data["<>"][seqName]["lastTrueTime"] = time_[frame]
                    self.data["<>"][seqName]["lastTime"] = time_[frame]
                elif funcName in ["{}"]:
                    value_, score_ = getResult(self.data, self.data["{}"][seqName]["convertedRule"])
                    if value_ is None:
                        continue
                    else:
                        self.data["{}"][seqName]["value"].append(value_)
                        self.data["{}"][seqName]["score"].append(score_)
                        self.data["{}"][seqName]["time"].append(time_[frame])
                elif funcName in ["PreCond"]:
                    value_, _ = getResult(self.data, self.data["PreCond"][seqName]["convertedRule"])
                    if value_ is None:
                        continue
                    if value_ and not self.data["PreCond"][seqName]["state"]:
                        self.data["PreCond"][seqName]["validedTime"] = time_[frame]
                    self.data["PreCond"][seqName]["state"] = value_
                elif funcName in ["Trigger"]:
                    value_, _ = getResult(self.data, self.data["Trigger"][seqName]["cancelRule"])
                    if value_:
                        self.data["Trigger"][seqName]["trigTime"] = -1
                        self.data["Trigger"][seqName]["state"] = None
                    else:
                        value_, _ = getResult(self.data, self.data["Trigger"][seqName]["convertedRule"])
                        if not value_ is None:
                            if value_ and not self.data["Trigger"][seqName]["state"]:
                                self.data["Trigger"][seqName]["trigTime"] = time_[frame]
                            self.data["Trigger"][seqName]["state"] = value_
            for ruleId in self.ruleOrder:
                res, score = getResult(self.data, self.rule[ruleId])
                if res:
                    resultList[ruleId].append(frame)
                scoreList[ruleId].append(score)
                self.data["Fault"][self.fnames[ruleId]]["state"] = res
                self.data["Fault"][self.fnames[ruleId]]["score"] = score
                self.data["Fault"][self.fnames[ruleId]]["time"] = time_[frame]
        return resultList, [{"fname": self.fnameMap.get(fn, fn), "fuid": fn, "scoreList": sl,
                             "descript": des,
                             "relatPara": [i for i in des[-1]["value"].split(",") if i] if des[-1]["name"] == "相关参数" else []
                             } for fn, sl, des in zip(self.fnames, scoreList, self.descript)]

if __name__ == "__main__":
    pnames = ["P1", "P2"]
    times = [1000,1000.2, 1000.3, 1000.5, 1000.6, 1000.7]
    dataFrame = [[1,6],[2,5],[3,4],[4,5],[5,6],[6,8]]
    rules = [
                    {"showId": 0, "ruleExpress": "Max(P1+5,1,0)+5>15", "faultName":"Tag1"},
                    {"showId": 1, "ruleExpress": "Max(P1+2,1,1)+5>15", "faultName":"Tag2"},
                    {"showId": 2, "ruleExpress": "Increase(P2*2,1,1) and Para(P1,0.1,1)<=10", "faultName":"故障001,1"},
                    {"showId": 3, "ruleExpress": "PreCond([0.1](P1<5), 0.3, Para(P1,0.1,1)>0)", "faultName":"故障002,2"}
                ]
    rule, seqOrder, ruleOrder, data, faults, rulesOnlineId, descript = ruleConvertor(pnames)._convert_rule(rules)
    print(rule)
    print(seqOrder)
    print(ruleOrder)
    print(ruleEvaluator(rule, seqOrder, ruleOrder, data, faults, pnames).validate(dataFrame, times))
