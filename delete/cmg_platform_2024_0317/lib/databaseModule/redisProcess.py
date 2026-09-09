from redis import Redis
from threading import Thread
from datetime import datetime
from typing import Dict
import json, subprocess, uuid, time
from .dataBaseEngine import dataBase, dataInfoBase,ruleBase, msfgBase,Session

from ..flaskModule.msfgModule import utils as msfg_util
from ..algoModule.detectAlgo.rule.RuleDetector import ruleConvertor
from ..flaskModule.pname_struct_op import convert_tree_to_dict
def get_uuid(kw=""):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{kw}#%.7f"%time.time()))

class safeRedis:
    def __init__(self, host='localhost', port=6379, decode_responses=True, db=None, **kwargs):
        self.host = host
        self.port = port
        self.decode_repsonses = decode_responses
        self.kwargs = kwargs
        self.initRedis()
        self.dbCache = []
        self.process = None
        Thread(target=self.db_thread, name="Thread-Redis2DB", daemon=True).start()
    
    @property
    def get_config(self):
        return [self.host, self.port, self.decode_repsonses, self.kwargs]

    def initRedis(self):
        for _ in range(3):
            try:
                self.redis = Redis(host=self.host, port=self.port, decode_responses=self.decode_responses, **self.kwargs)
                self.redis.ping() 
                return True
            except Exception as e:
                try:
                    self.process = subprocess.Popen([".\\support\\Redis5\\redis-server.exe", ".\\support\\Redis5\\redis.windows.conf"])
                    time.sleep(0.2)
                    self.redis = Redis(host=self.host, port=self.port, decode_responses=self.decode_responses, **self.kwargs)
                    self.redis.ping()
                    print("[INFO] Succeed to connecting Redis")
                    return True
                except Exception as e:
                    print(f"[WARN] Failed to connect Redis\n\t[Traceback] {repr(e)}")
                    pass
        return False

    def __getattr__(self, method_name):
        if method_name[0] == "_":
            method_name = method_name[1:]
        def inner_func(*args, **kwargs):
            try:
                return getattr(self.redis, method_name)(*args, **kwargs)
            except Exception as e:
                if self.initRedis():
                    try:
                        return getattr(self.redis, method_name)(*args, **kwargs)
                    except Exception as e:
                        args = ",".join(list(map(str, args)) + \
                            list(map(lambda item: f"{item[0]}={item[1]}", kwargs.items())))
                        print(f"[WARN] Failed to execute command \'redis.{method_name}({args})\'\n\t[Traceback] {repr(e)}")
                else:
                    print(f"[WARN] Failed to connect Redis\n\t[Traceback] {repr(e)}")
                    return None
        return inner_func

    def __del__(self):
        self.redis.save()

    def db_thread(self):
        while True:
            dbCache = self.dbCache.copy()
            dbCacheLen = len(dbCache)
            self.dbCache = self.dbCache[dbCacheLen:]
            for dbInfo in dbCache:
                db_name, db_obj, db_info = dbInfo
                if db_info:
                    for _ in range(5):
                        try:
                            self._to_db(db_name, db_obj, db_info)
                            break
                        except Exception as e:
                            time.sleep(2)
                            self._to_db(db_name, db_obj, db_info)
            time.sleep(0.5)

    def hget(self, field, key, *args, **kwargs):
        result = self._hget(field, key, *args, **kwargs)

        if result is None:
            result = self._from_db(field, key)
            if not result is None:
                self._hset(field, key, result)
        return result

    def hset(self, field, key, value, *args, **kwargs):
        self._hset(field, key, value, *args, **kwargs)
        if key == "dataInfo":
            self.dbCache.append([field, key, json.loads(value)])
        elif key == "msfg-raw-config":
            struct = json.loads(value)
            if isinstance(struct, Dict):
                struct = struct["SystemData"]
            D_mat, testName, faultName, ConnIds, testLoc, faultLoc, \
                   sysmap, collision_node, faultConfig = msfg_util.to_D_mat(
                       *msfg_util.flatten_graph(struct), eps=1e-15, raise_collision=False)
            graphJson = msfg_util.to_json(D_mat, struct,
                                          testLoc, faultLoc, sysmap,
                                          testName, faultName,
                                          collision_node, ConnIds)
            self._hset(field, "msfg-config", graphJson)
            self.dbCache.append([field, key, [{
                "msfg_raw_params": value.encode(),
                "msfg_params": graphJson.encode(),
                }]])
        elif key == "rule-edit-config":
            pnames = json.loads(self.hget(field, "pnames") or "{}")
            pnames =  {p:p for p in pnames}  #后续可能需要修改，更正为如下格式 key为测点名字 value为其属于的部件名字
            #pnames = {k: v[1] for k, v in pnames_components.items()}
            # components = {v[1]: v[0] for k, v in pnames_components.items() if v[0] and v[1]}
            tableData = json.loads(value)
            ruleData = [{
                "ruleExpress": itm["ruleCriterion"],
                "faultName": itm["faultName"],
                "planDescript": itm["planDescript"],
                "component": sorted({pnames[p] for p in itm.get("pnames", []) if p in pnames.keys()}),
                "ruleOnline": False,
                } for itm in tableData if itm.get("ruleCriterion") and itm.get("ruleOnline")]
            self._hset(field, "rule-config", json.dumps(ruleConvertor(pnames)._convert_rule(ruleData)))
            self.dbCache.append([field, key, tableData])
        
        return

 

    @ staticmethod 
    def _register_db(dataBaseClass, obj, dataBaseInfo, del_mode=True):
        session = Session()
        if del_mode:
            session.query(dataBaseClass).delete()
        session.bulk_insert_mappings(dataBaseClass, dataBaseInfo)
        session.commit()
        session.close()
        time.sleep(0.5)
        print(f"[DB-Registration] Succed to write into DB#{dataBaseClass.__tablename__.replace('_', '')}")
        return 
  
 
    def _to_db(self, obj, key, value):
        if key == "dataInfo":
            
            result = [
                {
                    "data_name": v["dataName"]  ,
                    "data_descript": v["dataDescript"],
                    "source": v.get("source", ""),  # 使用get方法提供默认值
                    "data_uuid": v["dataUuid"],
                } for v in value]
            self._register_db(dataInfoBase, obj, result)
        elif key == "msfg-config":
            result = [{
                    "obj": obj,
                    "msfg_raw_params": v["msfg_raw_params"],
                    "msfg_params": v["msfg_params"],
                } for v in value]
            self._register_db(msfgBase, obj, result)
        elif key == "rule-edit-config":
            result = [{
                    "rule_express": ml_info["ruleExpress"],
                    "fault_name_uuid": ml_info["faultName"],
                    "plan_descript": ml_info.get("planDescript", "[]"),
                    "online_state": int(ml_info["ruleOnline"]),
                    "obj": obj,
                } for ml_id, ml_info in enumerate(value)]
            self._register_db(ruleBase, obj, result)
       

    def _from_db(self, obj, key):
      
        if key == "dataInfo":
            session = Session()
            db_res = session.query(dataInfoBase).all()
            
            db_info = [{
                "dataName": db_info_itm.data_name,
                "dataDescript":db_info_itm.data_descript,
                "source": db_info_itm.source,
                "dataUuid": db_info_itm.data_uuid,
            }  for db_info_id, db_info_itm in enumerate(db_res)]
            session.close()
            resultJson = json.dumps(db_info)
            self._hset(obj, key, resultJson)
            return resultJson
      
        elif key == "msfg-config":
            session = Session()
            db_res = session.query(msfgBase)\
                .filter(msfgBase.obj==obj).first()
            if not db_res is None:
                msfg_raw_params = db_res.msfg_raw_params.decode()
                msfg_params = db_res.msfg_params.decode()
            else:
                msfg_params = None
            session.close()
            if db_res:
                self._hset(obj, "msfg-raw-config", msfg_raw_params)
                self._hset(obj, "msfg-config", msfg_params)
            return msfg_params
        elif key == "rule-edit-config":
            session = Session()
            db_res = session.query(ruleBase)\
                .filter(ruleBase.obj==obj).all()
            db_info = [{
                    "ruleExpress": db_info_itm.rule_express,
                    "faultName": db_info_itm.fault_name_uuid,
                    "planDescript": db_info_itm.plan_descript,
                    "ruleOnline": bool(db_info_itm.online_state),
                    "obj": obj,
                } for db_info_id, db_info_itm in enumerate(db_res)]
            session.close()
            resultJson = json.dumps(db_info)
            resultJson_ = json.dumps([itm for itm in db_info if itm.get("mdlOnline")])
            self._hset(obj, "rule-edit-config", resultJson)
            self._hset(obj, "rule-config", resultJson_)
            return resultJson
        elif key == "rule-config":
            session = Session()
            db_res = session.query(ruleBase)\
                .filter(ruleBase.obj==obj).all()
            db_info = [{
                    "ruleExpress": db_info_itm.rule_express,
                    "faultName": db_info_itm.fault_name_uuid,
                    "planDescript": db_info_itm.plan_descript,
                    "ruleOnline": bool(db_info_itm.online_state),
                    "obj": obj,
                } for db_info_id, db_info_itm in enumerate(db_res)]
            session.close()
            resultJson = json.dumps(db_info)
            resultJson_ = json.dumps([itm for itm in db_info if itm.get("mdlOnline")])
            self._hset(obj, "rule-edit-config", resultJson)
            self._hset(obj, "rule-config", resultJson_)
            return resultJson_
           
        return

