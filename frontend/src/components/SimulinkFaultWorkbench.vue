<template>
  <div class="workbench">
    <header class="heading">
      <h1>{{ mode === 'realtime' ? '实时故障注入' : '离线故障数据集生成' }}</h1>
      <div class="runtime">
        <el-tag :type="runtime.available ? 'success' : 'warning'">{{ runtime.available ? 'Engine 已配置' : 'Engine 未就绪' }}</el-tag>
        <span>rocket_sim · {{ runtime.matlab_release || 'R2023a' }} · 480 s</span>
        <el-tooltip content="刷新运行环境"><el-button :icon="Refresh" circle aria-label="刷新运行环境" @click="loadCatalog" /></el-tooltip>
      </div>
    </header>
    <el-alert v-if="runtime.error" :title="runtime.error" type="warning" :closable="false" show-icon class="runtime-error" />
    <el-alert v-else-if="runtime.compatibility_warning" :title="runtime.compatibility_warning" type="warning" :closable="false" show-icon class="runtime-error" />

    <section class="configuration">
      <h2>注入参数</h2>
      <el-form label-position="top" class="parameter-form">
        <el-form-item label="任务名称"><el-input v-model="form.name" maxlength="200" placeholder="动力故障仿真" /></el-form-item>
        <el-form-item label="子系统">
          <el-select v-model="form.subsystem" @change="changeSubsystem"><el-option v-for="(_, subsystem) in options" :key="subsystem" :label="subsystem" :value="subsystem" /></el-select>
        </el-form-item>
        <el-form-item label="故障类型">
          <el-select v-model="form.fault_mode"><el-option v-for="fault in options[form.subsystem] || []" :key="fault" :label="fault" :value="fault" /></el-select>
        </el-form-item>
        <el-form-item label="注入时刻 (s)"><el-input-number v-model="form.injection_time" :min="0" :max="479.99" :precision="2" controls-position="right" /></el-form-item>
        <el-form-item label="恢复时刻 (s)"><el-input-number v-model="form.end_time" :min="0.01" :max="480" :precision="2" controls-position="right" /></el-form-item>
        <el-form-item label="飞行次数"><el-input-number v-model="form.flight_count" :min="0" :max="20" :precision="0" controls-position="right" /></el-form-item>
      </el-form>
      <div class="commands">
        <el-button :icon="DocumentAdd" :loading="saving" :disabled="!canSubmit || starting" @click="createTask">保存任务</el-button>
        <el-button type="primary" :icon="VideoPlay" :loading="saving || starting" :disabled="!canSubmit || !runtime.available || busy" @click="createAndRun">提交仿真</el-button>
      </div>
    </section>

    <section class="task-section">
      <div class="section-heading">
        <h2>仿真任务</h2>
        <el-select :model-value="task?.id" :disabled="saving || starting" placeholder="选择任务" class="task-select" @change="selectTask">
          <el-option v-for="item in history" :key="item.id" :value="item.id" :label="`${item.name} · ${statusLabel(item.status)}`" />
        </el-select>
      </div>
      <el-empty v-if="!task" description="暂无仿真任务" :image-size="64" />
      <template v-else>
        <div class="task-summary">
          <strong>{{ task.name }}</strong>
          <el-tag :type="task.status === 'failed' ? 'danger' : task.status === 'completed' ? 'success' : 'info'">{{ statusLabel(task.status) }}</el-tag>
          <span>{{ task.subsystem }} / {{ task.fault_mode }}</span>
          <span>{{ task.injection_time }}–{{ task.end_time }} s</span>
          <span>飞行次数 {{ task.flight_count }}</span>
          <el-button v-if="['ready', 'failed'].includes(task.status) && task.simulation_backend === 'simulink'" :icon="VideoPlay" :disabled="!runtime.available || !canSubmit || saving" :loading="starting" @click="startTask">{{ task.status === 'failed' ? '重试' : '启动' }}</el-button>
        </div>
        <el-steps :active="stageIndex" :process-status="task.status === 'failed' ? 'error' : 'process'" finish-status="success" align-center>
          <el-step title="排队" /><el-step title="启动引擎" /><el-step title="配置模型" /><el-step title="求解" /><el-step title="导出 CSV" /><el-step title="登记数据集" />
        </el-steps>
        <el-alert v-if="task.latest_result?.error" :title="task.latest_result.error" type="error" :closable="false" show-icon />
        <el-alert v-if="pollError" :title="pollError" type="warning" :closable="false" show-icon />
        <div v-if="busy" class="running-state"><el-icon class="is-loading"><Loading /></el-icon><span>{{ stageLabel }}...</span></div>
      </template>
    </section>

    <section v-if="outputs.length" class="outputs">
      <div class="section-heading"><h2>仿真输出</h2><div class="result-links"><router-link to="/data-management">数据管理</router-link><router-link to="/fault-replay">故障回放</router-link><router-link to="/fault-diagnosis">故障诊断</router-link></div></div>
      <el-table :data="outputs">
        <el-table-column prop="component" label="输出类型" min-width="120" />
        <el-table-column prop="dataset_id" label="数据集 ID" width="110" />
        <el-table-column prop="row_count" label="样本数" width="110" />
        <el-table-column prop="fault_row_count" label="故障标记样本数" min-width="150" />
        <el-table-column label="参数数" width="90"><template #default="scope">{{ scope.row.parameter_columns.length }}</template></el-table-column>
        <el-table-column label="文件" min-width="170"><template #default="scope"><a class="download" :href="scope.row.url" download><el-icon><Download /></el-icon>{{ scope.row.component === '原始状态量' ? 'scope_data.csv' : 'P_values.csv' }}</a></template></el-table-column>
      </el-table>
      <div class="preview-controls">
        <el-radio-group v-model="outputIndex"><el-radio-button v-for="(output, index) in outputs" :key="output.dataset_id" :label="index" :value="index">{{ output.component }}</el-radio-button></el-radio-group>
        <el-select v-model="signals" multiple collapse-tags collapse-tags-tooltip :multiple-limit="4" placeholder="参数" class="signal-select"><el-option v-for="key in activeOutput?.parameter_columns || []" :key="key" :label="key" :value="key" /></el-select>
        <span>{{ activeOutput?.time_range?.[0] }}–{{ activeOutput?.time_range?.[1] }} s</span>
      </div>
      <ReportChart :option="chart" />
      <el-table :data="activeOutput?.preview?.slice(-12) || []" class="preview-table">
        <el-table-column prop="Time" label="Time (s)" min-width="120" />
        <el-table-column prop="FaultFlag" label="FaultFlag · 真值" min-width="150" />
        <el-table-column v-for="key in signals" :key="key" :prop="key" :label="key" min-width="140"><template #default="scope">{{ number(scope.row[key]) }}</template></el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { DocumentAdd, Download, Loading, Refresh, VideoPlay } from '@element-plus/icons-vue'
import ReportChart from './ReportChart.vue'

const props = defineProps({ mode: { type: String, default: 'offline' } })
const options = ref({}), runtime = ref({ available: false }), canSubmit = ref(false)
const form = ref({ name: '', subsystem: '动力', fault_mode: '泵气蚀', injection_time: 40, end_time: 480, flight_count: 0 })
const task = ref(null), history = ref([]), saving = ref(false), starting = ref(false), pollError = ref('')
const outputIndex = ref(0), signals = ref([])
const key = `simulink-task-${props.mode}`
let timer, disposed = false, selection = 0
const busy = computed(() => ['queued', 'running'].includes(task.value?.status))
const outputs = computed(() => task.value?.simulation_output?.datasets || [])
const activeOutput = computed(() => outputs.value[outputIndex.value])
const stageOrder = ['queued', 'starting_engine', 'configuring', 'solving', 'exporting', 'registering', 'completed']
const stageIndex = computed(() => Math.max(0, stageOrder.indexOf(task.value?.current_stage)))
const stageLabel = computed(() => ({ queued: '等待执行', starting_engine: '启动 MATLAB', configuring: '配置故障块', solving: 'Simulink 求解中', exporting: '导出结果', registering: '登记数据集' }[task.value?.current_stage] || '运行中'))
const statusLabel = status => ({ ready: '待启动', queued: '已排队', running: '运行中', completed: '已完成', failed: '失败' }[status] || status)
const number = value => typeof value === 'number' ? Number(value.toPrecision(7)) : value
const chart = computed(() => ({
  legend: { data: signals.value, top: 10, bottom: 'auto' },
  xAxis: { type: 'value', name: 'Time (s)', nameLocation: 'middle', nameGap: 30 }, yAxis: { type: 'value', scale: true },
  series: signals.value.map(name => ({ name, type: 'line', data: (activeOutput.value?.preview || []).map(row => [row.Time, row[name]]) })),
}))
watch(activeOutput, output => { signals.value = (output?.parameter_columns || []).slice(0, 2) })
async function request(path, body) {
  const response = await fetch(`/api/v1/simulation-demo/${path}`, body === undefined ? {} : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  const result = await response.json()
  if (!response.ok) { if (result.task) acceptTask(result.task); throw new Error(result.error || '请求失败') }
  return result
}
function acceptTask(value) {
  task.value = value
  localStorage.setItem(key, value.id)
  history.value = [value, ...history.value.filter(item => item.id !== value.id)]
}
function changeSubsystem() { form.value.fault_mode = options.value[form.value.subsystem]?.[1] || '无故障' }
async function loadCatalog() {
  try {
    const result = await request('sample/')
    options.value = result.subsystems; runtime.value = result.runtime; canSubmit.value = result.can_submit
  } catch (error) { ElMessage.error(error.message) }
}
async function createTask() {
  if (form.value.injection_time == null || form.value.end_time == null || form.value.injection_time >= form.value.end_time) {
    ElMessage.error('恢复时刻必须晚于注入时刻'); return false
  }
  saving.value = true
  try {
    clearTimeout(timer); selection++
    const result = await request('workflows/', { ...form.value, mode: props.mode, simulation_backend: 'simulink' })
    acceptTask(result.task); outputIndex.value = 0; pollError.value = ''
    return true
  } catch (error) { ElMessage.error(error.message); return false }
  finally { saving.value = false }
}
async function createAndRun() { if (!saving.value && !starting.value && await createTask()) await startTask() }
async function startTask() {
  if (!task.value || starting.value || saving.value) return
  starting.value = true
  try { const result = await request(`workflows/${task.value.id}/generate/`, {}); acceptTask(result.task); pollError.value = ''; schedulePoll() }
  catch (error) { ElMessage.error(error.message) }
  finally { starting.value = false }
}
function schedulePoll() { clearTimeout(timer); if (!disposed && busy.value) timer = setTimeout(poll, 1500) }
async function poll() {
  const id = task.value?.id, version = selection
  try {
    const result = await request(`workflows/${id}/`)
    if (disposed || selection !== version) return
    acceptTask(result.task); pollError.value = ''
  } catch (error) { if (selection === version) pollError.value = error.message }
  schedulePoll()
}
async function selectTask(id) {
  selection++; clearTimeout(timer); pollError.value = ''; outputIndex.value = 0
  try { acceptTask((await request(`workflows/${id}/`)).task); schedulePoll() }
  catch (error) { ElMessage.error(error.message) }
}
onMounted(async () => {
  await loadCatalog()
  try {
    history.value = (await request('workflows/')).results.filter(item => item.simulation_backend === 'simulink' && item.mode === props.mode)
    const saved = localStorage.getItem(key)
    const id = history.value.find(item => item.id === saved)?.id || history.value[0]?.id
    if (id) await selectTask(id)
  } catch (error) { ElMessage.error(error.message) }
})
onBeforeUnmount(() => { disposed = true; selection++; clearTimeout(timer) })
</script>

<style scoped>
.workbench{max-width:1400px;width:100%;min-width:0}.heading,.section-heading{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}.heading h1{font-size:24px;margin:0}.runtime{display:flex;gap:12px;align-items:center;flex-wrap:wrap;font-size:13px;color:#65717d}.runtime-error{margin-top:20px}.configuration,.task-section,.outputs{padding:24px 0;border-bottom:1px solid #dfe5ea}h2{font-size:17px;margin:0 0 20px}.section-heading h2{margin:0}.section-heading{margin-bottom:20px}.parameter-form{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0 20px}.parameter-form :deep(.el-select),.parameter-form :deep(.el-input-number){width:100%}.commands{display:flex;gap:8px}.task-select{width:min(420px,100%)}.task-summary{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-bottom:24px;font-size:14px}.task-summary strong{overflow-wrap:anywhere}.task-section :deep(.el-steps){margin-bottom:22px}.running-state{display:flex;gap:10px;align-items:center;color:#497a9c;padding:12px 0}.result-links{display:flex;gap:18px;font-size:14px}.result-links a,.download{color:#2473a9;text-decoration:none}.download{display:inline-flex;align-items:center;gap:6px}.preview-controls{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:24px 0 16px}.signal-select{width:280px;max-width:100%}.preview-controls>span{font-size:13px;color:#65717d}.preview-table{margin-top:18px}.workbench :deep(.el-alert__title){overflow-wrap:anywhere}.workbench :deep(.el-alert__content){min-width:0}
@media(max-width:850px){.parameter-form{grid-template-columns:repeat(2,minmax(0,1fr))}.heading h1{font-size:22px}.task-summary{gap:10px}.result-links{gap:12px}.task-section :deep(.el-step__title){font-size:12px}}
@media(max-width:500px){.parameter-form{grid-template-columns:minmax(0,1fr)}.runtime{gap:8px}.task-section :deep(.el-step__title){font-size:11px;line-height:18px}.task-select{width:100%}.preview-controls{gap:12px}}
</style>
