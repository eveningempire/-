from time import time, sleep
from typing import Dict
import json, warnings
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

try:
    from ......databaseModule.dataBaseEngine import Session, mlMdlBase
except:
    pass

def KBest(data, early_stop=5):
    to_stop = 0
    sbest = 0
    kbest = 1
    for k in range(2, 8):
        estimator = KMeans(n_clusters=k)  # 构造聚类器
        estimator.fit(data)
        sk = silhouette_score(data, estimator.labels_, metric='euclidean')
        if sk > sbest:
            kbest = k
        else:
            to_stop += 1
        if to_stop > early_stop:
            break
    return kbest, estimator

def _get_bole_rule(data, pnames, eps=1e-5):
    center = np.median(data, axis=0)
    radius = 1.5*np.mean((data-center)**2, axis=0)**0.5
    return "(" + " and ".join([f"{c-r}<={p}<={c+r}" for c, r, p in zip(center, radius, pnames)]) + ")"

class BaseModel:
    """故障检测算法的模板（基类）
    """
    def __init__(self, index=0, name="model", pnames=[], component="@", config={}):
        ### 1. 模型的基本信息与核心中间变量的初始化 #################
        self.uuid = index
        self.name = name
        self.pnames = pnames
        self._component, self._obj = map(lambda itm: itm[::-1], component.split("@", 1))
        self.valid_inds = [i for i in range(len(pnames))]
        self._faultLevel = 1
        
        self.trainTime = 0
        self.predictTime = -1
        self.multiTrainTime = 0
        self.multiPredictTime = -1
        
        self.trained = False
        self._histAnom = False
        self._lastAnomTime = -1

        ### 2. 模型的在线/离线窗口配置的缺省值（在外部重写） #######
        self._timeStep = 0.02
        self._maxStep = 20
        self._windowStep = 1
        self._offlineSpanStep = 1

        ### 3. 载入模型的动态配置 ##################################
        self.set_config(config)

        ### 4. 初始化模型的窗口数据缓存 ############################
        self.clearStock()

    def clearStock(self):
        """ [面向在线检测] 窗口数据的缓存域清理"""
        self._dataStock = np.ones((self._windowStep+self._maxStep, len(self.pnames)))*float("nan")
        self._timeStock = []

    def dataStockRefresh(self, dataFrame, time_):
        """ [面向在线检测] 窗口数据的缓存域更新
        [Inputs]
        ` dataFrame : Union(Dict[str, float], Itearable[float]), 输入数据帧的参数数值
                     （可以提供按照键-值对输入的参数数据，也可以提供）
        ` time_: float, 输入数据帧的时间戳
    
        """
        if isinstance(dataFrame, Dict):
            dataFrame = [dataFrame.get(pn, float('nan')) for pn in self.pnames]
        if self._timeStock and \
           time_/self._timeStep - round(self._timeStock[-1]/self._timeStep) < 0.5:
            self._dataStock[-1, ~np.isnan(dataFrame)] = [v for v in dataFrame if not np.isnan(v)]
            self._timeStock[-1] = time_
        else:
            self._dataStock[:-1, :] = self._dataStock[1:,:]
            self._dataStock[-1] = dataFrame
            self._timeStock.append(time_)
            self._timeStock = self._timeStock[-self._windowStep-self._maxStep:]

    @property
    def _config(self):
        if self._configMap is None:
            return {v: getattr(self, k) for k, v in self._configMap}
        else:
            return {k: v for k, v in self.get_config.items() if "_" not in k and any([isinstance(v, typ) for typ in [int, float, str, bool]])}

    @property
    def train_state(self):
        return self.trained

    @property
    def train_info(self):
        """ [面向训练] 获取训练状态(属性)
        [Outputs]
        ` RunTime : float, 已运行时间
        ` RemainTime: float, 预计还需运行时间
    
        """
        return [time() - self.trainTime,
                max(self.predictTime-(time() - self.trainTime), 0.1)]

    @property
    def multi_train_info(self):
        """ [面向训练] 多样本训练模式下的训练状态(属性)
        [Outputs]
        ` RunTime : float, 已运行时间
        ` RemainTime: float, 预计还需运行时间
    
        """
        return [time() - self.multiTrainTime, self.multiPredictTime + self.predictTime]

    @property
    def descript(self):
        return [
            {"name": "算法名称", "value": self._zh_name},
            {"name": "感知深度", "value": self._faultLevel},
            {"name": "涉及部件", "value": self._component},
            {"name": "算法参数", "value": self._config}
            ]

    def get_config(self):
        return {
            "timeStep": self._timeStep, "maxStep": self._maxStep,
            "windowStep": self._windowStep, "offlineSpanStep": self._offlineSpanStep,
            **self.config
            }

    def set_config(self, config={}):
        self._timeStep = config.get("timeStep", self._timeStep)
        self._maxStep = config.get("maxStep", self._maxStep)
        self._windowStep = config.get("windowStep", self._windowStep)
        self._offlineSpanStep = min(
            config.get("offlineSpanStep", self._offlineSpanStep),
            self._windowStep
            )
        self.config = config

    def config_normalization(self, data):
        """ [面向训练] 归一化上下限提取
        [Outputs]
        ` RunTime : float, 已运行时间
        ` RemainTime: float, 预计还需运行时间
        """
        data = data[~np.isnan(data.sum(axis=-1))]
        self.mins = np.min(data,axis=0)
        self.maxs = np.max(data,axis=0)
        self.id_const = np.where(self.maxs == self.mins)[0]
        self.id_nonconst = np.where(self.maxs != self.mins)[0]

    def reconfig_normalization(self, data):
        """ [面向重训练] 归一化上下限重提取
        [Inputs]
        ` dataFrame : numpy.darray, 参数对应的时序
                     （列对于各参数时序，顺序与`self.pnames`一致）
                     （行对于不同时间的参数帧，需要确保时序按照从前到后进行排序）
        """
        data = data[~np.isnan(data.sum(axis=-1))]
        if self.id_const.size:
            mins_ = self.mins[self.id_const]
            maxs_ = self.maxs[self.id_const]
            mins = np.min(data[..., self.id_const],axis=0)
            maxs = np.max(data[..., self.id_const],axis=0)
            mins[mins>mins_] = mins_[mins>mins_]
            maxs[maxs<maxs_] = maxs_[maxs<maxs_]
            min_app = mins_ - mins
            max_app = maxs - maxs_
            min_app[max_app>min_app] = max_app[max_app>min_app]
            self.mins[self.id_const] -= min_app
            self.maxs[self.id_const] += min_app
            self.id_const = np.where(self.maxs == self.mins)[0]
            self.id_nonconst = np.where(self.maxs != self.mins)[0]

    def normalization(self, data):
        """ [面向训练/检测] 归一化参数时序
        [Inputs]
        ` dataFrame : numpy.darray, 参数对应的时序
                     （列对于各参数时序，顺序与`self.pnames`一致）
                     （行对于不同时间的参数帧，需要确保时序按照从前到后进行排序，且采样间隔一致）
        [Outputs]
        ` NormalDataFrame : numpy.darray, 最大-最小值归一化后的参数时序
                     （列对于各参数时序，顺序与`self.pnames`一致）
                     （行对于不同时间的参数帧，需要确保时序按照从前到后进行排序，且采样间隔一致）
        """
        for i in self.id_const:
            data_ = data[:,i]
            data_[~np.isnan(data_)] = 0.5 * np.sign(data[~np.isnan(data_), i]-self.mins[i])
            data[:,i] = data_
        for i in self.id_nonconst:
            data_ = data[:,i]
            data_[~np.isnan(data_)] = (data[~np.isnan(data_), i]  - self.mins[i]) / \
                                            (self.maxs[i] - self.mins[i]) - 0.5
            data[:,i] = data_
        return data

    def anti_normalization(self, data, chosen_ids = None):
        """ [面向训练/检测] 反归一化参数时序
        [Inputs]
        ` dataFrame : numpy.darray, 最大-最小值归一化后参数对应的时序/辅助线时序
                     （列对于各参数时序，顺序与`self.pnames`一致）
                     （行对于不同时间的参数帧，需要确保时序按照从前到后进行排序，且采样间隔一致）
        [Outputs]
        ` DeNormalDataFrame : numpy.darray, 最大-最小值归一化前的参数时序/辅助线时序
                     （列对于各参数时序，顺序与`self.pnames`一致）
                     （行对于不同时间的参数帧，需要确保时序按照从前到后进行排序，且采样间隔一致）
        """
        data_ = data.copy()
        if chosen_ids is None:
            if self.id_const.size:
                data_[..., self.id_const] += self.mins[self.id_const]
            if self.id_nonconst.size:
                data_[..., self.id_nonconst] = (self.maxs[self.id_nonconst] - self.mins[self.id_nonconst]) * \
                    (data_[..., self.id_nonconst] + 0.5)  + self.mins[self.id_nonconst]
        else:
            id_const = [i for i, true_id in enumerate(chosen_ids) if true_id in self.id_const]
            id_nonconst = [i for i, true_id in enumerate(chosen_ids) if true_id in self.id_nonconst]
            if len(id_const):
                data_[..., id_const] += self.mins[id_const]
            if len(id_nonconst):
                data_[..., id_nonconst] = (self.maxs[id_nonconst] - self.mins[id_nonconst]) * \
                    (data_[..., id_nonconst] + 0.5)  + self.mins[id_nonconst]
        return data_

    @staticmethod
    def merged_data(data):
        """[面向数据输入] 多样本合并
        [Inputs]
        ` data : List[np.darray], 多个不等长的参数时序
        [Outputs]
        ` data_: np.darray, 直接拼接而成的时序
        """
        if np.ndim(data[0]) >= 1:
            return data
        data_ = data[0]
        for single_data in data[1:]:
            data_ = np.concatenate((data_,single_data),axis=0)
        return data_

    def windowize(self, data, drop_imcomplet_how=None):
        """[面向数据输入] 输入时序的窗口化处理
        [Inputs]
        ` data : List[np.darray], 多个不等长的参数时序
        ` drop_imcomplet_how: Bool， 是否丢弃末尾不完整时序（否则末尾会自动向前补全时序窗口）
        [Outputs]
        ` data_: np.darray, 不同窗口下时序切片组成的三维数组
        """
        wdata = [data[i:i+self._windowStep] for i in range(0, len(data)-self._windowStep+self._offlineSpanStep, self._offlineSpanStep)]
        endSize = len(wdata[-1])
        if endSize + self._offlineSpanStep <= self._windowStep:
            wdata = wdata[:-1]
        elif endSize < self._windowStep:
            if drop_imcomplet_how:
                wdata = wdata[:-1]
            else:
                wdata[-1] = data[-self._windowStep:]
        return np.array(wdata, dtype="float32")

    def onlineValidate(self, dataFrame, time_):
        """ [面向在线检测] 在线故障检测方法 （Default: 直接利用`self.validate`函数）
        [Inputs]
        ` dataFrame : Union(Dict[str, float], Itearable[float]), 输入数据帧的参数数值
                     （可以提供按照键-值对输入的参数数据，也可以提供）
        ` time_: float, 输入数据帧的时间戳
        [Outputs]
        ` result: Dict, 面向前端显示的在线检测结果
        """
        self.dataStockRefresh(dataFrame, time_)
        score, aidLines, aidLabels = self.singleValidate(pd.DataFrame(self._dataStock).fillna(method="ffill",
                                                                                              limit=self._maxStep).values)        
        if score >= 0.5:
            self._histAnom = True
            self._lastAnomTime = time_
        
        return {
            "detectType": self._algoType,
            "result": {
                "state": score >= 0.5,
                "score": score,
                "histAnom": self._histAnom,
                "lastAnomTime": self._lastAnomTime,
                "component": self._component,
                "faultLevel": self._faultLevel,
                "addLine": [aidLines, aidLabels]
                }
            }
    
    def offlineValidate(self, dataFrames):
        """ [面向离线检测] 离线故障检测方法 （Default: 直接利用`self.validate`函数）
        [Inputs]
        ` dataFrames : numpy.darray, 最大-最小值归一化前参数对应的时序
                     （列对于各参数时序，顺序与`self.pnames`一致）
                     （行对于不同时间的参数帧，需要确保时序按照从前到后进行排序，且采样间隔一致）
        [Outputs]
        ` result: Dict, 面向前端显示的离线线检测结果
        """
        resultList, scoreList, aidLinesList = self.validate(dataFrames)
        return {
            "detectType": self._algoType,
            "resultList": resultList,
            "scoreList": scoreList,
            "descript": self.descript,
            "addLine": aidLinesList,
            }

    ### 在具体项目中，需要根据数据库接口重写
    def save_model(self, count=0, raise_err=False):
        """[面向数据库] 模型参数的储存
        主要提供调用self.to_json()打包模型参数二进制数据储存入uuid所对应的数据中
        """
        try:
            """
            config = self.to_json() #long-blob
            with open(f"{self.uuid}.json", "wb+") as f:
                f.write(config)
            """
            session = Session()
            session.merge(mlMdlBase(obj=self._obj, model_uuid=self.uuid, model_params=self.to_json()))
            session.commit()
            session.close()
        except Exception as e:
            ### 三次写入数据库失败才放弃模型的写入
            if count < 3:
                sleep(1)
                self.save_model(count=count+1)
            if raise_err:
                raise Exception(f"[ERROR] [{self.name}#{self.uuid}]训练阶段保存失败|{e}")
            else:
                warnings.warn(f"[ERROR] [{self.name}#{self.uuid}]训练阶段保存失败|{e}")

    ### 在具体项目中，需要根据数据库接口重写 
    def load_model(self, uuid=None):
        """[面向数据库] 模型参数的读取
        主要负责读取模型参数二进制数据储存入uuid所对应的数据中，调用self.from_json()填充模型参数
        """
        if uuid is None:
            uuid = self.uuid
        session = Session()
        config = session.query(mlMdlBase.model_params).filter(mlMdlBase.model_uuid==uuid).first()
        if config:
            self.from_json(config[0])
            self.trained = True
        else:
            pass
        session.close()
        """
        if uuid is None:
            uuid = self.uuid
        with open(f"{self.uuid}.json", "rb+") as f:
            self.from_json(f.read())
        """


    ## 需要在具体算法中重定义
    def to_json(self):
        """[面向数据库] 模型参数的载入
        将二进制字符流数据解码并载入到模型中
        """
        return json.dumps(self.config).encode()

    ## 需要在具体算法中重定义
    def from_json(self, config=b""):
        """[面向数据库] 模型参数的整理
        将模型重要参数整理编码为二进制字符流数据
        """
        return json.loads(config.decode())

    ## 需要在具体算法中重定义
    def fit(self, data, save=True):
        """面向训练/检测] 反归一化参数时序
        [Inputs]
        ` dataFrame : numpy.darray, 最大-最小值归一化前参数对应的时序
                     （列对于各参数时序，顺序与`self.pnames`一致）
                     （行对于不同时间的参数帧，需要确保时序按照从前到后进行排序，且采样间隔一致）
        """
        ##### 1. 初始化训练信息 #############
        self.trainTime = time()
        self.predictTime = data.size * 0.001 ## 默认算法时间复杂度是O(data.size)

        ##### 2. 配置归一化阈值 #############
        if not self.trained:
            self.config_normalization(data)
        else:
            self.reconfig_normalization(data)

        ##### 3. 数据进行归一化 #############
        X = self.normalization(data)

        ##### 4. 具体算法训练逻辑(必须重写) #
        if not self.trained:
            pass # Insert your pure training algorithm here
        else:
            pass # Replace your reinforce training algorithm here

        ##### 5. 进行模型的状态更新与储存 ###
        self.trained = True
        if save:
            self.save_model()

    ## 需要在具体算法中重定义
    def validate(self, dataFrames):
        """[面向离线检测] 离线故障检测逻辑
        [Inputs]
        ` dataFrames : numpy.darray, 根据批量导入数据
        [Outputs]
        ` scoreList: List[float], 异常指标时序
        ` aidLines: List[List[float]], 各辅助线的时序
        ` labelList: List[str]，各辅助线名称
        """
        ##### 1. 归一化窗口化时序 #########
        data = self.normalization(dataFrames)
        data_ = self.windowize(data)

        ##### 2. 初始化异常指标时序 ########
        scores = np.zeros(len(dataFrames))
        
        ##### 3. 逐窗口进行异常指标更新（必须重写） ########
        for i, dat in enumerate(data_):
            sliceRes = 0 ## Replace By your Slice Detect Logic
            scores[i:i+self._windowStep] = np.minimum(scores[i:i+self._windowStep], sliceRes)

        """对于神经网络而言，可以一次性并行计算异常指标，再填入具体异常指标时序中
        sliceRes = np.zeros(len(data_))## Replace By your Slice Detect Logic
        for i, sco_ in enumerate(sliceRes):
            scores[i:i+self._windowStep] = np.minimum(scores[i:i+self._windowStep], sco_)
        """
        scores[scores > 1] = 1; scores[scores < 0] = 0
        abList = list(np.where(scores>=0.5)[0])
        return abList, list(scores), [None, None]

    ## + 可以在具体算法中重定义
    def singleValidate(self, dataFrames):
        """ [面向在线检测] 在线故障检测逻辑 （Default: 直接利用`self.validate`函数）
        [Inputs]
        ` dataFrames : numpy.darray, 根据模型超参数配置完成窗口化实时更新的多参数时序
        [Outputs]
        ` score: float, 该帧的异常指标
        ` aidPoints: List[float], 该帧的各辅助线数值
        ` labelList: List[str]，该帧的各辅助线名称
        """
        _, scoreList, addativeLowList = self.validate(dataFrames)
        aidLines, labelList = addativeLowList
        if not aidLines is None:
            aidPoints = [aidLine[-1] for aidLine in aidLines]
        else:
            aidPoints = None
        return scoreList[-1], aidPoints, labelList

    def _check_nonvalid(self, data, beta=0.75, ab_min=20):
        abList, scores, _ = self.validate(data)
        if len(abList) > ab_min:
            return abList
        else:
            return []
    
    ## 需要在具体算法中重定义
    def rule_induce(self, data, beta=0.75, eps=1e-5):
        nonvalid = self._check_nonvalid(data, beta=beta)
        if len(nonvalid) == 0:
            return ""
        else:
            anomlyData = data[nonvalid, :]
            normalData = data[[i for i in range(len(data)) if i not in nonvalid], :]
        _, _estimator = KBest(anomlyData, early_stop=3)
        abLabels = _estimator.predict(anomlyData)
        normLabels = _estimator.predict(normalData)
        normLabelsCnt = {l: np.sum(normLabels==l)/normLabels.size for l in np.unique(normLabels)}
        labels = [l if normLabelsCnt.get(l, 0)<1-beta else -1 for l in abLabels]
        print([np.sum(labels==l) for l in np.unique(labels) if l!=-1])
        return " or ".join([_get_bole_rule(anomlyData[labels==l], self.pnames, eps=eps) for l in np.unique(labels) if l != -1 or np.sum(labels==l)/len(labels) > 1 - beta])
