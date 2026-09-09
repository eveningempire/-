import json
from flask import Blueprint, render_template, request, jsonify
from app import redis_engine
from lib.flaskModule.msfgModule import utils as msfg_util
from typing import Dict

# 创建蓝图
msfg_bp = Blueprint('msfg', __name__)

@msfg_bp.route('/multi-info-edit', methods=['GET', 'POST'])
def msfg_init():
    return render_template('msfg-edit.html')

@msfg_bp.route('/multi-info-edit/init-graph/', methods=['GET', 'POST'])
def msfg_init_graph():
    res = json.loads(redis_engine.hget('cmg', "msfg-raw-config") or "[]")
    return jsonify(res)

@msfg_bp.route('/multi-info-edit/init-graph1/', methods=['GET', 'POST'])
def msfg_init_graph1():
    res = json.loads(redis_engine.hget('cmg', "msfg-raw-config") or "[]")
    return jsonify(res)


@msfg_bp.route('/multi-info-edit/config-graph/', methods=['GET', 'POST'])
def msfg_config_graph():
    graphData = request.form.get("graphData")
    redis_engine.hset('cmg', "msfg-raw-config", graphData)
    struct = json.loads(graphData)
    if isinstance(struct, Dict):
        struct = struct["SystemData"]
    D_mat, testName, faultName, ConnIds, testLoc, faultLoc, sysmap, collision_node, faultConfig = msfg_util.to_D_mat(
        *msfg_util.flatten_graph(struct),
        eps=1e-15, raise_collision=False)

    pnames = testName
    components = extract_component_names(struct) 
    redis_engine.hset('cmg', 'pnames', json.dumps(pnames))
    redis_engine.hset('cmg', 'components', json.dumps(components))
    
    redis_engine.hset('cmg', "fault-name-config", json.dumps(
        {infon: {
            **info, "component": info.get("component", "")}
         for infon, info in faultConfig.items()}))
    return jsonify(None)

def extract_component_names(data):
    components = []
    for i in range(len(data)):
        components.append(data[i]['name'])
    return components

def extract_test_node_names(data):
    """
    Extracts all 'name' values from nodes where 'types' is 'test-node'.

    Parameters:
    - data (dict): The nested dictionary to search.

    Returns:
    - list: A list of 'name' values from nodes where 'types' is 'test-node'.
    """
    result = []

    def recursive_search(node):
        if isinstance(node, dict):
            # Check if 'types' is 'test-node' and add 'name' to result if it exists
            if node.get('types') == 'test-node' and 'name' in node:
                result.append(node['name'])
            
            if 'child' in node and isinstance(node['child'], list):
                for child in node['child']:
                    recursive_search(child)
        elif isinstance(node, list):
            # If the current node is a list, iterate through its elements
            for item in node:
                recursive_search(item)

    # Start the recursive search from the root node
    recursive_search(data)
    return result
