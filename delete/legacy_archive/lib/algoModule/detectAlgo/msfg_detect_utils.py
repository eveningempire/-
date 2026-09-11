### 前端基本配置
SYS = "subsystem-node"
INPUT_NODE = "input-node"
OUTPUT_NODE = "output-node"
RES = "fault-node" ## 故障节点
SW = "switch-node" ## 开关节点
CKPT = "test-node" ## 测点
EDGE = "custom-edge"
TESTTYPE = [CKPT]
FAULTTYPE = [INPUT_NODE, OUTPUT_NODE, RES, SW]

CHECK_INVALID_COL = ["单元名称、型号或图号（2）", "故障模式(4)"]
COMPONENT_COL = "{单元名称、型号或图号（2）}"
FAULTCAUSE_COL = "{故障原因(5)}"
FAULTMODE_COL ="{单元名称、型号或图号（2）}{故障模式(4)}"
DETECTION_COL = "{单元名称、型号或图号（2）}{故障模式(4)}@{故障检测方法（8）}"
SELF_EFFECT_COL = "{故障自身影响}"
TRANS_EFFECT_COL = "{对上一级产品的影响}"
FINAL_EFFECT_COL = "{最终影响}"

WIDTH = 180
NODEWIDTH = 100
HEIGHT = 24
PADDING = 50

DEBUG_MODE = False

import copy
import json
import uuid
from typing import Iterable

import numpy as np
import scipy
from scipy.sparse import coo_matrix, csr_matrix


### D矩阵推理依赖方法
def _cal_failure(D_mat, p_test, eps=1e-20):
    return np.exp(D_mat.dot(np.log(np.maximum(p_test, 0) + eps)[:,None]))

def _divide_sparse_neg_log_1p(vector_, denom_mat, eps=1e-20):
    return denom_mat._with_data(np.log(1-vector_[denom_mat.indices]/denom_mat.data+eps)).tocsr()

def _cal_fuzzy(D_mat, p_fault, eps=1e-20):
    ## ε-slack
    c_p_fault = 1 - p_fault + eps
    logc_p_fault = np.log(c_p_fault)
    #D_mat_bool = (D_mat > eps).astype("float32")
    DmatT = D_mat.T.tocsr()
    itm = DmatT._with_data(logc_p_fault[DmatT.indices, 0]/DmatT.data).T.tocsr()
    log_p_eff_diff = D_mat.multiply(
        _divide_sparse_neg_log_1p(
            np.exp(D_mat.T.dot(logc_p_fault)).flatten(),
            itm._with_data(np.exp(itm.data)).tocsr(), eps=eps
            )
        )
    log_p_eff = log_p_eff_diff.sum(axis=-1).A
    return p_fault*np.minimum(1, np.exp(log_p_eff))

def _or_failure_fuzzy(p_failure, p_fuzzy, n_round=5):
    p_failure = np.array(p_failure, dtype="float32").flatten()
    p_fuzzy = np.array(p_fuzzy, dtype="float32").flatten()
    return {
        "proba": round(float(np.max(p_failure)), n_round),
        "fuzzy_proba": round(float(np.min(p_failure*p_fuzzy+1-p_failure)*np.max(p_failure)), n_round)
        #"proba": round(1-np.prod([1-itm for itm in p_failure])**(1/len(p_failure)), n_round),
        #"fuzzy_proba": round(1-np.prod([1-itm for itm in p_fuzzy])**(1/len(p_fuzzy)), n_round)
        }

def _fuse_dict(resList):
    res = {"proba": [], "fuzzy_proba": []}
    for resL in resList:
        res["proba"].append(resL["proba"])
        res["fuzzy_proba"].append(resL["fuzzy_proba"])
    return res

### D矩阵推理
def detect_by_D_mat(p_test, f_test, D_mat, sysmap={}, ConnIds=[], eps=1e-10, n_round=5):
    p_fault = np.array([np.maximum(np.where(~np.isnan(f_t_[:,None]), f_t_[:,None], 0),
                                   _cal_failure(D_mat, p_t_, eps=eps**2)) for f_t_, p_t_ in zip(f_test, p_test.T)], dtype="float32")
    
    DmatT = D_mat.T.tocsr()
    if len(ConnIds) == 0:
        p_fuzzy = np.array([np.minimum(1-np.array(f_t_[:,None], dtype="float32"), _cal_fuzzy(D_mat, p_t_, eps=eps**2)) for f_t_, p_t_ in zip(f_test, p_fault)])
    else:
        Dpure = DmatT._with_data(np.array([0 if i in ConnIds else v for i, v in zip(DmatT.indices, DmatT.data)], dtype="float32")).T.tocsr()
        Dpure.eliminate_zeros()
        p_fuzzy = np.array([np.minimum(1-np.array(f_t_[:,None], dtype="float32"), _cal_fuzzy(Dpure, p_t_, eps=eps**2)) for f_t_, p_t_ in zip(f_test, p_fault)])
    print(p_fuzzy.shape, p_fault.shape)
    for sysk, sysv in sysmap.items():
        print(sysv["nodesId"])
    sysres = {}
    for sysk, sysv in sysmap.items():
        z = zip(p_fuzzy, p_fault)
        l = []
        for p_fu_, p_f_ in z:
            l2 = []
            for nId in sysv["nodesId"]:
                if nId not in ConnIds:
                    l2.append([p_f_[nId], p_fu_[nId]])
            z1 = zip(*l2)
            if not len(l2):
                # breakpoint()
                l2 = [[np.array([0], dtype=np.float32), np.array([0], dtype=np.float32)]]
                z1 = zip(*l2)
                l.append(_or_failure_fuzzy(*z1, n_round=n_round))
                pass
            else:
                l.append(_or_failure_fuzzy(*z1, n_round=n_round))
        sysres[sysk] = _fuse_dict(l)
    # sysres = {
    #     sysk: _fuse_dict([
    #         _or_failure_fuzzy(*zip(*[[p_f_[nId], p_fu_[nId]] for nId in sysv["nodesId"] if nId not in ConnIds]), n_round=n_round)
    #         for p_fu_, p_f_ in zip(p_fuzzy, p_fault)])
    #     for sysk, sysv in sysmap.items()}
    p_fault = np.where(~np.isnan(p_fault), p_fault, 0)
    p_fuzzy = np.where(~np.isnan(p_fuzzy), p_fuzzy, 0)
    return np.round(p_fault[...,0], n_round), np.round(p_fuzzy[...,0], n_round), sysres

def _anomCount(result,n_round=5):
    if np.ndim(result) >= 2:
        result = np.max(result, axis=-1)
    return round(np.mean(np.sort(result)[-max(30, min(10, round(len(result)/10))):]),n_round)

## D矩阵推理（含渲染）
def fuse_detect_with_render(p_testT, f_test, D_mat, struct, testLoc, faultLoc, sysmap, ConnIds=[], eps=1e-9, n_round=5):
    # print(f"==>> type(n_round): {type(n_round)}")
    # print(f"==>> type(eps): {type(eps)}")
    # print(f"==>> type(ConnIds): {type(ConnIds)}")
    # print(f"==>> type(f_test): {type(f_test)}")
    # print(f"==>> type(p_testT): {type(p_testT)}")
    # print(f"==>> type(sysmap): {type(sysmap)}")
    # print(f"==>> type(faultLoc): {type(faultLoc)}")
    # print(f"==>> type(testLoc): {type(testLoc)}")
    # print(f"==>> type(struct): {type(struct)}")
    # print(f"==>> type(D_mat): {type(D_mat)}")
    # np.savez(
    #     r"D:\dev\CF_2_plateform\lib\algoModule\detectAlgo\test_1024.npz",
    #     p_testT=p_testT,
    #     f_test=f_test,
    #     # D_mat=D_mat,
    #     struct=struct,
    #     testLoc=testLoc,
    #     faultLoc=faultLoc,
    #     sysmap=sysmap,
    #     ConnIds=ConnIds,
    #     eps=eps,
    #     n_round=n_round,
    # )
    # scipy.sparse.save_npz(r"D:\dev\CF_2_plateform\lib\algoModule\detectAlgo\test_1024_D_mat.npz", D_mat)  # 存放csr形式的文件
    p_test = np.where(~np.isnan(p_testT.T), p_testT.T, 0)
    p_test = np.maximum(p_test, 0)
    f_test = np.maximum(f_test, 0)
    p_fault, p_fuzzy, sysres = detect_by_D_mat(p_test, f_test, D_mat, sysmap, ConnIds=ConnIds, eps=eps/10)

    ## 渲染步骤
    struct = copy.deepcopy(struct)
    for t_ind, p_fault_ in enumerate(p_test):
        act_id, node_id = testLoc[t_ind]
        struct[act_id]["data"]["nodes"][node_id]["properties"]["showType"] = "analyse"
        struct[act_id]["data"]["nodes"][node_id]["properties"]["probaRange"] = [float(v) for v in np.where(~np.isnan(p_fault_), p_fault_, 0)]
        struct[act_id]["data"]["nodes"][node_id]["properties"]["state"] = _anomCount(struct[act_id]["data"]["nodes"][node_id]["properties"]["probaRange"], n_round=n_round)
        struct[act_id]["data"]["nodes"][node_id]["properties"]["proba"] = _anomCount(struct[act_id]["data"]["nodes"][node_id]["properties"]["probaRange"], n_round=n_round)
        struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_probaRange"] = [0 for _ in range(len(p_fault_))]
        struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = _anomCount(struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_probaRange"], n_round=n_round)
        struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_proba"] = _anomCount(struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_probaRange"], n_round=n_round)
    f_ind = 0
    for p_fault_, p_fuzzy_ in zip(p_fault.T, p_fuzzy.T):
        act_id, node_id = faultLoc[f_ind]
        struct[act_id]["data"]["nodes"][node_id]["properties"]["showType"] = "analyse"
        if struct[act_id]["data"]["nodes"][node_id]["properties"].get("detectable", True):
            struct[act_id]["data"]["nodes"][node_id]["properties"]["stateRange"] = [float(v) for v in np.where(~np.isnan(p_fault_), p_fault_, 0)]
            struct[act_id]["data"]["nodes"][node_id]["properties"]["state"] = _anomCount(struct[act_id]["data"]["nodes"][node_id]["properties"]["stateRange"],n_round=n_round)
            struct[act_id]["data"]["nodes"][node_id]["properties"]["proba"] = _anomCount(struct[act_id]["data"]["nodes"][node_id]["properties"]["stateRange"],n_round=n_round)
            struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_stateRange"] = [float(v) for v in np.where(~np.isnan(p_fuzzy_), p_fuzzy_, 0)]
            struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = _anomCount(struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_stateRange"],n_round=n_round)
            struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_proba"] = _anomCount(struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_stateRange"],n_round=n_round)
        else: ## 补充不可测试测点的逻辑
            struct[act_id]["data"]["nodes"][node_id]["properties"]["stateRange"] = [0 for _ in range(len(p_fault_))]
            struct[act_id]["data"]["nodes"][node_id]["properties"]["state"] = 0
            struct[act_id]["data"]["nodes"][node_id]["properties"]["proba"] = 0
            struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_stateRange"] = [1 for _ in range(len(p_fault_))]
            struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = 1
            struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_proba"] = 1
        f_ind += 1
    for key, sysr_ in sysres.items():
        parent_sys_id = sysmap[key]["ParentSubsystemId"]
        node_id = sysmap[key]["NodeId"]
        struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["showType"] = "analyse"
        struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["stateRange"] = [float(v) for v in np.where(~np.isnan(sysr_["proba"]), sysr_["proba"], 0)]
        struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["state"] = _anomCount(struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["stateRange"],n_round=n_round)
        struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["proba"] = _anomCount(struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["stateRange"],n_round=n_round)
        struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["fuzzy_stateRange"] = [float(v) for v in np.where(~np.isnan(sysr_["fuzzy_proba"]), sysr_["fuzzy_proba"], 0)]
        struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = _anomCount(struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["fuzzy_stateRange"],n_round=n_round)
        struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["fuzzy_proba"] = _anomCount(struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["fuzzy_stateRange"],n_round=n_round)
        struct[int(key)]["data"]["properties"] = {**struct[int(key)]["data"].get("properties", {}), **sysr_}
    return struct, {struct[int(k)]["name"]: v for k,v in sysres.items()}

## 解算依赖从Json导入
def from_json(configJson):
    config = json.loads(configJson)
    struct = config["struct"]
    testLoc = config["testLoc"]
    faultLoc = config["faultLoc"]
    sysmap = config["sysmap"]
    testName = config["testName"]
    faultName = config["faultName"]
    D_indptr, D_indices, D_values = config["D_mat"]
    D_mat = csr_matrix((D_values, D_indices, D_indptr),shape=(len(faultName), len(testName)), dtype="float32")
    collision_node = config["collision_node"]
    ConnIds = config["ConnIds"]
    return D_mat, struct, testLoc, faultLoc, sysmap, testName, faultName, collision_node, ConnIds


if __name__ == '__main__':
    res = np.load(r'D:\dev\CF_2_plateform\lib\algoModule\detectAlgo\test_1024.npz', allow_pickle=True)
    p_testT=res['p_testT']
    print(f"==>> type(p_testT): {type(p_testT)}")
    f_test=res['f_test']
    print(f"==>> type(f_test): {type(f_test)}")
    # D_mat=res['D_mat']
    D_mat = scipy.sparse.load_npz(r'D:\dev\CF_2_plateform\lib\algoModule\detectAlgo\test_1024_D_mat.npz')
    print(f"==>> type(D_mat): {type(D_mat)}")
    struct=res['struct'].tolist()
    print(f"==>> type(struct): {type(struct)}")
    testLoc=res['testLoc'].tolist()
    print(f"==>> type(testLoc): {type(testLoc)}")
    faultLoc=res['faultLoc'].tolist()
    print(f"==>> type(faultLoc): {type(faultLoc)}")
    sysmap=res['sysmap'].item()
    print(f"==>> type(sysmap): {type(sysmap)}")
    ConnIds=res['ConnIds'].tolist()
    print(f"==>> type(ConnIds): {type(ConnIds)}")
    eps=float(res['eps'])
    print(f"==>> type(eps): {type(eps)}")
    n_round=int(res['n_round'])
    print(f"==>> type(n_round): {type(n_round)}")
    fuse_detect_with_render(p_testT, f_test, D_mat, struct, testLoc, faultLoc, sysmap, ConnIds, eps, n_round)
