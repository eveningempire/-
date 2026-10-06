import BaseNode from './BaseNode.mjs'

class AndNodeModel extends BaseNode.model {
  initNodeData (data) {
    super.initNodeData(data)
  }
  setAttributes () {
    super.setAttributes()
    const circleOnlyAsTarget = {
      message: "只允许从右边的锚点连出",
      validate: (sourceNode, targetNode, sourceAnchor, targetAnchor) => {
        return sourceAnchor.type === "right"
      }
    }
    this.sourceRules.push(circleOnlyAsTarget)
    this.targetRules.push({
      message: "只允许连接左边的锚点",
      validate: (sourceNode, targetNode, sourceAnchor, targetAnchor) => {
        return targetAnchor.type === "left"
      }
    })
  }
}


class AndNodeView extends BaseNode.view {}


export default {
  type: 'and-node',
  model: AndNodeModel,
  view: AndNodeView
}