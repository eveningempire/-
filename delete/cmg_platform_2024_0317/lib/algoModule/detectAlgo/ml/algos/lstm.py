import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.initializers import RandomNormal
from tensorflow.keras.regularizers import L2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout, Permute
from tensorflow.keras.models import model_from_json
from time import time
import warnings, json

if __name__ == "__main__":
    from support.BaseAlgoClass import BaseModel
else:
    from .support.BaseAlgoClass import BaseModel

class Model(BaseModel):
    def __init__(self, index=0, name="model", pnames=[], config={}, **kwargs):
        # Algorithm Body - START -> Credit  Configuration
        self._faultLevel = 1
        self._algoType = "LSTM"
        self._zh_name = "长短期记忆网络"
        # Algorithm Body - END -> Credit Configuration
        
        # Algorithm Body - START -> HyperParameters  Configuration
        self.backStep = 20
        self.forwardStep = 5
        self.epochs = 150
        self.model = None
        self.thres_max = 5
        # Algorithm Body - END -> HyperParameters  Configuration

        super().__init__(index=index, name=name, pnames=pnames, config=config, **kwargs)

    def set_config(self, config):
        try:
            self.backStep = int(config['backStep'])
        except:
            pass
        try:
            self.forwardStep = int(config['forwardStep'])
        except:
            pass
        try:
            self.epochs = int(config['epochs'])
        except:
            pass
        try:
            self.thres_max = float(config['thres_max'])
        except:
            pass
        self.regularizer = L2(2.5e-5)
        self.initializer = RandomNormal(stddev=0.02)
        self._windowStep = config.get("windowStep", self.backStep+self.forwardStep)
        super().set_config(config)

    def get_config(self):
        return {"backStep":self.backStep, "forwardStep":self.forwardStep, "epochs":self.epochs}

    def _createDataset(self, data):
        data_x, data_y = zip(*[[itm[:self.backStep], itm[self.backStep:]] for itm in self.windowize(data)])
        return np.array(data_x, dtype="float32"), np.array(data_y, dtype="float32")

    def _createModel(self, dLen):
        model = Sequential()
        model.add(LSTM(dLen, return_sequences=True, \
            kernel_regularizer=self.regularizer, bias_regularizer=self.regularizer, \
                recurrent_regularizer=self.regularizer,kernel_initializer=self.initializer, \
                    bias_initializer=self.initializer, recurrent_initializer=self.initializer, \
                        input_shape=(self.backStep, dLen))) ## @JZU LSTM默认是[batch,时间维度, 特征维度]
        model.add(Permute((2,1)))
        model.add(Dropout(0.2))
        model.add(Dense(self.forwardStep, kernel_regularizer=self.regularizer, \
            bias_regularizer=self.regularizer, kernel_initializer=self.initializer, \
                bias_initializer=self.initializer))
        model.add(Permute((2,1)))
        model.compile(loss='mean_squared_error', optimizer='adam')
        return model

    def fit(self, data, save=False, verbose=0):
        data = pd.DataFrame(self.merged_data(data)).fillna(method="ffill").fillna(method="bfill").values.astype("float32")
        #data = data[(~np.isnan(data)).any(axis=1)]
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
            self.model = self._createModel(X.shape[-1])
        else:
            self.reconfig_normalization(data)
            X = self.normalization(data)
            
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dataX, dataY = self._createDataset(data) ## @JZU [batch,时间维度, 特征维度]
            self.model.fit(dataX, dataY, epochs=self.epochs, batch_size=12, verbose=verbose)
            err_ = np.mean((dataY - self.model.predict(dataX)).reshape(-1,dataX.shape[-1])**2, axis=0)
            self._thres_min = np.maximum(3*err_, 1e-9)
            self.valid_inds = np.where(self._thres_min <= self.thres_max)[0]
        if save:
            self.save_model()  # @Editor: Save model 保存模型
        self.trained = True
    
    def validate(self, data):
        scores = float("nan")*np.ones(data.shape, dtype="float32")
        subData = float("nan")*np.ones(data.shape, dtype="float32")
        supData = float("nan")*np.ones(data.shape, dtype="float32")
        ind = np.where((~np.isnan(data)).any(axis=1))[0]
        X = self.normalization(data[ind])

        dataX, dataY = self._createDataset(X)
        dataY_pred = self.model.predict(dataX)
        residual = np.mean((dataY - dataY_pred)**2, axis=1)
        sliceRes = (residual/2/self._thres_min)[:, self.valid_inds].max(axis=1)
        scores_ = np.ones(X.shape, dtype="float32")
        subData_ = - np.ones(X.shape, dtype="float32")*float("inf")
        supData_ = np.ones(X.shape, dtype="float32")*float("inf")
        for i, sco_ in enumerate(sliceRes):
            scores_[i*self._offlineSpanStep+self.backStep:i*self._offlineSpanStep+self._windowStep, self.valid_inds] = np.minimum(
                scores_[i*self._offlineSpanStep+self.backStep:i*self._offlineSpanStep+self._windowStep, self.valid_inds], 
                sco_)
            supData_[i*self._offlineSpanStep+self.backStep:i*self._offlineSpanStep+self._windowStep, self.valid_inds] = np.maximum(
                supData[i*self._offlineSpanStep+self.backStep:i*self._offlineSpanStep+self._windowStep, self.valid_inds], 
                dataY_pred[i][:, self.valid_inds]+self._thres_min[self.valid_inds])
            subData_[i*self._offlineSpanStep+self.backStep:i*self._offlineSpanStep+self._windowStep, self.valid_inds] = np.minimum(
                subData[i*self._offlineSpanStep+self.backStep:i*self._offlineSpanStep+self._windowStep, self.valid_inds], 
                dataY_pred[i][:, self.valid_inds]-self._thres_min[self.valid_inds])
        scores[ind] = scores_
        subData[ind] = np.where(~np.isinf(subData_), subData_, X)
        supData[ind] = np.where(~np.isinf(supData_), supData_, X)
        scores = np.where(~np.isnan(scores), scores, 0)
        scores[scores > 1] = 1; scores[scores < 0] = 0
        abList = list(np.where(scores.max(axis=-1)>=0.5)[0])
        subData = self.anti_normalization(np.array([subData], dtype="float32"))[0].T.tolist()
        supData = self.anti_normalization(np.array([supData], dtype="float32"))[0].T.tolist()
        return abList, scores.tolist(), [[list(itm) for itm in zip(subData, supData)], ["下阈值","上阈值"]]

    def to_json(self):
        """
        Load Special Configurations By Path
        """
        return json.dumps({
            "lstm_info": self.get_config(),
            "valid_ind": self.valid_ind.tolist(),
            "thres_min": self._thres_min.tolist(),
            "model": self.model.to_json(),
            "mins": self.mins.tolist(),
            "maxs": self.maxs.tolist()
        }).encode()

    def from_json(self, configJson=b""):
        """
        Load Special Configurations By Path
        """
        config = json.loads(configJson.decode())
        self.set_config(config['lstm_info'])
        self.valid_ind = np.array(config["valid_ind"], dtype="int32")
        self._thres_min = np.array(config["thres_min"], dtype="float32")
        self.model = model_from_json(config["model"])
        self.mins = np.array(config["mins"], dtype="float32")
        self.maxs = np.array(config["maxs"], dtype="float32")
        
        # To calculate some latent parameters which could be deducated from the former parameters
        self.id_const = np.where(self.maxs == self.mins)[0]
        self.id_nonconst = np.where(self.maxs != self.mins)[0]
        self.xFilter = None


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
