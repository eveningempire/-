import numpy as np

def _render_tree(tree, nodes, x=0, y=0, width=200, height=24, padding=10, convert_map=set()):
    if tree["nid"] in convert_map:
        return nodes, convert_map
    if len(tree["branches"]) == 0:
        nodes[tree["nid"]]["x"] = x
        nodes[tree["nid"]]["y"] = y
        convert_map.add(tree["nid"])
    else:
        branch_all = [bran["num"] for bran in tree["branches"]]
        area_height = sum(branch_all)*(height+padding)
        y_dev = area_height/2
        nodes[tree["nid"]]["x"] = x
        nodes[tree["nid"]]["y"] = y + y_dev
        convert_map.add(tree["nid"])
        for brannum, braninfo, branoffset in zip(branch_all, tree["branches"], np.cumsum([0]+branch_all)[:-1]):
            nodes, _ = _render_tree(braninfo, nodes,
                                              x=x+round(width*1.5)+padding*round(1.25*width/height),
                                              y=y+(branoffset+brannum/2)*(height+padding),
                                              width=width, height=height, padding=padding,
                                              convert_map=set(convert_map))
    return nodes, convert_map

def _get_tree(nodeConn, root_id, convert_map=set()):
    if not root_id in nodeConn.keys():
        convert_map.add(root_id)
        return 1, {"nid": root_id, "branches": [], "num": 1}, convert_map
    else:
        nums = 0
        branches = []
        convert_map.add(root_id)
        for ind in nodeConn[root_id]:
            if not ind in convert_map:
                _num, _branch, convert_map = _get_tree(nodeConn, ind, convert_map=convert_map)
                branches.append(_branch)
                nums += _num
        return max(nums, 1), {
            "nid": root_id,
            "branches": branches,
            "num": max(nums, 1)
            }, convert_map
        
def render_node_pos(nodes, edges, width=5, height=3, padding=1,
                    srcKey="source", trgKey="target", idKey="id"):
    nodeConn = {}
    nodeDict = {node[idKey]: node_ind for node_ind, node in enumerate(nodes)}
    for edge in edges:
        if not nodeDict[edge[trgKey]] in nodeConn.keys():
            nodeConn[nodeDict[edge[trgKey]]] = [nodeDict[edge[srcKey]]]
        else:
            nodeConn[nodeDict[edge[trgKey]]].append(nodeDict[edge[srcKey]])
    root_id = list(set(range(len(nodes))) - {node_ind for node_edge in nodeConn.values() for node_ind in node_edge})
    if len(root_id) > 1:
        _root_id = len(nodes)
        nodeConn[_root_id] = root_id
        nodes.append({idKey: "fakeroot"})
        root_id = _root_id
    else:
        root_id = root_id[0]
    _, struct, _ = _get_tree(nodeConn, root_id, convert_map=set())
    nodes, _ = _render_tree(struct, nodes, x=0, y=0, width=width, height=height, padding=padding, convert_map=set())
    nodes = [node for node in nodes if node[idKey] != "fakeroot"]
    x_max = max([node["x"] for node in nodes if "x" in node.keys()])
    nodes = [{**node, "x": padding*1.5 + (node["x"] - x_max)} for node in nodes]
    return nodes

if __name__ == "__main__":
    input_ = {
        'nodes': [
            {'id': 'd3a845f5-2d85-53a1-9fc1-18e87c5a7043', 'name': '故障A', 'class': '故障'},
            {'id': 'a6fdcc90-16b2-58e6-99d6-a87114aa80fb', 'name': '故障A', 'class': '故障'},
            {'id': 'a6fdcc90-16b2-58e6-99d6-a87114aa80fb', 'name': '故障A', 'class': '故障'},
            {'id': '17fd7cda-6285-515d-827d-084bedd293bd', 'name': '测点1', 'class': '测点'},
            {'id': 'b559f5df-3c87-5a32-b8df-60251b619404', 'name': '测点2', 'class': '测点'},
            {'id': '6d459e32-2df7-566f-ad29-738427a76177', 'name': '测点3', 'class': '测点'},
            {'id': '57feeb4f-cf1a-5784-8150-eee17c4b8443', 'name': '', 'class': 'OR'},
            {'id': '57feeb4f-cf1a-5784-8150-eee17c4b8443', 'name': '', 'class': 'OR'},
            {'id': '57feeb4f-cf1a-5784-8150-eee17c4b8443', 'name': '', 'class': 'OR'}
            ],
        'edges': [
            {'source': 'a6fdcc90-16b2-58e6-99d6-a87114aa80fb', 'target': '57feeb4f-cf1a-5784-8150-eee17c4b8443'},
            {'source': 'a6fdcc90-16b2-58e6-99d6-a87114aa80fb', 'target': '57feeb4f-cf1a-5784-8150-eee17c4b8443'},
            {'source': '17fd7cda-6285-515d-827d-084bedd293bd', 'target': '57feeb4f-cf1a-5784-8150-eee17c4b8443'},
            {'source': 'b559f5df-3c87-5a32-b8df-60251b619404', 'target': '57feeb4f-cf1a-5784-8150-eee17c4b8443'},
            {'source': 'b559f5df-3c87-5a32-b8df-60251b619404', 'target': '57feeb4f-cf1a-5784-8150-eee17c4b8443'},
            {'source': '6d459e32-2df7-566f-ad29-738427a76177', 'target': '57feeb4f-cf1a-5784-8150-eee17c4b8443'},
            {'source': '57feeb4f-cf1a-5784-8150-eee17c4b8443', 'target': 'd3a845f5-2d85-53a1-9fc1-18e87c5a7043'},
            {'source': '57feeb4f-cf1a-5784-8150-eee17c4b8443', 'target': 'a6fdcc90-16b2-58e6-99d6-a87114aa80fb'},
            {'source': '57feeb4f-cf1a-5784-8150-eee17c4b8443', 'target': 'a6fdcc90-16b2-58e6-99d6-a87114aa80fb'}
            ]
        }
    output_ = render_node_pos(input_["nodes"], input_["edges"])
    print(output_)
