import os, json
import numpy as np
import pandas as pd
from time import time

if __name__ == "__main__":
    from support.BaseAlgoClass import BaseModel
else:
    from .support.BaseAlgoClass import BaseModel

class Model(BaseModel): # Use Model Template
    def __init__(self, index=0, name="model", pnames=[], config={}, **kwargs):
        # Algorithm Body - START -> Credit  Configuration
        self._faultLevel = 1
        self._algoType = "ims"
        self._zh_name = "归纳监视系统"
        # Algorithm Body - END -> Credit Configuration
        
        # Algorithm Body - START -> HyperParameters  Configuration，超参数
        self.initial_dist_threshold = 0.05     #创建新簇时，簇上下限初始值
        self.expansion_rate = 0.001       #簇增长百分比
        self.incorporate_dist_threshold = 0.01  #簇膨胀系数
        self.temporalView = 10
        self.thred = 1.5*self.incorporate_dist_threshold      #检测阈值，3sigama准则
        # Algorithm Body - END  -> HyperParameters Configuration
        
        super().__init__(index=index, name=name, pnames=pnames, config=config, **kwargs)

    def set_config(self,config):
        try:
            self.initial_dist_threshold = float(config["initial_dist_threshold"])
        except:
            pass
        try:
            self.expansion_rate = float(config["expansion_rate"])
        except:
            pass
        try:
            self.incorporate_dist_threshold = float(config["incorporate_dist_threshold"])
        except:
            pass
        try:
            self.thred = float(config["thred"])
        except:
            pass
        try:
            self.temporalView = float(config["temporalView"])
        except:
            pass
        self._windowStep = self.temporalView  #窗口大小
        self._offlineSpanStep = 1 #窗口步进
        super().set_config(config)

    def get_config(self):
        return{
            "initial_dist_threshold":self.initial_dist_threshold,
            "expansion_rate":self.expansion_rate,
            "incorporate_dist_threshold":self.incorporate_dist_threshold,
            "thred":self.thred,
            "temporalView": self.temporalView,
            }


    def _check_noise_index(self, pId, samp_point, samp_slice, eps_neighors, relation_min=1):
        distance_bool_mat = (np.abs(samp_slice - samp_point) < eps_neighors).astype("int32")
        paramInId = np.where(np.einsum("ij->j", distance_bool_mat)>self.n_neighbors)[0]
        if pId in paramInId or len(paramInId) < relation_min:
            distance_bool_mat = distance_bool_mat[:, paramInId]
            return any(itm >= relation_min for itm in np.einsum("ij->i", distance_bool_mat))
        else:
            return False
               
    def fit(self, data, save=False):
        data = pd.DataFrame(self.merged_data(data)).fillna(method="ffill").fillna(method="bfill").values.astype(np.float64)
        #data = np.diff(data, axis=0)
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
            # @ Editor: Design for Pure Train Mode with a non-trained model 为未训练过的模型的纯训练模式作出具体的设计
            self.config_normalization(data)
            X = self.normalization(data)
        else:
            # @ Editor: Design for Reinforcing Train Mode with a trained model 为训练过的模型的增强训练模式作出具体的设计
            self.reconfig_normalization(data)
            X = self.normalization(data)

        _offlineSpanStep, self._offlineSpanStep = self._offlineSpanStep, 1
        X = self.windowize(X)
        self._offlineSpanStep = _offlineSpanStep

        X = np.array(X, dtype="float32").reshape((len(X), -1))

        if not self.trained:
            # Algorithm Body - START -> Pure Train Mode
            self.relation_min = max(min(int(X.shape[1]/2), 10),
                                    min(int(X.shape[1]), 3))
            
            relatMatrix = np.zeros([X.shape[1], X.shape[1]])

            self.clusters_count = 1
            self.clusters_max_border = np.array(
                [X[0, :]+self.initial_dist_threshold])
            self.clusters_min_border = np.array(
                [X[0, :]-self.initial_dist_threshold])
            self.clusters_submax_border = np.array(
                [X[0, :]+self.incorporate_dist_threshold])
            self.clusters_submin_border = np.array(
                [X[0, :]-self.incorporate_dist_threshold])
            X = X[1:, :]
            # Algorithm Body - END -> Pure Train Mode
        else:
            # Algorithm Body - START -> Reinforcing Train Mode
            self.relation_min = max(
                int(np.median(self.relatFilter)), min(int(data.shape[1]), 3))
            relatMatrix = self.relatMatrix.copy()
            # Algorithm Body - END -> Reinforcing Train Mode

        # Algorithm Body - START
        count_all = X.shape[0]

        trainTime = 0  # @Editor: To initialize Already-Costed-Time 初始化已耗费时间

        for i in range(count_all):
            t = time()  # @Editor: To remark Epoch-Start-Time 记录本轮开始时间

            V = X[i, :]
            compara_matrix = np.append(np.zeros([1]+list(self.clusters_max_border.shape)), \
                                    [V-self.clusters_max_border, self.clusters_min_border-V], axis=0)
            per_cluster_score = np.max(compara_matrix, axis=0)
            filter_ = np.sum(per_cluster_score == 0, axis=1)
            if any(filter_ >= self.relation_min):
                per_cluster_score = per_cluster_score[filter_ >= self.relation_min]
                index_sort = np.argsort(filter_[filter_ >= self.relation_min])
                per_cluster_score = per_cluster_score[index_sort]
                per_isnon = np.any(per_cluster_score == 0, axis=0)
            else:
                self.clusters_max_border = np.append(self.clusters_max_border, [V+self.initial_dist_threshold], axis=0)
                self.clusters_min_border = np.append(self.clusters_min_border, [V-self.initial_dist_threshold], axis=0)
                self.clusters_submax_border = np.append(self.clusters_submax_border, [V+self.incorporate_dist_threshold], axis=0)
                self.clusters_submin_border = np.append(self.clusters_submin_border, [V-self.incorporate_dist_threshold], axis=0)
                self.clusters_count += 1
                continue
            if not all(per_isnon):
                compara_matrix = np.append(np.zeros([1]+list(self.clusters_submax_border.shape)), \
                                            [V-self.clusters_submax_border, self.clusters_submin_border-V], axis=0)
                per_cluster_score = np.max(compara_matrix, axis=0)
                filter_ = np.sum(per_cluster_score == 0, axis=1)
                if any(filter_ >= self.relation_min):
                    per_cluster_score = per_cluster_score[filter_ >= self.relation_min]
                    index_sort = np.argsort(filter_[filter_ >= self.relation_min])
                    per_cluster_score = per_cluster_score[index_sort]
                    per_isnon = np.any(per_cluster_score == 0, axis=0)
                else:
                    self.clusters_max_border = np.append(self.clusters_max_border, [V+self.initial_dist_threshold], axis=0)
                    self.clusters_min_border = np.append(self.clusters_min_border, [V-self.initial_dist_threshold], axis=0)
                    self.clusters_submax_border = np.append(self.clusters_submax_border, [V+self.incorporate_dist_threshold], axis=0)
                    self.clusters_submin_border = np.append(self.clusters_submin_border, [V-self.incorporate_dist_threshold], axis=0)
                    self.clusters_count += 1
                    continue
                if all(per_isnon):
                    arg_index = np.argmin(per_cluster_score, axis=0)
                    for ii in range(arg_index.size):
                        refresh_cons = False
                        if self.clusters_max_border[int(arg_index[ii]), ii] < V[ii]:
                            self.clusters_max_border[int(arg_index[ii]), ii] = V[ii] + \
                                (V[ii]-self.clusters_max_border[int(arg_index[ii]), ii])*self.expansion_rate
                            refresh_cons = True
                        if self.clusters_min_border[int(arg_index[ii]), ii] > V[ii]:
                            self.clusters_min_border[int(arg_index[ii]), ii] = V[ii] - \
                                (self.clusters_min_border[int(arg_index[ii]), ii]-V[ii])*self.expansion_rate
                            refresh_cons = True
                        if refresh_cons:
                            self.clusters_submax_border[int(arg_index[ii]), ii] = \
                                self.clusters_max_border[int(arg_index[ii]), ii]+self.incorporate_dist_threshold
                            self.clusters_submin_border[int(arg_index[ii]), ii] = \
                                self.clusters_min_border[int(arg_index[ii]), ii]-self.incorporate_dist_threshold
                        relatIndex = np.where(per_cluster_score[arg_index[ii]] == 0)[0]
                        relatMatrix[ii, relatIndex] += 1 / relatIndex.size
                else:
                    if any(per_isnon):
                        arg_index = np.argmin(per_cluster_score[:, per_isnon], axis=0)
                        arg_act = 0
                        for ii in range(len(V)):
                            if per_isnon[ii]:
                                refresh_cons = False
                                if self.clusters_max_border[int(arg_index[arg_act]), ii] < V[ii]:
                                    self.clusters_max_border[int(arg_index[arg_act]), ii] = V[ii] + \
                                        (V[ii]-self.clusters_max_border[int(arg_index[arg_act]), ii])*self.expansion_rate
                                    refresh_cons = True
                                if self.clusters_min_border[int(arg_index[arg_act]), ii] > V[ii]:
                                    self.clusters_min_border[int(arg_index[arg_act]), ii] = V[ii] - \
                                        (self.clusters_min_border[int(arg_index[arg_act]), ii]-V[ii])*self.expansion_rate
                                    refresh_cons = True
                                if refresh_cons:
                                    self.clusters_submax_border[int(arg_index[arg_act]), ii] = \
                                        self.clusters_max_border[int(arg_index[arg_act]), ii]+self.incorporate_dist_threshold
                                    self.clusters_submin_border[int(arg_index[arg_act]), ii] = \
                                        self.clusters_min_border[int(arg_index[arg_act]), ii]-self.incorporate_dist_threshold
                                relatIndex = np.where(per_cluster_score[arg_index[arg_act]] == 0)[0]  # relatMatrix
                                relatMatrix[ii, relatIndex] += 1 / relatIndex.size  # relatMatrix
                                arg_act += 1
                            else:
                                relatMatrix[ii, ii] += 1  # relatMatrix
                    else:
                        relatMatrix += np.eye(len(V))
                    self.clusters_max_border = np.append(self.clusters_max_border, [V+self.initial_dist_threshold], axis=0)
                    self.clusters_min_border = np.append(self.clusters_min_border, [V-self.initial_dist_threshold], axis=0)
                    self.clusters_submax_border = np.append(self.clusters_submax_border, [V+self.incorporate_dist_threshold], axis=0)
                    self.clusters_submin_border = np.append(self.clusters_submin_border, [V-self.incorporate_dist_threshold], axis=0)
                    self.clusters_count += 1
            else:  # relatMatrix
                arg_index = np.argmin(per_cluster_score, axis=0)  # relatMatrix
                for ii in range(arg_index.size):  # relatMatrix
                    relatIndex = np.where(per_cluster_score[arg_index[ii]] == 0)[
                        0]  # relatMatrix
                    relatMatrix[ii, relatIndex] += 1 / relatIndex.size  # relatMatrix

            time_act = time() - t  # @Editor: To calculate Epoch-Costed-Time 计算本轮耗费的时间
            trainTime += time_act  # @Editor: To refresh Already-Costed-Time 更新已耗费的时间
            # @Editor: To re-estimate Training Remain-Time 重新估算剩余的训练时间
            self.predictTime = trainTime/(i+1) * (count_all-i-1)

        self.score_reference = np.append(np.array(
            self.clusters_submax_border), np.array(self.clusters_submin_border), axis=0)
        self.score_reference = np.append(np.zeros(
            [len(self.clusters_submax_border), self.clusters_submax_border[0].size]), self.score_reference, axis=0)
        self.score_reference = self.score_reference.reshape(
            3, len(self.clusters_max_border), self.clusters_max_border[0].size)
        self.relatMatrix = relatMatrix / np.diag(relatMatrix)[:, None]
        self.relatFilter = (self.relatMatrix>0.6).sum(axis=1)
        print(self.relatFilter)
        # Algorithm Body - END
        if save:
            self.save_model()  # @Editor: Save model 保存模型
        self.trained = True  # @Editor: To refresh Training State 刷新模型训练状态
        # @Editor: To reset Training Remain-Time to meaningless -1 重置剩余训练时间(-1即本估算时间无意义)

    def single_validate(self, V, inner=False):
        """
        data: M (M is the parameter dimension) -> T/F[Global Anomaly or Not], anomaly score of each parameter
        """
        if not inner:
            V = self.normalization(V)
        sub = np.ones(V.size)*float("nan")
        sup = np.ones(V.size)*float("nan")
        compara_matrix = (self.score_reference-V)
        compara_matrix[0, :, :] *= 0
        compara_matrix[1, :, :] *= -1
        compara_matrix[np.where(np.isnan(compara_matrix))] = float("inf")
        per_cluster_score_ = np.max(compara_matrix, axis=0)
        filter_ = np.sum(per_cluster_score_ < self.thred, axis=1)
        if any(filter_):
            filter_ind = np.where(filter_ > 0)[0]
            filter_ = filter_[filter_ind]
            per_cluster_score_ = per_cluster_score_[filter_ind, :]
            min_score = per_cluster_score_[np.argmax(filter_)] / self.thred
            sub[:] = self.score_reference[2, filter_ind[np.argmax(filter_)], :]
            sup[:] = self.score_reference[1, filter_ind[np.argmax(filter_)], :]
        else:
            return 1, list(sub), list(sup)
        for ii in range(len(V)):  # relatMatrix
            filter_ind_ = filter_ind[filter_ >= self.relatFilter[ii]]
            if len(filter_ind_):
                per_cluster_score = per_cluster_score_[filter_ >= self.relatFilter[ii], :]
                filter_ind_ = filter_ind_[per_cluster_score[:, ii] < self.thred]
                per_cluster_score = per_cluster_score[per_cluster_score[:, ii] < self.thred, :]
                if len(filter_ind_):
                    arg_index = np.argmin(per_cluster_score[:, ii])  # relatMatrix
                    min_score[ii] = per_cluster_score[arg_index, ii] / self.thred
                    sub[ii] = self.score_reference[2, filter_ind_[arg_index], ii]
                    sup[ii] = self.score_reference[1, filter_ind_[arg_index], ii]
        return min(max(np.where(~np.isinf(min_score), min_score, 0))/2, 1), list(sub), list(sup)

    def validate(self, data):
        # Algorithm Body - START
        # data = np.diff(data, axis=0)
        scores = float("nan")*np.ones(data.shape, dtype="float32")
        subData = float("nan")*np.ones(data.shape, dtype="float32")
        supData = float("nan")*np.ones(data.shape, dtype="float32")
        ind = np.where((~np.isnan(data)).any(axis=1))[0]
        X = self.normalization(data[ind])
        for i, _ in enumerate(range(0, len(X)-self._windowStep + self._offlineSpanStep, self._offlineSpanStep)):
            V = X[i*self._offlineSpanStep:i*self._offlineSpanStep+self._windowStep, :]
            cons = False
            if V.shape[0] < self._windowStep:
                cons = True
                V = X[-self._windowStep:, :]
            V = V.flatten()
            score, sub, sup = self.single_validate(V, inner=True)
            if cons:
                scores[ind[-self._windowStep:]] = np.minimum(
                    np.where(~np.isnan(scores[ind[-self._windowStep:]]), scores[ind[-self._windowStep:]], 1), 
                    score)
                subData[ind[-self._windowStep:]] = np.minimum(
                    np.where(~np.isnan(subData[ind[-self._windowStep:]]), subData[ind[-self._windowStep:]], float("inf")), 
                    np.array(sub, dtype="float32").reshape((self._windowStep, -1)))
                supData[ind[-self._windowStep:]] = np.maximum(
                    np.where(~np.isnan(supData[ind[-self._windowStep:]]), supData[ind[-self._windowStep:]], -float("inf")), 
                    np.array(sup, dtype="float32").reshape((self._windowStep, -1)))
            else:
                scores[ind[i:i+self._windowStep]] = np.minimum(
                    np.where(~np.isnan(scores[ind[i:i+self._windowStep]]), scores[ind[i:i+self._windowStep]], 1), 
                    score)
                subData[ind[i:i+self._windowStep]] = np.minimum(
                    np.where(~np.isnan(subData[ind[i:i+self._windowStep]]), subData[ind[i:i+self._windowStep]], float("inf")), 
                    np.array(sub, dtype="float32").reshape((self._windowStep, -1)))
                supData[ind[i:i+self._windowStep]] = np.maximum(
                    np.where(~np.isnan(supData[ind[i:i+self._windowStep]]), supData[ind[i:i+self._windowStep]], -float("inf")), 
                    np.array(sup, dtype="float32").reshape((self._windowStep, -1)))

        # Algorithm Body - END
        # @Editor: return List[anomalies' frame(index)], List[anomaly-score of each frame] 返回异常帧序号的列表和各帧异常分数的列表
        scores = np.where(~np.isnan(scores), scores, 0)
        scores[scores>1] = 1; scores[scores<0] = 0
        abList = np.where(scores.max(axis=-1)>0.5)[0].tolist()
        
        subData = [list(map(float, subD_)) for subD_ in self.anti_normalization(np.array(subData, dtype="float32")).T]
        supData = [list(map(float, supD_)) for supD_ in self.anti_normalization(np.array(supData, dtype="float32")).T]
        return abList, scores.tolist(), [list(zip(subData, supData)), ["下阈值", "上阈值"]]
        #    P.S. 0.5 as a common jungle for anomaly score, i.e. 0~0.5 as normaly while 0.5~1 as anomaly, 异常分数统一以0.5为判据(即0~0.5一下是正常，0.5~1是异常)

    def to_json(self):
        """
        Load Special Configurations By Path
        """
        return json.dumps({
            "ims_info": [self.relation_min, self.thred, self.initial_dist_threshold, \
                            self.expansion_rate, self.incorporate_dist_threshold],
            "score_reference": [[list(map(float, refere)) for refere in reference] for reference in self.score_reference],
            "relatMatrix": [list(map(float, relatM)) for relatM in self.relatMatrix],
            "relatFilter": list(map(int,self.relatFilter)),
            #"relatFilter": list(self.relatFilter),
            "mins": list(map(float, self.mins)),
            "maxs": list(map(float, self.maxs))
        }).encode()

    def from_json(self, configJson=b""):
        """
        Load Special Configurations By Path
        """
        config = json.loads(configJson.decode())
        self.relation_min, self.thred, self.initial_dist_threshold, \
            self.expansion_rate, self.incorporate_dist_threshold = config['ims_info']
        self.score_reference = np.array(config["score_reference"])
        self.relatMatrix = np.array(config["relatMatrix"])
        self.relatFilter = np.array(config["relatFilter"])
        self.mins = np.array(config["mins"])
        self.maxs = np.array(config["maxs"])

        # To calculate some latent parameters which could be deducated from the former parameters
        self.id_const = np.where(self.maxs == self.mins)[0]
        self.id_nonconst = np.where(self.maxs != self.mins)[0]
        self.clusters_submax_border = self.score_reference[1, ...]
        self.clusters_submin_border = self.score_reference[2, ...]
        self.clusters_count = self.score_reference.shape[1]
        self.clusters_max_border = self.clusters_submax_border - \
            self.incorporate_dist_threshold
        self.clusters_min_border = self.clusters_submin_border + \
            self.incorporate_dist_threshold
    
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
