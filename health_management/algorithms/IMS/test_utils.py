import numpy as np
import pandas as pd
import os
from typing import Iterable
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties
plt.rc("font", family="Times New Roman", size=16)   #font设置字体大小;family设置字体样式;
plt.rcParams["font.sans-serif"] = "SimHei"      #设置中文字体为黑体
plt.rcParams["axes.unicode_minus"] = False      #将负号正常显示
FONT = FontProperties(fname=os.path.join(r".", "support", "simhei.ttf"), size=16)   #设置matplotlib绘图时使用的字体


def _auc_calculate(preLabel, realLabel, n_bins=100):
    preLabel = np.array(preLabel, dtype="float32")
    realLabel = np.array(realLabel, dtype="float32")
    postive_len = np.sum((realLabel <= 0.5))   #正样本数量（因为正样本都是1）
    negative_len = np.sum((realLabel > 0.5)) #负样本数量
    total_case = postive_len * negative_len #正负样本对
    pos_histogram = [0 for _ in range(n_bins)] 
    neg_histogram = [0 for _ in range(n_bins)]
    bin_width = 1.0 / n_bins
    for i in range(len(realLabel)):
        nth_bin = min(int(preLabel[i]/bin_width), n_bins-1)
        if realLabel[i]==1:
            pos_histogram[nth_bin] += 1
        else:
            neg_histogram[nth_bin] += 1
    accumulated_neg = 0
    satisfied_pair = 0
    for i in range(n_bins):
        satisfied_pair += (pos_histogram[i]*accumulated_neg + pos_histogram[i]*neg_histogram[i]*0.5)
        accumulated_neg += neg_histogram[i]
    return satisfied_pair / float(total_case) if float(total_case) != 0 else 0

def calcul_sparse_acc(abList, realLabel):
    """[面向性能评估] 预测异常帧与实际标签的对比
    [Inputs]
    `abList: List[Integer], 异常帧的坐标
    `realLabel: List[float], 实际异常指标
    [Outputs]
    `result: Dict[str, float], 对比结果
    """
    preLabel = np.zeros(len(realLabel))
    if len(abList):
        preLabel[abList] = 1
    return calcul_acc(preLabel, realLabel)

def calcul_acc(preLabel, realLabel, n_bins=100):
    """[面向性能评估] 预测标签与实际标签的对比
    [Inputs]
    `preLabel: List[float], 预测异常指标
    `realLabel: List[float], 实际异常指标
    [Outputs]
    `result: Dict[str, float], 对比结果
    """
    preLabel = np.array(preLabel, dtype="float32")
    preLabel = np.where(~np.isnan(preLabel), preLabel, 0.0)
    realLabel = np.array(realLabel, dtype="float32")
    nTP = np.sum((preLabel <= 0.5) * (realLabel <= 0.5))
    nFP = np.sum((preLabel <= 0.5) * (realLabel > 0.5))
    nFN = np.sum((preLabel > 0.5) * (realLabel <= 0.5))
    nTN = np.sum((preLabel > 0.5) * (realLabel > 0.5))
    s_P = nTP/(nTP+nFP) if nFP != 0 else 1
    s_R = nTP/(nTP+nFN) if nFN != 0 else 1
    s_F1 = 2*s_P*s_R/(s_P+s_R) if nTP != 0 else float(int(nFP + nFN != 0))
    acc = (nTP+nTN)/(nTP+nTN+nFP+nFN)
    bacc = ((nTP/(nTP+nFN) if nFN != 0 else 1) + (nTN/(nTN+nFP) if nFP != 0 else 1))/2
    auc = _auc_calculate(preLabel, realLabel, n_bins=n_bins)
    return {"P": s_P, "R": s_R, "F1": s_F1, "acc": acc, "bacc": bacc, "auc": auc}

def _inner_test_process(mdlClass, trainPath, testPath, pnames=None, nlimit=5, nstep=1):
    """[面向性能评估] 数据集上的算法性能评估
    [Inputs]
    `mdlClass: Object, 算法类
    `trainPath: str, 训练数据集路径
    `testPath: str, 检测数据集路径（异常标签的类名为"label"）
    `pnames: List[str], 参数名称（缺省则直接录入训练集列名）
    `nlimit: Integer, 向后补值的最大范围
    `nstep: Integer, 重采样频率
    [Outputs]
    `result: Dict[str, float], 对比结果
    """
    try:
        train_data = pd.read_csv(trainPath, index_col=0, encoding="gbk").fillna(method="ffill", limit=nlimit).dropna(how="any", axis=1)
    except:
        train_data = pd.read_csv(trainPath, index_col=0).fillna(method="ffill", limit=nlimit).dropna(how="any", axis=1)
    if pnames is None:
        pnames = [l for l in train_data.columns.values if l!="label"]
    train_data = train_data.loc[::nstep, pnames].values.astype("float32")

    datasetname = trainPath.split("\\")[-2]  #将训练集路径逐个分割，取倒数第二个如D:\testCaseData\ALFA\data_test.csv,则为ALFA
    
    model = mdlClass(pnames=pnames)
    model.fit(train_data, save=False)       #将训练数据（原始数据集路径）进行训练
    
    try:
        test_data = pd.read_csv(testPath, index_col=0, encoding="gbk").fillna(method="ffill", limit=nlimit)
    except:
        test_data = pd.read_csv(testPath, index_col=0).fillna(method="ffill", limit=nlimit)
    try:
        realLabel = test_data.loc[::nstep, "label"].values.astype("int32")
    except:
        realLabel = np.ones(len(test_data.loc[::nstep]), dtype="float32")

    if not os.path.exists("./Figure_dspot"):
        os.mkdir("./Figure_dspot")
    if not os.path.exists(rf"./Figure_dspot/{datasetname}"):
        os.mkdir(rf"./Figure_dspot/{datasetname}")
    
    test_data = test_data.loc[::nstep, pnames].values.astype("float32")
    ablist, scores, suppInfo = model.validate(test_data)    #获取各个参数的阈值suppInfo，validate(test_data)，对已经注入故障的数据进行验证

    suppData, suppLabel = suppInfo
    suppData = np.array(suppData, dtype="float32")
    for pid, pn in enumerate(pnames):      #将pnames整为迭代对象,pid为pnames中的每个元素编号，test_data[:, pid]取出第pid列的所有元素
        plt.figure(figsize=(12,10))
        plt.fill_between(np.arange(len(realLabel)), test_data[:, pid].max(), test_data[:, pid].min(), where=(realLabel>=0.5), color="r", alpha=0.4)
        plt.plot(test_data[:, pid], "b", linewidth=1., label="参数值")
        plt.scatter(ablist, test_data[ablist, pid], marker="o", c="r", label="异常帧")
        if suppLabel is not None:
            for lid, lab in enumerate(suppLabel):
                suppD = suppData[pid,lid,:]     #lid为0,1;pid为各个参数从0开始的编号,suppData[:,0,0]第一个参数的上阈值。
                plt.plot(np.arange(len(suppD)), suppD, "--", c="orange", linewidth=1., label=lab)   #lab为标签，上阈值与下阈值
        labels = plt.legend().get_texts()   #获取曲线图例的文本
        for label_ in labels:
            label_.set_fontproperties(FONT) #将图例文本更改为设置的字体样式
        plt.tight_layout()      #自动调整图形的布局
        plt.savefig(rf"./Figure_dspot/{datasetname}/{pn}.png")
        plt.close()

    return calcul_acc(scores, realLabel)

def _inner_get_rule(mdlClass, trainPath, testPath, pnames=None, nlimit=5, nstep=1):
    """[面向性能评估] 数据集上的算法性能评估
    [Inputs]
    `mdlClass: Object, 算法类
    `trainPath: str, 训练数据集路径
    `testPath: str, 检测数据集路径（异常标签的类名为"label"）
    `pnames: List[str], 参数名称（缺省则直接录入训练集列名）
    `nlimit: Integer, 向后补值的最大范围
    `nstep: Integer, 重采样频率
    [Outputs]
    `result: Dict[str, float], 对比结果
    """
    try:
        train_data = pd.read_csv(trainPath, index_col=0, encoding="gbk").fillna(method="ffill", limit=nlimit).dropna(how="any", axis=1)
    except:
        train_data = pd.read_csv(trainPath, index_col=0).fillna(method="ffill", limit=nlimit).dropna(how="any", axis=1)
    if pnames is None:
        pnames = [l for l in train_data.columns.values if l!="label"]
    train_data = train_data.loc[::nstep, pnames].values.astype("float32")

    model = mdlClass(pnames=pnames)
    fit_time = model.fit(train_data, save=False)

    
    try:
        test_data = pd.read_csv(testPath, index_col=0, encoding="gbk").fillna(method="ffill", limit=nlimit)
    except:
        test_data = pd.read_csv(testPath, index_col=0).fillna(method="ffill", limit=nlimit)
    try:
        realLabel = test_data.loc[::nstep, "label"].values.astype("int32")
    except:
        realLabel = np.ones(len(test_data.loc[::nstep]), dtype="float32")
    test_data = test_data.loc[::nstep, pnames].values.astype("float32")
    return {
        "null_rule": model.rule_induce(train_data),
        "rule": model.rule_induce(test_data),
        "fit_time": fit_time
        
        }

def test_process(mdlClass, dataPathMap, nlimit=5, nstep=1):
    """[面向性能评估] 数据集上的算法性能评估
    [Inputs]
    `mdlClass: Object, 算法类
    `trainPath: str, 训练数据集路径
    `testPath: str, 检测数据集路径（异常标签的类名为"label"）
    `pnames: List[str], 参数名称（缺省则直接录入训练集列名）
    `nlimit: Integer, 向后补值的最大范围
    `nstep: Integer, 重采样频率
    [Outputs]
    `result: Dict[str, float], 对比结果
    """
    res = {}
    for dId, dataConfig in enumerate(dataPathMap):
        if len(dataConfig) == 2:
            dataDir, pnames = dataConfig
        else:
            dataDir = dataConfig
            pnames = None
        if isinstance(nstep, Iterable):
            nstep_ = nstep[dId]
        else:
            nstep_ = nstep
        trainPath = os.path.join(dataDir, "data.csv")
        testPath = os.path.join(dataDir, "data_test.csv")
        res[dataDir.split("\\")[-1] + "(" + "/".join(pnames or ["all"]) + ")"] = _inner_test_process(mdlClass, trainPath, testPath, pnames=pnames, nlimit=nlimit, nstep=nstep_)
    return res

def get_rule(mdlClass, dataPathMap, nlimit=5, nstep=1):
    """[面向性能评估] 数据集上的算法性能评估
    [Inputs]
    `mdlClass: Object, 算法类
    `trainPath: str, 训练数据集路径
    `testPath: str, 检测数据集路径（异常标签的类名为"label"）
    `pnames: List[str], 参数名称（缺省则直接录入训练集列名）
    `nlimit: Integer, 向后补值的最大范围
    `nstep: Integer, 重采样频率
    [Outputs]
    `result: Dict[str, float], 对比结果
    """
    res = {}
    for dId,dataConfig in enumerate(dataPathMap):
        if len(dataConfig) == 2:
            dataDir, pnames = dataConfig
        else:
            dataDir = dataConfig
            pnames = None
        if isinstance(nstep, Iterable):
            nstep_ = nstep[dId]
        else:
            nstep_ = nstep
        trainPath = os.path.join(dataDir, "data.csv")
        testPath = os.path.join(dataDir, "data_test.csv")
        res[dataDir.split("\\")[-1] + "(" + "/".join(pnames or ["all"]) + ")"] = _inner_get_rule(mdlClass, trainPath, testPath, pnames=pnames, nlimit=nlimit, nstep=nstep_)
    return res

def draw_figures(dataPathMap, figDir=r".\figures", nlimit=5, nstep=1):
    if not os.path.exists(figDir):
        os.mkdir(figDir)
            
    for dataConfig in dataPathMap:
        if len(dataConfig) == 2:
            dataDir, pnames = dataConfig
        else:
            dataDir = dataConfig
            pnames = None
        trainPath = os.path.join(dataDir, "data.csv")
        testPath = os.path.join(dataDir, "data_test.csv")
        try:
            train_data = pd.read_csv(trainPath, index_col=0, encoding="gbk").fillna(method="ffill", limit=nlimit).dropna(how="any", axis=1)
        except:
            train_data = pd.read_csv(trainPath, index_col=0).fillna(method="ffill", limit=nlimit).dropna(how="any", axis=1)
        if pnames is None:
            pnames = [l for l in train_data.columns.values if l!="label"]
        train_data = train_data.loc[::nstep, pnames].values.astype("float32")

        if not os.path.exists(os.path.join(figDir, dataDir.split("\\")[-1])):
            os.mkdir(os.path.join(figDir, dataDir.split("\\")[-1]))
        
        try:
            test_data = pd.read_csv(testPath, index_col=0, encoding="gbk").fillna(method="ffill", limit=nlimit)
        except:
            test_data = pd.read_csv(testPath, index_col=0).fillna(method="ffill", limit=nlimit)
        try:
            realLabel = test_data.loc[::nstep, "label"].values.astype("int32")
        except:
            realLabel = np.ones(len(test_data.loc[::nstep]), dtype="float32")
        test_data = test_data.loc[::nstep, pnames].values.astype("float32")
        for trainv, testv, pname in zip(train_data.T, test_data.T, pnames):
            if pname == "label":
                continue
            fig = plt.figure(figsize=(12,10))
            data = trainv.tolist()+testv.tolist()
            data_upp = max(data); data_low = min(data); data_amp = (data_upp-data_low) or 1
            data_upp += data_amp/10; data_low -= data_amp/10
            x = np.arange(len(trainv) + len(testv))
            plt.fill_between(x, data_low, data_upp, facecolor = "#ffc0cb", where=(np.append(np.zeros(len(trainv)), realLabel)>0.5))
            plt.plot(x, data)
            plt.ylim([data_low, data_upp])
            plt.title(pname)
            plt.tight_layout()
            plt.savefig(os.path.join(figDir, dataDir.split("\\")[-1], f"{pname}.png"))
            plt.close()
    return

if __name__ == "__main__":
    preLabel = np.random.uniform(0,1, (1000,))
    realLabel = np.array(np.random.uniform(0,1, (1000,)) > 0.5, dtype="int8")
    
    res = calcul_acc(preLabel, realLabel)
    print(res)
    
    DIR = r"..\testCaseData"
    draw_figures([
        [os.path.join(DIR, 'missile'), ["Vxm","Vym","Vzm","αa","βa","γm","φm","ψm"]],
        os.path.join(DIR, 'rocket'),
        os.path.join(DIR, 'ALFA'),
        os.path.join(DIR, 'KDD99'),
        os.path.join(DIR, 'MSL'),
        os.path.join(DIR, 'SMAP')
        ])
