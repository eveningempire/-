<template>
  <div class="dashboard-page">
    <!-- 系统时间 -->
    <div class="system-time">
      <el-card class="time-card compact">
        <div class="time-display">
          <div class="current-time">{{ currentTime }}</div>
          <div class="current-date">{{ currentDate }}</div>
        </div>
      </el-card>
    </div>

    <!-- 总体统计数据和设置合并 -->
    <div class="top-section">
      <el-row :gutter="16">
        <!-- 统计数据 -->
        <el-col :span="6">
          <el-card class="stat-card compact">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Setting /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">CMG类型</div>
                <div class="stat-value">{{ cmgTypeCount }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card compact">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-label">CMG个体</div>
                <div class="stat-value">{{ cmgIndividualCount }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <!-- 数据更新设置 -->
        <el-col :span="12">
          <el-card class="settings-card compact">
            <div class="settings-content">
              <div class="settings-info">
                <div class="settings-title">数据更新设置</div>
                <div class="last-update">最后更新：{{ lastUpdateTime }}</div>
              </div>
              <div class="settings-controls">
                <el-select v-model="updateFrequency" size="small" @change="onUpdateFrequencyChange">
                  <el-option label="1分钟" value="1" />
                  <el-option label="5分钟" value="5" />
                  <el-option label="15分钟" value="15" />
                  <el-option label="30分钟" value="30" />
                  <el-option label="1小时" value="60" />
                  <el-option label="6小时" value="360" />
                  <el-option label="1天" value="1440" />
                </el-select>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="refreshData" 
                  :loading="refreshing"
                  style="margin-left: 8px;"
                >
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 大屏展示入口 -->
    <div class="bigscreen-entrance" @click="openBigScreen">
      <div class="bigscreen-content">
        <div class="bigscreen-icon">
          <el-icon :size="32"><Monitor /></el-icon>
        </div>
        <div class="bigscreen-info">
          <div class="bigscreen-title">大屏监控展示</div>
          <div class="bigscreen-desc">点击进入全屏监控模式</div>
        </div>
        <div class="bigscreen-arrow">
          <el-icon :size="24"><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <!-- CMG个体卡片 -->
    <div class="cmg-cards">
      <h3>CMG个体状态</h3>
      <el-row :gutter="16">
                 <el-col 
           :span="8" 
           v-for="cmg in cmgIndividuals" 
           :key="cmg.id"
         >
           <el-card class="cmg-card compact" :class="{ 'loading': cmg.loading }" v-loading="cmg.loading">
            <div class="cmg-card-header">
              <div class="cmg-info">
                <div class="cmg-name">{{ cmg.name }}</div>
                <div class="cmg-id">ID: {{ cmg.cmg_id }}</div>
                <div class="cmg-type">型号: {{ cmg.cmg_model_detail?.model_name || '未知' }}</div>
              </div>
              <div class="cmg-status">
                <el-tag :type="cmg.enabled ? 'success' : 'info'">
                  {{ cmg.enabled ? '启用' : '禁用' }}
                </el-tag>
              </div>
            </div>
            
            <div class="cmg-stats">
                             <div class="stat-row">
                 <div class="stat-item">
                   <div class="stat-label">数据帧总数</div>
                   <div class="stat-value">{{ formatNumber(cmg.totalFrames) }}</div>
                 </div>
                 <div class="stat-item">
                   <div class="stat-label">异常帧比例</div>
                   <div class="stat-value" :class="getAnomalyClass(cmg.anomalyRatio)">
                     {{ formatPercentage(cmg.anomalyRatio) }}
                   </div>
                 </div>
               </div>
               
               <div class="stat-row">
                 <div class="stat-item">
                   <div class="stat-label">异常帧</div>
                   <div class="stat-value">{{ formatNumber(cmg.anomalyFrames) }}</div>
                 </div>
                 <div class="stat-item">
                   <div class="stat-label">最后数据时间</div>
                   <div class="stat-value">{{ formatDateTime(cmg.lastDataTime) }}</div>
                 </div>
               </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 空状态 -->
      <div v-if="cmgIndividuals.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无CMG个体数据">
          <el-button type="primary" @click="refreshData">刷新数据</el-button>
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Setting, Monitor, Refresh, ArrowRight } from '@element-plus/icons-vue';
import api from '../api';

defineOptions({
  name: 'Dashboard'
});

const router = useRouter();

// 打开大屏展示
function openBigScreen() {
  // 🔧 修复：在新标签页中打开大屏界面（移除第三个参数）
  const bigScreenUrl = window.location.origin + '/bigscreen'
  window.open(bigScreenUrl, '_blank')
}

function openOrbitTwinDashboard() {
  const { href } = router.resolve({ name: 'OrbitTwinDashboard' });
  window.open(href, '_blank', 'noopener');
}

// 响应式数据
const currentTime = ref('');
const currentDate = ref('');
const cmgTypeCount = ref(0);
const cmgIndividualCount = ref(0);
const cmgIndividuals = ref([]);
const updateFrequency = ref('5'); // 默认5分钟
const lastUpdateTime = ref('');
const refreshing = ref(false);
const loading = ref(false);

// 定时器
let timeTimer = null;
let dataTimer = null;

// 格式化数字
function formatNumber(num) {
  if (num === null || num === undefined) return '0';
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

// 格式化百分比
function formatPercentage(ratio) {
  if (ratio === null || ratio === undefined) return '0%';
  return (ratio * 100).toFixed(2) + '%';
}

// 格式化日期时间
function formatDateTime(dateTime) {
  if (!dateTime) return '无数据';
  return new Date(dateTime).toLocaleString('zh-CN');
}

// 获取异常比例样式类
function getAnomalyClass(ratio) {
  if (ratio === null || ratio === undefined) return '';
  if (ratio > 0.1) return 'high-anomaly';
  if (ratio > 0.05) return 'medium-anomaly';
  return 'low-anomaly';
}

// 更新系统时间
function updateTime() {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString('zh-CN');
  currentDate.value = now.toLocaleDateString('zh-CN');
}

// 加载CMG类型和个体统计
async function loadOverviewStats() {
  try {
    const [cmgIndividuals] = await Promise.all([
      api.get('/data/cmgs/')
    ]);
    
    // 调试输出
    console.log('CMG个体数据:', cmgIndividuals.data);
    
    // 从CMG个体数据中提取唯一的CMG型号名称作为类型
    const uniqueModelNames = new Set();
    if (Array.isArray(cmgIndividuals.data)) {
      cmgIndividuals.data.forEach(cmg => {
        if (cmg.cmg_model_detail && cmg.cmg_model_detail.model_name) {
          uniqueModelNames.add(cmg.cmg_model_detail.model_name);
        }
      });
    }
    
    cmgTypeCount.value = uniqueModelNames.size;
    cmgIndividualCount.value = Array.isArray(cmgIndividuals.data) ? cmgIndividuals.data.length : 0;
    
    console.log('CMG类型数量:', cmgTypeCount.value);
    console.log('CMG个体数量:', cmgIndividualCount.value);
    console.log('CMG型号列表:', Array.from(uniqueModelNames));
  } catch (error) {
    console.error('加载统计数据失败:', error);
    ElMessage.error('加载统计数据失败');
  }
}

// 加载CMG个体详细数据
async function loadCmgIndividuals() {
  loading.value = true;
  try {
    const res = await api.get('/data/cmgs/');
    const cmgs = Array.isArray(res.data) ? res.data : [];
    
    if (cmgs.length === 0) {
      cmgIndividuals.value = [];
      lastUpdateTime.value = new Date().toLocaleString('zh-CN');
      return;
    }
    
    // 为每个CMG加载详细统计信息
    const cmgPromises = cmgs.map(async (cmg) => {
      const cmgData = {
        ...cmg,
        loading: true,
        totalFrames: 0,
        anomalyFrames: 0,
        anomalyRatio: 0,
        lastDataTime: null
      };
      
      try {
        // 并行获取数据帧总数和最后数据时间
        const [totalRes, dataRes, anomalyRes] = await Promise.allSettled([
          api.get('/data/data/count/', { params: { cmg_id: cmg.cmg_id } }),
          api.get('/data/data/', { params: { cmg_id: cmg.cmg_id, limit: 1 } }),
          api.get('/health/ims-results/anomaly-data/', { 
            params: { cmg_id: cmg.cmg_id, anomaly_only: 'true' } 
          })
        ]);
        
        // 处理总帧数
        if (totalRes.status === 'fulfilled') {
          cmgData.totalFrames = totalRes.value.data?.count || 0;
        } else {
          console.error(`CMG ${cmg.cmg_id} 获取总帧数失败:`, totalRes.reason);
        }
        
        // 处理最后数据时间
        if (dataRes.status === 'fulfilled' && dataRes.value.data && dataRes.value.data.length > 0) {
          cmgData.lastDataTime = dataRes.value.data[0].timestamp;
        }
        
        // 处理异常帧数量
        if (anomalyRes.status === 'fulfilled') {
          const anomalies = Array.isArray(anomalyRes.value.data) ? anomalyRes.value.data : [];
          cmgData.anomalyFrames = anomalies.length;
          cmgData.anomalyRatio = cmgData.totalFrames > 0 ? cmgData.anomalyFrames / cmgData.totalFrames : 0;
        }
        
      } catch (error) {
        console.error(`加载CMG ${cmg.cmg_id} 数据失败:`, error);
      } finally {
        cmgData.loading = false;
      }
      
      return cmgData;
    });
    
    cmgIndividuals.value = await Promise.all(cmgPromises);
    lastUpdateTime.value = new Date().toLocaleString('zh-CN');
    
  } catch (error) {
    console.error('加载CMG个体数据失败:', error);
    ElMessage.error('加载CMG个体数据失败');
    cmgIndividuals.value = [];
  } finally {
    loading.value = false;
  }
}

// 刷新数据
async function refreshData() {
  refreshing.value = true;
  try {
    await Promise.all([
      loadOverviewStats(),
      loadCmgIndividuals()
    ]);
    
    // 广播刷新事件，通知其他页面更新统计信息
    window.dispatchEvent(new CustomEvent('dashboard-refresh', {
      detail: { timestamp: new Date().toISOString() }
    }));
    
    ElMessage.success('数据刷新成功');
  } catch (error) {
    console.error('刷新数据失败:', error);
    ElMessage.error('刷新数据失败');
  } finally {
    refreshing.value = false;
  }
}

// 更新频率变化
function onUpdateFrequencyChange() {
  // 清除现有定时器
  if (dataTimer) {
    clearInterval(dataTimer);
  }
  
  // 设置新的定时器
  const minutes = parseInt(updateFrequency.value);
  if (minutes > 0) {
    dataTimer = setInterval(refreshData, minutes * 60 * 1000);
  }
}

// 查看CMG详情
function viewCmgDetail(cmg) {
  router.push({
    path: '/cmg-detail',
    query: { cmgId: cmg.cmg_id }
  });
}

// 组件挂载
onMounted(() => {
  // 初始化时间
  updateTime();
  timeTimer = setInterval(updateTime, 1000);
  
  // 加载初始数据
  refreshData();
  
  // 设置数据更新定时器
  onUpdateFrequencyChange();
});

// 组件卸载
onUnmounted(() => {
  if (timeTimer) {
    clearInterval(timeTimer);
  }
  if (dataTimer) {
    clearInterval(dataTimer);
  }
});
</script>

<style scoped>
.dashboard-page {
  padding: 0px;
  background: #f5f7fa;
  min-height: 100vh;
}

.system-time {
  margin-bottom: 8px;
}

.time-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: linear-gradient(180deg, var(--cmg-aerospace-primary), var(--cmg-primary-800));
  color: white;
  border: none;
  width: 100%;
}

.time-card.compact {
  height: auto;
}

.time-display {
  padding: 0px 0px;
}

.orbit-launch {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

.orbit-launch__button {
  min-width: 160px;
}

.current-time {
  font-size: 1.3rem;
  font-weight: bold;
  margin-bottom: 0px;
}

.current-date {
  font-size: 0.8rem;
  opacity: 0.9;
}

/* 新增顶部区域样式 */
.top-section {
  margin-bottom: 16px;
}

.stat-card {
  height: 120px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-card.compact {
  height: 80px;
}

.stat-card.compact :deep(.el-card__body) {
  padding: 8px 12px;
  height: 100%;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 20px;
}

.stat-card.compact .stat-content {
  padding: 8px 4px;
}

.stat-icon {
  font-size: 2.5rem;
  color: #409EFF;
  margin-right: 20px;
}

.stat-card.compact .stat-icon {
  font-size: 1.8rem;
  margin-right: 12px;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 1rem;
  color: #606266;
  margin-bottom: 8px;
}

.stat-card.compact .stat-label {
  font-size: 0.85rem;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #303133;
}

.stat-card.compact .stat-value {
  font-size: 1.4rem;
}

/* 设置卡片样式 */
.settings-card {
  height: 80px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.settings-card.compact :deep(.el-card__body) {
  padding: 8px 12px;
  height: 100%;
}

.settings-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 8px 4px;
}

.settings-info {
  flex: 1;
}

.settings-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.settings-controls {
  display: flex;
  align-items: center;
}

.last-update {
  font-size: 0.8rem;
  color: #909399;
}

/* 大屏展示入口样式 */
.bigscreen-entrance {
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.bigscreen-content {
  display: flex;
  align-items: center;
  padding: 20px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.bigscreen-entrance:hover .bigscreen-content {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
}

.bigscreen-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  color: white;
  margin-right: 20px;
  transition: all 0.3s ease;
}

.bigscreen-entrance:hover .bigscreen-icon {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.bigscreen-info {
  flex: 1;
}

.bigscreen-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: white;
  margin-bottom: 4px;
  letter-spacing: 0.5px;
}

.bigscreen-desc {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.85);
}

.bigscreen-arrow {
  display: flex;
  align-items: center;
  color: white;
  opacity: 0.8;
  transition: all 0.3s ease;
}

.bigscreen-entrance:hover .bigscreen-arrow {
  opacity: 1;
  transform: translateX(5px);
}

.cmg-cards h3 {
  margin-bottom: 16px;
  color: #303133;
  font-size: 1.1rem;
}

.cmg-card {
  margin-bottom: 16px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.cmg-card.compact {
  margin-bottom: 10px;
}

.cmg-card.compact :deep(.el-card__body) {
  padding: 8px;
}

.cmg-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
}

.cmg-card.loading {
  opacity: 0.7;
}

.cmg-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.cmg-card.compact .cmg-card-header {
  margin-bottom: 4px;
  padding-bottom: 4px;
}

.cmg-name {
  font-size: 1.2rem;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.cmg-card.compact .cmg-name {
  font-size: 0.9rem;
  margin-bottom: 1px;
}

.cmg-id {
  font-size: 0.9rem;
  color: #606266;
  margin-bottom: 2px;
}

.cmg-card.compact .cmg-id {
  font-size: 0.75rem;
  margin-bottom: 0px;
}

.cmg-type {
  font-size: 0.9rem;
  color: #909399;
}

.cmg-card.compact .cmg-type {
  font-size: 0.75rem;
}

.cmg-stats {
  margin-bottom: 15px;
}

.cmg-card.compact .cmg-stats {
  margin-bottom: 4px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.cmg-card.compact .stat-row {
  margin-bottom: 2px;
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-item .stat-label {
  font-size: 0.8rem;
  color: #909399;
  margin-bottom: 4px;
}

.cmg-card.compact .stat-item .stat-label {
  font-size: 0.7rem;
  margin-bottom: 1px;
}

.stat-item .stat-value {
  font-size: 1.1rem;
  font-weight: bold;
  color: #303133;
}

.cmg-card.compact .stat-item .stat-value {
  font-size: 0.85rem;
}

.stat-item .stat-value.high-anomaly {
  color: #f56c6c;
}

.stat-item .stat-value.medium-anomaly {
  color: #e6a23c;
}

.stat-item .stat-value.low-anomaly {
  color: #67c23a;
}

.cmg-actions {
  text-align: center;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.cmg-card.compact .cmg-actions {
  padding-top: 4px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .dashboard-page {
    padding: 10px;
  }
  
  .current-time {
    font-size: 2rem;
  }
  
  .stat-card {
    height: 100px;
  }
  
  .stat-icon {
    font-size: 2rem;
  }
  
  .stat-value {
    font-size: 1.5rem;
  }
  
  .settings-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .cmg-card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .stat-row {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
