import os, json, warnings
import numpy as np
import pandas as pd
from time import time
from sklearn.linear_model import Lasso

if __name__ == "__main__":
    from support.BaseAlgoClass import BaseModel #基础模型类，构建和训练算法
else:
    from .support.BaseAlgoClass import BaseModel

def _get_endog(X, xid):
    corrx = np.empty(X.shape)
    for yid, y in enumerate(X.T):
        corrx[:,yid] = (np.correlate(X[:,xid],y,mode="full")/\
                        np.correlate(np.ones(len(y)),np.ones(len(y)),mode="full"))[-y.size:]
    return corrx

def _get_tr(X, p):
    xdim, ydim = X.shape
    x = np.empty([xdim, ydim*p+1])
    x[:,0] = 1
    for i in range(p):
        x[:-i-1,1+i*ydim:1+(i+1)*ydim] = X[i+1:,:]
        x[-i-1:,1+i*ydim:1+(i+1)*ydim] = X[:i+1,:]
    return x

def _get_trendog(X, xid, p):
    raw_x = _get_endog(X, xid)
    return _get_tr(raw_x, p), raw_x[:, xid]

def _get_p_params(X, p, method="lasso",
                alpha=0.1, max_iter=1000, step_max=2500):
    xdim, ydim = X.shape
    params = np.empty([p*ydim+1, ydim])
    err = np.empty(ydim)
    if method == "lasso":
        lasso = Lasso(alpha=alpha, max_iter=int(max_iter))
    for yid in range(ydim):
        xi, yi = _get_trendog(X, yid, p)
        xi -= xi.mean(axis=0)
        yi -= yi.mean()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            if method == "lasso":
                lasso.fit(xi, yi)
                params[:, yid] = lasso.coef_
            else:
                params[:, yid] =  np.linalg.lstsq(xi, yi[:,None])[0].flatten()
        X_ = _get_tr(X[::-1,:], p)
        err_ = []
        std_ = []
        for tid in range(int(np.ceil((xdim-p)/step_max))):
            err_.append(np.mean(
                (X[p+tid*step_max:p+(tid+1)*step_max, yid] - \
                 np.dot(X_[-p-1-tid*step_max:-p-1-(tid+1)*step_max:-1], params[:, yid, None])).flatten()))
            std_.append(np.std(
                (X[p+tid*step_max:p+(tid+1)*step_max, yid] - \
                 np.dot(X_[-p-1-tid*step_max:-p-1-(tid+1)*step_max:-1], params[:, yid, None])).flatten()))
        params[0, yid] += np.mean(err_)
        err[yid] = np.mean(std_)
    return params, err

def _weight_str(param_norm, param, all_names, eps=1e-6):
    n = int(round(np.log(1/eps)/np.log(10)))
    if abs(param[0]) < eps:
        rule_str = ""
    else:
        rule_str = f"{round(param[0],n)}"
    #param[1:] = np.where(param_norm[1:]>=param_norm[1:].max()/(10**n), param[1:], 0)
    for order_, weights_all_ in enumerate(zip(param_norm[1:].reshape(-1, len(all_names)), param[1:].reshape(-1, len(all_names)))):
        weights_norm_, weights_ = weights_all_
        rule_itms_ = [
            f"{round(weight_,n)}*{name_}({order_+1})"
            for weight_norm_, weight_, name_ in zip(weights_norm_, weights_, all_names)
            if abs(weight_norm_) > eps and abs(weight_) > eps 
            ]
        if rule_itms_:
            rule_str += "+" + "+".join(rule_itms_)
    if rule_str[:1] == "+":
        rule_str = rule_str[1:]
    return rule_str.replace("+-","-")

def _get_rule(params_norm, params, all_names, detect_names, detect_err, nonvalid, eps=1e-6):
    n = int(round(np.log(1/eps)/np.log(10)))
    result = []
    for index in nonvalid:
        param = params[index]
        param_norm = params_norm[index]
        detecterr = detect_err[index]
        detect_name = all_names[detect_names[index]]
        result.append(f"abs({_weight_str(param_norm,param,all_names,eps=eps)}-{detect_name})>"
                      f"{round(detecterr+param[1:].max()/100*np.sum(param[1:]<param[1:].max()/100),n)}")
    return " or ".join(result)

class Model(BaseModel): # Use Model Template
    def __init__(self, index=0, name="model", pnames=[], config={}, **kwargs):
        # Algorithm Body - START -> Credit  Configuration
        self._faultLevel = 3
        self._algoType = "MVARMA"
        self._zh_name = "多参数自回归模型"
        # Algorithm Body - END -> Credit Configuration

        # Algorithm Body - START -> HyperParameters  Configuration
        self.pmin = 5
        self.pmax = 10
        self.relat_thred = 0.5
        self.err_max = 0.3
        self.err_min = 1e-5
        self.method = "lasso"
        self.l1 = 2e-4
        self.max_iter = 500
        # Algorithm Body - END -> HyperParameters  Configuration

        super().__init__(index=index, name=name, pnames=pnames, config=config, **kwargs)

    def set_config(self,config):
        try:
            self.pmin = int(config["pmin"])
        except:
            pass
        try:
            self.pmax = int(config["pmax"])
        except:
            pass
        try:
            self.relat_thred = float(config["relat_thred"])
        except:
            pass
        try:
            self.err_max = float(config["err_max"])
        except:
            pass
        try:
            self.err_min = float(config["err_min"])
        except:
            pass
        try:
            self.method = config["method"]
        except:
            pass
        try:
            self.l1 = float(config["l1"])
        except:
            pass
        try:
            self.max_iter = int(config["max_iter"])
        except:
            pass
        super().set_config(config)

    def get_config(self):
        return{
            "pmin":self.pmin, "pmax":self.pmax,
            "relat_thred":self.relat_thred,
            "err_max":self.err_max, "err_min":self.err_min,
            "method":self.method, "l1":self.l1,
            "max_iter":self.max_iter,}

    def fit(self, data, save=False):
        data = (
            pd.DataFrame(self.merged_data(data))
            .fillna(method="ffill")
            .fillna(method="bfill")
            .values.astype("float32")
        )
        data = data[(~np.isnan(data)).any(axis=1)]
        """
        N*M (N is frames, M is parameter dimensions)
        """
        self.trainTime = time()  # @Editor: Register Training Start-Time 记录训练开始时间
        # @Editor: Estimated Training Remain-Time 预估训练剩余的训练时间
        self.predictTime = self.pmax * 8e-5 * data.size
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

        # Algorithm Body - START
        err = float('inf')*np.ones(X.shape[1])
        loss = float('inf')*np.ones(X.shape[1])
        count = 0
        self.params = None
        slice_time = 8e-5 * data.size
        for p in range(self.pmin, self.pmax):
            t = time()
            params_, err_ = _get_p_params(X, p,
                                          method=self.method,
                                          alpha=self.l1,
                                          max_iter=self.max_iter)
            if self.params is None:
                self.params, err = params_, err_
                loss = err + self.l1*p
            elif any(err_ + self.l1*p < err):
                params, self.params = self.params, params_
                self.params[:, err_ + self.l1*p < loss] = 0
                self.params[:params.shape[1], err_ + self.l1*p < loss] = params[:params.shape[1], err_ + self.l1*p < loss]
                err[err_ + self.l1*p < loss] = err_[err_ + self.l1*p < loss]
                loss = np.minimum(err_ + self.l1*p, loss)
                count = 0
                self._windowStep = p
            else:
                count += 1
            if count > 5:
                break
            slice_time = 0.15*slice_time + 0.85*(time() - t)
            self.predictTime = (self.pmax-p) * slice_time
        # print(err)
        self.valid_inds = np.where(err <= self.err_max)[0]
        self.params = self.params[:, self.valid_inds]
        p = (self.params.shape[0]-1)//data.shape[1]
        x = _get_tr(np.array(X[::-1,:], dtype="float32"), p)[-p-1::-1,:]
        trueY = X[p:, self.valid_inds]
        mainData = np.dot(x, self.params)
        self.thred = self.relat_thred * np.maximum(np.max(np.abs(trueY - mainData),axis=0), self.err_min)
        self._windowStep = max(self._windowStep, p*2)
        # Algorithm Body - END
        if save:
            self.save_model()  # @Editor: Save model 保存模型
        self.trained = True  # @Editor: To refresh Training State 刷新模型训练状态
        # @Editor: To reset Training Remain-Time to meaningless -1 重置剩余训练时间(-1即本估算时间无意义)

    def validate(self, data):
        # Algorithm Body - START
        scores = float("nan")*np.ones(data.shape, dtype="float32")
        subData = float("nan")*np.ones(data.shape, dtype="float32")
        supData = float("nan")*np.ones(data.shape, dtype="float32")
        ind = np.where((~np.isnan(data)).any(axis=1))[0]
        X = self.normalization(data[ind])
        mainData = np.array(X[:, :], dtype="float32")
        if len(self.valid_inds):
            p = (self.params.shape[0]-1)//data.shape[1]
            x = _get_tr(np.array(X[::-1,:], dtype="float32"), p)[-p-1::-1,:]
            mainData[p:, self.valid_inds] = np.dot(x, self.params)
            scores_ = float("nan")*np.ones([len(ind), data.shape[1]], dtype="float32")
            scores_[:, self.valid_inds] = np.minimum(1, np.abs(X[:, self.valid_inds] - mainData[:, self.valid_inds]) / (2*self.thred))
            scores[ind] = scores_
            scores = np.where(~np.isnan(scores), scores, 0)
            scores[scores > 1] = 1; scores[scores < 0] = 0
        else:
            p = 0
            scores = np.zeros(data.shape)
        # Algorithm Body - END
        # @Editor: return List[anomalies' frame(index)], List[anomaly-score of each frame] 返回异常帧序号的列表和各帧异常分数的列表
        scores = np.where(~np.isnan(scores), scores, 0)
        scores[scores>1] = 1; scores[scores<0] = 0
        abList = np.where(scores.max(axis=-1)>0.5)[0].tolist()

        subData_ = np.array(mainData, dtype="float32")
        subData_[p:, self.valid_inds] -= self.thred
        subData[ind, :] = subData_

        supData_ = np.array(mainData, dtype="float32")
        supData_[p:, self.valid_inds] += self.thred
        supData[ind, :] = supData_

        subData = [list(map(float, subD_)) for subD_ in self.anti_normalization(np.array(subData, dtype="float32")).T]
        supData = [list(map(float, supD_)) for supD_ in self.anti_normalization(np.array(supData, dtype="float32")).T]
        return abList, scores.tolist(), [list(zip(subData, supData)), ["下阈值", "上阈值"]]
        #    P.S. 0.5 as a common jungle for anomaly score, i.e. 0~0.5 as normaly while 0.5~1 as anomaly, 异常分数统一以0.5为判据(即0~0.5一下是正常，0.5~1是异常)

    def to_json(self):
        """
        Load Special Configurations By Path
        """
        print("get mvarma json str")
        print(self.get_config())
        return json.dumps({
            "var_info": self.get_config(),
            "valid_inds": self.valid_inds.tolist(),
            "params": self.params.tolist(),
            "thred": self.thred.tolist(),
            "mins": self.mins.tolist(),
            "maxs": self.maxs.tolist()
        }).encode()

    def from_json(self, configJson=b""):
        """
        Load Special Configurations By Path
        """
        config = json.loads(configJson.decode())
        self.set_config(config['var_info'])
        self.valid_inds = np.array(config["valid_inds"], dtype="int32")
        self.params = np.array(config["params"], dtype="float32")
        self.thred = np.array(config["thred"], dtype="float32")
        self.mins = np.array(config["mins"], dtype="float32")
        self.maxs = np.array(config["maxs"], dtype="float32")

        # To calculate some latent parameters which could be deducated from the former parameters
        self.id_const = np.where(self.maxs == self.mins)[0]
        self.id_nonconst = np.where(self.maxs != self.mins)[0]

    def _check_nonvalid(self, data, beta=0.75, ab_min=100):
        # Algorithm Body - START
        X = self.normalization(data)
        if len(self.valid_inds):
            p = (self.params.shape[0]-1)//data.shape[1]
            x = _get_tr(X[::-1,:], p)[-p-1::-1,:]
            trueY = X[p:, self.valid_inds]
            mainData = np.dot(x, self.params)
            ab_freq = (np.abs(trueY - mainData) >= self.thred).max(axis=1).sum(axis=0)
            ind_freq = (np.abs(trueY - mainData) >= self.thred).sum(axis=0)/(1+ab_freq)
            # print(ab_freq)
            if ab_freq > min(ab_min, 0.1*len(data)):
                return np.where(ind_freq >= min(ind_freq.max()*2/3, beta))[0].tolist()
            else :
                return []
        else:
            return []

    def rule_induce(self, data, beta=0.75, eps=1e-5):
        nonvalid = self._check_nonvalid(data, beta=beta)
        p = (self.params.shape[0]-1)//data.shape[1]
        params = np.zeros(self.params.shape)
        params[1:, :] = self.params[1:,:]/(np.tile(self.maxs-self.mins, p))[:,None]*(self.maxs-self.mins)[None,self.valid_inds]
        params[0, :] += (self.maxs+self.mins)[self.valid_inds]/2 - np.dot((np.tile(self.maxs+self.mins, p))[None, :]/2, params[1:,:]).flatten()
        thred = self.thred * (self.maxs-self.mins)[self.valid_inds]
        # print(params.T)
        return _get_rule(self.params.T, params.T, self.pnames, self.valid_inds, thred, nonvalid, eps=eps)

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
##        [os.path.join(DIR, 'missile'), ["Vxm","Vym","Vzm","αa","βa","γm","φm","ψm"]],
##        os.path.join(DIR, 'rocket'),
##        os.path.join(DIR, 'ALFA'),
##        os.path.join(DIR, 'KDD99'),
##        os.path.join(DIR, 'MSL'),
##        os.path.join(DIR, 'SMAP'),
        os.path.join(DIR, 'LSSC')
        ], nstep=1))

    ## 算法规则挖掘性能验证
    print("[Rules]")
    pprint(get_rule(Model, [
##        [os.path.join(DIR, 'missile'), ["Vxm","Vym","Vzm","αa","βa","γm","φm","ψm"]],
##        os.path.join(DIR, 'rocket'),
##        os.path.join(DIR, 'ALFA'),
##        os.path.join(DIR, 'KDD99'),
##        os.path.join(DIR, 'MSL'),
##        os.path.join(DIR, 'SMAP'),
        os.path.join(DIR, 'LSSC')
        ], nstep=1))
