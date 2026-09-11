from sklearn.ensemble import IsolationForest
import numpy as np
import pandas as pd
import pickle
from time import time
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

if __name__ == "__main__":
    from support.BaseAlgoClass import BaseModel
else:
    from .support.BaseAlgoClass import BaseModel

def _get_bole_rule(data, trueData, pnames, window, eps=1e-5, anom_ratio=0.2):
    n = int(round(-np.log(eps) / np.log(10)))  # 计算整数n格式化输出的阈值
    center = np.median(data, axis=0)
    radius = 3 * np.mean((data - center) ** 2, axis=0) ** 0.5

    return "(" + " and ".join([itm for itm in [
        f"{p}-Mean({p},{window},0)<={round(c + r, n)}" if c + r < 0 else f"{p}-Mean({p},{window},0)>={round(c - r, n)}"
        for c, r, p, td in zip(center, radius, pnames, trueData.T) if abs(c) > r and r > eps and \
        ((c + r < 0 and np.mean(td <= c + r) < anom_ratio) or (c - r > 0 and np.mean(td >= c - r) < anom_ratio))]
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
    def __init__(self, index=0, name="model", pnames=[], config={}, **kwargs):
        # Algorithm Body - START -> Credit  Configuration
        self._faultLevel = 1
        self._algoType = "iForest"
        self._zh_name = "孤立森林"
        # Algorithm Body - END -> Credit Configuration
        
        # Algorithm Body - START -> HyperParameters  Configuration
        self.random_state = 0
        self.n_estimators = 100
        self.clf = None
        self.window = 50
        # Algorithm Body - END -> HyperParameters  Configuration
        
        super().__init__(index=index, name=name, pnames=pnames, config=config, **kwargs)
    
    
    def set_config(self,config):
        try:
            self.random_state = float(config["random_state"])
        except:
            pass
        try:
            self.n_estimators = int(config["n_estimators"])
        except:
            pass
        super().set_config(config)
    
    def get_config(self):
        return{
            "random_state":self.random_state,"n_estimators":self.n_estimators
            }
        
    def fit(self, data, save=False):
        data = pd.DataFrame(self.merged_data(data)).fillna(method="ffill").fillna(method="bfill").values.astype(np.float64)
        data = data[(~np.isnan(data)).any(axis=1)]
        self.trainTime = time()
        self.predictTime = 0.002 * data.size # follow O(M*N)
        if not self.trained:
            self.config_normalization(data)
            X = self.normalization(data)
            ### X -> Y (PCA(X)) ###
            self._pcaclf = PCA(n_components="mle", svd_solver='auto')
            Y = self._pcaclf.fit_transform(X)
            if Y.size == 0:
                self._pcaclf = None
                Y = X #self._pcaclf.fit_transform(X)
            #######################
            self.clf = IsolationForest(random_state=self.random_state, n_estimators=self.n_estimators, contamination=0.016, max_features=1.0)
            self.clf.fit(Y)
        elif len(self.validate(data)) >= len(data)*0.02:
            self.clf.warm_start = True
            self.reconfig_normalization(data)
            X = self.normalization(data)
            self.clf.n_estimators += min(20, len(X))
            self.clf.fit(X)
        if save:
            self.save_model()
        self.trained = True
            
    def validate(self, data):
        scores = float("nan")*np.ones(data.shape[0], dtype="float32")
        ind = np.where((~np.isnan(data)).any(axis=1))[0]
        X = self.normalization(data[ind])
        ### X -> Y (PCA(X)) ###
        if self._pcaclf is None:
            Y = X
        else:
            Y = self._pcaclf.transform(X)
        #######################
        scores[ind] = 0.5 - 0.5 * self.clf.decision_function(Y)
        scores = np.where(~np.isnan(scores), scores, 0)
        scores[scores > 1] = 1; scores[scores < 0] = 0
        return list(np.where(scores>=0.5)[0]), scores.tolist(), [None, None]

    def to_json(self): ## An basic component is written by C-language which could be reloaded whiling loading
        return pickle.dumps([
            self.random_state, self.n_estimators, self.clf,
            list(map(float, self.maxs)), list(map(float, self.mins))
            ])

    def from_json(self, config=b""):
        self.random_state, self.n_estimators, self.clf, maxs, mins = pickle.loads(config)
        self.maxs = np.array(maxs, dtype="float64")
        self.mins = np.array(mins, dtype="float64")
        self.id_const = np.where(self.maxs == self.mins)[0]
        self.id_nonconst = np.where(self.maxs != self.mins)[0]

    ##### Useless[START] #####
    ## In fact, at saving part, all components' jsonifying are feasible, which is showed in [_display(self)]
    def _get_tree(self, tree):
        baseInfo = [int(tree.n_outputs_), int(tree.max_features_), int(tree.n_features_), [int(n_class) for n_class in tree.n_classes_]]
        featureImportances_ = [float(feature_importance) for feature_importance in tree.feature_importances_]
        treeInfo = [int(tree.tree_.capacity), int(tree.tree_.n_classes), int(tree.tree_.max_depth), int(tree.tree_.n_leaves), int(tree.tree_.node_count)]
        treeFeature = [int(feature) for feature in tree.tree_.feature]
        treeImpurity = [float(impurity) for impurity in tree.tree_.impurity]
        childrenLeft = [int(childleft) for childleft in tree.tree_.children_left]
        childrenRight = [int(childright) for childright in tree.tree_.children_right]
        threshold = [float(thres) for thres in tree.tree_.threshold]
        value = [float(val) for val in tree.tree_.value.flatten()]
        weightedNode = [float(weighted_n_node) for weighted_n_node in tree.tree_.weighted_n_node_samples]
        return {
                "base_info": baseInfo,
                "feature_importances": featureImportances_,
                "tree_info": treeInfo,
                "tree_feature": treeFeature,
                "tree_impurity": treeImpurity,
                "children_left": childrenLeft,
                "children_right": childrenRight,
                "threshold": threshold,
                "value": value,
                "weighted_node": weightedNode
            }

    def _dict2json(self, config):
        return {k: v if not v is None else None for k,v in config.items()}
        
    def _display(self):
        clfParams = [int(self.clf.n_features_), int(self.clf.max_samples_)]
        base_estimator_ = self._dict2json(self.clf.base_estimator_ .get_params())
        estimatorParams = [self._dict2json(tree.get_params()) for tree in self.clf.estimators_]
        estimatorConfig = [self._get_tree(tree)  for tree in self.clf.estimators_]
        return {
                "clf_params": clfParams,
                "base_estimator": base_estimator_,
                "estimator_params": estimatorParams,
                "estimator_config": estimatorConfig
            }
    ##### Useless[END] #####
    def _check_nonvalid(self, data, beta=0.75, ab_min=75):
        abList, _, _ = self.validate(data)
        if len(abList) > ab_min:
            return abList
        else:
            return []
    def rule_induce(self, data, beta=0.75, eps=1e-5):
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
