import os, time, uuid, math
import aspose.diagram
from aspose.diagram import Diagram, SaveFileFormat, License
# pip install aspose-diagram-python
if os.path.exists("visio_gui_utils"):
    from visio_gui_utils import render_node_pos
else:
    from .visio_gui_utils import render_node_pos
from zipfile import ZipFile
from io import BytesIO

LIC = License()
# LIC.set_license(r".\license.lic")

IDKEY = "id"
NAMEKEY = "text"
CLASSKEY = "type"
SRCKEY = "from"
TRGKEY = "to"

def get_uuid(kw=""):
    "生成ID"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{kw}#%.7f"%time.time()))

def _getType(node, return_mode=False):
    "读取类型"
    try:
        if return_mode:
            return node.props[0].value.val, "props"
        return node.props[0].value.val
    except Exception as e:
        if return_mode:
            return node.name_u.split(".")[0], "name"
        return node.name_u.split(".")[0]

def _createConfigQueryMap(config_path):
    """为读取构建所有的类型查表"""
    with Diagram(config_path) as diagram:
        typeConfig = {}
        for node in diagram.pages[0].shapes:
            typeName = node.get_display_text().replace("\n", "").replace("\r","")
            type_raw = _getType(node)
            if not ("连接线" in type_raw or "connector" in type_raw.lower()):
                typeConfig[type_raw] = typeName
    return typeConfig

def parse_docx_visio(path, config_path):
    """从doc/docx对应的path/ByteIO中读取所有visio嵌入的流图"""
    figures = {"nodes": [], "edges": []}
    with ZipFile(path, "r") as zipf:
        for entry in zipf.infolist():
            if entry.filename.lower().startswith('word/embeddings') and \
               (entry.filename.lower().endswith('.vsd') or \
                entry.filename.lower().endswith('.vsdx')):
                with BytesIO() as bf:
                    bf.write(zipf.read(entry.filename))
                    bf.seek(0)
                    struct = parse_visio(bf, config_path)
                    figures["nodes"].extend(struct.get("nodes", []))
                    figures["edges"].extend(struct.get("edges", []))
    return figures

def _wash_or_node(edge, trgRootId, or_source_map, check_map=set()):
    edges = []
    for trgid in or_source_map[trgRootId]:
        if trgid in or_source_map.keys():
            if trgid in check_map:
                continue
            edges.extend(_wash_or_node(edge, trgid, or_source_map, check_map|{trgRootId, trgid}))
        else:
            edges.append({**edge, TRGKEY: trgid})
    return edges

def faultTree2msfd(struct):
    or_node = [node[IDKEY] for node in struct["nodes"] if node[CLASSKEY].lower() == "or"]
    nodes = [node for node in struct["nodes"] if node[CLASSKEY].lower() != "or"]
    or_source_map = {}
    for edge in struct["edges"]:
        if edge[SRCKEY] in or_node:
            if not edge[SRCKEY] in or_source_map.keys():
                or_source_map[edge[SRCKEY]] = [edge[TRGKEY]]
            else:
                or_source_map[edge[SRCKEY]].append(edge[TRGKEY])
    edges = []
    for edge in struct["edges"]:
        if edge[TRGKEY] in or_source_map.keys():
            edges.extend(_wash_or_node(edge, edge[TRGKEY], or_source_map))
        elif not edge[SRCKEY] in or_node:
            edges.append(edge)
    return {"nodes": nodes, "edges": edges}

def parse_visio(path, config_path):
    """从visio对应的path/ByteIO中读取单幅流图"""
    typeConfig = _createConfigQueryMap(config_path)
    with Diagram(path) as diagram:
        result = {"nodes": [], "edges": []}
        for node in diagram.pages[0].shapes:
            type_raw =  _getType(node)
            if type_raw in typeConfig.keys():
                type_ = typeConfig[type_raw]
                result["nodes"].append({
                    "text": node.get_display_text().replace("\n", "").replace("\r",""),
                    "type": type_,
                    "id": node.id,
                } ) 
            elif "连接线" in type_raw or "connector" in type_raw.lower():
                edge = node.get_connector_rule()
                result["edges"].append({
                    "from_id": edge.start_shape_id,
                    "to_id":edge.end_shape_id,
                } )
    nodeMap = {node["id"]: {
        IDKEY: get_uuid(f"{node['text']}#{nodeId}"),
        NAMEKEY: node["text"],
        CLASSKEY: node["type"]
        } for nodeId, node in enumerate(result["nodes"])}
    return {"nodes": list(nodeMap.values()),
            "edges": [{SRCKEY: nodeMap[edge["from_id"]][IDKEY],
                       "from_text": nodeMap[edge["from_id"]][NAMEKEY],
                       "to_text": nodeMap[edge["to_id"]][NAMEKEY],
                       TRGKEY: nodeMap[edge["to_id"]][IDKEY]} for edge in result["edges"]
                      if edge["from_id"] in nodeMap.keys() and edge["to_id"] in nodeMap.keys()]}

#################################################################################################

def _createConfigGeneMap(config_path):
    """为绘图构建所有的类型查表"""
    with Diagram(config_path) as diagram:
        typeConfig = {}
        nodeTypeMap = {node.id: node.get_display_text().replace("\n", "").replace("\r","") for node in diagram.pages[0].shapes}
        for node in diagram.pages[0].shapes:
            typeName = node.get_display_text().replace("\n", "").replace("\r","")
            type_raw =  _getType(node)
            if "连接线" in type_raw or "connector" in type_raw.lower():
                edge = node.get_connector_rule()
                if not edge.start_shape_connection is None:
                    inName = nodeTypeMap[edge.start_shape_id]
                    if inName in typeConfig.keys():
                        typeConfig[inName][1].append([int(typeName), edge.start_shape_connection.ix])
                    else:
                        typeConfig[inName] = [None, [[int(typeName), edge.start_shape_connection.ix]], []]
                if not edge.end_shape_connection is None:
                    inName = nodeTypeMap[edge.end_shape_id]
                    if inName in typeConfig.keys():
                        typeConfig[inName][2].append([int(typeName), edge.end_shape_connection.ix])
                    else:
                        typeConfig[inName] = [None, [], [[int(typeName), edge.end_shape_connection.ix]]]
                if typeName == "线" or not "线" in typeConfig.keys():
                    typeConfig["线"] = [type_raw, node.line.end_arrow.value]
            else:
                if typeName in typeConfig.keys():
                    typeConfig[typeName][0] = type_raw
                else:
                    typeConfig[typeName] = [type_raw, [], []]
    return typeConfig

class visioGramManage:
    def __init__(self, demo_path="faultTreeDemo.vsdx",
                 roaming_path="faultTreeRoaming.vsdx",
                 config_path="faultTreeConfig.vsdx", pixelSize=0.2):
        self.d = Diagram(demo_path)
        self._demo_path = demo_path
        self._roaming_path = roaming_path
        self._pixelSize = pixelSize
        self._typConfig =  _createConfigGeneMap(config_path)
        self._typName = _createConfigQueryMap(config_path)
        self._nameMap = {}
        self._cnt = 0
        
    def add_node(self, pos, typ, name="", ref=None, angle=0):
        typName, _, _ = self._typConfig[typ]
        width = (len(name)+1)*self._pixelSize
        height = 2*self._pixelSize
        self.d.add_shape(pos[0]+width/2, pos[1]+height/2, width,
                         height, typName, 0)
        
        self.n = self.d.pages[0].shapes[self._cnt]
        self.d.pages[0].shapes[self._cnt].text.value.set_whole_text(name)
        self.d.pages[0].shapes[self._cnt].set_angle(angle/180*math.pi)
        self._nameMap[ref or f"{name}#{typ}"] = [self._cnt, self.d.pages[0].shapes[self._cnt].id,
                                                 pos[0]+width/2, pos[1]+height/2]
        self._cnt += 1
        """
        if self._cnt == 8:
            self.save(self._roaming_path, close_after=True, restart_after=False)
            self.d = Diagram(self._roaming_path)
            self._cnt += 1
        """

    def add_edge(self, start_name, end_name):
        # start_name/end_name = ref OR f"{name}#{typ}"
        typName, arrowType = self._typConfig["线"]
        if start_name in self._nameMap.keys() and end_name in self._nameMap.keys():
            start_cnt, start_id, start_x, start_y  = self._nameMap[start_name]
            end_cnt, end_id, end_x, end_y  = self._nameMap[end_name]
            # print(self.d.pages[0].shapes[start_cnt].get_display_text() or "OR", "->",
            #       self.d.pages[0].shapes[end_cnt].get_display_text() or "OR")
            start_type = self._typName[_getType(self.d.pages[0].shapes[start_cnt])]
            end_type = self._typName[_getType(self.d.pages[0].shapes[end_cnt])]
            _, startConnConfig, _ = self._typConfig[start_type]
            startConnConfig = [itm[1] for itm in sorted(startConnConfig, key=lambda itm: itm[0])]
            _, _, endConnConfig = self._typConfig[end_type]
            endConnConfig = [itm[1] for itm in sorted(endConnConfig, key=lambda itm: itm[0])]
            
            self.d.add_shape(0, 0, 20, 20, typName, 0)
            if start_y < end_y:
                self.d.pages[0].connect_shapes_via_connector_index(start_id, startConnConfig[0],
                                                                   end_id, endConnConfig[-1],
                                                                   self.d.pages[0].shapes[self._cnt].id)
            else:
                self.d.pages[0].connect_shapes_via_connector_index(start_id, startConnConfig[-1],
                                                                   end_id, endConnConfig[0],
                                                                   self.d.pages[0].shapes[self._cnt].id)
            self.d.pages[0].shapes[self._cnt].line.end_arrow.value = arrowType
            
            self._cnt += 1
            """
            if self._cnt == 8:
                self.save(self._roaming_path, close_after=True, restart_after=False)
                self.d = Diagram(self._roaming_path)
                self._cnt += 1
            """

    def save(self, export_path, close_after=True, restart_after=False):
        self.d.save(export_path, SaveFileFormat.VSDX)
        if close_after or restart_after:
            self.d.__exit__()
            if restart_after:
                self.d = Diagram(self._demo_path)
                self._cnt = 0
                self._nameMap = {}

def drawStruct(struct, path, demo_path="faultTreeDemo.vsdx",
               config_path="faultTreeConfig.vsdx",
               pixelSize=0.2, width=1, height=1, padding=0.2):
    nodes = struct.get("nodes", []); edges = struct.get("edges", [])
    nodes = render_node_pos(nodes, edges,
                            width=width, height=height, padding=padding,
                            srcKey=SRCKEY, trgKey=TRGKEY, idKey=IDKEY)
    v = visioGramManage(demo_path=demo_path, config_path=config_path,
                        pixelSize=pixelSize)
    for node in nodes:
        v.add_node([node['x'],node['y']],
                   node[CLASSKEY],node[NAMEKEY],node[IDKEY])
    for edge in edges:
        v.add_edge(edge[SRCKEY],edge[TRGKEY]) 
    v.save(path)

def msfd2faultTree(struct):
    return struct

if __name__ == "__main__":
    #result = parse_visio(r"pic.vsd")#r"pic.vsdx"
    res = parse_docx_visio("pic.docx", "faultTreeConfig.vsdx")
    res_msfd = faultTree2msfd(res)
    drawStruct(res_msfd, "1.vsdx")
