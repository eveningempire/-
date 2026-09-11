from typing import Any
from sklearn.model_selection import KFold
import numpy as np
from time import time

if __name__ == "__main__":
    TEST_MODE = True
else:
    TEST_MODE = False

if TEST_MODE:
    import algos
    from algos import *
else:
    from . import algos
    from .algos import *

def _auc_calculate(preLabel, realLabel, n_bins=10):
    preLabel = np.array(preLabel, dtype="float32")
    realLabel = np.array(realLabel, dtype="float32")
    postive_len = np.sum((realLabel <= 0.5))   #正样本数量（因为正样本都是1）
    negative_len = np.sum((realLabel > 0.5)) #负样本数量
    total_case = postive_len * negative_len #正负样本对
    pos_histogram = [0 for _ in range(n_bins)] 
    neg_histogram = [0 for _ in range(n_bins)]
    bin_width = 1.0 / n_bins
    for pv, rv in zip(preLabel, realLabel):
        nth_bin = min(int(pv/bin_width), n_bins-1)
        if rv == 1:
            pos_histogram[nth_bin] += 1
        else:
            neg_histogram[nth_bin] += 1
    accumulated_neg = 0
    satisfied_pair = 0
    for i in range(n_bins):
        satisfied_pair += (pos_histogram[i]*accumulated_neg + pos_histogram[i]*neg_histogram[i]*0.5)
        accumulated_neg += neg_histogram[i]
    return min(1, max(0, satisfied_pair / float(total_case))) if float(total_case) != 0 else 0

def _evaluateMdl(model, valid_data, eps=1e-6, n_bins=10):
    score_index = []
    for train_index, test_index in KFold(n_splits=5).split(valid_data):
        _train_data = valid_data[train_index] # 本组训练集
        _test_data = valid_data[test_index] # 本组验证集
        _test_anom_ind = np.random.permutation(len(_test_data))[:len(_test_data)//3]
        noise = np.random.uniform(5, 10, [_test_anom_ind.size, len(_test_data[0])])
        _test_data[_test_anom_ind] += np.std(_test_data, axis=0) * noise
        _test_label = np.zeros(len(_test_data))
        _test_label[_test_anom_ind] = 1
        model.fit(_train_data, save=False)
        _, scores, _ = model.validate(_test_data)
        scores = np.array(scores, dtype="float32")
        if np.ndim(scores) == 2:
            scores = np.max(scores, axis=1)
        score_bound_lower = np.min(scores)
        if score_bound_lower <0.5:
            scores[scores<0.5] = np.maximum(0, scores[scores<0.5]-score_bound_lower)/(0.5-score_bound_lower)
        score_index.append(_auc_calculate(scores, _test_label, n_bins=n_bins))
    score_index = np.array(score_index, dtype="float32")
    socre_w = np.exp(score_index)
    socre = np.sum(socre_w*score_index)/socre_w.sum()
    return model, socre

SPAN_INVALID = 500
SPAN_VALID = 20

import time, warnings
try:
    from ....databaseModule.dataBaseEngine import Session, mlMdlBase
except:
    pass

SPLIT_SPEC_SEQUENCE = "||<-EPC_subete_wa_unmeiseki_no_tobira_no_sentaku_desu_EPC->||".encode()

class EnsembleModel:
    def __init__(self, modelGenerator=None, select_proba=0.2):
        self._modelGenerator= modelGenerator
        self._select_proba = select_proba
        self._models = []

    def __getattr__(self, name):
        if self._models:
            if name == "_model":
                return self._model[0]
            return getattr(self._models[0], name)
        else:
            if name == "_model":
                return self._modelGenerator()
            return getattr(self._modelGenerator(), name)
        
    def set_rl(self):
        for mdl in self._models:
            mdl.trained = False
        
    def fit(self, data, save=False):
        data_slice = []
        inds = np.where(np.abs(np.where(~np.isnan(data), data, 0)).sum(axis=1) > 1e-10)[0]
        inds_inds = np.sort(np.unique(np.where(np.diff(inds) > SPAN_INVALID)[0].tolist()+[len(inds)-1]))
        sindind = 0
        for ind in inds_inds:
            sind = inds[min(sindind, len(inds)-1)]
            eind = inds[min(ind, len(inds)-1)] + 1
            sindind = ind + 1
            if eind - sind < SPAN_VALID:
                continue
            data_slice.append(data[sind:eind])
        data_slice.append(data)
        for data_itm in data_slice:
            for mdl in self._models:
                ablist, _, _ = mdl.validate(data_itm)
                if len(ablist)/len(data_itm) <= self._select_proba:
                    mdl.fit(data_itm)
                    break
            else:
                self._models.append(self._modelGenerator())
                self._models[-1].fit(data_itm)
                if len(self._models[-1].valid_inds) == 0:
                    self._models.pop(-1)
        if self._models:
            valid_inds = set(self._models[0].valid_inds)
            for mdl in self._models[1:]:
                valid_inds &= set(mdl.valid_inds)
            self.valid_inds = sorted(self.valid_inds)
        if save:
            self.save_model()

    def validate(self, data):
        scores = None
        ablist = []
        suppValues = None
        suppLabel = None
        inds = np.where(np.abs(np.where(~np.isnan(data), data, 0)).sum(axis=1) > 1e-10)[0]
        inds_inds = np.sort(np.unique(np.where(np.diff(inds) > SPAN_INVALID)[0].tolist()+[len(inds)-1]))
        sindind = 0
        for ind in inds_inds:
            sind = inds[min(sindind, len(inds)-1)]
            eind = inds[min(ind, len(inds)-1)] + 1
            sindind = ind + 1
            if eind - sind < SPAN_VALID:
                continue
            if len(self._models) == 0:
                break
            scores_slice_match = []
            for mdl in self._models:
                if len(self.valid_inds) == 0:
                    ablist_itm = []
                else:
                    _, scores_itm, _ = mdl.validate(data[sind:eind])
                    if (isinstance(scores_itm[0], list) and len(scores_itm[0]) < len(self.valid_inds) ) or np.ndim(scores_itm) == 1:
                        ablist_itm = np.where(np.max(np.array(scores_itm, dtype="float32")[:], axis=-1) > 0.5)[0]
                    else:
                        ablist_itm = np.where(np.max(np.array(scores_itm, dtype="float32")[:,self.valid_inds], axis=-1) > 0.5)[0]
                scores_slice_match.append(len(ablist_itm)/len(data[sind:eind]))
            if len(self.valid_inds) == 0:
                scores_ = np.zeros(data.shape, dtype="float32")
                supValues_ = (None, None)
            else:
                if np.ndim(scores_slice_match) == 1:
                    mdl_id = np.argmin(scores_slice_match)
                else:
                    mdl_id = np.argmin(np.max(scores_slice_match, axis=-1))
                _, scores_, supValues_ = self._models[mdl_id].validate(data[sind:eind])
            scores_res, scores_ = np.array(scores_, dtype="float32"), np.zeros(np.shape(scores_), dtype="float32")
            if len(self.valid_inds) == 0:
                ablist_ = []
            else:
                if np.ndim(scores_) == 2:
                    ablist_ = np.where(np.max(scores_res[:,self.valid_inds], axis=-1) > 0.5)[0]
                else:
                    ablist_ = np.where(scores_res > 0.5)[0]
                if np.ndim(scores_) == 2:
                    scores_[:, self.valid_inds] = scores_res[:, self.valid_inds]
                else:
                    scores_ = scores_res
            suppValue_, suppLabel = supValues_
            ablist.extend([itm+sind for itm in ablist_])
            if scores is None:
                if np.ndim(scores_) == 2:
                    scores = float("nan") * np.ones([len(data), len(scores_[0])], dtype="float32")
                else:
                    scores = float("nan") * np.ones(len(data), dtype="float32")
                if not suppValue_ is None:
                    np_, ns, _ = np.shape(suppValue_)
                    suppValues = float("nan") * np.ones([np_, ns, len(data)], dtype="float32")
            if not suppValue_ is None:
                suppValues[:, :, sind:eind] = suppValue_
            scores[sind:eind] = scores_
        scores = np.where(~np.isnan(scores), scores, 0) if not scores is None else np.zeros(len(data), dtype="float32")
        scores[scores<0] = 0; scores[scores>1] = 1
        return ablist, scores.tolist(), [(suppValues.tolist() if not suppValues is None else None), suppLabel]

    ### [照旧] 在具体项目中，需要根据数据库接口重写 
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
                time.sleep(1)
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

    ### [照旧] 在具体项目中，需要根据数据库接口重写 
    def to_json(self):
        """[面向数据库] 模型参数的载入
        将二进制字符流数据解码并载入到模型中
        """
        return SPLIT_SPEC_SEQUENCE.join([mdl.to_json() for mdl in self._models])

    ## 需要在具体算法中重定义
    def from_json(self, config=b""):
        """[面向数据库] 模型参数的整理
        将模型重要参数整理编码为二进制字符流数据
        """
        self._models = []
        for params in config.split(SPLIT_SPEC_SEQUENCE):
            self._models.append(self._modelGenerator())
            self._models[-1].from_json(params)
        if self._models:
            valid_inds = set(self._models[0].valid_inds)
            for mdl in self._models[1:]:
                valid_inds &= set(mdl.valid_inds)
            self.valid_inds = sorted(self.valid_inds)

    ## 需要在具体算法中重定义
    def rule_induce(self, data, beta=0.75, eps=1e-5):
        data_slice = []
        inds = np.where(np.abs(np.where(~np.isnan(data), data, 0)).sum(axis=1) > 1e-10)[0]
        inds_inds = np.sort(np.unique(np.where(np.diff(inds) > SPAN_INVALID)[0].tolist()+[len(inds)-1]))
        sindind = 0
        for ind in inds_inds:
            sind = inds[min(sindind, len(inds)-1)]
            eind = inds[min(ind, len(inds)-1)] + 1
            sindind = ind + 1
            if eind - sind < SPAN_VALID:
                continue
            data_slice.append(data[sind:eind])
        rules = []
        for data_itm in data_slice:
            scores = []
            for mdl in self._models:
                if len(self.valid_inds) == 0:
                    ablist = []
                else:
                    _, scores_, _ = mdl.validate(data_itm)
                    if (isinstance(scores_[0], list) and len(scores_[0]) < len(self.valid_inds) ) or np.ndim(scores_) == 1:
                        ablist = np.where(np.max(np.array(scores_, dtype="float32")[:], axis=-1) > 0.5)[0]
                    else:
                        ablist = np.where(np.max(np.array(scores_, dtype="float32")[:,self.valid_inds], axis=-1) > 0.5)[0]
                    # ablist = np.where(np.max(np.array(scores_, dtype="float32")[:,self.valid_inds], axis=-1) > 0.5)[0]
                scores.append(len(ablist)/len(data_itm))
            if len(self.valid_inds) != 0:
                mdl_id = np.argmin(scores)
                rules.append(self._models[mdl_id].rule_induce(data_itm))
        return " or ".join([rule for rule in rules if rule])

class Model:
    def __init__(self, **kwargs):
        self._config_args = {k:v for k,v in kwargs.items() if k !="algoname"}
        self.algoname = kwargs.get("algoname")
        self.component = kwargs.get("component")
        self.mdl_best_thres = kwargs.get("mdl_best_thres", 0.45)
        if self.algoname:
            def gene():
                return getattr(algos, self.algoname).Model(**self._config_args)
            self._model = EnsembleModel(gene)
        else:
            self._model = None
        
        self.trainTime = 0
        self.predictTime = -1
        self.multiTrainTime = 0
        self.multiPredictTime = -1

        self.algosOptions = self.get_algos()

    @staticmethod
    def get_algos():
        algosOptions = []
        for algoname in algos.__all__:
            mdl = getattr(algos, algoname).Model()
            algosOptions.append({
                "key": algoname,
                "name": mdl._algoType,
                "zh_name": mdl._zh_name
                })
        return algosOptions

    def get_config(self):
        return {"algoname": self.algoname, "configs": self._model.get_config()}

    def set_config(self, config={}):
        self.algoname = config.get("algoname", self.algoname)
        if self.algoname:
            self._model = getattr(algos, self.algoname).Model(**self._config_args)
            self._model.set_config(config.get("configs", {}))

    def __getattr__(self, method):
        return getattr(self._model, method)
    
    def fit(self, train_data, model_rl=False, save=False, verbose=False):
        self.trainTime = time.time()  # @Editor: Register Training Start-Time 记录训练开始时间
        # @Editor: Estimated Training Remain-Time 预估训练剩余的训练时间
        if isinstance(train_data, list):
            datasize = sum([d.size for d in train_data])
        else:
            datasize = train_data.size
        self.predictTime = 8e-5 * datasize * (len(self.algosOptions)+1)
        slice_time = 8e-5 * datasize
        
        if self._model is None:
            score_best = -1; mdl_best = None
            for algoId, algoname in enumerate(algos.__all__):
                t = time.time()
                def gene():
                    return getattr(algos, algoname).Model(**self._config_args)
                if isinstance(train_data, list):
                    ind = 0
                    for td in train_data:
                        mdl = EnsembleModel(gene)
                        mdl, ind_ = _evaluateMdl(mdl, td)
                        ind += ind_
                    ind /= len(train_data)
                else:
                    mdl = EnsembleModel(gene)
                    mdl, ind = _evaluateMdl(Model(algoname=self.algoname, **self._config_args), train_data)
                if ind > score_best:
                    mdl_best = mdl._model
                    score_best = ind
                    self.algoname = algoname
                slice_time = 0.15*slice_time + 0.85*(time.time() - t)
                self.predictTime = ((len(self.algosOptions)+1)-algoId) * slice_time
            if verbose:
                print(f"{algoname}: {round(ind*100, 2)}")
            if not mdl_best is None and score_best > self.mdl_best_thres:
                if isinstance(train_data, list):
                    for tdid, td in enumerate(train_data):
                        self._model = mdl_best
                        self._model_score = score_best 
                        self._model.fit(td, save=(save and (tdid==len(train_data)-1)))
                else:
                    self._model = mdl_best
                    self._model.fit(train_data, save=save)
        else:
            if not model_rl:
                self._model.set_rl()
            if isinstance(train_data, list):
                for tdid, td in enumerate(train_data):
                    self._model.fit(td, save=(save and (tdid==len(train_data)-1)))
            else:
                self._model.fit(train_data, save=save)
        
if __name__ == "__main__":
    TEST_MODE = True
    print(algos.__all__)
    print(getattr(algos,'dbscan'))
    # Test Case 测试用例
    import pandas as pd
    import os
    
    DIR = r"algos\testCaseData"
    paras = ["Vxm","Vym","Vzm","αa","βa","γm","φm","ψm"]
    train_data = pd.read_csv(os.path.join(DIR, 'data.csv'), index_col=0, encoding="gbk").fillna(method="ffill", limit=5)
    train_data = train_data.loc[::20, paras].values.astype("float32")

    mdl = Model() 
    mdl.fit(train_data)
