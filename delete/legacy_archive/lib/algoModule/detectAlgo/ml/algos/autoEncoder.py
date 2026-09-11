import numpy as np
import pandas as pd
import pickle
from time import time

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

import tensorflow as tf
from tensorflow.keras.models import model_from_json
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.initializers import RandomNormal
from tensorflow.keras.regularizers import L2
from tensorflow.keras.models import Model as tfModel

regularizer = L2(2.5e-8)
initializer = RandomNormal(stddev=0.1)

if __name__ == "__main__":
    from support.BaseAlgoClass import BaseModel #基础模型类，构建和训练算法
else:
    from .support.BaseAlgoClass import BaseModel

def _get_encoder(in_sh=50, feature_num=10):
    ## To-detect Data Input
    input_layer = Input(
        shape=(in_sh,)
        )

    layer1 = Dense(
        feature_num*4,
        use_bias=True,
        kernel_initializer=initializer,
        kernel_regularizer=regularizer,
        bias_initializer=initializer,
        bias_regularizer=regularizer,
        activation="relu"
        )(input_layer)

    output_layer = Dense(
        feature_num,
        use_bias=True,
        kernel_initializer=initializer,
        kernel_regularizer=regularizer,
        bias_initializer=initializer,
        bias_regularizer=regularizer,
        activation="relu"
        )(layer1)

    model = tfModel(
        inputs=input_layer, 
        outputs=output_layer, 
        name="encoder"
        )
    
    return model

def _get_decoder(in_sh=20, feature_num=10):
    ## To-detect Data Input
    input_layer = Input(
        shape=(feature_num,)
        )

    layer1 = Dense(
        feature_num*4,
        use_bias=True,
        kernel_initializer=initializer,
        kernel_regularizer=regularizer,
        bias_initializer=initializer,
        bias_regularizer=regularizer,
        activation="relu"
        )(input_layer)

    output_layer = Dense(
        in_sh,
        use_bias=True,
        kernel_initializer=initializer,
        kernel_regularizer=regularizer,
        bias_initializer=initializer,
        bias_regularizer=regularizer,
        activation="relu"
        )(layer1)

    model = tfModel(
        inputs=input_layer, 
        outputs=output_layer, 
        name="decoder"
        )
    
    return model

def KBest(data, early_stop=5):
    to_stop = 0
    sbest = 0
    kbest = 1
    try:
        for k in range(2, 20):
            estimator = KMeans(n_clusters=k)  # 构造聚类器
            estimator.fit(data)
            sk = silhouette_score(data, estimator.labels_, metric='euclidean')
            if sk > sbest:
                kbest = k
            else:
                to_stop += 1
            if to_stop > early_stop:
                break
    except Exception as e:
        print(f"@{__file__}, kbest=1. Exception occurs in KBest: {e}.")
    return kbest, estimator

class Model(BaseModel):
    def __init__(self, index=0, name="model", pnames=[], config={}, **kwargs):
        # Algorithm Body - START -> Credit  Configuration
        self._faultLevel = 1
        self._algoType = "AutoEncoder"
        self._zh_name = "自编码器"
        # Algorithm Body - END -> Credit Configuration
        
        # Algorithm Body - START -> HyperParameters  Configuration
        self.lr = 1e-5
        self.batch_size = 64
        self.epoches = 100 ## At Least 50
        self.feature_num = 20
        self._stop_loss = 1e-5
        self._k = 1
        # Algorithm Body - END -> HyperParameters  Configuration

        super().__init__(index=index, name=name, pnames=pnames, config=config, **kwargs)
        
    def set_config(self,config):
        try:
            self.lr = float(config["learning_rate"])
        except:
            pass
        try:
            self.batch_size = int(config["batch_size"])
        except:
            pass
        try:
            self.epoches = int(config["epoches"])
        except:
            pass
        try:
            self.feature_num = int(config["feature_num"])
        except:
            pass
        try:
            self._k = int(config["k"])
        except:
            pass
        try:
            self._stop_loss = float(config["stop_loss"])
        except:
            pass
        super().set_config(config)
        self._opt = tf.keras.optimizers.Adam(learning_rate=self.lr, beta_1=0.75, beta_2=0.8)
    
    def get_config(self):
        return{
            "learning_rate":self.lr, "batch_size":self.batch_size,
            "epoches": self.epoches, "feature_num": self.feature_num,
            "stop_loss": self._stop_loss, "k": self._k
            }

    def _train_step(self, in_y):
        with tf.GradientTape() as _tape:
            _pred = self._encoder(in_y, training=True)
            _out_y = self._decoder(_pred, training=True)
            _loss = tf.reduce_mean(tf.abs(_out_y - in_y))
            _grad = _tape.gradient(_loss,
                                   self._encoder.trainable_variables + self._decoder.trainable_variables)
            self._opt.apply_gradients(zip(_grad,
                                          self._encoder.trainable_variables + self._decoder.trainable_variables))
            self._cumloss += float(_loss.numpy())
        
    def fit(self, data, save=False, verbose=False):
        data = pd.DataFrame(self.merged_data(data)).fillna(method="ffill").fillna(method="bfill").values.astype(np.float)
        data = data[(~np.isnan(data)).any(axis=1)]
        self.trainTime = time()
        self.predictTime = 0.002 * data.size # follow O(M*N)
        if not self.trained:
            self.config_normalization(data)
            X = self.normalization(data)
        else:
            self.reconfig_normalization(data)
            X = self.normalization(data)

        ## 基于Encoder-Decoder实现特征的无监督挖掘
        X = np.reshape(X, (len(X), -1))
        self._encoder = _get_encoder(X.shape[1], self.feature_num)
        self._decoder = _get_decoder(X.shape[1], self.feature_num)
        batch_num = min(200, max(3, int(round(len(data)/self.batch_size))*3))
        for eid in range(self.epoches):
            self._cumloss = 0
            sid = np.random.permutation(batch_num*self.batch_size) % len(data)           
            for n in range(batch_num):
                self._train_step(
                    X[sid[n*self.batch_size:(n+1)*self.batch_size]]
                    )
            if self._cumloss/batch_num < self._stop_loss:
                break
            if verbose:
                print(f"Epoch {eid+1}:",self._cumloss)

        ## 基于KMeans实现特征的正常边界划定
        _labels = self._encoder.predict(data)
        self._k, self._estimator = KBest(_labels, early_stop=5)

        if save:
            self.save_model()
        self.trained = True
            
    def validate(self, data):
        scores = float("nan")*np.ones(data.shape[0], dtype="float32")
        ind = np.where((~np.isnan(data)).any(axis=1))[0]
        X = self.normalization(data[ind])
        ## 基于Encoder实现特征的提取
        _labels = self._encoder.predict(X)
        ## 基于KMeans实现特征的量化异常判读
        scores[ind] = self._estimator.transform(_labels).min(axis=-1)/2
        scores = np.where(~np.isnan(scores), scores, 0)
        scores[scores > 1] = 1; scores[scores < 0] = 0
        return list(np.where(scores>=0.5)[0]), scores.tolist(), [None, None]

    def to_json(self):
        """
        Load Special Configurations By Path
        """
        return pickle.dumps({
            "ae_info": self.get_config(),
            "encoder_model": self._encoder.to_json(),
            "decoder_model": self._decoder.to_json(),
            "estimator": self._estimator,
            "mins": self.mins.tolist(),
            "maxs": self.maxs.tolist()
        })

    def from_json(self, configJson=b""):
        """
        Load Special Configurations By Path
        """
        config = pickle.loads(configJson)
        self.set_config(config['ae_info'])
        self._encoder = model_from_json(config["encoder_model"])
        self._encoder = model_from_json(config["decoder_model"])
        self._estimator = config["estimator"]
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
