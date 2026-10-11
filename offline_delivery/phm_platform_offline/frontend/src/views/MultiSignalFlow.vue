<template>
  <div class="page">
    <div class="head"><div><h2>多信号流图</h2><p>按数据集查看测量信号、PBS 所属单机和分析模块的接入条件。</p></div><el-button :loading="loading" @click="load">刷新数据</el-button></div>
    <el-card shadow="never" class="selector"><el-select v-model="datasetId" filterable placeholder="选择已登记的 CSV 数据集" @change="loadSamples"><el-option v-for="item in selectableDatasets" :key="item.id" :label="`${item.name} · #${item.id}`" :value="item.id"/></el-select><el-tag v-if="selectedDataset" :type="selectedDataset.structure_node_id?'success':'warning'">{{selectedDataset.structure_node_name||'未关联 PBS'}}</el-tag><span v-if="sampleCount">已载入 {{sampleCount}} 行用于预览{{hasMore?'，仍有后续数据':''}}</span></el-card>
    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false"/>
    <el-empty v-if="!selectedDataset&&!loading" description="请选择数据集"/>
    <template v-if="selectedDataset">
      <div class="summary"><el-card shadow="never"><small>PBS 关联</small><strong>{{selectedDataset.structure_node_name||'未建立'}}</strong><p>{{selectedDataset.structure_node_id?'已通过结构节点编号关联':'请在数据管理中点击“关联 PBS”'}}</p></el-card><el-card shadow="never"><small>健康评估输入</small><strong>{{numericSignals.length}} 路数值信号</strong><p>单机评估可处理数值信号；生成的 HI 仅属于本次所选数据集</p></el-card><el-card shadow="never"><small>寿命预测输入</small><strong>{{hiReady?'预览中满足行数':'预览中未满足'}}</strong><p>{{hiReady?'预览区间有至少 51 行 HI；仍需选择匹配部件模型':'训练寿命模型需要 CSV 中至少 51 行 HI'}}</p></el-card></div>
      <el-card shadow="never" class="flow-card"><template #header><b>信号与分析接入关系</b></template><el-alert title="箭头只表示数据接入和已登记的结构关系，不表示已完成诊断、健康评估或寿命预测。" type="info" :closable="false"/><ReportChart v-if="flowOption.series[0].data.length" :key="`flow-${datasetId}`" :option="flowOption" :height="Math.max(500, 160 + Math.min(numericSignals.length, 10) * 36)"/></el-card>
      <el-card shadow="never" class="trend-card"><template #header><div class="chart-head"><div><b>多信号趋势</b><p>为便于同图比较，每路信号在当前预览区间按自身最小值和最大值缩放到 0–1；悬停可查看原始数值。</p></div><span>预览 {{sampleCount}} 行{{hasMore?'（仅前 1000 行）':''}} · 最多显示 {{MAX_SIGNALS}} 路</span></div></template>
        <el-select v-model="visibleSignals" multiple collapse-tags filterable placeholder="选择要比较的信号" class="signal-select"><el-option v-for="name in numericSignals" :key="name" :label="name" :value="name"/></el-select>
        <ReportChart v-if="visibleSignals.length" :key="`trend-${datasetId}`" :option="trendOption" :height="460"/><el-empty v-else description="没有可显示的数值信号"/>
      </el-card>
      <el-card shadow="never" class="conditions"><template #header><b>当前数据的跨模块一致性</b></template><el-descriptions :column="1" border><el-descriptions-item label="结构标识">{{selectedDataset.structure_node_name||'未关联 PBS；系统/部件文本不能代替结构标识'}}</el-descriptions-item><el-descriptions-item label="健康评估">数值信号可作为算法输入，健康指数由运行时计算；图中不预设 HI 结果</el-descriptions-item><el-descriptions-item label="寿命预测">{{hiReady?'已有 HI 输入列；仍需核对所选部件模型与 PBS 单机一致':'当前预览未验证有至少 51 行 HI，不能直接断言可做训练模型寿命预测'}}</el-descriptions-item></el-descriptions><div class="links"><el-button type="primary" plain @click="go('/platform-health')">前往健康评估</el-button><el-button plain @click="go('/lifetime-prediction')">前往寿命预测</el-button><el-button plain @click="go('/data-management')">管理 PBS 关联</el-button></div></el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import ReportChart from '../components/ReportChart.vue'
import { isSelectableDataset } from '../utils/datasetVisibility.js'

const MAX_SIGNALS = 8
const router = useRouter(), route = useRoute()
const datasets = ref([]), datasetId = ref(null), rows = ref([]), columns = ref([]), visibleSignals = ref([]), loading = ref(false), error = ref(''), hasMore = ref(false)
const selectableDatasets = computed(() => datasets.value.filter(isSelectableDataset))
const selectedDataset = computed(() => selectableDatasets.value.find(item => item.id === datasetId.value))
const sampleCount = computed(() => rows.value.length)
const numericSignals = computed(() => columns.value.filter(name => rows.value.some(row => row[name] !== '' && row[name] != null && Number.isFinite(Number(row[name]))) && !/^(time|timestamp|index)$/i.test(name)))
const hiColumn = computed(() => columns.value.find(name => /^(hi_norm|hi|health_index|health|健康指数)$/i.test(name)))
const hiReady = computed(() => Boolean(hiColumn.value && rows.value.filter(row => row[hiColumn.value] !== '' && row[hiColumn.value] != null && Number.isFinite(Number(row[hiColumn.value]))).length >= 51))
const timeColumn = computed(() => columns.value.find(name => /^(time|timestamp)$/i.test(name)))

const flowOption = computed(() => {
  const signals = numericSignals.value.slice(0, 10)
  if (hiReady.value && hiColumn.value && !signals.includes(hiColumn.value)) {
    if (signals.length) signals[signals.length - 1] = hiColumn.value
    else signals.push(hiColumn.value)
  }
  const data = [{ id: 'dataset', name: selectedDataset.value?.name || '数据集', category: 0, x: 100, y: 220, symbolSize: 90, itemStyle: { color: '#386da7' } }]
  const links = []
  if (selectedDataset.value?.structure_node_id) {
    data.push({ id: 'pbs', name: selectedDataset.value.structure_node_name, category: 1, x: 100, y: 55, symbolSize: 86, itemStyle: { color: '#1f9d83' } })
    links.push({ source: 'dataset', target: 'pbs', value: '已登记 PBS 关联' })
  }
  signals.forEach((name, index) => {
    data.push({ id: `signal-${index}`, name, category: 2, x: 340 + (index % 2) * 135, y: 35 + Math.floor(index / 2) * 105, symbolSize: 64, itemStyle: { color: '#4b9bd2' } })
    links.push({ source: 'dataset', target: `signal-${index}`, value: 'CSV 列' })
  })
  if (signals.length) {
    data.push({ id: 'health-input', name: '健康评估输入', category: 3, x: 710, y: 155, symbolSize: 88, itemStyle: { color: '#9b75c4' } })
    signals.forEach((_,index) => links.push({ source: `signal-${index}`, target: 'health-input', value: '可用数值输入' }))
  }
  if (hiReady.value && signals.includes(hiColumn.value)) {
    data.push({ id: 'rul-input', name: '寿命预测输入', category: 4, x: 930, y: 290, symbolSize: 88, itemStyle: { color: '#d2963e' } })
    links.push({ source: `signal-${signals.indexOf(hiColumn.value)}`, target: 'rul-input', value: 'CSV 已含 HI' })
  }
  return { tooltip: { formatter: params => params.dataType === 'edge' ? params.data.value : params.name }, legend: { data: ['数据集', 'PBS', '信号', '健康评估', '寿命预测'], bottom: 0 }, series: [{ type: 'graph', layout: 'none', roam: true, draggable: true, coordinateSystem: null, categories: [{ name: '数据集' }, { name: 'PBS' }, { name: '信号' }, { name: '健康评估' }, { name: '寿命预测' }], data, links, label: { show: true, position: 'bottom', width: 110, overflow: 'truncate' }, lineStyle: { color: 'source', opacity: 0.55, curveness: 0.08, width: 2 }, edgeSymbol: ['none', 'arrow'], edgeSymbolSize: [0, 8], emphasis: { focus: 'adjacency' } }] }
})

const trendOption = computed(() => {
  const selected = visibleSignals.value.slice(0, MAX_SIGNALS)
  const originals = {}
  const series = selected.map(name => {
    const values = rows.value.map(row => { const value = Number(row[name]); return row[name] === '' || row[name] == null || !Number.isFinite(value) ? null : value })
    const finite = values.filter(value => value != null)
    let minimum = Infinity, maximum = -Infinity
    for (const value of finite) { if (value < minimum) minimum = value; if (value > maximum) maximum = value }
    const spread = maximum - minimum
    originals[name] = values
    return { name, type: 'line', data: values.map((value, index) => [timeColumn.value && Number.isFinite(Number(rows.value[index][timeColumn.value])) ? Number(rows.value[index][timeColumn.value]) : index, value == null ? null : spread ? (value - minimum) / spread : 0.5]), connectNulls: false }
  })
  return { legend: { data: selected, type: 'scroll', top: 8 }, tooltip: { trigger: 'axis', formatter: params => params.map(item => `${item.marker}${item.seriesName}: ${originals[item.seriesName]?.[item.dataIndex] ?? '—'}`).join('<br>') }, grid: { top: 72, bottom: 105, left: 55, right: 45, containLabel: true }, xAxis: { type: 'value', name: timeColumn.value || '样本序号', scale: true }, yAxis: { type: 'value', name: '相对变化 (0–1)', min: 0, max: 1 }, dataZoom: [{ type: 'inside' }, { type: 'slider', bottom: 18 }], series }
})

async function load() {
  loading.value = true; error.value = ''
  try { const response = await fetch('/api/v1/datasets/', { credentials: 'include' }); if (!response.ok) throw Error('数据集目录加载失败'); datasets.value = await response.json(); const requested = Number(route.query.dataset_id); if (!datasetId.value && selectableDatasets.value.some(item => item.id === requested)) datasetId.value = requested; if (datasetId.value) await loadSamples() }
  catch (exc) { error.value = exc.message }
  finally { loading.value = false }
}
async function loadSamples() {
  rows.value = []; columns.value = []; visibleSignals.value = []; error.value = ''
  if (!datasetId.value) return
  loading.value = true
  try { const response = await fetch(`/api/v1/datasets/${datasetId.value}/samples/?limit=1000`, { credentials: 'include' }); const body = await response.json(); if (!response.ok) throw Error(body.detail || 'CSV 读取失败'); columns.value = body.columns || []; rows.value = body.rows || []; hasMore.value = Boolean(body.has_more); visibleSignals.value = numericSignals.value.slice(0, 4) }
  catch (exc) { error.value = exc.message }
  finally { loading.value = false }
}
function go(path) { router.push({ path, query: { dataset_id: datasetId.value } }) }
onMounted(load)
</script>

<style scoped>
.page{max-width:1500px;min-width:0}.head,.chart-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.head h2{margin:0 0 6px}.head p,.chart-head p{margin:0;color:#687c91}.selector{margin:18px 0}.selector :deep(.el-card__body){display:flex;align-items:center;gap:14px;flex-wrap:wrap}.selector .el-select{width:min(460px,100%)}.selector span,.chart-head span{font-size:12px;color:#718198}.summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:16px 0}.summary small,.summary strong{display:block}.summary small{color:#718198}.summary strong{font-size:20px;margin:9px 0}.summary p{color:#66788c;font-size:12px;margin:0}.flow-card,.trend-card,.conditions{margin-top:16px}.flow-card .el-alert{margin-bottom:16px}.signal-select{width:min(520px,100%);margin-bottom:16px}.links{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}@media(max-width:850px){.summary{grid-template-columns:1fr}.head,.chart-head{display:block}}
</style>
