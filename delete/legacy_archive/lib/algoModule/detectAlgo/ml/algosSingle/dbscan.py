import os, json, warnings
import numpy as np
import pandas as pd
from time import time

if __name__ == "__main__":
    from support.BaseAlgoClass import BaseModel #基础模型类，构建和训练算法
else:
    from .support.BaseAlgoClass import BaseModel

def _get_rule(nonvalid, valid_ids, pnames, tot_corrIds, tot_reference, thred, eps=1e-5):
    n = int(round(-np.log(eps)/np.log(10)))
    rule = []
    for itm in nonvalid:
        pid_cid, cond_pid = itm
        pid, cid = pid_cid
        p_true_id = valid_ids[pid]
        corr_ids = tot_corrIds[pid]
        corr_true_ids = [corr_ids[j] for j in cond_pid if corr_ids[j] != p_true_id]
        p_reference = tot_reference[pid][cid][corr_ids.index(p_true_id)]
        cond_reference = [tot_reference[pid][cid][j] for j in cond_pid  if corr_ids[j] != p_true_id]
        rule_main = f"{pnames[p_true_id]}>={round(p_reference[1]+thred[p_true_id], n)} or "\
                    f"{pnames[p_true_id]}<={round(p_reference[0]-thred[p_true_id], n)}"
        rule_cond = " and ".join(map(
            lambda itm: f"({pnames[itm[0]]}<={round(itm[1][1]+thred[itm[0]], n)} and "\
                        f"{pnames[itm[0]]}<={round(itm[1][0]-thred[itm[0]], n)})",
            zip(corr_true_ids, cond_reference
                )))
        if not rule_cond:
            rule_m = []
            p_thres_low = np.sort([ref_[corr_ids.index(p_true_id)][0] for ref_ in tot_reference[pid]])
            p_thres_upp = np.sort([ref_[corr_ids.index(p_true_id)][1] for ref_ in tot_reference[pid]])
            if any(p_thres_upp<p_reference[0]):
                p_min = np.max(p_thres_upp[p_thres_upp<p_reference[0]])
                rule_m.append(f"{pnames[p_true_id]}>={round(p_min+thred[p_true_id], n)}")
            if any(p_thres_low>p_reference[1]):
                p_max = np.min(p_thres_upp[p_thres_low>p_reference[1]])
                rule_m.append(f"{pnames[p_true_id]}<={round(p_max-thred[p_true_id], n)}")
            rule_cond = " and ".join(rule_m)
            if rule_cond:
                rule_cond = f"({rule_cond})"
        if rule_cond:
            rule.append(f"(({rule_main}) and {rule_cond})")
        else:
            rule.append(f"({rule_main})")
    return " or ".join(rule)
    ## nonvalid = [(0,0)] ## [("P2", cluster1)]
    ## pnames = ["P1", "P2", "P3"]
    ## valid_ids = [1, 2]
    ## tot_corrIds = [[0,1,2], [2,3]]
    ## tot_reference = [
    ##    [  ## clusters for P2
    ##        [
    ##            [0.1, 0.2], [0.05,0.06], [0.01, 0.02] ## cluster1 for P2
    ##            ],
    ##        [
    ##            [0.3, 0.5], [0.25,0.46], [0.61, 0.72] ## cluster2 for P2
    ##            ],
    ##        ],
    ##    [  ## clusters for P3
    ##        [
    ##          [-0.31, -0.2], [-0.15,-0.06] ## cluster1 for P3
    ##          ],
    ##        [
    ##            [-0.73, -0.5], [-0.65,-0.46] ## cluster2 for P3
    ##            ],
    ##        ],
    ##    ]
    ## thred = [
    ##        [0.01, 0.02, 0.03], ## for P2
    ##        [0.045, 0.1] ## for P3
    ##    ]
    ## =>
    ##       (0,0) = ("P2", cluster1)
    ##              => PARAS = tot_corrIds[0] = [0,1,2] = ["P1", "P2", "P3"]
    ##              => REFERENCE = tot_reference[0][1] = [0.1, 0.2], [0.05,0.06], [0.01, 0.02]
    ##              => THRES = thred[0] = [0.01, 0.02, 0.03]
    ##      => (P2-0.06>0.02 or 0.05-P2>0.02) and (P1-0.2<0.01 and 0.1-P1<0.01) and (P3-0.02<0.03 and 0.01-P1<0.03)

def _get_cossim(quasiCodeJ, codeI, cossim_den):
    codeJ = np.eye(max(quasiCodeJ.max(), 0)+2)[quasiCodeJ,:-1]
    return np.einsum("i->", np.einsum("ij,ik->jk", codeI, codeJ).max(axis=1)) / cossim_den

class Model(BaseModel): # Use Model Template
    def __init__(self, index=0, name="model", pnames=[], config={}, **kwargs):
        # Algorithm Body - START -> Credit  Configuration
        self._faultLevel = 3
        self._algoType = "dbscan"
        self._zh_name = "含噪密度聚类模型"
        # Algorithm Body - END -> Credit Configuration
        
        # Algorithm Body - START -> HyperParameters  Configuration
        self.relation_min = 2
        self.n_neighbors = 5#10
        self.r_noise = 0.75
        self.min_eps = 1e-6
        self.max_ncluster = 20
        self.corr_thres = 0.75
        # Algorithm Body - END -> HyperParameters  Configuration
        
        super().__init__(index=index, name=name, pnames=pnames, config=config, **kwargs)

    def set_config(self,config):
        try:
            self.relation_min = int(round(float(config["relation_min"])))
        except:
            pass
        try:
            self.n_neighbors = int(round(float(config["n_neighbors"])))
        except:
            pass
        try:
            self.r_noise = float(config["r_noise"])
        except:
            pass
        try:
            self.min_eps = float(config["min_eps"])
        except:
            pass
        try:
            self.max_ncluster = int(round(float(config["max_ncluster"])))
        except:
            pass
        try:
            self.corr_thres = float(config["corr_thres"])
        except:
            pass
        super().set_config(config)

    def get_config(self):
        return{
            "relation_min":self.relation_min, "n_neighbors":self.n_neighbors,
            "r_noise":self.r_noise,"min_eps":self.min_eps,
            "max_ncluster":self.max_ncluster,
            "corr_thres":self.corr_thres
            }

    @staticmethod
    def _calcul_corr(groupIds, r_noise=0.2):
        fcnt, pcount = groupIds.shape
        _relatMat = np.zeros([pcount, pcount])
        for i in range(pcount):
            codeI = np.eye(max(groupIds[:, i].max(), 0)+2)[groupIds[:, i],:-1]
            cossim_den = np.sum(codeI)
            if cossim_den < (1-r_noise) * fcnt:
                _relatMat[i,:] = 0
                continue
            for j, quasiCodeJ in enumerate(groupIds.T):
                _relatMat[i,j] = _get_cossim(quasiCodeJ, codeI, cossim_den) ## dependence of j on i
        return _relatMat.T

    def _check_noise_index(self, pId, samp_point, samp_slice, eps_neighors, relation_min=1):
        distance_bool_mat = (np.abs(samp_slice - samp_point) < eps_neighors).astype("int32")
        paramInId = np.where(np.einsum("ij->j", distance_bool_mat)>self.n_neighbors)[0]
        if pId in paramInId or len(paramInId) < relation_min:
            distance_bool_mat = distance_bool_mat[:, paramInId]
            return any(itm >= relation_min for itm in np.einsum("ij->i", distance_bool_mat))
        else:
            return False
               
    def fit(self, data, save=False):
        data = pd.DataFrame(self.merged_data(data)).fillna(method="ffill").fillna(method="bfill").values.astype("float32")
        data = data[(~np.isnan(data)).any(axis=1)]
        """
        N*M (N is frames, M is parameter dimensions)
        """
        self.trainTime = time()  # @Editor: Register Training Start-Time 记录训练开始时间
        # @Editor: Estimated Training Remain-Time 预估训练剩余的训练时间
        self.predictTime = 8e-5 * data.size
        # (P.S. Here, estimated by experiment with Hypothese O(N*M))

        # Initialization Part (Different Modes: Pure Train Mode/Reinforcing Train Mode)
        # @Editor: Use [trained] to distinguish actual mode 通过[trained]区分模型现在的而状态
        if not self.trained:
            self.config_normalization(data)
            X = self.normalization(data)
        else:
            self.reconfig_normalization(data)
            X = self.normalization(data)
            
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            self.cluster_maxs = []
            self.cluster_mins = []
            groupIds = -1 * np.ones(X.shape, dtype="int32")
            interval = int(round(1.2 * self.n_neighbors / (1-self.r_noise)))
            err = np.diff(np.sort(X, axis=0), axis=0)
            for _ in range(3):
                err[np.abs(err)<np.max(np.abs(err))/10] = 0
            eps_neighors = 3 * np.mean(np.maximum(err, self.min_eps)**2, axis=0)**0.5
            slice_time = 8e-5 * data.shape[-1]
            for pId, pVal in list(enumerate(X.T)):
                t = time()
                pSampOrd = np.argsort(pVal)
                groupActId = 0
                for sampId_, rawSampId in enumerate(pSampOrd[interval:]):
                    sampId = sampId_ + interval
                    X_p_slice_pre = X[pSampOrd[sampId - interval: sampId], :]
                    X_p_slice_post = X[pSampOrd[sampId + 1: sampId + interval + 1], :]
                    X_p_point = pVal[rawSampId]
                    if self._check_noise_index(pId, X_p_point, X_p_slice_pre, eps_neighors, relation_min=self.relation_min):
                        groupIds[rawSampId, pId] = groupActId
                    elif sampId < pSampOrd.size - interval and self._check_noise_index(pId, X_p_point, X_p_slice_post, eps_neighors, relation_min=self.relation_min) :
                        groupActId += 1
                        groupIds[rawSampId, pId] = groupActId
                    if groupActId > self.max_ncluster:
                        break

                if groupActId > self.max_ncluster:
                    _relation_min = 1
                    pSampOrd = np.argsort(pVal)
                    groupIds[:, pId] = -1
                    groupActId = 0
                    for sampId_, rawSampId in enumerate(pSampOrd[interval:]):
                        sampId = sampId_ + interval
                        X_p_slice_pre = X[pSampOrd[sampId - interval: sampId], :]
                        X_p_slice_post = X[pSampOrd[sampId + 1: sampId + interval + 1], :]
                        X_p_point = pVal[rawSampId]
                        if sampId < pSampOrd.size - interval and not self._check_noise_index(pId, X_p_point, X_p_slice_post, eps_neighors, relation_min=1):
                            continue
                        elif not self._check_noise_index(pId, X_p_point, X_p_slice_pre, eps_neighors, relation_min=1):
                            if sampId < pSampOrd.size - interval:
                                groupActId += 1
                                groupIds[rawSampId, pId] = groupActId
                        else:
                            groupIds[rawSampId, pId] = groupActId
                else:
                    _relation_min = self.relation_min
                            
                for sampId_, rawSampId in enumerate(pSampOrd[:interval]):
                    sampId = sampId_
                    X_p_slice_post = X[pSampOrd[sampId + 1: sampId + interval + 1], :]
                    X_p_point = pVal[rawSampId]
                    if  self._check_noise_index(pId, X_p_point, X_p_slice_post, eps_neighors, relation_min=_relation_min):
                        groupIds[rawSampId, pId] = 0
                            
                group_min = {}
                group_max = {}
                for groupId in range(groupActId+1):
                    if any(groupIds[:, pId]==groupId):
                        group_min[groupId] = float(pVal[groupIds[:, pId]==groupId].min() - eps_neighors[pId])
                        group_max[groupId] = float(pVal[groupIds[:, pId]==groupId].max() + eps_neighors[pId])
                self.cluster_mins.append(group_min)
                self.cluster_maxs.append(group_max)
                slice_time = 0.15*slice_time + 0.85*(time() - t)
                self.predictTime = (data.shape[-1]-pId) * slice_time
            self.thres = eps_neighors
            self.corr_mat = self._calcul_corr(groupIds, self.r_noise)
            self.valid_ids, self.tot_corrIds, self.tot_reference = self._getRef(self.cluster_mins, self.cluster_maxs,
                                                                                groupIds, self.corr_mat,
                                                                                self.corr_thres, self.r_noise)
        if save:
            self.save_model()  # @Editor: Save model 保存模型
        self.trained = True  # @Editor: To refresh Training State 刷新模型训练状态


    @staticmethod
    def _getRef(cluster_mins, cluster_maxs, groupIds, corr_mat, corr_thres=0.6, r_noise=0.2):
        valid_ids = []
        tot_corrIds = []
        tot_reference = []
        for pId in range(corr_mat.shape[1]):
            if corr_mat[pId, pId] < corr_thres or \
               np.sum(groupIds[:,pId]==-1)/groupIds.shape[0] > r_noise:
                continue
            corrIds = np.where(corr_mat[pId, :] > corr_thres)[0].tolist()
            reference = []; aidRef = set()
            for itm in groupIds[:, corrIds]:
                if any(map(lambda it: it==-1, itm)):
                    continue
                tag = "|".join(map(str, itm))
                if tag in aidRef:
                    continue
                aidRef.add(tag)
                reference.append([
                    [
                        cluster_mins[corrIds[pId_]][cId_] if cId_ != -1 else min(cluster_mins[corrIds[pId_]].values()),
                        cluster_maxs[corrIds[pId_]][cId_] if cId_ != -1 else max(cluster_maxs[corrIds[pId_]].values())
                        ] for pId_, cId_ in enumerate(itm)
                    ])
                
            if reference:
                valid_ids.append(pId)
                tot_corrIds.append(corrIds)
                tot_reference.append(np.array(reference, dtype="float32"))
        return valid_ids, tot_corrIds, tot_reference

    def _single_validate(self, V, inner=False):
        if not inner:
            V = self.normalization([V])[0]
        subD = np.array(V, dtype="float32")
        supD = np.array(V, dtype="float32")
        for i, p in enumerate(self.valid_ids):
            corrIds = self.tot_corrIds[i]
            reference = self.tot_reference[i]
            cond_cnt = np.sum(np.maximum(reference[:,:,0] - V[corrIds], V[corrIds] - reference[:,:,1]) <= self.thres[corrIds], axis=1)
            dis_raw = np.maximum(0, np.maximum(reference[:,corrIds.index(p),0] - V[p], V[p] - reference[:,corrIds.index(p),1]))
            dis = 1 - np.exp(-dis_raw)/(1+np.exp(-dis_raw))
            c_id = np.argmax(cond_cnt+dis)
            subD_, supD_ = reference[c_id][corrIds.index(p)]
            subD[p] = subD_
            supD[p] = supD_
        score = max(0, np.max(np.maximum(subD-V, V-supD)/(self.thres*2)))
        return score, (subD-self.thres).tolist(), (supD+self.thres).tolist()

    def validate(self, data):
        scores = float("nan")*np.ones(data.shape[0], dtype="float32")
        subData = float("nan")*np.ones(data.shape, dtype="float32")
        supData = float("nan")*np.ones(data.shape, dtype="float32")
        ind = np.where((~np.isnan(data)).any(axis=1))[0]
        X = self.normalization(data[ind])
        # Algorithm Body - START
        abList = []
        for frame, V in enumerate(X):
            score, sub, sup = self._single_validate(V, inner=True)
            subData[ind[frame], :] = sub
            supData[ind[frame], :] = sup
            scores[ind[frame]] = score
            if np.any(score >= 0.5):
                abList.append(ind[frame])
        # Algorithm Body - END
        # @Editor: return List[anomalies' frame(index)], List[anomaly-score of each frame] 返回异常帧序号的列表和各帧异常分数的列表
        subData = [list(map(float, subD_)) for subD_ in self.anti_normalization(np.array(subData, dtype="float32")).T]
        supData = [list(map(float, supD_)) for supD_ in self.anti_normalization(np.array(supData, dtype="float32")).T]
        scores = np.where(~np.isnan(scores), scores, 0)
        scores[scores > 1] = 1; scores[scores < 0] = 0
        return abList, scores.tolist(), [list(zip(subData, supData)), ["下阈值", "上阈值"]]
        #    P.S. 0.5 as a common jungle for anomaly score, i.e. 0~0.5 as normaly while 0.5~1 as anomaly, 异常分数统一以0.5为判据(即0~0.5一下是正常，0.5~1是异常)

    def to_json(self):
        """
        Load Special Configurations By Path
        """
        return json.dumps({
            "dbscan_info": self.get_config(),
            "cluster_mins": self.cluster_mins,
            "cluster_maxs": self.cluster_maxs,
            "corr_mat": self.corr_mat.tolist(),
            "thres": self.thres.tolist(),
            "valid_ids": self.valid_ids,
            "tot_corrIds": self.tot_corrIds,
            "tot_reference": [itm.tolist() for itm in self.tot_reference],
            "mins": self.mins.tolist(),
            "maxs": self.maxs.tolist()
        }).encode()

    def from_json(self, configJson=b""):
        """
        Load Special Configurations By Path
        """
        config = json.loads(configJson.decode())
        self.set_config(config['dbscan_info'])
        self.cluster_mins = config["cluster_mins"]
        self.cluster_maxs = config["cluster_maxs"]
        self.corr_mat = np.array(config["corr_mat"])
        self.thres = np.array(config["thres"])
        self.valid_ids = config["valid_ids"]
        self.tot_corrIds = config["tot_corrIds"]
        self.tot_reference = [np.array(itm, dtype="float32") for itm in config["tot_reference"]]
        self.mins = np.array(config["mins"])
        self.maxs = np.array(config["maxs"])

        # To calculate some latent parameters which could be deducated from the former parameters
        self.id_const = np.where(self.maxs == self.mins)[0]
        self.id_nonconst = np.where(self.maxs != self.mins)[0]
        
    def _check_nonvalid(self, data, beta=0.75, ab_min=100):
        if len(self.valid_ids):
            scores = []
            res = {}
            cond = {}
            for frame, V in enumerate(self.normalization(data)):
                score = []
                subD = np.array(V, dtype="float32")
                supD = np.array(V, dtype="float32")
                for i, p in enumerate(self.valid_ids):
                    corrIds = self.tot_corrIds[i]
                    reference = self.tot_reference[i]
                    cond_cnt = np.sum(np.maximum(reference[:,:,0] - V[corrIds], V[corrIds] - reference[:,:,1]) <= self.thres[corrIds], axis=1)
                    dis_raw = np.maximum(0, np.maximum(reference[:,corrIds.index(p),0] - V[p], V[p] - reference[:,corrIds.index(p),1]))
                    dis = 1 - np.exp(-dis_raw)/(1+np.exp(-dis_raw))
                    c_id = np.argmax(cond_cnt+dis)
                    subD_, supD_ = reference[c_id][corrIds.index(p)]
                    if subD_ - V[p] >= self.thres[p] or V[p] - supD_ >= self.thres[p]:
                        if (i, c_id) in res.keys():
                            res[(i, c_id)] += 1
                            for j, p_ in enumerate(corrIds):
                                subD_j, supD_j = reference[c_id][j]
                                cond[(i, c_id)][j] += int(subD_j - V[p_] >= self.thres[p_] or V[p_] - supD_j >= self.thres[p_])
                        else:
                            res[(i, c_id)] = 1
                            cond[(i, c_id)]= [
                                int(reference[c_id][j][0] - V[p_] >= self.thres[p_] or V[p_] - reference[c_id][j][1] >= self.thres[p_])
                                for j, p_ in enumerate(corrIds)
                                ]
                        score.append(1)
                    else:
                        score.append(0)
                scores.append(score)
                    
            scores = np.array(scores, dtype="int8")
            ab_freq = (scores >= 0.5).max(axis=1).sum(axis=0)
            if ab_freq > min(ab_min, 0.1*len(data)):
                criteria = min(ab_freq, max(res.values()))/3
                return [(itm, [cpid for cpid, cnd in enumerate(cond[itm]) if cnd/freq>beta]) for itm, freq in res.items() if freq > criteria]
            else :
                return []
        else:
            return []

    def _ref_anti_normalization(self, tot_ref, tot_corr):
        tot_ref_upp = tot_ref[:,:,0]
        tot_ref_low = tot_ref[:,:,1]
        tot_ref_upp_ = self.anti_normalization(tot_ref_upp, tot_corr)
        tot_ref_low_ = self.anti_normalization(tot_ref_low, tot_corr)
        return np.append(tot_ref_upp_[:,:,None], tot_ref_low_[:,:,None], axis=-1)
        
    def rule_induce(self, data, beta=0.75, eps=1e-5):
        nonvalid = self._check_nonvalid(data, beta=beta)
        tot_reference = [self._ref_anti_normalization(tot_ref, tot_corr) for tot_corr, tot_ref in zip(self.tot_corrIds, self.tot_reference)]
        return _get_rule(nonvalid, self.valid_ids, self.pnames, self.tot_corrIds, tot_reference, self.thres, eps=eps)

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
