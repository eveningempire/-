<template>
  <div class="degradation-simulation">
    <el-card class="page-header" shadow="never">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon class="title-icon"><TrendCharts /></el-icon>
            空间执行机构退化规律的健康演化模型
          </h1>
          <p class="page-description">CMG退退化规律的健康演化模型可视化</p>
        </div>
      </div>
    </el-card>

    <el-card class="control-panel" shadow="never">
      <div class="control-row">
        <div class="control-item">
          <label class="control-label">退化类型</label>
          <el-select 
            v-model="selectedType" 
            placeholder="请选择退化类型"
            size="large"
            @change="loadData"
          >
            <el-option
              v-for="item in degradationTypes"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
              <span class="option-content">
                <el-icon><Position /></el-icon>
                {{ item.label }}
              </span>
            </el-option>
          </el-select>
        </div>

        <div class="control-item">
          <label class="control-label">工况条件</label>
          <el-select 
            v-model="selectedCondition" 
            placeholder="请选择工况条件"
            size="large"
            @change="loadData"
          >
            <el-option
              v-for="item in workingConditions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
              <span class="option-content">
                <el-icon><Setting /></el-icon>
                {{ item.label }}
              </span>
            </el-option>
          </el-select>
        </div>

        <div class="control-item button-group">
          <el-button 
            type="primary" 
            size="large"
            :icon="RefreshRight"
            @click="loadData"
            :loading="dataLoading"
          >
            刷新显示
          </el-button>
          
          <el-button 
            type="success" 
            size="large"
            :icon="TrendCharts"
            @click="showHICurvesDialog"
          >
            参数退化注入
          </el-button>
          
          <el-button 
            type="warning" 
            size="large"
            :icon="PictureFilled"
            @click="showPathDiagramDialog"
          >
            退化路径图示
          </el-button>
        </div>
      </div>
        </el-card>

    <!-- 第一步：参数退化注入 -->
    <el-card class="visualization-panel step-panel" shadow="never">
      <div class="panel-header">
        <h2 class="panel-title">
          <span class="step-badge">步骤 1</span>
          <el-icon><TrendCharts /></el-icon>
          参数退化注入曲线
        </h2>
        <div class="panel-actions">
          <el-button 
            type="primary"
            :icon="TrendCharts"
            @click="showHICurvesDialog"
          >
            查看完整HI曲线
          </el-button>
        </div>
      </div>
      
      <div class="step-description">
        <el-icon><InfoFilled /></el-icon>
        基于维纳过程的参数退化注入，模拟CMG关键参数随时间的退化趋势
      </div>

      <div class="hi-curves-preview" ref="chartHIPreview" v-loading="hiCurvesLoading"></div>
    </el-card>

    <!-- 连接箭头 -->
    <div class="chain-connector">
      <el-icon class="connector-icon"><Bottom /></el-icon>
    </div>

    <!-- 第二步：局部仿真信息 -->
    <el-card class="visualization-panel step-panel" shadow="never" v-loading="dataLoading">
      <div class="panel-header">
        <h2 class="panel-title">
          <span class="step-badge step-badge-2">步骤 2</span>
          <el-icon><DataAnalysis /></el-icon>
          局部仿真信息
        </h2>
        <div class="panel-actions">
          <el-tag type="info" effect="plain">时间尺度：秒级</el-tag>
        </div>
      </div>
      
      <div class="step-description">
        <el-icon><InfoFilled /></el-icon>
        局部时间段内的高速电机电流和电压变化曲线，反映退化参数对电机性能的影响
      </div>

      <div class="charts-grid-horizontal" v-if="currentData && !dataError">
        <!-- 局部电流 -->
        <div class="chart-wrapper">
          <div class="chart-title">局部高速电机电流曲线</div>
          <div ref="chartShortCurrent" class="chart-container"></div>
        </div>
        
        <!-- 局部电压 -->
        <div class="chart-wrapper">
          <div class="chart-title">局部高速电机电压曲线</div>
          <div ref="chartShortVoltage" class="chart-container"></div>
        </div>
      </div>

      <el-empty 
        v-else-if="dataError"
        description="数据加载失败，请检查JSON文件是否存在"
        :image-size="200"
      >
        <el-button type="primary" @click="loadData">重新加载</el-button>
      </el-empty>

      <el-empty 
        v-else
        description="请选择退化类型和工况条件以查看仿真结果"
        :image-size="200"
      />
    </el-card>

    <!-- 连接箭头 -->
    <div class="chain-connector">
      <el-icon class="connector-icon"><Bottom /></el-icon>
    </div>

    <!-- 第三步：整体仿真结果 -->
    <el-card class="visualization-panel step-panel" shadow="never" v-loading="dataLoading">
      <div class="panel-header">
        <h2 class="panel-title">
          <span class="step-badge step-badge-3">步骤 3</span>
          <el-icon><PictureFilled /></el-icon>
          整体仿真结果
        </h2>
        <div class="panel-actions">
          <el-tag type="success" effect="plain">时间尺度：天级</el-tag>
          <el-button 
            :icon="Download" 
            @click="downloadCharts"
            :disabled="!currentData"
          >
            导出图表
          </el-button>
        </div>
      </div>
      
      <div class="step-description">
        <el-icon><InfoFilled /></el-icon>
        整个生命周期内的全局电流和电压演化趋势，展示退化对整体健康状态的长期影响
      </div>

      <div class="charts-grid-horizontal" v-if="currentData && !dataError">
        <!-- 全局电流 -->
        <div class="chart-wrapper">
          <div class="chart-title">全局高速电机电流曲线</div>
          <div ref="chartFullCurrent" class="chart-container"></div>
        </div>
        
        <!-- 全局电压 -->
        <div class="chart-wrapper">
          <div class="chart-title">全局高速电机电压曲线</div>
          <div ref="chartFullVoltage" class="chart-container"></div>
        </div>
      </div>

      <el-empty 
        v-else-if="dataError"
        description="数据加载失败，请检查JSON文件是否存在"
        :image-size="200"
      >
        <el-button type="primary" @click="loadData">重新加载</el-button>
      </el-empty>

      <el-empty 
        v-else
        description="请选择退化类型和工况条件以查看仿真结果"
        :image-size="200"
      />
    </el-card>

    <!-- 数据集说明 -->
    <el-card class="info-panel" shadow="never">
      <h3 class="info-title">
        <el-icon><InfoFilled /></el-icon>
        数据集说明
      </h3>
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="info-card">
            <div class="info-card-header">
              <el-icon class="info-icon" color="#409EFF"><Connection /></el-icon>
              <h4>退化类型</h4>
            </div>
            <ul class="info-list">
              <li><strong>磨损退化 (m)</strong>: 轴承磨损导致的性能退化</li>
              <li><strong>润滑退化 (r)</strong>: 润滑油老化引起的退化</li>
              <li><strong>综合退化 (z)</strong>: 磨损与润滑的耦合退化</li>
            </ul>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="info-card">
            <div class="info-card-header">
              <el-icon class="info-icon" color="#67C23A"><Setting /></el-icon>
              <h4>工况条件</h4>
            </div>
            <ul class="info-list">
              <li><strong>普通工况</strong>: 正常运行条件</li>
              <li><strong>加速寿命正弦工况</strong>: 正弦负载加速老化</li>
              <li><strong>加速寿命矩形工况</strong>: 矩形负载加速老化</li>
            </ul>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="info-card">
            <div class="info-card-header">
              <el-icon class="info-icon" color="#E6A23C"><DataAnalysis /></el-icon>
              <h4>图表特性</h4>
            </div>
            <ul class="info-list">
              <li><strong>交互缩放</strong>: 支持鼠标滚轮缩放</li>
              <li><strong>数据详情</strong>: 鼠标悬停查看数值</li>
              <li><strong>图表导出</strong>: 支持PNG格式导出</li>
            </ul>
          </div>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- HI曲线展示对话框 -->
    <el-dialog 
      v-model="hiCurvesDialogVisible" 
      title="参数退化注入曲线（基于维纳过程的参数退化注入）"
      width="85%"
      @opened="onDialogOpened"
    >
      <div class="dialog-controls">
        <label style="margin-right: 8px;">显示曲线数量:</label>
        <el-select 
          v-model="selectedCurveCount" 
          @change="renderHICurvesChart"
          style="width: 150px;"
          size="small"
        >
          <el-option label="前5条" :value="5" />
          <el-option label="前10条" :value="10" />
          <el-option label="全部" :value="-1" />
        </el-select>
      </div>
      <div ref="chartHICurves" class="hi-curves-chart" v-loading="hiCurvesLoading"></div>
    </el-dialog>
    
    <!-- 退化路径图示对话框 -->
    <el-dialog 
      v-model="pathDiagramDialogVisible" 
      title="退化路径图示"
      width="70%"
    >
      <div class="path-diagram-controls">
        <label style="margin-right: 8px;">选择退化路径:</label>
        <el-radio-group v-model="selectedPathType" @change="updatePathImage" size="large">
          <el-radio-button label="磨损退化路径" />
          <el-radio-button label="润滑退化路径" />
          <el-radio-button label="综合退化路径" />
        </el-radio-group>
      </div>
      <div class="path-diagram-container">
        <el-image 
          :src="currentPathImage" 
          fit="contain"
          style="width: 100%; height: 600px;"
          :preview-src-list="[currentPathImage]"
        >
          <template #error>
            <div class="image-error">
              <el-icon :size="50"><PictureFilled /></el-icon>
              <p>图片加载失败</p>
            </div>
          </template>
        </el-image>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue';
import * as echarts from 'echarts';
import { 
  TrendCharts, Position, Setting, RefreshRight, DataAnalysis, 
  Document, PictureFilled, Download, InfoFilled, Connection, Bottom
} from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

// 退化类型选项
const degradationTypes = [
  { value: 'm', label: '路径一:磨损退化' },
  { value: 'r', label: '路径二:润滑退化' },
  { value: 'z', label: '路径三:综合退化' }
];

// 工况条件选项
const workingConditions = [
  { value: '1', label: '普通工况' },
  { value: '2', label: '加速寿命试验-正弦工况' },
  { value: '3', label: '加速寿命试验矩形工况' }
];

// 选择的值
const selectedType = ref('m');
const selectedCondition = ref('1');

// 数据加载状态
const dataLoading = ref(false);
const dataError = ref(false);
const currentData = ref(null);

// ECharts实例
const chartFullCurrent = ref(null);
const chartShortCurrent = ref(null);
const chartFullVoltage = ref(null);
const chartShortVoltage = ref(null);

let chartInstanceFullCurrent = null;
let chartInstanceShortCurrent = null;
let chartInstanceFullVoltage = null;
let chartInstanceShortVoltage = null;

// HI曲线对话框
const hiCurvesDialogVisible = ref(false);
const hiCurvesData = ref(null);
const hiCurvesLoading = ref(false);
const chartHICurves = ref(null);
const chartHIPreview = ref(null);  // HI曲线预览
const selectedCurveCount = ref(5); // 默认显示前5条
let chartInstanceHICurves = null;
let chartInstanceHIPreview = null;  // HI曲线预览实例

// 退化路径图示对话框
const pathDiagramDialogVisible = ref(false);
const selectedPathType = ref('磨损退化路径'); // 默认选择
const currentPathImage = ref('/degradation-paths/磨损退化路径.png');

// 当前数据键
const currentDataKey = computed(() => {
  if (selectedType.value && selectedCondition.value) {
    return `${selectedType.value}${selectedCondition.value}`;
  }
  return '';
});

// 加载JSON数据
async function loadData() {
  if (!currentDataKey.value) return;
  
  dataLoading.value = true;
  dataError.value = false;
  
  try {
    const response = await fetch(`/simulation-data/plot_${currentDataKey.value}_ds20.json`);
    if (!response.ok) {
      throw new Error('数据文件不存在');
    }
    
    const data = await response.json();
    currentData.value = data;
    
    await nextTick();
    renderCharts();
    
    // 自动加载HI曲线预览
    if (!hiCurvesData.value) {
      await loadHICurvesData();
    }
    renderHIPreview();
    
    ElMessage.success('数据加载成功');
  } catch (error) {
    console.error('数据加载失败:', error);
    dataError.value = true;
    currentData.value = null;
    ElMessage.error('数据加载失败: ' + error.message);
  } finally {
    dataLoading.value = false;
  }
}

// 渲染图表
function renderCharts() {
  if (!currentData.value) return;
  
  // 初始化图表实例
  if (!chartInstanceFullCurrent && chartFullCurrent.value) {
    chartInstanceFullCurrent = echarts.init(chartFullCurrent.value);
  }
  if (!chartInstanceShortCurrent && chartShortCurrent.value) {
    chartInstanceShortCurrent = echarts.init(chartShortCurrent.value);
  }
  if (!chartInstanceFullVoltage && chartFullVoltage.value) {
    chartInstanceFullVoltage = echarts.init(chartFullVoltage.value);
  }
  if (!chartInstanceShortVoltage && chartShortVoltage.value) {
    chartInstanceShortVoltage = echarts.init(chartShortVoltage.value);
  }
  
  const data = currentData.value;
  
  // 全局电流图表
  const optionFullCurrent = createChartOption(
    data.days_full,
    data.current,
    '时间 (天)',
    '电流 (A)',
    '全局电流曲线',
    '#2563eb'
  );
  chartInstanceFullCurrent?.setOption(optionFullCurrent);
  
  // 局部电流图表
  const optionShortCurrent = createChartOption(
    data.days_short,
    data.I,
    '时间 (秒)',
    '电流 (A)',
    '局部电流曲线',
    '#0ea5e9'
  );
  chartInstanceShortCurrent?.setOption(optionShortCurrent);
  
  // 全局电压图表
  const optionFullVoltage = createChartOption(
    data.days_full,
    data.voltage,
    '时间 (天)',
    '电压 (V)',
    '全局电压曲线',
    '#dc2626'
  );
  chartInstanceFullVoltage?.setOption(optionFullVoltage);
  
  // 局部电压图表
  const optionShortVoltage = createChartOption(
    data.days_short,
    data.V,
    '时间 (秒)',
    '电压 (V)',
    '局部电压曲线',
    '#f59e0b'
  );
  chartInstanceShortVoltage?.setOption(optionShortVoltage);
}

// 创建图表配置
function createChartOption(xData, yData, xLabel, yLabel, title, color) {
  return {
    title: {
      show: false
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      borderColor: color,
      borderWidth: 1,
      textStyle: {
        color: '#fff',
        fontSize: 12
      },
      formatter: function(params) {
        const point = params[0];
        return `
          <div style="padding: 5px;">
            <div style="font-weight: 600; margin-bottom: 5px;">${title}</div>
            <div>${xLabel}: ${point.axisValue}</div>
            <div>${yLabel}: ${point.value}</div>
          </div>
        `;
      }
    },
    grid: {
      left: '12%',
      right: '5%',
      top: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: xData,
      name: xLabel,
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: {
        fontSize: 13,
        fontWeight: 500,
        color: '#374151'
      },
      axisLine: {
        lineStyle: {
          color: '#d1d5db',
          width: 1.5
        }
      },
      axisLabel: {
        color: '#6b7280',
        fontSize: 11,
        interval: 'auto',
        rotate: 0,
        formatter: function(value) {
          return parseFloat(value).toFixed(1);
        }
      },
      splitLine: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: yLabel,
      nameTextStyle: {
        fontSize: 13,
        fontWeight: 500,
        color: '#374151'
      },
      axisLine: {
        show: true,
        lineStyle: {
          color: '#d1d5db',
          width: 1.5
        }
      },
      axisLabel: {
        color: '#6b7280',
        fontSize: 11,
        formatter: function(value) {
          return value.toFixed(2);
        }
      },
      splitLine: {
        lineStyle: {
          color: '#f3f4f6',
          type: 'dashed'
        }
      }
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true
      },
      {
        type: 'slider',
        start: 0,
        end: 100,
        height: 20,
        bottom: 5,
        borderColor: '#e5e7eb',
        fillerColor: 'rgba(37, 99, 235, 0.1)',
        handleStyle: {
          color: color,
          borderColor: color
        },
        textStyle: {
          color: '#6b7280',
          fontSize: 10
        }
      }
    ],
    series: [
      {
        name: yLabel,
        type: 'line',
        data: yData,
        smooth: false,
        symbol: 'none',
        lineStyle: {
          color: color,
          width: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: `${color}40` },
            { offset: 1, color: `${color}10` }
          ])
        },
        emphasis: {
          focus: 'series',
          lineStyle: {
            width: 3
          }
        }
      }
    ]
  };
}

// 导出图表
function downloadCharts() {
  if (!currentData.value) return;
  
  const charts = [
    { instance: chartInstanceFullCurrent, name: 'full_current' },
    { instance: chartInstanceShortCurrent, name: 'short_current' },
    { instance: chartInstanceFullVoltage, name: 'full_voltage' },
    { instance: chartInstanceShortVoltage, name: 'short_voltage' }
  ];
  
  charts.forEach(chart => {
    if (chart.instance) {
      const url = chart.instance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff'
      });
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `${currentDataKey.value}_${chart.name}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  });
  
  ElMessage.success('图表导出成功');
}

// 窗口大小调整
function handleResize() {
  chartInstanceFullCurrent?.resize();
  chartInstanceShortCurrent?.resize();
  chartInstanceFullVoltage?.resize();
  chartInstanceShortVoltage?.resize();
  chartInstanceHIPreview?.resize();
}

// 渲染HI曲线预览
function renderHIPreview() {
  if (!hiCurvesData.value) return;
  
  if (!chartInstanceHIPreview && chartHIPreview.value) {
    chartInstanceHIPreview = echarts.init(chartHIPreview.value);
  }
  
  if (!chartInstanceHIPreview) return;
  
  const data = hiCurvesData.value;
  // 只显示前3条曲线作为预览
  const previewCount = Math.min(3, data.curves.length);
  const previewCurves = data.curves.slice(0, previewCount);
  
  // 降采样以提高性能
  const downsampleRate = 1000;
  const series = previewCurves.map(curve => {
    const sampledValues = [];
    for (let i = 0; i < curve.values.length; i += downsampleRate) {
      sampledValues.push(curve.values[i]);
    }
    
    return {
      name: curve.name,
      type: 'line',
      data: sampledValues,
      symbol: 'none',
      lineStyle: {
        width: 2
      },
      smooth: true
    };
  });
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: previewCurves.map(c => c.name),
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      name: '数据点索引',
      nameLocation: 'middle',
      nameGap: 30,
      axisLabel: {
        formatter: function(value) {
          return (parseInt(value) * downsampleRate).toString();
        }
      }
    },
    yAxis: {
      type: 'value',
      name: 'HI值',
      nameLocation: 'middle',
      nameGap: 50
    },
    series: series
  };
  
  chartInstanceHIPreview.setOption(option);
}

// 生命周期
onMounted(() => {
  loadData();
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  chartInstanceFullCurrent?.dispose();
  chartInstanceShortCurrent?.dispose();
  chartInstanceFullVoltage?.dispose();
  chartInstanceShortVoltage?.dispose();
  chartInstanceHICurves?.dispose();
  chartInstanceHIPreview?.dispose();
});

// 显示HI曲线对话框
async function showHICurvesDialog() {
  hiCurvesDialogVisible.value = true;
  await loadHICurvesData();
}

// 对话框打开后的回调 - 修复重新打开时的显示Bug
function onDialogOpened() {
  if (chartInstanceHICurves) {
    // 延迟调整大小以确保容器已正确渲染
    nextTick(() => {
      chartInstanceHICurves.resize();
    });
  }
}

// 加载HI曲线数据
async function loadHICurvesData() {
  if (hiCurvesData.value) {
    // 已加载，直接渲染
    await nextTick();
    renderHICurvesChart();
    return;
  }
  
  hiCurvesLoading.value = true;
  try {
    const response = await fetch('/simulation-data/HI_curves.json');
    const data = await response.json();
    hiCurvesData.value = data;
    
    await nextTick();
    renderHICurvesChart();
    
    ElMessage.success(`HI曲线加载成功: ${data.metadata.total_curves}条曲线`);
  } catch (error) {
    ElMessage.error('HI曲线加载失败: ' + error.message);
  } finally {
    hiCurvesLoading.value = false;
  }
}

// 渲染HI曲线图表
function renderHICurvesChart() {
  if (!hiCurvesData.value) return;
  
  if (!chartInstanceHICurves && chartHICurves.value) {
    chartInstanceHICurves = echarts.init(chartHICurves.value);
  }
  
  if (!chartInstanceHICurves) return;
  
  const data = hiCurvesData.value;
  
  // 确定要显示的曲线数量
  const displayCount = selectedCurveCount.value === -1 ? data.curves.length : Math.min(selectedCurveCount.value, data.curves.length);
  const displayCurves = data.curves.slice(0, displayCount);
  
  // 准备系列数据 - 为了性能考虑，对数据进行降采样
  const downsampleRate = 100; // 每100个点取1个
  const series = displayCurves.map(curve => {
    // 降采样
    const sampledValues = [];
    for (let i = 0; i < curve.values.length; i += downsampleRate) {
      sampledValues.push(curve.values[i]);
    }
    
    return {
      name: curve.name,
      type: 'line',
      data: sampledValues,
      symbol: 'none',
      lineStyle: {
        width: 2
      },
      emphasis: {
        lineStyle: {
          width: 3
        }
      }
    };
  });
  
  const option = {
    title: {
      text: '参数退化注入HI曲线',
      subtext: `显示${displayCount}/${data.metadata.total_curves}条曲线，每条${data.metadata.points_per_curve}个数据点（降采样显示）`,
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params) {
        let result = `数据点: ${params[0].dataIndex * downsampleRate}<br/>`;
        params.forEach(param => {
          result += `${param.marker} ${param.seriesName}: ${param.value?.toFixed(4) || 'N/A'}<br/>`;
        });
        return result;
      }
    },
    legend: {
      data: displayCurves.map(c => c.name),
      top: 60,
      left: 'center',
      type: 'scroll',
      width: '80%',
      tooltip: {
        show: true
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 120,  // 增加顶部空间以适应图例
      containLabel: true
    },
    toolbox: {
      feature: {
        dataZoom: {
          yAxisIndex: 'none'
        },
        restore: {},
        saveAsImage: {}
      }
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      name: '数据点索引',
      nameLocation: 'middle',
      nameGap: 30,
      axisLabel: {
        formatter: function(value) {
          return (parseInt(value) * downsampleRate).toString();
        }
      }
    },
    yAxis: {
      type: 'value',
      name: 'HI值',
      nameLocation: 'middle',
      nameGap: 50
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100
      },
      {
        start: 0,
        end: 100
      }
    ],
    series: series
  };
  
  chartInstanceHICurves.setOption(option, true); // 使用true参数强制重新渲染
}

// 显示退化路径图示对话框
function showPathDiagramDialog() {
  pathDiagramDialogVisible.value = true;
}

// 更新路径图片
function updatePathImage() {
  const pathMap = {
    '磨损退化路径': '/degradation-paths/磨损退化路径.png',
    '润滑退化路径': '/degradation-paths/润滑退化路径.png',
    '综合退化路径': '/degradation-paths/综合退化路径.png'
  };
  currentPathImage.value = pathMap[selectedPathType.value] || pathMap['磨损退化路径'];
}
</script>

<style scoped>
.degradation-simulation {
  padding: 0;
}

/* 页面头部 */
.page-header {
  margin-bottom: 20px;
  border-radius: 8px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 28px;
  color: var(--el-color-primary);
}

.page-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

/* 控制面板 */
.control-panel {
  margin-bottom: 20px;
  border-radius: 8px;
}

.control-row {
  display: flex;
  gap: 20px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.control-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 按钮组 - 水平布局 */
.control-item.button-group {
  flex-direction: row;
  align-items: center;
  gap: 12px;
}

.control-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.control-item .el-select {
  min-width: 280px;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-row {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-light);
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.info-row .el-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
}

/* 可视化面板 */
.visualization-panel {
  margin-bottom: 20px;
  border-radius: 8px;
}

/* 步骤面板特殊样式 */
.step-panel {
  border: 2px solid var(--el-border-color-lighter);
  transition: all 0.3s ease;
}

.step-panel:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 12px 0 rgba(64, 158, 255, 0.15);
}

/* 链式连接器 */
.chain-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 0;
  margin: 8px 0;
  gap: 6px;
}

.connector-icon {
  font-size: 32px;
  color: var(--el-color-primary);
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

.connector-text {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  font-weight: 500;
  background: linear-gradient(90deg, var(--el-color-primary-light-7), var(--el-color-primary-light-5));
  padding: 4px 16px;
  border-radius: 12px;
}

/* 步骤徽章 */
.step-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 70px;
  height: 28px;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.step-badge-2 {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  box-shadow: 0 2px 8px rgba(245, 87, 108, 0.3);
}

.step-badge-3 {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  box-shadow: 0 2px 8px rgba(79, 172, 254, 0.3);
}

/* 步骤说明 */
.step-description {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  margin: 0 0 20px 0;
  background: linear-gradient(90deg, var(--el-color-info-light-9), var(--el-fill-color-blank));
  border-left: 4px solid var(--el-color-primary);
  border-radius: 4px;
  color: var(--el-text-color-regular);
  font-size: 14px;
  line-height: 1.6;
}

.step-description .el-icon {
  color: var(--el-color-primary);
  font-size: 18px;
}

/* HI曲线预览 */
.hi-curves-preview {
  width: 100%;
  height: 350px;
  border-radius: 8px;
  background: var(--el-fill-color-blank);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--el-border-color-light);
}

.panel-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-actions {
  display: flex;
  gap: 12px;
}

/* 图表网格 - 水平布局 */
.charts-grid-horizontal {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-wrapper {
  background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.chart-wrapper:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--el-color-primary-light-8);
}

.chart-container {
  width: 100%;
  height: 350px;
}

/* 信息面板 */
.info-panel {
  border-radius: 8px;
}

.info-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-card {
  background: var(--el-fill-color-light);
  padding: 20px;
  border-radius: 8px;
  height: 100%;
  transition: all 0.3s ease;
}

.info-card:hover {
  background: var(--el-color-primary-light-9);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.info-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.info-icon {
  font-size: 24px;
}

.info-card-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-list li {
  color: var(--el-text-color-regular);
  font-size: 14px;
  line-height: 1.6;
  padding-left: 20px;
  position: relative;
}

.info-list li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--el-color-primary);
  font-weight: bold;
  font-size: 18px;
}

.info-list li strong {
  color: var(--el-text-color-primary);
  font-weight: 600;
}

/* HI曲线对话框控件 */
.dialog-controls {
  margin-bottom: 20px;
  padding: 12px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  display: flex;
  align-items: center;
}

/* HI曲线图表样式 */
.hi-curves-chart {
  width: 100%;
  height: 650px;
  min-height: 500px;
}

/* 退化路径图示样式 */
.path-diagram-controls {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.path-diagram-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--el-text-color-secondary);
}

.image-error p {
  margin-top: 16px;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-container {
    height: 400px;
  }
}

@media (max-width: 768px) {
  .control-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .control-item .el-select {
    min-width: 100%;
  }
  
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .chart-container {
    height: 300px;
  }
}
</style>
