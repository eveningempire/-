<template>
  <div class="time-domain-analysis-page">
    <!-- 查询工具栏 -->
    <SectionCard 
      title="时域特征分析"
      icon="DataAnalysis"
      size="small"
      class="query-card"
    >
      <div class="query-form">
        <el-form :model="query" inline>
          <el-form-item label="CMG">
            <el-select 
              v-model="query.cmgId" 
              placeholder="选择 CMG" 
              @change="onCmgChange"
              clearable
              filterable
              style="min-width: 200px;"
            >
              <el-option
                v-for="cmg in cmgList"
                :key="cmg.id"
                :label="cmg.name + '(' + cmg.cmg_id + ')'"
                :value="cmg.cmg_id"
              >
                <div class="cmg-option">
                  <el-icon><Cpu /></el-icon>
                  <span>{{ cmg.name }}</span>
                  <span class="cmg-option-id">({{ cmg.cmg_id }})</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          
          <!-- 数据库统计信息显示 -->
          <el-form-item v-if="query.cmgId" label="数据库统计">
            <div class="database-stats">
              <el-tag 
                v-for="stat in databaseStats" 
                :key="stat.type"
                :type="getStatTagType(stat.type)"
                size="small"
                class="stat-tag"
              >
                <el-icon><component :is="stat.icon" /></el-icon>
                {{ stat.label }}: {{ formatNumber(stat.count) }}
              </el-tag>
              <el-button 
                size="small" 
                type="primary" 
                text 
                @click="refreshDatabaseStats"
                :loading="statsLoading"
                title="刷新统计信息"
              >
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </el-form-item>
          
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="query.dates"
              type="datetimerange"
              range-separator="-"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              style="min-width: 360px;"
              :shortcuts="timeShortcuts"
              :disabled="!query.cmgId"
            />
          </el-form-item>
          
          <!-- 快捷时间选择（基于数据库最新时间） -->
          <el-form-item label="快捷选择" v-if="latestDataTime">
            <el-button-group>
              <el-button size="small" @click="selectRecentTime(1, 'hour')">最新1小时</el-button>
              <el-button size="small" @click="selectRecentTime(1, 'day')">最新1天</el-button>
              <el-button size="small" @click="selectRecentTime(7, 'day')">最新1周</el-button>
              <el-button size="small" @click="selectRecentTime(30, 'day')">最新1个月</el-button>
              <el-button size="small" @click="selectRecentTime(90, 'day')">最新3个月</el-button>
            </el-button-group>
            <div class="time-hint">数据库最新时间: {{ formatDateTime(latestDataTime) }}</div>
          </el-form-item>
          
          <el-form-item>
            <el-button-group>
              <el-button type="primary" @click="loadDataForAnalysis" :loading="loading">
                <el-icon><Search /></el-icon>
                查询分析
              </el-button>
            </el-button-group>
          </el-form-item>
          
          <el-form-item>
            <el-dropdown @command="handleCommand">
              <el-button type="danger" :disabled="!query.cmgId">
                <el-icon><Delete /></el-icon>
                数据管理
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="deleteAll" :disabled="!query.cmgId">
                    <el-icon><Delete /></el-icon>
                    删除该CMG全部数据
                  </el-dropdown-item>
                  <el-dropdown-item command="deleteByRange" :disabled="!query.cmgId || query.dates.length !== 2">
                    <el-icon><Delete /></el-icon>
                    按时间范围删除
                  </el-dropdown-item>
                  <el-dropdown-item divided command="export" :disabled="rawData.length === 0">
                    <el-icon><Download /></el-icon>
                    导出数据
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </el-form-item>
        </el-form>
      </div>
    </SectionCard>

    <!-- 主分析区域 -->
    <div v-if="dataLoaded" class="analysis-container">
      <el-row :gutter="16" class="equal-height-row">
        <!-- 左侧：时序图展示 -->
        <el-col :span="12" class="equal-height-col">
          <SectionCard title="遥测量时序图" icon="TrendCharts" class="chart-card">
            <div class="chart-container">
              <!-- 参数选择移到内容区 -->
              <div class="param-selector">
                <label class="selector-label">选择显示的遥测量：</label>
                <el-select 
                  v-model="selectedParams" 
                  multiple 
                  placeholder="选择要显示的遥测量"
                  style="width: 100%;"
                  :max-collapse-tags="3"
                  collapse-tags
                  size="small"
                >
                  <el-option
                    v-for="param in availableParams"
                    :key="param"
                    :label="param"
                    :value="param"
                  />
                </el-select>
          </div>
              
              <el-divider />
              
              <!-- 时序图区域 -->
              <div 
                v-for="param in selectedParams" 
                :key="param" 
                class="param-chart"
              >
                <div class="chart-title">{{ param }}</div>
                <div :ref="el => setChartRef(param, el)" class="chart chart-compact" :id="`chart-${param}`"></div>
        </div>
              
              <div v-if="selectedParams.length === 0" class="empty-hint">
                <el-empty description="请在上方选择要显示的遥测量" />
              </div>
            </div>
          </SectionCard>
        </el-col>

        <!-- 右侧：时域特征提取 -->
        <el-col :span="12" class="equal-height-col">
          <SectionCard title="时域特征提取" icon="DataLine" class="feature-card">
            <div class="feature-extraction">
              <!-- 参数选择 -->
              <el-form :model="featureConfig" label-width="120px" size="small">
                <el-form-item label="选择遥测量">
                  <el-select 
                    v-model="featureConfig.selectedParam" 
                    placeholder="选择遥测量"
                    style="width: 100%;"
                  >
                    <el-option
                      v-for="param in availableParams"
                      :key="param"
                      :label="param"
                      :value="param"
                    />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="时间窗口">
                  <el-input-number 
                    v-model="featureConfig.windowSize" 
                    :min="10" 
                    :max="1000" 
                    :step="10"
                    style="width: 100%;"
                  />
                  <div class="param-hint">用于滑动窗口特征计算的窗口大小（帧数）</div>
                </el-form-item>
                
                <el-form-item label="窗口步长">
                  <el-input-number 
                    v-model="featureConfig.stepSize" 
                    :min="1" 
                    :max="500" 
                    :step="10"
                    style="width: 100%;"
                  />
                  <div class="param-hint">滑动窗口的移动步长（帧数），步长越小趋势越平滑</div>
                </el-form-item>
                
                <el-form-item label="选择特征">
                  <el-checkbox-group v-model="featureConfig.selectedFeatures" class="feature-checkbox-grid">
                    <el-checkbox label="mean">均值</el-checkbox>
                    <el-checkbox label="std">标准差</el-checkbox>
                    <el-checkbox label="variance">方差</el-checkbox>
                    <el-checkbox label="rms">均方根</el-checkbox>
                    <el-checkbox label="peak">峰值</el-checkbox>
                    <el-checkbox label="peak2peak">峰峰值</el-checkbox>
                    <el-checkbox label="kurtosis">峭度</el-checkbox>
                    <el-checkbox label="skewness">偏度</el-checkbox>
                    <el-checkbox label="crest_factor">峰值因子</el-checkbox>
                    <el-checkbox label="impulse_factor">脉冲因子</el-checkbox>
                    <el-checkbox label="shape_factor">波形因子</el-checkbox>
                    <el-checkbox label="clearance_factor">裕度因子</el-checkbox>
                    <el-checkbox label="kurtosis_factor">峭度因子</el-checkbox>
                  </el-checkbox-group>
                  <div class="feature-selection-footer">
                    <el-button-group size="small">
                      <el-button size="small" @click="selectAllFeatures">全选</el-button>
                      <el-button size="small" @click="selectCommonFeatures">常用</el-button>
                      <el-button size="small" @click="clearAllFeatures">清空</el-button>
                    </el-button-group>
                  </div>
                </el-form-item>
                
                <el-form-item>
                  <el-button 
                    type="primary" 
                    @click="extractFeatures" 
                    :loading="featureLoading"
                    :disabled="!featureConfig.selectedParam || featureConfig.selectedFeatures.length === 0"
                  >
                    <el-icon><Histogram /></el-icon>
                    提取特征
                  </el-button>
                  <el-button @click="clearFeatures">
                    <el-icon><Delete /></el-icon>
                    清空
                  </el-button>
                </el-form-item>
              </el-form>

              <!-- 特征结果显示 -->
              <div v-if="extractedFeatures.length > 0" class="feature-results">
                <el-divider content-position="left">
                  <el-icon><DataAnalysis /></el-icon>
                  特征统计值（全时段）
                </el-divider>
                
                <el-table :data="extractedFeatures" size="small" border stripe>
                  <el-table-column prop="feature" label="特征名称" width="120">
            <template #default="scope">
                      <el-tag size="small" type="primary">{{ getFeatureLabel(scope.row.feature) }}</el-tag>
            </template>
          </el-table-column>
                  <el-table-column prop="value" label="特征值" align="right" width="120">
            <template #default="scope">
                      <span class="feature-value">{{ formatFeatureValue(scope.row.value) }}</span>
            </template>
          </el-table-column>
                  <el-table-column prop="description" label="说明" show-overflow-tooltip />
        </el-table>
        
                <!-- 特征趋势图 -->
                <div v-if="featureTrendData.length > 0" class="feature-trend">
                  <el-divider content-position="left">
                    <el-icon><TrendCharts /></el-icon>
                    特征时域变化趋势
                  </el-divider>
                  
                  <div class="trend-info">
                    <el-tag size="small" type="info">窗口: {{ featureConfig.windowSize }}帧</el-tag>
                    <el-tag size="small" type="info">步长: {{ featureConfig.stepSize }}帧</el-tag>
                    <el-tag size="small" type="success">趋势点数: {{ featureTrendData.length }}</el-tag>
          </div>
          
                  <div ref="featureTrendChart" class="trend-chart"></div>
                </div>
                
                <div class="feature-actions">
                  <el-button size="small" @click="exportFeatures">
                    <el-icon><Download /></el-icon>
                    导出特征
                  </el-button>
                </div>
        </div>
      </div>
    </SectionCard>
        </el-col>
      </el-row>
    </div>

    <!-- 空状态提示 -->
    <div v-else class="empty-state">
      <el-empty description="请选择CMG和时间范围，然后点击查询分析按钮">
        <el-button type="primary" @click="loadDataForAnalysis" :disabled="!query.cmgId || query.dates.length !== 2">
          <el-icon><Search /></el-icon>
          开始分析
        </el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  Search, Cpu, DataAnalysis, TrendCharts, DataLine, Histogram, 
  Delete, Download, Refresh, Warning, CircleCheck, Connection, 
  WarnTriangleFilled, ArrowDown
} from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import api from '../api';
import SectionCard from '../components/SectionCard.vue';

// 为 keep-alive 添加组件名称
defineOptions({
  name: 'DataRecords'
});

// 数据状态
const cmgList = ref([]);
const query = ref({
  cmgId: null,
  dates: []
});
const loading = ref(false);
const dataLoaded = ref(false);
const rawData = ref([]); // 原始数据
const availableParams = ref([]); // 可用参数列表
const selectedParams = ref([]); // 选中要展示的参数
const latestDataTime = ref(null); // 数据库中该CMG的最新数据时间

// 数据库统计相关
const databaseStats = ref([]);
const statsLoading = ref(false);

// 图表相关
const chartInstances = ref({});
const chartRefs = ref({});

// 特征提取配置
const featureConfig = ref({
  selectedParam: null,
  windowSize: 50,
  stepSize: 50,  // 滑动窗口步长
  selectedFeatures: ['mean', 'std', 'rms', 'peak', 'peak2peak']
});
const featureLoading = ref(false);
const extractedFeatures = ref([]);
const featureTrendData = ref([]); // 特征趋势数据
const featureTrendChart = ref(null); // 特征趋势图实例

// 时间快捷选项
const timeShortcuts = [
  {
    text: '近 1 小时',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setHours(start.getHours() - 1);
      return [start, end];
    }
  },
  {
    text: '近 6 小时',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setHours(start.getHours() - 6);
      return [start, end];
    }
  },
  {
    text: '近 24 小时',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setHours(start.getHours() - 24);
      return [start, end];
    }
  },
  {
    text: '近 7 天',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - 7);
      return [start, end];
    }
  }
];

// 特征标签映射
const featureLabels = {
  mean: '均值',
  std: '标准差',
  variance: '方差',
  rms: '均方根',
  peak: '峰值',
  peak2peak: '峰峰值',
  kurtosis: '峭度',
  skewness: '偏度',
  crest_factor: '峰值因子',
  impulse_factor: '脉冲因子',
  shape_factor: '波形因子',
  clearance_factor: '裕度因子',
  kurtosis_factor: '峭度因子'
};

// 特征说明映射
const featureDescriptions = {
  mean: '信号的平均值',
  std: '信号的标准差，反映波动程度',
  variance: '信号的方差，标准差的平方',
  rms: '均方根值，反映信号的能量',
  peak: '信号的最大绝对值',
  peak2peak: '信号的最大值与最小值之差',
  kurtosis: '峭度，反映信号分布的尖锐程度',
  skewness: '偏度，反映信号分布的对称性',
  crest_factor: '峰值因子 = 峰值/均方根',
  impulse_factor: '脉冲因子 = 峰值/均值',
  shape_factor: '波形因子 = 均方根/均值',
  clearance_factor: '裕度因子 = 峰值/方根幅值',
  kurtosis_factor: '峭度因子 = 峭度/均方根^4'
};

// 加载CMG列表
async function loadCmgs() {
  try {
    const res = await api.get('/data/cmgs/');
    cmgList.value = res.data;
  } catch (e) {
    ElMessage.error('加载CMG列表失败');
  }
}

// CMG变化处理
async function onCmgChange() {
  dataLoaded.value = false;
  rawData.value = [];
  availableParams.value = [];
  selectedParams.value = [];
  extractedFeatures.value = [];
  featureTrendData.value = [];
  latestDataTime.value = null;
  databaseStats.value = [];
  
  // 加载该CMG的最新数据时间和统计信息
  if (query.value.cmgId) {
    await Promise.all([
      loadLatestDataTime(),
      loadDatabaseStats()
    ]);
  }
}

// 加载数据库统计信息
async function loadDatabaseStats() {
  if (!query.value.cmgId) return;
  
  statsLoading.value = true;
  try {
    const res = await api.get('/data/data/statistics/', { 
      params: { cmg_id: query.value.cmgId, refresh: 'true' } 
    });
    
    const stats = res.data.statistics || {};
    databaseStats.value = [
      {
        type: 'cmg_data',
        label: '遥测数据',
        count: stats.cmg_data?.count || 0,
        icon: 'DataAnalysis'
      },
      {
        type: 'ims_results',
        label: 'IMS检测',
        count: stats.ims_results?.count || 0,
        icon: 'Warning'
      },
      {
        type: 'rule_results',
        label: '规则检测',
        count: stats.rule_results?.count || 0,
        icon: 'CircleCheck'
      },
      {
        type: 'msfg_results',
        label: 'MSFG检测',
        count: stats.msfg_results?.count || 0,
        icon: 'Connection'
      },
      {
        type: 'anomaly_frames',
        label: '异常帧',
        count: stats.anomaly_frames?.count || 0,
        icon: 'WarnTriangleFilled'
      }
    ];
  } catch (error) {
    console.error('加载数据库统计信息失败:', error);
  } finally {
    statsLoading.value = false;
  }
}

// 刷新数据库统计信息
async function refreshDatabaseStats() {
  await loadDatabaseStats();
  ElMessage.success('统计信息已刷新');
}

// 获取统计标签类型
function getStatTagType(type) {
  const typeMap = {
    'cmg_data': 'info',
    'ims_results': 'warning',
    'rule_results': 'success',
    'msfg_results': 'primary',
    'anomaly_frames': 'danger'
  };
  return typeMap[type] || 'info';
}

// 格式化数字（K, M表示）
function formatNumber(num) {
  if (num === null || num === undefined) return '0';
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

// 加载数据库中该CMG的最新数据时间
async function loadLatestDataTime() {
  try {
    const res = await api.get('/data/data/', {
      params: {
        cmg_id: query.value.cmgId,
        limit: 1
      }
    });
    
    if (res.data && res.data.length > 0) {
      latestDataTime.value = res.data[0].timestamp;
    }
  } catch (error) {
    console.error('获取最新数据时间失败:', error);
  }
}

// 快捷选择时间（基于数据库最新时间）
function selectRecentTime(amount, unit) {
  if (!latestDataTime.value) {
    ElMessage.warning('无法获取最新数据时间');
    return;
  }
  
  const endTime = new Date(latestDataTime.value);
  const startTime = new Date(endTime);
  
  switch (unit) {
    case 'hour':
      startTime.setHours(startTime.getHours() - amount);
      break;
    case 'day':
      startTime.setDate(startTime.getDate() - amount);
      break;
    case 'month':
      startTime.setMonth(startTime.getMonth() - amount);
      break;
  }
  
  query.value.dates = [startTime, endTime];
  ElMessage.success(`已选择: ${formatDateTime(startTime)} 至 ${formatDateTime(endTime)}`);
}

// 格式化日期时间
function formatDateTime(timestamp) {
  if (!timestamp) return '-';
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// 加载数据进行分析
async function loadDataForAnalysis() {
  if (!query.value.cmgId) {
    ElMessage.warning('请选择 CMG');
    return;
  }
  if (query.value.dates.length !== 2) {
    ElMessage.warning('请选择时间范围');
    return;
  }
  
  loading.value = true;
  try {
    const params = {
        cmg_id: query.value.cmgId, 
      start: new Date(query.value.dates[0]).toISOString(),
      end: new Date(query.value.dates[1]).toISOString(),
      limit: 10000  // 最多加载10000条数据
    };
    
    const res = await api.get('/data/data/', { params });
    
    if (!res.data || res.data.length === 0) {
      ElMessage.warning('当前时间范围内没有数据');
      dataLoaded.value = false;
      return;
    }
    
    // 处理数据
    rawData.value = res.data;
    
    // 提取所有可用参数
    const paramSet = new Set();
    res.data.forEach(record => {
      if (record.data && typeof record.data === 'object') {
        Object.keys(record.data).forEach(key => {
          // 只添加数值型参数
          const value = record.data[key];
          if (typeof value === 'number' || !isNaN(parseFloat(value))) {
            paramSet.add(key);
          }
        });
      }
    });
    
    availableParams.value = Array.from(paramSet).sort();
    
    // 默认选择前5个参数
    selectedParams.value = availableParams.value.slice(0, 5);
    
    // 默认选择第一个参数用于特征提取
    if (availableParams.value.length > 0 && !featureConfig.value.selectedParam) {
      featureConfig.value.selectedParam = availableParams.value[0];
    }
    
    dataLoaded.value = true;
    
    ElMessage.success(`成功加载 ${res.data.length} 条数据，包含 ${availableParams.value.length} 个遥测量`);
    
    // 等待DOM更新后绘制图表
    await nextTick();
    renderCharts();
    
  } catch (e) {
    ElMessage.error('加载数据失败: ' + (e.response?.data?.error || e.message));
    console.error(e);
  } finally {
    loading.value = false;
  }
}

// 命令处理（数据管理下拉菜单）
function handleCommand(command) {
  switch (command) {
    case 'deleteAll':
      deleteAllData();
      break;
    case 'deleteByRange':
      deleteDataByRange();
      break;
    case 'export':
      exportData();
      break;
  }
}

// 删除该CMG的全部数据
async function deleteAllData() {
  if (!query.value.cmgId) {
    ElMessage.warning('请选择 CMG');
    return;
  }
  
  try {
    await ElMessageBox.confirm(
      `确认删除 CMG ${query.value.cmgId} 的全部数据？此操作不可恢复！`,
      '危险操作',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    );
    
    await api.post('/data/data/delete-range/', {
      cmg_id: query.value.cmgId
    });
    
    ElMessage.success('数据已删除');
    
    // 清空当前显示
    dataLoaded.value = false;
    rawData.value = [];
    availableParams.value = [];
    selectedParams.value = [];
    extractedFeatures.value = [];
    featureTrendData.value = [];
    
    // 刷新数据库统计
    await loadDatabaseStats();
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.response?.data?.error || error.message));
    }
  }
}

// 按时间范围删除数据
async function deleteDataByRange() {
  if (!query.value.cmgId) {
    ElMessage.warning('请选择 CMG');
    return;
  }
  
  if (query.value.dates.length !== 2) {
    ElMessage.warning('请选择时间范围');
    return;
  }
  
  try {
    const startTime = new Date(query.value.dates[0]).toLocaleString('zh-CN');
    const endTime = new Date(query.value.dates[1]).toLocaleString('zh-CN');
    
    await ElMessageBox.confirm(
      `确认删除 CMG ${query.value.cmgId} 在以下时间段的数据？\n\n${startTime}\n至\n${endTime}\n\n此操作不可恢复！`,
      '危险操作',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    );
    
    await api.post('/data/data/delete-range/', {
      cmg_id: query.value.cmgId,
      start: new Date(query.value.dates[0]).toISOString(),
      end: new Date(query.value.dates[1]).toISOString()
    });
    
    ElMessage.success('时间范围内的数据已删除');
    
    // 清空当前显示
    dataLoaded.value = false;
    rawData.value = [];
    availableParams.value = [];
    selectedParams.value = [];
    extractedFeatures.value = [];
    featureTrendData.value = [];
    
    // 刷新数据库统计
    await loadDatabaseStats();
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.response?.data?.error || error.message));
    }
  }
}

// 导出原始数据
function exportData() {
  if (rawData.value.length === 0) {
    ElMessage.warning('没有可导出的数据');
    return;
  }
  
  const exportData = {
    cmg_id: query.value.cmgId,
    time_range: {
      start: query.value.dates[0],
      end: query.value.dates[1]
    },
    data_count: rawData.value.length,
    parameters: availableParams.value,
    data: rawData.value,
    exported_at: new Date().toISOString()
  };
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `cmg_data_${query.value.cmgId}_${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  ElMessage.success('数据已导出');
}

// 设置图表引用
function setChartRef(param, el) {
  if (el) {
    chartRefs.value[param] = el;
  }
}

// 渲染图表
function renderCharts() {
  // 销毁旧图表
  Object.values(chartInstances.value).forEach(chart => {
    if (chart) chart.dispose();
  });
  chartInstances.value = {};
  
  // 为每个选中的参数创建图表
  selectedParams.value.forEach(param => {
    const chartEl = chartRefs.value[param];
    if (!chartEl) return;
    
    const chart = echarts.init(chartEl);
    chartInstances.value[param] = chart;
    
    // 准备数据
    const timeData = [];
    const valueData = [];
    
    rawData.value.forEach(record => {
      timeData.push(new Date(record.timestamp));
      const value = record.data[param];
      valueData.push(typeof value === 'number' ? value : parseFloat(value) || null);
    });
    
    // 配置图表
    const option = {
      title: {
        show: false
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          const date = new Date(params[0].value[0]);
          const dateStr = date.toLocaleString('zh-CN');
          const value = params[0].value[1];
          return `${dateStr}<br/>${param}: ${value !== null ? value.toFixed(4) : 'N/A'}`;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'time',
        boundaryGap: false,
        axisLabel: {
          formatter: (value) => {
            const date = new Date(value);
            return date.toLocaleString('zh-CN', {
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            });
          }
        }
      },
      yAxis: {
        type: 'value',
        name: param,
        axisLabel: {
          formatter: (value) => value.toFixed(2)
        }
      },
      series: [
        {
          name: param,
          type: 'line',
          data: timeData.map((time, idx) => [time, valueData[idx]]),
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 1.5
          },
          itemStyle: {
            color: '#1890ff'
          }
        }
      ],
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100
        },
        {
          type: 'slider',
          start: 0,
          end: 100,
          height: 20
        }
      ]
    };
    
    chart.setOption(option);
  });
}

// 提取时域特征
async function extractFeatures() {
  if (!featureConfig.value.selectedParam) {
    ElMessage.warning('请选择要分析的遥测量');
    return;
  }
  
  if (featureConfig.value.selectedFeatures.length === 0) {
    ElMessage.warning('请至少选择一个特征');
    return;
  }
  
  featureLoading.value = true;
  
  try {
    // 提取参数数据（保留时间戳）
    const paramDataWithTime = rawData.value.map(record => {
      const value = record.data[featureConfig.value.selectedParam];
      return {
        timestamp: record.timestamp,
        value: typeof value === 'number' ? value : parseFloat(value) || null
      };
    }).filter(item => item.value !== null && !isNaN(item.value));
    
    if (paramDataWithTime.length === 0) {
      ElMessage.warning('所选参数没有有效数据');
      return;
    }
    
    const paramData = paramDataWithTime.map(item => item.value);
    
    // ========== 第一部分：计算全时段的统计特征 ==========
    const features = [];
    const selectedFeats = featureConfig.value.selectedFeatures;
    
    // 基础统计特征
    if (selectedFeats.includes('mean')) {
      features.push({
        feature: 'mean',
        value: calculateMean(paramData),
        description: featureDescriptions.mean
      });
    }
    
    if (selectedFeats.includes('std')) {
      features.push({
        feature: 'std',
        value: calculateStd(paramData),
        description: featureDescriptions.std
      });
    }
    
    if (selectedFeats.includes('variance')) {
      features.push({
        feature: 'variance',
        value: calculateVariance(paramData),
        description: featureDescriptions.variance
      });
    }
    
    if (selectedFeats.includes('rms')) {
      features.push({
        feature: 'rms',
        value: calculateRMS(paramData),
        description: featureDescriptions.rms
      });
    }
    
    if (selectedFeats.includes('peak')) {
      features.push({
        feature: 'peak',
        value: calculatePeak(paramData),
        description: featureDescriptions.peak
      });
    }
    
    if (selectedFeats.includes('peak2peak')) {
      features.push({
        feature: 'peak2peak',
        value: calculatePeak2Peak(paramData),
        description: featureDescriptions.peak2peak
      });
    }
    
    if (selectedFeats.includes('kurtosis')) {
      features.push({
        feature: 'kurtosis',
        value: calculateKurtosis(paramData),
        description: featureDescriptions.kurtosis
      });
    }
    
    if (selectedFeats.includes('skewness')) {
      features.push({
        feature: 'skewness',
        value: calculateSkewness(paramData),
        description: featureDescriptions.skewness
      });
    }
    
    // 形状因子类特征
    const mean = calculateMean(paramData);
    const rms = calculateRMS(paramData);
    const peak = calculatePeak(paramData);
    
    if (selectedFeats.includes('crest_factor')) {
      features.push({
        feature: 'crest_factor',
        value: rms !== 0 ? peak / rms : 0,
        description: featureDescriptions.crest_factor
      });
    }
    
    if (selectedFeats.includes('impulse_factor')) {
      const absData = paramData.map(v => Math.abs(v));
      const meanAbs = calculateMean(absData);
      features.push({
        feature: 'impulse_factor',
        value: meanAbs !== 0 ? peak / meanAbs : 0,
        description: featureDescriptions.impulse_factor
      });
    }
    
    if (selectedFeats.includes('shape_factor')) {
      const absData = paramData.map(v => Math.abs(v));
      const meanAbs = calculateMean(absData);
      features.push({
        feature: 'shape_factor',
        value: meanAbs !== 0 ? rms / meanAbs : 0,
        description: featureDescriptions.shape_factor
      });
    }
    
    if (selectedFeats.includes('clearance_factor')) {
      const sqrtMeanRoot = calculateSqrtMeanRoot(paramData);
      features.push({
        feature: 'clearance_factor',
        value: sqrtMeanRoot !== 0 ? peak / sqrtMeanRoot : 0,
        description: featureDescriptions.clearance_factor
      });
    }
    
    if (selectedFeats.includes('kurtosis_factor')) {
      const kurt = calculateKurtosis(paramData);
      features.push({
        feature: 'kurtosis_factor',
        value: rms !== 0 ? kurt / Math.pow(rms, 4) : 0,
        description: featureDescriptions.kurtosis_factor
      });
    }
    
    extractedFeatures.value = features;
    
    // ========== 第二部分：计算滑动窗口的特征趋势 ==========
    const windowSize = featureConfig.value.windowSize;
    const stepSize = featureConfig.value.stepSize;
    
    if (paramDataWithTime.length >= windowSize) {
      const trendData = [];
      
      // 滑动窗口遍历
      for (let i = 0; i <= paramDataWithTime.length - windowSize; i += stepSize) {
        const windowData = paramDataWithTime.slice(i, i + windowSize);
        const windowValues = windowData.map(item => item.value);
        const windowTimestamp = windowData[Math.floor(windowSize / 2)].timestamp; // 使用窗口中点的时间
        
        const trendPoint = {
          timestamp: windowTimestamp,
          features: {}
        };
        
        // 计算选中的每个特征在当前窗口的值
        selectedFeats.forEach(featName => {
          let value = 0;
          
          switch (featName) {
            case 'mean':
              value = calculateMean(windowValues);
      break;
            case 'std':
              value = calculateStd(windowValues);
      break;
            case 'variance':
              value = calculateVariance(windowValues);
              break;
            case 'rms':
              value = calculateRMS(windowValues);
              break;
            case 'peak':
              value = calculatePeak(windowValues);
              break;
            case 'peak2peak':
              value = calculatePeak2Peak(windowValues);
              break;
            case 'kurtosis':
              value = calculateKurtosis(windowValues);
              break;
            case 'skewness':
              value = calculateSkewness(windowValues);
              break;
            case 'crest_factor':
              const rms_cf = calculateRMS(windowValues);
              const peak_cf = calculatePeak(windowValues);
              value = rms_cf !== 0 ? peak_cf / rms_cf : 0;
              break;
            case 'impulse_factor':
              const absData_if = windowValues.map(v => Math.abs(v));
              const meanAbs_if = calculateMean(absData_if);
              const peak_if = calculatePeak(windowValues);
              value = meanAbs_if !== 0 ? peak_if / meanAbs_if : 0;
              break;
            case 'shape_factor':
              const absData_sf = windowValues.map(v => Math.abs(v));
              const meanAbs_sf = calculateMean(absData_sf);
              const rms_sf = calculateRMS(windowValues);
              value = meanAbs_sf !== 0 ? rms_sf / meanAbs_sf : 0;
              break;
            case 'clearance_factor':
              const sqrtMeanRoot_clf = calculateSqrtMeanRoot(windowValues);
              const peak_clf = calculatePeak(windowValues);
              value = sqrtMeanRoot_clf !== 0 ? peak_clf / sqrtMeanRoot_clf : 0;
              break;
            case 'kurtosis_factor':
              const kurt_kf = calculateKurtosis(windowValues);
              const rms_kf = calculateRMS(windowValues);
              value = rms_kf !== 0 ? kurt_kf / Math.pow(rms_kf, 4) : 0;
      break;
  }
          
          trendPoint.features[featName] = value;
        });
        
        trendData.push(trendPoint);
      }
      
      featureTrendData.value = trendData;
      
      // 绘制特征趋势图
      await nextTick();
      renderFeatureTrendChart();
      
      ElMessage.success(`成功提取 ${features.length} 个特征，生成 ${trendData.length} 个趋势点`);
        } else {
      featureTrendData.value = [];
      ElMessage.success(`成功提取 ${features.length} 个时域特征（数据量不足，无法生成趋势）`);
    }
    
  } catch (error) {
    ElMessage.error('特征提取失败: ' + error.message);
    console.error(error);
  } finally {
    featureLoading.value = false;
  }
}

// ==================== 时域特征计算函数 ====================

// 均值
function calculateMean(data) {
  if (data.length === 0) return 0;
  const sum = data.reduce((acc, val) => acc + val, 0);
  return sum / data.length;
}

// 方差
function calculateVariance(data) {
  if (data.length === 0) return 0;
  const mean = calculateMean(data);
  const squaredDiffs = data.map(val => Math.pow(val - mean, 2));
  return calculateMean(squaredDiffs);
}

// 标准差
function calculateStd(data) {
  return Math.sqrt(calculateVariance(data));
}

// 均方根 (RMS)
function calculateRMS(data) {
  if (data.length === 0) return 0;
  const squares = data.map(val => val * val);
  const meanSquare = calculateMean(squares);
  return Math.sqrt(meanSquare);
}

// 峰值
function calculatePeak(data) {
  if (data.length === 0) return 0;
  return Math.max(...data.map(v => Math.abs(v)));
}

// 峰峰值
function calculatePeak2Peak(data) {
  if (data.length === 0) return 0;
  return Math.max(...data) - Math.min(...data);
}

// 峭度 (Kurtosis)
function calculateKurtosis(data) {
  if (data.length === 0) return 0;
  const mean = calculateMean(data);
  const std = calculateStd(data);
  if (std === 0) return 0;
  
  const fourthMoment = data.reduce((acc, val) => {
    return acc + Math.pow((val - mean) / std, 4);
  }, 0) / data.length;
  
  return fourthMoment - 3; // 减3得到超额峭度
}

// 偏度 (Skewness)
function calculateSkewness(data) {
  if (data.length === 0) return 0;
  const mean = calculateMean(data);
  const std = calculateStd(data);
  if (std === 0) return 0;
  
  const thirdMoment = data.reduce((acc, val) => {
    return acc + Math.pow((val - mean) / std, 3);
  }, 0) / data.length;
  
  return thirdMoment;
}

// 方根幅值 (用于裕度因子)
function calculateSqrtMeanRoot(data) {
  if (data.length === 0) return 0;
  const absData = data.map(v => Math.abs(v));
  const sqrtData = absData.map(v => Math.sqrt(v));
  const meanSqrt = calculateMean(sqrtData);
  return meanSqrt * meanSqrt;
}

// 绘制特征趋势图
function renderFeatureTrendChart() {
  const chartEl = featureTrendChart.value;
  if (!chartEl || featureTrendData.value.length === 0) return;
  
  // 销毁旧图表
  if (chartInstances.value.featureTrend) {
    chartInstances.value.featureTrend.dispose();
  }
  
  const chart = echarts.init(chartEl);
  chartInstances.value.featureTrend = chart;
  
  // 准备系列数据
  const series = [];
  const legendData = [];
  
  featureConfig.value.selectedFeatures.forEach(featName => {
    const seriesData = featureTrendData.value.map(point => [
      new Date(point.timestamp),
      point.features[featName]
    ]);
    
    const featureLabel = getFeatureLabel(featName);
    legendData.push(featureLabel);
    
    series.push({
      name: featureLabel,
      type: 'line',
      data: seriesData,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: {
        width: 2
      }
    });
  });
  
  // 配置图表
  const option = {
    title: {
      text: `${featureConfig.value.selectedParam} - 特征时域演化`,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const date = new Date(params[0].value[0]);
        const dateStr = date.toLocaleString('zh-CN');
        let result = `${dateStr}<br/>`;
        params.forEach(param => {
          result += `${param.seriesName}: ${param.value[1].toFixed(4)}<br/>`;
        });
        return result;
      }
    },
    legend: {
      data: legendData,
      top: 30,
      type: 'scroll'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
      axisLabel: {
        formatter: (value) => {
          const date = new Date(value);
          return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
            minute: '2-digit'
          });
        }
      }
    },
    yAxis: {
      type: 'value',
      name: '特征值',
      axisLabel: {
        formatter: (value) => value.toFixed(2)
      }
    },
    series: series,
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 25
      }
    ]
  };
  
  chart.setOption(option);
}

// ==================== 辅助函数 ====================

function getFeatureLabel(feature) {
  return featureLabels[feature] || feature;
}

function formatFeatureValue(value) {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  if (Math.abs(value) < 0.001 || Math.abs(value) > 1000) {
    return value.toExponential(4);
  }
  return value.toFixed(6);
}

// 特征选择快捷操作
function selectAllFeatures() {
  featureConfig.value.selectedFeatures = [
    'mean', 'std', 'variance', 'rms', 'peak', 'peak2peak',
    'kurtosis', 'skewness', 'crest_factor', 'impulse_factor',
    'shape_factor', 'clearance_factor', 'kurtosis_factor'
  ];
}

function selectCommonFeatures() {
  featureConfig.value.selectedFeatures = ['mean', 'std', 'rms', 'peak', 'peak2peak', 'crest_factor'];
}

function clearAllFeatures() {
  featureConfig.value.selectedFeatures = [];
}

// 清空特征结果
function clearFeatures() {
  extractedFeatures.value = [];
  featureTrendData.value = [];
  featureConfig.value.selectedFeatures = ['mean', 'std', 'rms', 'peak', 'peak2peak'];
  
  // 销毁趋势图
  if (chartInstances.value.featureTrend) {
    chartInstances.value.featureTrend.dispose();
    delete chartInstances.value.featureTrend;
  }
}

// 导出特征
function exportFeatures() {
  if (extractedFeatures.value.length === 0) {
    ElMessage.warning('没有可导出的特征');
    return;
  }
  
  const exportData = {
    cmg_id: query.value.cmgId,
    parameter: featureConfig.value.selectedParam,
    time_range: {
      start: query.value.dates[0],
      end: query.value.dates[1]
    },
    window_size: featureConfig.value.windowSize,
    step_size: featureConfig.value.stepSize,
    sample_count: rawData.value.length,
    // 全时段统计特征
    statistical_features: extractedFeatures.value.reduce((obj, item) => {
      obj[item.feature] = {
        value: item.value,
        label: getFeatureLabel(item.feature),
        description: item.description
      };
      return obj;
    }, {}),
    // 特征时域趋势
    feature_trends: featureTrendData.value.length > 0 ? {
      trend_points: featureTrendData.value.length,
      data: featureTrendData.value
    } : null,
    extracted_at: new Date().toISOString()
  };
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `time_domain_features_${featureConfig.value.selectedParam}_${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  ElMessage.success('特征及趋势数据已导出');
}

// 监听窗口大小变化，重绘图表
function handleResize() {
  Object.values(chartInstances.value).forEach(chart => {
    if (chart) chart.resize();
  });
}

// 监听参数选择变化，自动重绘图表
watch(() => selectedParams.value, async () => {
  if (dataLoaded.value) {
    await nextTick();
    renderCharts();
  }
}, { deep: true });

// 生命周期
onMounted(() => {
  loadCmgs();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  // 销毁所有图表
  Object.values(chartInstances.value).forEach(chart => {
    if (chart) chart.dispose();
  });
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
/* 页面主容器 */
.time-domain-analysis-page {
  padding: 0;
  background: var(--cmg-bg-secondary);
  min-height: calc(100vh - 80px);
}

/* 查询卡片 */
.query-card {
  margin-bottom: 16px;
}

.query-form {
  padding: 8px 0;
}

.query-form :deep(.el-form-item) {
  margin-right: 16px;
  margin-bottom: 12px;
}

.cmg-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cmg-option-id {
  color: var(--cmg-text-tertiary);
  font-size: 12px;
  font-family: monospace;
}

/* 数据库统计 */
.database-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-tag {
  margin-right: 4px;
}

.stat-tag .el-icon {
  margin-right: 4px;
}

/* 分析容器 */
.analysis-container {
  margin-top: 16px;
}

/* 等高行列布局 */
.equal-height-row {
  display: flex;
  align-items: stretch;
}

.equal-height-col {
  display: flex;
  flex-direction: column;
}

/* 图表卡片 */
.chart-card {
  width: 100%;
}

.chart-card :deep(.el-card__body) {
  padding: 16px;
}

.chart-container {
  width: 100%;
}

/* 参数选择器 */
.param-selector {
  margin-bottom: 16px;
}

.selector-label {
  display: block;
  font-size: 13px;
  color: var(--cmg-text-secondary);
  margin-bottom: 8px;
  font-weight: 500;
}


.param-chart {
  margin-bottom: 12px;
}

.chart-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--cmg-text-primary);
  margin-bottom: 6px;
  padding: 4px 8px;
  background: var(--cmg-bg-tertiary);
  border-left: 3px solid var(--cmg-aerospace-primary);
  border-radius: 4px;
}

.chart {
  width: 100%;
  height: 300px;
}

.chart-compact {
  height: 160px;
}

.empty-hint {
  padding: 60px 0;
}

/* 特征卡片 */
.feature-card {
  width: 100%;
}

.feature-card :deep(.el-card__body) {
  padding: 16px;
}

.feature-extraction {
  width: 100%;
}

.feature-extraction :deep(.el-form-item) {
  margin-bottom: 16px;
}

/* 特征选择网格布局 */
.feature-checkbox-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px 12px;
  margin-bottom: 12px;
}

.feature-checkbox-grid :deep(.el-checkbox) {
  margin-right: 0;
  white-space: nowrap;
  font-size: 13px;
}

/* 特征选择底部按钮 */
.feature-selection-footer {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--cmg-border-light);
  display: flex;
  justify-content: center;
}

.param-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.time-hint {
  font-size: 12px;
  color: #67c23a;
  margin-top: 4px;
  font-weight: 500;
}

/* 特征结果 */
.feature-results {
  margin-top: 24px;
}

.feature-value {
  font-family: monospace;
  font-weight: 600;
  color: var(--cmg-aerospace-primary);
  font-size: 13px;
}

.feature-actions {
  margin-top: 16px;
  text-align: center;
}

/* 特征趋势图 */
.feature-trend {
  margin-top: 24px;
}

.trend-info {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.trend-chart {
  width: 100%;
  height: 400px;
  margin-top: 8px;
}

/* 空状态 */
.empty-state {
  padding: 120px 0;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .equal-height-row {
    flex-direction: column;
  }
  
  .equal-height-col {
    width: 100%;
    margin-bottom: 16px;
  }
  }
  
@media (max-width: 768px) {
  .query-form :deep(.el-form) {
    flex-direction: column;
  }
  
  .query-form :deep(.el-form-item) {
    margin-right: 0;
    width: 100%;
  }
  
  .chart-compact {
    height: 150px;
  }
}

/* 响应式布局 */
@media (max-width: 1400px) {
  .feature-checkbox-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 1024px) {
  .feature-checkbox-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .feature-checkbox-grid {
    grid-template-columns: 1fr;
  }
}
</style>
