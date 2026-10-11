// Nodes and connections share graph coordinates and one viewport transform.
export function nodeSize(node) {
  return node.type === 'AND' || node.type === 'OR' ? { width: 96, height: 64 } : { width: 176, height: 72 }
}

export function dragPosition(start, clientX, clientY) {
  return { x: start.x + (clientX - start.startX) / start.scale, y: start.y + (clientY - start.startY) / start.scale }
}

export function graphBounds(nodes, padding = 0) {
  if (!nodes.length) return { minX: 0, minY: 0, maxX: 900, maxY: 650, width: 900, height: 650 }
  const minX = Math.min(...nodes.map(node => node.x)) - padding
  const minY = Math.min(...nodes.map(node => node.y)) - padding
  const maxX = Math.max(...nodes.map(node => node.x + nodeSize(node).width)) + padding
  const maxY = Math.max(...nodes.map(node => node.y + nodeSize(node).height)) + padding
  return { minX, minY, maxX, maxY, width: maxX - minX, height: maxY - minY }
}

export function hasOverlaps(nodes) {
  return nodes.some((a, index) => nodes.slice(index + 1).some(b => {
    const aSize = nodeSize(a), bSize = nodeSize(b)
    return a.x < b.x + bSize.width + 12 && a.x + aSize.width + 12 > b.x && a.y < b.y + bSize.height + 12 && a.y + aSize.height + 12 > b.y
  }))
}

export function layoutGraph(nodes, edges) {
  const lookup = new Map(nodes.map(node => [String(node.id), node]))
  const incoming = new Map(nodes.map(node => [String(node.id), 0]))
  const children = new Map(nodes.map(node => [String(node.id), []]))
  const depths = new Map(nodes.map(node => [String(node.id), 0]))
  for (const edge of edges) {
    const source = String(edge.source), target = String(edge.target)
    if (!lookup.has(source) || !lookup.has(target)) continue
    incoming.set(target, incoming.get(target) + 1)
    children.get(source).push(target)
  }
  const queue = [...incoming.keys()].filter(id => incoming.get(id) === 0), visited = new Set()
  // A shared child is placed beneath every parent, including in multi-root DAGs.
  for (let index = 0; index < queue.length; index++) {
    const id = queue[index]; visited.add(id)
    for (const target of children.get(id)) {
      depths.set(target, Math.max(depths.get(target), depths.get(id) + 1))
      incoming.set(target, incoming.get(target) - 1)
      if (incoming.get(target) === 0) queue.push(target)
    }
  }
  const levels = new Map()
  const fallbackDepth = Math.max(0, ...[...visited].map(id => depths.get(id))) + 1
  for (const node of nodes) {
    const depth = visited.has(String(node.id)) ? depths.get(String(node.id)) : fallbackDepth
    if (!levels.has(depth)) levels.set(depth, [])
    levels.get(depth).push(node)
  }
  const rowWidth = row => row.reduce((width, node) => width + nodeSize(node).width, 0) + Math.max(0, row.length - 1) * 60
  const width = Math.max(0, ...[...levels.values()].map(rowWidth))
  for (const [depth, row] of levels) {
    let x = 40 + (width - rowWidth(row)) / 2
    for (const node of row) { node.x = x; node.y = 40 + depth * 150; x += nodeSize(node).width + 60 }
  }
}

export function edgePath(source, target) {
  const a = nodeSize(source), b = nodeSize(target)
  const x1 = source.x + a.width / 2, y1 = source.y + a.height
  const x2 = target.x + b.width / 2, y2 = target.y
  if (y2 >= y1 + 30) {
    const middleY = (y1 + y2) / 2
    return `M ${x1} ${y1} L ${x1} ${middleY} L ${x2} ${middleY} L ${x2} ${y2}`
  }
  // Use an outside lane for nodes at the same height or reversed vertically.
  const right = target.x >= source.x
  const startX = right ? source.x + a.width : source.x
  const endX = right ? target.x + b.width : target.x
  const lane = right ? Math.max(startX, endX) + 36 : Math.min(startX, endX) - 36
  return `M ${startX} ${source.y + a.height / 2} L ${lane} ${source.y + a.height / 2} L ${lane} ${target.y + b.height / 2} L ${endX} ${target.y + b.height / 2}`
}
