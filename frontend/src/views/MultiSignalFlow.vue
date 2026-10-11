<template>
  <div class="page">
    <div class="head"><div><h2>多信号流图</h2><p>展示型号内部的管路、部件和连接端拓扑。图中的箭头来自系统配置文件，不代表 CSV 参数接入关系。</p></div><el-button :loading="loading" @click="loadConfig">刷新配置</el-button></div>
    <el-card shadow="never" class="selector"><el-select v-model="selectedSystemId" filterable placeholder="选择型号/分系统" @change="selectedNodeId = ''"><el-option v-for="system in systems" :key="system.system_id" :label="system.name" :value="system.system_id" /></el-select><el-tag type="info">只读可视化</el-tag><span>节点 {{ currentGraph.nodes.length }} 个 · 连接 {{ currentGraph.edges.length }} 条</span></el-card>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" />
    <el-empty v-if="!loading && !systems.length && !error" description="配置文件中没有可显示的型号" />
    <template v-if="systems.length">
      <div class="summary"><el-card shadow="never"><small>当前型号</small><strong>{{ currentSystem?.name || '—' }}</strong><p>配置编号：{{ currentSystem?.system_id ?? '—' }}</p></el-card><el-card shadow="never"><small>拓扑节点</small><strong>{{ currentGraph.nodes.length }} 个</strong><p>包含部件、输入端、输出端和测试/故障节点</p></el-card><el-card shadow="never"><small>连接端</small><strong>{{ currentGraph.edges.length }} 条</strong><p>按配置中的 source/target 锚点绘制有向连接</p></el-card></div>
    <el-card shadow="never" class="flow-card"><template #header><div class="chart-head"><div><b>管路与连接端拓扑</b><p>滚轮缩放，按住鼠标拖动空白区域移动整体，点击节点查看属性。</p></div><div class="legend"><span v-for="item in legendItems" :key="item.type"><i :style="{ background: item.color }" />{{ item.label }}</span></div></div></template><el-alert title="默认显示当前型号的全部节点和连接。" type="info" :closable="false" class="hint" /><div v-if="svgGraph.nodes.length" class="topology-wrap"><div class="view-controls"><el-button size="small" @click="zoomOut">−</el-button><span>{{ Math.round(view.scale * 100) }}%</span><el-button size="small" @click="zoomIn">+</el-button><el-button size="small" @click="resetView">重置视图</el-button></div><svg ref="topologyHost" class="topology-svg" :viewBox="svgGraph.viewBox" role="img" aria-label="多信号流拓扑图" @wheel.prevent="zoomGraph" @mousedown="startPan" @mousemove="movePan" @mouseup="endPan" @mouseleave="endPan"><defs><marker id="msfg-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8392a5" /></marker></defs><g :transform="viewTransform"><line v-for="edge in svgGraph.edges" :key="edge.id" :x1="edge.x1" :y1="edge.y1" :x2="edge.x2" :y2="edge.y2" stroke="#8392a5" stroke-width="2" marker-end="url(#msfg-arrow)" /><g v-for="node in svgGraph.nodes" :key="node.id" class="topology-node" @click.stop="selectedNodeId = node.id"><rect v-if="node.type === 'subsystem-node'" :x="node.x - 78" :y="node.y - 25" width="156" height="50" rx="8" :fill="node.color" /><circle v-else :cx="node.x" :cy="node.y" r="22" :fill="node.color" /><text :x="node.x" :y="node.type === 'subsystem-node' ? node.y + 5 : node.y + 40" text-anchor="middle" :fill="node.type === 'subsystem-node' ? '#fff' : '#344054'">{{ node.name }}</text></g></g></svg></div><el-empty v-else description="当前型号没有拓扑节点" /></el-card>
      <el-card v-if="selectedNode" shadow="never" class="details"><template #header><b>节点详情</b></template><el-descriptions :column="2" border><el-descriptions-item label="名称">{{ selectedNode.name }}</el-descriptions-item><el-descriptions-item label="类型">{{ selectedNode.typeLabel }}</el-descriptions-item><el-descriptions-item label="节点 ID">{{ selectedNode.id }}</el-descriptions-item><el-descriptions-item label="坐标">({{ selectedNode.x }}, {{ selectedNode.y }})</el-descriptions-item><el-descriptions-item label="输入/输出端" :span="2">{{ selectedNode.portText || '配置中未标注' }}</el-descriptions-item></el-descriptions></el-card>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import bundledConfig from '../data/多信号流图配置.json'

const CONFIG_PATH = '3dmodel/多信号流图配置.json'
const CONFIG_URLS = [...new Set([
  `${import.meta.env.BASE_URL || '/'}${CONFIG_PATH}`,
  `/${CONFIG_PATH}`,
  `/static/${CONFIG_PATH}`
])]
const TYPE_META = { 'subsystem-node': { label: '部件/分系统', color: '#9673a6' }, 'input-node': { label: '输入端', color: '#67c23a' }, 'output-node': { label: '输出端', color: '#409eff' }, 'test-node': { label: '测试/故障节点', color: '#e6a23c' }, 'fault-node': { label: '故障节点', color: '#f56c6c' }, default: { label: '其他节点', color: '#909399' } }
const systems = ref([]), selectedSystemId = ref(null), selectedNodeId = ref(''), loading = ref(false), error = ref('')
const topologyHost = ref(null)
const view = reactive({ scale: 1, panX: 0, panY: 0, dragging: false, moved: false, startX: 0, startY: 0, originX: 0, originY: 0 })
const currentSystem = computed(() => systems.value.find(item => item.system_id === selectedSystemId.value) || systems.value[0])
const currentGraph = computed(() => currentSystem.value?.data || { nodes: [], edges: [] })
const selectedNode = computed(() => currentGraph.value.nodes.find(node => node.id === selectedNodeId.value))
const legendItems = computed(() => Object.entries(TYPE_META).filter(([type]) => type !== 'default').map(([type, meta]) => ({ type, ...meta })))
const viewTransform = computed(() => `translate(${view.panX} ${view.panY}) scale(${view.scale})`)
function typeMeta(type) { return TYPE_META[type] || TYPE_META.default }
function nodeName(node) { return node?.text?.value || node?.properties?.name || node?.id || '未命名节点' }
function parseProperties(value) { if (!value || typeof value !== 'string') return ''; const match = value.match(/input=([^;}]+).*output=([^;}]+)/i); return match ? `输入 ${match[1]} · 输出 ${match[2]}` : value }
function normalizeSystem(system, index) {
  const data = system?.data || {}, nodes = Array.isArray(data.nodes) ? data.nodes : [], edges = Array.isArray(data.edges) ? data.edges : []
  const normalizedNodes = nodes.map(node => { const meta = typeMeta(node.type); return { id: node.id, name: nodeName(node), type: node.type || 'default', typeLabel: meta.label, x: Number.isFinite(Number(node.x)) ? Number(node.x) : index * 100, y: Number.isFinite(Number(node.y)) ? Number(node.y) : index * 100, color: node?.properties?.typeColor || meta.color, portText: parseProperties(node?.properties?.fields), properties: node.properties || {}, anchors: Array.isArray(node.anchors) ? node.anchors : [] } })
  const nodeIds = new Set(normalizedNodes.map(node => node.id))
  return { system_id: system.system_id ?? system.id ?? index, name: system.name || `型号/分系统 ${index + 1}`, parent_id: system.parent_id, data: { nodes: normalizedNodes, edges: edges.filter(edge => nodeIds.has(edge.sourceNodeId) && nodeIds.has(edge.targetNodeId)) } }
}
const svgGraph = computed(() => {
  const nodes = currentGraph.value.nodes, xValues = nodes.map(node => node.x), yValues = nodes.map(node => node.y), minX = Math.min(...xValues, 0), minY = Math.min(...yValues, 0), maxX = Math.max(...xValues, 1000), maxY = Math.max(...yValues, 600), width = Math.max(1000, maxX - minX + 240), height = Math.max(520, maxY - minY + 180)
  const normalized = nodes.map(node => ({ ...node, x: node.x - minX + 120, y: node.y - minY + 80 }))
  const byId = new Map(normalized.map(node => [node.id, node]))
  const edges = currentGraph.value.edges.map(edge => { const source = byId.get(edge.sourceNodeId), target = byId.get(edge.targetNodeId); return source && target ? { id: edge.id, x1: source.x, y1: source.y, x2: target.x, y2: target.y } : null }).filter(Boolean)
  return { nodes: normalized, edges, viewBox: `0 0 ${width} ${height}` }
})
function resetView() { view.scale = 1; view.panX = 0; view.panY = 0 }
function zoomIn() { view.scale = Math.min(3, Number((view.scale + 0.15).toFixed(2))) }
function zoomOut() { view.scale = Math.max(0.35, Number((view.scale - 0.15).toFixed(2))) }
function zoomGraph(event) { event.deltaY < 0 ? zoomIn() : zoomOut() }
function startPan(event) { if (event.button !== 0) return; view.dragging = true; view.moved = false; view.startX = event.clientX; view.startY = event.clientY; view.originX = view.panX; view.originY = view.panY }
function movePan(event) { if (!view.dragging || !topologyHost.value) return; const rect = topologyHost.value.getBoundingClientRect(); const vb = svgGraph.value.viewBox.split(' ').map(Number); const dx = (event.clientX - view.startX) * vb[2] / rect.width / view.scale; const dy = (event.clientY - view.startY) * vb[3] / rect.height / view.scale; view.panX = view.originX + dx; view.panY = view.originY + dy; view.moved = Math.abs(dx) + Math.abs(dy) > 3 }
function endPan() { view.dragging = false }
watch(selectedSystemId, resetView)
async function loadConfig() {
  loading.value = true
  error.value = ''
  try {
    let body = null
    let lastError = null
    for (const url of CONFIG_URLS) {
      try {
        const response = await fetch(url, { cache: 'no-store', headers: { Accept: 'application/json' } })
        const text = await response.text()
        if (!response.ok || /^\s*</.test(text)) {
          lastError = new Error(`配置地址不可用：${url}`)
          continue
        }
        body = JSON.parse(text)
        break
      } catch (exc) {
        lastError = exc
      }
    }
    // 某些部署将未知静态路径回退到 index.html；此时使用随前端构建的同一份配置。
    if (!body) body = bundledConfig
    const rawSystems = Array.isArray(body.SystemData) ? body.SystemData : []
    systems.value = rawSystems.map(normalizeSystem).filter(system => system.data.nodes.length)
    const preferred = body.currentSystemId ?? systems.value[0]?.system_id
    selectedSystemId.value = systems.value.some(system => system.system_id === preferred) ? preferred : systems.value[0]?.system_id ?? null
    selectedNodeId.value = ''
  } catch (exc) {
    systems.value = []
    error.value = exc.message || '配置加载失败'
  } finally { loading.value = false }
}
onMounted(loadConfig)
</script>

<style scoped>
.page{max-width:1500px;min-width:0}.head,.chart-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.head h2{margin:0 0 6px}.head p,.chart-head p{margin:0;color:#687c91}.selector{margin:18px 0}.selector :deep(.el-card__body){display:flex;align-items:center;gap:14px;flex-wrap:wrap}.selector .el-select{width:min(460px,100%)}.selector span{font-size:12px;color:#718198}.summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:16px 0}.summary small,.summary strong{display:block}.summary small{color:#718198}.summary strong{font-size:20px;margin:9px 0}.summary p{color:#66788c;font-size:12px;margin:0}.flow-card,.details{margin-top:16px}.hint{margin-bottom:10px}.legend{display:flex;flex-wrap:wrap;gap:10px;font-size:12px;color:#62748a}.legend span{display:inline-flex;align-items:center;gap:4px}.legend i{display:inline-block;width:10px;height:10px;border-radius:50%}.topology-wrap{position:relative;width:100%;overflow:hidden;border:1px solid #e1e9f2;border-radius:8px;background:#fff;min-height:520px}.topology-svg{display:block;width:100%;min-width:900px;min-height:520px;cursor:grab}.topology-svg:active{cursor:grabbing}.topology-node{cursor:pointer}.topology-node:hover{filter:brightness(1.08)}.topology-node text{font-size:14px;pointer-events:none}.view-controls{position:absolute;right:12px;top:10px;z-index:2;display:flex;align-items:center;gap:6px;padding:4px 6px;background:rgba(255,255,255,.94);border:1px solid #dfe6ef;border-radius:6px}.view-controls span{min-width:42px;text-align:center;font-size:12px;color:#66788c}@media(max-width:850px){.summary{grid-template-columns:1fr}.head,.chart-head{display:block}.legend{margin-top:12px}}
</style>
