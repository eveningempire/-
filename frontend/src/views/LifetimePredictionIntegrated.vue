<template>
  <div class="lifetime-integrated-page">
    <!-- 页面头部 -->
    <div class="page-header-compact">
      <h1>寿命预测与模型拓展</h1>
      <p>基于CMG遥测数据的剩余使用寿命预测与模型在线微调</p>
    </div>

    <!-- 主内容区：左右布局 -->
    <div class="main-content-grid">
      <!-- 左侧：寿命预测 -->
      <div class="left-panel">
        <el-card class="panel-card" shadow="hover">
          <template #header>
            <div class="card-header-compact">
              <el-icon><TrendCharts /></el-icon>
              <span>寿命预测</span>
            </div>
          </template>

          <div class="compact-content">
            <!-- CMG选择 -->
            <div class="form-section-compact">
              <label class="section-label">CMG选择</label>
              <el-select
                v-model="selectedCmgId"
                placeholder="选择CMG"
                @change="onCmgChange"
                :loading="loadingCmgs"
                size="small"
                style="width: 100%"
              >
                <el-option
                  v-for="cmg in availableCmgs"
                  :key="cmg.id"
                  :label="`${cmg.name} (${cmg.cmg_id})`"
                  :value="cmg.id"
                >
                  <span style="float: left">{{ cmg.name }}</span>
                  <span style="float: right; color: #8492a6; font-size: 12px">{{ cmg.model_name }}</span>
                </el-option>
              </el-select>
            </div>

            <!-- CMG信息摘要（紧凑版） -->
            <div v-if="cmgSummary" class="info-grid-compact">
              <div class="info-item"><span class="key">ID:</span><span class="val">{{ cmgSummary.cmg_id }}</span></div>
              <div class="info-item"><span class="key">型号:</span><span class="val">{{ cmgSummary.cmg_model }}</span></div>
              <div class="info-item"><span class="key">数据:</span><span class="val">{{ cmgSummary.total_records }}</span></div>
              <div class="info-item"><span class="key">就绪:</span><el-tag :type="cmgSummary.prediction_ready ? 'success' : 'warning'" size="small">{{ cmgSummary.prediction_ready ? '是' : '否' }}</el-tag></div>
            </div>

            <!-- 预测参数 -->
            <div class="form-section-compact">
              <label class="section-label">预测参数</label>
              <el-form label-width="90px" label-position="left" size="small">
                <el-form-item label="设计寿命">
                  <el-input-number v-model="predictionParams.designLife" :min="1" :max="50" size="small" style="width: 100%" />
                  <span style="margin-left: 6px; font-size: 12px; color: #909399">年</span>
                </el-form-item>
                <el-form-item label="启用时间">
                  <el-date-picker
                    v-model="predictionParams.startTime"
                    type="datetime"
                    placeholder="选择时间"
                    format="YYYY/MM/DD HH:mm"
                    value-format="YYYY/MM/DD HH:mm:ss"
                    size="small"
                    style="width: 100%"
                  />
                </el-form-item>
                <el-form-item label="预测算法">
                  <el-select v-model="predictionParams.algorithm" placeholder="选择算法" size="small" style="width: 100%">
                    <el-option
                      v-for="alg in availableAlgorithms"
                      :key="alg.key"
                      :label="alg.name"
                      :value="alg.key"
                    />
                  </el-select>
                </el-form-item>
              </el-form>
            </div>

            <!-- 执行按钮 -->
            <el-button
              type="primary"
              size="small"
              @click="executePrediction"
              :loading="predicting"
              :disabled="!selectedCmgId || !isParamsValid"
              style="width: 100%"
            >
              <el-icon><TrendCharts /></el-icon>
              开始预测
            </el-button>

            <!-- 预测结果（紧凑版） -->
            <div v-if="predictionResult" class="result-compact">
              <div v-if="predictionResult.status === 'success'" class="success-result">
                <div class="rul-compact">
                  <span class="rul-num">{{ predictionResult.rul_value }}</span>
                  <span class="rul-unit">年</span>
                </div>
                <div class="rul-label-compact">剩余使用寿命</div>
                
                <!-- HI趋势图（紧凑版） -->
                <div v-if="predictionResult.hi_sequence && predictionResult.hi_sequence.length > 0" class="chart-compact-wrapper">
                  <div ref="healthTrendChart" style="width: 100%; height: 200px;"></div>
                </div>
              </div>
              <div v-else class="error-result-compact">
                <el-alert :title="predictionResult.message" type="error" :closable="false" show-icon />
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右侧：模型拓展更新 -->
      <div class="right-panel">
        <el-card class="panel-card" shadow="hover">
          <template #header>
            <div class="card-header-compact">
              <el-icon><Refresh /></el-icon>
              <span>模型拓展更新</span>
            </div>
          </template>

          <div class="compact-content">
            <!-- CMG选择 -->
            <div class="form-section-compact">
              <label class="section-label">CMG选择</label>
              <el-select
                v-model="finetuneParams.cmgId"
                placeholder="选择CMG"
                @change="onCmgChangeFinetune"
                :loading="loadingCmgs"
                size="small"
                style="width: 100%"
              >
                <el-option
                  v-for="cmg in availableCmgs"
                  :key="cmg.id"
                  :label="`${cmg.name} (${cmg.cmg_id})`"
                  :value="cmg.id"
                >
                  <span style="float: left">{{ cmg.name }}</span>
                  <span style="float: right; color: #8492a6; font-size: 12px">{{ cmg.model_name }}</span>
                </el-option>
              </el-select>
            </div>

            <!-- CMG信息（紧凑版） -->
            <div v-if="cmgSummaryFinetune" class="info-grid-compact">
              <div class="info-item"><span class="key">ID:</span><span class="val">{{ cmgSummaryFinetune.cmg_id }}</span></div>
              <div class="info-item"><span class="key">型号:</span><span class="val">{{ cmgSummaryFinetune.cmg_model }}</span></div>
              <div class="info-item"><span class="key">数据:</span><span class="val">{{ cmgSummaryFinetune.total_records }}</span></div>
            </div>

            <!-- 微调参数 -->
            <div class="form-section-compact">
              <label class="section-label">微调参数</label>
              <el-form label-width="70px" label-position="left" size="small">
                <el-form-item label="算法">
                  <el-select v-model="finetuneParams.algorithm" size="small" style="width: 100%">
                    <el-option label="AE" value="strategy0" />
                    <el-option label="VAE" value="strategy1" />
                  </el-select>
                </el-form-item>
                <el-form-item label="数据来源">
                  <el-radio-group v-model="finetuneParams.dataSource" @change="onDataSourceChange" size="small">
                    <el-radio value="database">数据库</el-radio>
                    <el-radio value="file">文件</el-radio>
                  </el-radio-group>
                </el-form-item>
                
                <!-- 数据库模式 -->
                <template v-if="finetuneParams.dataSource === 'database'">
                  <el-form-item label="开始时间">
                    <el-date-picker
                      v-model="finetuneParams.dataStartTime"
                      type="datetime"
                      placeholder="可选"
                      format="YYYY/MM/DD HH:mm"
                      value-format="YYYY/MM/DD HH:mm:ss"
                      size="small"
                      style="width: 100%"
                      clearable
                    />
                  </el-form-item>
                  <el-form-item label="结束时间">
                    <el-date-picker
                      v-model="finetuneParams.dataEndTime"
                      type="datetime"
                      placeholder="可选"
                      format="YYYY/MM/DD HH:mm"
                      value-format="YYYY/MM/DD HH:mm:ss"
                      size="small"
                      style="width: 100%"
                      clearable
                    />
                  </el-form-item>
                </template>

                <!-- 文件上传模式 -->
                <el-form-item v-if="finetuneParams.dataSource === 'file'" label="数据文件">
                  <el-upload
                    ref="uploadRef"
                    :auto-upload="false"
                    :on-change="handleFileChange"
                    :on-remove="handleFileRemove"
                    accept=".csv"
                    :limit="1"
                    drag
                    style="width: 100%"
                  >
                    <el-icon class="upload-icon"><UploadFilled /></el-icon>
                    <div class="upload-text">拖拽或<em>点击上传</em></div>
                    <template #tip>
                      <div class="upload-tip">CSV格式，最大50MB</div>
                    </template>
                  </el-upload>
                </el-form-item>

                <el-form-item label="训练轮数">
                  <el-input-number v-model="finetuneParams.epochs" :min="5" :max="500" :step="5" size="small" style="width: 100%" />
                </el-form-item>
                <el-form-item label="批大小">
                  <el-input-number v-model="finetuneParams.batchSize" :min="8" :max="256" :step="8" size="small" style="width: 100%" />
                </el-form-item>
                <el-form-item label="学习率">
                  <el-input-number v-model="finetuneParams.learningRate" :min="0.00001" :max="0.01" :step="0.00001" :precision="5" size="small" style="width: 100%" />
                </el-form-item>
              </el-form>
            </div>

            <!-- 执行按钮 -->
            <el-button
              type="success"
              size="small"
              @click="executeFinetune"
              :loading="finetuning"
              :disabled="!finetuneParams.cmgId"
              style="width: 100%"
            >
              <el-icon><Refresh /></el-icon>
              开始微调
            </el-button>

            <!-- 微调结果（紧凑版） -->
            <div v-if="finetuneResult" class="result-compact">
              <div v-if="finetuneResult.status === 'success'" class="success-message-compact">
                <el-icon class="success-icon"><CircleCheckFilled /></el-icon>
                <span>{{ finetuneResult.message }}</span>
              </div>
              <div v-else class="error-message-compact">
                <el-icon class="error-icon"><CircleCloseFilled /></el-icon>
                <span>{{ finetuneResult.message }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { TrendCharts, Refresh, CircleCheckFilled, CircleCloseFilled, UploadFilled } from '@element-plus/icons-vue'
import api from '../api'
import * as echarts from 'echarts'

export default {
  name: 'LifetimePredictionIntegrated',
  components: {
    TrendCharts,
    Refresh,
    CircleCheckFilled,
    CircleCloseFilled,
    UploadFilled
  },
  setup() {
    // 公共数据
    const availableCmgs = ref([])
    const loadingCmgs = ref(false)
    const availableAlgorithms = ref([])

    // 寿命预测相关
    const selectedCmgId = ref(null)
    const cmgSummary = ref(null)
    const predicting = ref(false)
    const predictionResult = ref(null)
    const predictionParams = ref({
      designLife: 10,
      startTime: null,
      algorithm: 'strategy0'
    })
    const healthTrendChart = ref(null)
    let healthChartInstance = null

    // 模型微调相关
    const cmgSummaryFinetune = ref(null)
    const finetuning = ref(false)
    const finetuneResult = ref(null)
    const uploadRef = ref(null)
    const finetuneParams = ref({
      cmgId: null,
      algorithm: 'strategy0',
      dataSource: 'database',
      dataStartTime: null,
      dataEndTime: null,
      uploadedFile: null,
      epochs: 50,
      batchSize: 64,
      learningRate: 0.0001
    })

    // 验证参数
    const isParamsValid = computed(() => {
      return predictionParams.value.designLife > 0 && predictionParams.value.startTime
    })

    // 获取CMG列表
    const fetchAvailableCmgs = async () => {
      loadingCmgs.value = true
      try {
        const response = await api.get('/lifetime/cmgs/')
        if (response.data.status === 'success') {
          availableCmgs.value = response.data.data
        }
      } catch (error) {
        console.error('获取CMG列表失败:', error)
        ElMessage.error('获取CMG列表失败')
      } finally {
        loadingCmgs.value = false
      }
    }

    // 获取算法列表
    const fetchAvailableAlgorithms = async () => {
      try {
        const response = await api.get('/lifetime/algorithms/')
        if (response.data.status === 'success') {
          availableAlgorithms.value = response.data.data
        } else {
          availableAlgorithms.value = [
            { key: 'strategy0', name: 'AE算法', description: '自编码器' }
          ]
        }
      } catch (error) {
        availableAlgorithms.value = [
          { key: 'strategy0', name: 'AE算法', description: '自编码器' }
        ]
      }
    }

    // CMG选择变化（寿命预测）
    const onCmgChange = async (cmgId) => {
      if (!cmgId) {
        cmgSummary.value = null
        return
      }
      try {
        const response = await api.get(`/lifetime/summary/${cmgId}/`)
        if (response.data.status === 'success') {
          cmgSummary.value = response.data.data
        }
      } catch (error) {
        console.error('获取CMG摘要失败:', error)
        ElMessage.error('获取CMG摘要失败')
      }
    }

    // CMG选择变化（微调）
    const onCmgChangeFinetune = async (cmgId) => {
      if (!cmgId) {
        cmgSummaryFinetune.value = null
        return
      }
      try {
        const response = await api.get(`/lifetime/summary/${cmgId}/`)
        if (response.data.status === 'success') {
          cmgSummaryFinetune.value = response.data.data
        }
      } catch (error) {
        console.error('获取CMG摘要失败:', error)
      }
    }

    // 执行寿命预测
    const executePrediction = async () => {
      if (!selectedCmgId.value) {
        ElMessage.warning('请先选择CMG')
        return
      }

      predicting.value = true
      predictionResult.value = null

      try {
        const selectedCmg = availableCmgs.value.find(cmg => cmg.id === selectedCmgId.value)
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

        const response = await api.post('/lifetime/predict/', requestData)

        if (response.data.status === 'success') {
          predictionResult.value = response.data.data
          ElMessage.success('寿命预测完成')

          if (response.data.data.hi_sequence && response.data.data.hi_sequence.length > 0) {
            nextTick(() => {
              drawHealthTrendChart(response.data.data.hi_sequence)
            })
          }
        } else {
          predictionResult.value = response.data
          ElMessage.error(response.data.message || '预测失败')
        }
      } catch (error) {
        console.error('寿命预测失败:', error)
        predictionResult.value = {
          status: 'error',
          message: error.response?.data?.message || '寿命预测失败'
        }
        ElMessage.error('寿命预测失败')
      } finally {
        predicting.value = false
      }
    }

    // 绘制健康趋势图（紧凑版）
    const drawHealthTrendChart = (hiSequence) => {
      if (!healthTrendChart.value || !hiSequence || hiSequence.length === 0) return

      if (healthChartInstance) {
        healthChartInstance.dispose()
      }

      healthChartInstance = echarts.init(healthTrendChart.value)

      const option = {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => `时间点: ${params[0].name}<br/>HI: ${params[0].value.toFixed(4)}`
        },
        grid: {
          left: '10%',
          right: '5%',
          bottom: '10%',
          top: '5%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: hiSequence.map((_, i) => i + 1),
          axisLabel: { fontSize: 10 }
        },
        yAxis: {
          type: 'value',
          axisLabel: { 
            fontSize: 10,
            formatter: (val) => val.toFixed(2)
          }
        },
        series: [{
          type: 'line',
          data: hiSequence,
          smooth: true,
          lineStyle: { color: '#409eff', width: 2 },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
                { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
              ]
            }
          }
        }]
      }

      healthChartInstance.setOption(option)
    }

    // 数据来源变化
    const onDataSourceChange = (value) => {
      if (value === 'database') {
        finetuneParams.value.uploadedFile = null
        if (uploadRef.value) {
          uploadRef.value.clearFiles()
        }
      } else {
        finetuneParams.value.dataStartTime = null
        finetuneParams.value.dataEndTime = null
      }
    }

    // 文件上传处理
    const handleFileChange = (file) => {
      if (!file.name.toLowerCase().endsWith('.csv')) {
        ElMessage.error('只支持CSV格式文件')
        return false
      }

      const maxSize = 50 * 1024 * 1024
      if (file.size > maxSize) {
        ElMessage.error('文件大小不能超过50MB')
        return false
      }

      finetuneParams.value.uploadedFile = file.raw
      ElMessage.success(`文件 ${file.name} 上传成功`)
    }

    const handleFileRemove = () => {
      finetuneParams.value.uploadedFile = null
    }

    // 执行模型微调
    const executeFinetune = async () => {
      if (!finetuneParams.value.cmgId) {
        ElMessage.warning('请先选择CMG')
        return
      }

      if (finetuneParams.value.dataSource === 'file' && !finetuneParams.value.uploadedFile) {
        ElMessage.warning('请上传数据文件')
        return
      }

      finetuning.value = true
      finetuneResult.value = null

      try {
        const selectedCmg = availableCmgs.value.find(cmg => cmg.id === finetuneParams.value.cmgId)
        if (!selectedCmg) {
          ElMessage.error('未找到选中的CMG')
          return
        }

        const requestData = {
          cmg_id: selectedCmg.cmg_id,
          algorithm: finetuneParams.value.algorithm,
          data_source: finetuneParams.value.dataSource,
          epochs: finetuneParams.value.epochs,
          batch_size: finetuneParams.value.batchSize,
          learning_rate: finetuneParams.value.learningRate
        }

        if (finetuneParams.value.dataSource === 'database') {
          requestData.data_start_time = finetuneParams.value.dataStartTime
          requestData.data_end_time = finetuneParams.value.dataEndTime
        } else if (finetuneParams.value.dataSource === 'file') {
          const formData = new FormData()
          formData.append('file', finetuneParams.value.uploadedFile)
          Object.keys(requestData).forEach(key => {
            formData.append(key, requestData[key])
          })

          const response = await api.post('/lifetime/finetune/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          })

          if (response.data.status === 'success') {
            finetuneResult.value = response.data
            ElMessage.success('模型微调完成')
          } else {
            finetuneResult.value = response.data
            ElMessage.error(response.data.message || '模型微调失败')
          }
          return
        }

        const response = await api.post('/lifetime/finetune/', requestData)

        if (response.data.status === 'success') {
          finetuneResult.value = response.data
          ElMessage.success('模型微调完成')
        } else {
          finetuneResult.value = response.data
          ElMessage.error(response.data.message || '模型微调失败')
        }
      } catch (error) {
        console.error('模型微调失败:', error)
        finetuneResult.value = {
          status: 'error',
          message: error.response?.data?.message || '模型微调失败'
        }
        ElMessage.error('模型微调失败')
      } finally {
        finetuning.value = false
      }
    }

    onMounted(() => {
      fetchAvailableCmgs()
      fetchAvailableAlgorithms()
    })

    return {
      availableCmgs,
      loadingCmgs,
      availableAlgorithms,
      // 寿命预测
      selectedCmgId,
      cmgSummary,
      predicting,
      predictionResult,
      predictionParams,
      isParamsValid,
      healthTrendChart,
      onCmgChange,
      executePrediction,
      // 模型微调
      cmgSummaryFinetune,
      finetuning,
      finetuneResult,
      finetuneParams,
      uploadRef,
      onCmgChangeFinetune,
      onDataSourceChange,
      handleFileChange,
      handleFileRemove,
      executeFinetune
    }
  }
}
</script>

<style scoped>
.lifetime-integrated-page {
  padding: 16px;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header-compact {
  text-align: center;
  margin-bottom: 16px;
}

.page-header-compact h1 {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
}

.page-header-compact p {
  font-size: 13px;
  color: #909399;
  margin: 0;
}

.main-content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.panel-card {
  border-radius: 8px;
  height: 100%;
}

.card-header-compact {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
}

.compact-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-section-compact {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-label {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
}

.info-grid-compact {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.info-item .key {
  color: #909399;
  font-weight: 500;
}

.info-item .val {
  color: #303133;
  font-weight: 500;
}

.result-compact {
  margin-top: 8px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.success-result {
  text-align: center;
}

.rul-compact {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 6px;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.rul-num {
  font-size: 32px;
  font-weight: 700;
}

.rul-unit {
  font-size: 16px;
}

.rul-label-compact {
  margin-top: 6px;
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.chart-compact-wrapper {
  margin-top: 12px;
  background: white;
  border-radius: 4px;
  padding: 8px;
}

.error-result-compact {
  padding: 8px;
}

.success-message-compact,
.error-message-compact {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  padding: 8px;
  border-radius: 4px;
}

.success-message-compact {
  background: #f0f9ff;
  color: #67c23a;
}

.error-message-compact {
  background: #fef0f0;
  color: #f56c6c;
}

.success-icon,
.error-icon {
  font-size: 18px;
}

.upload-icon {
  font-size: 24px;
  color: #c0c4cc;
  margin: 10px 0;
}

.upload-text {
  font-size: 12px;
  color: #606266;
}

.upload-text em {
  color: #409eff;
  font-style: normal;
}

.upload-tip {
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .main-content-grid {
    grid-template-columns: 1fr;
  }
}
</style>

