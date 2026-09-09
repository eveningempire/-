<template>
  <div class="page">
    <el-card class="section">
      <div class="card-header">
        <div class="title">网络传输设置</div>
        <div class="sub">配置 TCP 实时接收的监听参数与接收对象</div>
      </div>
      <el-form :model="form" label-width="90px" class="form-grid">
        <el-form-item label="监听地址">
          <el-input v-model="form.host" placeholder="0.0.0.0" style="width: 200px;" />
        </el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="form.port" :min="1" :max="65535" />
        </el-form-item>
        <div class="actions">
          <el-button type="primary" @click="start">启动</el-button>
          <el-button type="danger" @click="stop">停止</el-button>
          <el-button @click="refresh">刷新状态</el-button>
        </div>
      </el-form>
      <el-alert :title="`当前状态：${statusText}`" type="info" show-icon :closable="false" style="margin-top: 8px;" />
    </el-card>

    <el-card class="section">
      <div class="card-header">
        <div class="title">接收对象</div>
        <div class="sub">选择需要接收的 CMG 个体（可多选）</div>
      </div>
      <el-select v-model="selectedCmgs" multiple filterable collapse-tags placeholder="选择要接收的 CMG" style="width: 520px;">
        <el-option v-for="c in cmgList" :key="c.id" :label="c.name + '(' + c.cmg_id + ')'" :value="c.cmg_id" />
      </el-select>
      <div class="hint">注：发送端应使用上述 cmg_id 字段，接收端将按 cmg_id 直接入库到对应个体。</div>
    </el-card>

    <el-card class="section">
      <div class="card-header">
        <div class="title">发送端 ID 映射（可选）</div>
        <div class="sub">当发送端使用的 cmg_id 与平台中的 cmg_id 不一致时，可以配置映射表</div>
      </div>
      <div v-for="(m, idx) in idMapRows" :key="idx" class="map-row">
        <el-input v-model="m.sender" placeholder="发送端ID" style="width: 220px;" />
        <span style="margin: 0 8px;">→</span>
        <el-select v-model="m.platform" placeholder="平台CMG" style="width: 260px;">
          <el-option v-for="c in cmgList" :key="c.id" :label="c.name + '(' + c.cmg_id + ')'" :value="c.cmg_id" />
        </el-select>
        <el-button size="small" @click="removeMap(idx)" style="margin-left:8px;">移除</el-button>
      </div>
      <el-button size="small" @click="addMap" style="margin-top:8px;">新增映射</el-button>
    </el-card>

    <el-card class="section">
      <div class="card-header with-action">
        <div class="title">实时事件</div>
        <el-button size="small" @click="pullEvents">刷新</el-button>
      </div>
      <el-scrollbar height="220px">
        <div v-for="(e,i) in events" :key="i" class="event-line">{{ e }}</div>
      </el-scrollbar>
    </el-card>

    <el-card class="section">
      <div class="card-header with-action">
        <div class="title">统计</div>
        <el-button size="small" @click="pullMetrics">刷新</el-button>
      </div>
      <div>
        <div>累计批次：{{ metrics.total_batches || 0 }}</div>
        <div>累计帧数：{{ metrics.total_frames || 0 }}</div>
        <div style="margin-top:6px;">按 CMG：</div>
        <el-table :data="metricsRows" size="small" style="width: 100%;">
          <el-table-column prop="cmg_id" label="CMG" width="200" />
          <el-table-column prop="batches" label="批次" width="120" />
          <el-table-column prop="frames" label="帧数" width="120" />
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import api from '../api';

// 为 keep-alive 添加组件名称
defineOptions({
  name: 'TcpIngest'
});

const form = ref({ host: '0.0.0.0', port: 9000 });
const status = ref({ running: false, host: '', port: 0 });
const cmgList = ref([]);
const selectedCmgs = ref([]);
const events = ref([]);
const metrics = ref({ total_batches: 0, total_frames: 0, by_cmg: {} });
const metricsRows = computed(() => Object.entries(metrics.value.by_cmg || {}).map(([cmg_id, v]) => ({ cmg_id, ...v })));
const idMapRows = ref([]); // { sender, platform }

const statusText = computed(() => status.value.running ? `运行中 (${status.value.host}:${status.value.port})` : '已停止');

async function refresh() {
  const res = await api.get('/data/tcp-ingest/status/');
  status.value = res.data;
}

async function start() {
  try {
    const id_map = {};
    idMapRows.value.forEach(m => { if (m.sender && m.platform) id_map[m.sender] = m.platform; });
    const payload = { ...form.value, allowed_cmg_ids: selectedCmgs.value, id_map };
    const res = await api.post('/data/tcp-ingest/start/', payload);
    status.value = res.data;
    ElMessage.success('已启动 TCP 接收');
    pullEvents();
  } catch (e) {
    ElMessage.error('启动失败');
  }
}

async function stop() {
  try {
    const res = await api.post('/data/tcp-ingest/stop/');
    status.value = res.data;
    ElMessage.success('已停止 TCP 接收');
  } catch (e) {
    ElMessage.error('停止失败');
  }
}

async function loadCmgs() {
  const res = await api.get('/data/cmgs/');
  cmgList.value = Array.isArray(res.data) ? res.data : [];
}

async function pullEvents() {
  const res = await api.get('/data/tcp-ingest/events/');
  events.value = res.data.events || [];
}

async function pullMetrics() {
  const res = await api.get('/data/tcp-ingest/metrics/');
  metrics.value = res.data || { total_batches: 0, total_frames: 0, by_cmg: {} };
}

onMounted(async () => {
  await Promise.all([refresh(), loadCmgs(), pullEvents(), pullMetrics()]);
});

function addMap() { idMapRows.value.push({ sender: '', platform: '' }); }
function removeMap(i) { idMapRows.value.splice(i, 1); }
</script>

<style scoped>
.page { padding: 12px; }
.section { margin-top: 12px; }
.card-header { display: flex; flex-direction: column; margin-bottom: 10px; }
.card-header.with-action { flex-direction: row; align-items: center; justify-content: space-between; }
.title { font-weight: 600; font-size: 16px; color: #303133; }
.sub { color: #909399; font-size: 12px; margin-top: 4px; }
.form-grid { display: grid; grid-template-columns: repeat(3, max-content); gap: 12px 16px; align-items: end; }
.actions { display: flex; gap: 8px; }
.hint { color: #888; margin-top: 8px; }
.map-row { display: flex; align-items: center; margin-top: 8px; }
.event-line { padding: 6px 8px; border-bottom: 1px dashed #ebeef5; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 12px; line-height: 18px; }
</style>
