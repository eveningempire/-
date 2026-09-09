<template>
  <div class="lifetime-prediction">
    <div class="page-header">
      <h1>寿命预测</h1>
      <p class="page-description">
        基于CMG遥测数据进行剩余使用寿命(RUL)预测分析
      </p>
    </div>

    <div class="prediction-container">
      <!-- CMG选择区域 -->
      <div class="cmg-selection-section">
        <h2>选择CMG</h2>
        <div class="cmg-selector">
          <el-select
            v-model="selectedCmgId"
            placeholder="请选择CMG"
            @change="onCmgChange"
            :loading="loadingCmgs"
            style="width: 100%"
          >
            <el-option
              v-for="cmg in availableCmgs"
              :key="cmg.id"
              :label="`${cmg.name} (${cmg.cmg_id})`"
              :value="cmg.id"
            >
              <div class="cmg-option">
                <span class="cmg-name">{{ cmg.name }}</span>
                <span class="cmg-id">{{ cmg.cmg_id }}</span>
                <span class="cmg-model">{{ cmg.model_name }}</span>
              </div>
            </el-option>
          </el-select>
        </div>

        <!-- CMG信息摘要 -->
        <div v-if="cmgSummary" class="cmg-summary">
          <el-card class="summary-card">
            <template #header>
              <div class="card-header">
                <span>CMG信息摘要</span>
              </div>
            </template>
            <div class="summary-content">
              <div class="summary-item">
                <span class="label">CMG名称:</span>
                <span class="value">{{ cmgSummary.cmg_name }}</span>
              </div>
              <div class="summary-item">
                <span class="label">CMG ID:</span>
                <span class="value">{{ cmgSummary.cmg_id }}</span>
              </div>
              <div class="summary-item">
                <span class="label">模型:</span>
                <span class="value">{{ cmgSummary.cmg_model }}</span>
              </div>
              <div class="summary-item">
                <span class="label">数据记录数:</span>
                <span class="value">{{ cmgSummary.total_records }}</span>
              </div>
              <div class="summary-item">
                <span class="label">最新数据时间:</span>
                <span class="value">{{ formatTime(cmgSummary.latest_data_time) }}</span>
              </div>
              <div class="summary-item">
                <span class="label">预测就绪:</span>
                <el-tag :type="cmgSummary.prediction_ready ? 'success' : 'warning'">
                  {{ cmgSummary.prediction_ready ? '是' : '否' }}
                </el-tag>
              </div>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 预测控制区域 -->
      <div class="prediction-control-section">
        <h2>执行预测</h2>
        <div class="control-panel">
          <!-- 用户输入参数 -->
          <div class="prediction-params">
            <h3>预测参数设置</h3>
            <div class="params-form">
              <div class="param-item">
                <label for="design-life">设计寿命（年）:</label>
                <el-input
                  id="design-life"
                  v-model="predictionParams.designLife"
                  type="number"
                  placeholder="请输入设计寿命，如：10"
                  :min="1"
                  :max="50"
                  style="width: 200px"
                >
                  <template #append>年</template>
                </el-input>
              </div>
              <div class="param-item">
                <label for="start-time">开始使用时间:</label>
                <el-date-picker
                  id="start-time"
                  v-model="predictionParams.startTime"
                  type="datetime"
                  placeholder="选择开始使用时间"
                  format="YYYY/MM/DD HH:mm:ss"
                  value-format="YYYY/MM/DD HH:mm:ss"
                  style="width: 250px"
                />
              </div>
              <div class="param-item">
                <label for="algorithm">预测算法:</label>
                <el-select
                  id="algorithm"
                  v-model="predictionParams.algorithm"
                  placeholder="请选择预测算法"
                  style="width: 300px"
                  :loading="loadingAlgorithms"
                >
                  <el-option
                    v-for="algorithm in availableAlgorithms"
                    :key="algorithm.key"
                    :label="algorithm.name"
                    :value="algorithm.key"
                  >
                    <div class="algorithm-option">
                      <div class="algorithm-name">{{ algorithm.name }}</div>
                      <div class="algorithm-description">{{ algorithm.description }}</div>
                    </div>
                  </el-option>
                </el-select>
              </div>
            </div>
          </div>

          <!-- 数据时间轴选择 -->
          <div v-if="selectedCmgId" class="timeline-section">
            <h3>数据时间轴选择</h3>
            <div class="timeline-container">
              <div class="timeline-header">
                <label class="timeline-label">拖动时间轴选择数据时间段：</label>
                                  <el-button 
                    size="small" 
                    type="primary" 
                    text 
                    @click="refreshTimeline"
                    :loading="timelineLoading"
                    title="刷新时间轴"
                  >
                    刷新
                  </el-button>
              </div>
              <div class="timeline-track-container" v-loading="timelineLoading">
                <div v-if="timelineData.length > 0" class="timeline-content">
                  <div 
                    class="timeline-track"
                    ref="timelineRef"
                    @mousedown="onTimelineMouseDown"
                    @mousemove="onTimelineMouseMove"
                    @mouseup="onTimelineMouseUp"
                    @mouseleave="onTimelineMouseLeave"
                  >
                    <div 
                      v-for="(segment, index) in timelineData" 
                      :key="index"
                      class="timeline-segment"
                      :style="getTimelineSegmentStyle(segment)"
                      :title="formatTimelineSegment(segment)"
                    ></div>
                    <div 
                      v-if="selectedTimeRange.start && selectedTimeRange.end"
                      class="timeline-selection"
                      :style="getTimelineSelectionStyle()"
                    ></div>
                  </div>
                  <div class="timeline-labels">
                    <span>{{ formatDateTime(timelineStart) }}</span>
                    <span>{{ formatDateTime(timelineEnd) }}</span>
                  </div>
                </div>
                <div v-else-if="!timelineLoading" class="timeline-empty">
                  <el-empty description="暂无时间轴数据，请先选择CMG" :image-size="60" />
                </div>
              </div>
              
              <!-- 推荐时间段 -->
              <div v-if="recommendedSegments.length > 0" class="recommended-segments">
                <label class="recommended-label">推荐时间段：</label>
                <div class="segment-tags">
                  <el-tag
                    v-for="(segment, index) in recommendedSegments"
                    :key="index"
                    class="segment-tag"
                    type="info"
                    @click="pickSegment(segment)"
                    style="margin-right: 8px; margin-bottom: 8px; cursor: pointer;"
                  >
                    {{ formatSegmentLabel(segment) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>

          <el-button
            type="primary"
            size="large"
            @click="executePrediction"
            :loading="predicting"
            :disabled="!selectedCmgId || !cmgSummary?.prediction_ready || !isParamsValid"
          >
            <el-icon><TrendCharts /></el-icon>
            开始寿命预测
          </el-button>
          

          

        </div>
      </div>

      <!-- 预测结果区域 -->
      <div v-if="predictionResult" class="prediction-result-section">
        <h2>预测结果</h2>
        <el-card class="result-card" :class="getResultCardClass()">
          <template #header>
            <div class="card-header">
              <span>RUL预测结果</span>
              <el-tag :type="getStatusType()" size="small">
                {{ predictionResult.status === 'success' ? '成功' : '失败' }}
              </el-tag>
            </div>
          </template>
          
          <div v-if="predictionResult.status === 'success'" class="result-content">
            <div class="rul-display">
              <div class="rul-value">
                <span class="rul-number">{{ predictionResult.rul_value }}</span>
                <span class="rul-unit">年</span>
              </div>
              <div class="rul-label">剩余使用寿命 (RUL)</div>
            </div>
            
            <!-- 健康趋势图表 -->
            <div v-if="predictionResult.hi_sequence && predictionResult.hi_sequence.length > 0" class="health-trend-chart">
              <h3>健康趋势变化</h3>
              <div class="chart-container">
                <div ref="healthTrendChart" style="width: 100%; height: 350px;"></div>
              </div>
              
              <!-- 置信区间数值显示 -->
              <div v-if="predictionResult.confidence_upper && predictionResult.confidence_lower" class="confidence-info">
                <div class="confidence-values">
                  <span class="confidence-label">健康指数置信区间：</span>
                  <span class="confidence-range">
                    [{{ Math.min(...predictionResult.confidence_lower).toFixed(4) }}, {{ Math.max(...predictionResult.confidence_upper).toFixed(4) }}]
                  </span>
                </div>
              </div>
            </div>
            
            <div class="result-details">
              <div class="detail-item">
                <span class="label">设计寿命:</span>
                <span class="value">{{ predictionParams.designLife }} 年</span>
              </div>
              <div class="detail-item">
                <span class="label">启用时间:</span>
                <span class="value">{{ predictionParams.startTime }}</span>
              </div>
              <div class="detail-item">
                <span class="label">预测时间:</span>
                <span class="value">{{ formatTime(predictionResult.prediction_time) }}</span>
              </div>
              <div v-if="predictionResult.algorithm_version" class="detail-item">
                <span class="label">算法版本:</span>
                <span class="value">{{ predictionResult.algorithm_version }}</span>
              </div>
              <div v-if="predictionParams.dataStartTime && predictionParams.dataEndTime" class="detail-item">
                <span class="label">数据时间段:</span>
                <span class="value">{{ predictionParams.dataStartTime }} 至 {{ predictionParams.dataEndTime }}</span>
              </div>
            </div>
          </div>
          
          <div v-else class="error-content">
            <el-alert
              :title="predictionResult.message"
              type="error"
              :closable="false"
              show-icon
            />
          </div>
        </el-card>
      </div>

      <!-- 加载状态 -->
      <div v-if="predicting" class="loading-overlay">
        <el-card class="loading-card">
          <div class="loading-content">
            <el-icon class="loading-icon" size="large"><Loading /></el-icon>
            <p>正在执行寿命预测...</p>
            <p class="loading-tip">请稍候，系统正在分析遥测数据</p>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { TrendCharts, Loading } from '@element-plus/icons-vue'
import api from '@/api'
import * as echarts from 'echarts'

export default {
  name: 'LifetimePrediction',
  components: {
    TrendCharts,
    Loading
  },
  setup() {
    const availableCmgs = ref([])
    const selectedCmgId = ref(null)
    const cmgSummary = ref(null)
    const predictionResult = ref(null)
    const loadingCmgs = ref(false)
    const predicting = ref(false)

    // 算法相关
    const availableAlgorithms = ref([])
    const loadingAlgorithms = ref(false)

    // 预测参数
    const predictionParams = ref({
      designLife: 10, // 设计寿命 (年)
      startTime: null, // 开始试用时间 (YYYY/MM/DD HH:mm:ss)
      dataStartTime: null, // 数据开始时间 (YYYY/MM/DD HH:mm:ss)
      dataEndTime: null, // 数据结束时间 (YYYY/MM/DD HH:mm:ss)
      algorithm: 'strategy0' // 默认算法
    })

    // 验证预测参数
    const isParamsValid = ref(false)
    
    // 健康趋势图表引用
    const healthTrendChart = ref(null)
    let healthChartInstance = null

    // 时间轴相关
    const timelineData = ref([])
    const timelineLoading = ref(false)
    const timelineRef = ref(null)
    const timelineStart = ref(null)
    const timelineEnd = ref(null)
    const selectedTimeRange = ref({ start: null, end: null })
    const isTimelineDragging = ref(false)
    const dragStartX = ref(0)
    const dragStartTime = ref(null)
    const recommendedSegments = ref([])

    // 获取可用的算法列表
    const fetchAvailableAlgorithms = async () => {
      if (loadingAlgorithms.value) return
      
      loadingAlgorithms.value = true
      try {
        const response = await api.get('/lifetime/algorithms/')
        console.log('获取算法列表响应:', response.data)
        
        if (response.data.status === 'success') {
          availableAlgorithms.value = response.data.data
          console.log('成功获取算法列表:', availableAlgorithms.value)
        } else {
          console.error('获取算法列表失败:', response.data.message)
          ElMessage.error('获取算法列表失败')
        }
      } catch (error) {
        console.error('获取算法列表错误:', error)
        ElMessage.error('获取算法列表失败')
        // 使用默认算法列表
        availableAlgorithms.value = [
          {
            key: 'strategy0',
            name: '自编码器网络3sigma算法',
            description: '基于自编码器的异常检测算法，使用3sigma规则进行健康指数计算'
          }
        ]
      } finally {
        loadingAlgorithms.value = false
      }
    }

    // 获取可用的CMG列表
    const fetchAvailableCmgs = async () => {
      loadingCmgs.value = true
      try {
        const response = await api.get('/lifetime/cmgs/')
        if (response.data.status === 'success') {
          availableCmgs.value = response.data.data
        } else {
          ElMessage.error('获取CMG列表失败')
        }
      } catch (error) {
        console.error('获取CMG列表失败:', error)
        ElMessage.error('获取CMG列表失败')
      } finally {
        loadingCmgs.value = false
      }
    }

    // CMG选择变化处理
    const onCmgChange = async (cmgId) => {
      if (!cmgId) {
        cmgSummary.value = null
        timelineData.value = []
        return
      }

      try {
        const response = await api.get(`/lifetime/summary/${cmgId}/`)
        if (response.data.status === 'success') {
          cmgSummary.value = response.data.data
          // 获取时间轴数据
          await fetchTimelineData()
        } else {
          ElMessage.error(response.data.message || '获取CMG摘要失败')
        }
      } catch (error) {
        console.error('获取CMG摘要失败:', error)
        ElMessage.error('获取CMG摘要失败')
      }
    }

    // 验证时间设置
    const validateTimeSettings = () => {
      if (!predictionParams.value.designLife || predictionParams.value.designLife <= 0) {
        ElMessage.warning('请设置有效的设计寿命（大于0年）')
        return false
      }

      if (!predictionParams.value.startTime) {
        ElMessage.warning('请设置开始使用时间')
        return false
      }

      // 如果用户选择了数据时间段，检查时间逻辑
      if (predictionParams.value.dataStartTime && predictionParams.value.dataEndTime) {
        const startUseTime = new Date(predictionParams.value.startTime)
        const dataStartTime = new Date(predictionParams.value.dataStartTime)
        const dataEndTime = new Date(predictionParams.value.dataEndTime)

        // 检查启用时间是否晚于数据开始时间
        if (startUseTime > dataStartTime) {
          ElMessage.warning('开始使用时间不能晚于数据开始时间，请调整时间设置')
          return false
        }

        // 检查数据时间范围是否合理
        if (dataStartTime >= dataEndTime) {
          ElMessage.warning('数据开始时间必须早于结束时间')
          return false
        }

        // 简单检查数据时间范围是否超过设计寿命
        const dataSpanYears = (dataEndTime - startUseTime) / (1000 * 60 * 60 * 24 * 365.25)
        if (dataSpanYears > predictionParams.value.designLife) {
          ElMessage.warning(`数据时间范围(${dataSpanYears.toFixed(1)}年)超过设计寿命(${predictionParams.value.designLife}年)，请调整设置`)
          return false
        }
      }

      return true
    }

    // 执行寿命预测
    const executePrediction = async () => {
      if (!selectedCmgId.value) {
        ElMessage.warning('请先选择CMG')
        return
      }

      // 验证时间设置
      if (!validateTimeSettings()) {
        return
      }

      predicting.value = true
      predictionResult.value = null

      try {
        // 从选中的CMG中获取cmg_id
        const selectedCmg = availableCmgs.value.find(cmg => cmg.id === selectedCmgId.value);
        if (!selectedCmg) {
          ElMessage.error('未找到选中的CMG')
          return
        }
        
        const requestData = {
          cmg_id: selectedCmg.cmg_id,
          design_life: predictionParams.value.designLife,
          start_time: predictionParams.value.startTime,
          algorithm: predictionParams.value.algorithm
        }
        
        // 如果用户选择了数据时间段，则添加到请求中
        if (predictionParams.value.dataStartTime && predictionParams.value.dataEndTime) {
          requestData.data_start_time = predictionParams.value.dataStartTime
          requestData.end_time = predictionParams.value.dataEndTime
          requestData.use_time_range = true
        }
        
        const response = await api.post('/lifetime/predict/', requestData)

        if (response.data.status === 'success') {
          predictionResult.value = response.data.data
          ElMessage.success('寿命预测完成')
          
          // 如果有健康趋势数据，绘制图表
          if (response.data.data.hi_sequence && response.data.data.hi_sequence.length > 0) {
            nextTick(() => {
              drawHealthTrendChart(
                response.data.data.hi_sequence,
                response.data.data.confidence_upper,
                response.data.data.confidence_lower
              )
            })
          }
        } else {
          predictionResult.value = response.data
          // 针对特定错误提供更友好的提示
          const errorMessage = response.data.message || '预测失败'
          if (errorMessage.includes('使用起点时间不能晚于数据起点时间')) {
            ElMessage.error('设置的启用时间晚于数据起始时间，请调整启用时间或选择其他时间段的数据')
          } else if (errorMessage.includes('数据终点时间已经超过设计寿命')) {
            ElMessage.error('数据时间范围已超过设计寿命，请调整设计寿命或数据时间范围')
          } else if (errorMessage.includes('没有可用的遥测数据')) {
            ElMessage.error('所选时间段内没有找到遥测数据，请选择其他时间段')
          } else if (errorMessage.includes('数据长度不足')) {
            ElMessage.error('数据量不足以进行寿命预测，请选择更长的时间段')
          } else {
            ElMessage.error(errorMessage)
          }
        }
      } catch (error) {
        console.error('寿命预测失败:', error)
        
        // 检查是否是网络错误或服务器错误
        let errorMessage = '寿命预测失败'
        if (error.response) {
          // 服务器返回了错误响应
          if (error.response.data && error.response.data.message) {
            const serverMessage = error.response.data.message
            if (serverMessage.includes('使用起点时间不能晚于数据起点时间')) {
              errorMessage = '设置的启用时间晚于数据起始时间，请调整启用时间或选择其他时间段的数据'
            } else if (serverMessage.includes('数据终点时间已经超过设计寿命')) {
              errorMessage = '数据时间范围已超过设计寿命，请调整设计寿命或数据时间范围'
            } else {
              errorMessage = serverMessage
            }
          } else {
            errorMessage = `服务器错误 (${error.response.status})`
          }
        } else if (error.request) {
          // 网络错误
          errorMessage = '网络连接失败，请检查网络连接后重试'
        }
        
        predictionResult.value = {
          status: 'error',
          message: errorMessage,
          rul_value: 0
        }
        ElMessage.error(errorMessage)
      } finally {
        predicting.value = false
      }
    }

    // 格式化时间
    const formatTime = (timeStr) => {
      if (!timeStr) return '未知'
      return new Date(timeStr).toLocaleString('zh-CN')
    }

    // 格式化日期时间
    const formatDateTime = (val) => {
      if (!val) return '';
      try {
        const d = new Date(val);
        return d.toLocaleString('zh-CN');
      } catch(e) { 
        return String(val); 
      }
    }

    // 获取结果卡片样式
    const getResultCardClass = () => {
      if (!predictionResult.value) return ''
      return predictionResult.value.status === 'success' ? 'success-card' : 'error-card'
    }

    // 获取状态类型
    const getStatusType = () => {
      if (!predictionResult.value) return 'info'
      return predictionResult.value.status === 'success' ? 'success' : 'danger'
    }

    // 绘制健康趋势图表（不包含置信区间）
    const drawHealthTrendChart = (hiSequence, confidenceUpper = null, confidenceLower = null) => {
      if (!healthTrendChart.value || !hiSequence || hiSequence.length === 0) return
      
      // 销毁之前的图表实例
      if (healthChartInstance) {
        healthChartInstance.dispose()
      }
      
      // 创建新的图表实例
      healthChartInstance = echarts.init(healthTrendChart.value)
      
      // 准备数据
      const xAxisData = hiSequence.map((_, index) => index + 1)
      const seriesData = hiSequence.map((value, index) => ({
        value: value,
        itemStyle: {
          color: '#409eff'
        }
      }))
      
      // 准备系列数据 - 只包含健康指数主线
      const series = []
      
      // 健康指数主线
      series.push({
        name: '健康指数',
        type: 'line',
        data: seriesData,
        smooth: true,
        lineStyle: {
          color: '#409eff',
          width: 3
        },
        symbol: 'circle',
        symbolSize: 4,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: 'rgba(64, 158, 255, 0.3)'
              },
              {
                offset: 1,
                color: 'rgba(64, 158, 255, 0.1)'
              }
            ]
          }
        }
      })
      
      // 配置图表选项
      const option = {
        title: {
          text: '健康指数变化趋势',
          left: 'center',
          textStyle: {
            fontSize: 16,
            fontWeight: 'bold',
            color: '#2c3e50'
          }
        },
        tooltip: {
          trigger: 'axis',
          formatter: function(params) {
            let result = `时间点: ${params[0].name}<br/>`
            params.forEach(param => {
              if (param.seriesName === '健康指数') {
                result += `健康指数: ${param.value.toFixed(4)}<br/>`
              }
            })
            return result
          }
        },
        legend: {
          data: ['健康指数'],
          top: 30,
          left: 'center'
        },
        grid: {
          left: '10%',
          right: '10%',
          bottom: '15%',
          top: '20%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: xAxisData,
          name: '时间点',
          nameLocation: 'middle',
          nameGap: 30,
          axisLine: {
            lineStyle: {
              color: '#ddd'
            }
          },
          axisLabel: {
            color: '#606266'
          }
        },
        yAxis: {
          type: 'value',
          name: '健康指数',
          nameLocation: 'middle',
          nameGap: 50,
          axisLine: {
            lineStyle: {
              color: '#ddd'
            }
          },
          axisLabel: {
            color: '#606266',
            formatter: function(value) {
              return value.toFixed(3)
            }
          },
          splitLine: {
            lineStyle: {
              color: '#f0f0f0',
              type: 'dashed'
            }
          }
        },
        series: series
      }
      
      // 设置图表配置并渲染
      healthChartInstance.setOption(option)
      
      // 响应式处理
      window.addEventListener('resize', () => {
        if (healthChartInstance) {
          healthChartInstance.resize()
        }
      })
    }

    // 监听预测参数变化，验证是否有效
    watch(() => predictionParams.value, (newVal) => {
      // 基本验证：设计寿命和开始使用时间必须填写
      const basicValid = newVal.designLife > 0 && newVal.startTime;
      
      // 如果用户选择了数据时间段，则验证时间段的合理性
      let timeRangeValid = true;
      if (newVal.dataStartTime && newVal.dataEndTime) {
        const startTime = new Date(newVal.dataStartTime);
        const endTime = new Date(newVal.dataEndTime);
        timeRangeValid = startTime < endTime;
      }
      
      isParamsValid.value = basicValid && timeRangeValid;
    }, { deep: true });

    // 时间轴相关函数
    const fetchTimelineData = async () => {
      if (!selectedCmgId.value) return;
      
      timelineLoading.value = true;
      timelineData.value = [];
      
      try {
        console.log('开始获取时间轴数据，CMG ID:', selectedCmgId.value);
        
        // 显示加载提示
        ElMessage.info('正在获取时间轴数据，请稍候...');
        
        // 从选中的CMG中获取cmg_id
        const selectedCmg = availableCmgs.value.find(cmg => cmg.id === selectedCmgId.value);
        if (!selectedCmg) {
          console.error('未找到选中的CMG');
          ElMessage.error('未找到选中的CMG');
          return;
        }
        
        console.log('选中的CMG:', selectedCmg);
        
        // 获取CMG数据用于构建时间轴
        const response = await api.get(`/data/data/`, { 
          params: { 
            cmg_id: selectedCmg.cmg_id, 
            limit: 5000000 
          },
          timeout: 300000 // 5分钟超时
        });
        
        console.log('API响应:', response.data);
        
        const rows = response.data.results || response.data || [];
        console.log('数据行数:', rows.length);
        
        if (rows.length < 2) {
          console.log('数据不足，无法生成时间轴');
          timelineLoading.value = false;
          return;
        }
        
        const sorted = rows
          .filter(r => r && r.timestamp)
          .slice()
          .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        
        if (sorted.length < 2) {
          timelineLoading.value = false;
          return;
        }

        // 设置时间轴范围
        timelineStart.value = new Date(sorted[0].timestamp);
        timelineEnd.value = new Date(sorted[sorted.length - 1].timestamp);

        // 计算相邻间隔的中位数
        const deltas = [];
        for (let i = 1; i < sorted.length; i++) {
          const prev = new Date(sorted[i-1].timestamp).getTime();
          const cur = new Date(sorted[i].timestamp).getTime();
          const d = cur - prev;
          if (Number.isFinite(d) && d > 0) deltas.push(d);
        }
        deltas.sort((a, b) => a - b);
        const medianDelta = deltas.length > 0 ? deltas[Math.floor(deltas.length / 2)] : 60 * 1000;
        
        // 定义"断点"阈值
        const gapThreshold = Math.max(5 * medianDelta, 5 * 60 * 1000);

        const segments = [];
        let segStartMs = new Date(sorted[0].timestamp).getTime();
        let prevMs = segStartMs;
        let segmentDataCount = 1;
        
        for (let i = 1; i < sorted.length; i++) {
          const curMs = new Date(sorted[i].timestamp).getTime();
          if (curMs - prevMs > gapThreshold) {
            if (segmentDataCount >= 50) {
              segments.push({ 
                start: new Date(segStartMs).toISOString(), 
                end: new Date(prevMs).toISOString(),
                dataCount: segmentDataCount
              });
            }
            segStartMs = curMs;
            segmentDataCount = 1;
          } else {
            segmentDataCount++;
          }
          prevMs = curMs;
        }
        
        if (segmentDataCount >= 50) {
          segments.push({ 
            start: new Date(segStartMs).toISOString(), 
            end: new Date(prevMs).toISOString(),
            dataCount: segmentDataCount
          });
        }

        timelineData.value = segments;
        console.log('生成的时间轴段数:', segments.length);
        console.log('时间轴数据:', segments);
        
        // 生成推荐时间段
        segments.sort((a, b) => new Date(b.end) - new Date(a.end));
        recommendedSegments.value = segments.slice(0, 5);
        console.log('推荐时间段:', recommendedSegments.value);
        
      } catch (error) {
        console.error('获取时间轴数据失败:', error);
        
        if (error.code === 'ECONNABORTED') {
          ElMessage.error('获取时间轴数据超时，请稍后重试或减少数据量');
        } else if (error.response?.status === 413) {
          ElMessage.error('数据量过大，请减少查询范围');
        } else {
          ElMessage.error(`获取时间轴数据失败: ${error.message || '未知错误'}`);
        }
      } finally {
        timelineLoading.value = false;
      }
    };

    const refreshTimeline = async () => {
      await fetchTimelineData();
      ElMessage.success('时间轴已刷新');
    };

    // 时间轴交互功能
    const onTimelineMouseDown = (event) => {
      if (!timelineRef.value || !timelineStart.value || !timelineEnd.value) return;
      
      const rect = timelineRef.value.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const time = getTimeFromPosition(x);
      
      isTimelineDragging.value = true;
      dragStartX.value = x;
      dragStartTime.value = time;
      selectedTimeRange.value = { start: time, end: time };
    };

    const onTimelineMouseMove = (event) => {
      if (!isTimelineDragging.value || !timelineRef.value) return;
      
      const rect = timelineRef.value.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const time = getTimeFromPosition(x);
      
      if (time && dragStartTime.value) {
        const start = new Date(Math.min(dragStartTime.value.getTime(), time.getTime()));
        const end = new Date(Math.max(dragStartTime.value.getTime(), time.getTime()));
        selectedTimeRange.value = { start, end };
      }
    };

    const onTimelineMouseUp = (event) => {
      if (!isTimelineDragging.value) return;
      
      isTimelineDragging.value = false;
      
      // 应用选择的时间范围到预测参数
      if (selectedTimeRange.value.start && selectedTimeRange.value.end) {
        predictionParams.value.dataStartTime = selectedTimeRange.value.start.toISOString().slice(0, 19).replace('T', ' ');
        predictionParams.value.dataEndTime = selectedTimeRange.value.end.toISOString().slice(0, 19).replace('T', ' ');
        ElMessage.success('已选择数据时间段');
      }
    };

    const onTimelineMouseLeave = (event) => {
      if (isTimelineDragging.value) {
        onTimelineMouseUp(event);
      }
    };

    const getTimeFromPosition = (x) => {
      if (!timelineRef.value || !timelineStart.value || !timelineEnd.value) return null;
      
      const rect = timelineRef.value.getBoundingClientRect();
      const width = rect.width;
      const ratio = Math.max(0, Math.min(1, x / width));
      
      const startTime = timelineStart.value.getTime();
      const endTime = timelineEnd.value.getTime();
      const time = startTime + ratio * (endTime - startTime);
      
      return new Date(time);
    };

    const getTimelineSegmentStyle = (segment) => {
      if (!timelineStart.value || !timelineEnd.value) return {};
      
      const startTime = timelineStart.value.getTime();
      const endTime = timelineEnd.value.getTime();
      const totalDuration = endTime - startTime;
      
      const segmentStart = new Date(segment.start).getTime();
      const segmentEnd = new Date(segment.end).getTime();
      
      const left = ((segmentStart - startTime) / totalDuration) * 100;
      const width = ((segmentEnd - segmentStart) / totalDuration) * 100;
      
      return {
        left: `${left}%`,
        width: `${width}%`
      };
    };

    const getTimelineSelectionStyle = () => {
      if (!selectedTimeRange.value.start || !selectedTimeRange.value.end || !timelineStart.value || !timelineEnd.value) return {};
      
      const startTime = timelineStart.value.getTime();
      const endTime = timelineEnd.value.getTime();
      const totalDuration = endTime - startTime;
      
      const selectionStart = selectedTimeRange.value.start.getTime();
      const selectionEnd = selectedTimeRange.value.end.getTime();
      
      const left = ((selectionStart - startTime) / totalDuration) * 100;
      const width = ((selectionEnd - selectionStart) / totalDuration) * 100;
      
      return {
        left: `${left}%`,
        width: `${width}%`
      };
    };

    const formatTimelineSegment = (segment) => {
      const start = new Date(segment.start).toLocaleString('zh-CN');
      const end = new Date(segment.end).toLocaleString('zh-CN');
      const duration = Math.round((new Date(segment.end) - new Date(segment.start)) / 1000 / 60);
      return `${start} - ${end} (${duration}分钟, ${segment.dataCount || 0}帧)`;
    };

    const formatSegmentLabel = (segment) => {
      const start = new Date(segment.start).toLocaleString('zh-CN', { 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      const end = new Date(segment.end).toLocaleString('zh-CN', { 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      const duration = Math.round((new Date(segment.end) - new Date(segment.start)) / 1000 / 60);
      return `${start} - ${end} (${duration}分钟)`;
    };

    const pickSegment = (segment) => {
      predictionParams.value.dataStartTime = new Date(segment.start).toISOString().slice(0, 19).replace('T', ' ');
      predictionParams.value.dataEndTime = new Date(segment.end).toISOString().slice(0, 19).replace('T', ' ');
      selectedTimeRange.value = { start: new Date(segment.start), end: new Date(segment.end) };
      ElMessage.success('已选择推荐时间段，正在执行预测...');
      
      // 自动执行预测（使用默认参数）
      setTimeout(() => {
        executePrediction();
      }, 500);
    };

    onMounted(() => {
      fetchAvailableCmgs()
      fetchAvailableAlgorithms()
    })
    
    // 组件卸载时清理图表实例
    const onUnmounted = () => {
      if (healthChartInstance) {
        healthChartInstance.dispose()
        healthChartInstance = null
      }
    }

    return {
      availableCmgs,
      selectedCmgId,
      cmgSummary,
      predictionResult,
      loadingCmgs,
      predicting,
      predictionParams,
      isParamsValid,
      healthTrendChart,
      // 算法相关
      availableAlgorithms,
      loadingAlgorithms,
      // 时间轴相关
      timelineData,
      timelineLoading,
      timelineRef,
      timelineStart,
      timelineEnd,
      selectedTimeRange,
      recommendedSegments,
      onCmgChange,
      executePrediction,
      formatTime,
      formatDateTime,
      getResultCardClass,
      getStatusType,
      // 时间轴函数
      refreshTimeline,
      onTimelineMouseDown,
      onTimelineMouseMove,
      onTimelineMouseUp,
      onTimelineMouseLeave,
      getTimelineSegmentStyle,
      getTimelineSelectionStyle,
      formatTimelineSegment,
      formatSegmentLabel,
      pickSegment
    }
  }
}
</script>

<style scoped>
.lifetime-prediction {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 8px;
}

.page-description {
  color: #7f8c8d;
  font-size: 16px;
  margin: 0;
}

.prediction-container {
  position: relative;
}

.cmg-selection-section,
.prediction-control-section,
.prediction-result-section {
  margin-bottom: 32px;
}

.cmg-selection-section h2,
.prediction-control-section h2,
.prediction-result-section h2 {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
  border-left: 4px solid #409eff;
  padding-left: 12px;
}

.cmg-selector {
  margin-bottom: 24px;
}

.cmg-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cmg-name {
  font-weight: 500;
}

.cmg-id {
  color: #7f8c8d;
  font-size: 14px;
}

.cmg-model {
  color: #409eff;
  font-size: 12px;
}

.cmg-summary {
  margin-top: 16px;
}

.summary-card {
  border: 1px solid #e4e7ed;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.summary-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-item .label {
  font-weight: 500;
  color: #606266;
}

.summary-item .value {
  color: #2c3e50;
}

.control-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.prediction-params {
  width: 100%;
  margin-bottom: 24px;
}

.prediction-params h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
  border-left: 4px solid #409eff;
  padding-left: 12px;
}

.params-form {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  justify-content: center;
}

.param-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-item label {
  font-weight: 500;
  color: #606266;
  font-size: 14px;
}

.algorithm-option {
  padding: 8px 0;
}

.algorithm-name {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 4px;
}

.algorithm-description {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}



.result-card {
  border: 1px solid #e4e7ed;
}

.result-card.success-card {
  border-color: #67c23a;
}

.result-card.error-card {
  border-color: #f56c6c;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.rul-display {
  text-align: center;
  padding: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.rul-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 8px;
  margin-bottom: 8px;
}

.rul-number {
  font-size: 48px;
  font-weight: 700;
  line-height: 1;
}

.rul-unit {
  font-size: 20px;
  font-weight: 500;
}

.rul-label {
  font-size: 16px;
  opacity: 0.9;
}

.health-trend-chart {
  margin-top: 24px;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.health-trend-chart h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
  text-align: center;
}

.chart-container {
  background: white;
  border-radius: 6px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  min-height: 350px;
}

.confidence-info {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
}

.confidence-values {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.confidence-label {
  font-weight: 600;
  color: #2c3e50;
}

.confidence-range {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-weight: 500;
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid rgba(64, 158, 255, 0.2);
}

.result-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 6px;
}

.detail-item .label {
  font-weight: 500;
  color: #606266;
}

.detail-item .value {
  color: #2c3e50;
  font-family: 'Courier New', monospace;
}

.error-content {
  padding: 16px;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-card {
  max-width: 400px;
  text-align: center;
}

.loading-content {
  padding: 32px;
}

.loading-icon {
  color: #409eff;
  animation: rotate 2s linear infinite;
  margin-bottom: 16px;
}

.loading-tip {
  color: #7f8c8d;
  font-size: 14px;
  margin-top: 8px;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .lifetime-prediction {
    padding: 16px;
  }
  
  .summary-content {
    grid-template-columns: 1fr;
  }
  
  .result-details {
    grid-template-columns: 1fr;
  }
  
  .rul-number {
    font-size: 36px;
  }
}

/* 时间轴样式 */
.timeline-section {
  margin-top: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  width: 100%;
}

.timeline-section h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 12px;
  border-left: 4px solid #409eff;
  padding-left: 12px;
}

.timeline-container {
  background: white;
  border-radius: 6px;
  padding: 12px;
  border: 1px solid #e4e7ed;
  width: 100%;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.timeline-label {
  font-weight: 500;
  color: #606266;
  font-size: 14px;
}

.timeline-track-container {
  margin-bottom: 12px;
}

.timeline-track {
  position: relative;
  height: 30px;
  background: #f5f7fa;
  border-radius: 6px;
  cursor: crosshair;
  border: 1px solid #dcdfe6;
  overflow: hidden;
}

.timeline-segment {
  position: absolute;
  height: 100%;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.timeline-segment:hover {
  background: #f0f2f5;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.timeline-selection {
  position: absolute;
  height: 100%;
  background: rgba(103, 194, 58, 0.3);
  border: 2px solid #67c23a;
  border-radius: 6px;
  pointer-events: none;
  z-index: 10;
}

.timeline-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.recommended-segments {
  margin-top: 12px;
}

.recommended-label {
  font-weight: 500;
  color: #606266;
  font-size: 14px;
  margin-bottom: 8px;
  display: block;
}

.segment-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.segment-tag {
  cursor: pointer;
  transition: all 0.2s ease;
}

.segment-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
