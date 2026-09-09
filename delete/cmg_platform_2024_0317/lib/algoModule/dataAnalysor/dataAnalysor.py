import numpy as np
import pandas as pd
from datetime import datetime
from vmdpy import VMD
from .FuncBase import evalOp
from .opParse import opParse

def _splitTrend(data):
    data = data[data.shape[0]%2:]
    data_ = np.zeros(len(data))
    try:
        u, _, _ = VMD(data, alpha=len(data), tau=np.diff(data).std(), K=10, \
                      DC=np.median(data), init=np.median(data[:20]), tol=np.diff(data).std()*0.01)
        for uComp in u:
            p = (uComp[:uComp.size//2] - uComp[-uComp.size//2:] > (uComp.max()-uComp.min())/10).sum()
            n = (uComp[:uComp.size//2] - uComp[-uComp.size//2:] < -(uComp.max()-uComp.min())/10).sum()
            if max(p,n) != 0 and min(p,n)/max(p,n)>0.75:
                break
            data_ += uComp
    except:
        data_ = np.ones(len(data))*np.median(data)
    return data_

def _getEnvelope(data, envelopeWindow=20):
    uppEnvelope = []
    lowEnvelope = []
    for i in range(len(data) - envelopeWindow):
        uppEnvelope.append([data[i:i+envelopeWindow].max()])
        lowEnvelope.append([data[i:i+envelopeWindow].min()])
    return pd.DataFrame(uppEnvelope).ewm(span=envelopeWindow//2).mean().values.flatten(), \
           pd.DataFrame(lowEnvelope).ewm(span=envelopeWindow//2).mean().values.flatten()

def convert_express(opExpress):
    opP = opParse()
    opStructedExpress = opP.convert(opExpress)
    return opStructedExpress, opP.relatPara

def calcul_express(data, opStructedExpress):
    return np.array(
        evalOp(data, opStructedExpress),
        dtype="float32").reshape(-1,1)

def analyse(timeIndex, values, ndigits=6):
    values = values.flatten()

    vlen = len(values)

    valind = np.where(~np.isnan(values))[0]

    values = values[valind]

    values_mean = values.mean()

    #fftValues = np.fft.fft(values - values_mean) + values_mean
    #fftAmplt = np.abs(fftValues)
    #fftPhase = np.angle(fftValues)
    
    trend = np.ones(vlen)*float("nan")
    res = _splitTrend(values-values_mean)+values_mean
    trend[valind[-len(res):]] = res

    xSupp = np.ones([len(trend[valind[1:]]),2])
    xSupp[:, 0] = np.arange(len(trend[valind[1:]]))
    abMat = np.dot(np.linalg.pinv(xSupp),trend[valind[1:], None])
    lineTrend = np.ones(vlen)*float("nan")
    lineTrend[valind] = abMat[0,0]*(np.arange(len(values))-len(values)+len(trend)) + abMat[1,0]

    uppEnv, lowEnv = _getEnvelope(values)
    
    baseInfo = [
        {
            "label": "最大值", # 0
            "value": round(float(values.max()), ndigits)
        },{
            "label": "最小值", # 1
            "value": round(float(values.min()), ndigits)
        },{
            "label": "平均值", # 2
            "value": round(float(values_mean), ndigits)
        },{
            "label": "标准差", # 3
            "value": round(float(values.std()), ndigits)
        },{
            "label": "1/4分位数", # 4
            "value": round(float(np.quantile(values, 0.25)), ndigits)
        },{
            "label": "中位数", # 5
            "value": round(float(np.median(values)), ndigits)
        },{
            "label": "3/4分位数", # 6
            "value": round(float(np.quantile(values, 0.75)), ndigits)
        },{
            "label": "累计数", # 7
            "value": round(float(values.sum()), ndigits)
        }]


    # dT = np.diff([float(t)/1e9-28800 for t in timeIndex]).mean()
    try:
        timeRange = [datetime.fromtimestamp(float(t)/1e9-28800).strftime("%Y/%m/%d %H:%M:%S") for t in timeIndex]
    except:
        timeRange = list(range(len(timeIndex)))
    #print([round(float(itm), ndigits) for itm in values])
    return {
        "baseInfo": baseInfo,
        "timeData": timeRange,
        "ruleData": [round(float(itm), ndigits) for itm in values],
        "supportData": [
            [round(float(itm), ndigits) for itm in trend],
            [round(float(itm), ndigits) for itm in lineTrend],
            [round(float(itm), ndigits) for itm in uppEnv],
            [round(float(itm), ndigits) for itm in lowEnv]
            ],
        "supportLabel": ["主趋势","线性拟合","上包络线", "下包络线"]
        }

def analyseByExpress(opExpress, timeIndex, paranames, values, ndigits=6):
    structedExpress, relatPara = convert_express(opExpress)
    """
    print("structedExpress=", structedExpress)
    print("relatPara=", relatPara)
    print("values=", np.array(values))
    print("paranames=", paranames)
    print("values=", np.array([values[paranames.index(pname)] if pname in paranames else [float("nan")]*len(values[0]) for pname in relatPara]))
    """
    values = calcul_express(np.array([values[paranames.index(pname)] if pname in paranames else [float("nan")]*len(values[0]) for pname in relatPara], dtype="float32").T, structedExpress)
    return analyse(timeIndex, values, ndigits=ndigits)

if __name__ == "__main__":
    res = analyse(np.random.random(100))
