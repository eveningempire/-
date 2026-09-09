import tensorflow as tf
from tensorflow.keras.models import model_from_json
import numpy as np
import os, json
from time import time

from .support import gan_models_

from .support.BaseAlgoClass import BaseModel

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.executing_eagerly()

class Model(BaseModel):
    def __init__(self, index=0, name="model", pnames=[], config={}, **kwargs):
        #index：模型索引   name：模型名称   pnames：列表，模型参数名称  config：字典，模型配置信息
        # Algorithm Body - START -> Credit  Configuration
        self._faultLevel = 1        #设置故障级别为1
        self._algoType = "gan"       #模型的算法类型
        self._zh_name = "对抗神经网络"  #模型的中文名称
        # Algorithm Body - END -> Credit Configuration
        
        ## HyperParameters
        self.d_iter = 5
        self.zn_dim = 100
        self.epoches = 20 # 调试时，可以将epoches调小，提高调试效率
        self.batchSize = 32
        self.l_s = 100
        self.s_w = max(int(self.l_s//4), 1)
        self.g_opt = tf.keras.optimizers.Adam(learning_rate=1e-4, beta_1=0.5, beta_2=0.9)
        self.d_opt = tf.keras.optimizers.Adam(learning_rate=1e-4, beta_1=0.5, beta_2=0.9)
        self.scale = 10
        self.g_rl_ratio = 0.4
        self.d_rl_ratio = 0.1
        ## HyperParameters

        super().__init__(index=index, name=name, pnames=pnames, config=config, **kwargs) #调用父类构造函数，初始化Model实例

    def setConfig(self,config):
        try:
            self.d_iter = int(config["d_iter"])
        except:
            pass
        try:
            self.zn_dim = int(config["zn_dim"])
        except:
            pass
        try:
            self.epoches = int(config["epoches"])
        except:
            pass
        try:
            self.batchSize = int(config["batchSize"])
        except:
            pass
        try:
            self.l_s = int(config["l_s"])
        except:
            pass
        try:
            self.s_w = int(config["s_w"])
        except:
            pass
        try:
            self.scale =  int(config["scale"])
        except:
            pass
        try:
            self.g_rl_ratio = float(config["g_rl_ratio"])
        except:
            pass
        try:
            self.d_rl_ratio = float(config["d_rl_ratio"])
        except:
            pass

    def getConfig(self):
        return{"d_iter":self.d_iter, "zn_dim":self.zn_dim, "epoches":self.epoches, "batchSize":self.batchSize,\
               "l_s":self.l_s,"s_w":self.s_w,"scale":self.scale,"g_rl_ratio":self.g_rl_ratio,"d_rl_ratio":self.d_rl_ratio}

    def _calc_penalty(self, realSample, artificialSample):  # gradient panelty for WGAN-GP
        eps = tf.random.uniform([realSample.shape[0], 1, 1, 1], 0.0, 0.1)
        x_hat = eps * realSample  + (1 - eps) * artificialSample
        with tf.GradientTape() as penalty_tape:
            penalty_tape.watch(x_hat)
            pred = self.discriminator(x_hat)
        ddx = penalty_tape.gradient(pred, x_hat)
        ddx = tf.sqrt(tf.reduce_sum(tf.square(ddx), axis=1) + 1e-8)
        ddx = tf.reduce_mean(tf.square(ddx - 1.0) * self.scale)
        return ddx
    
    def _train_step(self, realSample, reinforce=False):
        zn = np.random.normal(0, 1, [realSample.shape[0], self.zn_dim])
        zn_exp = np.exp(zn)
        zn = zn_exp / zn_exp.sum(axis=1)[:,None]
        with tf.GradientTape() as g_tape, tf.GradientTape() as d_tape, tf.GradientTape() as e_tape:
            realPred = self.discriminator(realSample, training=True)
            ## ge
            artificialSample = self.generator(zn, training=True)
            artificialPred = self.discriminator(artificialSample, training=True)
            # for every d_iter iterations of the discriminator, iterate generator_encoder once
            if reinforce:
                softArtificialLabel = self.g_rl_ratio*artificialPred.numpy() + (1-self.g_rl_ratio)#*1
                softArtificialSample = self.g_rl_ratio*artificialSample.numpy() + (1-self.g_rl_ratio)*realSample
                self.g_loss = tf.reduce_mean(softArtificialLabel - artificialPred) \
                              + 0.1*self._calc_penalty(softArtificialSample, artificialSample)
            else:
                self.g_loss = tf.reduce_mean(1-artificialPred) + 0.1*self._calc_penalty(realSample, artificialSample)
            if self.iter == self.d_iter:
                g_grad = g_tape.gradient(self.g_loss,
                                           self.generator.trainable_variables)
                self.g_opt.apply_gradients(zip(g_grad,
                                                self.generator.trainable_variables))
                self.iter = 0
            else:
                if reinforce:
                    softArtificialLabel = self.g_rl_ratio*artificialPred.numpy() # + (1-self.g_rl_ratio)*0
                    softRealLabel = self.d_rl_ratio*realPred.numpy() + (1-self.d_rl_ratio)#*1
                    self.d_loss = tf.reduce_mean(artificialPred - softArtificialLabel) \
                                  + tf.reduce_mean(softRealLabel - realPred)
                else:
                    self.d_loss = tf.reduce_mean(artificialPred) + tf.reduce_mean(1-realPred)
                d_grad = d_tape.gradient(self.d_loss,
                                         self.discriminator.trainable_variables)
                self.d_opt.apply_gradients(zip(d_grad,
                                               self.discriminator.trainable_variables))

    def _windowize(self, data, train=True):
        dataLen = len(data)
        if train:
            arr = [data[i*self.s_w : i*self.s_w + self.l_s] \
                   for i in range((dataLen - self.l_s) // self.s_w)]
            if (dataLen - self.l_s) % self.s_w != 0:
                arr.append(data[-self.l_s:])
        else:
            s_w = max(self.l_s // 2, 1)
            arr = [data[i*s_w : i*s_w + self.l_s] \
                   for i in range((dataLen - self.l_s) // s_w)]
            if (dataLen - self.l_s) % s_w != 0:
                arr.append(data[-self.l_s:])
        m = len(arr); n, p = arr[0].shape
        return np.reshape(arr, (m, n, p, 1))

    def _batchize(self, data):
        return [data[i * self.batchSize: (i+1) * self.batchSize, :, :, :] \
                for i in range(len(data)//self.batchSize)]

    def to_json(self):
        return json.dumps({
                "g_model": self.generator.to_json(),
                "d_model": self.discriminator.to_json(),
                "maxs": list(map(float, self.maxs)),
                "mins": list(map(float, self.mins))
            }).encode()                      #@yhc二进制编码

    def from_json(self, config=""):
        config = json.loads(config.decode()) #@yhc加载二进制编码
        self.generator = model_from_json(config["g_model"], \
                                         custom_objects={'DotLayer': gan_models_.DotLayer,
                                                                         'LeakyReLU': gan_models_.LeakyReLU,
                                                                         'BatchNorm': gan_models_.BatchNorm})
        self.discriminator = model_from_json(config["d_model"], \
                                             custom_objects={'DotLayer': gan_models_.DotLayer,
                                                                             'LeakyReLU': gan_models_.LeakyReLU,
                                                                             'BatchNorm': gan_models_.BatchNorm})
        self.maxs = np.array(config["maxs"], dtype="float64")
        self.mins = np.array(config["mins"], dtype="float64")
        self.id_const = np.where(self.maxs==self.mins)[0]
        self.id_nonconst = np.where(self.maxs!=self.mins)[0]

    def merged_batches(self,data):
        batches = []
        total_data_size = 0
        for data_ in data:
            data_ = data_[(~np.isnan(data_)).any(axis=1)]
            total_data_size += data_.size 
            if not self.trained:
                self.config_normalization(data_)
                x_sh = (self.l_s, data_.shape[-1])
                self.generator = gan_models_.generator(in_sh=(self.zn_dim,), out_sh=x_sh)
                self.discriminator = gan_models_.discriminator(in_sh=(x_sh[0], x_sh[1], 1))  
            else:
                self.reconfig_normalization(data_)        
            X = self._windowize(self.normalization(data_))
            batches = batches + self._batchize(X)
        self.predictTime = 8e-5 * total_data_size
        return batches

    def fit(self, data, save=False):
        self.trainTime = time()       
        batches = self.merged_batches(data)
        trainTime = 0; batchLen = len(batches)
        for epoch in range(self.epoches):
            self.iter = 0
            for batchNum in np.random.permutation(batchLen):
                t = time()
                self._train_step(batches[batchNum], reinforce=self.trained)
                self.iter += 1
                time_act = time() - t
                trainTime += time_act
                self.predictTime = trainTime/(batchNum + 1 + self.epoches*batchLen) \
                                   * (batchLen-1 -batchNum + (self.epoches-1-self.epoches)*batchLen)
        if save:
            self.save_model()
        self.trained = True

    def validate_score(self, data):
        X = self._windowize(self.normalization(data))
        Xlen = len(X)
        score_ = np.ones(Xlen)
        for i in range(int(np.ceil(Xlen/100))):
            pred = self.discriminator(X[i*100:(i+1)*100,...], training=False)
            score_[i*100:(i+1)*100,] = 1 - pred.numpy().flatten()

        score = np.ones(data.shape[0])
        s_w = max(self.l_s // 2, 1)
        dataLen = len(data)
        for i in range((dataLen - self.l_s) // s_w):
            score_w = score[i*s_w : i*s_w + self.l_s]
            score_w[score_w>score_[i]] = score_[i]
            score[i*s_w : i*s_w + self.l_s] = score_w
        if (dataLen - self.l_s) % s_w != 0:
            score_w = score[-self.l_s:]
            score_w[score_w>score_[i+1]] = score_[i+1]
            score[-self.l_s:] = score_w
        return score

    def validate(self, data):
        data = self.merged_data(data)
        score = self.validate_score(data)
        score = np.where(~np.isnan(score), score, 0)
        score[score>1] = 1; score[score<0] = 0
        return list(np.where(score>=0.5)[0]), list(score), [None, None]

if __name__ == "__main__":
    # Test Case 测试用例
    import pandas as pd
    import os
    from time import time
    DIR = "testCaseData"

    def calcul_acc(abList, realLabel):
        preLabel = np.zeros(len(realLabel))
        if len(abList):
            preLabel[abList] = 1
        TP = np.sum((preLabel == 0) * (realLabel == 0))
        FP = np.sum((preLabel == 0) * (realLabel == 1))
        FN = np.sum((preLabel == 1) * (realLabel == 0))
        TN = np.sum((preLabel == 1) * (realLabel == 1))
        print(TP, FP, FN, TN)
        P = TP/(TP+FP)
        R = TP/(TP+FN)
        F1 = 2*P*R/(P+R)
        acc = (TP+TN)/(TP+TN+FP+FN)
        return P, R, F1, acc

    model = Model()

    data_name = ['train_data1.csv','train_data2.csv','train_data3.csv','train_data4.csv']
    data_name = ["data.csv"]
    trainData = []
    paras = ["DT的侧滑角_βa", "DT的攻角_αa", "DT的姿态角_γm", "DT的姿态角_φm", "DT的姿态角_ψm", 
            "DD在惯性系下的速度_Vxm", "DD在惯性系下的速度_Vym", "DD在惯性系下的速度_Vzm"]
    paras = ["DCL_B2", "DCL_B3", "DCL_B_V"]
    for data_name in data_name:
        #train_data = np.array(pd.DataFrame(pd.read_csv(os.path.join(DIR, data_name),encoding="gbk")), dtype="float32")
        #trainData.append(train_data)
        train_data = pd.read_csv(os.path.join(DIR, data_name), index_col=0, encoding="gbk").fillna(method="ffill", limit=5)
        train_data = train_data.loc[::20, paras].values.astype("float32")
        trainData.append(train_data)
    '''
    train_data = []
    for data_name in data_name:
        trainData = np.array(pd.DataFrame(pd.read_csv(os.path.join(DIR, data_name))), dtype="float32")[:,:16]   
        train_data.append(trainData)
    '''
    print("=====\tTrain\t=====")
    t = time()
    model.fit(trainData)
#    print(f"Parameters' Dimension :\t{trainData.shape}")
#    print(f"Time cost :\t{round((time()-t)/trainData.shape[0]*1000,5)} ms/frame")

    config = model.to_json()
    print("aaaaaaaaaaaaaaaaaaaaaaah", type(config))
    print("over train")

    #暂存模型参数至txt文件,可删除

    path = f"../modelConfig/gan_{'_'.join(paras)}_config.txt"
    try:
        with open(path, 'wb+') as f:
            f.write(config)
    except:
        print("can not write in file!!!")

'''
    model = Model()
    model.from_json(config)

    testData = np.array(pd.DataFrame(pd.read_csv(os.path.join(DIR, "test_data.csv"))), dtype="float32")
    testLabel = testData[:, -1]
    testData = testData[:, :16]


    print("\n=====\tTest\t=====")
    t = time()
    abList, score_list, _ = model.validate(testData)
    print(f"Detect Speed :\t{round((time()-t)/testData.shape[0]*1000,5)} ms/frame")

    print("P:%.3f||R:%.3f||F1:%.3f||acc:%.3f" % calcul_acc(abList, testLabel))
'''
