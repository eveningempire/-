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
        score_bound_lower = np.min(scores)
        if score_bound_lower <0.5:
            scores[scores<0.5] = np.maximum(0, scores[scores<0.5]-score_bound_lower)/(0.5-score_bound_lower)
        score_index.append(_auc_calculate(scores, _test_label, n_bins=n_bins))
    score_index = np.array(score_index, dtype="float32")
    socre_w = np.exp(score_index)
    socre = np.sum(socre_w*score_index)/socre_w.sum()
    return model, socre

class Model:
    def __init__(self, **kwargs):
        self._config_args = {k:v for k,v in kwargs.items() if k !="algoname"}
        self.algoname = kwargs.get("algoname")
        self.component = kwargs.get("component")
        self.mdl_best_thres = kwargs.get("mdl_best_thres", 0.45)
        if self.algoname:
            self._model = getattr(algos, self.algoname).Model(**self._config_args)
        else:
            self._model = None
        
        self.trainTime = 0
        self.predictTime = -1
        self.trained = False

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
        self.trainTime = time()  # @Editor: Register Training Start-Time 记录训练开始时间
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
                t = time()
                if isinstance(train_data, list):
                    ind = 0
                    for td in train_data:
                        mdl, ind_ = _evaluateMdl(getattr(algos, algoname).Model(**self._config_args), td)
                        ind += ind_
                    ind /= len(train_data)
                else:
                    mdl, ind = _evaluateMdl(getattr(algos, algoname).Model(**self._config_args), train_data)
                if ind > score_best:
                    mdl_best = mdl
                    score_best = ind
                    self.algoname = algoname
                slice_time = 0.15*slice_time + 0.85*(time() - t)
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
            if isinstance(train_data, list):
                for tdid, td in enumerate(train_data):
                    self._model.fit(td, save=(save and (tdid==len(train_data)-1)))
            else:
                self._model.fit(train_data, save=save)
        
if __name__ == "__main__":
    TEST_MODE = True
    
    # Test Case 测试用例
    import pandas as pd
    import os
    
    DIR = r"algos\testCaseData"
    paras = ["Vxm","Vym","Vzm","αa","βa","γm","φm","ψm"]
    train_data = pd.read_csv(os.path.join(DIR, 'data.csv'), index_col=0, encoding="gbk").fillna(method="ffill", limit=5)
    train_data = train_data.loc[::20, paras].values.astype("float32")

    mdl = Model() 
    mdl.fit(train_data)
