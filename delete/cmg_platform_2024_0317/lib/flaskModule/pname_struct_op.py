import json

def _branch_uncollapse(branch, father_id, max_=20, delta_id=1): #
    children_ = json.loads(branch['stock'])
    branch["id"] = father_id+delta_id
    branch["stock"] = ""
    branch["collapsed"] = False
    branch["cssAsBlock"] = branch['cssAsBlock']
    branch["inputs"] = [father_id]
    branch["outputs"] = []
    branch["children"] = children_
    return _dealTree(branch, start_id=father_id, delta_id=delta_id, max_=max_+father_id)

def _branch_collapse(branch, father_id, delta_id=1):
    branch["id"] = father_id+delta_id
    branch["stock"] = json.dumps(branch['children'])
    branch["collapsed"] = True
    branch["cssAsBlock"] = branch['cssAsBlock']
    branch["inputs"] = [father_id]
    branch["outputs"] = []
    branch["children"] = []
    return 1, branch
    
def _dealTree(tree, start_id=1, max_=20, delta_id=1):
    if tree["collapsed"] and tree["children"] and not tree["stock"]:
        return _branch_collapse(tree, start_id, delta_id=delta_id)
    elif not tree["collapsed"] and not tree["children"] and tree["stock"]:
        return _branch_uncollapse(tree, start_id, delta_id=delta_id, max_=max_)
    elif tree["children"]:
        tree["id"] = start_id+delta_id
        tree["inputs"] = [start_id]
        sums = 0
        args = []
        outputs = []
        for ind in range(len(tree["children"])):
            sums_, arg =  _dealTree(tree["children"][ind], start_id=start_id+delta_id, max_=max_, delta_id=sums+1)
            args.append(arg)
            outputs.append(arg["id"])
            sums += sums_
        tree["children"] = args
        tree["outputs"] = outputs
        return sums+1, tree
    else:
        tree["inputs"] = [start_id]
        tree["id"] = start_id+delta_id
        return 1, tree

def dealTree(tree, max_=20):
    return _dealTree(tree, start_id=0, max_=max_)[1]

def initialTree(tree, sysName="系统", max_=20):
    res = {}; aideList = []; idMax = 1
    for pname, pInfo in tree.items():
        idMax += 1
        pSys, pComp = pInfo
        if pSys in res.keys():
            if pname[:22] == "||<-EL-PSY-CONGROO->||":
                res[pSys]["_count"] += 1
                res[pSys][pComp] = {
                    "_ord": res[pSys]["_count"],
                    "_id": idMax
                    }
                aideList[res[pSys]["_ord"]]["children"].append(
                    {
                        "id": idMax,
                        "cssAsBlock": "componentBlock",
                        "inputs": [res[pSys]["_id"]],
                        "outputs": [],
                        "text": pComp,
                        "collapsed": True,
                        "stock": "",
                        "children": []
                        })
                aideList[res[pSys]["_ord"]]["outputs"].append(idMax)
            elif pComp in res[pSys].keys():
                aideList[res[pSys]["_ord"]]["children"][res[pSys][pComp]["_ord"]]["children"].append(
                        {
                            "id": idMax,
                            "cssAsBlock": "paraBlock",
                            "inputs": [res[pSys][pComp]["_id"]],
                            "outputs": [],
                            "text": pname,
                            "collapsed": False,
                            "stock": "",
                            "children": []
                            }
                    )
                aideList[res[pSys]["_ord"]]["children"][res[pSys][pComp]["_ord"]]["outputs"].append(idMax)
            else:
               res[pSys]["_count"] += 1
               res[pSys][pComp] = {
                   "_ord": res[pSys]["_count"],
                   "_id": idMax
                   }
               aideList[res[pSys]["_ord"]]["children"].append(
                   {
                        "id": idMax,
                        "cssAsBlock": "componentBlock",
                        "inputs": [res[pSys]["_id"]],
                        "outputs": [idMax+1],
                        "text": pComp,
                        "collapsed": True,
                        "stock": "",
                        "children": [
                            {
                                "id": idMax+1,
                                "cssAsBlock": "paraBlock",
                                "inputs": [idMax],
                                "outputs": [],
                                "text": pname,
                                "collapsed": False,
                                "stock": "",
                                "children": []
                                }
                        ]
                    })
               aideList[res[pSys]["_ord"]]["outputs"].append(idMax)
               idMax += 1
        elif pComp == "||<-EL-PSY-CONGROO->||":
            aideList.append({
                "id": idMax,
                "cssAsBlock": "subsystemBlock",
                "inputs": [1],
                "outputs": [],
                "text": pSys,
                "collapsed": False,
                "stock": "",
                "children": []
            })
        elif pname[:22] == "||<-EL-PSY-CONGROO->||":
            res[pSys] = {
                "_count": 0,
                "_id": idMax,
                "_ord": len(res.keys()),
                pComp:{
                    "_ord": 0,
                    "_id": idMax + 1
                   }
            }
            aideList.append({
                "id": idMax,
                "cssAsBlock": "subsystemBlock",
                "inputs": [1],
                "outputs": [idMax+1],
                "text": pSys,
                "collapsed": False,
                "stock": "",
                "children": [{
                    "id": idMax+1,
                    "cssAsBlock": "componentBlock",
                    "inputs": [idMax],
                    "outputs": [idMax+2],
                    "text": pComp,
                    "collapsed": True,
                    "stock": "",
                    "children": []
                    }]
                })
            idMax += 1
        else:
            res[pSys] = {
                "_count": 0,
                "_id": idMax,
                "_ord": len(res.keys()),
                pComp:{
                    "_ord": 0,
                    "_id": idMax + 1
                   }
            }
            aideList.append({
                "id": idMax,
                "cssAsBlock": "subsystemBlock",
                "inputs": [1],
                "outputs": [idMax+1],
                "text": pSys,
                "collapsed": False,
                "stock": "",
                "children": [{
                    "id": idMax+1,
                    "cssAsBlock": "componentBlock",
                    "inputs": [idMax],
                    "outputs": [idMax+2],
                    "text": pComp,
                    "collapsed": True,
                    "stock": "",
                    "children": [
                        {
                            "id": idMax+2,
                            "cssAsBlock": "paraBlock",
                            "inputs": [idMax+1],
                            "outputs": [],
                            "text": pname,
                            "collapsed": False,
                            "stock": "",
                            "children": []
                            }
                        ]
                    }]
                })
            idMax += 2
    result = {
        "id": 1,
        "cssAsBlock": "systemBlock",
        "inputs": [],
        "outputs": [sys["id"] for sys in aideList],
        "text": sysName,
        "collapsed": False,
        "stock": "",
        "children": aideList
        }
    return dealTree(result)

def convert_tree_to_dict(tree, current_path=[]):
    result={}
    if tree["stock"]:
        tree = _branch_uncollapse(tree, 1)
    for child in tree["children"]:
        new_path = current_path + [tree['text']]
        if child["children"] != []:
            result.update(convert_tree_to_dict(child, new_path))
        else:  # 如果是叶子节点
            result[child['text']] = new_path
    return result

def convert_dict_to_tree(data):
    index = 0 
    def insert_path(tree,leaf, path):
        """
        将路径插入到嵌套的字典中。
        
        :param tree: 当前的树状字典。
        :param path: 需要插入的路径列表。
        """
        current = tree
        nonlocal index
        for node in path[1:]: 
            found = False
            for child in current:
                if child == []: continue
                if child['text'] == node:
                    current = child['child']
                    found = True
                    break
            if not found:
                new_node = {'text': node, 'child': [],'id':index}
                index=index+1
                current.append(new_node)
                current = new_node['child']
        # 最后一个节点是叶子节点
        current.append({'text': leaf,'id':index,'child': []})
        index = index + 1
    for leaf, path in data.items():
        root = data[leaf][0]
        break 
    nested_dict = {'text': root,'id':index,'child': []}
    index = index + 1
    for leaf, path in data.items():
        insert_path(nested_dict['child'], leaf,path)
    
    return nested_dict
    

def getAllPara(tree, paraList=None):
    if paraList == None:
        paraList = []
    if tree['cssAsBlock'] == 'paraBlock':
        paraList.append(tree['text'])
    for child in tree['children']: 
        if child !=[]:
            paraList = getAllPara(child,paraList)
    return paraList
def getAllComponents(tree, components=None):
    if components == None:
        components = []
    if tree['cssAsBlock'] == 'componentBlock':
        components.append(tree['text'])
    for child in tree['children']: 
        if child !=[]:
            components = getAllComponents(child,components)
    return components

def configTree(tree):
    res = {}; msg=[]; syscons = True; count = 0
    if tree["stock"]:
        tree = _branch_uncollapse(tree, 1)
    # for subsysInfo in tree["children"]:
    #     subsys = (subsysInfo["text"] or "").replace(" ","")
    #     compcons = True
    #     for compInfo in subsysInfo["children"]:
    #         if compInfo["stock"]:
    #             compInfo = _branch_uncollapse(compInfo, 1)[1]
    #         comp = (compInfo["text"] or "").replace(" ","")
    #         for pInfo in compInfo["children"]:
    #             pn = (pInfo["text"] or "").replace(" ","")
    #             if not subsys:
    #                 msg.append(f"{len(msg)+1}. 参数<{pn if pn else 'unnamed'}>所在分系统未命名")
    #             if not comp:
    #                 msg.append(f"{len(msg)+1}. 参数<{pn if pn else 'unnamed'}>所在部件未命名")
    #             if not pn:
    #                 msg.append(f"{len(msg)+1}. 存在参数未命名")
    #             elif pn in res.keys():
    #                 msg.append(f"{len(msg)+1}. 参数<{pn}>命名重复")
    #             else:
    #                 res[pn] = [subsys, comp]
    #                 syscons = False
    #                 compcons = False
    #     if comp and compcons:
    #         res[f"||<-EL-PSY-CONGROO->||{count}"] = [subsys, comp]
    #         count += 1
    #         syscons = False
    # if subsys and syscons:
    #     res[f"||<-EL-PSY-CONGROO->||{count}"] = [subsys, "||<-EL-PSY-CONGROO->||"]
    #     count += 1
                
    return "；<br/>".join(msg), res

if __name__=="__main__":
    res = initialTree({
            "pname001":["comp001", "sub001"],
            "pname002":["comp001", "sub001"],
            "pname003":["comp002", "sub002"],
            "pname004":["comp003", "sub002"]
        })
