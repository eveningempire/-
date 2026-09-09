import numpy as np
import pandas as pd

def generator_norm(N_relat = [[500,5001]] + [[0,1] for _ in range(500)] + [[500,1000], [20,50],[20,50],[5,20],[5,20]]):

    x1 = np.zeros(25000)
    x1[12000:12500] = 0.5
    x1[12500:13000] = 1
    x1[13000:14000] = 1.5
    x1[14000:15500] = 2

    x2 = np.zeros(25000)
    N_r = [np.random.randint(n_min, n_max) for n_min,n_max in N_relat[1:]]
    x2[12000+N_r[0]:12500+N_r[0]] = 1.5*(1-np.exp(-np.arange((12500+N_r[0])-(12000+N_r[0]))/100))
    x2[12350+N_r[0]:12500+N_r[0]] -= 3*(np.arange(150)/1600)**2
    x2[12500+N_r[0]:13000+N_r[1]] = 1.75*(1-np.exp(-np.arange((13000+N_r[1])-(12500+N_r[0]))/100)) + 1.25
    x2[12850+N_r[1]:13000+N_r[1]] -= 3*(np.arange(150)/1600)**2
    x2[13000+N_r[1]:14000+N_r[2]] = 2*(1-np.exp(-np.arange((14000+N_r[2])-(13000+N_r[1]))/100)) + 2.5
    x2[13750+N_r[2]:14000+N_r[2]] -= 3*(np.arange(250)/2400)**2
    x2[14000+N_r[2]:15500+N_r[3]] = 2.25*(1-np.exp(-np.arange((15500+N_r[3])-(14000+N_r[2]))/100)) + 3.75
    x2[15000+N_r[3]:15500+N_r[3]] -= 3*(np.arange(500)/3200)**2
    x2[12050+N_r[0]:15500+N_r[3]] += 0.2*np.random.uniform(-1,1,(15500+N_r[3])-(12050+N_r[0]))
    x2[12000+N_r[0]:15500+N_r[3]] *= 0.99 + 0.01*np.sin(np.arange((15500+N_r[3])-(12000+N_r[0]))/750*2*np.pi)
    x2[12050+N_r[0]:15500+N_r[3]] = np.maximum(0, x2[12050+N_r[0]:15500+N_r[3]])

    x3 = np.zeros(25000)
    dx = 0.00001 + x2/30000
    N_r0 = np.random.randint(N_relat[0][0], N_relat[0][1])
    x3[12000-N_r0:15500+N_r[3]] = np.cumsum(dx[12000-N_r0:15500+N_r[3]])
    x3_m = x3[15499]
    x3[12000-N_r0:15500+N_r[3]] = x3_m - x3[12000-N_r0:15500+N_r[3]]
    x3 *= 100
    x3[12000-N_r0:15500+N_r[3]] += 0.05*np.random.normal(-1,1,(15500+N_r[3])-(12000-N_r0))
    x3 = np.maximum(x3,0)
    return pd.DataFrame(np.array([x1.tolist(), x2.tolist(), x3.tolist(), x1.tolist(), x2.tolist(), x3.tolist()]).T,
             columns=["左机轮刹车给定","左机轮刹车液压压力", "左机轮速度",
                      "右机轮刹车给定","右机轮刹车液压压力", "右机轮速度"])

## 这个是轮速异常 不是响应延时异常
def generator_anom(N_relat = [[500,1000], [20,50],[20,50],[5,20],[5,20]]):
    x1 = np.zeros(25000)
    x1[12000:12500] = 0.5
    x1[12500:13000] = 1
    x1[13000:14000] = 1.5
    x1[14000:15500] = 2

    x2 = np.zeros(25000)
    N_r = [np.random.randint(n_min, n_max) for n_min,n_max in N_relat[1:]]
    x2[12000+N_r[0]:12500+N_r[0]] = 1.5*(1-np.exp(-np.arange((12500+N_r[0])-(12000+N_r[0]))/100))
    #x2[12350+N_r[0]:12500+N_r[0]] -= 3*(np.arange(150)/1600)**2
    x2[12500+N_r[0]:13000+N_r[1]] = 1.75*(1-np.exp(-np.arange((13000+N_r[1])-(12500+N_r[0]))/100)) + 1.25
    #x2[12850+N_r[1]:13000+N_r[1]] -= 3*(np.arange(150)/1600)**2
    x2[13000+N_r[1]:14000+N_r[2]] = 2*(1-np.exp(-np.arange((14000+N_r[2])-(13000+N_r[1]))/100)) + 2.5
    #x2[13750+N_r[2]:14000+N_r[2]] -= 3*(np.arange(250)/2400)**2
    x2[14000+N_r[2]:15500+N_r[3]] = 2.25*(1-np.exp(-np.arange((15500+N_r[3])-(14000+N_r[2]))/100)) + 3.75
    #x2[15000+N_r[3]:15500+N_r[3]] -= 3*(np.arange(500)/3200)**2
    x2[12050+N_r[0]:15500+N_r[3]] += 0.2*np.random.uniform(-1,1,(15500+N_r[3])-(12050+N_r[0]))
    #x2[12000+N_r[0]:15500+N_r[3]] *= 0.99 + 0.01*np.sin(np.arange((15500+N_r[3])-(12000+N_r[0]))/750*2*np.pi)
    x2[12050+N_r[0]:15500+N_r[3]] = np.maximum(0, x2[12050+N_r[0]:15500+N_r[3]])

    x3 = np.zeros(25000)
    dx = 0.00001 + x2/30000
    N_r0 = np.random.randint(N_relat[0][0], N_relat[0][1])
    x3[12000-N_r0:15500+N_r[3]] = np.cumsum(dx[12000-N_r0:15500+N_r[3]])
    x3_m = x3[15499]
    x3[12000-N_r0:15500+N_r[3]] = x3_m - x3[12000-N_r0:15500+N_r[3]]
    x3 *= 100
    x3[12000-N_r0:15500+N_r[3]] += 0.05*np.random.normal(-1,1,(15500+N_r[3])-(12000-N_r0))
    x3 = np.maximum(x3,0)
                   
    x3_ = np.zeros(25000)
    dx_ = 0.00001 + x2/30000
    N_r0 = np.random.randint(N_relat[0][0], N_relat[0][1])
    x3_[12000-N_r0:15500+N_r[3]] = np.cumsum(dx_[12000-N_r0:15500+N_r[3]])
    x3_m_ = x3_[15499]
    x3_[12000-N_r0:15500+N_r[3]] = x3_m_ - x3_[12000-N_r0:15500+N_r[3]]
    x3_ *= 100
    x3_[12000-N_r0:15500+N_r[3]] += 0.05*np.random.normal(-1,1,(15500+N_r[3])-(12000-N_r0))
    x3_ = np.maximum(x3_,0)
        
    d = pd.DataFrame(np.array([x1.tolist(), x2.tolist(), x3_.tolist(), x1.tolist(), x2.tolist(), x3.tolist()]).T,
                 columns=["左机轮刹车给定","左机轮刹车液压压力", "左机轮速度",
                          "右机轮刹车给定","右机轮刹车液压压力", "右机轮速度"])

    labels = np.zeros(len(x1))
    ind = np.where(x2[:15500+N_r[3]]<4.6)[0][-1]
    labels[ind:15500+N_r[3]] = 1
    d["label"] = labels

    return d

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    N_relat = [[500,1000], ## 着陆提前范围
               [20,50], ## 阶梯1响应迟滞范围
               [20,50], ## 阶梯2响应迟滞范围
               [5,20], ## 阶梯3响应迟滞范围
               [5,20] ## 阶梯4响应迟滞范围
               ]

    data = generator_norm()#N_relat = N_relat)
    data.iloc[11500:15500].to_csv("data.csv", encoding="gbk")

    fig = plt.figure()
    ax = fig.add_subplot(3,1,1)
    ax.plot(data.iloc[11500:15500, 0])
    ax = fig.add_subplot(3,1,2)
    ax.plot(data.iloc[11500:15500, 1])
    ax = fig.add_subplot(3,1,3)
    ax.plot(data.iloc[11500:15500, 2])

    data_anom = generator_anom()#N_relat = N_relat)
    data_anom.iloc[11500:15500].to_csv("data_test.csv", encoding="gbk")

    fig = plt.figure()
    ax = fig.add_subplot(3,1,1)
    ax.plot(data_anom.iloc[11500:15500, 0])
    ax = fig.add_subplot(3,1,2)
    ax.plot(data_anom.iloc[11500:15500, 1])
    ax = fig.add_subplot(3,1,3)
    ax.plot(data_anom.iloc[11500:15500, 2])

    plt.show()
