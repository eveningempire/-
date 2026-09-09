<template>
  <div>
    <el-card>
      <h3>文件数据导入</h3>
      <el-form :model="form" inline>
        <el-form-item label="选择 CMG">
          <el-select v-model="form.cmg" placeholder="请选择 CMG" filterable clearable class="cmg-select" style="min-width: 360px; width: 360px; max-width: 480px;">
            <el-option
              v-for="cmg in cmgList"
              :key="cmg.id"
              :label="cmg.name + '(' + cmg.cmg_id + ')'"
              :value="cmg.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数据文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :file-list="fileList"
            :on-change="handleFileChange"
            :before-remove="beforeRemove"
            accept=".json,.csv,.ndjson,.xlsx,.xlsm,.xls"
            :limit="1"
          >
            <el-button type="primary">选择文件</el-button>
          </el-upload>
        </el-form-item>
        
        <!-- 新增：导入模式选择 -->
        <el-form-item v-if="fileList.length > 0" label="导入模式">
          <el-radio-group v-model="form.importMode" @change="handleImportModeChange">
            <el-radio label="IMPORT_AND_DETECT">导入并检测</el-radio>
            <el-radio label="IMPORT_ONLY">仅导入</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 新增：文件行数选择 -->
        <el-form-item v-if="fileList.length > 0" label="上传模式">
          <el-radio-group v-model="form.uploadMode" @change="handleUploadModeChange">
            <el-radio label="all">上传整个文件</el-radio>
            <el-radio label="partial">指定行数</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 新增：毫秒处理选项 -->
        <el-form-item v-if="fileList.length > 0" label="时间戳处理">
          <el-checkbox v-model="form.addMilliseconds">
            自动为重复时间戳添加毫秒
          </el-checkbox>
          <div style="margin-top: 4px; color: #909399; font-size: 12px;">
            勾选后，系统会自动为重复的时间戳添加毫秒级精度，确保每帧时间戳唯一
          </div>
        </el-form-item>
        
        <el-form-item v-if="form.uploadMode === 'partial' && fileList.length > 0" label="行数">
          <el-input-number 
            v-model="form.rowCount" 
            :min="1" 
            :max="1000000"
            placeholder="请输入行数"
            style="width: 200px;"
          />
          <span style="margin-left: 8px; color: #909399; font-size: 12px;">
            最大支持 1,000,000 行
          </span>
        </el-form-item>
        
        <el-form-item>
          <el-button type="success" @click="submitUpload" :loading="uploading">上传</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 处理进度卡片 -->
    <el-card v-if="activeSession" style="margin-top: 20px;">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>处理进度</span>
          <el-tag :type="getStatusTagType(activeSession.status)">
            {{ getStatusText(activeSession.status) }}
          </el-tag>
        </div>
      </template>
      
      <div class="progress-content">
        <div class="progress-info">
          <p><strong>文件:</strong> {{ activeSession.filename || '未知' }}</p>
          <p><strong>CMG:</strong> {{ activeSession.cmg_name || '未知' }}</p>
        </div>
        
        <div v-if="activeSession.detection_summary && Object.keys(activeSession.detection_summary).length > 0" class="detection-summary">
          <h4>{{ activeSession.detection_summary.import_only ? '导入摘要' : '检测摘要' }}</h4>
          
          <!-- 仅导入模式的摘要 -->
          <div v-if="activeSession.detection_summary.import_only" class="import-summary">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-statistic title="导入记录数" :value="activeSession.detection_summary.imported_records || 0" />
              </el-col>
              <el-col :span="12">
                <el-statistic title="总记录数" :value="activeSession.detection_summary.total_records || 0" />
              </el-col>
            </el-row>
            <div class="import-message">
              <el-alert
                :title="activeSession.detection_summary.message || '仅导入模式，未进行检测'"
                type="info"
                :closable="false"
                show-icon
              />
            </div>
          </div>
          
          <!-- 检测模式的摘要 -->
          <div v-else class="detection-summary-content">
            <el-row :gutter="16">
              <el-col :span="8">
                <el-statistic title="IMS检测" :value="activeSession.detection_summary.ims_evaluations || 0" />
                <el-statistic title="异常数量" :value="activeSession.detection_summary.ims_anomalies || 0" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="规则评估" :value="activeSession.detection_summary.rule_evaluations || 0" />
                <el-statistic title="规则触发" :value="activeSession.detection_summary.rule_triggers || 0" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="MSFG评估" :value="activeSession.detection_summary.msfg_evaluations || 0" />
                <el-statistic title="检测错误" :value="activeSession.detection_summary.detection_errors || 0" />
              </el-col>
            </el-row>
          </div>
        </div>
        
        <div v-if="activeSession.error_message" class="error-message">
          <el-alert
            :title="activeSession.error_message"
            type="error"
            :closable="false"
          />
        </div>
        

      </div>
    </el-card>

    <el-card style="margin-top: 20px;">
      <div style="display:flex; justify-content: space-between; align-items: center;">
        <h3>导入记录</h3>
        <div>
          <el-button size="small" type="danger" @click="clearAllSessions" :disabled="sessions.length===0">一键删除所有</el-button>
        </div>
      </div>
      <el-table :data="sessions" style="width: 100%">
        <el-table-column type="index" label="#" width="60" />
        <el-table-column label="CMG" width="160">
          <template #default="{ row }">
            {{ row.cmg_name }}
          </template>
        </el-table-column>
        <el-table-column prop="method" label="导入方式" width="100" />
        <el-table-column prop="import_mode" label="导入模式" width="120">
          <template #default="{ row }">
            <el-tag :type="row.import_mode === 'IMPORT_ONLY' ? 'info' : 'success'" size="small">
              {{ row.import_mode === 'IMPORT_ONLY' ? '仅导入' : '导入并检测' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="processing_status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.processing_status)">
              {{ getStatusText(row.processing_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="file" label="文件" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small"
              @click="watchSession(row)"
            >
              查看详情
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              @click="deleteSession(row)"
              style="margin-left:8px;"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import api from '../api';

// 为 keep-alive 添加组件名称
defineOptions({
  name: 'DataImport'
});

const form = ref({ cmg: null, uploadMode: 'all', rowCount: 1000, importMode: 'IMPORT_AND_DETECT', addMilliseconds: true });
const cmgList = ref([]);
const sessions = ref([]);
const fileList = ref([]);
const uploadRef = ref(null);
const uploading = ref(false);
const restarting = ref(false);

// 进度相关
const activeSession = ref(null);
const progressSocket = ref(null);

// Load list of CMGs for the select component
async function loadCmgs() {
  const res = await api.get('/data/cmgs/');
  cmgList.value = res.data;
}

// Load import sessions and attach CMG names for display
async function loadSessions() {
  const res = await api.get('/data/import-sessions/');
  const cmgMap = {};
  cmgList.value.forEach(item => {
    cmgMap[item.id] = item.name + '(' + item.cmg_id + ')';
  });
  sessions.value = (Array.isArray(res.data)? res.data : (res.data?.results||[])).map(s => ({
    ...s,
    cmg_name: cmgMap[s.cmg] || s.cmg
  }));
}

const handleFileChange = (file, files) => {
  fileList.value = files;
  // 当选择文件时，重置上传模式为默认值
  if (files.length > 0) {
    form.value.uploadMode = 'all';
    form.value.rowCount = 1000;
    form.value.importMode = 'IMPORT_AND_DETECT';
    form.value.addMilliseconds = true;
  }
};

const handleUploadModeChange = (value) => {
  if (value === 'partial' && !form.value.rowCount) {
    form.value.rowCount = 1000;
  }
};

const handleImportModeChange = (value) => {
  // 导入模式变化时的处理逻辑
  console.log('导入模式已更改为:', value);
};

const beforeRemove = () => {
  return true;
};

async function submitUpload() {
  if (!form.value.cmg || fileList.value.length === 0) {
    ElMessage.warning('请选择 CMG 并选择文件');
    return;
  }
  
  // 验证行数输入
  if (form.value.uploadMode === 'partial') {
    if (!form.value.rowCount || form.value.rowCount < 1) {
      ElMessage.warning('请输入有效的行数');
      return;
    }
    if (form.value.rowCount > 1000000) {
      ElMessage.warning('行数不能超过 1,000,000');
      return;
    }
  }
  
  uploading.value = true;
  const fd = new FormData();
  fd.append('cmg', form.value.cmg);
  fd.append('method', 'FILE');
  fd.append('file', fileList.value[0].raw);
  
  // 添加行数参数
  if (form.value.uploadMode === 'partial') {
    fd.append('max_rows', form.value.rowCount);
  }
  
  // 添加导入模式参数
  fd.append('import_mode', form.value.importMode);
  
  // 添加毫秒处理参数
  fd.append('add_milliseconds', form.value.addMilliseconds);
  
  try {
    const response = await api.post('/data/import-sessions/', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    const uploadModeText = form.value.uploadMode === 'partial' 
      ? `前 ${form.value.rowCount} 行` 
      : '整个文件';
    const importModeText = form.value.importMode === 'IMPORT_ONLY' ? '仅导入' : '导入并检测';
    ElMessage.success(`文件上传成功，将${importModeText}${uploadModeText}，正在处理...`);
    fileList.value = [];
    
    // 开始监控新创建的会话
    const newSession = response.data;
    if (newSession && newSession.id) {
      watchSession(newSession);
    }
    
    await loadSessions();
  } catch (e) {
    ElMessage.error('导入失败: ' + (e.response?.data?.detail || e.message));
  } finally {
    uploading.value = false;
  }
}

// WebSocket连接管理
function connectProgressSocket(sessionId) {
  if (progressSocket.value) {
    progressSocket.value.close();
  }
  
  const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const isViteDev = window.location.hostname === 'localhost' && window.location.port === '5173';
  const wsHost = isViteDev ? `${window.location.hostname}:8000` : window.location.host;
  const wsUrl = `${wsProtocol}://${wsHost}/ws/import-progress/${sessionId}/`;
  progressSocket.value = new WebSocket(wsUrl);
  
  progressSocket.value.onopen = () => {
    console.log(`Connected to progress stream for session ${sessionId}`);
  };
  
  progressSocket.value.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleProgressMessage(data);
  };
  
  progressSocket.value.onclose = () => {
    console.log('Progress WebSocket connection closed');
    // 若仍在处理阶段，尝试重连
    try {
      if (activeSession.value && ['PENDING','PARSING','STORING','DETECTING'].includes(activeSession.value.status)) {
        setTimeout(() => connectProgressSocket(sessionId), 1500);
      }
    } catch (_) {}
  };
  
  progressSocket.value.onerror = (error) => {
    console.error('Progress WebSocket error:', error);
  };
}

function handleProgressMessage(data) {
  switch (data.type) {
    case 'connection_established':
      console.log('Progress connection established');
      break;
    case 'status_update':
      if (activeSession.value && activeSession.value.id === data.session_id) {
        Object.assign(activeSession.value, {
          status: data.status,
          progress: data.progress,
          total_records: data.total_records,
          processed_records: data.processed_records,
          failed_records: data.failed_records,
          error_message: data.error_message,
          detection_summary: data.detection_summary
        });
      }
      break;
    case 'processing_complete':
      if (activeSession.value && activeSession.value.id === data.session_id) {
        activeSession.value.status = 'COMPLETED';
        activeSession.value.detection_summary = data.summary;
        ElMessage.success('文件处理完成！');
      }
      loadSessions(); // 刷新会话列表
      break;
  }
}

// 状态相关函数
function getStatusText(status) {
  const statusMap = {
    'PENDING': '待处理',
    'PARSING': '解析中',
    'STORING': '存储中',
    'DETECTING': '检测中',
    'COMPLETED': '已完成',
    'FAILED': '失败'
  };
  return statusMap[status] || status;
}

function getStatusTagType(status) {
  const typeMap = {
    'PENDING': 'info',
    'PARSING': 'warning',
    'STORING': 'warning',
    'DETECTING': 'warning',
    'COMPLETED': 'success',
    'FAILED': 'danger'
  };
  return typeMap[status] || 'info';
}


// 会话操作函数
async function watchSession(session) {
  activeSession.value = {
    ...session,
    cmg_name: session.cmg_name || getCmgName(session.cmg),
    filename: session.file ? session.file.split('/').pop() : '未知文件'
  };
  
  // 连接WebSocket监控进度
  connectProgressSocket(session.id);
  
  // 获取最新状态
  try {
    const response = await api.get(`/data/import-sessions/${session.id}/status/`);
    Object.assign(activeSession.value, response.data);
  } catch (error) {
    console.error('获取会话状态失败:', error);
  }
}

async function restartProcessing() {
  if (!activeSession.value) return;
  
  restarting.value = true;
  try {
    await api.post(`/data/import-sessions/${activeSession.value.id}/restart/`);
    ElMessage.success('重新开始处理');
    
    // 重置状态并重新连接WebSocket
    activeSession.value.status = 'PENDING';
    activeSession.value.error_message = null;
    connectProgressSocket(activeSession.value.id);
    
  } catch (error) {
    ElMessage.error('重启失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    restarting.value = false;
  }
}

function viewResults() {
  // 这里可以跳转到结果查看页面
  ElMessage.info('查看结果功能待实现');
}

function getCmgName(cmgId) {
  const cmg = cmgList.value.find(c => c.id === cmgId);
  return cmg ? `${cmg.name}(${cmg.cmg_id})` : '未知CMG';
}

onMounted(async () => {
  await loadCmgs();
  await loadSessions();
});

onUnmounted(() => {
  if (progressSocket.value) {
    progressSocket.value.close();
  }
});

// 删除记录
async function deleteSession(row){
  try{
    await api.delete(`/data/import-sessions/${row.id}/`);
    ElMessage.success('已删除');
    if(activeSession.value && activeSession.value.id===row.id){
      activeSession.value=null;
    }
    await loadSessions();
  }catch(e){ ElMessage.error('删除失败'); }
}

async function clearAllSessions(){
  try{
    const ids = sessions.value.map(s=>s.id);
    await Promise.all(ids.map(id=>api.delete(`/data/import-sessions/${id}/`)));
    ElMessage.success('已清空');
    activeSession.value=null;
    await loadSessions();
  }catch(e){ ElMessage.error('清空失败'); }
}
</script>

<style scoped>
.progress-content {
  padding: 16px 0;
}

.progress-info {
  margin-bottom: 20px;
}

.progress-info p {
  margin: 8px 0;
  color: #606266;
}

.detection-summary {
  margin: 20px 0;
  padding: 16px;
  background-color: #fafafa;
  border-radius: 6px;
}

.detection-summary h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.import-summary {
  margin-bottom: 16px;
}

.import-message {
  margin-top: 16px;
}

.detection-summary-content {
  margin-bottom: 16px;
}

.error-message {
  margin: 20px 0;
}

.el-statistic {
  text-align: center;
}

.el-progress {
  margin: 16px 0;
}

/* CMG选择框样式已由全局样式统一处理 */
</style>