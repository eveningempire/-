from openpyxl import Workbook
from openpyxl.styles import Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
import numpy as np

### 前端基本配置
AND_NODE = "and-node" ## 故障节点
RES = "fault-node" ## 故障节点
SW = "switch-node" ## 开关节点
CKPT = "test-node" ## 测点
EDGE = "custom-edge"
TESTTYPE = [CKPT, SW]

def to_merge(df, cols):
    """
    key 列去重并合并单元格并居中
    Args:
        df: DataFrame输入表
        key: （多个）列名
        output_path: 保存路径

    Returns: Workbook 工作簿

    """
    wb = Workbook()  # 创建工作簿
    ws = wb.active  # 获取第一个工作表

    set_col = set(cols)
    columns = [*cols, *(i for i in df.columns if i not in set_col)]
    _df = df[columns]

    # 将每行数据写入工作表中
    for row in dataframe_to_rows(_df, index=False, header=True):
        ws.append(row)

    align = Alignment(horizontal="center", vertical="center")  # 居中样式

    idx = {-1, _df.shape[0] - 1}
    for i, _ in enumerate(cols):
        c = _df[_].values
        idx.update(np.where(c[1:] != c[:-1])[0])
        sorted_idx = sorted(idx)
        for start, end in zip(sorted_idx[:-1], sorted_idx[1:]):
            # OpenPyXL 序号从1开始，所以行序号需要+2
            ws.merge_cells(start_row=start + 3, end_row=end + 2, start_column=i + 1, end_column=i + 1)
            # 仅需对合并单元格后的一个 cell 居中即可
            ws.cell(start + 3, i + 1).alignment = align

    return wb

def _get_valid_map(n_id_nonvalid, edges, nodeValidMap):
    if n_id_nonvalid in nodeValidMap:
        return [n_id_nonvalid]
    elif len(edges[n_id_nonvalid]) == 0:
        return []
    else:
        res = []
        for n_id in edges[n_id_nonvalid]:
            res.extend(_get_valid_map(n_id, edges, nodeValidMap))
        return res

def _wash_non_fault_edge(edges, nodeValidMap):
    return [sorted({n_id for n_id_nonvalid in edge for n_id in _get_valid_map(n_id_nonvalid, edges, nodeValidMap)}) for edge in edges]

def _get_testIds(rootIds, edges, nodes):
    newRootIds = [eid for rootId in rootIds for eid in edges[rootId]]
    testIds = [rootId for rootId in rootIds if rootId in nodes]
    if len(newRootIds) != 0:
        testIds.extend(_get_testIds(newRootIds, edges, nodes))
        return testIds
    else:
        return testIds

def msfd2fmeca(nodes, edges, system):
    sysInfo = {}
    for sys in sorted(system, key=lambda itm: itm["nodesId"]):
        for nodeId in sys["nodesId"]:
            if nodeId not in sysInfo.keys():
                sysInfo[nodeId] = sys["name"]
    nodeValidMap = [nodeId for nodeId, node in enumerate(nodes) if node["type"] in TESTTYPE + [RES]]
    testValidMap = [nodeId for nodeId, node in enumerate(nodes) if node["type"] in TESTTYPE]
    edges = _wash_non_fault_edge(edges, nodeValidMap)
    res = []
    for nodeId, node in enumerate(nodes):
        if node["type"] == RES and nodeId in sysInfo.keys():
            testMethods = [(nodes[_id]["text"] if isinstance(nodes[_id]["text"], str) else nodes[_id]["text"]["value"]) for _id in _get_testIds(edges[nodeId], edges, testValidMap)]
            testCause = [(nodes[edgeId]["text"] if isinstance(nodes[edgeId]["text"], str) else nodes[edgeId]["text"]["value"])
                         for edgeId, edge in enumerate(edges) if nodeId in edge and nodes[edgeId]["type"] == RES]
            res_ = [sysInfo[nodeId], (node["text"] if isinstance(node["text"], str) else node["text"]["value"]), 
                    ";".join(testCause),
                    ";".join([sgn.split("@")[-1] for sgn in testMethods])]
            cons_1 = True
            for effect_1 in edges[nodeId]:
                if nodes[effect_1]["type"] == RES:
                    cons_2 = True
                    for effect_2 in edges[effect_1]:
                        if nodes[effect_2]["type"] == RES:
                            cons_3 = True
                            for effect_3 in edges[effect_2]:
                                if nodes[effect_2]["type"] == RES:
                                    cons_1 = False
                                    cons_2 = False
                                    cons_3 = False
                                    res.append([*res_, 
                                                (nodes[effect_1]["text"] if isinstance(nodes[effect_1]["text"], str) else nodes[effect_1]["text"]["value"]),
                                                (nodes[effect_2]["text"] if isinstance(nodes[effect_2]["text"], str) else nodes[effect_2]["text"]["value"]),
                                                (nodes[effect_3]["text"] if isinstance(nodes[effect_3]["text"], str) else nodes[effect_3]["text"]["value"])])
                            if cons_3:
                                cons_2 = False
                                res.append([*res_, 
                                            (nodes[effect_1]["text"] if isinstance(nodes[effect_1]["text"], str) else nodes[effect_1]["text"]["value"]),
                                            (nodes[effect_2]["text"] if isinstance(nodes[effect_2]["text"], str) else nodes[effect_2]["text"]["value"]),
                                            ""])
                    if cons_2:
                        cons_1 = False
                        res.append([*res_, 
                                    (nodes[effect_1]["text"] if isinstance(nodes[effect_1]["text"], str) else nodes[effect_1]["text"]["value"]),
                                    "",
                                    ""])
            if cons_1:
                res.append([*res_, "", "", ""])
    data = pd.DataFrame(res, columns=["产品名称", "故障模式", "故障原因", "故障检测方法", "局部影响", "高一层次影响", "最终影响"])
    wf = to_merge(data, cols=["产品名称", "故障模式", "故障原因", "故障检测方法", "局部影响", "高一层次影响"])
    return wf