<template>
  <div class="report-chart">
    <div class="chart-actions">
      <span>滚轮缩放 · 拖动底部滑块查看区间 · 悬停查看数值</span>
      <div><el-button size="small" text @click="resetZoom">重置视图</el-button><el-button size="small" type="primary" plain @click="expanded = true">放大查看</el-button></div>
    </div>
    <div ref="host" class="chart-host" :style="{ height: `${height}px` }" />
    <el-dialog v-model="expanded" title="图表详情" width="min(1400px, 96vw)" top="3vh" append-to-body @opened="openExpanded" @closed="closeExpanded">
      <div ref="expandedHost" class="expanded-host" />
      <template #footer><el-button @click="expanded = false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ option: { type: Object, default: () => ({}) }, height: { type: Number, default: 390 } })
const host = ref(null), expandedHost = ref(null), expanded = ref(false)
let chart, largeChart, observer, largeObserver
const displayOption = computed(() => {
  const source = props.option || {}
  const hasAxis = Boolean(source.xAxis && source.yAxis)
  const zoom = source.dataZoom || (hasAxis ? [{ type: 'inside', xAxisIndex: 0 }, { type: 'slider', xAxisIndex: 0, bottom: 12, height: 22 }] : [])
  return {
    ...source,
    animation: false,
    backgroundColor: '#fff',
    color: source.color || ['#2878c7', '#1b9e83', '#d18a25', '#9262b5', '#d45c67', '#498fbd', '#657895'],
    tooltip: { trigger: hasAxis ? 'axis' : 'item', axisPointer: { type: 'cross', snap: false }, confine: true, ...(source.tooltip || {}) },
    grid: hasAxis ? { left: 64, right: 35, top: source.legend ? 56 : 32, bottom: zoom.length ? 100 : 55, containLabel: true, ...(source.grid || {}) } : source.grid,
    dataZoom: zoom,
    toolbox: hasAxis ? { right: 14, top: 8, feature: { dataZoom: { yAxisIndex: 'none' }, restore: {}, saveAsImage: { title: '保存图片' } } } : source.toolbox,
    series: (source.series || []).map(item => item.type === 'line' ? { ...item, showSymbol: item.showSymbol ?? false, sampling: item.sampling || 'lttb', progressive: item.progressive ?? 3000, lineStyle: { width: 1.8, ...(item.lineStyle || {}) }, emphasis: { focus: 'series', ...(item.emphasis || {}) } } : item),
  }
})
function resetZoom() { for (const target of [chart, largeChart]) target?.dispatchAction({ type: 'restore' }) }
function openExpanded() {
  if (!expandedHost.value) return
  largeChart = echarts.init(expandedHost.value)
  largeChart.setOption(displayOption.value, true)
  largeObserver = new ResizeObserver(() => largeChart?.resize())
  largeObserver.observe(expandedHost.value)
}
function closeExpanded() { largeObserver?.disconnect(); largeChart?.dispose(); largeChart = null }
onMounted(() => {
  chart = echarts.init(host.value)
  chart.setOption(displayOption.value, true)
  observer = new ResizeObserver(() => chart?.resize())
  observer.observe(host.value)
})
watch(displayOption, value => { chart?.setOption(value, true); largeChart?.setOption(value, true) }, { deep: true })
onBeforeUnmount(() => { observer?.disconnect(); chart?.dispose(); closeExpanded() })
</script>

<style scoped>
.report-chart{min-width:0;border:1px solid #e1e9f2;border-radius:10px;background:#fff;overflow:hidden}
.chart-actions{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:8px 14px;border-bottom:1px solid #edf1f6;color:#687c91;font-size:12px}
.chart-actions>div{display:flex;align-items:center}.chart-host{width:100%;min-width:0}.expanded-host{height:min(78vh,850px);width:100%}
@media(max-width:700px){.chart-actions{align-items:flex-start;flex-direction:column}}
</style>
