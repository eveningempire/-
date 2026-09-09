from sklearn.ensemble import AdaBoostClassifier
import numpy as np
import pandas as pd
import pickle
from time import time

if __name__ == "__main__":
    from support.BaseAlgoClass import BaseModel #基础模型类，构建和训练算法
else:
    from .support.BaseAlgoClass import BaseModel

class Model(BaseModel):
    def __init__(self, index=0, name="model", pnames=[], config={}, **kwargs):
        # Algorithm Body - START -> Credit  Configuration
        self._faultLevel = 1
        self._algoType = "AdaBoost"
        self._zh_name = "自主提升算法"
        # Algorithm Body - END -> Credit Configuration

        # Algorithm Body - START -> HyperParameters  Configuration
        self.lr = 0.01
        self.n_estimators = 250
        # Algorithm Body - END -> HyperParameters  Configuration

        super().__init__(index=index, name=name, pnames=pnames, config=config, **kwargs)
        self.clf = AdaBoostClassifier(n_estimators=self.n_estimators, learning_rate=self.lr)

    def set_config(self,config):
        try:
            self.lr = float(config["learning_rate"])
        except:
            pass
        try:
            self.n_estimators = int(config["n_estimators"])
        except:
            pass
        super().set_config(config)

    def get_config(self):
        return{
            "learning_rate":self.lr, "n_estimators":self.n_estimators
            }

    def fit(self, data, save=False):
        data = pd.DataFrame(self.merged_data(data)).fillna(method="ffill").fillna(method="bfill").values.astype(float)
        data = data[(~np.isnan(data)).any(axis=1)]
        self.trainTime = time()
        self.predictTime = 0.002 * data.size # follow O(M*N)
        if not self.trained:
            self.config_normalization(data)
            X = self.normalization(data)
            X_fake_delta = np.random.normal(0, 1, X.shape)
            self.clf.fit(np.append(X, X+X_fake_delta, axis=0), [0 for _ in X]+[1 for _ in X_fake_delta])
        elif len(self.validate(data)) >= len(data)*0.02:
            self.clf.warm_start = True
            self.reconfig_normalization(data)
            X = self.normalization(data)
            X_fake_delta = np.random.normal(
                np.zeros(len(X[0]), dtype="float32"),
                np.std(X, axis=0),
                X.shape
                )
            self.clf.n_estimators += min(20, len(X))
            self.clf.fit(np.append(X, X+X_fake_delta, axis=0), [0 for _ in X]+[1 for _ in X_fake_delta])
        if save:
            self.save_model()
        self.trained = True

    def validate(self, data):
        scores = float("nan")*np.ones(data.shape[0], dtype="float32")
        ind = np.where((~np.isnan(data)).any(axis=1))[0]
        X = self.normalization(data[ind])
        scores[ind] = np.array([pv[1] for pv in self.clf.predict_proba(X)], dtype="float32")
        scores = np.where(~np.isnan(scores), scores, 0)
        scores[scores > 1] = 1; scores[scores < 0] = 0
        return list(np.where(scores>=0.5)[0]), scores.tolist(), [None, None]

    def to_json(self): ## An basic component is written by C-language which could be reloaded whiling loading
        return pickle.dumps([
            self.lr, self.n_estimators, self.clf,
            list(map(float, self.maxs)), list(map(float, self.mins))
            ])

    def from_json(self, config=b""):
        self.lr, self.n_estimators, self.clf, maxs, mins = pickle.loads(config)
        self.maxs = np.array(maxs, dtype="float64")
        self.mins = np.array(mins, dtype="float64")
        self.id_const = np.where(self.maxs == self.mins)[0]
        self.id_nonconst = np.where(self.maxs != self.mins)[0]

if __name__ == "__main__":
    # Test Case 测试用例
    import os
    from support.test_utils import test_process, get_rule
    from pprint import pprint

    ## 验证数据集与参数组合配置
    DIR = "testCaseData"

    ## 算法异常检测性能验证
    print("[Performance]")
    pprint(test_process(Model, [
        #[os.path.join(DIR, 'missile'), ["Vxm","Vym","Vzm","αa","βa","γm","φm","ψm"]],
        #os.path.join(DIR, 'rocket'),
        #os.path.join(DIR, 'ALFA'),
        #os.path.join(DIR, 'KDD99'),
        #os.path.join(DIR, 'MSL'),
        #os.path.join(DIR, 'LSSC'),
        os.path.join(DIR, 'LSSC')
        ], nstep=1))

    ## 算法规则挖掘性能验证
    print("[Rules]")
    pprint(get_rule(Model, [
        #[os.path.join(DIR, 'missile'), ["Vxm","Vym","Vzm","αa","βa","γm","φm","ψm"]],
        #os.path.join(DIR, 'rocket'),
        #os.path.join(DIR, 'ALFA'),
        #os.path.join(DIR, 'KDD99'),
        #os.path.join(DIR, 'MSL'),
        #os.path.join(DIR, 'SMAP'),
        os.path.join(DIR, 'LSSC')
        ], nstep=1))
