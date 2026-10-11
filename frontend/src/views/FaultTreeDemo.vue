<template>
  <div class="page">
    <div class="head">
      <div><span class="eyebrow">FAULT TREE ANALYSIS</span><h2>FTA 图形化故障树</h2><p>维护事件、逻辑门与父子关系，可拖动节点调整布局。</p></div>
      <el-button type="primary" :loading="saving" :disabled="loading" @click="save">保存故障树</el-button>
    </div>
    <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" class="load-error" />
    <div class="layout">
      <el-card shadow="never" class="editor">
        <template #header><div class="title"><b>节点与关系</b><el-tag size="small">修订 {{ version }}</el-tag></div></template>
        <el-form label-position="top"><el-form-item label="故障树名称"><el-input v-model="treeName" /></el-form-item></el-form>
        <div class="buttons"><el-button v-for="item in types" :key="item.value" size="small" @click="add(item.value)">+ {{ item.label }}</el-button></div>
        <el-table :data="nodes" size="small" max-height="310" row-key="id" :row-class-name="rowClass" @row-click="selectRow">
          <el-table-column label="名称" min-width="160"><template #default="scope"><el-input v-model="scope.row.name" /></template></el-table-column>
          <el-table-column label="类型" width="110"><template #default="scope"><el-select v-model="scope.row.type"><el-option v-for="item in types" :key="item.value" :label="item.label" :value="item.value" /></el-select></template></el-table-column>
          <el-table-column width="60"><template #default="scope"><el-button link type="danger" @click.stop="removeNode(scope.row.id)">删除</el-button></template></el-table-column>
        </el-table>
        <h3>新增连线</h3>
        <div class="edge-add">
          <el-select v-model="edgeForm.source" placeholder="父节点" filterable><el-option v-for="node in nodes" :key="node.id" :label="node.name" :value="node.id" /></el-select>
          <span>→</span>
          <el-select v-model="edgeForm.target" placeholder="子节点" filterable><el-option v-for="node in nodes" :key="node.id" :label="node.name" :value="node.id" /></el-select>
          <el-button type="primary" plain @click="addEdge">连接</el-button>
        </div>
        <el-table :data="edges" size="small" max-height="220">
          <el-table-column label="父节点"><template #default="scope">{{ nodeName(scope.row.source) }}</template></el-table-column>
          <el-table-column label="子节点"><template #default="scope">{{ nodeName(scope.row.target) }}</template></el-table-column>
          <el-table-column width="60"><template #default="scope"><el-button link type="danger" @click="edges.splice(scope.$index, 1)">删除</el-button></template></el-table-column>
        </el-table>
        <p class="editor-help">点击列表可选中节点；修改完成后保存，节点位置与连线将一并保留。</p>
      </el-card>
      <el-card shadow="never" :class="['canvas-card', { expanded }]">
        <template #header><div class="title"><b>故障逻辑图</b><el-button size="small" @click="toggleExpand">{{ expanded ? '退出大图' : '展开大图' }}</el-button></div></template>
        <div class="toolbar">
          <div class="tools"><el-button size="small" @click="autoLayout">自动布局</el-button><el-button size="small" @click="fitView">适应画布</el-button></div>
          <div class="tools"><el-button size="small" aria-label="缩小" @click="zoomAt(scale / 1.2)">−</el-button><el-button size="small" title="恢复 100% 缩放" @click="zoomAt(1)">{{ Math.round(scale * 100) }}%</el-button><el-button size="small" aria-label="放大" @click="zoomAt(scale * 1.2)">+</el-button><el-checkbox v-model="snapToGrid">网格吸附</el-checkbox></div>
        </div>
        <div ref="canvas" :class="['canvas', { panning: gesture?.kind === 'pan' }]" :style="gridStyle" tabindex="0" aria-label="故障树画布：拖动节点，拖动空白平移，滚轮缩放" @pointerdown="startPan" @pointermove="movePointer" @pointerup="finishPointer" @pointercancel="cancelPointer" @lostpointercapture="cancelPointer" @wheel.prevent="wheelZoom">
          <div class="world" :style="worldStyle">
            <svg class="connections" :style="svgStyle" :width="drawingBounds.width" :height="drawingBounds.height" :viewBox="`${drawingBounds.minX} ${drawingBounds.minY} ${drawingBounds.width} ${drawingBounds.height}`">
              <defs><marker id="fta-arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0 0 L10 4 L0 8 Z" fill="#8294ac" /></marker></defs>
              <path v-for="(edge, index) in edgePaths" :key="index" :d="edge.path" :class="{ active: edge.active }" fill="none" stroke="#8294ac" stroke-width="2" marker-end="url(#fta-arrow)" />
            </svg>
            <div v-for="node in nodes" :key="node.id" :class="['node', node.type, { selected: selectedId === node.id, dragging: gesture?.nodeId === node.id }]" :style="nodeStyle(node)" :title="`${node.name} · ${typeName(node.type)}`" @pointerdown.stop="startNodeDrag($event, node)">
              <span v-if="isGate(node)" class="gate-label">{{ node.type }}</span><span v-else class="node-name">{{ node.name }}</span>
              <small>{{ isGate(node) ? (node.type === 'AND' ? '与门' : '或门') : typeName(node.type) }}</small>
            </div>
          </div>
          <el-empty v-if="!nodes.length && !loading" description="在左侧添加事件或逻辑门" />
          <div v-if="loading" class="canvas-loading">正在加载故障树…</div>
          <div class="canvas-hint">拖节点调整位置 · 拖空白平移 · 滚轮缩放</div>
        </div>
        <div class="statusbar"><span>{{ nodes.length }} 个节点 · {{ edges.length }} 条连线</span><span>{{ selectedNode ? `已选：${selectedNode.name}` : '自动布局可整理重叠节点' }}</span></div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { nodeSize, graphBounds, layoutGraph, edgePath, hasOverlaps, dragPosition } from '../utils/faultTreeGeometry.js'

const types = [{ label: '顶事件', value: 'top' }, { label: '中间事件', value: 'event' }, { label: '基础事件', value: 'basic' }, { label: 'AND门', value: 'AND' }, { label: 'OR门', value: 'OR' }]
const treeId = ref(), treeName = ref('默认故障树'), version = ref(1), nodes = ref([]), edges = ref([])
const edgeForm = ref({ source: '', target: '' }), canvas = ref(), selectedId = ref(null)
const scale = ref(1), offset = ref({ x: 0, y: 0 }), viewport = ref({ width: 900, height: 650 })
const gesture = ref(null), snapToGrid = ref(true), expanded = ref(false), saving = ref(false), loading = ref(true), loadError = ref('')
let resizeObserver
const typeName = type => types.find(item => item.value === type)?.label || type
const nodeName = id => nodes.value.find(node => String(node.id) === String(id))?.name || id
const isGate = node => node.type === 'AND' || node.type === 'OR'
const selectedNode = computed(() => nodes.value.find(node => node.id === selectedId.value))
const drawingBounds = computed(() => graphBounds(nodes.value, 180))
const worldStyle = computed(() => ({ transform: `translate(${offset.value.x}px, ${offset.value.y}px) scale(${scale.value})` }))
const svgStyle = computed(() => ({ left: `${drawingBounds.value.minX}px`, top: `${drawingBounds.value.minY}px` }))
const gridStyle = computed(() => ({ backgroundSize: `${20 * scale.value}px ${20 * scale.value}px`, backgroundPosition: `${offset.value.x}px ${offset.value.y}px` }))
const edgePaths = computed(() => {
  const lookup = new Map(nodes.value.map(node => [String(node.id), node]))
  return edges.value.map(edge => {
    const source = lookup.get(String(edge.source)), target = lookup.get(String(edge.target))
    return source && target ? { path: edgePath(source, target), active: source.id === selectedId.value || target.id === selectedId.value } : null
  }).filter(Boolean)
})
const nodeStyle = node => ({ left: `${node.x}px`, top: `${node.y}px`, width: `${nodeSize(node).width}px`, height: `${nodeSize(node).height}px` })
const rowClass = ({ row }) => row.id === selectedId.value ? 'selected-row' : ''
function selectRow(node) { selectedId.value = node.id }
function fitView() {
  if (!canvas.value || !nodes.value.length) return
  const bounds = graphBounds(nodes.value, 45)
  scale.value = Math.max(0.1, Math.min(1.25, viewport.value.width / bounds.width, viewport.value.height / bounds.height))
  offset.value = { x: (viewport.value.width - bounds.width * scale.value) / 2 - bounds.minX * scale.value, y: (viewport.value.height - bounds.height * scale.value) / 2 - bounds.minY * scale.value }
}
function zoomAt(value, point = { x: viewport.value.width / 2, y: viewport.value.height / 2 }) {
  if (gesture.value) return
  const nextScale = Math.max(0.1, Math.min(2.5, value)), ratio = nextScale / scale.value
  offset.value = { x: point.x - (point.x - offset.value.x) * ratio, y: point.y - (point.y - offset.value.y) * ratio }
  scale.value = nextScale
}
function wheelZoom(event) {
  const rect = canvas.value.getBoundingClientRect()
  zoomAt(scale.value * Math.exp(-Math.max(-100, Math.min(100, event.deltaY)) * 0.002), { x: event.clientX - rect.left, y: event.clientY - rect.top })
}
function capture(event) { canvas.value.setPointerCapture(event.pointerId); event.preventDefault() }
function startNodeDrag(event, node) {
  if (event.button !== 0 || gesture.value) return
  selectedId.value = node.id
  gesture.value = { kind: 'node', nodeId: node.id, pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, x: node.x, y: node.y, scale: scale.value, moved: false }
  capture(event)
}
function startPan(event) {
  if (event.button !== 0 || gesture.value) return
  selectedId.value = null
  gesture.value = { kind: 'pan', pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, x: offset.value.x, y: offset.value.y }
  capture(event)
}
function movePointer(event) {
  const active = gesture.value
  if (!active || active.pointerId !== event.pointerId) return
  const dx = event.clientX - active.startX, dy = event.clientY - active.startY
  if (active.kind === 'pan') offset.value = { x: active.x + dx, y: active.y + dy }
  else {
    const node = nodes.value.find(item => item.id === active.nodeId)
    if (!node) return
    if (Math.abs(dx) + Math.abs(dy) > 2) active.moved = true
    Object.assign(node, dragPosition(active, event.clientX, event.clientY))
  }
}
function finishPointer(event) {
  if (!gesture.value || gesture.value.pointerId !== event.pointerId) return
  movePointer(event)
  const active = gesture.value, node = nodes.value.find(item => item.id === active.nodeId)
  if (node && active.moved && snapToGrid.value) { node.x = Math.round(node.x / 20) * 20; node.y = Math.round(node.y / 20) * 20 }
  releasePointer()
}
function releasePointer() {
  const pointerId = gesture.value?.pointerId
  gesture.value = null
  if (pointerId !== undefined && canvas.value?.hasPointerCapture(pointerId)) canvas.value.releasePointerCapture(pointerId)
}
function cancelPointer() { releasePointer() }
function escape(event) { if (event.key === 'Escape') { releasePointer(); expanded.value = false } }
async function toggleExpand() { expanded.value = !expanded.value; await nextTick(); updateViewport(); fitView() }
function updateViewport() { if (canvas.value) viewport.value = { width: canvas.value.clientWidth, height: canvas.value.clientHeight } }
function add(type) {
  const node = { id: `n-${Date.now()}-${Math.random().toString(16).slice(2, 6)}`, name: type === 'AND' || type === 'OR' ? `${type}逻辑门` : '新故障事件', type, x: 0, y: 0 }
  const size = nodeSize(node)
  node.x = Math.round(((viewport.value.width / 2 - offset.value.x) / scale.value - size.width / 2) / 20) * 20
  node.y = Math.round(((viewport.value.height / 2 - offset.value.y) / scale.value - size.height / 2) / 20) * 20
  while (nodes.value.some(item => hasOverlaps([item, node]))) { node.x += 20; node.y += 20 }
  nodes.value.push(node); selectedId.value = node.id
  const rect = graphBounds([node], 24)
  if (rect.minX * scale.value + offset.value.x < 0 || rect.minY * scale.value + offset.value.y < 0 || rect.maxX * scale.value + offset.value.x > viewport.value.width || rect.maxY * scale.value + offset.value.y > viewport.value.height) fitView()
}
function removeNode(id) {
  nodes.value = nodes.value.filter(node => node.id !== id)
  edges.value = edges.value.filter(edge => String(edge.source) !== String(id) && String(edge.target) !== String(id))
  if (selectedId.value === id) selectedId.value = null
  if (edgeForm.value.source === id) edgeForm.value.source = ''
  if (edgeForm.value.target === id) edgeForm.value.target = ''
}
function addEdge() {
  const { source, target } = edgeForm.value
  if (!source || !target) return ElMessage.warning('请选择父节点和子节点')
  if (String(source) === String(target)) return ElMessage.warning('不能连接自身')
  if (edges.value.some(edge => String(edge.source) === String(source) && String(edge.target) === String(target))) return ElMessage.warning('连线已存在')
  const visited = new Set(), pending = [String(target)]
  while (pending.length) {
    const id = pending.pop()
    if (id === String(source)) return ElMessage.warning('该连接会形成循环，请重新选择')
    if (visited.has(id)) continue
    visited.add(id)
    pending.push(...edges.value.filter(edge => String(edge.source) === id).map(edge => String(edge.target)))
  }
  edges.value.push({ source, target }); edgeForm.value = { source: '', target: '' }
}
function autoLayout() { releasePointer(); layoutGraph(nodes.value, edges.value); fitView() }
async function load() {
  try {
    const response = await fetch('/api/v1/knowledge/fault-trees/', { credentials: 'include' })
    if (!response.ok) throw Error('故障树加载失败，请检查登录状态后刷新')
    const data = await response.json(), tree = data[0]
    if (tree) {
      treeId.value = tree.id; treeName.value = tree.name; version.value = tree.version
      nodes.value = (tree.graph?.nodes || []).map((node, index) => ({ ...node, x: Number.isFinite(Number(node.x)) ? Number(node.x) : 60 + index * 210, y: Number.isFinite(Number(node.y)) ? Number(node.y) : 60 }))
      edges.value = tree.graph?.edges || []
    }
    if (!nodes.value.length) {
      nodes.value = [{ id: 'top-1', name: '运载器任务失效', type: 'top' }, { id: 'or-1', name: '任一关键分系统失效', type: 'OR' }, { id: 'power-1', name: '动力系统失效', type: 'event' }, { id: 'electric-1', name: '电源系统失效', type: 'event' }]
      edges.value = [{ source: 'top-1', target: 'or-1' }, { source: 'or-1', target: 'power-1' }, { source: 'or-1', target: 'electric-1' }]
      layoutGraph(nodes.value, edges.value)
    } else if (hasOverlaps(nodes.value)) layoutGraph(nodes.value, edges.value)
    await nextTick(); updateViewport(); fitView()
  } catch (error) { loadError.value = error.message }
  finally { loading.value = false }
}
async function save() {
  saving.value = true
  try {
    releasePointer()
    const token = document.cookie.split('; ').find(item => item.startsWith('csrftoken='))?.slice(10)
    const body = { name: treeName.value, graph: { nodes: nodes.value, edges: edges.value, layout: { width: drawingBounds.value.width, height: drawingBounds.value.height } } }
    const url = treeId.value ? `/api/v1/knowledge/fault-trees/${treeId.value}/` : '/api/v1/knowledge/fault-trees/'
    const response = await fetch(url, { method: treeId.value ? 'PUT' : 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json', ...(token ? { 'X-CSRFToken': decodeURIComponent(token) } : {}) }, body: JSON.stringify(body) })
    const result = await response.json()
    if (!response.ok) throw Error(result.graph || result.detail || '保存失败')
    treeId.value = result.id; version.value = result.version
    ElMessage.success('故障树节点、布局和连线已保存')
  } catch (error) { ElMessage.error(error.message) }
  finally { saving.value = false }
}
onMounted(() => {
  updateViewport(); resizeObserver = new ResizeObserver(updateViewport); resizeObserver.observe(canvas.value)
  window.addEventListener('keydown', escape); load()
})
onUnmounted(() => { releasePointer(); resizeObserver?.disconnect(); window.removeEventListener('keydown', escape) })
</script>

<style scoped>
.page{max-width:1800px}.head,.title{display:flex;justify-content:space-between;align-items:center;gap:16px}.head{margin-bottom:18px}.eyebrow{font-size:12px;color:#1677ff;letter-spacing:1px}.head h2{margin:8px 0}.head p{color:#718198;margin:0;line-height:1.6}.load-error{margin-bottom:16px}.layout{display:grid;grid-template-columns:minmax(390px,440px) minmax(0,1fr);gap:16px}.editor,.canvas-card{min-width:0}.buttons{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}.buttons .el-button+.el-button,.tools .el-button+.el-button{margin-left:0}.edge-add{display:flex;align-items:center;gap:8px;margin-bottom:10px}.edge-add .el-select{flex:1;min-width:0}.editor-help{font-size:12px;color:#718198;line-height:1.8;margin-bottom:0}.editor :deep(.selected-row){--el-table-tr-bg-color:#edf5ff}.canvas-card :deep(.el-card__body){padding:0;display:flex;flex-direction:column}.toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:12px 16px;border-bottom:1px solid #e4ebf4;background:#fff}.tools{display:flex;align-items:center;gap:6px}.tools .el-checkbox{margin-left:6px}.canvas{height:clamp(480px,65vh,780px);min-height:420px;position:relative;overflow:hidden;background-color:#f8faff;background-image:linear-gradient(#e6edf7 1px,transparent 1px),linear-gradient(90deg,#e6edf7 1px,transparent 1px);cursor:grab;touch-action:none;user-select:none;outline:none}.canvas:focus-visible{box-shadow:inset 0 0 0 2px #409eff}.canvas.panning{cursor:grabbing}.world{position:absolute;left:0;top:0;width:0;height:0;transform-origin:0 0}.connections{position:absolute;overflow:visible;pointer-events:none}.connections path.active{stroke:#3b82f6;stroke-width:3}.node{position:absolute;box-sizing:border-box;padding:10px 14px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px;border:1.5px solid #76a4d8;border-radius:10px;background:#fff;color:#24364b;text-align:center;cursor:grab;box-shadow:0 3px 9px #1d4b7512;transition:box-shadow .15s,border-color .15s;touch-action:none}.node:hover{border-color:#3b82f6;box-shadow:0 5px 16px #1d4b7525}.node.selected{outline:3px solid #3b82f640;border-color:#3b82f6;z-index:2}.node.dragging{cursor:grabbing;box-shadow:0 8px 20px #1d4b7530;z-index:3}.node-name{font-size:13px;line-height:18px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere}.node small{color:#75869a;font-size:11px;line-height:13px}.node.top{background:#fff4f3;border-color:#ed8c86}.node.basic{border-radius:36px;background:#f0f9f5;border-color:#75b69c}.node.AND,.node.OR{border-radius:24px 24px 12px 12px;background:#fff9eb;border-color:#dcb059;padding:8px}.gate-label{font-size:17px;font-weight:700;color:#9a6814}.canvas-hint{position:absolute;bottom:14px;left:50%;transform:translateX(-50%);padding:7px 12px;border:1px solid #e4ebf4;border-radius:18px;background:#fffffff0;font-size:12px;white-space:nowrap;color:#6d7f96;pointer-events:none}.canvas-loading{position:absolute;inset:0;display:grid;place-items:center;background:#f8faffc9;color:#718198}.canvas :deep(.el-empty){pointer-events:none;padding-top:140px}.statusbar{display:flex;justify-content:space-between;gap:12px;padding:10px 16px;border-top:1px solid #e4ebf4;font-size:12px;color:#718198}.statusbar span:last-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.canvas-card.expanded{position:fixed;inset:18px;z-index:2100;box-shadow:0 0 0 30px #142a4b40;display:flex;flex-direction:column}.expanded :deep(.el-card__body){flex:1;min-height:0}.expanded .canvas{flex:1;height:auto;min-height:0}.expanded .statusbar,.expanded .toolbar{flex-shrink:0}@media(max-width:1150px){.layout{grid-template-columns:1fr}.canvas-card{grid-row:1}.editor{grid-row:2}.canvas{height:560px}.canvas-card.expanded{inset:8px}}@media(max-width:600px){.head{align-items:flex-start}.toolbar{padding:10px}.tools{flex-wrap:wrap}.canvas-hint{font-size:11px}.statusbar{flex-wrap:wrap}}
</style>
