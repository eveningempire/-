from sklearn.neighbors import LocalOutlierFactor
import numpy as np
import pandas as pd
import json

if __name__ == "__main__":
    from support.BaseAlgoClass import BaseModel #基础模型类，构建和训练算法
else:
    from .support.BaseAlgoClass import BaseModel

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def _get_bole_rule(data, trueData, pnames, window, eps=1e-5, anom_ratio=0.2):
    n = int(round(-np.log(eps)/np.log(10)))     #计算整数n格式化输出的阈值
    center = np.median(data, axis=0)
    radius = 3*np.mean((data-center)**2, axis=0)**0.5
    
    return "(" + " and ".join([itm for itm in [
        f"{p}-Mean({p},{window},0)<={round(c+r, n)}" if c+r <0 else f"{p}-Mean({p},{window},0)>={round(c-r, n)}"
        for c, r, p, td in zip(center, radius, pnames, trueData.T) if abs(c)>r and r> eps and \
        ((c+r<0 and np.mean(td<=c+r)<anom_ratio) or (c-r>0 and np.mean(td>=c-r)<anom_ratio))]
                               if itm]) + ")"

def KBest(data, early_stop=5):
    to_stop = 0
    sbest = 0
    kbest = 1
    for k in range(2, 5):
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

class Model(BaseModel):
    def __init__(self, index=0, name="model", window=200, pnames=[], config={}, **kwargs):
        # Algorithm Body - START -> Credit  Configuration
        self._faultLevel = 1
        self._algoType = "LoF"
        self._zh_name = "离群因子检测"
        # Algorithm Body - END -> Credit Configuration
        
        # Algorithm Body - START -> HyperParameters  Configuration
        self.window = window # rocket取200
        self.span = int(self.window/2)
        self.alpha = 0.1
        # Algorithm Body - END  -> HyperParameters Configuration

        super().__init__(index=index, name=name, pnames=pnames, config=config, **kwargs)
    
    def set_config(self, config):
        try:
            self.window = int(config['window'])
        except:
            pass
        try:
            self.span = int(config['span'])
        except:
            pass
        try:
            self.alpha = float(config['alpha'])
        except:
            pass
        super().set_config(config)

    def get_config(self):
        return{"window":self.window,"span":self.span, "alpha":self.alpha}

    def to_json(self): ## An basic component is written by C-language which could be reloaded whiling loading
        return json.dumps([
            self.get_config(),
            list(map(float, self.maxs)), list(map(float, self.mins))
            ]).encode()

    def from_json(self, config=b""):
        config_, maxs, mins = json.loads(config.decode())
        self.maxs = np.array(maxs, dtype="float64")
        self.mins = np.array(mins, dtype="float64")
        self.set_config(config_)

    def fit(self, data, save=False):
        data = pd.DataFrame(self.merged_data(data)).fillna(method="ffill").fillna(method="bfill").values.astype(float)
        data = data[(~np.isnan(data)).any(axis=1)]
        self.config_normalization(data)
        X = self.normalization(data)
        s_diff = self.check_frame(np.diff(X, axis=0), diff_mode=True)
        s_raw = self.check_frame(X)
        credit_diff = max(0, 1 - np.mean(s_diff) - 3*np.std(s_diff)) ## 差分时序的异常分数
        credit_raw = max(0, 1 - np.mean(s_raw) - 3*np.std(s_raw)) ## 正常时序的异常分数
        self.alpha = credit_diff/(credit_diff+credit_raw) if credit_diff+credit_raw > 1e-10 else 0.5
        if save:
            self.save_model()
        self.trained = True

    def check_frame(self, series, diff_mode=False):
        scoresAll = np.ones(series.shape[0])
        XStd = 3*np.std(series, axis=0) #+ np.mean(series, axis=0)
        for i in range(int(np.ceil(series.shape[0]/self.span))):
            startId = i*self.span
            V = series[startId: startId+self.window]
            if V.shape[0] < self.window:
                V = series[-self.window:]
                startId = max(0, series.shape[0] - self.window)
            if np.isnan(V).any():
                scores = np.zeros(self.window)
            else:
                contamination = min(np.mean(np.any(np.abs(V) > XStd, axis=1))*0.8, 0.3)
                # contamination = np.mean(np.any(np.abs(V) > XStd, axis=1))
                # contamination = 0.2
                if contamination == 0:
                    scoresAll[startId:startId+self.window] = 0
                    continue
                elif contamination < 2/self.window and diff_mode:
                    scoresAll[startId:startId+self.window] = 0
                    continue
                # print(contamination)
                clf = LocalOutlierFactor(contamination=contamination)
                clf.fit_predict(V)
                # anom_score =  -anom_score_raw     / -threshold / 2
                scores = clf.negative_outlier_factor_/clf.offset_/2#-0.5
            scores_ = scoresAll[startId:startId+self.window]
            scores[scores_<scores] = scores_[scores_<scores]
            scoresAll[startId:startId+self.window] = scores
        scoresAll = np.where(~np.isnan(scoresAll), scoresAll, 0)
        scoresAll[scoresAll>1] = 1; scoresAll[scoresAll<0] = 0
        #scoresAll_ = np.array(scoresAll_)
        return scoresAll

    def validate(self, data):
        scores = float("nan")*np.ones(data.shape[0], dtype="float32")
        ind = np.where((~np.isnan(data)).any(axis=1))[0]
        X = self.normalization(data[ind])
        scoresAll_ = self.check_frame(np.diff(X, axis=0), diff_mode=True) ## 差分时序的异常分数
        scoresAll = self.check_frame(X) ## 正常时序的异常分数
        ## 主张是通过一个alpha进行加权融合，而不是做最小值融合
        scoresAll[1:-1] = (1-self.alpha)*scoresAll[1:-1] + self.alpha*scoresAll_[1:]*0.5 + self.alpha*scoresAll_[:-1]*0.5
        scoresAll[0] = (1-self.alpha)*scoresAll[0] + self.alpha*scoresAll_[0]*0.5
        scoresAll[-1] = (1-self.alpha)*scoresAll[-1] + self.alpha*scoresAll_[-1]*0.5
        scores[ind] = scoresAll
        scores = np.where(~np.isnan(scores), scores, 0)
        scores[scores > 1] = 1; scores[scores < 0] = 0
        return np.where(scores>=0.5)[0].tolist(), scores.tolist(), [None, None]

    def rule_induce(self, data, beta=0.9, eps=1e-5):
        data_mean = np.array([np.median(data[fid:fid+self.window], axis=0) for fid in range(len(data))], dtype="float32")
        nonvalid = self._check_nonvalid(data, beta=beta)
        if len(nonvalid) == 0:
            return ""
        else:
            X = data - data_mean
            anomlyData = X[nonvalid, :]
            normalData = X[[i for i in range(len(data)) if i not in nonvalid], :]
        _, _estimator = KBest(anomlyData, early_stop=3)
        abLabels = _estimator.predict(anomlyData)
        normLabels = _estimator.predict(normalData)
        normLabelsCnt = {l: np.sum(normLabels==l)/normLabels.size for l in np.unique(normLabels)}
        labels = [l if normLabelsCnt.get(l, 0)<1-beta else -1 for l in abLabels]
        return " or ".join([ itm for itm in [
            _get_bole_rule(anomlyData[labels==l], normalData, self.pnames, window=self.window, eps=eps)
            for l in np.unique(labels) if l != -1 or np.sum(labels==l)/len(labels) > 1 - beta]
                             if itm.replace("()", "")])


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
