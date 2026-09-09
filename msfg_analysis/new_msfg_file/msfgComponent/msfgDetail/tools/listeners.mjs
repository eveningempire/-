/**
 * 添加事件监听参考 http://logic-flow.org/guide/basic/event.html
 * LogicFlow 提供的事件参考 http://logic-flow.org/api/eventCenterApi.html
 * 也可以监听基于 LogicFlow eventCenter 抛出的自定义事件，如何抛出自定义事件参考 http://logic-flow.org/api/graphModelApi.html#eventcenter
 */
function deepDelete(sys, inds){
  for (let ind of inds){
    let current_system_ind = sys.map(itm=>itm.system_id).indexOf(ind);
    if (current_system_ind !== -1){
      let current_system = sys.splice(current_system_ind, 1)[0]
      let toDeleteSysInds = current_system.data.nodes.filter(itm=> itm.type=="sub-system").map(itm=>itm.properties.SubsystemId)
      if (toDeleteSysInds.length > 0){
        sys = deepDelete(sys, toDeleteSysInds);
      }
    }
  }
  return sys
}

const listeners = {
  $_LfEvent () {
    // 单击节点 测试用
    /**this.lf.on('node:click', ({ data }) => {
      console.log(data) // for test
    })
    // 单击边 测试用
    this.lf.on('edge:click', ({ data }) => {
      console.log(data) // for test

    })**/
    // 画布重新渲染记录
    this.lf.on('graph:rendered', () => {
      
      let currentSystem = this.gData.SystemData.find(item => item.system_id === this.gData.currentSystemId)
      if (currentSystem) {
        currentSystem.data = this.lf.getGraphData()
				this.module_tree =  this.getModuleTree(this.gData.SystemData)
      }
    })

    // 画布变化触发
    this.lf.on('history:change', () => {
      
      let currentSystem = this.gData.SystemData.find(item => item.system_id === this.gData.currentSystemId)
      if (currentSystem) {
        currentSystem.data = this.lf.getGraphData()
				this.module_tree =  this.getModuleTree(this.gData.SystemData)
      }
    })
    
    // 双击节点
    this.lf.on('node:dbclick', ({ data }) => {
      if (data.type == 'subsystem-node') {
        this.handleNodeClick({ id: data.properties.SubsystemId })
        this.dialogVisible = false;
      } else {

        this.formData = data
        this.dialogVisible = true
      }
    })

    // ※节点信息编辑
    this.lf.on('node:edit', (data) => {
      this.formData = data
      this.dialogVisible = true
    })

    this.lf.on('node:delete', (data) => {
      let node = data.data;
      if (node.type == "subsystem-node"){
        let systemData = deepDelete(this.gData.SystemData, [node.properties.SubsystemId])
        let currentSystemId = systemData.map(item => item.system_id).indexOf(this.gData.currentSystemId);
        let currentSystem = systemData[currentSystemId];
        currentSystem.data.nodes = currentSystem.data.nodes.filter(itm=> itm.properties.SubsystemId !== node.properties.SubsystemId)
        let nodeInds = currentSystem.data.nodes.map(itm=>itm.id)
        currentSystem.data.edges = currentSystem.data.edges.filter(itm=> (nodeInds.includes(itm.sourceNodeId) &&  nodeInds.includes(itm.targetNodeId)))
        this.gData.SystemData = systemData;
        let graphData = this.lf.getGraphData()
        graphData.nodes = currentSystem.data.nodes;
        graphData.edges = currentSystem.data.edges;
        this.lf.render(graphData)
        this.module_tree = this.getModuleTree(systemData)
      } else if(node.type === "input-node"){
        // 1. 将剩余input节点的index重新排序和命名
        let graph_data = this.lf.getGraphData()
        let input_nodes = graph_data.nodes.filter((item) => {
          return item.type === "input-node"})

        input_nodes.forEach((item, index) => {
          item.properties.index = index + 1
          item.text = item.text.value || "输入" + (index + 1)
        })
        // 2. 将父系统中的子系统组件的input属性更新

              // 根据子系统的id找到父系统
        let parent_id = this.gData.SystemData.find(item => item.system_id == this.gData.currentSystemId).parent_id
        let parent_system = this.gData.SystemData.find(item => item.system_id == parent_id)

        /// 更新parent_system的中对应子系统的input或output
        let subsystem_node = parent_system.data.nodes.find(item => item.properties.SubsystemId == this.gData.currentSystemId)
        subsystem_node.properties.fields.input = input_nodes.length
        subsystem_node.properties.fields.inputNames = input_nodes.map(itm=>itm.text)
        // 更新parent_system的中对应子系统的input或output连线的锚点数据
        // 1. 删除相关连线
        let input_anchors = subsystem_node.anchors.filter(item => item.type == "left")
        let delete_edge_index = parent_system.data.edges.findIndex(item => item.targetAnchorId == input_anchors[node.properties.index - 1].id)
        if (delete_edge_index != -1) {
          parent_system.data.edges.splice(delete_edge_index, 1)
        }
        // 2. 重排其他连线的顺序
        for (let i = node.properties.index; i < input_anchors.length; i++) {
          let edge_index = parent_system.data.edges.findIndex(item => item.targetAnchorId == input_anchors[i].id)
          if (edge_index != -1) {
            parent_system.data.edges[edge_index].targetAnchorId = input_anchors[i - 1].id
          }
        }

        // 3. 重新渲染页面
        this.lf.render(graph_data)
      } else if(node.type === "output-node"){
        // 1. 将剩余input节点的index重新排序和命名
        let graph_data = this.lf.getGraphData()
        let output_nodes = graph_data.nodes.filter((item) => {
          return item.type === "output-node"})

        output_nodes.forEach((item, index) => {
          item.properties.index = index + 1
          item.text = item.text.value || "输出" + (index + 1)
        })
        // 2. 将父系统中的子系统组件的input属性更新

        // 根据子系统的id找到父系统
        let parent_id = this.gData.SystemData.find(item => item.system_id == this.gData.currentSystemId).parent_id
        let parent_system = this.gData.SystemData.find(item => item.system_id == parent_id)

        // 更新parent_system的中对应子系统的input或output
        let subsystem_node = parent_system.data.nodes.find(item => item.properties.SubsystemId == this.gData.currentSystemId)
        subsystem_node.properties.fields.output = output_nodes.length
        subsystem_node.properties.fields.outputNames = output_nodes.map(itm=>itm.text)

        // 更新parent_system的中对应子系统的input或output连线的锚点数据
        // 1. 删除相关连线
        let output_anchors = subsystem_node.anchors.filter(item => item.type == "right")
        let delete_edge_index = parent_system.data.edges.findIndex(item => item.sourceAnchorId == output_anchors[node.properties.index - 1].id)
        if (delete_edge_index != -1) {
          parent_system.data.edges.splice(delete_edge_index, 1)
        }
        // 2. 重排其他连线的顺序
        for (let i = node.properties.index; i < output_anchors.length; i++) {
          let edge_index = parent_system.data.edges.findIndex(item => item.sourceAnchorId == output_anchors[i].id)
          if (edge_index != -1) {
            parent_system.data.edges[edge_index].sourceAnchorId = output_anchors[i - 1].id
          }
        }

        // 3. 重新渲染页面
        this.lf.render(graph_data)
      }
    })

    // 鼠标进入节点
    this.lf.on('node:mouseenter', ({ data }) => {
      let element = document.querySelector('.popper')
      if (element) { element.remove() }
      if (data.properties.showType === 'analyse' && data.type !== 'sub-system') {
        const { transformModel } = this.lf.graphModel
        const [x, y] = transformModel.CanvasPointToHtmlPoint([
          data.x,
          data.y
        ])
        let left = x + 10 + data.properties.width / 2
        let top = y - 10
        let element = document.createElement('div')
        element.className = "popper"
        element.style.left = `${left}px`
        element.style.top = `${top}px`
        element.innerHTML = `
          <p>名称: ${data.text.value}</p>
          <p>故障分数: ${Math.round(data.properties.state * 10000)/100}</p>
          <p>模糊分数: ${Math.round(data.properties.fuzzy_state * 10000)/100}</p>
        `
        let view = document.querySelector('.logic-flow-view')
        view.appendChild(element)
      }
    })
    // 鼠标离开节点
    this.lf.on('node:mouseleave', (node) => {
      let element = document.querySelector('.popper')
      if (element) { element.remove() }
    })
    // 连线删除
    this.lf.on('edge:delete', ({data}) => {
      let node = this.lf.graphModel.getNodeModelById(data.targetNodeId)
      if (node.type === 'switch-node' && node.properties.control === data.sourceNodeId) {
        node.properties.control = null
      }
    })
    // 锚点连线拖动连线成功时触发，主要用于添加额外的连线验证
    this.lf.on('anchor:drop', (data) => {
      let model = data.edgeModel
      let edges = this.lf.getEdgeModels({
        sourceAnchorId: model.sourceAnchorId,
        targetAnchorId: model.targetAnchorId
      })
      if (edges.length > 1) {
        this.$alert('重复连线')
        this.lf.deleteEdge(model.id)
      } else {
        // 开关的控制节点接入
        if (model.targetNodeId + '_top' === model.targetAnchorId || model.targetNodeId + '_bottom' === model.targetAnchorId) {
          let node = this.lf.graphModel.getNodeModelById(model.targetNodeId)
          if (node.properties.control === null) {
            node.properties.control = model.sourceNodeId
          } else {
            this.$alert('该开关已有控制节点')
            this.lf.deleteEdge(model.id)
          }
        }
      }
    })
    // ※子系统折叠 & 展开
    this.lf.on('group:fold', (data) => {
      if (data.isFolded === true) {
        data.foldGroup(false)
        this.foldAllChild(data.children)
        data.foldGroup(true)
      } else {
        this.unfoldAllChild(data.children)
      }
    })
  }
}

export { listeners }