<template>
  <div class="smart-sensing">
    <el-card class="page-header" shadow="never">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon class="title-icon"><TrendCharts /></el-icon>
            CMG智能感知方法研究
          </h1>
          <p class="page-description">基于退化预测的CMG智能感知及多层耦合方法研究</p>
        </div>
      </div>
    </el-card>

    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- Tab 1: 预测性能对比 -->
      <el-tab-pane label="预测性能对比" name="prediction">
        <el-card class="control-panel" shadow="never">
          <div class="control-row">
            <label class="control-label">实验编号:</label>
            <el-radio-group v-model="selectedExp" size="large" @change="loadPredictionData">
              <el-radio-button value="015">案例一</el-radio-button>
              <el-radio-button value="016">案例二</el-radio-button>
              <el-radio-button value="017">案例三</el-radio-button>
            </el-radio-group>
            
            <el-button 
              type="primary" 
              :icon="RefreshRight"
              @click="loadPredictionData"
              :loading="predictionLoading"
              style="margin-left: 20px;"
            >
              刷新数据
            </el-button>
          </div>
        </el-card>

        <!-- 预测结果对比图 -->
        <el-card class="viz-panel" shadow="never" v-loading="predictionLoading">
          <div class="panel-header">
            <h2 class="panel-title">
              <el-icon><TrendCharts /></el-icon>
              预测结果对比
            </h2>
            <div class="panel-desc">基准模型与融合模型的预测性能对比</div>
          </div>

          <div class="chart-container" v-if="predictionData">
            <div ref="chartPrediction" class="chart large"></div>
          </div>
        </el-card>

        <!-- 性能指标对比表格 -->
        <el-card class="viz-panel" shadow="never" v-if="predictionData">
          <div class="panel-header">
            <h2 class="panel-title">
              <el-icon><DataAnalysis /></el-icon>
              性能指标对比
            </h2>
            <div class="panel-desc">不同模型的预测精度指标</div>
          </div>

          <el-table :data="metricsTableData" border stripe>
            <el-table-column prop="model" label="模型名称" align="center" width="200">
              <template #default="{ row }">
                <el-tag :type="row.isBest ? 'success' : 'info'" size="small">
                  {{ row.model }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="mse" label="MSE" align="center">
              <template #default="{ row }">
                <span :class="{ 'metric-best': row.isBest }">{{ row.mse }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="mae" label="MAE" align="center">
              <template #default="{ row }">
                <span :class="{ 'metric-best': row.isBest }">{{ row.mae }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="rmse" label="RMSE" align="center">
              <template #default="{ row }">
                <span :class="{ 'metric-best': row.isBest }">{{ row.rmse }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="r2" label="R²" align="center">
              <template #default="{ row }">
                <span :class="{ 'metric-best': row.isBest }">{{ row.r2 }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <!-- Tab 2: 退化耦合层级 -->
      <el-tab-pane label="退化耦合层级" name="coupling">
        <el-card class="control-panel" shadow="never">
          <div class="control-row">
            <el-button 
              type="primary" 
              :icon="RefreshRight"
              @click="loadCouplingData"
              :loading="couplingLoading"
            >
              刷新数据
            </el-button>
          </div>
        </el-card>

        <!-- 退化耦合层级展示 -->
        <el-card class="viz-panel" shadow="never" v-loading="couplingLoading">
          <div class="panel-header">
            <h2 class="panel-title">
              <el-icon><Connection /></el-icon>
              多层退化耦合效应
            </h2>
            <div class="panel-desc">轴承退化对系统性能的逐层影响分析</div>
          </div>

          <div class="coupling-charts-container" v-if="couplingData">
            <!-- Layer 1 -->
            <div class="chart-box">
              <div class="chart-title">{{ couplingData.layer1?.fig_info?.title }}</div>
              <div ref="chartLayer1" class="chart"></div>
            </div>

            <!-- Layer 2 -->
            <div class="chart-box">
              <div class="chart-title">{{ couplingData.layer2?.fig_info?.title }}</div>
              <div ref="chartLayer2" class="chart"></div>
            </div>

            <!-- Layer 3 -->
            <div class="chart-box">
              <div class="chart-title">{{ couplingData.layer3?.fig_info?.title }}</div>
              <div ref="chartLayer3" class="chart"></div>
            </div>
          </div>
        </el-card>

        <!-- 耦合机理说明 -->
        <el-card class="info-panel" shadow="never">
          <h3 class="info-title">
            <el-icon><InfoFilled /></el-icon>
            耦合机理说明
          </h3>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="info-card">
                <div class="info-card-header">
                  <el-icon class="info-icon" color="#E6A23C"><Warning /></el-icon>
                  <h4>第一层耦合</h4>
                </div>
                <p>高速轴承退化导致摩擦力矩增大，直接影响高速转子的运动特性</p>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-card">
                <div class="info-card-header">
                  <el-icon class="info-icon" color="#F56C6C"><TrendCharts /></el-icon>
                  <h4>第二层耦合</h4>
                </div>
                <p>耦合力矩增大影响框架跟踪精度，导致指令跟踪误差增大</p>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-card">
                <div class="info-card-header">
                  <el-icon class="info-icon" color="#909399"><Setting /></el-icon>
                  <h4>第三层耦合</h4>
                </div>
                <p>控制精度下降最终导致CMG输出力矩精度降低，影响系统性能</p>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-tab-pane>

      <!-- Tab 3: 技术说明 -->
      <el-tab-pane label="技术说明" name="info">
        <el-card class="info-panel" shadow="never">
          <h3 class="info-title">
            <el-icon><Document /></el-icon>
            研究概述
          </h3>
          <div class="info-content">
            <h4>研究背景</h4>
            <p>
              控制力矩陀螺(CMG)是航天器姿态控制的核心部件，其健康状态直接影响航天器的姿态控制精度和可靠性。
              本研究基于图神经网络(GCN)构建了CMG退化预测模型，实现了对CMG健康状态的智能感知和预测。
            </p>

            <h4>技术特点</h4>
            <ul>
              <li><strong>多传感器融合</strong>：融合高速电机电流、温度、转速等多维传感器数据</li>
              <li><strong>图神经网络</strong>：利用GCN捕捉传感器间的关联关系和时序特征</li>
              <li><strong>多层耦合分析</strong>：揭示轴承退化对系统性能的逐层影响机理</li>
              <li><strong>自适应学习</strong>：通过在线学习实现模型的自扩展和动态更新</li>
            </ul>

            <h4>模型对比</h4>
            <ul>
              <li><strong>基准模型(Base)</strong>：仅使用基础传感器数据(高速电机电流、温度、转速)</li>
              <li><strong>融合模型 B/K</strong>：融合轴承摩擦系数(b)和刚度(k)隐参数</li>
              <li><strong>融合模型 μ/ν</strong>：融合润滑效率(μ)和粘度(ν)隐参数</li>
            </ul>

            <h4>实验数据</h4>
            <p>
              实验数据来自多个CMG长期运行测试(编号015-018)，涵盖了从正常到退化的完整生命周期数据。
              通过对比不同模型的预测性能，验证了融合隐参数的有效性。
            </p>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, watch } from 'vue';
import * as echarts from 'echarts';
import { 
  TrendCharts, RefreshRight, DataAnalysis, Connection,
  InfoFilled, Document, Warning, Setting
} from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import api from '../api';

// Tab状态
const activeTab = ref('prediction');

// 预测模块状态
const selectedExp = ref('015');
const predictionLoading = ref(false);
const predictionData = ref(null);

// 耦合层级模块状态
const couplingLoading = ref(false);
const couplingData = ref(null);

// 图表DOM引用 - 使用Vue ref
const chartPrediction = ref(null);
const chartLayer1 = ref(null);
const chartLayer2 = ref(null);
const chartLayer3 = ref(null);

// 性能指标表格数据
const metricsTableData = ref([]);

// 监听标签页切换，重新渲染图表
watch(activeTab, async (newTab) => {
  console.log('Tab changed to:', newTab);
  await nextTick();
  
  if (newTab === 'prediction' && predictionData.value) {
    console.log('Re-rendering prediction chart after tab change');
    renderPredictionChart();
  } else if (newTab === 'coupling' && couplingData.value) {
    console.log('Re-rendering coupling charts after tab change');
    renderCouplingCharts();
  }
});

// 加载预测数据
async function loadPredictionData() {
  predictionLoading.value = true;
  try {
    const response = await api.get(`/intelligent-sensing/prediction-results/?exp=${selectedExp.value}`);
    predictionData.value = response.data;
    
    // 更新表格数据
    updateMetricsTable();
    
    // 渲染图表
    await nextTick();
    renderPredictionChart();
    
    ElMessage.success('数据加载成功');
  } catch (error) {
    console.error('加载预测数据失败:', error);
    ElMessage.error('加载数据失败');
  } finally {
    predictionLoading.value = false;
  }
}

// 更新性能指标表格
function updateMetricsTable() {
  if (!predictionData.value) return;
  
  const data = predictionData.value;
  metricsTableData.value = [
    {
      model: '基准模型 (Base)',
      mse: data.base?.metrics?.mse?.toFixed(4) || 'N/A',
      mae: data.base?.metrics?.mae?.toFixed(4) || 'N/A',
      rmse: data.base?.metrics?.rmse?.toFixed(4) || 'N/A',
      r2: data.base?.metrics?.r2?.toFixed(4) || 'N/A',
      isBest: false
    },
    {
      model: '融合模型 (B/K)',
      mse: data.fusion_b_k?.metrics?.mse?.toFixed(4) || 'N/A',
      mae: data.fusion_b_k?.metrics?.mae?.toFixed(4) || 'N/A',
      rmse: data.fusion_b_k?.metrics?.rmse?.toFixed(4) || 'N/A',
      r2: data.fusion_b_k?.metrics?.r2?.toFixed(4) || 'N/A',
      isBest: false
    },
    {
      model: '融合模型 (μ/ν)',
      mse: data.fusion_u_v?.metrics?.mse?.toFixed(4) || 'N/A',
      mae: data.fusion_u_v?.metrics?.mae?.toFixed(4) || 'N/A',
      rmse: data.fusion_u_v?.metrics?.rmse?.toFixed(4) || 'N/A',
      r2: data.fusion_u_v?.metrics?.r2?.toFixed(4) || 'N/A',
      isBest: true
    }
  ];
}

// 渲染预测对比图表
function renderPredictionChart() {
  console.log('renderPredictionChart called', {
    hasData: !!predictionData.value,
    hasRef: !!chartPrediction.value,
    dataKeys: predictionData.value ? Object.keys(predictionData.value) : []
  });
  
  if (!predictionData.value || !chartPrediction.value) return;
  
  const chart = echarts.getInstanceByDom(chartPrediction.value) || echarts.init(chartPrediction.value);
  
  const data = predictionData.value;
  console.log('Chart data loaded:', {
    trueLabelsLength: data.base?.true_labels?.length,
    predLabelsLength: data.base?.pred_labels?.length
  });
  const indices = Array.from({ length: data.base.true_labels.length }, (_, i) => i);
  
  const expNameMap = {
    '015': '案例一',
    '016': '案例二',
    '017': '案例三'
  };
  const expTitle = expNameMap[selectedExp.value] || selectedExp.value;

  const option = {
    title: {
      text: `${expTitle}预测结果对比`,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['真实值', '基准模型', '融合模型(B/K)', '融合模型(μ/ν)'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: indices,
      name: '样本点'
    },
    yAxis: {
      type: 'value',
      name: '退化值'
    },
    series: [
      {
        name: '真实值',
        type: 'line',
        data: data.base.true_labels,
        lineStyle: { width: 2, color: '#5470c6' },
        symbol: 'none'
      },
      {
        name: '基准模型',
        type: 'line',
        data: data.base.pred_labels,
        lineStyle: { width: 1.5, color: '#91cc75' },
        symbol: 'none'
      },
      {
        name: '融合模型(B/K)',
        type: 'line',
        data: data.fusion_b_k.pred_labels,
        lineStyle: { width: 1.5, color: '#fac858' },
        symbol: 'none'
      },
      {
        name: '融合模型(μ/ν)',
        type: 'line',
        data: data.fusion_u_v.pred_labels,
        lineStyle: { width: 1.5, color: '#ee6666' },
        symbol: 'none'
      }
    ]
  };
  
  chart.setOption(option);
}

// 加载耦合层级数据
async function loadCouplingData() {
  couplingLoading.value = true;
  try {
    const response = await api.get('/intelligent-sensing/coupling-layers/');
    couplingData.value = response.data;
    
    console.log('Coupling data loaded, current tab:', activeTab.value);
    
    // 只有在当前Tab是coupling时才立即渲染图表
    // 否则等待用户切换到coupling tab时再渲染（通过watch实现）
    if (activeTab.value === 'coupling') {
      await nextTick();
      renderCouplingCharts();
    } else {
      console.log('Coupling data loaded but not rendering yet (waiting for tab switch)');
    }
    
    ElMessage.success('数据加载成功');
  } catch (error) {
    console.error('加载耦合层级数据失败:', error);
    ElMessage.error('加载数据失败');
  } finally {
    couplingLoading.value = false;
  }
}

// 渲染耦合层级图表
function renderCouplingCharts() {
  console.log('renderCouplingCharts called', {
    hasData: !!couplingData.value,
    hasLayer1Ref: !!chartLayer1.value,
    hasLayer2Ref: !!chartLayer2.value,
    hasLayer3Ref: !!chartLayer3.value,
    dataKeys: couplingData.value ? Object.keys(couplingData.value) : []
  });
  
  if (!couplingData.value) return;
  
  const data = couplingData.value;
  
  console.log('Coupling data structure:', {
    hasT: !!data.t,
    tLength: data.t?.length,
    hasLayer1: !!data.layer1,
    hasLayer2: !!data.layer2,
    hasLayer3: !!data.layer3
  });
  
  // Layer 1
  renderLayerChart('layer1', data.t, data.layer1);
  
  // Layer 2
  renderLayerChart('layer2', data.t, data.layer2);
  
  // Layer 3
  renderLayerChart('layer3', data.t, data.layer3);
}

// 渲染单个层级图表
function renderLayerChart(layerKey, timeData, layerData) {
  let dom = null;
  if (layerKey === 'layer1') dom = chartLayer1.value;
  else if (layerKey === 'layer2') dom = chartLayer2.value;
  else if (layerKey === 'layer3') dom = chartLayer3.value;
  
  console.log(`renderLayerChart(${layerKey})`, {
    hasDom: !!dom,
    hasTimeData: !!timeData,
    timeDataLength: timeData?.length,
    hasLayerData: !!layerData,
    layerDataKeys: layerData ? Object.keys(layerData) : []
  });
  
  if (!dom) {
    console.warn(`No DOM for ${layerKey}`);
    return;
  }
  
  const chart = echarts.getInstanceByDom(dom) || echarts.init(dom);
  console.log(`Chart initialized for ${layerKey}`);
  
  const seriesData = [];
  const legendData = [];
  
  // 添加level曲线
  Object.keys(layerData.data).forEach(key => {
    if (key !== 'Ω_cmd') {
      seriesData.push({
        name: key,
        type: 'line',
        data: layerData.data[key],
        symbol: 'none',
        lineStyle: { width: 2 }
      });
      legendData.push(key);
    }
  });
  
  // 如果有参考线(如Ω_cmd)，单独添加
  if (layerData.data.Ω_cmd) {
    seriesData.push({
      name: 'Ω_cmd (指令值)',
      type: 'line',
      data: layerData.data.Ω_cmd,
      symbol: 'none',
      lineStyle: { 
        width: 2, 
        type: 'dashed',
        color: '#909399'
      }
    });
    legendData.push('Ω_cmd (指令值)');
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: legendData,
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: timeData,
      name: '时间'
    },
    yAxis: {
      type: 'value',
      name: layerData.fig_info.ylabel
    },
    series: seriesData
  };
  
  chart.setOption(option);
}

// 窗口大小变化时调整图表
function handleResize() {
  const refs = [chartPrediction.value, chartLayer1.value, chartLayer2.value, chartLayer3.value];
  refs.forEach(dom => {
    if (dom) {
      const chart = echarts.getInstanceByDom(dom);
      if (chart) {
        chart.resize();
      }
    }
  });
}

// 组件挂载
onMounted(() => {
  // 等待DOM渲染完成后加载数据
  nextTick(() => {
    loadPredictionData();
    loadCouplingData();
  });
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize);
});

// 组件卸载
onBeforeUnmount(() => {
  // 销毁图表实例
  const refs = [chartPrediction.value, chartLayer1.value, chartLayer2.value, chartLayer3.value];
  refs.forEach(dom => {
    if (dom) {
      const chart = echarts.getInstanceByDom(dom);
      if (chart) {
        chart.dispose();
      }
    }
  });
  
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.smart-sensing {
  padding: 0;
}

/* 页面头部 */
.page-header {
  margin-bottom: var(--cmg-space-4);
  background: linear-gradient(135deg, var(--cmg-bg-primary), var(--cmg-bg-secondary));
  border: none;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-3);
  margin: 0 0 var(--cmg-space-2) 0;
  font-size: var(--cmg-text-2xl);
  font-weight: 700;
  color: var(--cmg-aerospace-primary);
}

.title-icon {
  font-size: 32px;
  color: var(--cmg-aerospace-accent);
}

.page-description {
  margin: 0;
  color: var(--cmg-text-secondary);
  font-size: var(--cmg-text-base);
}

/* 控制面板 */
.control-panel {
  margin-bottom: var(--cmg-space-4);
}

.control-row {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-3);
}

.control-label {
  font-weight: 600;
  color: var(--cmg-text-primary);
}

/* 可视化面板 */
.viz-panel {
  margin-bottom: var(--cmg-space-4);
}

.panel-header {
  margin-bottom: var(--cmg-space-4);
  padding-bottom: var(--cmg-space-3);
  border-bottom: 2px solid var(--cmg-border-light);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
  margin: 0 0 var(--cmg-space-2) 0;
  font-size: var(--cmg-text-xl);
  font-weight: 600;
  color: var(--cmg-text-primary);
}

.panel-desc {
  color: var(--cmg-text-secondary);
  font-size: var(--cmg-text-sm);
}

/* 图表容器 */
.chart-container {
  width: 100%;
}

.chart {
  width: 100%;
  height: 400px;
}

.chart.large {
  height: 500px;
}

.coupling-charts-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--cmg-space-6);
}

.chart-box {
  background: var(--cmg-bg-primary);
  border-radius: var(--cmg-radius-lg);
  padding: var(--cmg-space-4);
  box-shadow: var(--cmg-shadow-sm);
}

.chart-title {
  font-size: var(--cmg-text-lg);
  font-weight: 600;
  color: var(--cmg-text-primary);
  margin-bottom: var(--cmg-space-3);
  text-align: center;
}

/* 表格样式 */
.metric-best {
  color: var(--el-color-success);
  font-weight: 600;
}

/* 信息面板 */
.info-panel {
  margin-bottom: var(--cmg-space-4);
}

.info-title {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
  margin: 0 0 var(--cmg-space-4) 0;
  font-size: var(--cmg-text-xl);
  font-weight: 600;
  color: var(--cmg-text-primary);
}

.info-card {
  background: var(--cmg-bg-secondary);
  border-radius: var(--cmg-radius-lg);
  padding: var(--cmg-space-4);
  height: 100%;
  transition: var(--cmg-transition-all);
}

.info-card:hover {
  box-shadow: var(--cmg-shadow-md);
  transform: translateY(-2px);
}

.info-card-header {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
  margin-bottom: var(--cmg-space-3);
}

.info-card-header h4 {
  margin: 0;
  font-size: var(--cmg-text-lg);
  font-weight: 600;
  color: var(--cmg-text-primary);
}

.info-icon {
  font-size: 24px;
}

.info-card p {
  margin: 0;
  color: var(--cmg-text-secondary);
  line-height: 1.6;
}

.info-content {
  line-height: 1.8;
  color: var(--cmg-text-primary);
}

.info-content h4 {
  margin-top: var(--cmg-space-4);
  margin-bottom: var(--cmg-space-2);
  font-size: var(--cmg-text-lg);
  font-weight: 600;
  color: var(--cmg-aerospace-primary);
}

.info-content ul {
  margin: var(--cmg-space-2) 0;
  padding-left: var(--cmg-space-6);
}

.info-content li {
  margin: var(--cmg-space-2) 0;
  color: var(--cmg-text-secondary);
}

.info-content strong {
  color: var(--cmg-text-primary);
  font-weight: 600;
}

/* 暗色主题适配 */
[data-theme="dark"] .page-header {
  background: linear-gradient(135deg, var(--cmg-gray-900), var(--cmg-gray-800));
}

[data-theme="dark"] .chart-box {
  background: var(--cmg-gray-800);
}

[data-theme="dark"] .info-card {
  background: var(--cmg-gray-800);
}
</style>
