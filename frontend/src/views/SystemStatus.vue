<template>
  <div class="system-status">
    <el-card class="status-card">
      <template #header>
        <div class="card-header">
          <span>系统状态监控</span>
          <el-button @click="refreshStatus" :loading="loading" size="small">
            刷新状态
          </el-button>
        </div>
      </template>

      <!-- 总体状态 -->
      <el-row :gutter="16" class="status-overview">
        <el-col :span="6">
          <el-statistic title="系统状态" :value="overallStatusValue" :value-style="hiddenNumberStyle">
            <template #suffix>
              <span :style="overallStatusStyle" style="margin-right:6px;">{{ overallStatus }}</span>
              <el-icon :style="{ color: overallStatusColor }">
                <CircleCheck v-if="overallStatus === '正常'" />
                <Warning v-else />
              </el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="WebSocket连接" :value="wsStatusValue" :value-style="hiddenNumberStyle">
            <template #suffix>
              <span :style="wsStatusStyle" style="margin-right:6px;">{{ wsStatus }}</span>
              <el-icon :style="{ color: wsStatusColor }">
                <Connection v-if="wsStatus === '已连接'" />
                <Close v-else />
              </el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="Redis连接" :value="redisStatusValue" :value-style="hiddenNumberStyle">
            <template #suffix>
              <span :style="redisStatusStyle" style="margin-right:6px;">{{ redisStatus }}</span>
              <el-icon :style="{ color: redisStatusColor }">
                <CircleCheck v-if="redisStatus === '正常'" />
                <Close v-else />
              </el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="缓存命中率" :value="cacheHitRate" suffix="%" :precision="1" />
        </el-col>
      </el-row>

      <el-divider />

      <!-- 详细状态信息 -->
      <el-row :gutter="16">
        <!-- Redis状态 -->
        <el-col :span="12">
          <el-card class="detail-card">
            <template #header>
              <span>Redis缓存状态</span>
            </template>
            <div v-if="cacheStats.redis_cache">
              <el-descriptions :column="1" size="small">
                <el-descriptions-item label="连接状态">
                  <el-tag :type="cacheStats.redis_cache.redis_connected ? 'success' : 'danger'">
                    {{ cacheStats.redis_cache.redis_connected ? '已连接' : '断开' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="内存使用">
                  {{ cacheStats.redis_cache.memory_used || '0B' }}
                </el-descriptions-item>
                <el-descriptions-item label="峰值内存">
                  {{ cacheStats.redis_cache.memory_peak || '0B' }}
                </el-descriptions-item>
                <el-descriptions-item label="缓存键数量">
                  <el-tag>{{ cacheStats.redis_cache.keys_count?.total || 0 }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="运行时间">
                  {{ formatUptime(cacheStats.redis_cache.uptime_seconds) }}
                </el-descriptions-item>
              </el-descriptions>
              
              <!-- 缓存键分布 -->
              <div class="cache-breakdown" v-if="cacheStats.redis_cache.keys_count">
                <h4>缓存键分布</h4>
                <el-row :gutter="8">
                  <el-col :span="12">
                    <el-statistic title="实时数据" :value="cacheStats.redis_cache.keys_count.realtime_data || 0" />
                  </el-col>
                  <el-col :span="12">
                    <el-statistic title="查询缓存" :value="cacheStats.redis_cache.keys_count.query_cache || 0" />
                  </el-col>
                </el-row>
              </div>
            </div>
            <div v-else class="no-data">无法获取Redis状态</div>
          </el-card>
        </el-col>

        <!-- 内存缓存状态 -->
        <el-col :span="12">
          <el-card class="detail-card">
            <template #header>
              <span>内存缓存状态</span>
            </template>
            <div v-if="cacheStats.memory_cache">
              <el-descriptions :column="1" size="small">
                <el-descriptions-item label="CMG数量">
                  {{ cacheStats.memory_cache.total?.cmg_count || 0 }}
                </el-descriptions-item>
                <el-descriptions-item label="数据点总数">
                  {{ cacheStats.memory_cache.total?.total_data_points || 0 }}
                </el-descriptions-item>
                <el-descriptions-item label="内存使用估算">
                  {{ (cacheStats.memory_cache.total?.memory_usage_mb || 0).toFixed(2) }} MB
                </el-descriptions-item>
              </el-descriptions>

              <!-- CMG详细状态 -->
              <div v-if="Object.keys(cacheStats.memory_cache).length > 1" class="cmg-details">
                <h4>CMG缓存详情</h4>
                <el-table :data="memoryeCacheDetails" size="small" max-height="200">
                  <el-table-column prop="cmg_id" label="CMG ID" width="120" />
                  <el-table-column prop="data_points" label="数据点数" width="100" />
                  <el-table-column prop="latest_time" label="最新时间" min-width="150" />
                </el-table>
              </div>
            </div>
            <div v-else class="no-data">无法获取内存缓存状态</div>
          </el-card>
        </el-col>
      </el-row>

      <el-divider />

      <!-- WebSocket状态 -->
      <el-row>
        <el-col :span="24">
          <el-card class="detail-card">
            <template #header>
              <span>WebSocket连接状态</span>
            </template>
            <div class="ws-status">
              <el-descriptions :column="2" size="small">
                <el-descriptions-item label="连接状态">
                  <el-tag :type="wsConnected ? 'success' : 'info'">
                    {{ wsConnected ? '已连接' : '未连接' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="连接地址">
                  {{ wsUrl || '未设置' }}
                </el-descriptions-item>
                <el-descriptions-item label="重连次数">
                  {{ wsReconnectAttempts }}
                </el-descriptions-item>
                <el-descriptions-item label="连接中">
                  <el-tag :type="wsConnecting ? 'warning' : 'info'">
                    {{ wsConnecting ? '是' : '否' }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>

              <div class="ws-actions">
                <el-button @click="testWebSocket" :loading="wsConnecting" size="small">
                  测试连接
                </el-button>
                <el-button @click="disconnectWebSocket" :disabled="!wsConnected" size="small">
                  断开连接
                </el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 系统配置管理 -->
      <el-divider />
      <el-card class="config-card">
        <template #header>
          <div class="card-header">
            <span>系统配置管理</span>
            <div>
              <el-button @click="resetConfig" type="warning" size="small" style="margin-right: 8px;">
                重置默认
              </el-button>
              <el-button @click="saveConfig" type="primary" size="small" :loading="configSaving">
                保存配置
              </el-button>
            </div>
          </div>
        </template>

        <el-form :model="systemConfig" label-width="200px" size="small">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="流式处理触发阈值">
                <el-input-number 
                  v-model="systemConfig.streaming_threshold" 
                  :min="100" 
                  :max="1000000"
                  :step="1000"
                  style="width: 100%"
                />
                <div class="config-description">
                  当数据帧数超过此阈值时，启用流式处理模式（帧数，范围：100-1,000,000）
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="每批处理帧数">
                <el-input-number 
                  v-model="systemConfig.batch_size" 
                  :min="50" 
                  :max="50000"
                  :step="100"
                  style="width: 100%"
                />
                <div class="config-description">
                  流式处理时每批处理的数据帧数（范围：50-50,000）
                </div>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="批量保存批次大小">
                <el-input-number 
                  v-model="systemConfig.batch_size_for_save" 
                  :min="100" 
                  :max="50000"
                  :step="500"
                  style="width: 100%"
                />
                <div class="config-description">
                  批量保存数据时的批次大小（范围：100-50,000）
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </el-card>

      <!-- 检测频率控制设置 -->
      <el-divider />
      <el-card class="config-card">
        <template #header>
          <div class="card-header">
            <span>检测频率控制设置</span>
            <div>
              <el-button @click="testDetectionFrequency" type="info" size="small" style="margin-right: 8px;">
                测试配置
              </el-button>
              <el-button @click="resetDetectionConfig" type="warning" size="small" style="margin-right: 8px;">
                重置默认
              </el-button>
              <el-button @click="saveDetectionConfig" type="primary" size="small" :loading="detectionConfigSaving">
                保存配置
              </el-button>
            </div>
          </div>
        </template>

        <el-form :model="detectionConfig" label-width="200px" size="small">
          <!-- 基本设置 -->
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="启用检测频率控制">
                <el-switch 
                  v-model="detectionConfig.enabled" 
                  active-text="启用"
                  inactive-text="禁用"
                />
                <div class="config-description">
                  启用后将根据配置的检测频率减少检测量，提升处理性能
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="检测模式">
                <el-select v-model="detectionConfig.mode" style="width: 100%" :disabled="!detectionConfig.enabled">
                  <el-option label="自适应模式" value="adaptive" />
                  <el-option label="高频模式" value="high_frequency" />
                  <el-option label="中频模式" value="medium_frequency" />
                  <el-option label="低频模式" value="low_frequency" />
                  <el-option label="禁用模式" value="disabled" />
                </el-select>
                <div class="config-description">
                  选择检测频率模式，自适应模式会根据数据量自动调整
                </div>
              </el-form-item>
            </el-col>
          </el-row>

                     <!-- 固定模式设置 -->
           <el-row :gutter="16" v-if="detectionConfig.mode !== 'adaptive' && detectionConfig.mode !== 'disabled'">
             <el-col :span="12">
               <el-form-item :label="`${getModeLabel(detectionConfig.mode)}检测间隔`">
                 <el-input-number 
                   v-model="currentInterval" 
                   :min="1" 
                   :max="3600"
                   :step="1"
                   style="width: 100%"
                   @change="updateInterval"
                 />
                 <div class="config-description">
                   {{ getModeLabel(detectionConfig.mode) }}模式下的检测间隔（秒）
                 </div>
               </el-form-item>
             </el-col>
           </el-row>

          <!-- 自适应模式设置 -->
          <el-row :gutter="16" v-if="detectionConfig.mode === 'adaptive'">
            <el-col :span="24">
              <h4>自适应模式阈值设置</h4>
            </el-col>
          </el-row>
          <el-row :gutter="16" v-if="detectionConfig.mode === 'adaptive'">
            <el-col :span="8">
              <el-form-item label="小数据集阈值">
                <el-input-number 
                  v-model="detectionConfig.adaptive.small_dataset_threshold" 
                  :min="100" 
                  :max="5000"
                  :step="100"
                  style="width: 100%"
                />
                <div class="config-description">
                  小于等于此帧数时使用高频检测（帧数）
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="中数据集阈值">
                <el-input-number 
                  v-model="detectionConfig.adaptive.medium_dataset_threshold" 
                  :min="1000" 
                  :max="10000"
                  :step="500"
                  style="width: 100%"
                />
                <div class="config-description">
                  小于等于此帧数时使用中频检测（帧数）
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="大数据集阈值">
                <el-input-number 
                  v-model="detectionConfig.adaptive.large_dataset_threshold" 
                  :min="5000" 
                  :max="50000"
                  :step="1000"
                  style="width: 100%"
                />
                <div class="config-description">
                  小于等于此帧数时使用低频检测（帧数）
                </div>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16" v-if="detectionConfig.mode === 'adaptive'">
            <el-col :span="8">
              <el-form-item label="小数据集间隔">
                <el-input-number 
                  v-model="detectionConfig.adaptive.small_dataset_interval" 
                  :min="1" 
                  :max="60"
                  :step="1"
                  style="width: 100%"
                />
                <div class="config-description">
                  小数据集检测间隔（秒）
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="中数据集间隔">
                <el-input-number 
                  v-model="detectionConfig.adaptive.medium_dataset_interval" 
                  :min="10" 
                  :max="300"
                  :step="5"
                  style="width: 100%"
                />
                <div class="config-description">
                  中数据集检测间隔（秒）
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="大数据集间隔">
                <el-input-number 
                  v-model="detectionConfig.adaptive.large_dataset_interval" 
                  :min="30" 
                  :max="600"
                  :step="10"
                  style="width: 100%"
                />
                <div class="config-description">
                  大数据集检测间隔（秒）
                </div>
              </el-form-item>
            </el-col>
          </el-row>


        </el-form>
      </el-card>

      <!-- 操作按钮 -->
      <el-divider />
      <div class="actions">
        <el-button @click="clearCache" type="warning" size="small">
          清空所有缓存
        </el-button>
        <el-button @click="downloadStatus" type="primary" size="small">
          导出状态报告
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { CircleCheck, Warning, Connection, Close } from '@element-plus/icons-vue';
import api from '../api';
import websocketService from '../services/websocket';

// 为 keep-alive 添加组件名称
defineOptions({
  name: 'SystemStatus'
});

const loading = ref(false);
const cacheStats = ref({});
const wsConnected = ref(false);
const wsConnecting = ref(false);
const wsUrl = ref('');
const wsReconnectAttempts = ref(0);

// 系统配置相关
const systemConfig = ref({
  streaming_threshold: 1000,
  batch_size: 500,
  batch_size_for_save: 1000
});
const configSaving = ref(false);

// 检测频率配置相关
const detectionConfig = ref({
  enabled: true,
  mode: 'adaptive',
  high_frequency: {
    interval_seconds: 1,
    frames_per_interval: 1
  },
  medium_frequency: {
    interval_seconds: 30,
    frames_per_interval: 1
  },
  low_frequency: {
    interval_seconds: 60,
    frames_per_interval: 1
  },
  adaptive: {
    small_dataset_threshold: 1000,
    medium_dataset_threshold: 5000,
    large_dataset_threshold: 10000,
    small_dataset_interval: 1,
    medium_dataset_interval: 30,
    large_dataset_interval: 60
  }
});
const detectionConfigSaving = ref(false);

// 计算属性
const overallStatus = computed(() => {
  const redis = cacheStats.value.redis_cache?.redis_connected;
  if (redis) return '正常';
  return '异常';
});

const overallStatusStyle = computed(() => ({
  color: overallStatus.value === '正常' ? '#67c23a' : '#f56c6c'
}));

const overallStatusColor = computed(() => 
  overallStatus.value === '正常' ? '#67c23a' : '#f56c6c'
);

const wsStatus = computed(() => wsConnected.value ? '已连接' : '未连接');
const wsStatusStyle = computed(() => ({ color: wsConnected.value ? '#67c23a' : '#909399' }));
const wsStatusColor = computed(() => wsConnected.value ? '#67c23a' : '#909399');

const redisStatus = computed(() => 
  cacheStats.value.redis_cache?.redis_connected ? '正常' : '异常'
);
const redisStatusStyle = computed(() => ({ color: cacheStats.value.redis_cache?.redis_connected ? '#67c23a' : '#f56c6c' }));
const redisStatusColor = computed(() => 
  cacheStats.value.redis_cache?.redis_connected ? '#67c23a' : '#f56c6c'
);

const cacheHitRate = computed(() => {
  // 这里可以根据实际情况计算缓存命中率
  // 暂时返回一个模拟值
  return 85.6;
});

// 为了满足 ElStatistic 的 value 必须是 Number | Object 的限制，这里传入占位数值，实际文本由 suffix 插槽展示
const hiddenNumberStyle = { color: 'transparent' };
const overallStatusValue = 0;
const wsStatusValue = 0;
const redisStatusValue = 0;

const memoryeCacheDetails = computed(() => {
  if (!cacheStats.value.memory_cache) return [];
  
  return Object.entries(cacheStats.value.memory_cache)
    .filter(([key]) => key !== 'total')
    .map(([cmg_id, stats]) => ({
      cmg_id,
      data_points: stats.data_points || 0,
      latest_time: stats.latest_time ? new Date(stats.latest_time).toLocaleString() : '无数据'
    }));
});

// 当前间隔计算属性
const currentInterval = computed({
  get() {
    const mode = detectionConfig.value.mode;
    if (mode === 'high_frequency') {
      return detectionConfig.value.high_frequency.interval_seconds;
    } else if (mode === 'medium_frequency') {
      return detectionConfig.value.medium_frequency.interval_seconds;
    } else if (mode === 'low_frequency') {
      return detectionConfig.value.low_frequency.interval_seconds;
    }
    return 1;
  },
  set(value) {
    updateInterval(value);
  }
});

// 方法
async function loadSystemConfig() {
  try {
    const response = await api.get('/data/system-config/');
    systemConfig.value = response.data.config;
    
    // 加载检测频率配置
    if (response.data.config.detection_frequency) {
      detectionConfig.value = response.data.config.detection_frequency;
    }
  } catch (error) {
    console.error('Failed to load system config:', error);
    ElMessage.error('加载系统配置失败');
  }
}

async function saveConfig() {
  configSaving.value = true;
  try {
    await api.put('/data/system-config/update/', {
      config: systemConfig.value
    });
    ElMessage.success('配置保存成功');
  } catch (error) {
    console.error('Failed to save config:', error);
    ElMessage.error('保存配置失败');
  } finally {
    configSaving.value = false;
  }
}

async function resetConfig() {
  try {
    await ElMessageBox.confirm('确定要重置为默认配置吗？', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    await api.post('/data/system-config/reset/');
    await loadSystemConfig();
    ElMessage.success('配置已重置为默认值');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to reset config:', error);
      ElMessage.error('重置配置失败');
    }
  }
}

// 检测频率配置相关方法
async function saveDetectionConfig() {
  detectionConfigSaving.value = true;
  try {
    const configToSave = {
      ...systemConfig.value,
      detection_frequency: detectionConfig.value
    };
    
    await api.put('/data/system-config/update/', {
      config: configToSave
    });
    ElMessage.success('检测频率配置保存成功');
  } catch (error) {
    console.error('Failed to save detection config:', error);
    ElMessage.error('保存检测频率配置失败');
  } finally {
    detectionConfigSaving.value = false;
  }
}

async function resetDetectionConfig() {
  try {
    await ElMessageBox.confirm('确定要重置检测频率配置为默认值吗？', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    // 重置为默认值
    detectionConfig.value = {
      enabled: true,
      mode: 'adaptive',
      high_frequency: {
        interval_seconds: 1,
        frames_per_interval: 1
      },
      medium_frequency: {
        interval_seconds: 30,
        frames_per_interval: 1
      },
      low_frequency: {
        interval_seconds: 60,
        frames_per_interval: 1
      },
      adaptive: {
        small_dataset_threshold: 1000,
        medium_dataset_threshold: 5000,
        large_dataset_threshold: 10000,
        small_dataset_interval: 1,
        medium_dataset_interval: 30,
        large_dataset_interval: 60
      }
    };
    
    ElMessage.success('检测频率配置已重置为默认值');
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to reset detection config:', error);
      ElMessage.error('重置检测频率配置失败');
    }
  }
}

async function testDetectionFrequency() {
  try {
    ElMessage.info('检测频率配置测试功能待实现');
    // 这里可以调用后端的测试接口
  } catch (error) {
    console.error('Failed to test detection frequency:', error);
    ElMessage.error('测试检测频率配置失败');
  }
}

// 辅助方法
function getModeLabel(mode) {
  const labels = {
    'high_frequency': '高频',
    'medium_frequency': '中频',
    'low_frequency': '低频',
    'adaptive': '自适应',
    'disabled': '禁用'
  };
  return labels[mode] || mode;
}

function updateInterval(value) {
  const mode = detectionConfig.value.mode;
  if (mode === 'high_frequency') {
    detectionConfig.value.high_frequency.interval_seconds = value;
  } else if (mode === 'medium_frequency') {
    detectionConfig.value.medium_frequency.interval_seconds = value;
  } else if (mode === 'low_frequency') {
    detectionConfig.value.low_frequency.interval_seconds = value;
  }
}

async function refreshStatus() {
  loading.value = true;
  try {
    // 获取缓存状态
    const response = await api.get('/data/data/cache-stats/');
    cacheStats.value = response.data;
    
    // 更新WebSocket状态
    const wsStatus = websocketService.getStatus();
    wsConnected.value = wsStatus.connected;
    wsConnecting.value = wsStatus.connecting;
    wsUrl.value = wsStatus.url;
    wsReconnectAttempts.value = wsStatus.reconnectAttempts;
    
  } catch (error) {
    console.error('Failed to refresh status:', error);
    ElMessage.error('刷新状态失败');
  } finally {
    loading.value = false;
  }
}

function formatUptime(seconds) {
  if (!seconds) return '未知';
  
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) {
    return `${days}天${hours}小时`;
  } else if (hours > 0) {
    return `${hours}小时${minutes}分钟`;
  } else {
    return `${minutes}分钟`;
  }
}

async function testWebSocket() {
  try {
    wsConnecting.value = true;
    await websocketService.connect();
    ElMessage.success('WebSocket连接测试成功');
  } catch (error) {
    ElMessage.error('WebSocket连接测试失败');
  } finally {
    wsConnecting.value = false;
    setTimeout(refreshStatus, 500);
  }
}

function disconnectWebSocket() {
  websocketService.disconnect();
  ElMessage.info('WebSocket已断开');
  setTimeout(refreshStatus, 500);
}

async function clearCache() {
  try {
    await ElMessageBox.confirm('确定要清空所有缓存吗？这将影响系统性能。', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    });
    
    // 这里应该调用清空缓存的API
    ElMessage.info('缓存清空功能待实现');
    
  } catch {
    // 用户取消
  }
}

function downloadStatus() {
  const statusData = {
    timestamp: new Date().toISOString(),
    overall_status: overallStatus.value,
    websocket: {
      connected: wsConnected.value,
      url: wsUrl.value,
      reconnect_attempts: wsReconnectAttempts.value
    },
    cache_stats: cacheStats.value
  };
  
  const blob = new Blob([JSON.stringify(statusData, null, 2)], { 
    type: 'application/json' 
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `system-status-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  ElMessage.success('状态报告已导出');
}

// 生命周期
onMounted(() => {
  refreshStatus();
  loadSystemConfig();
  
  // 设置WebSocket事件监听
  websocketService.onConnect(() => {
    wsConnected.value = true;
    wsConnecting.value = false;
  });
  
  websocketService.onDisconnect(() => {
    wsConnected.value = false;
    wsConnecting.value = false;
  });
});

// 定时刷新状态
let statusInterval;
onMounted(() => {
  statusInterval = setInterval(refreshStatus, 30000); // 每30秒刷新一次
});

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval);
  }
});
</script>

<style scoped>
.system-status {
  padding: 20px;
}

.status-card {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-overview {
  margin-bottom: 20px;
}

.detail-card {
  height: 100%;
}

.no-data {
  color: #909399;
  text-align: center;
  padding: 20px;
}

.cache-breakdown,
.cmg-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.cache-breakdown h4,
.cmg-details h4 {
  margin: 0 0 12px 0;
}

.config-card {
  margin-bottom: 20px;
}

.config-description {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.performance-preview {
  font-size: 13px;
  line-height: 1.6;
}

.performance-preview ul {
  margin: 8px 0;
  padding-left: 20px;
}

.performance-preview li {
  margin: 4px 0;
}

.performance-preview strong {
  color: #409eff;
}

.ws-status {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ws-actions {
  display: flex;
  gap: 8px;
}

.actions {
  text-align: center;
}

.actions .el-button {
  margin: 0 8px;
}
</style>
