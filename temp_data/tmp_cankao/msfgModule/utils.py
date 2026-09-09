### 前端基本配置
SYS = "subsystem-node"
INPUT_NODE = "input-node"
OUTPUT_NODE = "output-node"
AND_NODE = "and-node" ## 故障节点
RES = "fault-node" ## 故障节点
SW = "switch-node" ## 开关节点
CKPT = "test-node" ## 测点
EDGE = "custom-edge"
TESTTYPE = [CKPT, SW]
FAULTTYPE = [INPUT_NODE, OUTPUT_NODE, RES, SW, AND_NODE]

WIDTH = 180
NODEWIDTH = 200
HEIGHT = 24
NODEHEIGHT = 30
ANC_HEIGHT = 24
PADDING = 50

DEBUG_MODE = False

from scipy.sparse import coo_matrix, csr_matrix
import numpy as np
import json, copy, time, uuid
from typing import Iterable, Dict
from io import BytesIO


if __name__ == "__main__":
    from gui_utils import render_node_pos, wash_node_pos
    from fmecaReader import read_fmeca
    from visioParse import parse_docx_visio, faultTree2msfd
    from pptxParse import parse_pptx, drawStruct as draw_fta
    CHECK_INVALID_COL = ["产品名称", "故障模式"] #["单元名称、型号或图号（2）", "故障模式(4)"]
    COMPONENT_COL = "{产品名称}" #"{单元名称、型号或图号（2）}"
    FAULTCAUSE_COL = "{故障原因}" #"{故障原因(5)}"
    FAULTMODE_COL = "{产品名称}#@#{故障模式}" #"{单元名称、型号或图号（2）}{故障模式(4)}"
    DETECTION_COL = "{故障检测方法}"
    SELF_EFFECT_COL = "{局部影响}"
    TRANS_EFFECT_COL = "{高一层次影响}"
    FINAL_EFFECT_COL = "{最终影响}"
else:
    from .gui_utils import render_node_pos, wash_node_pos
    from .fmecaReader import read_fmeca
    from .visioParse import parse_docx_visio, faultTree2msfd
    from .pptxParse import parse_pptx, drawStruct as draw_fta
    from ..configAll import CHECK_INVALID_COL, COMPONENT_COL, FAULTCAUSE_COL, FAULTMODE_COL, DETECTION_COL, SELF_EFFECT_COL, TRANS_EFFECT_COL, FINAL_EFFECT_COL

def get_uuid(kw=""):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{kw}#%.7f"%time.time()))

def _get_root_nodes(struct):
    return set(list(struct.keys())) - set({itt for it in struct.values() for itt in it})

def _get_sub_tree(struct, root_nodes, systemids, pre_name="", sys_map = {}):
    sys_res = []
    for itm in root_nodes:
        sys_map[itm] = f"{pre_name}{itm}"
        if len(struct.get(itm, [])) > 0:
            sys_res_ch, sys_map_ch = _get_sub_tree(struct, struct[itm], systemids, pre_name=f"{pre_name}{itm}>")
            sys_res.append({"name": itm, "true_name": itm, "key": str(systemids[itm][0]), "id": systemids[itm][1], "full_name": f"{pre_name}{itm}",
                    "children": sys_res_ch})
            sys_map.update(sys_map_ch)
        else: 
            sys_res.append({"name": itm, "true_name": itm, "key": str(systemids[itm][0]), "id": systemids[itm][1], "full_name": f"{pre_name}{itm}", "value": 1})
    return sys_res, sys_map
    
def get_base_tree(struct):
    system = {itm["name"]: {it["text"]["value"] for it in itm["data"]["nodes"] if it["type"]==SYS} for itm in struct}
    systemids = {itm["name"]: [itmId, itm["system_id"]] for itmId, itm in enumerate(struct)}
    root_nodes = _get_root_nodes(system)
    sys_res, sys_map = _get_sub_tree(system, root_nodes, systemids)
    return sys_res, sys_map

### 拉直多子系统嵌套结构依赖方法
def _flatten_graph(struct, act_uid=1, nodes_cnt=0):
    nodes = []; edges = []
    id_map = {}; systems = {}
    in_inds = []; out_inds = []
    planConfig = {}
    start_cnt = nodes_cnt
    act_id = struct[0]["sysmap"][act_uid]
    for itmId, itm in enumerate(struct[act_id]["data"]["nodes"]):
        if itm["type"] == SYS:
            nodes_, edges_, in_inds_, out_inds_, systems_, planConfig_ = _flatten_graph(struct, act_uid=itm["properties"]["SubsystemId"], nodes_cnt=nodes_cnt)
            planConfig.update(planConfig_)
            nodes.extend(nodes_)
            edges.extend(edges_)
            for true_ind, anchor_id in zip(in_inds_, [lin_["id"] for lin_ in sorted(itm["anchors"], key=lambda it_: it_["y"]) if lin_["type"]=="left"]):
                id_map[anchor_id] = true_ind
            for true_ind, anchor_id in zip(out_inds_, [lout_["id"] for lout_ in sorted(itm["anchors"], key=lambda it_: it_["y"]) if lout_["type"]=="right"]):
                id_map[anchor_id] = true_ind
            systems.update(systems_)
            systems[struct[0]["sysmap"][itm["properties"]["SubsystemId"]]] = {
                    "info": itm,
                    "name": itm["text"]["value"],
                    "SubsystemId": itm["properties"]["SubsystemId"], ## 该分系统本身的编号
                    "ParentSubsystemId": act_id, ## 需要同步更新上级分系统编号
                    "NodeId": itmId, ## 需要同步更新上级分系统中该分系统的队列编号
                    "nodesId": [nodes_cnt+node_itm for node_itm in range(len(nodes_))]
                }
            if itm["properties"].get("planDescript"):
                planConfig[itm["text"]["value"]] = itm["properties"]["planDescript"]
            nodes_cnt += len(nodes_)
        else:
            if itm["type"] == INPUT_NODE:
                in_inds.append([nodes_cnt, itm["properties"]["index"]])
            elif itm["type"] == OUTPUT_NODE:
                out_inds.append([nodes_cnt, itm["properties"]["index"]])
            nodes.append({
                **itm,
                "SubsystemId": act_id, ## 该节点所属的分系统编号
                "NodeId": itmId ## 需要系统中该节点的队列编号
                })
            id_map[itm["id"]+"_left"] = nodes_cnt
            id_map[itm["id"]+"_right"] = nodes_cnt
            for anchor_itm in itm["anchors"]:
                id_map[anchor_itm["id"]] = nodes_cnt
            edges.append({})
            nodes_cnt += 1
    for itm in struct[act_id]["data"]["edges"]:
        if "sourceAnchorId" in itm.keys():
            srcId = id_map[itm["sourceAnchorId"]]
        elif "sourceAnchorId" in itm.get("properties", {}).keys():
            srcId = id_map[itm["properties"]["sourceAnchorId"]]
        else:
            for nid, ninfo in enumerate(nodes):
                if ninfo["id"]==itm["sourceNodeId"]:
                    srcId = nid
                    break
            else:
                continue
        if "targetAnchorId" in itm.keys():
            trgId = id_map[itm["targetAnchorId"]]
        elif "targetAnchorId" in itm.get("properties", {}).keys():
            trgId = id_map[itm["properties"]["targetAnchorId"]]
        else:
            for nid, ninfo in enumerate(nodes):
                if ninfo["id"]==itm["targetNodeId"]:
                    trgId = nid
                    break
            else:
                continue
        edges[srcId-start_cnt][trgId] = itm.get("properties", {}).get("proba", 1.0)
    in_inds = [it[0] for it in sorted(in_inds, key=lambda it_: it_[1])]
    out_inds = [it[0] for it in sorted(out_inds, key=lambda it_: it_[1])]
    return nodes, edges, in_inds, out_inds, systems, planConfig

def _wash_or_node_edge(nodes, conn_source_map, nodes_map):
    edges = []
    for trgid in nodes:
        if trgid in nodes_map:
            edges.append(nodes_map.index(trgid))
        else:
            edges.extend(_wash_or_node_edge(conn_source_map[trgid], conn_source_map, nodes_map))
    return sorted(set(edges))

def filter_graph(nodes, edges, system):
    nodesMap = [nodeId for nodeId, node in enumerate(nodes) if node["type"] in [CKPT, RES, SW, AND_NODE]]
    conn_source_map = {}
    for edgeId, edge in enumerate(edges):
        edgeTrgIds = [int(k) for k in edge.keys()]
        if not edgeId in nodesMap:
            if not edgeId in conn_source_map.keys():
                conn_source_map[edgeId] = set(edgeTrgIds)
            else:
                conn_source_map[edgeId] |= set(edgeTrgIds)
    nodes = [nodes[nodeId] for nodeId in nodesMap]
    edges = [_wash_or_node_edge([int(k) for k in edges[nodeId].keys()], conn_source_map, nodesMap) for nodeId in nodesMap]
    system = [{**v, "nodesId": [nodesMap.index(v_) for v_ in v.get("nodesId", []) if v_ in nodesMap]} for v in system.values()]
    return nodes, edges, system

### 拉直多子系统嵌套结构
def flatten_graph(struct, only_mode=False):
    struct[0]["sysmap"] = dict([(itm["system_id"],itmId) for itmId, itm in enumerate(struct)])
    nodes, edges, _, _, system, planConfig = _flatten_graph(struct)
    if only_mode:
        nodes, edges, system = filter_graph(nodes, edges, system)
    return nodes, edges, system, planConfig

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

def msfd2triple(struct):
    info = []
    if isinstance(struct, Dict):
        struct = struct["SystemData"]
    nodes, edges, system, _ = flatten_graph(struct, only_mode=True)
    nodeValidMap = [nodeId for nodeId, node in enumerate(nodes) if node["type"] in TESTTYPE + [RES]]
    edges = _wash_non_fault_edge(edges, nodeValidMap)
    for srcId, trgIds in enumerate(edges):
        if nodes[srcId]["type"] == RES:
            for trgId in trgIds:
                if nodes[trgId]["type"] == RES:
                    info.append([nodes[srcId]["text"]["value"], nodes[trgId]["text"]["value"], 1])
                elif nodes[trgId]["type"] in TESTTYPE:
                    info.append([nodes[srcId]["text"]["value"], nodes[trgId]["text"]["value"], 2])
    sysInfo = {}
    for sys in sorted(system, key=lambda itm: itm["nodesId"]):
        for nodeId in sys["nodesId"]:
            if nodeId not in sysInfo.keys() and nodes[nodeId]["type"] == RES:
                sysInfo[nodeId] = sys["name"]
    for k, v in sysInfo.items():
        info.append([nodes[k]["text"]["value"], v, 3])    
    for itm in struct:
        for it in itm["data"]["nodes"]:
            if it["type"] == SYS:
                info.append([it["text"]["value"], itm["name"], 4])
    return info

def _render_edge(sysnodes, sysedges):
    sysedges_ = []
    for srcInd, trgInds in enumerate(sysedges):
        if len(trgInds)>0 and not all(map(lambda trgInd: isinstance(trgInd, Iterable), trgInds)):
            trgInds = [trgInds]
        for srcgrpind, trgInditm in enumerate(trgInds):
            if trgInditm and not isinstance(trgInditm[0], list):
                trgInditm = [trgInditm]
            for trgInd in trgInditm:
                if isinstance(trgInd, Iterable):
                    trggrpind, trgInd = trgInd
                else:
                    trggrpind = 0
                    
                srcAncs = [anchor for anchor in sysnodes[srcInd]["anchors"] if anchor["type"] == "right"]
                srcAnc = srcAncs[min(srcgrpind, len(srcAncs)-1)]
                trgAncs = [anchor for anchor in sysnodes[trgInd]["anchors"] if anchor["type"] == "left"]
                trgAnc = trgAncs[min(trggrpind, len(trgAncs)-1)]
                sysedges_.append({
                    "id": f"{sysnodes[srcInd]['id']}-{sysnodes[trgInd]['id']}-aslink",
                    "type": EDGE,
                    "sourceNodeId": sysnodes[srcInd]["id"],
                    "targetNodeId": sysnodes[trgInd]["id"],
                    "startPoint": {"x": srcAnc.get("x", -1), "y": srcAnc.get("y", -1)},
                    "endPoint": {"x": trgAnc.get("x", -1), "y": trgAnc.get("y", -1)},
                    "properties": {
                        "sourceAnchorId": srcAnc["id"],
                        "targetAnchorId": trgAnc["id"],
                        },
                    "pointsList": [],
                    "sourceAnchorId": srcAnc["id"],
                    "targetAnchorId": trgAnc["id"],
                    })
    return [noditm for noditm in sysnodes if noditm], sysedges_

def _flatten_edge(edge):
    if all(map(lambda itm: isinstance(itm, Iterable), edge)):
        edge = [ed for edg in edge for ed in edg]
    return [f"{edg[0]}#{edg[1]}" if isinstance(edg, Iterable) else f"0#{edg}" for edg in edge]

def _check_node(node):
    node["id"] = node.get("id", str(uuid.uuid1()))
    node["text"]["value"] = node["text"]["value"].split("#@#")[-1]
    node["type"] = node.get("type", RES)
    return node

def _getalledge(eid, pure_ind, edges):
    if eid in pure_ind:
        return [pure_ind.index(eid)]
    else:
        edges_ = []
        for eid_ in edges[eid]:
            edges_.extend(_getalledge(eid_, pure_ind, edges))
        return edges_

def _wash_nes(nodes, edges, system):
    pure_ind, nodes = zip(*[[itmId, node] for itmId, node in enumerate(nodes) if node["type"] not in [INPUT_NODE, OUTPUT_NODE]])
    pure_ind = list(pure_ind); nodes = list(nodes)
    system = {k: {**itm, "nodesId": [pure_ind.index(ind) for ind in itm.get("nodesId", []) if ind in pure_ind]} for k, itm in system.items()}
    allnodes = [i for i in range(len(pure_ind))]
    if max([0] + [len(itm["nodesId"]) for itm in system.values()]) != len(nodes):
        system[len(system)] = {"name": "root", "nodesId": allnodes}
    edges_ = [[] for _ in range(len(pure_ind))]
    for ind, rind in enumerate(pure_ind):
        for eid in edges[rind]:
            edges_[ind].extend(_getalledge(eid, pure_ind, edges))
    return nodes, [[[[0, eit] for eit in eitm]] for eitm in edges_], system

def reconstruct_graph(nodes, edges, system):
    struct = []; node2sys = {}
    nodes = [_check_node(node) for node in nodes]
    nodes, edges, system = _wash_nes(nodes, edges, system)
    system = sorted(system.values(), key=lambda itm: len(itm["nodesId"]))
    system_names = [itm["name"] for itm in system]
    sysalllen=len(system)
    nodeLen = len(nodes)
    for sysind, sysinfo in enumerate(system):
        xmin, xmax = float("inf"), -float("inf")
        ymin, ymax = float("inf"), -float("inf")
        sysnodeInd = sorted(set([node2sys.get(ind, ind) for ind in sysinfo["nodesId"]]))
        sysnodeInd = [ind for ind in sysnodeInd if "text" in nodes[ind].keys()]
        for sysinfoid in sysnodeInd:
            if not "text" in nodes[sysinfoid].keys():
                continue
            xmin = min(xmin, nodes[sysinfoid]["x"])
            xmax = max(xmax, nodes[sysinfoid]["x"])
            ymin = min(ymin, nodes[sysinfoid]["y"])
            ymax = max(ymin, nodes[sysinfoid]["y"])
            if nodes[sysinfoid]["type"] == SYS:
                node_name = nodes[sysinfoid]["text"]["value"]
                sysinnerind = system_names.index(node_name)
                struct[sysinnerind]["parent_id"] = sysalllen - sysind
        if len(sysnodeInd) == 0:
            xmin, xmax = -5000, 5000
            ymin, ymax = -5000, 5000
        in_map = {}
        out_map = {}
        sysnodes = [{
            "anchors": [{**anc, "x": anc["x"]-xmin, "y": anc["y"]-ymin} for anc in nodes[ind]["anchors"]],
            "text": {
                "x": nodes[ind]["text"]["x"]-xmin,
                "y": nodes[ind]["text"]["y"]-ymin,
                "value": nodes[ind]["text"]["value"]
                },
            "type": nodes[ind]["type"],
            "id": nodes[ind]["id"],
            "x":nodes[ind]["x"]-xmin,
            "y":nodes[ind]["y"]-ymin,
            "properties": nodes[ind]["properties"]}  for ind in sysnodeInd]
        sysedges = [[] for _ in sysnodeInd]
        for srcNind, trgNinds in enumerate(edges):
            if srcNind in sysnodeInd:
                srcInnerInd = sysnodeInd.index(srcNind)
                sysedges[srcInnerInd] = [[] for _ in trgNinds]
                for srcPortId, trgNinds_ in enumerate(trgNinds):
                    for trgNind in _flatten_edge([trgNinds_]):
                        if int(trgNind.split("#")[1]) in sysnodeInd:
                            trgportId, trgNind = map(int, trgNind.split("#"))
                            trgInnerInd = sysnodeInd.index(trgNind)
                            if f"{trgportId}#{trgNind}" not in _flatten_edge(sysedges[srcInnerInd][srcPortId]):
                                sysedges[srcInnerInd][srcPortId].append([trgportId, trgInnerInd])
                        elif trgNind not in out_map.keys():
                            out_map[trgNind] = {f"{srcPortId}#{srcInnerInd}"}
                        else:
                            out_map[trgNind].add(f"{srcPortId}#{srcInnerInd}")
            else:
                for trgNind in _flatten_edge(trgNinds):
                    if int(trgNind.split("#")[1]) in sysnodeInd:
                        trgportId, trgNind = map(int, trgNind.split("#"))
                        trgInnerInd = sysnodeInd.index(trgNind)
                        if srcNind not in in_map.keys():
                            in_map[srcNind] = {f"{trgportId}#{trgInnerInd}"}
                        else:
                            in_map[srcNind].add(f"{trgportId}#{trgInnerInd}")
        cnt = len(sysnodeInd)
        if nodeLen == len(sysinfo["nodesId"]):
            sysnodes = wash_node_pos(sysnodes, width=NODEWIDTH, height=NODEHEIGHT, padding=PADDING, sys=SYS)
            sysnodes_, sysedges_ = _render_edge(sysnodes, sysedges)
            struct.append({
                    "data":{
                        "nodes": sysnodes_,
                        "edges": sysedges_,
                        },
                    "name": sysinfo["name"],
                    "system_id": sysalllen-sysind,
                    "parent_id": None,
                })
        else:
            out_map_filter = []
            for trgNind, innerNindGrp in out_map.items():
                trgportId, trgNind = map(int, trgNind.split("#"))
                nodeRef = nodes[node2sys.get(trgNind, trgNind)]
                for itmId, itm in enumerate(out_map_filter):
                    if itm["nodeInds"] == innerNindGrp:
                        out_map_filter[itmId]["trgNinds"].append([trgportId, trgNind])
                else:
                    out_map_filter.append({
                        "name": f"输出{len(out_map_filter)+1}",
                        "config":{
                            "anchors": [{
                                "x": xmax-xmin+round(NODEWIDTH*1.5)+PADDING*round(1.25*NODEWIDTH/NODEHEIGHT)-NODEWIDTH/2,
                                "y": len(out_map_filter)*(PADDING + NODEHEIGHT),
                                "id": nodeRef["id"] + f"-asoutput{len(out_map_filter)}_left",
                                "type": "left"
                                }],
                            "text": {
                                "x":xmax-xmin+round(NODEWIDTH*1.5)+PADDING*round(1.25*NODEWIDTH/NODEHEIGHT) + 10,
                                "y": len(out_map_filter)*(PADDING + NODEHEIGHT),
                                "value": f"输出{len(out_map_filter)+1}"},
                            "type": "output-node",
                            "id": nodeRef["id"] + f"-asoutput{len(out_map_filter)}",
                            "x":xmax-xmin+round(NODEWIDTH*1.5)+PADDING*round(1.25*NODEWIDTH/NODEHEIGHT),
                            "y":len(out_map_filter)*(PADDING + NODEHEIGHT),
                            "properties": {
                                "showType": "edit",
                                "collision": False,
                                "detectable": True,
                                "fuzzible": False,
                                "fuzzy_state": 0,
                                "state": 0,
                                "icon": "/static/images/input.png",
                                "typeColor": '#85C1E9',
                                "typeColorRaw": '#85C1E9',
                                "flevel": 0,
                                "width": NODEWIDTH,
                                "ui": "node-red",
                                "index": len(out_map_filter)+1,
                                },
                            },
                        "trgNinds": [[trgportId, trgNind]],
                        "nodeInds": innerNindGrp,
                        "nodecnt": cnt,
                        })
                    cnt += 1
            in_map_filter = []
            for srcNind, innerNindGrp in in_map.items():
                for itmId, itm in enumerate(in_map_filter):
                    if itm["nodeInds"] == innerNindGrp:
                        in_map_filter[itmId]["srcNinds"].append(srcNind)
                else:
                    nodeRef = nodes[node2sys.get(srcNind, srcNind)]
                    in_map_filter.append({
                        "name": f"输入{len(in_map_filter)+1}",
                        "config":{
                            "anchors": [{
                                "x": -round(NODEWIDTH*1.5)-PADDING*round(1.25*NODEWIDTH/NODEHEIGHT)+NODEWIDTH/2,
                                "y": len(in_map_filter)*(PADDING + NODEHEIGHT),
                                "id": nodeRef["id"] + f"-asinput{len(in_map_filter)}_right",
                                "type": "right"
                                }],
                            "text": {
                                "x":-round(NODEWIDTH*1.5)-PADDING*round(1.25*NODEWIDTH/NODEHEIGHT) + 10,
                                "y":len(in_map_filter)*(PADDING + NODEHEIGHT),
                                "value": f"输入{len(in_map_filter)+1}"},
                            "type": "input-node",
                            "id": nodeRef["id"] + f"-asinput{len(in_map_filter)}",
                            "x":-round(NODEWIDTH*1.5)-PADDING*round(1.25*NODEWIDTH/NODEHEIGHT),
                            "y":len(in_map_filter)*(PADDING + NODEHEIGHT),
                            "properties": {
                                "showType": "edit",
                                "collision": False,
                                "detectable": True,
                                "fuzzible": False,
                                "fuzzy_state": 0,
                                "state": 0,
                                "icon": "/static/images/output.png",
                                "typeColor": '#85C1E9',
                                "typeColorRaw": '#85C1E9',
                                "flevel": 0,
                                "width": NODEWIDTH,
                                "ui": "node-red",
                                "index": len(in_map_filter)+1,
                                },
                            },
                        "srcNinds": [srcNind],
                        "nodeInds": [[int(it) for it in trgItem.split("#")] for trgItem in innerNindGrp],
                        "nodecnt": cnt,
                        })
                    cnt += 1
            sysnodes.extend([itm["config"] for itm in out_map_filter])
            sysnodes.extend([itm["config"] for itm in in_map_filter])
            sysedges.extend([[[]] for _ in range(len(sysnodes)-len(sysedges))])
            for itm in out_map_filter:
                for srcind in itm["nodeInds"]:
                    srcPortInd, srcNind = map(int, srcind.split("#"))
                    sysedges[srcNind] += [[] for _ in range(srcPortInd+1-len(sysedges[srcNind]))]
                    sysedges[srcNind][srcPortInd].append([0,itm["nodecnt"]])
            for itm in in_map_filter:
                sysedges[itm["nodecnt"]] = [sorted(itm["nodeInds"],key=lambda _x : _x[1]+_x[0]/100)]
            sysnodes = wash_node_pos(sysnodes, width=NODEWIDTH, height=NODEHEIGHT, padding=PADDING, sys=SYS)
            sysnodes_, sysedges_ = _render_edge(sysnodes, sysedges)
            struct.append({
                    "data":{
                        "nodes": sysnodes_,
                        "edges": sysedges_,
                        },
                    "name": sysinfo["name"],
                    "system_id": sysalllen-sysind,
                    "parent_id": None,
                })
            if len(sysnodes_) != 0:
                sysNodeRef = sysnodes_[0]
            else:
                sysNodeRef = {"id": get_uuid("node-conn")}
            sysnode = {
                    "id": sysNodeRef["id"]+"-assys",
                    "type": SYS,
                    "x": round((xmax+xmin)/2),
                    "y": round((ymax+ymin)/2),
                    "properties": {
                        "tableName": "",
                        "SubsystemId": sysalllen-sysind,
                        "fields": {
                            "input": len(in_map_filter),
			                "inputNames": [in_itm['config']['text']['value'] for in_itm in in_map_filter],
                            "output": len(out_map_filter),
                            "outputNames": [out_itm['config']['text']['value'] for out_itm in out_map_filter],
                            },
                        },
                    "text": {
                        "x": round((xmax+xmin)/2) - 5,
                        "y": round((ymax+ymin)/2) + 5 + ANC_HEIGHT*(-max(len(in_map_filter), len(out_map_filter))/2),
                        "value": sysinfo["name"],
                        },
                    "anchors": [
                        {
                            "x": round((xmax+xmin)/2) - WIDTH/2,
                            "y": round((ymax+ymin)/2) + 35 + ANC_HEIGHT*(-max(len(in_map_filter), len(out_map_filter))/2+itmId),
                            "id": sysNodeRef["id"]+f"-assys_{itmId}_left",
                            "edgeAddable": False,
                            "type": "left",
                            } for itmId, itm in enumerate(in_map_filter)] + \
                    [
                        {
                            "x": round((xmax+xmin)/2) + WIDTH/2,
                            "y": round((ymax+ymin)/2) + 35 + ANC_HEIGHT*(-max(len(in_map_filter), len(out_map_filter))/2+itmId),
                            "id": sysNodeRef["id"]+f"-assys_{itmId}_right",
                            "edgeAddable": False,
                            "type": "right",
                            } for itmId, itm in enumerate(out_map_filter)]

                }
            for nid in sysnodeInd:
                nodes[nid] = {}
                edges[nid] = [[]]
            nodes.append(sysnode)
            edges.append([[] for _ in out_map_filter])
            for itmId, itm in enumerate(out_map_filter):
                edges[-1][itmId] = itm["trgNinds"]
            for itmId, itm in enumerate(in_map_filter):
                for srcId in itm["srcNinds"]:
                    edgesSys = [itmId for itmId, itm in enumerate(edges[srcId]) if any(
                        map(lambda it_: it_[1] in sysnodeInd if isinstance(it_, Iterable) else it_ in sysnodeInd, itm)
                        )]
                    edgraw, edges[srcId] = edges[srcId], [[]]
                    for itm_ in edgraw:
                        edges[srcId].append([])
                        for itm in itm_:
                            if not isinstance(itm, Iterable):
                                itm = [0, itm]
                            itmport, itmv = itm
                            if itmv not in sysnodeInd:
                                edges[srcId].extend([[] for _ in range(itmport+1-len(edges[srcId]))])
                                edges[srcId][itmport].append(itmv)
                    for srcport in edgesSys:
                        edges[srcId].extend([[] for _ in range(srcport+1-len(edges[srcId]))])
                        edges[srcId][srcport].append([itmId, len(nodes)-1])
            node2sys.update({ind: len(nodes)-1 for ind in sysinfo["nodesId"]})
    return struct[::-1]

### D矩阵转化
def to_D_mat(nodes, edges, system, eps=1e-9, raise_collision=True):
    faultInd, faultName, faultLoc, faultType, faultUUid = zip(*[[nodeId, node["text"]["value"], (node["SubsystemId"], node["NodeId"]), node["type"], node["id"]] for nodeId, node in enumerate(nodes) if node["type"] in FAULTTYPE])
    testInd, testName, testLoc = zip(*[[nodeId, node["text"]["value"], (node["SubsystemId"], node["NodeId"])] for nodeId, node in enumerate(nodes) if node["type"] in TESTTYPE])
    try:
        ConnInd, _, _ = zip(*[[nodeId, node["text"]["value"], (node["SubsystemId"], node["NodeId"])] for nodeId, node in enumerate(nodes) if node["type"] in INPUT_NODE + OUTPUT_NODE])
    except:
        ConnInd, _, _ = [], [], []
    ConnIds = [faultInd.index(ind) for ind in ConnInd]
    try:
        ANDInd, _, _ = zip(*[[nodeId, node["text"]["value"], (node["SubsystemId"], node["NodeId"])] for nodeId, node in enumerate(nodes) if node["type"] == AND_NODE])
    except:
        ANDInd, _, _ = [], [], []
    ANDIds = [faultInd.index(ind) for ind in ANDInd]
    try:
        swInd, _, _ = zip(*[[nodeId, node["text"]["value"], (node["SubsystemId"], node["NodeId"])] for nodeId, node in enumerate(nodes) if node["type"] == SW])
    except:
        swInd = []
    edges = [{srcId: 1, **edge} if srcId in swInd else edge for srcId, edge in enumerate(edges) ]
    faultMap = [[faultInd.index(srcId), faultInd.index(trgId), edgeP] for srcId, edge in enumerate(edges) for trgId, edgeP in edge.items() if trgId in faultInd]
    testMap = [[faultInd.index(srcId), testInd.index(trgId), edgeP] for srcId, edge in enumerate(edges) for trgId, edgeP in edge.items() if trgId in testInd]

    if len(testMap) == 0:
        test_mat = coo_matrix(([0], ([0],[0])),shape=(len(faultName), len(testName)), dtype="float32")
        test_mat.eliminate_zeros()
    else:
        xid, yid, p = zip(*testMap)
        test_mat = coo_matrix((p, (xid, yid)), shape=(len(faultName), len(testName)), dtype="float32")

    inner_forward_map = {}
    inner_forward_map_and = {}
    inner_forward_map_without_and = {}
    collision_node = set()
    if len(faultMap) == 0:
        fault_and_couple_mat = coo_matrix(([0], ([0],[0])),shape=(len(faultName), len(faultName)), dtype="float32")
        fault_and_couple_mat.eliminate_zeros()
    else:
        for xid_, yid_, p_ in faultMap:
            if yid_ in inner_forward_map.keys():
                inner_forward_map[yid_][xid_] = p_
            else:
                inner_forward_map[yid_] = {xid_: p_}
            ## AND as ckpt in order to decouple the source
            if faultType[yid_] == AND_NODE:
                if yid_ in inner_forward_map_and.keys():
                    inner_forward_map_and[yid_][xid_] = p_
                else:
                    inner_forward_map_and[yid_] = {xid_: p_}
        for _ in edges:
            lin_cnt = 0
            for yid_, itm in inner_forward_map.items():
                for xid_, p_1 in list(itm.items()):
                    if yid_ == xid_:
                        continue
                    for x_id_new, p_2 in inner_forward_map.get(xid_, {}).items():
                        if xid_ == x_id_new:
                            continue
                        if yid_ == x_id_new:
                            collision_node.add(yid_)
                            continue
                        pre_p = inner_forward_map[yid_].get(x_id_new, 0)
                        new_p = max(pre_p, p_1*p_2 if p_1*p_2>eps else 0)
                        inner_forward_map[yid_][x_id_new] = new_p
                        lin_cnt += inner_forward_map[yid_][x_id_new] - pre_p
                        ## AND as ckpt in order to decouple the source
                        if faultType[yid_] == AND_NODE:
                            if yid_ in inner_forward_map_and.keys():
                                inner_forward_map_and[yid_][x_id_new] = new_p
                            else:
                                inner_forward_map_and[yid_] = {x_id_new: new_p}
                        if faultType[xid_] != AND_NODE:
                            if yid_ in inner_forward_map_without_and.keys():
                                inner_forward_map_without_and[yid_][x_id_new] = new_p
                            else:
                                inner_forward_map_without_and[yid_] = {x_id_new: new_p}
            if lin_cnt < eps:
                break
        if collision_node and raise_collision:
            raise Exception(f"[LoopError] It exists {len(collision_node)} Cause-Effect Loop on Fault Node list(collision_node)")
        if inner_forward_map_and:
            xid, yid, p = zip(*[[xid_, yid_, p_] for yid_, itm in inner_forward_map_and.items() for xid_, p_ in itm.items()])
            fault_mat_without_and = coo_matrix((p, (xid, yid)),shape=(len(faultName), len(faultName)), dtype="float32")
        
            ## Calcul AND-fuzzy Matrix
            fault_and_couple_mat = - fault_mat_without_and.T.dot(((eps - 1)* fault_mat_without_and).log1p()).expm1()
            fault_and_couple_mat = (fault_and_couple_mat + fault_and_couple_mat.T)/2
        else:
            fault_and_couple_mat = coo_matrix(([0], ([0], [0])),shape=(len(faultName), len(faultName)), dtype="float32")
        _findRange = list(range(len(faultName)))
        fault_and_couple_mat += coo_matrix(([1 for _ in faultName], (_findRange, _findRange)),shape=(len(faultName), len(faultName)), dtype="float32")
        fault_and_couple_mat.eliminate_zeros()
        
    ckpt_map = {}
    ckpt_map_without_and = {}
    if testMap:
        for xid_, yid_, p_ in testMap:
            if yid_ not in ckpt_map.keys():
                ckpt_map[yid_] = {}
            ckpt_map[yid_][xid_] = max(ckpt_map[yid_].get(xid_, 0), p_)
            for trgid_, p_2 in inner_forward_map.get(xid_, {}).items():
                ckpt_map[yid_][trgid_] = max(ckpt_map[yid_].get(trgid_, 0), p_*p_2)
            
            if yid_ not in ckpt_map_without_and.keys():
                ckpt_map_without_and[yid_] = {}
            ckpt_map_without_and[yid_][xid_] = max(ckpt_map_without_and[yid_].get(xid_, 0), p_)
            for trgid_, p_2 in inner_forward_map_and.get(xid_, {}).items():
                ckpt_map_without_and[yid_][trgid_] = max(ckpt_map_without_and[yid_].get(trgid_, 0), p_*p_2)
                
        xid, yid, p = zip(*[[xid_, yid_, p_] for yid_, itm in ckpt_map.items() for xid_, p_ in itm.items()])
        D_mat = coo_matrix((p, (xid, yid)), shape=(len(faultName), len(testName)), dtype="float32").tocsr()
        D_mat.eliminate_zeros()
        
        if ckpt_map_without_and:
            xid, yid, p = zip(*[[xid_, yid_, p_] for yid_, itm in ckpt_map_without_and.items() for xid_, p_ in itm.items()])
            D_without_and_mat = coo_matrix((p, (xid, yid)), shape=(len(faultName), len(testName)), dtype="float32").tocsr()
            D_without_and_mat.eliminate_zeros()
        else:
            D_without_and_mat = coo_matrix(([0], ([0], [0])), shape=(len(faultName), len(testName)), dtype="float32").tocsr()
            D_without_and_mat.eliminate_zeros()
        
        F_xid, F_yid, F_p = zip(*[[xid_, yid_, p_] for yid_, itm in inner_forward_map.items() for xid_, p_ in itm.items()])
        F_mat = coo_matrix((F_p, (F_xid, F_yid)), shape=(len(faultName), len(faultName)), dtype="float32").tocsr()
        F_mat.eliminate_zeros()
    else:
        D_mat = coo_matrix(([0], ([0], [0])), shape=(len(faultName), len(testName)), dtype="float32").tocsr()
        D_mat.eliminate_zeros()
        
        D_without_and_mat = coo_matrix(([0], ([0], [0])), shape=(len(faultName), len(testName)), dtype="float32").tocsr()
        D_without_and_mat.eliminate_zeros()
        
        F_mat = coo_matrix(([0], ([0], [0])), shape=(len(faultName), len(faultName)), dtype="float32").tocsr()
        F_mat.eliminate_zeros()

    sysmap = {
        sysk: {
            **sysv,
            "nodesId": [faultInd.index(nid) for nid in sysv["nodesId"] if nid in faultInd]
            } for sysk, sysv in system.items()
        }
    
    if sysmap:
        sysNames, sysFaultIds = zip(*[[k, v["nodesId"]] for k,v in sysmap.items()])
        sysRowIds, sysColIds = zip(*[[kid, v_] for kid, v in enumerate(sysFaultIds) for v_ in v])
        C_mat = coo_matrix(([1 for _ in sysRowIds], (sysRowIds, sysColIds)), shape=(len(sysNames), len(faultName)), dtype="float32").tocsr()
        C_mat.eliminate_zeros()
    else:
        sysNames = []
        C_mat = coo_matrix(([0], ([0], [0])), shape=(len(sysNames), len(faultName)), dtype="float32").tocsr()
    
    faultValid = [fid for fid, fn in enumerate(faultInd) if fn not in swInd]
    faultValidNonConn = [fid for fid, fn in enumerate(faultInd) if fn not in swInd and fid not in ConnIds]
    D_mat = D_mat[faultValid, :]
    D_without_and_mat = D_without_and_mat[faultValid, :]
    faultNameNonConn = [itm for itmid, itm in enumerate(faultName) if itmid in faultValidNonConn]
    faultUUidNonConn = [itm for itmid, itm in enumerate(faultUUid) if itmid in faultValidNonConn]
    faultName = [itm for itmid, itm in enumerate(faultName) if itmid in faultValid]
    faultLoc = [itm for itmid, itm in enumerate(faultLoc) if itmid in faultValid]
    faultUUid = [itm for itmid, itm in enumerate(faultUUid) if itmid in faultValid]
    faultConfig = {
        faultUUid_: {
            "name": faultName_, "component": [v["name"] for k, v in sysmap.items() if faultInd[faultId_] in v["nodesId"]]
            }
        for faultId_, faultName_, faultUUid_ in zip(range(len(faultValidNonConn)), faultNameNonConn, faultUUidNonConn)}
    #D_mat, testName, faultName, ConnIds, sysmap [0,1,2,3,6]
    return D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, testName, faultName, sysNames, ConnIds, ANDIds, testLoc, faultLoc, sysmap, collision_node, faultConfig

### D矩阵推理依赖方法
def _cal_failure(D_mat, p_test, eps=1e-20):
    return np.minimum(1, np.maximum(0, np.exp(D_mat.dot(np.log(np.maximum(p_test, eps))[:,None]))))

def _divide_sparse_neg_log_1p(vector_, denom_mat, eps=1e-20):
    return denom_mat._with_data(np.log(np.maximum(1-vector_[denom_mat.indices]/denom_mat.data, eps))).tocsr()

def _cal_fuzzy(D_mat, p_fault, fault_and_couple_mat, eps=1e-20):
    ## ε-slack
    logc_p_fault = np.log(np.maximum(1 - p_fault, eps))
    #D_mat_bool = (D_mat > eps).astype("float32")
    DmatT = D_mat.T.tocsr()
    
    ## Eliminate And-fuzzy
    itm = DmatT._with_data(logc_p_fault[DmatT.indices, 0]*DmatT.data).dot(fault_and_couple_mat).T.tocsr()
    
    log_p_eff_diff = D_mat.multiply(
        _divide_sparse_neg_log_1p(
            np.exp(D_mat.T.dot(logc_p_fault)).flatten(),
            itm._with_data(np.exp(itm.data)).tocsr(), eps=eps
            )
        )
    log_p_eff = log_p_eff_diff.sum(axis=-1).A
    
    return np.maximum(0, p_fault*np.minimum(1, np.exp(log_p_eff)))

### D矩阵推理
def detect_by_D_mat(p_test, D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, fault_and_comp_couple_mat=None, sysNames=[], sysmap={}, ConnIds=[], ANDIds=[], p_fault_semi=None, eps=1e-10, n_round=5):
    p_fault = _cal_failure(D_mat, np.maximum(0, np.minimum(1, p_test)), eps=eps**2)
    p_fault = p_fault*D_mat.max(axis=1).A
    if len(ANDIds) > 0:
        p_fault_without_and = _cal_failure(D_without_and_mat, np.maximum(0, np.minimum(1, p_test)), eps=eps**2)
        p_fault_without_and = p_fault_without_and*D_without_and_mat.max(axis=1).A
        p_fault = np.maximum(p_fault, p_fault_without_and)
    if not p_fault_semi is None:
        p_fault = p_fault_semi*p_fault
    DmatT = D_mat.T.tocsr()
    if len(ConnIds) == 0:
        p_fuzzy = _cal_fuzzy(D_mat, p_fault, fault_and_couple_mat, eps=eps**2)
    else:
        Dpure = DmatT._with_data(np.array([0 if (i in ConnIds or i in ANDIds) else v for i, v in zip(DmatT.indices, DmatT.data)], dtype="float32")).T.tocsr()
        Dpure.eliminate_zeros()
        p_fuzzy = _cal_fuzzy(Dpure, p_fault, fault_and_couple_mat, eps=eps**2)
     
    _sys_p_fault = np.minimum(1, np.maximum(0, np.exp(C_mat.dot(np.log(1 - p_fault + eps)))))
    sys_p_fault = 1 - np.round(_sys_p_fault, int(round(n_round*1.5)))**(1/np.maximum(1, C_mat.sum(axis=1).A))
    
    if fault_and_comp_couple_mat is None:
        fault_comp_couple_mat = - C_mat.T.dot(((eps-1)*C_mat).log1p()).expm1()
        fault_and_comp_couple_mat = fault_and_couple_mat + fault_comp_couple_mat - fault_and_couple_mat.multiply(fault_comp_couple_mat)
    if len(ConnIds) == 0:
        p_fuzzy_ = _cal_fuzzy(D_mat, p_fault, fault_and_comp_couple_mat, eps=eps**2)
    else:
        Dpure = DmatT._with_data(np.array([0 if (i in ConnIds or i in ANDIds) else v for i, v in zip(DmatT.indices, DmatT.data)], dtype="float32")).T.tocsr()
        Dpure.eliminate_zeros()
        p_fuzzy_ = _cal_fuzzy(Dpure, p_fault, fault_and_comp_couple_mat, eps=eps**2)
    sys_p_fuzzy = sys_p_fault * np.minimum(1, np.maximum(0, np.exp(C_mat.dot(np.log(np.maximum(p_fuzzy_ + (1 - p_fault), eps))))))
    
    sysres = {str(sysk): {"proba": float(round(sys_p_fault_, n_round)),
                                    "fuzzy_proba": float(round(sys_p_fuzzy_, n_round))} for sysk, sys_p_fault_, sys_p_fuzzy_ in zip(sysNames, 
                                                                                                                    sys_p_fault.flatten(), 
                                                                                                                    sys_p_fuzzy.flatten())}
    sysres["-1"] = {"proba": float(round(1 - np.prod(1 - p_fault)**(1/np.maximum(1, p_fault.size)), n_round)), "fuzzy_proba": 0}
    # sysres = {sysk: _or_failure_fuzzy(*zip(*[[p_fault[nId], p_fuzzy[nId]] for nId in sysv["nodesId"] if nId not in ConnIds])) for sysk, sysv in sysmap.items()}
    return np.round(p_fault.flatten(), n_round), np.round(p_fuzzy.flatten(), n_round), sysres

def render(struct, p_test, p_fault, p_fuzzy, testLoc, faultLoc, sysmap, sysres):
    struct = copy.deepcopy(struct)
    for t_ind, p_fault_ in enumerate(p_test):
        act_id, node_id = testLoc[t_ind]
        struct[act_id]["data"]["nodes"][node_id]["properties"]["showType"] = "analyse"
        struct[act_id]["data"]["nodes"][node_id]["properties"]["state"] = float(p_fault_)
        struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = 0
    f_ind = 0
    for p_failure_, p_fuzzy_ in zip(p_fault, p_fuzzy):
        act_id, node_id = faultLoc[f_ind]
        struct[act_id]["data"]["nodes"][node_id]["properties"]["showType"] = "analyse"
        if struct[act_id]["data"]["nodes"][node_id]["properties"].get("detectable", True):
            struct[act_id]["data"]["nodes"][node_id]["properties"]["state"] = float(p_failure_)
            struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = float(p_fuzzy_)
        else: ## 补充不可测试测点的逻辑
            struct[act_id]["data"]["nodes"][node_id]["properties"]["state"] = 0
            struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = 1
        f_ind += 1
    for key, sysr_ in sysres.items():
        if key == "-1":
            continue
        parent_sys_id = sysmap[str(key)]["ParentSubsystemId"]
        node_id = sysmap[str(key)]["NodeId"]
        struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["showType"] = "analyse"
        struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["state"] = float(sysr_["proba"])
        struct[parent_sys_id]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = float(sysr_["fuzzy_proba"])
        struct[int(key)]["data"]["properties"] = {**struct[int(key)]["data"].get("properties", {}), **sysr_}
    return struct

## D矩阵推理（含渲染）
def detect_with_render(p_test, D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, struct, testLoc, faultLoc, sysNames, sysmap, ConnIds=[], ANDIds=[], fault_and_comp_couple_mat=None, eps=1e-9, n_round=5):
    p_fault, p_fuzzy, sysres = detect_by_D_mat(p_test, D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, fault_and_comp_couple_mat, sysNames, sysmap, ConnIds=ConnIds, ANDIds=ANDIds, eps=eps/10)
    ## 渲染步骤
    struct = copy.deepcopy(struct)
    for t_ind, p_fault_ in enumerate(p_test):
        act_id, node_id = testLoc[t_ind]
        struct[act_id]["data"]["nodes"][node_id]["properties"]["showType"] = "analyse"
        struct[act_id]["data"]["nodes"][node_id]["properties"]["state"] = float(p_fault_)
        struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = 0
    f_ind = 0
    for p_failure_, p_fuzzy_ in zip(p_fault, p_fuzzy):
        act_id, node_id = faultLoc[f_ind]
        struct[act_id]["data"]["nodes"][node_id]["properties"]["showType"] = "analyse"
        if struct[act_id]["data"]["nodes"][node_id]["properties"].get("detectable", True):
            struct[act_id]["data"]["nodes"][node_id]["properties"]["state"] = float(p_failure_)
            struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = float(p_fuzzy_)
        else: ## 补充不可测试测点的逻辑
            struct[act_id]["data"]["nodes"][node_id]["properties"]["state"] = 0
            struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = 1
        f_ind += 1
    for key, sysr_ in sysres.items():
        parent_sys_id = sysmap[key]["ParentSubsystemId"]
        node_id = sysmap[key]["NodeId"]
        struct[int(parent_sys_id)]["data"]["nodes"][node_id]["properties"]["showType"] = "analyse"
        struct[int(parent_sys_id)]["data"]["nodes"][node_id]["properties"]["state"] = float(sysr_["proba"])
        struct[int(parent_sys_id)]["data"]["nodes"][node_id]["properties"]["fuzzy_state"] = float(sysr_["fuzzy_proba"])
        struct[int(key)]["data"]["properties"] = {**struct[int(key)]["data"].get("properties", {}), **sysr_}
    return struct

def qualitat_detect_by_D_mat(p_test, D_mat):
    norm_test = np.where(p_test<0.5)[0]
    D_mat_ = D_mat[:, norm_test]
    D_mat_.eliminate_zeros()
    norm_fault = set(np.where(np.diff(D_mat_.tocsr().indptr)>0.5)[0])
    f_f_fault = set(range(D_mat.shape[0])) - norm_fault
    f_f_fault = list(f_f_fault)
    if f_f_fault:
        test_inds = list(set(range(len(p_test)))-set(norm_test))
        D_mat_ = D_mat[:, test_inds].tocsc()[f_f_fault, :].tocsr()
        D_mat_.eliminate_zeros()
        only_one_test = np.where(np.diff(D_mat_.T.tocsr().indptr)<1.5)[0]
        D_mat_ = D_mat_[:, only_one_test]
        fuzzy_fault = [f_f_fault[i] for i in set(np.where(np.diff(D_mat_.tocsr().indptr)>0.5)[0])]
    else:
        fuzzy_fault = f_f_fault
    return zip(*[[float(i not in norm_fault), float(i not in norm_fault)*float(i not in fuzzy_fault)] for i in range(D_mat.shape[0])])

## 解算依赖导出为Json
def to_json(D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, struct, testLoc, faultLoc, sysmap, testName, faultName, sysNames, collision_node=[], ConnIds=[], ANDIds=[]):
    return json.dumps({
        "struct": struct,
        "testLoc": testLoc,
        "faultLoc": faultLoc,
        "sysmap": sysmap,
        "testName": testName,
        "faultName": faultName,
        "sysNames": sysNames,
        "collision_node": [int(ind) for ind in collision_node],
        "ANDIds": [int(ind) for ind in ANDIds],
        "ConnIds": [int(ind) for ind in ConnIds],
        "C_mat": [
                C_mat.indptr.tolist(),
                C_mat.indices.tolist(),
                C_mat.data.tolist()
                ],
        "D_mat": [
                D_mat.indptr.tolist(),
                D_mat.indices.tolist(),
                D_mat.data.tolist()
                ],
        "D_without_and_mat": [
                D_without_and_mat.indptr.tolist(),
                D_without_and_mat.indices.tolist(),
                D_without_and_mat.data.tolist()
                ],
        "fault_and_couple_mat": [
                fault_and_couple_mat.indptr.tolist(),
                fault_and_couple_mat.indices.tolist(),
                fault_and_couple_mat.data.tolist()
                ],
        "F_mat": [
                F_mat.indptr.tolist(),
                F_mat.indices.tolist(),
                F_mat.data.tolist()
                ]
        })

## 解算依赖从Json导入
def from_json(configJson):
    config = json.loads(configJson)
    struct = config["struct"]
    testLoc = config["testLoc"]
    faultLoc = config["faultLoc"]
    sysmap = config["sysmap"]
    testName = config["testName"]
    faultName = config["faultName"]
    sysNames = config["sysNames"]
    C_indptr, C_indices, C_values = config["C_mat"]
    C_mat = csr_matrix((C_values, C_indices, C_indptr),shape=(len(sysNames), len(faultName)), dtype="float32")
    D_indptr, D_indices, D_values = config["D_mat"]
    D_mat = csr_matrix((D_values, D_indices, D_indptr),shape=(len(faultName), len(testName)), dtype="float32")
    D_without_and_indptr, D_without_and_indices, D_without_and_values = config["D_without_and_mat"]
    D_without_and_mat = csr_matrix((D_without_and_values, D_without_and_indices, D_without_and_indptr),shape=(len(faultName), len(testName)), dtype="float32")
    fault_and_couple_indptr, fault_and_couple_indices, fault_and_couple_values = config["fault_and_couple_mat"]
    fault_and_couple_mat = csr_matrix((fault_and_couple_values, fault_and_couple_indices, fault_and_couple_indptr),shape=(len(faultName), len(faultName)), dtype="float32")
    F_indptr, F_indices, F_values = config["F_mat"]
    F_mat = csr_matrix((F_values, F_indices, F_indptr),shape=(len(faultName), len(faultName)), dtype="float32")
    collision_node = config["collision_node"]
    ANDIds = config["ANDIds"]
    ConnIds = config["ConnIds"]
    return D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, struct, testLoc, faultLoc, sysmap, testName, faultName, sysNames, collision_node, ConnIds, ANDIds

def _get_detect_isolat_ratio(checkLen, fuzzyLen, faultLen, testLen):
    return [
            min(1, max(0, checkLen/faultLen)),
            min(1, max(0, 1 - fuzzyLen/checkLen)), #min(1, max(0, 1 - fuzzyLen/checkLen)),
            min(1, max(0, 1 - max(0, min(1, (checkLen-fuzzyLen)/testLen))))
            ]

## 流图性能评测
def check_graph(convertStruct, eps=1e-9):
    D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, struct, testLoc, faultLoc, sysmap, testName, faultName, sysNames, collision_node, ConnIds, ANDIds = from_json(convertStruct)
    fnodes = [struct[act_id]["data"]["nodes"][node_id] for act_id, node_id in faultLoc]
    validNodes = [nodeId for nodeId, node in enumerate(fnodes) if node["type"] not in [INPUT_NODE, OUTPUT_NODE]]
    unCheckIdList_ = np.where(D_mat.max(axis=1).todense() < 0.5)[0]
    DmatT = D_mat.T.tocsr()
    Dpure = DmatT._with_data(np.array([0 if i in ConnIds else v for i, v in zip(DmatT.indices, DmatT.data)], dtype="float32")).T.tocsr()
    Dpure.eliminate_zeros()
    fuzzyList = np.where(_cal_fuzzy(Dpure, np.ones((len(faultName),1), dtype="float32"), fault_and_couple_mat, eps=eps**2).flatten() >= 0.5 - eps)[0]

    collision_node_str = {f"{faultLoc[f_ind][0]}#{faultLoc[f_ind][1]}" for f_ind in collision_node}
    unCheckIdList_in_str = {f"{faultLoc[f_ind][0]}#{faultLoc[f_ind][1]}" for f_ind in unCheckIdList_}
    fuzzyList_in_str = {f"{faultLoc[f_ind][0]}#{faultLoc[f_ind][1]}" for f_ind in fuzzyList if not f_ind in unCheckIdList_}

    for act_id, _ in enumerate(struct):
        for node_id, _ in enumerate(struct[act_id]["data"]["nodes"]):
            struct[act_id]["data"]["nodes"][node_id]["properties"]["collision"] = False
            struct[act_id]["data"]["nodes"][node_id]["properties"]["detectable"] = True
            struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzible"] = False
            struct[act_id]["data"]["nodes"][node_id]["properties"]["showType"] = "check"
            if f"{act_id}#{node_id}" in collision_node_str:
                struct[act_id]["data"]["nodes"][node_id]["properties"]["collision"] = True
            if f"{act_id}#{node_id}" in unCheckIdList_in_str:
                struct[act_id]["data"]["nodes"][node_id]["properties"]["detectable"] = False
            if f"{act_id}#{node_id}" in fuzzyList_in_str:
                struct[act_id]["data"]["nodes"][node_id]["properties"]["fuzzible"] = True
    for subsysId, subsysInfo in sysmap.items():
        act_id = subsysInfo["ParentSubsystemId"]
        node_id = subsysInfo["NodeId"]
        if not act_id is None:
            struct[int(act_id)]["data"]["nodes"][node_id]["properties"]["showType"] = "check"
            struct[int(act_id)]["data"]["nodes"][node_id]["properties"]["detectable"] = not all(map(lambda itm: itm in unCheckIdList_, subsysInfo["nodesId"]))
            struct[int(act_id)]["data"]["nodes"][node_id]["properties"]["collision"] = any(map(lambda itm: itm in collision_node, subsysInfo["nodesId"]))
            struct[int(act_id)]["data"]["nodes"][node_id]["properties"]["fuzzible"] = any(map(lambda itm: itm in list(set(fuzzyList) - set(unCheckIdList_)), subsysInfo["nodesId"]))
    fLen = len(validNodes)
    checkLen = fLen - len([nodeInd for nodeInd in unCheckIdList_ if nodeInd in validNodes])
    fuzzyLen = len([nodeInd for nodeInd in fuzzyList if nodeInd in validNodes])
    inds = [ind for ind in range(len(faultName)) if ind not in ConnIds and ind not in ANDIds]
    return {
        "data": struct,
        "D_mat": D_mat.todense()[inds, :].tolist(),
        "col_names": testName,
        "row_names": [faultName[ind] for ind in inds],
        "detect_isolat_ratio": _get_detect_isolat_ratio(checkLen, fuzzyLen, fLen, len(testName)),
        }

def convert_fmeca(df):
    nodes, edges, system = read_fmeca(
        df,
        check_invalid_col=CHECK_INVALID_COL,
        component_col=COMPONENT_COL,
        faultcause_col=FAULTCAUSE_COL,
        faultmode_col=FAULTMODE_COL,
        detection_col=DETECTION_COL,
        self_effect_col=SELF_EFFECT_COL,
        trans_effect_col=TRANS_EFFECT_COL,
        final_effect_col=FINAL_EFFECT_COL,
        ckptnode=CKPT, resnode=RES)
    nodes = render_node_pos(nodes, edges, width=NODEWIDTH, height=NODEHEIGHT, padding=PADDING)
    return reconstruct_graph(nodes, edges, system)

def convert_fta(df):
    if isinstance(df, str):
        try:
            res = parse_pptx(df)
        except:
            res = parse_docx_visio(df, r"./static/format/faultTreeConfig.vsdx")
    else:
        with BytesIO() as io_roaming:
            df.save(io_roaming)
            io_roaming.seek(0)
            try:
                res = parse_pptx(df)
            except:
                import traceback
                traceback.print_exc()
                res = parse_docx_visio(df, r"./static/format/faultTreeConfig.vsdx")
    res = faultTree2msfd(res)
    nodes = res.get("nodes", [])
    edges_ = res.get("edges", [])
    nodeIdList = [node["id"] for node in nodes]
    edges = [[] for _ in nodes]
    for edge in edges_:
        if edge["from"] in nodeIdList and edge["to"] in nodeIdList:
            edges[nodeIdList.index(edge["from"])].append(nodeIdList.index(edge["to"]))
    nodes = render_node_pos(nodes, edges, width=NODEWIDTH, height=NODEHEIGHT, padding=PADDING)
    system = {0: {"name": "root", "nodesId": sorted([i for i in range(len(nodes))])}} 
    return reconstruct_graph(nodes, edges, system)

def optimize_struct(struct, p_min=0.25):
    nodes, edges, _, _ = flatten_graph(struct)
    faultInd, faultName, faultLoc = zip(*[[nodeId, node["text"]["value"], (node["SubsystemId"], node["NodeId"])] for nodeId, node in enumerate(nodes) if node["type"] in FAULTTYPE])
    testInd, testName, testLoc = zip(*[[nodeId, node["text"]["value"], (node["SubsystemId"], node["NodeId"])] for nodeId, node in enumerate(nodes) if node["type"] in TESTTYPE])
    try:
        ConnInd, ConnName, ConnLoc = zip(*[[nodeId, node["text"]["value"], (node["SubsystemId"], node["NodeId"])] for nodeId, node in enumerate(nodes) if node["type"] in INPUT_NODE + OUTPUT_NODE])
    except:
        ConnInd, ConnName, ConnLoc = [], [], []
    ConnIds = [faultInd.index(ind) for ind in ConnInd]

    faultMap = [[faultInd.index(srcId), faultInd.index(trgId)] for srcId, edge in enumerate(edges) for trgId, edgeP in edge.items() if trgId in faultInd if edgeP > p_min]
    testMap = [[faultInd.index(srcId), testInd.index(trgId)] for srcId, edge in enumerate(edges) for trgId, edgeP in edge.items() if trgId in testInd if edgeP > p_min]

    inner_forward_map = {}
    for xid_, yid_ in faultMap:
        if yid_ in inner_forward_map.keys():
            inner_forward_map[yid_].add(xid_)
        else:
            inner_forward_map[yid_] = {xid_}
    for _ in edges:
        lin_cnt = 0
        for yid_, itm in inner_forward_map.items():
            for xid_ in set(itm):
                for x_id_new in inner_forward_map.get(xid_, set()):
                    if yid_ == x_id_new:
                        continue
                    if x_id_new in inner_forward_map[yid_]:
                        lin_cnt += 1
                    else:
                        inner_forward_map[yid_].add(x_id_new)
        if lin_cnt < 0.5:
            break
    ckpt_map = {ind: set() for ind in range(len(testInd))}
    for xid_, yid_ in testMap:
        ckpt_map[yid_] |= {xid_}
        ckpt_map[yid_] |= inner_forward_map.get(xid_, set())
    ckptinds = sorted(ckpt_map.keys(), key=lambda itm: len(ckpt_map[itm]))
    for ckptsortid, ckptind in enumerate(ckptinds):
        cons = -1; inner_forward_map_ = set(ckpt_map[ckptind])
        for ckptinnerid in ckptinds[:ckptsortid]:
            if len(ckpt_map[ckptind]) < len(ckpt_map[ckptinnerid]):
                break
            elif len(ckpt_map[ckptinnerid] - ckpt_map[ckptind]) > 0:
                continue
            elif len(ckpt_map[ckptinnerid] - ckpt_map[ckptind]) == 0 and \
                 len(ckpt_map[ckptind] - ckpt_map[ckptinnerid]) == 0:
                cons = ckptinnerid
                break
            inner_forward_map_ -= ckpt_map[ckptinnerid]
        if cons != -1:
            act_id, node_id = testLoc[cons]
            struct[act_id]["data"]["nodes"][node_id]["properties"]["redundancy"] = 0.1
            act_id_, node_id_ = testLoc[ckptind]
            struct[act_id_]["data"]["nodes"][node_id_]["properties"]["redundancy"] = 0.5
        elif len(inner_forward_map_) == 0:
            act_id, node_id = testLoc[ckptind]
            struct[act_id]["data"]["nodes"][node_id]["properties"]["redundancy"] = 1
        else:
            act_id, node_id = testLoc[ckptind]
            struct[act_id]["data"]["nodes"][node_id]["properties"]["redundancy"] = 0
    return struct

if __name__ == "__main__":
    struct = convert_fta(r"pic.vsdx")
    with open("data.json", "w+", encoding="utf-8") as f:
        json.dump({
        "currentSystemId": 1,
        "SystemData": struct},
                  f, indent=4, ensure_ascii=False)
    nodes, edges, system, planConfig = flatten_graph(struct)
    D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, testName, faultName, sysNames, ConnIds, ANDIds, testLoc, faultLoc, sysmap, collision_node, faultConfig = to_D_mat(nodes, edges, system)
    p_test = (np.random.uniform(0,1, len(testName))>0.5).astype("float32")
    p_fault, p_fuzzy, sysres = detect_by_D_mat(p_test, D_mat, D_without_and_mat, F_mat, fault_and_couple_mat, None, sysmap, ConnIds, ANDIds)
    print("D_mat:", D_mat)
    print("P_FAULT:", p_fault.tolist(), "\tP_FUZZY:", p_fuzzy.tolist())
    structNew = detect_with_render(p_test, D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, struct, testLoc, faultLoc, sysNames, sysmap, ConnIds, ANDIds, eps=1e-10, n_round=5)
    structJson = to_json(D_mat, D_without_and_mat, C_mat, fault_and_couple_mat, struct, testLoc, faultLoc, sysmap, testName, faultName, sysNames, collision_node, ConnIds)
    checkRes = check_graph(structJson)
    print(checkRes["detect_isolat_ratio"])
    D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, struct, testLoc, faultLoc, sysmap, testName, faultName, sysNames, collision_node, ConnIds, ANDIds = from_json(structJson)
    import pandas as pd
    print(pd.DataFrame(D_mat.A, index=faultName, columns=testName))
