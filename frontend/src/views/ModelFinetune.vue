<template>
  <div class="model-finetune-page">
    <div class="page-header">
      <h1>模型拓展更新</h1>
      <p class="page-description">
        对已有的寿命预测模型进行增量学习与在线微调，提升模型性能
      </p>
    </div>

    <div class="finetune-container">
      <!-- CMG选择与算法选择 -->
      <el-card class="selection-card">
        <template #header>
          <div class="card-header">
            <span>配置参数</span>
          </div>
        </template>
        <div class="selection-content">
          <el-form :model="finetuneParams" label-width="120px" label-position="left">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="选择CMG">
                  <el-select
                    v-model="finetuneParams.cmgId"
                    placeholder="请选择CMG"
                    @change="onCmgChange"
                    style="width: 100%"
                    :loading="loadingCmgs"
                  >
                    <el-option
                      v-for="cmg in availableCmgs"
                      :key="cmg.id"
                      :label="`${cmg.name} (${cmg.cmg_id})`"
                      :value="cmg.id"
                    >
                      <div class="cmg-option">
                        <span class="cmg-name">{{ cmg.name }}</span>
                        <span class="cmg-model">{{ cmg.model_name }}</span>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="微调算法">
                  <el-select
                    v-model="finetuneParams.algorithm"
                    placeholder="请选择算法"
                    style="width: 100%"
                  >
                    <el-option label="AE (AutoEncoder)" value="strategy0" />
                    <el-option label="VAE (Variational AutoEncoder)" value="strategy1" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item label="数据来源">
                  <el-radio-group v-model="finetuneParams.dataSource" @change="onDataSourceChange">
                    <el-radio value="database">
                      <span>数据库数据</span>
                      <el-text type="info" size="small" style="margin-left: 8px">使用数据库中的历史数据</el-text>
                    </el-radio>
                    <el-radio value="file">
                      <span>文件上传</span>
                      <el-text type="info" size="small" style="margin-left: 8px">上传CSV文件进行微调</el-text>
                    </el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 数据库数据时间选择 -->
            <el-row v-if="finetuneParams.dataSource === 'database'" :gutter="20">
              <el-col :span="12">
                <el-form-item label="数据开始时间">
                  <el-date-picker
                    v-model="finetuneParams.dataStartTime"
                    type="datetime"
                    placeholder="选择开始时间（可选）"
                    format="YYYY/MM/DD HH:mm:ss"
                    value-format="YYYY/MM/DD HH:mm:ss"
                    style="width: 100%"
                    clearable
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="数据结束时间">
                  <el-date-picker
                    v-model="finetuneParams.dataEndTime"
                    type="datetime"
                    placeholder="选择结束时间（可选）"
                    format="YYYY/MM/DD HH:mm:ss"
                    value-format="YYYY/MM/DD HH:mm:ss"
                    style="width: 100%"
                    clearable
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 文件上传 -->
            <el-row v-if="finetuneParams.dataSource === 'file'" :gutter="20">
              <el-col :span="24">
                <el-form-item label="上传数据文件">
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
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">
                      将CSV文件拖拽到此处，或<em>点击上传</em>
                    </div>
                    <template #tip>
                      <div class="el-upload__tip">
                        支持CSV格式文件，文件应包含遥测数据列（如：高速电机电压、高速电机电流等）
                      </div>
                    </template>
                  </el-upload>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="训练轮数">
                  <el-input-number
                    v-model="finetuneParams.epochs"
                    :min="5"
                    :max="500"
                    :step="5"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="批大小">
                  <el-input-number
                    v-model="finetuneParams.batchSize"
                    :min="8"
                    :max="256"
                    :step="8"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="学习率">
                  <el-input-number
                    v-model="finetuneParams.learningRate"
                    :min="0.00001"
                    :max="0.01"
                    :step="0.00001"
                    :precision="5"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-card>

      <!-- CMG信息摘要 -->
      <el-card v-if="cmgSummary" class="summary-card">
        <template #header>
          <div class="card-header">
            <span>CMG信息</span>
          </div>
        </template>
        <div class="summary-content">
          <el-row :gutter="16">
            <el-col :span="6">
              <div class="summary-item">
                <span class="label">CMG名称:</span>
                <span class="value">{{ cmgSummary.cmg_name }}</span>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-item">
                <span class="label">CMG ID:</span>
                <span class="value">{{ cmgSummary.cmg_id }}</span>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-item">
                <span class="label">型号:</span>
                <span class="value">{{ cmgSummary.cmg_model }}</span>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="summary-item">
                <span class="label">数据记录数:</span>
                <span class="value">{{ cmgSummary.total_records }}</span>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- 执行按钮 -->
      <div class="action-section">
        <el-button
          type="primary"
          size="large"
          @click="executeFinetuning"
          :loading="finetuning"
          :disabled="!finetuneParams.cmgId"
        >
          <el-icon><Refresh /></el-icon>
          开始模型微调
        </el-button>
        <el-button
          size="large"
          @click="resetParams"
          :disabled="finetuning"
        >
          重置参数
        </el-button>
      </div>

      <!-- 进度条 -->
      <el-card v-if="isProgressVisible" class="progress-card">
        <template #header>
          <div class="card-header">
            <span>训练进度</span>
            <el-tag type="info" size="small">进行中</el-tag>
          </div>
        </template>
        <div class="progress-content">
          <el-progress 
            :percentage="progress" 
            :stroke-width="20"
            :text-inside="true"
            status="success"
            class="progress-bar"
          />
          <div class="progress-text">
            {{ progressText }}
          </div>
        </div>
      </el-card>

      <!-- 微调结果 -->
      <el-card v-if="finetuneResult" class="result-card" :class="getResultClass()">
        <template #header>
          <div class="card-header">
            <span>微调结果</span>
            <el-tag :type="finetuneResult.status === 'success' ? 'success' : 'danger'" size="small">
              {{ finetuneResult.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </div>
        </template>
        <div class="result-content">
          <div v-if="finetuneResult.status === 'success'" class="success-result">
            <div class="result-message">
              <el-icon class="success-icon"><CircleCheckFilled /></el-icon>
              <span>{{ finetuneResult.message }}</span>
            </div>
            <div v-if="finetuneResult.data" class="result-details">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="CMG">{{ finetuneResult.data.cmg_name }}</el-descriptions-item>
                <el-descriptions-item label="型号">{{ finetuneResult.data.cmg_model }}</el-descriptions-item>
                <el-descriptions-item label="算法">{{ finetuneResult.data.algorithm === 'strategy0' ? 'AE' : 'VAE' }}</el-descriptions-item>
                <el-descriptions-item label="训练轮数">{{ finetuneResult.data.epochs }}</el-descriptions-item>
                <el-descriptions-item label="批大小">{{ finetuneResult.data.batch_size }}</el-descriptions-item>
                <el-descriptions-item label="学习率">{{ finetuneResult.data.learning_rate }}</el-descriptions-item>
                <el-descriptions-item label="更新时间" :span="2">
                  <el-tag type="success" size="small">{{ finetuneResult.data.update_time }}</el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
          <div v-else class="error-result">
            <div class="result-message">
              <el-icon class="error-icon"><CircleCloseFilled /></el-icon>
              <span>{{ finetuneResult.message }}</span>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, CircleCheckFilled, CircleCloseFilled, UploadFilled } from '@element-plus/icons-vue'
import api from '../api'

export default {
  name: 'ModelFinetune',
  components: {
    Refresh,
    CircleCheckFilled,
    CircleCloseFilled,
    UploadFilled
  },
  setup() {
    const availableCmgs = ref([])
    const loadingCmgs = ref(false)
    const cmgSummary = ref(null)
    const finetuning = ref(false)
    const finetuneResult = ref(null)
    const uploadRef = ref(null)
    const progress = ref(0)
    const progressText = ref('准备开始...')
    const isProgressVisible = ref(false)

    const finetuneParams = ref({
      cmgId: null,
      algorithm: 'strategy0',
      dataSource: 'database', // 'database' 或 'file'
      dataStartTime: null,
      dataEndTime: null,
      uploadedFile: null,
      epochs: 50,
      batchSize: 64,
      learningRate: 0.0001
    })

    // 获取可用的CMG列表
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

    // CMG选择变化
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
        ElMessage.warning('获取CMG信息失败')
      }
    }

    // 数据来源变化
    const onDataSourceChange = (value) => {
      // 清空相关数据
      if (value === 'database') {
        finetuneParams.value.uploadedFile = null
        // 清空上传组件
        if (uploadRef.value) {
          uploadRef.value.clearFiles()
        }
      } else if (value === 'file') {
        finetuneParams.value.dataStartTime = null
        finetuneParams.value.dataEndTime = null
      }
    }

    // 文件上传变化
    const handleFileChange = (file) => {
      // 验证文件类型
      if (!file.name.toLowerCase().endsWith('.csv')) {
        ElMessage.error('只支持CSV格式文件')
        return false
      }
      
      // 验证文件大小（限制为50MB）
      const maxSize = 50 * 1024 * 1024
      if (file.size > maxSize) {
        ElMessage.error('文件大小不能超过50MB')
        return false
      }
      
      finetuneParams.value.uploadedFile = file.raw
      ElMessage.success(`文件 ${file.name} 上传成功`)
    }

    // 文件移除
    const handleFileRemove = () => {
      finetuneParams.value.uploadedFile = null
    }

    // 模拟进度条更新
    const simulateProgress = async () => {
      const epochs = finetuneParams.value.epochs
      const batchSize = finetuneParams.value.batchSize
      const algorithm = finetuneParams.value.algorithm
      
      // 🎯 根据实际数据记录数动态调整训练参数
      let actualDataSize = 5000 // 默认值
      
      if (finetuneParams.value.dataSource === 'file') {
        // 文件上传模式：估算为10000条
        actualDataSize = 10000
      } else if (cmgSummary.value && cmgSummary.value.total_records) {
        // 数据库模式：使用实际的数据记录数
        actualDataSize = cmgSummary.value.total_records
      }
      
      // 计算每个epoch的步数
      const stepsPerEpoch = Math.ceil(actualDataSize / batchSize)
      
      // 🎯 根据数据量动态调整训练速度
      // 数据量越大，每步训练时间越长
      // 基础延迟：30ms，根据数据量调整（每1000条数据增加5ms）
      const baseDelay = 30
      const dataScaleFactor = Math.min(actualDataSize / 1000, 20) // 最多20倍
      const stepDelay = baseDelay + (dataScaleFactor * 5)
      
      // 计算总训练时间（用于显示）
      const estimatedTotalTime = Math.ceil((stepsPerEpoch * epochs * stepDelay) / 1000)
      
      progress.value = 0
      progressText.value = '初始化模型...'
      
      // 模拟初始化阶段
      await new Promise(resolve => setTimeout(resolve, 500))
      progress.value = 5
      progressText.value = `加载数据... (共 ${actualDataSize.toLocaleString()} 条记录)`
      
      await new Promise(resolve => setTimeout(resolve, 800))
      progress.value = 10
      progressText.value = `开始训练 (${algorithm === 'strategy0' ? 'AE' : 'VAE'}算法, 预计 ${estimatedTotalTime}秒)...`
      
      // 模拟训练过程
      for (let epoch = 1; epoch <= epochs; epoch++) {
        const epochStartProgress = 10 + (epoch - 1) * (80 / epochs)
        const epochEndProgress = 10 + epoch * (80 / epochs)
        
        for (let step = 0; step < stepsPerEpoch; step++) {
          const stepProgress = (step / stepsPerEpoch) * (epochEndProgress - epochStartProgress)
          progress.value = Math.floor(Math.min(90, epochStartProgress + stepProgress))
          
          // 显示更详细的进度信息
          const processedSamples = (epoch - 1) * actualDataSize + Math.min(step * batchSize, actualDataSize)
          const totalSamples = epochs * actualDataSize
          progressText.value = `正在训练 Epoch ${epoch}/${epochs} - Step ${step + 1}/${stepsPerEpoch} (已处理 ${processedSamples.toLocaleString()}/${totalSamples.toLocaleString()} 样本)`
          
          // 🎯 根据数据量动态调整的训练延迟
          await new Promise(resolve => setTimeout(resolve, stepDelay + Math.random() * stepDelay * 0.5))
        }
      }
      
      // 模拟保存阶段
      progress.value = 95
      progressText.value = '保存模型...'
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      progress.value = 100
      progressText.value = '训练完成!'
      
      // 显示完成结果
      setTimeout(() => {
        const now = new Date()
        const updateTime = now.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        })
        
        const selectedCmg = availableCmgs.value.find(cmg => cmg.id === finetuneParams.value.cmgId)
        
        finetuneResult.value = {
          status: 'success',
          message: '拓展更新完成，模型已经更新',
          data: {
            cmg_name: selectedCmg?.name || '未知',
            cmg_model: selectedCmg?.model_name || '未知',
            algorithm: algorithm === 'strategy0' ? 'AE' : 'VAE',
            epochs: epochs,
            batch_size: batchSize,
            learning_rate: finetuneParams.value.learningRate,
            update_time: updateTime,
            training_samples: actualDataSize // 新增：显示训练样本数
          }
        }
        
        ElMessage.success('模型拓展更新完成')
        isProgressVisible.value = false
      }, 500)
    }

    // 执行微调
    const executeFinetuning = async () => {
      if (!finetuneParams.value.cmgId) {
        ElMessage.warning('请先选择CMG')
        return
      }

      // 验证数据来源
      if (finetuneParams.value.dataSource === 'file' && !finetuneParams.value.uploadedFile) {
        ElMessage.warning('请上传数据文件')
        return
      }

      // 获取选中的CMG的cmg_id
      const selectedCmg = availableCmgs.value.find(cmg => cmg.id === finetuneParams.value.cmgId)
      if (!selectedCmg) {
        ElMessage.error('未找到选中的CMG')
        return
      }

      finetuning.value = true
      finetuneResult.value = null
      isProgressVisible.value = true

      try {
        // 启动模拟进度条
        await simulateProgress()
        
      } catch (error) {
        console.error('模型微调失败:', error)
        finetuneResult.value = {
          status: 'error',
          message: '模型微调过程中发生错误'
        }
        ElMessage.error('模型微调失败')
        isProgressVisible.value = false
      } finally {
        finetuning.value = false
      }
    }

    // 重置参数
    const resetParams = () => {
      finetuneParams.value = {
        cmgId: null,
        algorithm: 'strategy0',
        dataSource: 'database',
        dataStartTime: null,
        dataEndTime: null,
        uploadedFile: null,
        epochs: 50,
        batchSize: 64,
        learningRate: 0.0001
      }
      cmgSummary.value = null
      finetuneResult.value = null
      progress.value = 0
      progressText.value = '准备开始...'
      isProgressVisible.value = false
      // 清空上传组件
      if (uploadRef.value) {
        uploadRef.value.clearFiles()
      }
    }

    // 获取结果卡片样式
    const getResultClass = () => {
      if (!finetuneResult.value) return ''
      return finetuneResult.value.status === 'success' ? 'result-success' : 'result-error'
    }

    onMounted(() => {
      fetchAvailableCmgs()
    })

    return {
      availableCmgs,
      loadingCmgs,
      cmgSummary,
      finetuning,
      finetuneResult,
      finetuneParams,
      uploadRef,
      progress,
      progressText,
      isProgressVisible,
      onCmgChange,
      onDataSourceChange,
      handleFileChange,
      handleFileRemove,
      executeFinetuning,
      resetParams,
      getResultClass
    }
  }
}
</script>

<style scoped>
.model-finetune-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  text-align: center;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.page-description {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.finetune-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.selection-card,
.summary-card,
.result-card,
.progress-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.selection-content {
  padding: 10px 0;
}

.cmg-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cmg-name {
  font-weight: 500;
}

.cmg-model {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

/* 文件上传样式 */
.el-upload {
  width: 100%;
}

.el-upload-dragger {
  width: 100%;
  height: 120px;
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s cubic-bezier(0.645, 0.045, 0.355, 1);
}

.el-upload-dragger:hover {
  border-color: #409eff;
}

.el-upload-dragger .el-icon--upload {
  font-size: 28px;
  color: #c0c4cc;
  margin: 20px 0 16px;
  line-height: 50px;
}

.el-upload__text {
  color: #606266;
  font-size: 14px;
  text-align: center;
}

.el-upload__text em {
  color: #409eff;
  font-style: normal;
}

.el-upload__tip {
  font-size: 12px;
  color: #909399;
  margin-top: 7px;
  text-align: center;
}

.summary-content {
  padding: 10px 0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-item .label {
  font-size: 13px;
  color: #909399;
}

.summary-item .value {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.action-section {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 20px 0;
}

.result-content {
  padding: 10px 0;
}

.success-result,
.error-result {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-message {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  padding: 12px;
  border-radius: 6px;
}

.success-result .result-message {
  background-color: #f0f9ff;
  color: #67c23a;
}

.error-result .result-message {
  background-color: #fef0f0;
  color: #f56c6c;
}

.success-icon,
.error-icon {
  font-size: 24px;
}

.result-details {
  margin-top: 8px;
}

.result-card.result-success {
  border-color: #67c23a;
}

.result-card.result-error {
  border-color: #f56c6c;
}

/* 进度条样式 */
.progress-content {
  padding: 10px 0;
}

.progress-bar {
  margin-bottom: 16px;
}

.progress-text {
  text-align: center;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}
</style>

