import json
import numpy as np
from typing import Dict
from flask import request, send_file
from io import BytesIO
from .utils import convert_fmeca, flatten_graph, convert_fta, to_D_mat, \
     detect_with_render, to_json, check_graph, optimize_struct, draw_fta
from .parseDoc import read_table
from .msfd2fmeca import msfd2fmeca

EPS = 1e-9
DEFAULT_P = 0.2

def upload_fmeca():
    graphStruct = read_table(request.files.get("modelFile"), header=0)
    struct = convert_fmeca(graphStruct)
    return json.dumps({
        "currentSystemId": 1,
        "SystemData": struct
        }).replace("NaN", "null")
    
def download_fmeca():
    obj = request.form.get("obj") or "产品"
    graphStruct = json.loads(request.form.get("graphStruct"))
    if isinstance(graphStruct, Dict):
        graphStruct = graphStruct["SystemData"]
    nodes, edges, system, _ = flatten_graph(graphStruct, only_mode=True)
    io_ = BytesIO()
    msfd2fmeca(nodes, edges, system).save(io_)
    io_.seek(0)
    return send_file(io_, as_attachment=True, download_name=f"{obj}_FMECA表.xlsx")
    
def upload_fta():
    struct = convert_fta(request.files.get("modelFile"))
    return json.dumps({
        "currentSystemId": 1,
        "SystemData": struct
        }).replace("NaN", "null")
    
def download_fta():
    obj = request.form.get("obj") or "产品"
    graphStruct = json.loads(request.form.get("graphStruct"))
    if isinstance(graphStruct, Dict):
        graphStruct = graphStruct["SystemData"]
    nodes, edges, _, _ = flatten_graph(graphStruct, only_mode=True)
    io_ = BytesIO()
    draw_fta({"nodes": nodes, "edges": edges}, io_)
    io_.seek(0)
    return send_file(io_, as_attachment=True, download_name=f"{obj}_故障树.pptx")

def optimize_graph():
    graphStruct = json.loads(request.form.get("graphStruct"))
    if isinstance(graphStruct, Dict):
        graphStruct = graphStruct["SystemData"]
    struct = optimize_struct(graphStruct)
    return json.dumps({
        "data": struct
        }).replace("NaN", "null")

def service_to_D_mat():
    struct = json.loads(request.form.get("graphStruct"))
    if isinstance(struct, Dict):
        struct = struct["SystemData"]
    nodes, edges, system, _ = flatten_graph(struct)
    D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, testName, faultName, sysNames, ConnIds, ANDIds, testLoc, faultLoc, sysmap, collision_node, _ = to_D_mat(nodes, edges, system, eps=EPS, raise_collision=False)
    return to_json(D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, struct, testLoc, faultLoc, sysmap, testName, faultName, sysNames, collision_node, ConnIds, ANDIds)

def app_check_graph():
    struct = json.loads(request.form.get("graphStruct"))
    if isinstance(struct, Dict):
        struct = struct["SystemData"]
    nodes, edges, system, _ = flatten_graph(struct)
    with open("result.json", "w+", encoding="utf-8") as f:
        json.dump({"nodes": nodes, "edges": edges, "system": system}, f, indent=4, ensure_ascii=False)
    D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, testName, faultName, sysNames, ConnIds, ANDIds, testLoc, faultLoc, sysmap, collision_node, _ = to_D_mat(nodes, edges, system, eps=EPS, raise_collision=False)
    #print(D_mat)
    structJson = to_json(D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, struct, testLoc, faultLoc, sysmap, testName, faultName, sysNames, collision_node, ConnIds, ANDIds)
    #structJson = request.form.get("convertedStruct")
    info = check_graph(structJson, eps=EPS)
    return json.dumps(info).replace("NaN", "null")

def _fuse_p(testPs, defaultP=0.2):
    if len(testPs) == 0:
        return defaultP
    elif len(testPs) <= 2:
        return np.mean(testPs)
    else:
        testPs = np.array(testPs, dtype="float32")
        testPw = np.abs(testPs - np.median(testPs))
        testPwExp = np.exp(-testPw/testPw.max())
        testPw = testPwExp/testPwExp.sum()
        return sum(testPs*testPw)

def _washItm(testName, values, defaultP=0.2):
    testValues = {testN: [] for testN in testName}
    for ckptn, p in values:
        if ckptn in testValues.keys():
            testValues[ckptn].append(p)
    return np.array([_fuse_p(testValues[testN], defaultP=defaultP) for testN in testName], dtype="float32")

def result_analyse_main():
    struct = json.loads(request.form.get("graphStruct"))
    if isinstance(struct, Dict):
        struct = struct["SystemData"]
    nodes, edges, system, _ = flatten_graph(struct)
    D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, testName, msfgFaultNames, _, ConnIds, ANDIds, testLoc, faultLoc, sysmap, _, _ = to_D_mat(nodes, edges, system, eps=EPS, raise_collision=False)
    p_test = _washItm(
        testName,
        [[itm["text"], itm["state"]] for itm in read_table(request.files.get("dataFile"), header=0).T.to_dict().values()],
        defaultP=DEFAULT_P)
    struct = detect_with_render(p_test, D_mat, D_without_and_mat, C_mat, F_mat, fault_and_couple_mat, struct, testLoc, faultLoc, msfgFaultNames, sysmap, ConnIds, ANDIds)
    return json.dumps({
        "data": struct
        }).replace("NaN", "null")

def msfg_route_app(app):
    app.route("/multi-info-edit/upload-fmeca/",methods=['POST'])(upload_fmeca)
    app.route("/multi-info-edit/upload-fta/",methods=['POST'])(upload_fta)
    app.route("/multi-info-edit/optimize-graph/",methods=['POST'])(optimize_graph)
    app.route("/multi-info-edit/check-graph/",methods=['POST'])(app_check_graph)
    app.route("/multi-info-edit/convert-graph/",methods=['POST'])(service_to_D_mat)
    app.route("/multi-info-analyse/analyse-data/",methods=['POST'])(result_analyse_main)
    app.route("/multi-info-analyse/download-fta/",methods=['POST'])(download_fta)
    app.route("/multi-info-analyse/download-fmeca/",methods=['POST'])(download_fmeca)
