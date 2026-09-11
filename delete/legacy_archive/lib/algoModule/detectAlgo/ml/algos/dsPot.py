import os, json, warnings     #处理操作系统和JSON数据
import pandas as pd
import numpy as np
from time import time      #计算代码执行时间

from scipy.optimize import minimize     #用于优化问题寻找最小值

if __name__ == "__main__":
    from support.BaseAlgoClass import BaseModel #基础模型类，构建和训练算法
else:
    from .support.BaseAlgoClass import BaseModel

def _get_rule(extreme_quantiles, mean_cnts, thres, pnames, valid_inds, nonvalid, eps=1e-6):
    #extreme_quantiles：上下阈值
    #mean_cnts：滑动窗口
    #thres：超参数，设置的阈值下限
    #pnames：要检测的参数
    #valid_inds：有效值索引
    #nonvalid：异常值列表
    #eps：精度
    try:
        n = int(round(-np.log(eps)/np.log(10)))     #计算整数n格式化输出的阈值
    except:
        n = 2
    rule = []   #初始化空列表，存储生成的规则
    for index in nonvalid:  #遍历nonvalid列表中的每个索引
        param = extreme_quantiles[index]    #获取当前索引对应的极值上下限
        mean_cnt = mean_cnts[index]     #获取当前索引对应的平均计数
        detecterr = thres[index]        #获取当前索引对应的阈值
        detect_name = pnames[valid_inds[index]]  #获取当前索引对应的参数名称
        rule.append(f"[{round(0.5*mean_cnt)}]({detect_name}>=Mean({detect_name},{round(mean_cnt)},0)+{round(param[0]+detecterr,n)}"
                    f" or {detect_name}<=Mean({detect_name},{round(mean_cnt)},0)+{round(param[1]-detecterr,n)})".replace("+-", "-"))
        #round()方法四舍五入。f与{}，使用{}嵌入变量，只有{}里的变量是“真的”运行时替换为实际值。

    return " or ".join(rule)    #将rule列表中的所有规则用or连接并返回结果，满足任何一个条件即可触发异常


class Model(BaseModel): # Use Model Template
    def __init__(self, index=0, name="model", pnames=[], config={}, **kwargs):
        #index：模型索引   name：模型名称   pnames：列表，模型参数名称  config：字典，模型配置信息
        # Algorithm Body - START -> Credit  Configuration
        self._faultLevel = 1        #设置故障级别为1
        self._algoType = "dsPot"       #模型的算法类型
        self._zh_name = "漂移浮动阈值"  #模型的中文名称
        # Algorithm Body - END -> Credit Configuration
        
        # Algorithm Body - START -> HyperParameters  Configuration
        # self.depth = 10     #刚开始选取的点数5*depth
        self.q = 0.002     #q值，单侧异常概率
        self.rt = 0.85      #模型rt值,设置的初始阈值t
        self.sec_rt = 1 - self.q    #模型sec_rt值,设置的防噪阈值t
        self.countMax = 30  #最大计数值
        self.thres_min = 0.01   #残差阈值上限
        # Algorithm Body - END -> HyperParameters  Configuration
        
        super().__init__(index=index, name=name, pnames=pnames, config=config, **kwargs) #调用父类构造函数，初始化Model实例

    def set_config(self,config):    #self模型实例，config字典参数
        #try:
        #    self.depth = int(config['depth'])   #将config中的depth键转成int并赋给模型中的depth
        #except:
        #    pass
        try:
            self.q = int(config['q'])
        except:
            pass
        try:
            self.rt = float(config['rt'])
        except:
            pass
        try:
            self.sec_rt = float(config['sec_rt'])
        except:
            pass
        try:
            self.countMax = int(config['countMax'])
        except:
            pass
        try:
            self.thres_min = float(config['thres_min'])
        except:
            pass
        self._initStock = []
        super().set_config(config) #调用父类方法，传递config参数

    def get_config(self):   #self为模型实例，构造config字典
        return {
            #"depth":self.depth,
            "q":self.q,"rt":self.rt,"sec_rt":self.sec_rt,
            "countMax":self.countMax, "thres_min":self.thres_min
            }

    '''
    静态方法是指在类中定义的，不需要实例化类就可以调用的方法。
    静态方法的主要特点是它不依赖于类的实例，而是直接依赖于类本身。
    静态方法的主要作用是对类的属性和方法进行操作，而不需要操作类的实例。
    '''
    @staticmethod
    def objFun(X, f, jac):      #定义静态方法objFun,X为向量，f为函数，jac为梯度函数
            g = 0
            j = np.zeros(X.shape)   #初始化一个与X相同得0向量j
            i = 0
            for x in X:     #遍历X
                fx = f(x)   #计算当前x在函数f下的值
                g = g + fx ** 2 #fx的2次幂与g相加
                j[i] = 2 * fx * jac(x)  #计算梯度jac(x)
                i = i + 1
            return g, j
        
    @staticmethod
    def rootsFinder(fun, jac, bounds, npoints): #fun为函数，jac为梯度函数，bounds包含区间边界的元组，npoints整数
        """
        Find possible roots of a scalar function 
        """
        if bounds[0] == bounds[1]: #边界若相等只可能一个根，直接返回边界值
            return np.array([bounds[0]])
        elif bounds[0] > bounds[1]:
            bounds = [bounds[1], bounds[0]]
        X0 = np.linspace(bounds[0], bounds[1], npoints) #使用npoints个插值点创建两边界的等差数列

        #minimize()方法：fun返回标量值的目标函数;x0初始猜测值;method优化方法;jac梯度函数，计算目标函数梯度
        X = minimize(lambda X: Model.objFun(X, fun, jac), X0,   #lambda为匿名函数，接收参数X，调用objFun。作为优化目标
                     method='L-BFGS-B',         #指定优化算法，随机梯度下降算法
                     jac=True, bounds=[bounds] * len(X0)).x     #优化过程计算梯度，每个插值点都有相同边界
        return np.unique(np.round(X, decimals=5))

    @staticmethod
    def log_likelihood(Y, gamma, sigma):    #给定gamma和sigma计算帕累托分布的似然函数值
        """
        Compute the log-likelihood for the Generalized Pareto Distribution (μ=0)

        """
        n = len(Y)
        if n == 0:
            return 0
        if gamma > 0 and sigma > 0:
            tau = gamma / sigma
            return -n * np.log(sigma) - (1 + (1 / gamma)) * (np.log(1 + tau * Y)).sum()
        elif np.mean(Y) > 0:
            return n * (1 + np.log(np.mean(Y)))
        else:
            return -np.inf

    @staticmethod
    def grimshaw(peak, epsilon=1e-8, n_points=10):  
        """
        Compute the GPD parameters estimation with the Grimshaw's trick
        根据给定的数据点计算通用Pareto分布的参数，根据Grimshaw策略计算最优参数sigma与gama
        """
        peak = peak[peak!=0]
        if len(peak) == 0:
            return 0, 0

        Ym = np.min(peak)
        YM = np.max(peak)
        Y_ = np.mean(peak)

        a = -1 / YM
        if abs(a) < 2 * epsilon:
            epsilon = abs(a) / n_points
        # We look for possible roots
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            left_zeros = Model.rootsFinder(lambda t: (1+np.mean(np.log(1+t*peak)))*np.mean(1/(1+t*peak)),\
                lambda t: np.mean(1+np.log(1+t*peak))*(-np.mean(1/(1+t*peak))+np.mean(1/(1+t*peak)**2))/t+\
                    np.mean(1/(1+t*peak))*(1-np.mean(1/(1+t*peak)))/t,\
                        (a+epsilon, -epsilon), n_points)

            right_zeros = Model.rootsFinder(lambda t: (1+np.mean(np.log(1+t*peak)))*np.mean(1/(1+t*peak)),\
                lambda t: np.mean(1+np.log(1+t*peak))*(-np.mean(1/(1+t*peak))+np.mean(1/(1+t*peak)**2))/t+\
                    np.mean(1/(1+t*peak))*(1-np.mean(1/(1+t*peak)))/t,\
                        (2*(Y_-Ym)/(Y_*Ym), 2*(Y_-Ym)/(Y_**2)), n_points)

            # all the possible roots
            zeros = np.concatenate((left_zeros, right_zeros))

            # 0 is always a solution so we initialize with it
            gamma_best = 0
            sigma_best = Y_
            ll_best = Model.log_likelihood(peak, gamma_best, sigma_best)

            # we look for better candidates
            for z in zeros:
                if z <= 0:
                    continue
                gamma = np.mean(np.log(1 + z * peak)) - 1
                sigma = gamma / z
                ll = Model.log_likelihood(peak, gamma, sigma)
                if ll > ll_best:
                    gamma_best = gamma
                    sigma_best = sigma
                    ll_best = ll
        return gamma_best, sigma_best

    def fit(self, data, save=False):        #拟合通用帕累托分布模型(训练)检测输入数据的异常值
        data = pd.DataFrame(self.merged_data(data)).fillna(method="ffill").fillna(method="bfill").values.astype(np.float64)
        # data = np.diff(data, axis=0).fillna(method="ffill").fillna(method="bfill").values.astype(np.float64)
        """  
        N*M (N is frames, M is parameter dimensions)
        """
        self.start_trainTime = time()  # @Editor: Register Training Start-Time 记录训练开始时间
        # @Editor: Estimated Training Remain-Time 预估训练剩余的训练时间
        self.predictTime = 8e-5 * data.size
        # (P.S. Here, estimated by experiment with Hypothese O(N*M)),通过实验估计复杂度为o(N*M)

        # Initialization Part (Different Modes: Pure Train Mode/Reinforcing Train Mode)
        #初始化部分(纯训练模式/强化学习训练模式)
        # @Editor: Use [trained] to distinguish actual mode 通过[trained]区分模型现在的而状态

        '''
         这段代码首先检查模型是否已经训练。如果模型尚未训练，则执行`config_normalization`方法来配置归一化参数，
         然后使用`normalization`方法对输入数据进行归一化。
         如果模型已经训练，则执行`reconfig_normalization`方法来重新配置归一化参数，
         然后使用`normalization`方法对输入数据进行归一化。
         这是为了确保在训练过程中始终使用相同的归一化参数。
        '''
        if not self.trained:
            self.config_normalization(data)
            data = self.normalization(data)
        else:
            self.reconfig_normalization(data)
            data = self.normalization(data)

        self.valid_inds = [] #存储有效的参数索引
        self.thresPres = [] #存储阈值
        self.extremeQuantiles = []  #极端四分位数
        self.beta = []      
        self.thres = []     #阈值
        slice_time = 8e-5 * data.shape[-1]  #存储每个参数的检测时间

        #针对单参数算法，对每个参数执行异常值检测，然后对结果进行融合    
        for p in range(data.shape[-1]): # As for a single-para algorithm, execute the detection on each para and then fusion result
            t = time()
            ## Algorithm Body - START
            # 1 - Unvalid Condition (Drop detection on such para and set all frame  directly to normaly)
            #无效条件（对此类参数进行丢弃检测，并将所有帧直接设置为正常）
           
            #对参数(p)去重，并其个数<=10,跳过该参数的检测(数据太少)
            if np.unique(data[:,p]).size <= 10: 
                continue
            stcnt = 5
            beta_ = 1/(stcnt - 1 + self.countMax - np.argmax([np.mean(data[cnt:]*data[:-cnt]) - 1e-6 * cnt
                                                              for cnt in range(stcnt, self.countMax)][::-1]))
            #print(beta_)

            # 2 - PreTrain the model if necessary #如有必要，对模型预训练
            # pretrainData = data[::, p] # Choose the first 5*[depth] frames as pre-train dataset，选择前 5*[depth] 帧作为预训练数据集
            pretrainData = data[::, p]
            nPre = len(pretrainData) 
            # pretrainData = data[:self.depth*5, p]
            # nPre = len(pretrainData) - self.depth            
            xFilter = data[0, p]; residuPre=[0] #获取参数p的第一个数据给xFilter。初始化residuPre列表值为0
            for i in range(1, len(data)):
                xFilter = (1 - beta_) * data[i, p] + beta_ * xFilter       
                residuPre.append(data[i, p]  - xFilter)
            
            #nPre_ = len(residuPre)
            residuPre = np.sort(residuPre)      #重新排序
            thresPre = [residuPre[int(self.rt*nPre)], residuPre[int((1-self.rt)*nPre)]] #从residupre列表提取俩元素放入threspre列表
            # peaks = [residuPre[int(self.rt*nPre):int(0.99*nPre)]-thresPre[0], thresPre[1]-residuPre[int(0.01*nPre):int((1-self.rt)*nPre)]]
            peaks = [residuPre[int(self.rt*nPre):int(self.sec_rt*nPre)]-thresPre[0], thresPre[1]-residuPre[int((1-self.sec_rt)*nPre):int((1-self.rt)*nPre)]]
            #peaks = [residuPre[int(self.rt*nPre):]-thresPre[0],
            #         thresPre[1]-residuPre[:int((1-self.rt)*nPre)]]

            peaks[0] = peaks[0][peaks[0]>0]
            peaks[1] = peaks[1][peaks[1]>0]

            Nt = [len(peaks[0]),len(peaks[1])]
            extremeQuantile = [thresPre[0],thresPre[1]]
            ratio = [nPre*self.q/max(Nt[0],0.0001), nPre*self.q/max(Nt[1],0.0001)]
            if peaks[0].size:
                g1, s1 = Model.grimshaw(peaks[0])
                if g1 != 0:
                    extremeQuantile[0] += s1/g1*(1/ratio[0]**g1-1)
                else:
                    extremeQuantile[0] -= s1*np.log(ratio[0])
                extremeQuantile[0] = min(extremeQuantile[0], thresPre[0]+max(peaks[0]))

            if peaks[1].size:
                g2, s2 = Model.grimshaw(peaks[1])
                if g2 != 0:
                    extremeQuantile[1] -= s2/g2*(1/ratio[1]**g2-1)
                else:
                    extremeQuantile[1] += s2*np.log(ratio[1])
                extremeQuantile[1] = max(extremeQuantile[1], thresPre[1]-max(peaks[1]))
            thres_ = np.percentile(np.maximum(0, np.maximum(residuPre - extremeQuantile[0], extremeQuantile[1] - residuPre)), (1-self.q/2)*100)
            #thres_ = np.maximum(0, np.maximum(residuPre - extremeQuantile[0], extremeQuantile[1] - residuPre)).max()
            if thres_ < self.thres_min:
                self.valid_inds.append(p)
                self.beta.append(beta_)
                self.thresPres.append(thresPre)
                self.extremeQuantiles.append(extremeQuantile)
                self.thres.append(thres_)
            slice_time = 0.15*slice_time + 0.85*(time() - t)
            self.predictTime = (data.shape[-1]-p) * slice_time
        self.valid_inds = np.array(self.valid_inds, dtype="int32")
        self.thresPres = np.array(self.thresPres, dtype="float32")
        self.extremeQuantiles = np.array(self.extremeQuantiles, dtype="float32")
        self.beta = np.array(self.beta, dtype="float32")
        self.thres = np.maximum(np.array(self.thres, dtype="float32"), self.thres_min/1e6)
        if save:
            self.save_model()  # @Editor: Save model 保存模型
        self.trained = True  # @Editor: To refresh Training State 刷新模型训练状态
        self.end_trainTime = time()
        return self.end_trainTime - self.start_trainTime   #记录训练时间

    def singleValidate(self, dataFrames):   #对一组数据进行单次验证
        subData = np.array(dataFrames, dtype="float32")
        supData = np.array(dataFrames, dtype="float32")
        dataframe = self.normalization(dataFrames)[0]
        if len(self.valid_inds) == 0:
            return 0, [list(itm) for itm in zip(subData, supData)], ["下阈值", "上阈值"]
        
        if self.xFilter is None:
            xFilter_ = dataframe[self.valid_inds]
        else:
            xFilter_ = (1 - self.beta) * dataframe[self.valid_inds] + self.beta * self.xFilter

        xResidu = dataframe[self.valid_inds] - xFilter_
        scoresPer = [
                min(max(
                    (xRes_i - self.thresPres[i,0])/((1+self.q)*(self.extremeQuantiles[i,0] - self.thresPres[i,0])+self.thres[i])/2,
                    (self.thresPres[i,1]-xRes_i)/((1+self.q)*(self.thresPres[i,1]-self.extremeQuantiles[i,1])+self.thres[i])/2,
                    0),1) for i, xRes_i in enumerate(xResidu)]
        score = max(scoresPer)
        # if score >= 0.5:
        #    ablist.append(i)
        # scores.append(score)
        
        cons_ind = (np.array(scoresPer, dtype="float32") > 3.5)
        if self.xFilter is None:
            self.xFilter = xFilter_
        else:
            self.xFilter[~cons_ind] = xFilter_[~cons_ind]
            self.xFilter[cons_ind] = dataframe[self.valid_inds][cons_ind]
            
        suppD = self.extremeQuantiles + self.xFilter[:,None]

        # Algorithm Body - END
        supD, subD = zip(*suppD)
        subData[:, self.valid_inds] = self.anti_normalization(np.array([subD], dtype="float32"))[0].tolist()
        supData[:, self.valid_inds] = self.anti_normalization(np.array([supD], dtype="float32"))[0].tolist()
        return score, [list(itm) for itm in zip(subData, supData)], ["下阈值", "上阈值"]
    
    def validate(self, data):       #对输入的数据进行验证
        scores = float("nan")*np.ones(data.shape, dtype="float32")
        supD = np.array(data, dtype="float32")
        subD = np.array(data, dtype="float32")
        ind = np.where((~np.isnan(data)).any(axis=1))[0]
        X = self.normalization(data[ind])
        xFilter = None
        ablist = []
        for frame, dataframe in enumerate(X):
            if len(self.valid_inds) == 0:
                scores[ind[frame]] = 0
                continue
            if xFilter is None:
                xFilter_ = dataframe[self.valid_inds]
            else:
                xFilter_ = (1 - self.beta) * dataframe[self.valid_inds] + self.beta * xFilter

            xResidu = dataframe[self.valid_inds] - xFilter_
            scoresPer = [
                min(max(
                    (xRes_i - self.thresPres[i,0])/((1+self.q)*(self.extremeQuantiles[i,0] - self.thresPres[i,0])+self.thres[i])/2,
                    (self.thresPres[i,1]-xRes_i)/((1+self.q)*(self.thresPres[i,1]-self.extremeQuantiles[i,1])+self.thres[i])/2,
                    0),1) for i, xRes_i in enumerate(xResidu)]
            score = max(scoresPer)
            if score >= 0.5:
                ablist.append(ind[frame])
            scores[ind[frame], self.valid_inds] = scoresPer
            
            cons_ind = (np.array(scoresPer, dtype="float32") > 3.5)
            if xFilter is None:
                xFilter = xFilter_
            else:
                xFilter[~cons_ind] = xFilter_[~cons_ind]
                xFilter[cons_ind] = dataframe[self.valid_inds][cons_ind]
                
            suppD = self.extremeQuantiles + xFilter[:,None]
            supD[ind[frame], self.valid_inds] = suppD[:,0]
            subD[ind[frame], self.valid_inds] = suppD[:,1]
        subData = self.anti_normalization(np.array([subD], dtype="float32"))[0].T.tolist()
        supData = self.anti_normalization(np.array([supD], dtype="float32"))[0].T.tolist()

        return ablist, scores.tolist(), [[list(itm) for itm in zip(subData, supData)], ["下阈值","上阈值"]]


    def to_json(self):  #将对象转换为JSON格式
        """
        Load Special Configurations By Path
        """
        return json.dumps({
            "dspot_info": self.get_config(),
            "valid_inds": self.valid_inds.tolist(),
            "beta": self.beta.tolist(),
            "thresPres": self.thresPres.tolist(),
            "extremeQuantiles": self.extremeQuantiles.tolist(),
            "thres": self.thres.tolist(),
            "mins": self.mins.tolist(),
            "maxs": self.maxs.tolist()
        }).encode()

    def from_json(self, configJson=b""):    #从JSON字符串加载特殊配置
        """
        Load Special Configurations By Path
        """
        config = json.loads(configJson.decode())
        self.set_config(config['dspot_info'])
        self.valid_inds = np.array(config["valid_inds"], dtype="int32")
        self.beta = np.array(config["beta"], dtype="int32")
        self.thresPres = np.array(config["thresPres"], dtype="float32")
        self.extremeQuantiles = np.array(config["extremeQuantiles"], dtype="float32")
        self.thres = np.array(config["thres"], dtype="float32")
        self.mins = np.array(config["mins"], dtype="float32")
        self.maxs = np.array(config["maxs"], dtype="float32")
        
        # To calculate some latent parameters which could be deducated from the former parameters
        self.id_const = np.where(self.maxs == self.mins)[0]
        self.id_nonconst = np.where(self.maxs != self.mins)[0]
        self.xFilter = None

    def _check_nonvalid(self, data, beta=0.75, ab_min=20): #过滤输入数据无效值，保留有效值
        data = self.normalization(data)
        xFilter = None
        scores = []
        if len(self.valid_inds):
            for i, dataframe in enumerate(data):
                if xFilter is None:
                    xFilter_ = dataframe[self.valid_inds]
                else:
                    xFilter_ = (1 - self.beta) * dataframe[self.valid_inds] + self.beta * xFilter
                xResidu = dataframe[self.valid_inds] - xFilter_
                scores.append([
                    min(max(
                        (xRes_i - self.thresPres[i,0])/((1+self.q)*(self.extremeQuantiles[i,0] - self.thresPres[i,0])+self.thres[i])/2,
                        (self.thresPres[i,1]-xRes_i)/((1+self.q)*(self.thresPres[i,1]-self.extremeQuantiles[i,1])+self.thres[i])/2,
                        0),1) for i, xRes_i in enumerate(xResidu)])
                cons_ind = (np.array(scores[-1], dtype="float32") > 3.5)
                if xFilter is None:
                    xFilter = xFilter_
                else:
                    xFilter[~cons_ind] = xFilter_[~cons_ind]
                    xFilter[cons_ind] = dataframe[self.valid_inds][cons_ind]
            scores = np.array(scores, dtype="float32")
            ab_freq = (scores >= 0.5).max(axis=1).sum(axis=0)
            ind_freq = (scores >= 0.5).sum(axis=0)/(1+ab_freq)
            if ab_freq > min(ab_min, 0.1*len(data)):
                return np.where(ind_freq >= min(ind_freq.max()*0.75+ind_freq.min()*0.25, beta))[0].tolist()
            else :
                return []
        else:
            return []
        
    #根据训练好的模型生成规则
    def rule_induce(self, data, beta=0.9, eps=1e-5):
        nonvalid = self._check_nonvalid(data, beta=beta)
        extremeQuantiles = self.extremeQuantiles * (self.maxs-self.mins)[self.valid_inds, None]
     
        return _get_rule(extremeQuantiles, np.round(1/(self.beta+eps)),
                         self.thres, self.pnames, self.valid_inds, nonvalid, eps=eps)

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

