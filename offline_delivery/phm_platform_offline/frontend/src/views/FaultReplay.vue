<template>
  <div class="page">
    <div class="head"><div><h2>故障事件重演</h2><p>选择数据管理中的 CSV 和一个参数，按时间查看曲线；有 FaultFlag 的数据会随重演显示异常预警。</p></div><el-button :loading="loading" @click="loadEvents">刷新事件</el-button></div>
    <div class="stats"><el-card shadow="never"><small>可重演事件</small><strong>{{ events.length }}</strong></el-card><el-card shadow="never"><small>当前数据源</small><strong class="source">{{ selected?.diagnosis?.source_csv || selected?.name || '—' }}</strong></el-card><el-card shadow="never"><small>样本点</small><strong>{{ selected?.diagnosis?.sample_count || curve.count || '—' }}</strong></el-card></div>
    <el-card shadow="never">
      <el-alert v-if="!loading && !events.length" title="尚未发现可重演事件，请确认数据管理中已有可用 CSV。" type="warning" show-icon :closable="false" />
      <el-form inline><el-form-item label="故障事件"><el-select v-model="eventId" filterable placeholder="选择仿真故障事件" @change="selectEvent"><el-option v-for="event in events" :key="event.id" :value="event.id" :label="`${event.name} / ${formatTime(event.start_time)}—${formatTime(event.end_time ?? event.start_time)}`" /></el-select></el-form-item><el-form-item label="开始"><el-input-number v-model="form.start" :min="selected?.start_time ?? 0" :max="form.end" :precision="2" /></el-form-item><el-form-item label="结束"><el-input-number v-model="form.end" :min="form.start" :max="selected?.end_time ?? form.end" :precision="2" /></el-form-item><el-form-item label="倍速"><el-select v-model="form.speed"><el-option v-for="speed in [.5, 1, 2, 5, 10]" :key="speed" :value="speed" :label="`${speed}x`" /></el-select></el-form-item><el-button type="primary" :loading="creating" :disabled="!eventId" @click="create">创建重演</el-button></el-form>
    </el-card>
    <el-card v-if="replay" shadow="never" class="result">
      <div class="toolbar"><el-tag :type="replay.state === 'finished' ? 'success' : 'primary'">{{ states[replay.state] }}</el-tag><b>当前时间 {{ formatTime(replay.current_time) }}</b><span>窗口 {{ formatTime(replay.window_start) }}—{{ formatTime(replay.window_end) }}</span><span>{{ replay.speed }}x</span><el-progress class="progress" :percentage="progress" :show-text="false" /><el-button @click="control('restart')">重置</el-button><el-button type="primary" @click="control(replay.state === 'playing' ? 'pause' : 'play')">{{ replay.state === 'playing' ? '暂停' : '播放' }}</el-button></div>
      <el-alert v-if="activeWarning" class="warning" title="异常预警" :description="`当前回放数据的 ${faultFlagColumn} 为 1，事件：${selected?.name || '故障事件'}。时间 ${formatTime(currentSample?.time)}。标签恢复为 0 时预警自动消除。`" type="error" show-icon :closable="false" />
      <p v-else-if="!faultFlagColumn" class="status-note">当前 CSV 没有 FaultFlag 故障标记，无法根据回放数据判断异常是否出现或消除。</p>
      <div class="parameter-toolbar"><label for="replay-parameter">查看参数</label><el-select id="replay-parameter" v-model="selectedParameter" filterable placeholder="默认显示全部参数"><el-option label="全部参数" value="" /><el-option v-for="parameter in parameters" :key="parameter" :label="labels[parameter] || parameter" :value="parameter" /></el-select><span>{{ selectedParameter ? '图表仅显示所选参数' : '默认显示全部参数，选择参数后切换为单参数视图' }}</span></div>
      <p v-if="curve.sample_stride > 1" class="sample-note">当前窗口共 {{ curve.count }} 个原始采样点，曲线展示 {{ curve.display_count }} 个点，并保留故障标签切换位置；完整数据可在数据管理中下载。</p>
      <ReportChart v-if="parameters.length" :option="chart" /><el-empty v-else description="当前数据没有可绘制的参数" />
      <el-table :data="visibleRows.slice(-30).reverse()" stripe><el-table-column prop="time" label="时间" /><el-table-column v-if="selectedParameter" :key="selectedParameter" :prop="selectedParameter" :label="labels[selectedParameter] || selectedParameter" /><el-table-column v-for="parameter in (!selectedParameter ? parameters : [])" :key="parameter" :prop="parameter" :label="labels[parameter] || parameter" /></el-table>
    </el-card>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import ReportChart from '../components/ReportChart.vue'
const emptyCurve = () => ({ columns: [], rows: [], series: {}, parameter_columns: [], count: 0 })
const events = ref([]), eventId = ref(null), replay = ref(null), curve = ref(emptyCurve()), selectedParameter = ref(null), form = ref({ start: 0, end: 10, speed: 1 }), loading = ref(false), creating = ref(false)
const states = { paused: '已暂停', playing: '播放中', finished: '已结束' }
const labels = { pressure: '压力', temperature: '温度', bus_voltage: '母线电压', battery_capacity: '电池容量', attitude_error: '姿态误差', control_error: '控制误差', HI_norm: '健康指数', health_index: '健康指数', current: '电流', voltage: '电压' }
let timer; let controlPending = false
const selected = computed(() => events.value.find(event => event.id === eventId.value))
const parameters = computed(() => curve.value.parameter_columns || Object.keys(curve.value.series || {}))
const faultFlagColumn = computed(() => curve.value.fault_flag_column || null)
const visibleRows = computed(() => (curve.value.rows || []).filter(row => Number(row.time) <= Number(replay.value?.current_time)))
const currentSample = computed(() => visibleRows.value.at(-1) || null)
const activeWarning = computed(() => faultFlagColumn.value && Number(currentSample.value?.[faultFlagColumn.value]) === 1)
const progress = computed(() => { if (!replay.value) return 0; const span = replay.value.window_end - replay.value.window_start; return span <= 0 ? 100 : Math.min(100, Math.round((replay.value.current_time - replay.value.window_start) / span * 100)) })
const formatTime = value => Number(value ?? 0).toFixed(2)
const chart = computed(() => {
  const names = selectedParameter.value ? [selectedParameter.value] : parameters.value
  const series = names.map(parameter => ({ name: labels[parameter] || parameter, type: 'line', showSymbol: false, smooth: true, data: (curve.value.series?.[parameter] || []).filter(point => Number(point[0]) <= Number(replay.value?.current_time)) }))
  return { tooltip: { trigger: 'axis' }, legend: { type: 'scroll' }, xAxis: { type: 'value', name: '时间' }, yAxis: { type: 'value', scale: true }, series }
})
async function api(url, options = {}) { const response = await fetch(url, { credentials: 'include', headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options }); const body = await response.json(); if (!response.ok) throw Error(body.error || body.detail || `请求失败 ${response.status}`); return body }
async function loadEvents() { loading.value = true; try { events.value = (await api('/api/v1/phm/fault-events/')).results || []; if (events.value.length && !events.value.some(event => event.id === eventId.value)) { eventId.value = events.value[0].id; selectEvent() } } catch (error) { ElMessage.error(error.message) } finally { loading.value = false } }
function selectEvent() { clearInterval(timer); const event = selected.value; if (!event) return; form.value = { start: event.start_time, end: event.end_time ?? event.start_time, speed: 1 }; replay.value = null; curve.value = emptyCurve(); selectedParameter.value = null }
function updateReplay(body) { replay.value = body.replay; curve.value = body.curve; if (selectedParameter.value && !parameters.value.includes(selectedParameter.value)) selectedParameter.value = null }
async function create() { creating.value = true; clearInterval(timer); try { updateReplay(await api(`/api/v1/phm/fault-events/${eventId.value}/replays/`, { method: 'POST', body: JSON.stringify(form.value) })); startTimer(); ElMessage.success('重演数据已加载') } catch (error) { ElMessage.error(error.message) } finally { creating.value = false } }
async function control(action) { if (!replay.value || controlPending) return; controlPending = true; try { updateReplay(await api(`/api/v1/phm/fault-replays/${replay.value.id}/`, { method: 'POST', body: JSON.stringify({ action, elapsed: .5 }) })) } catch (error) { clearInterval(timer); ElMessage.error(error.message) } finally { controlPending = false } }
function startTimer() { clearInterval(timer); timer = setInterval(() => { if (replay.value?.state === 'playing') control('tick') }, 500) }
onMounted(loadEvents); onUnmounted(() => clearInterval(timer))
</script>
<style scoped>
.page{max-width:1400px}.head{display:flex;justify-content:space-between;margin-bottom:18px}.head h2{margin:0 0 8px}.head p{color:#718198;margin:0}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:16px}.stats small{display:block;color:#718198}.stats strong{display:block;font-size:26px;margin-top:6px}.stats .source{font-size:16px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.el-select{width:280px}.result{margin-top:18px}.toolbar{display:flex;align-items:center;gap:14px;flex-wrap:wrap}.progress{width:180px}.warning{margin:16px 0}.status-note,.sample-note{color:#66788f;font-size:13px}.parameter-toolbar{display:flex;align-items:center;gap:12px;margin:18px 0 12px}.parameter-toolbar label{font-weight:600}.parameter-toolbar span{color:#718198;font-size:13px}@media(max-width:800px){.stats{grid-template-columns:1fr}.head{display:block}.head .el-button{margin-top:12px}.parameter-toolbar{align-items:flex-start;flex-direction:column}}
</style>
