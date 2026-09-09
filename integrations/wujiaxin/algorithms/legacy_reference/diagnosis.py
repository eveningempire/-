import json
import numpy as np
import copy
import threading
import time
file_path_para = 'D:\\1YAssistantDecision\\jie2\\health2\\backend\\backend\\algorithm\\para_real_time.json'
file_path_diag = 'D:\\1YAssistantDecision\\jie2\\health2\\backend\\backend\\algorithm\\digDatabase.json'
file_path_result = 'D:\\1YAssistantDecision\\jie2\\health2\\backend\\backend\\algorithm\\result.json'
file_path_testresult = 'D:\\1YAssistantDecision\\jie2\\health2\\backend\\backend\\algorithm\\testresult.json'
"""全局故障表"""
# 每一种故障模式对应的单机
Fault_SingeMachineList = [
	"PBSBA002", "PBSBA002", "PBSBA002", "PBSBB004",
	"PBSBB004", "PBSBB004", "PBSBC002", "PBSBC002",
	"PBSBD001", "PBSCC002", "PBSCB002", "PBSEC001",
	"PBSDB001", "PBSDA001", "PBSAA001", "PBSAA002",
	"PBSAA003", "PBSAA003", "PBSAA004", "PBSAA004",
	"PBSAD001", "PBSAD001", "PBSAC001", "PBSAC001",
	"PBSAC002", "PBSAC002", "PBSAB001", "PBSAB001",
	"PBSAB002", "PBSAB003", "PBSAB004", "PBSAB004",
]

# 飞行器结构树
aircraft_struct_dict = {
	"PBS00000":{
        'PBSA0000':{
            'PBSAA000':{
                "PBSAA001":{},
				"PBSAA002":{},
				"PBSAA003":{},
				"PBSAA004":{},
            },
            'PBSAB000':{
                "PBSAB001":{},
				"PBSAB002":{},
				"PBSAB003":{},
				"PBSAB004":{}},
            'PBSAC000':{
                "PBSAC001":{},
				"PBSAC002":{}},
            'PBSAD000':{
                "PBSAD001":{}
            }
        },
        'PBSB0000':{
            'PBSBA000':{
                "PBSBA001":{},
                "PBSBA002":{},
                "PBSBA003":{},
                "PBSBA004":{},
            },
            'PBSBB000':{
                "PBSBB001":{},
                "PBSBB002":{},
                "PBSBB003":{},
            },
            'PBSBC000':{
                "PBSBC001":{},
				"PBSBC002":{}
            },
            'PBSBD000':{
                "PBSBD001":{}
            }
        },
        'PBSC0000':{
            'PBSCA000':{
                "PBSCA001":{},
                "PBSCA002":{},
                "PBSCA003":{}
            },
            'PBSCB000':{
                "PBSCB001":{},
                "PBSCB002":{},
                "PBSCB003":{}
            },
            'PBSCC000':{
                "PBSCC001":{},
                "PBSCC002":{},
                "PBSCC003":{},
                "PBSCC004":{}
            }
        },
        'PBSD0000':{
            'PBSDA000':{
                "PBSDA001":{},
                "PBSDA002":{},
                "PBSDA003":{},
                "PBSDA004":{}
            },
            'PBSDB000':{
                "PBSDB001":{},
                "PBSDB002":{},
                "PBSDB003":{},
                "PBSDB004":{},
                "PBSDB005":{}
            }
        },
        'PBSE0000':{
            'PBSEA000':{
                "PBSEA001":{},
                "PBSEA002":{}
            },
            'PBSEB000':{
                "PBSEB001":{},
                "PBSEB002":{},
                "PBSEB003":{}
            }
        }
    }
}


class Mythread(threading.Thread):
    def __init__(self, func, args, name=""):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception:
            return None

def outlier_detection():
    with open(file_path_para, 'r') as json_file:
        loaded_data = json.load(json_file)
    # print(loaded_data)
    testresult = np.zeros(len(loaded_data ))
    # print(testresult)
    for index, param in enumerate(loaded_data):
        para_low = float(param["para_low"])
        para_up = float(param["para_up"])
        para_value = float(param["para_value"])
        if (para_value <= para_up) and (para_value >= para_low):
            testresult[index] = 0
        else:
            testresult[index] = 1
    if isinstance(testresult, np.ndarray):
        testresult = testresult.astype(int)
        testresult = testresult.tolist()
    with open(file_path_testresult, 'w') as f:
        json.dump(testresult, f, indent=4)
    with open(file_path_diag, 'r') as json_file:
        kb_dict = json.load(json_file)
    treeRoot = kb_dict['digtree']
    faultlist = kb_dict['faultlist']
    # print(treeRoot,faultlist)
    result = diagnostic(treeRoot, testresult, faultlist)
    # print(result)
    # result_item = {'testresult': testresult}
    # result.append(result_item)
    result['testresult'] = testresult
    with open(file_path_result, 'w') as f:
        json.dump(result, f, indent=4)

def diagnostic(root, testresultlist, faultlist):
    """通过故障树和D矩阵进行诊断"""
    g = []
    b = []
    u = copy.deepcopy(faultlist)  # 认为所有的故障都是未知
    s = []
    faultprocess = {}  # 故障详细情况

    # 判断唯一检测得到故障状态
    for td in root[0]:
        if td[1] in u:
            if testresultlist[td[0]] == 1:
                b.append(td[1])
                faultprocess[str(td[1])] = {'state': 'b', 'testsource': [td[0]],'probability':1}  # 将故障及诊断过程加入进来
            else:
                g.append(td[1])
                # faultprocess[str(td[1])] = {'state': 'g','probability':0}
            u.remove(td[1])

    digthreading = []
    threadingnum = len(root[1])  # 获取故障树中有多少个分支
    digresult = []

    for i in range(0, threadingnum):
        testresultcut = []
        for test in root[1][i][0]:
            testresultcut.append(testresultlist[test])  # 获取测试结果的子集
        thd = Mythread(treeDiagnostic, (root[1][i][2], testresultcut), treeDiagnostic.__name__)
        digthreading.append(thd)
    # for thd in digthreading:
    #     thd.start()
    for i in range(0, len(digthreading)):
        digresult.append(digthreading[i].get_result())

    # 结果收集
    for i in range(0, len(digresult)):
        g = list(set(g).union(set(digresult[i]['g'])))
        b = list(set(b).union(set(digresult[i]['b'])))
        s = list(set(s).union(set(digresult[i]['s'])))
        faultprocess = dict(faultprocess, **digresult[i]['faultprocess'])

    u = list(set(u).difference(set(g)))
    u = list(set(u).difference(set(b)))
    u = list(set(u).difference(set(s)))

    # 对faultprocess进行排序
    # for i in range(0,len(faultlist)):

    # faultprocess = sorted(faultprocess.items(), key=lambda d:d[0], reverse=False)
    sortedfaultprocess = {}
    for i in range(0,len(faultlist)):
        try:
            sortedfaultprocess[i] = faultprocess[str(i)]
        except:
            pass


    """根据故障诊断结果进行简单的健康评估计算"""
    # 对单机进行评分
    # print(sortedfaultprocess)


    # 需要修改
    aircraftHI = {}

    for aircraft_key in aircraft_struct_dict.keys():
        # print(aircraft_key)
        partsystem_struct_dict = aircraft_struct_dict[aircraft_key]
        aircraft_HI = 0
        aircraft_Pro = 0

        for partsystem_key in partsystem_struct_dict.keys():
            # print(partsystem_key)
            subsystem_struct_dict = partsystem_struct_dict[partsystem_key]
            partsystem_HI = 0
            partsystem_Pro = 0
            partsystemHI = {}

            for subsystem_key in subsystem_struct_dict.keys():
                # print(subsystem_key)

                subsystem_HI = 0
                subsystem_Pro = 0

                subsystemHI = {}
                singleMachine_struct_dict = subsystem_struct_dict[subsystem_key]

                for singleMechina_key in singleMachine_struct_dict.keys():
                    # print(singleMechina_key)
                    singleHI = {}
                    singHI = 0
                    singPro = 0
                    if singleMechina_key in Fault_SingeMachineList:
                        faultindex = [i for i, x in enumerate(Fault_SingeMachineList) if
                                      x == singleMechina_key]  # 找到单机所属的故障位置
                        # singHI = 0
                        # singPro = 0
                        if faultindex:
                            for i in faultindex:
                                if sortedfaultprocess.__contains__(i):  # 判断有故障
                                    if sortedfaultprocess[i]['state'] == 'b':
                                        singHI += 10
                                    elif sortedfaultprocess[i]['state'] == 's':
                                        singHI += (10 * sortedfaultprocess[i]['probability'])
                                    singPro = max(singPro, sortedfaultprocess[i]['probability'])
                    singleHI['HI'] = copy.deepcopy(singHI)
                    subsystem_HI += singHI
                    subsystem_Pro = max(subsystem_Pro, singPro)  # 故障率取最大
                    # subsystemHI[singleMechina_key] = copy.deepcopy(singleHI)

                subsystemHI['HI'] = copy.deepcopy(subsystem_HI)
                subsystemHI['Pro'] = copy.deepcopy(subsystem_Pro)
                if subsystemHI['HI'] >= 0 and subsystemHI['HI'] <= 5:
                    subsystemHI['level'] = '正常'
                elif subsystemHI['HI'] > 5 and subsystemHI['HI'] <= 10:
                    subsystemHI['level'] = '良好'
                elif subsystemHI['HI'] > 10 and subsystemHI['Pro'] != 1:
                    subsystemHI['level'] = '疑似故障'
                elif subsystemHI['HI'] > 10 and subsystemHI['Pro'] == 1:
                    subsystemHI['level'] = '故障'
                partsystem_HI += copy.deepcopy(subsystemHI['HI'])
                partsystem_Pro = max(partsystem_Pro, subsystemHI['Pro'])

                partsystemHI[subsystem_key] = copy.deepcopy(subsystemHI)

            partsystemHI['HI'] = copy.deepcopy(partsystem_HI)
            partsystemHI['Pro'] = copy.deepcopy(partsystem_Pro)
            if partsystemHI['HI'] >= 0 and partsystemHI['HI'] <= 5:
                partsystemHI['level'] = '正常'
            elif partsystemHI['HI'] > 5 and partsystemHI['HI'] <= 10:
                partsystemHI['level'] = '良好'
            elif partsystemHI['HI'] > 10 and partsystemHI['Pro'] != 1:
                partsystemHI['level'] = '疑似故障'
            elif partsystemHI['HI'] > 10 and partsystemHI['Pro'] == 1:
                partsystemHI['level'] = '故障'
            aircraft_HI += copy.deepcopy(partsystemHI['HI'])
            aircraft_Pro = max(aircraft_Pro, partsystemHI['Pro'])
            aircraftHI[partsystem_key] = copy.deepcopy(partsystemHI)

        aircraftHI['HI'] = copy.deepcopy(aircraft_HI)
        aircraftHI['Pro'] = copy.deepcopy(aircraft_Pro)
        if aircraftHI['HI'] >= 0 and aircraftHI['HI'] <= 5:
            aircraftHI['level'] = '正常'
        elif aircraftHI['HI'] > 5 and aircraftHI['HI'] <= 40:
            aircraftHI['level'] = '良好'
        elif aircraftHI['HI'] > 50 and aircraftHI['Pro'] != 1:
            aircraftHI['level'] = '疑似故障'
        elif aircraftHI['HI'] > 50 and aircraftHI['Pro'] == 1:
            aircraftHI['level'] = '故障'


    return {'time':time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())),'g': g, 'b': b, 'u': u, 's': s, 'faultprocess': sortedfaultprocess,
            aircraft_key:aircraftHI}

def treeDiagnostic(treenode, testresult):
    g = []
    b = []
    s = []
    faultprocess = {}
    if treenode[0] is not None:  # 如果需要进一步判断
        checktest = treenode[0]
        testlist = treenode[1]
        checkfaultlist = treenode[2]
        if testresult[testlist.index(checktest)] == 0:  # 测试通过，一定不会发生故障
            g = copy.deepcopy(checkfaultlist)
            for fault in checkfaultlist:
                pass
                # faultprocess[str(fault)] = {'state': 'g', 'probability':0}
            result = treeDiagnostic(treenode[3], testresult)
        elif testresult[testlist.index(checktest)] == 1:  # 测试未通过，需要进一步判断
            result = treeDiagnostic(treenode[4], testresult)

        g = list(set(g).union(set(result['g'])))
        b = list(set(b).union(set(result['b'])))
        s = list(set(s).union(set(result['s'])))
        faultprocess = dict(faultprocess, **result['faultprocess'])

    else:  # 已经到了叶子，仅剩下D矩阵的时候
        result = dmatrixDiag(treenode[3], testresult, treenode[2], treenode[1])
        g = list(set(g).union(set(result['g'])))
        b = list(set(b).union(set(result['b'])))
        s = list(set(s).union(set(result['s'])))
        faultprocess = dict(faultprocess, **result['faultprocess'])

    return {'g': g, 'b': b, 's': s, 'faultprocess': faultprocess}


"""我写的算法，保留TEAMS-RT的思想，采用矩阵的方式进行计算"""
def dmatrixDiag(dm, tv, fl, tl):
    """通过d矩阵进行判断"""
    num_f = len(dm)
    num_t = len(tv)
    faultprocess = {}

    # 4000ns = 4ms
    tv_re = copy.deepcopy(tv)
    for i in range(num_t):
        if tv_re[i] == 1:
            tv_re[i] = 0
        else:
            tv_re[i] = 1

    u, g, b, s = [], [], [], []

    # all faults are put into suspect set
    # this step may consume some time
    # 4000ns = 4ms
    for i in range(num_f):
        s.append(i)

    # 8ms
    positive_mul = np.dot(dm, tv)

    # 8ms
    negtive_mul = np.dot(dm, tv_re)

    # 4000ns = 4ms
    for i in range(num_f):
        # find good set
        if negtive_mul[i] >= 1:
            s.remove(i)
            g.append(i)
            # faultprocess[str(fl[i])] = {'state': 'g','probability':0}
        else:
            # find unknown set
            if positive_mul[i] == 0:
                s.remove(i)
                u.append(i)
                faultprocess[str(fl[i])] = {'state': 'u'}


    f_list = np.zeros([1, num_t])

    for i in s:
        f_list += dm[i]

    # 4000ns = 4ms
    for j in range(num_t):
        if f_list[0][j] == 1:  # only one fault have effect on this test point
            for i in s:
                if dm[i][j] == 1:
                    s.remove(i)
                    b.append(i)
                    faultprocess[str(fl[i])] = {'state': 'b','probability':1}
                    faultprocess[str(fl[i])]['testsource'] = [j]

    s_real = []
    g_real = []
    b_real = []
    for i in s:
        testsource = []
        s_real.append(fl[i])
        n = 0
        for j in range(0,len(tv)):
            if dm[i][j] == 1 and tv[j] == 1:
                n = n + 1
                testsource.append(tl[j])
        dm_np = np.array(dm)
        faultprocess[str(fl[i])] = {'state': 's', 'probability':(n/sum(abs(dm_np[i,:]))), 'testsource': testsource}  # 故障率计算
    for i in g:
        g_real.append(fl[i])
    for i in b:
        b_real.append(fl[i])

    return {'u': u, 'g': g_real, 'b': b_real, 's': s_real, 'faultprocess': faultprocess,}

if __name__ == "__main__":
    outlier_detection()