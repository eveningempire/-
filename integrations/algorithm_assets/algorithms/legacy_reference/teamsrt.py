"""分解型TEAMS-RT"""
"""算法原型"""
"""重要标注：测试通过为0，测试没有通过为1"""

import numpy as np
import copy
import threading
import json

import time


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

"""将大型D矩阵进行分解得到故障树，叶子为D矩阵"""
def createDiagTree(dmatrix):
    (faultNum, testNum) = dmatrix.shape
    faultlist = []
    testlist = []
    for i in range(0, testNum):
        testlist.append(i)
    for i in range(0, faultNum):
        faultlist.append(i)

    # 诊断树的根节点
    root = []

    """找到一种测试只对应一种故障的情况"""
    td = []  # 测试只对应一种故障的时候 (测试编号，故障编号，相关/互斥)
    for i in range(0, testNum):  # 一种测试值对应
        if sum(abs(dmatrix[:, i])) == 1:
            faultindex = np.where(abs(dmatrix[:, i]) == 1)
            td.append((i, faultindex[0].tolist()[0], 1))

    faultcutlist = []
    testcutlist = []
    for i in range(len(td)):
        testlist.remove(td[i][0])   # 去掉一一对应测试列表
        testcutlist.append(td[i][0])
        if td[i][1] in faultlist:
            faultlist.remove(td[i][1])  # 去掉一一对应故障列表
            faultcutlist.append(td[i][1])

    dmatrix=np.delete(dmatrix, testcutlist, axis=1)  # 删除列，去掉单一测试的
    dmatrix=np.delete(dmatrix, faultcutlist, axis=0)  # 删除行，去掉单一故障
    root.append(td)


    # 检查是否存在全零列，也就是无效测试
    unrelatedtestlist = []  # 全0列，无影响测试集
    for i in testlist:
        if np.sum(abs(dmatrix[:, testlist.index(i)])) == 0:  #判断全0列
            unrelatedtestlist.append(i)

    # 找到对应的index
    unrelatedtestlistindex = []
    for i in unrelatedtestlist:
        unrelatedtestlistindex.append(testlist.index(i))

    # 删除无关的节点
    for i in unrelatedtestlist:
        testlist.remove(i)

    dmatrix = np.delete(dmatrix, unrelatedtestlistindex, axis=1)

    """将测试和故障分块，用于并行计算"""
    """这种方法对于大型矩阵来说并不是很好"""
    branch = []  # 不同块的测试
    testlisttemp = copy.deepcopy(testlist)  # 待查看的测试
    testlisttemp.remove(testlist[0])
    checkqueue = [testlist[0]]  # 存放属于不同块的测试索引
    while(checkqueue):
        checkqueue = list(set(checkqueue))  # 保证没有重复
        checkqueue.sort(reverse=True)  # 保证得到最小的故障索引
        checktest = checkqueue.pop()  # 考察的序列
        branchtemp = [checktest]
        temp = []

        isChecked = False
        if branch:
            for i in range(0, len(branch)):
                if isChecked:
                    break
                for j in branch[i]:
                    if np.dot(np.transpose(abs(dmatrix[:, testlist.index(j)])),
                          abs(dmatrix[:, testlist.index(checktest)])) != 0:
                        branch[i].append(checktest)
                        isChecked = True
                        break
        if isChecked:
            continue

        for i in testlisttemp:
            if i == checktest:
                continue
            # 测试向量相互垂直，表示相互独立
            testindex = testlist.index(checktest)
            if np.dot(np.transpose(abs(dmatrix[:, testlist.index(i)])),
                      abs(dmatrix[:, testlist.index(checktest)])) == 0:
                checkqueue.append(i)
            # 测试向量相互不垂直，表示相互有交叉
            else:
                branchtemp.append(i)
                temp.append(i)
                if i in checkqueue:
                    checkqueue.remove(i)  # 如果待考察的测试节点中也存在i测试，则一起去掉
        for x in temp:
            testlisttemp.remove(x)
        branch.append(copy.deepcopy(branchtemp))  # 保证测试序列小的在前面，方便之后的计算

    # 将原来的D矩阵分解
    TreeNode = []
    for branchlist in branch:
        testlisttemp = copy.deepcopy(branchlist)
        testlisttemp.sort()
        faultlisttemp = []
        for test in testlisttemp:
            faultlistlocation = np.where(dmatrix[:, testlist.index(test)] == 1)[0].tolist()  # 故障所在的位置
            for x in faultlistlocation:
                faultlisttemp.append(faultlist[x])

        faultlisttemp = list(set(faultlisttemp))
        newdmatrix = np.zeros([len(faultlisttemp),len(testlisttemp)])

        for test in testlisttemp:
            for fault in faultlisttemp:
                newdmatrix[faultlisttemp.index(fault)][testlisttemp.index(test)] = \
                dmatrix[faultlist.index(fault)][testlist.index(test)]

        TreeNode.append((testlisttemp, faultlisttemp, newdmatrix))

    root.append([])
    for treenode in TreeNode:
        root[1].append([treenode[0], treenode[1], getTree(treenode[2], treenode[0], treenode[1])])

    return root


def getTree(dmatrix, testlist, faultlist):
    if not np.where(dmatrix == -1)[0].tolist():  # 如果不存在互斥
        return [None, testlist, faultlist, dmatrix.tolist()]

    """如果存在互斥，则继续分割"""
    treenode = []
    location = np.where(dmatrix == -1)
    faultlocationlist = location[0].tolist()
    testlocationlist = location[1].tolist()  # 互斥测试列表

    testindex = testlist[testlocationlist[0]]  # 取第一个互斥测试
    faultindex = []
    dtemp0 = copy.deepcopy(dmatrix)  # 测试通过的时候的D矩阵
    dtemp1 = copy.deepcopy(dmatrix)  # 测试未通过时候的D矩阵
    for i in range(len(faultlocationlist)):  # 提取出第一个互斥测试对应的故障
        if testlist[testlocationlist[i]] == testindex:
            faultindex.append(faultlist[faultlocationlist[i]])

    # 如果通过测试，则将故障行和测试列(?)去掉
    for i in range(len(faultindex)):
        dtemp0 = np.delete(dtemp0, faultlist.index(faultindex[i]), axis=0)  # 去掉故障行
    # dtemp0 = np.delete(dtemp0, testlist.index(testindex), axis=1)  # 去掉测试列

    # 如果未通过测试，则继续保留
    for i in range(len(faultindex)):
        dd = faultlist.index(faultindex[i])

        dtemp1[faultlist.index(faultindex[i])][testlist.index(testindex)] = 1  # 表示发生了故障

    treenode.append(testindex)
    treenode.append(testlist)
    treenode.append(faultindex)
    treenode.append(getTree(dtemp0, testlist, list(set(faultlist).difference(set(faultindex)))))
    treenode.append(getTree(dtemp1, testlist, faultlist))

    return treenode


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
    print(sortedfaultprocess)


    # 需要修改
    aircraftHI = {}

    for aircraft_key in aircraft_struct_dict.keys():
        print(aircraft_key)
        partsystem_struct_dict = aircraft_struct_dict[aircraft_key]
        aircraft_HI = 0
        aircraft_Pro = 0

        for partsystem_key in partsystem_struct_dict.keys():
            print(partsystem_key)
            subsystem_struct_dict = partsystem_struct_dict[partsystem_key]
            partsystem_HI = 0
            partsystem_Pro = 0
            partsystemHI = {}

            for subsystem_key in subsystem_struct_dict.keys():
                print(subsystem_key)

                subsystem_HI = 0
                subsystem_Pro = 0

                subsystemHI = {}
                singleMachine_struct_dict = subsystem_struct_dict[subsystem_key]

                for singleMechina_key in singleMachine_struct_dict.keys():
                    print(singleMechina_key)
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


def execute(kb_dict, ip_dict, action):
    """诊断执行操作"""
    if action == "execute_diagnose":
        # 准备消息
        treeRoot = kb_dict['digtree']
        # testlist = kb_dict['testlist']
        faultlist = kb_dict['faultlist']

        if isinstance(ip_dict, dict):
            inputlist = ip_dict['datablock']
        elif isinstance(ip_dict,list):
            inputlist = copy.deepcopy(ip_dict)

        testresult = np.zeros(len(inputlist))

        # 量化测试测试
        # 测试结果完全按照顺序来
        for testnum in range(0,len(inputlist)):
            value = float(inputlist[testnum]['value'])
            limit_up = float(inputlist[testnum]['limit_up'])
            limit_low = float(inputlist[testnum]['limit_low'])
            if (value <= limit_up) and (value >= limit_low):
                testresult[testnum] = 0
            else:
                testresult[testnum] = 1

        print(testresult)
        # 诊断
        result = diagnostic(treeRoot, testresult, faultlist)


        # json_filename = "temp.json"
        # with open(json_filename, 'w') as f:
        #     f.write(json.dumps(result))

        return json.dumps(result)

def change(dmatrix):
    return {'digtree': createDiagTree(dmatrix)}


if __name__ == "__main__":

    # 这个矩阵是行为测试，列为故障，实际使用的时候需要转置一下
    # Dmatrix = np.array([
    #     [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 1, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0],
    #     [0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    #     [0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, 0],
    #     [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    # ])
    Dmatrix = np.array([
        [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
        [1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1]
    ])
    # d = np.transpose(Dmatrix)
    d = copy.deepcopy(Dmatrix)
    dignosticTree = createDiagTree(d)
    testresult = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 测试结果，返回诊断结果
    # faultlist = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    faultlist = [0, 1, 2, 3, 4, 5, 6, 7, 8]


    digTree_dict = {'digtree': dignosticTree}
    filename = 'digDatabase.json'

    with open(filename, 'w') as f:
        f.write(json.dumps(digTree_dict))


    start_CPU = time.time_ns()
    result = diagnostic(dignosticTree, testresult, faultlist)
    end_CPU = time.time_ns()

    print(end_CPU-start_CPU)
