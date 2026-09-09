<template>
  <div class="detection-overview-page">
    <!-- 操作步骤提示 -->
    <div v-if="!hasSelectedCmgAndTime" class="operation-steps">
      <el-alert
        title="操作指南"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          <div class="steps-content">
            <span class="step-item">1. 选择操作模式（历史查询/文件检测）</span>
            <el-icon><ArrowRight /></el-icon>
            <span class="step-item">2. 选择CMG型号和个体</span>
            <el-icon><ArrowRight /></el-icon>
            <span class="step-item">3. 选择时间或上传文件</span>
            <el-icon><ArrowRight /></el-icon>
            <span class="step-item">4. 查看检测结果</span>
          </div>
        </template>
      </el-alert>
    </div>
    
    <!-- 主容器，变为左右布局 -->
    <div class="page-main-content">
      <!-- 左侧容器 -->
      <div class="left-panel">
        <div class="main-container">
          <!-- CMG选择容器 -->
          <div class="top-left-container">
            <el-card class="box-card" shadow="hover">
              <div class="actions-container">
                <!-- 模式选择 -->
                <div class="mode-selection">
                  <el-select 
                    v-model="selectedMode" 
                    placeholder="请选择操作模式" 
                    style="width: 100%;"
                    @change="onModeChange"
                    size="small"
                  >
                    <el-option label="查看历史结果" value="history">
                      <el-icon style="margin-right: 8px;"><Clock /></el-icon>
                      <span>查看历史结果</span>
                    </el-option>
                    <el-option label="上传文件检测" value="upload">
                      <el-icon style="margin-right: 8px;"><Upload /></el-icon>
                      <span>上传文件检测</span>
                    </el-option>
                  </el-select>
                </div>
                
                <!-- CMG型号选择 -->
                <div class="cmg-selection">
                  <el-select 
                    v-model="selectedCmgModel" 
                    placeholder="请选择CMG型号" 
                    style="width: 100%;"
                    @change="onModelChange"
                    size="small"
                    :disabled="!selectedMode"
                  >
                    <el-option
                      v-for="model in cmgModels"
                      :key="model.value"
                      :label="model.label"
                      :value="model.value"
                    />
                  </el-select>
                </div>
              </div>
              
              <!-- CMG个体展示 -->
              <div class="cmg-instances-container" v-if="selectedCmgModel">
                <el-divider content-position="left">CMG个体列表</el-divider>
                <div class="instances-grid">
                  <div 
                    v-for="cmg in filteredCmgs" 
                    :key="cmg.id"
                    class="cmg-instance-item"
                    :class="{ 'selected': selectedCmgId === cmg.id }"
                    :style="{ backgroundColor: getCmgHealthColor(cmg.health_score) }"
                    @click="selectCmg(cmg.id)"
                  >
                    <img 
                      :src="getCmgImagePath(cmg.cmg_model_name)" 
                      alt="CMG" 
                      class="cmg-instance-icon"
                      @error="handleImageError"
                    >
                    <span class="cmg-id">{{ cmg.cmg_id }}</span>
                    <!-- 显示健康分（仅当有健康分且不是灰色时） -->
                    <span 
                      v-if="cmg.health_score !== null && cmg.health_score !== undefined" 
                      class="health-score"
                    >
                      健康分: {{ cmg.health_score.toFixed(3) }}
                    </span>
                  </div>
                </div>
              </div>
              <div v-else class="placeholder-text">
                <div class="placeholder-content">
                  <el-icon size="60" color="#c0c4cc"><DataAnalysis /></el-icon>
                  <span v-if="!selectedMode">请先选择操作模式</span>
                  <span v-else>请选择一个CMG型号</span>
                </div>
              </div>
            </el-card>
          </div>

          <!-- 异常检测结果容器 -->
          <div class="anomaly-results-container">
            <el-card class="box-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <span>异常检测结果</span>
                </div>
              </template>
              
              <!-- 未选择状态 -->
              <div v-if="!hasSelectedCmgAndTime" class="no-selection-state">
                <el-empty description="请先选择CMG个体和时间段" :image-size="80">
                  <template #image>
                    <el-icon size="80" color="#c0c4cc"><DataAnalysis /></el-icon>
                  </template>
                </el-empty>
              </div>
              
              <!-- 加载状态 -->
              <div v-else-if="isDataLoading" class="loading-state">
                <div class="loading-content">
                  <el-icon class="is-loading" size="30" color="#409eff"><Loading /></el-icon>
                  <p>正在加载异常检测结果...</p>
                </div>
              </div>
              
              <!-- 已选择状态：显示数据 -->
              <template v-else>
              <!-- 频次统计 -->
              <div class="frequency-stats">
                <div class="stat-item">
                  <span class="stat-label">数据帧总数</span>
                  <span class="stat-value">{{ totalFrames }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">异常帧数量</span>
                  <span class="stat-value">{{ anomalyCount }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">异常帧比例</span>
                  <span class="stat-value" :class="anomalyRatioClass">{{ (anomalyRatio * 100).toFixed(2) }}%</span>
                </div>
              </div>

              <!-- 异常帧列表 -->
              <div class="anomaly-frames-container">
                <el-divider content-position="left">异常帧列表</el-divider>
                <div class="frames-list">
                  <div 
                    v-for="frame in anomalyFrames" 
                    :key="frame.id"
                    class="frame-item"
                    @click="showAnomalyDetails(frame)"
                  >
                    <span class="timestamp">{{ formatTimestamp(frame.timestamp) }}</span>
                    <!-- 异常遥测量显示 -->
                    <div v-if="frame.abnormal_parameters && frame.abnormal_parameters.length > 0" class="abnormal-params-section">
                      <span class="param-label">异常遥测量:</span>
                      <div class="abnormal-params">
                        <el-tag 
                          v-for="param in frame.abnormal_parameters" 
                          :key="param"
                          size="small"
                          type="warning"
                          class="param-tag"
                        >
                          {{ param }}
                        </el-tag>
                      </div>
                    </div>
                    <div class="score-section">
                      <span class="score-label">帧异常分:</span>
                      <el-tag :type="getScoreTagType(frame.score)" size="small" class="score">{{ frame.score.toFixed(4) }}</el-tag>
                    </div>
                  </div>
                </div>
              </div>
              </template>
            </el-card>
          </div>
        </div>
      </div>

      <!-- 右侧显示区域 -->
      <div class="right-panel">
        <!-- 上部：部件推理结果 -->
        <el-card class="box-card component-inference-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>部件推理结果</span>
            </div>
          </template>
          <div class="component-inference-content">
            <!-- 未选择状态：显示提示信息 -->
            <div v-if="!hasSelectedCmgAndTime" class="no-selection-state">
              <el-empty description="请先选择CMG个体和时间段" :image-size="100">
                <template #image>
                  <el-icon size="100" color="#c0c4cc"><DataAnalysis /></el-icon>
                </template>
              </el-empty>
            </div>
            
            <!-- 加载状态：显示加载效果 -->
            <div v-else-if="isDataLoading" class="loading-state">
              <div class="loading-content">
                <el-icon class="is-loading" size="30" color="#409eff"><Loading /></el-icon>
                <p>正在加载部件数据...</p>
              </div>
            </div>
            
            <!-- 已选择状态：显示部件推理结果 -->
            <div v-else class="enhanced-cmg-assembly-view">
              <!-- 左侧部件组 -->
              <div class="sub-components left" 
                   :class="{ 'scrollable': totalComponents > 6 }"
                   :style="{ gap: componentBoxStyle.gap }">
                <div v-for="comp in subComponents.left" :key="comp.id" 
                     class="enhanced-component-box" 
                     :style="{ 
                       width: componentBoxStyle.width, 
                       padding: componentBoxStyle.padding 
                     }"
                     @click="showInferenceDialog(comp)">
                  <div class="component-icon">
                    <el-icon><Setting /></el-icon>
                  </div>
                  <div class="component-name" :style="{ fontSize: componentBoxStyle.fontSize }">
                    {{ comp.name }}
                  </div>
                  <div class="component-health" :style="{ backgroundColor: getHealthColor(comp.healthScore) }">
                    {{ comp.healthScore.toFixed(2) }}
                  </div>
                  <div class="component-status-indicator" :class="getHealthStatusClass(comp.healthScore)"></div>
                </div>
              </div>
              
              <!-- 中央CMG主体 -->
              <div class="cmg-main-unit">
                <div class="cmg-image-container">
                  <img 
                    :src="getCmgImagePath(getSelectedCmgModelName())" 
                    alt="CMG" 
                    class="cmg-image"
                    @error="handleImageError"
                  >
                  <div class="cmg-overlay">
                    <div class="cmg-name">{{ getSelectedCmgName() }}</div>
                    <div class="cmg-status">
                      <el-tag type="success" size="small">运行中</el-tag>
                    </div>
                  </div>
                </div>
                <div class="cmg-connection-lines">
                  <div class="connection-line left"></div>
                  <div class="connection-line right"></div>
                </div>
              </div>
              
              <!-- 右侧部件组 -->
              <div class="sub-components right" 
                   :class="{ 'scrollable': totalComponents > 6 }"
                   :style="{ gap: componentBoxStyle.gap }">
                <div v-for="comp in subComponents.right" :key="comp.id" 
                     class="enhanced-component-box" 
                     :style="{ 
                       width: componentBoxStyle.width, 
                       padding: componentBoxStyle.padding 
                     }"
                     @click="showInferenceDialog(comp)">
                  <div class="component-icon">
                    <el-icon><Setting /></el-icon>
                  </div>
                  <div class="component-name" :style="{ fontSize: componentBoxStyle.fontSize }">
                    {{ comp.name }}
                  </div>
                  <div class="component-health" :style="{ backgroundColor: getHealthColor(comp.healthScore) }">
                    {{ comp.healthScore.toFixed(2) }}
                  </div>
                  <div class="component-status-indicator" :class="getHealthStatusClass(comp.healthScore)"></div>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 下部：寿命预测 -->
        <el-card class="box-card lifetime-prediction-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>寿命预测</span>
            </div>
          </template>
          <div class="lifetime-prediction-content">
            <!-- 未选择状态：显示提示信息 -->
            <div v-if="!hasSelectedCmgAndTime" class="no-selection-state">
              <el-empty description="请先选择CMG个体和时间段" :image-size="80">
                <template #image>
                  <el-icon size="80" color="#c0c4cc"><Timer /></el-icon>
                </template>
              </el-empty>
            </div>
            
            <!-- 已选择状态：显示寿命预测 -->
            <div v-else class="lifetime-prediction-layout">
              <!-- 左侧：参数设置 -->
              <div class="lifetime-params-section">
                <div class="params-header">
                  <h4>预测参数设置</h4>
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click="openLifetimeSettings" 
                    :loading="lifetimePredicting"
                    :disabled="!hasSelectedCmgAndTime"
                  >
                    <el-icon><Setting /></el-icon>
                    设置参数
                  </el-button>
                </div>
                
                <div class="current-params">
                  <div class="param-item">
                    <label>设计寿命:</label>
                    <span class="param-value">{{ lifetimeSettings.designLife }} 年</span>
                  </div>
                  <div class="param-item">
                    <label>启用时间:</label>
                    <span class="param-value">{{ lifetimeSettings.startUseTime || '未设置' }}</span>
                  </div>
                  <div class="param-item">
                    <label>预测算法:</label>
                    <span class="param-value">{{ currentAlgorithmInfo?.name || '默认算法' }}</span>
                  </div>
                </div>
                
                <div class="lifetime-result" v-if="remainingLife !== null">
                  <div class="result-header">预测结果</div>
                  <div class="result-content">
                    <div class="remaining-life-display">
                      <span class="life-value">{{ remainingLifeYears.toFixed(2) }}</span>
                      <span class="life-unit">年</span>
                    </div>
                    <div class="life-status" :class="getLifeStatusClass(remainingLifeYears)">
                      {{ getLifeStatusText(remainingLifeYears) }}
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 右侧：HI趋势图 -->
              <div class="lifetime-chart-section">
                <div class="chart-header">
                  <h4>健康指数 (HI) 趋势</h4>
                  <div class="chart-controls">
                    <el-button size="small" text @click="refreshLifetimeChart" :loading="lifetimePredicting">
                      <el-icon><Refresh /></el-icon>
                      刷新
                    </el-button>
                  </div>
                </div>
                <div class="chart-container-wrapper">
                  <div ref="healthChart" class="chart-container"></div>
                  <div v-if="lifetimePredicting" class="chart-loading-overlay">
                    <el-icon class="is-loading" size="24" color="#409eff"><Loading /></el-icon>
                    <span>正在预测寿命...</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
    
    <!-- 时间选择对话框 -->
    <el-dialog 
      v-model="showTimeSelector" 
      title="选择时间段" 
      width="800px" 
      center
    >
      <div class="time-picker-container">
        <!-- 显示当前选择的CMG个体信息 -->
        <div v-if="selectedCmgId" class="cmg-info">
          <el-alert 
            :title="`当前选择: ${getSelectedCmgName()}`" 
            type="info" 
            :closable="false"
            style="margin-bottom: 20px;"
          />
        </div>
        
        <!-- 时间轴选择器 -->
        <div v-if="timelineData && timelineData.timeline.length > 0" class="timeline-container">
          <div class="timeline-header">
            <h4>数据时间轴 (共 {{ timelineData.total_count }} 条记录)</h4>
            <p>时间范围: {{ formatTimeRange(timelineData.time_range) }}</p>
          </div>
          
          <div class="timeline-slider">
            <el-slider
              v-model="timelineRange"
              :min="0"
              :max="timelineData.timeline.length - 1"
              :step="1"
              range
              :marks="timelineMarks"
              :format-tooltip="formatTimelineTooltip"
              style="margin: 20px 0;"
            />
          </div>
          
          <div class="selected-time-info">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="开始时间">
                {{ getSelectedStartTime() }}
              </el-descriptions-item>
              <el-descriptions-item label="结束时间">
                {{ getSelectedEndTime() }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
        
        <!-- 备用时间选择器 -->
        <div v-else class="fallback-time-picker">
          <el-alert 
            title="未找到数据，请使用手动时间选择" 
            type="warning" 
            :closable="false"
            style="margin-bottom: 20px;"
          />
        <el-date-picker
          v-model="timeRange"
          type="datetimerange"
          range-separator="-"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          style="width: 100%;"
        />
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showTimeSelector = false">取消</el-button>
          <el-button type="primary" @click="confirmTimeRange">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 剩余寿命设置对话框 -->
    <el-dialog
      v-model="showLifetimeSettingsDialog"
      title="设置剩余寿命预测参数"
      width="500px"
      :before-close="handleLifetimeSettingsClose"
      :close-on-click-modal="!lifetimePredicting"
      :close-on-press-escape="!lifetimePredicting">
      <el-form :model="lifetimeSettings" label-width="120px">
        <el-form-item label="设计寿命">
          <el-input-number
            v-model="lifetimeSettings.designLife"
            :min="1"
            :max="50"
            :precision="1"
            controls-position="right"
            style="width: 200px">
          </el-input-number>
          <span style="margin-left: 10px; color: #666;">年</span>
        </el-form-item>
        <el-form-item label="启用时间">
          <el-date-picker
            v-model="lifetimeSettings.startUseTime"
            type="datetime"
            placeholder="选择启用时间"
            format="YYYY/MM/DD HH:mm:ss"
            value-format="YYYY/MM/DD HH:mm:ss"
            style="width: 200px">
          </el-date-picker>
        </el-form-item>
        <el-form-item label="预测算法">
          <el-select
            v-model="lifetimeSettings.algorithm"
            placeholder="请选择预测算法"
            style="width: 300px"
            :loading="loadingAlgorithms">
            <el-option
              v-for="algorithm in availableAlgorithms"
              :key="algorithm.key"
              :label="algorithm.name"
              :value="algorithm.key">
              <div class="algorithm-option">
                <div class="algorithm-name">{{ algorithm.name }}</div>
                <div class="algorithm-description">{{ algorithm.description }}</div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-text type="info" size="small">
            设计寿命默认为10年，启用时间默认为所选数据的最早时间戳
          </el-text>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showLifetimeSettingsDialog = false" :disabled="lifetimePredicting">取消</el-button>
          <el-button type="primary" @click="confirmLifetimeSettings" :loading="lifetimePredicting">
            {{ lifetimePredicting ? '预测中...' : '确定' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 异常详情主对话框 -->
    <el-dialog
      v-model="showAnomalyDetailDialog"
      width="85%"
      top="5vh"
      class="detail-dialog"
      :close-on-click-modal="false"
    >
      <template #header="{ close, titleId, titleClass }">
        <div class="custom-dialog-header">
          <h4 :id="titleId" :class="titleClass">
            异常详情: <span class="header-timestamp">{{ formatTimestamp(selectedAnomalyFrame?.timestamp) }}</span>
          </h4>
        </div>
      </template>
      <el-scrollbar max-height="75vh">
        <div class="detail-dialog-content">
          <!-- 左右布局：左侧三个模块堆叠，右侧遥测数据 -->
          <div class="main-layout-section">
            <!-- 左侧：IMS + 规则 + MSFG -->
            <div class="left-modules-section">
              <!-- IMS检测详情 -->
              <el-card class="detail-card" shadow="never">
                <template #header>
                  <div class="card-header">
                    <span>IMS检测详情</span>
                  </div>
                </template>
                <div class="ims-details-content">
                  <el-descriptions :column="2" border size="small">
                    <el-descriptions-item label="异常分数">
                      <el-tag :type="getScoreTagType(selectedAnomalyFrame.ims?.anomaly_score || selectedAnomalyFrame.score)">
                        {{ (selectedAnomalyFrame.ims?.anomaly_score || selectedAnomalyFrame.score).toFixed(4) }}
                      </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="CMG名称">{{ selectedAnomalyFrame.cmg_id || selectedCmgId }}</el-descriptions-item>
                    <el-descriptions-item label="IMS模型">{{ selectedAnomalyFrame.ims?.model_name || '未知' }}</el-descriptions-item>
                    <el-descriptions-item label="异常状态">
                      <el-tag :type="selectedAnomalyFrame.ims?.is_anomaly ? 'danger' : 'success'">
                        {{ selectedAnomalyFrame.ims?.is_anomaly ? '异常' : '正常' }}
                      </el-tag>
                    </el-descriptions-item>
                  </el-descriptions>
                  <el-divider content-position="left">遥测量分数</el-divider>
                  <el-table :data="formatParameterScores(selectedAnomalyFrame.ims?.parameter_scores || {})" border size="small" height="200">
                    <el-table-column prop="parameter" label="遥测量名称" />
                    <el-table-column prop="score" label="异常分数">
                      <template #default="{ row }">
                        <el-tag :type="getScoreTagType(parseFloat(row.score))" size="small">
                          {{ row.score }}
                        </el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </el-card>

              <!-- 规则检测结果 -->
              <el-card class="detail-card" shadow="never">
                <template #header>
                  <div class="card-header">
                    <span>规则检测结果</span>
                  </div>
                </template>
                <el-table :data="selectedAnomalyFrame.rules" border size="small" max-height="250">
                  <el-table-column prop="name" label="规则名称" width="150" />
                  <el-table-column prop="fault_name" label="故障类型" width="200" />
                  <el-table-column prop="fault_level" label="故障等级" width="100" align="center" />
                  <el-table-column prop="is_triggered" label="是否触发" width="100" align="center">
                    <template #default="{ row }">
                      <el-tag :type="row.is_triggered ? 'danger' : 'success'">
                        {{ row.is_triggered ? '是' : '否' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
              
              <!-- MSFG检测结果 -->
              <el-card class="detail-card" shadow="never">
                <template #header>
                  <div class="card-header">
                    <span>MSFG检测结果</span>
                  </div>
                </template>
                <div class="msfg-summary-content">
                  <!-- 整机分数 + TOP3列表 -->
                  <el-descriptions title="整机分数" :column="2" border size="small">
                    <el-descriptions-item label="整机健康分">{{ (selectedAnomalyFrame.msfg?.overall_health_score || selectedAnomalyFrame.msfg?.overall_score || 0).toFixed(4) }}</el-descriptions-item>
                    <el-descriptions-item label="风险等级">
                      <el-tag :type="getHealthScoreTagType(selectedAnomalyFrame.msfg?.overall_health_score || selectedAnomalyFrame.msfg?.overall_score || 0)">
                        {{ getHealthScoreText(selectedAnomalyFrame.msfg?.overall_health_score || selectedAnomalyFrame.msfg?.overall_score || 0) }}
                      </el-tag>
                    </el-descriptions-item>
                  </el-descriptions>
                  <el-divider content-position="left">TOP3 故障部件</el-divider>
                  <div class="msfg-top3-horizontal">
                    <div 
                      v-for="(item, index) in selectedAnomalyFrame.msfg?.top3 || []" 
                      :key="item.component || index" 
                      class="msfg-item-horizontal"
                    >
                      <div class="msfg-item-content">
                        <div class="msfg-rank">{{ index + 1 }}</div>
                        <div class="msfg-component">{{ item.component || '未知部件' }}</div>
                        <el-tag 
                          :type="getHealthScoreTagType(item.score || 0)" 
                          size="small"
                          class="msfg-score-tag"
                        >
                          {{ (item.score || 0).toFixed(2) }}
                        </el-tag>
                      </div>
                    </div>
                    <div v-if="!selectedAnomalyFrame.msfg?.top3?.length" class="msfg-no-data">
                      暂无MSFG数据
                    </div>
                  </div>
                </div>
              </el-card>
            </div>

            <!-- 右侧：关联遥测数据（高度等于左侧总和） -->
            <div class="right-telemetry-section">
              <el-card class="detail-card telemetry-full-card" shadow="never">
                <template #header>
                  <div class="card-header">
                    <span>关联遥测数据</span>
                  </div>
                </template>
                <div class="telemetry-inline-content">
                  <!-- 控制面板 -->
                  <div class="telemetry-controls-inline">
                    <div class="control-row-inline">
                      <div class="control-item-inline">
                        <label>前后帧数：</label>
                        <el-input-number 
                          v-model="telemetryFramesBefore" 
                          :min="10" 
                          :max="500" 
                          :step="10"
                          size="small"
                          style="width: 120px;"
                        />
                      </div>
                      <div class="control-item-inline">
                        <label>遥测量选择：</label>
                        <el-select 
                          v-model="selectedTelemetryParameters" 
                          multiple 
                          collapse-tags
                          collapse-tags-tooltip
                          placeholder="请选择遥测量" 
                          size="small"
                          style="width: 250px;"
                        >
                          <el-option 
                            v-for="param in availableTelemetryParameters" 
                            :key="param" 
                            :label="param" 
                            :value="param"
                          />
                        </el-select>
                      </div>
                      <el-button 
                        type="primary" 
                        size="small" 
                        @click="loadTelemetryData" 
                        :loading="telemetryLoading"
                      >
                        刷新图表
                      </el-button>
                    </div>
                  </div>
                  
                  <!-- 遥测量图表显示（可滚动） -->
                  <div class="telemetry-charts-scrollable">
                    <el-scrollbar>
                      <div class="telemetry-charts-inline" v-loading="telemetryLoading">
                        <div v-if="telemetryCharts.length === 0" class="no-telemetry-data">
                          <el-empty description="请选择遥测量并点击【刷新图表】" :image-size="80" />
                        </div>
                        <div v-else>
                          <div v-for="chart in telemetryCharts" :key="chart.parameter" class="telemetry-chart-item-inline">
                            <div class="chart-header-inline">
                              <span class="chart-title-inline">{{ chart.parameter }}</span>
                              <el-tag size="small" type="info">{{ chart.dataPoints.length }} 个数据点</el-tag>
                            </div>
                            <div :id="`inline-chart-${chart.parameter}`" class="chart-container-inline"></div>
                          </div>
                        </div>
                      </div>
                    </el-scrollbar>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </div>
      </el-scrollbar>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAnomalyDetailDialog = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- MSFG详情-弹出式对话框 -->
    <el-dialog
      v-model="showMsfgDetailDialog"
      :title="`${activeMsfgComponent?.component} - 分数详情`"
      width="60%"
      append-to-body
      destroy-on-close
    >
      <div v-if="activeMsfgComponent">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="测点分数">
            <el-table :data="activeMsfgComponent.scores.measurement" size="small" border>
              <el-table-column prop="name" label="测点" />
              <el-table-column prop="value" label="分数" />
            </el-table>
          </el-descriptions-item>
          <el-descriptions-item label="故障分数">
            <el-table :data="activeMsfgComponent.scores.fault" size="small" border>
              <el-table-column prop="name" label="故障模式" />
              <el-table-column prop="value" label="分数" />
            </el-table>
          </el-descriptions-item>
          <el-descriptions-item label="部件分数">
            <el-table :data="activeMsfgComponent.scores.component" size="small" border>
              <el-table-column prop="name" label="相关部件" />
              <el-table-column prop="value" label="分数" />
            </el-table>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 部件详细信息对话框 -->
    <el-dialog
      v-model="inferenceDialogVisible"
      :title="`'${selectedComponent?.name}' - 部件详细信息`"
      width="70%"
      top="8vh"
      class="component-detail-dialog"
      :close-on-click-modal="false"
    >
      <div v-loading="componentDetailLoading" class="component-detail-content">
        <!-- 饼状图可视化 -->
        <div v-if="componentDetailData" class="pie-chart-container">
          
          <!-- 部件基本信息 -->
          <div class="component-info-header">
            <h3>{{ componentDetailData.center_component?.name || '部件详情' }}</h3>
            <div class="component-stats">
              <el-tag :type="getHealthScoreTagType(componentDetailData.center_component?.average_score || 0)" size="large">
                平均分数: {{ (componentDetailData.center_component?.average_score || 0).toFixed(3) }}
              </el-tag>
              <span class="score-count">
                (基于 {{ componentDetailData.center_component?.score_count || 0 }} 个数据点)
              </span>
            </div>
          </div>
          
          <!-- 饼状图展示区域 -->
          <div class="pie-charts-section">
            <div class="pie-chart-wrapper">
              <div class="pie-chart-title">
                <h4>测点与故障分数分布图</h4>
              </div>
              <div ref="pieChartRef" class="pie-chart" style="width: 100%; height: 400px;"></div>
            </div>
          </div>
          
          <!-- 详细数据表格 -->
          <div class="detail-tables">
            <div class="table-section">
              <h4>测点异常分数</h4>
              <el-table 
                :data="limitedTestpoints" 
                size="small" 
                border
                max-height="200"
                style="margin-bottom: 16px;"
              >
                <el-table-column prop="name" label="测点名称" width="200" />
                <el-table-column prop="average_score" label="异常分数" width="120">
                  <template #default="{ row }">
                    <el-tag :type="getScoreTagType(row.average_score)" size="small">
                      {{ row.average_score.toFixed(3) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="score_count" label="数据点数" width="100" />
                <el-table-column prop="min_score" label="最小值" width="100">
                  <template #default="{ row }">
                    {{ row.min_score.toFixed(3) }}
                  </template>
                </el-table-column>
                <el-table-column prop="max_score" label="最大值" width="100">
                  <template #default="{ row }">
                    {{ row.max_score.toFixed(3) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
            
            <div class="table-section">
              <h4>故障异常分数</h4>
              <el-table 
                :data="limitedFaults" 
                size="small" 
                border
                max-height="200"
              >
                <el-table-column prop="name" label="故障名称" width="200" />
                <el-table-column prop="average_score" label="异常分数" width="120">
                  <template #default="{ row }">
                    <el-tag :type="getScoreTagType(row.average_score)" size="small">
                      {{ row.average_score.toFixed(3) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="score_count" label="数据点数" width="100" />
                <el-table-column prop="min_score" label="最小值" width="100">
                  <template #default="{ row }">
                    {{ row.min_score.toFixed(3) }}
                  </template>
                </el-table-column>
                <el-table-column prop="max_score" label="最大值" width="100">
                  <template #default="{ row }">
                    {{ row.max_score.toFixed(3) }}
                  </template>
                </el-table-column>
              </el-table>
          </div>
          </div>
        </div>

        <!-- 无数据提示 -->
        <el-empty v-if="!componentDetailLoading && !componentDetailData" description="暂无部件详细信息" :image-size="80">
          <template #image>
            <el-icon size="80" color="#c0c4cc"><DataAnalysis /></el-icon>
          </template>
        </el-empty>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="inferenceDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 新增：遥测数据对话框 -->
    <el-dialog
      v-model="telemetryDialogVisible"
      title="关联遥测数据"
      width="85%"
      append-to-body
      destroy-on-close
      top="3vh"
    >
      <!-- 控制面板 -->
      <div class="telemetry-controls">
        <div class="control-row">
          <div class="control-item">
            <label>前后帧数：</label>
            <el-input-number 
              v-model="telemetryFramesBefore" 
              :min="10" 
              :max="1000" 
              :step="10"
              size="small"
              style="width: 120px;"
            />
            <span style="margin: 0 8px;">帧</span>
            <el-input-number 
              v-model="telemetryFramesAfter" 
              :min="10" 
              :max="1000" 
              :step="10"
              size="small"
              style="width: 120px;"
            />
            <span style="margin-left: 8px;">帧</span>
          </div>
          <div class="control-item">
            <label>遥测量选择：</label>
            <el-select
              v-model="selectedTelemetryParameters"
              multiple
              placeholder="选择遥测量"
              size="small"
              style="width: 300px;"
              @change="onTelemetryParametersChange"
            >
              <el-option
                v-for="param in availableTelemetryParameters"
                :key="param"
                :label="param"
                :value="param"
              />
            </el-select>
          </div>
          <div class="control-item">
            <el-button type="primary" @click="fetchTelemetryData" :loading="telemetryLoading">
              获取数据
            </el-button>
          </div>
        </div>
      </div>

      <!-- 图表容器 -->
      <el-scrollbar max-height="80vh" style="margin-top: 15px;">
        <div class="telemetry-plots-container">
          <div v-if="telemetryLoading" class="loading-container">
            <el-icon class="is-loading" size="30"><Loading /></el-icon>
            <span>正在加载遥测数据...</span>
          </div>
          <div v-else-if="telemetryCharts.length === 0" class="no-data-container">
              <el-icon size="30"><DataLine /></el-icon>
            <span>暂无遥测数据，请点击"获取数据"按钮</span>
            </div>
          <div v-else>
            <div v-for="chart in telemetryCharts" :key="chart.parameter" class="telemetry-chart-item">
              <div class="chart-header">
                <span class="chart-title">{{ chart.parameter }}</span>
                <el-tag size="small" type="info">{{ chart.dataPoints.length }} 个数据点</el-tag>
              </div>
              <div :id="`telemetry-chart-${chart.parameter}`" class="chart-container"></div>
            </div>
          </div>
        </div>
      </el-scrollbar>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="telemetryDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 新增：文件上传对话框（上传模式） -->
    <el-dialog
      v-model="fileUploadDialogVisible"
      title="上传文件进行检测"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        :on-remove="handleFileRemove"
        accept=".csv,.xlsx,.xls"
        drag
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 CSV 或 Excel 格式，单次最大100MB
          </div>
        </template>
      </el-upload>

      <!-- 检测配置 -->
      <el-form :model="detectionConfig" label-width="120px" style="margin-top: 20px;">
        <el-form-item label="检测模式">
          <el-select v-model="detectionConfig.mode" placeholder="请选择检测模式" style="width: 100%;">
            <el-option label="完整检测（IMS+规则+MSFG）" value="full" />
            <el-option label="仅IMS检测" value="ims_only" />
            <el-option label="仅规则检测" value="rule_only" />
            <el-option label="仅MSFG检测" value="msfg_only" />
          </el-select>
        </el-form-item>

        <el-form-item label="数据处理模式" v-if="uploadedFile">
          <el-radio-group v-model="detectionConfig.uploadMode">
            <el-radio label="all">处理整个文件</el-radio>
            <el-radio label="partial">指定处理行数</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="处理行数" v-if="detectionConfig.uploadMode === 'partial' && uploadedFile">
          <el-input-number 
            v-model="detectionConfig.maxRows" 
            :min="1" 
            :max="1000000"
            placeholder="请输入行数"
            style="width: 200px;"
          />
          <span style="margin-left: 8px; color: #909399; font-size: 12px;">
            最大支持 1,000,000 行
          </span>
        </el-form-item>

        <el-form-item label="时间戳处理" v-if="uploadedFile">
          <el-checkbox v-model="detectionConfig.addMilliseconds">
            自动为重复时间戳添加毫秒
          </el-checkbox>
          <div style="margin-top: 4px; color: #909399; font-size: 12px;">
            勾选后，系统会自动为重复的时间戳添加毫秒级精度，确保每帧时间戳唯一
          </div>
        </el-form-item>

        <el-form-item label="保存到数据库">
          <el-switch v-model="detectionConfig.saveResults" disabled :model-value="true" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px;">
            检测结果将自动保存到数据库（必需，供其他模块使用）
          </span>
        </el-form-item>
      </el-form>

      <!-- 进度显示 -->
      <div v-if="isDetecting" class="detection-progress">
        <el-progress :percentage="detectionProgress" :status="detectionStatus" />
        <p style="margin-top: 10px; text-align: center; color: #606266;">{{ detectionMessage }}</p>
      </div>

      <template #footer>
        <el-button @click="fileUploadDialogVisible = false" :disabled="isDetecting">
          取消
        </el-button>
        <el-button 
          type="primary" 
          @click="startDetection" 
          :disabled="!uploadedFile || isDetecting"
          :loading="isDetecting"
        >
          {{ isDetecting ? '检测中...' : '开始检测' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { Calendar, Monitor, TrendCharts, DataLine, Loading, Setting, DataAnalysis, ArrowRight, InfoFilled, Clock, Upload, UploadFilled } from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import api from '@/api';

// 响应式数据
const selectedMode = ref(''); // 新增：操作模式 'history' 或 'upload'
const selectedCmgModel = ref('');
const selectedCmgId = ref(null);
const showTimeSelector = ref(false);
const timeRange = ref([]);
const fileUploadDialogVisible = ref(false); // 新增：文件上传对话框
const uploadedFile = ref(null); // 新增：上传的文件
const detectionConfig = ref({ // 新增：检测配置
  mode: 'full',
  uploadMode: 'all',
  maxRows: 1000,
  addMilliseconds: true,
  saveResults: true  // 强制保存到数据库
});
const isDetecting = ref(false); // 新增：是否正在检测
const detectionProgress = ref(0); // 新增：检测进度
const detectionStatus = ref(''); // 新增：检测状态
const detectionMessage = ref(''); // 新增：检测消息
const memoryDetectionResults = ref(null); // 新增：内存中的检测结果
const timelineData = ref(null);
const timelineRange = ref([0, 0]);
const selectedAnomalyFrame = ref(null); // 用于存储当前点击的异常帧
const showAnomalyDetailDialog = ref(false); // 控制主详情对话框的显示
const activeMsfgComponent = ref(null); // 新增：用于追踪当前选中的MSFG组件
const showMsfgDetailDialog = ref(false); // 恢复控制MSFG弹窗的ref
const inferenceDialogVisible = ref(false);
const selectedComponent = ref(null);
const componentDetailLoading = ref(false);
const componentDetailData = ref(null);
const circularLayoutRef = ref(null);
const pieChartRef = ref(null);
let pieChartInstance = null;
const telemetryDialogVisible = ref(false);

// 监听对话框关闭，清理饼状图实例
watch(inferenceDialogVisible, (newVal) => {
  if (!newVal && pieChartInstance) {
    pieChartInstance.dispose();
    pieChartInstance = null;
  }
});

// 遥测数据相关
const telemetryFramesBefore = ref(100);
const telemetryFramesAfter = ref(100);
const selectedTelemetryParameters = ref([]);
const availableTelemetryParameters = ref([]);
const telemetryLoading = ref(false);
const telemetryCharts = ref([]);
const telemetryChartInstances = ref({});
const telemetryPlots = ref([]);
const healthChart = ref(null);
let myChart = null;

// 新增：异常检测结果模拟数据
const anomalyRatio = ref(0.052); // 5.2%
const totalFrames = ref(0); // 总帧数
const anomalyCount = ref(0); // 异常帧数
const anomalyFrames = ref([
  { id: 1, timestamp: '2024-09-03 10:15:23', score: 0.8912 },
  { id: 2, timestamp: '2024-09-03 10:18:45', score: 0.7654 },
  { id: 3, timestamp: '2024-09-03 10:22:11', score: 0.9321 },
  { id: 4, timestamp: '2024-09-03 10:25:34', score: 0.6123 },
  { id: 5, timestamp: '2024-09-03 10:29:58', score: 0.8845 },
  { id: 6, timestamp: '2024-09-03 10:33:19', score: 0.9111 },
  { id: 7, timestamp: '2024-09-03 10:37:42', score: 0.7890 },
]);

// 新增：规则和MSFG的模拟详细数据
const mockDetails = {
  rules: [
    { id: 1, name: '主轴振动超限', confidence: 95.2, status: '已触发' },
    { id: 2, name: '电机温度异常', confidence: 88.5, status: '已触发' },
    { id: 3, name: '转速稳定性下降', confidence: 75.0, status: '警告' },
    { id: 4, name: '负载电流波动', confidence: 60.3, status: '正常' },
  ],
  msfg: {
    overall_score: 0.8532,
    risk_level: '高风险',
    top3: [
      { 
        id: 1, rank: 1, component: '主轴承', score: 0.91, 
        scores: {
          measurement: [ { name: '振动测点A', value: 0.95 }, { name: '温度测点B', value: 0.88 } ],
          fault: [ { name: '磨损故障', value: 0.92 }, { name: '润滑不良', value: 0.85 } ],
          component: [ { name: '内圈', value: 0.90 }, { name: '外圈', value: 0.89 } ]
        }
      },
      { 
        id: 2, rank: 2, component: '电机驱动单元', score: 0.85,
        scores: {
          measurement: [ { name: '电流测点C', value: 0.88 }, { name: '电压测点D', value: 0.82 } ],
          fault: [ { name: '过载故障', value: 0.86 }, { name: '控制信号异常', value: 0.81 } ],
          component: [ { name: 'IGBT模块', value: 0.84 }, { name: '控制板', value: 0.80 } ]
        }
      },
      { 
        id: 3, rank: 3, component: '冷却系统', score: 0.78,
        scores: {
          measurement: [ { name: '冷却液温度', value: 0.80 }, { name: '流量测点E', value: 0.75 } ],
          fault: [ { name: '堵塞故障', value: 0.79 }, { name: '泄漏', value: 0.72 } ],
          component: [ { name: '水泵', value: 0.77 }, { name: '散热风扇', value: 0.74 } ]
        }
      },
    ]
  },
  ims: {
    parameter_scores: {
      'Vibration_X': 0.95,
      'Vibration_Y': 0.92,
      'Vibration_Z': 0.88,
      'Motor_Current': 0.85,
      'Temperature_1': 0.75,
      'Temperature_2': 0.72,
      'Speed': 0.65
    }
  }
};

// CMG型号数据
const cmgModels = ref([]);

// CMG个体数据
const cmgInstances = ref([]);

// 计算属性，直接返回API返回的CMG个体（后端已筛选）
const filteredCmgs = computed(() => {
  return cmgInstances.value;
});

// 新增：计算属性，用于动态设置异常比例颜色
const anomalyRatioClass = computed(() => {
  const ratio = anomalyRatio.value * 100; // 转换为百分比
  if (ratio >= 50) return 'high-anomaly'; // 50%以上红色
  if (ratio >= 20) return 'medium-anomaly'; // 20%-50%橙色
  return 'low-anomaly'; // 20%以下绿色
});

// 新增：模拟数据
const remainingLife = ref(2.12); // 年（后端直接返回年单位）
const remainingLifeYears = computed(() => remainingLife.value); // 直接使用年
const showLifetimeSettingsDialog = ref(false);
const lifetimeSettings = ref({
  designLife: 10, // 默认10年
  startUseTime: null,
  algorithm: 'strategy0' // 默认算法
});

// 算法相关
const availableAlgorithms = ref([]);
const loadingAlgorithms = ref(false);
const currentAlgorithmInfo = ref(null); // 当前使用的算法信息

// 寿命预测加载状态
const lifetimePredicting = ref(false);

// 根据CMG型号获取对应的图片路径
function getCmgImagePath(cmgModel) {
  console.log('getCmgImagePath 调用，输入型号:', cmgModel);
  
  if (!cmgModel) {
    console.log('型号为空，使用默认图片');
    return '/images/CMG.png'; // 默认图片
  }
  
  // 提取型号中的数字部分，支持多种格式：CMG-2, 500NM, 15NMS等
  const modelMatch = cmgModel.match(/(\d+)/);
  if (!modelMatch) {
    console.log('型号中没有数字，使用默认图片');
    return '/images/CMG.png'; // 没有数字，使用默认图片
  }
  
  const modelNumber = modelMatch[1];
  console.log(`从型号 "${cmgModel}" 提取数字: ${modelNumber}`);
  
  // 根据实际可用的图片文件定义映射关系（只基于数字）
  const availableImages = {
    '2': '2NMS.jpg',
    '5': '5NMS.jpg', 
    '15': '15NMS.png',
    '500': '500NMS.png'
  };
  
  // 检查是否有对应的图片
  if (availableImages[modelNumber]) {
    const imagePath = `/images/${availableImages[modelNumber]}`;
    console.log(`找到对应图片: ${imagePath}`);
    return imagePath;
  }
  
  // 如果没有精确匹配，尝试按优先级匹配（保持原有逻辑）
  const possibleNames = [
    `${modelNumber}NMS.png`,
    `${modelNumber}NMS.jpg`, 
    `${modelNumber}NM.png`,
    `${modelNumber}NM.jpg`
  ];
  
  const fallbackPath = `/images/${possibleNames[0]}`;
  console.log(`CMG型号 ${cmgModel} (数字${modelNumber}) 没有找到精确匹配，尝试: ${fallbackPath}`);
  return fallbackPath;
}

// 处理图片加载错误，回退到默认图片
function handleImageError(event) {
  console.log('图片加载失败，使用默认CMG图片');
  event.target.src = '/images/CMG.png';
}

// 待更新的健康趋势数据
const pendingTrendData = ref(null);

// 页面状态控制
const hasSelectedCmgAndTime = ref(false); // 是否已选择CMG和时间段
const isDataLoading = ref(false); // 数据是否正在加载

const subComponents = ref({
  left: [
    { id: 'l1', name: '电机组件', healthScore: 0.95 },
    { id: 'l2', name: '轴承A', healthScore: 0.88 },
    { id: 'l3', name: '传感器模块', healthScore: 0.98 },
  ],
  right: [
    { id: 'r1', name: '控制单元', healthScore: 0.92 },
    { id: 'r2', name: '轴承B', healthScore: 0.96 },
    { id: 'r3', name: '散热系统', healthScore: 0.75 },
  ]
});

// API调用函数
async function fetchCmgModels() {
  try {
    const response = await fetch('/api/v1/data/detection-overview/?action=cmg_models');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    cmgModels.value = data.cmg_models.map(model => ({
      label: model.model_name,
      value: model.id,
      description: model.description,
      is_default: model.is_default
    }));
    ElMessage.success(`成功加载 ${data.total_count} 个CMG型号`);
  } catch (error) {
    console.error('获取CMG型号失败:', error);
    ElMessage.error('获取CMG型号失败，请检查网络连接');
  }
}

async function fetchCmgIndividuals(cmgModelId) {
  try {
    const response = await fetch(`/api/v1/data/detection-overview/?action=cmg_individuals&cmg_model_id=${cmgModelId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    
    // 获取每个CMG个体的最新MSFG健康分数
    const cmgIndividualsWithHealth = await Promise.all(
      data.cmg_individuals.map(async (individual) => {
        let healthScore = null;
        try {
          const healthResponse = await fetch(`/api/v1/data/detection-overview/?action=latest_msfg_health&cmg_id=${individual.id}`);
          if (healthResponse.ok) {
            const healthData = await healthResponse.json();
            healthScore = healthData.health_score;
            console.log(`获取CMG ${individual.cmg_id} 最新MSFG健康分数: ${healthScore}`);
          } else {
            console.warn(`获取CMG ${individual.cmg_id} 健康分数失败:`, healthResponse.status);
          }
        } catch (error) {
          console.warn(`获取CMG ${individual.cmg_id} 健康分数失败:`, error);
        }
        
        return {
          id: individual.id,
          cmg_id: individual.cmg_id,
          name: individual.name,
          enabled: individual.enabled,
          cmg_model_id: individual.cmg_model_id,
          cmg_model_name: individual.cmg_model__model_name,
          health_score: healthScore
        };
      })
    );
    
    cmgInstances.value = cmgIndividualsWithHealth;
    ElMessage.success(`成功加载 ${data.total_count} 个CMG个体`);
  } catch (error) {
    console.error('获取CMG个体失败:', error);
    ElMessage.error('获取CMG个体失败，请检查网络连接');
  }
}

async function fetchCmgTimeline(cmgId) {
  try {
    console.log('获取时间轴数据，cmgId:', cmgId, typeof cmgId);
    const response = await fetch(`/api/v1/data/detection-overview/?action=cmg_timeline&cmg_id=${cmgId}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('API错误响应:', errorData);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    timelineData.value = data;
    
    // 初始化时间轴范围
    if (data.timeline && data.timeline.length > 0) {
      timelineRange.value = [0, data.timeline.length - 1];
    }
    
    ElMessage.success(`成功加载时间轴数据，共 ${data.total_count} 条记录`);
  } catch (error) {
    console.error('获取时间轴数据失败:', error);
    ElMessage.error('获取时间轴数据失败，请检查网络连接');
    timelineData.value = null;
  }
}

async function fetchAnomalyResults(cmgId, startTime, endTime) {
  try {
    console.log('获取异常检测结果，cmgId:', cmgId, 'startTime:', startTime, 'endTime:', endTime);
    const response = await fetch(`/api/v1/data/detection-overview/?action=anomaly_results&cmg_id=${cmgId}&start_time=${startTime}&end_time=${endTime}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('API错误响应:', errorData);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    
    // 更新异常检测结果数据
    anomalyRatio.value = data.anomaly_ratio;
    totalFrames.value = data.total_frames;
    anomalyCount.value = data.anomaly_count;
    anomalyFrames.value = data.anomaly_frames;
    
    ElMessage.success(`成功加载异常检测结果，共 ${data.total_frames} 条数据，${data.anomaly_count} 条异常，异常比例 ${(data.anomaly_ratio * 100).toFixed(2)}%`);
  } catch (error) {
    console.error('获取异常检测结果失败:', error);
    ElMessage.error('获取异常检测结果失败，请检查网络连接');
    // 重置数据
    anomalyRatio.value = 0;
    totalFrames.value = 0;
    anomalyCount.value = 0;
    anomalyFrames.value = [];
  }
}

// 方法

// 新增：模式选择变化
function onModeChange() {
  // 清空之前的选择
  selectedCmgModel.value = '';
  selectedCmgId.value = null;
  cmgInstances.value = [];
  memoryDetectionResults.value = null;
  
  // 清空显示的数据
  anomalyRatio.value = 0;
  totalFrames.value = 0;
  anomalyCount.value = 0;
  anomalyFrames.value = [];
  hasSelectedCmgAndTime.value = false;
  
  const modeText = selectedMode.value === 'history' ? '历史查询' : '文件检测';
  ElMessage.info(`已切换到${modeText}模式`);
}

async function onModelChange() {
  selectedCmgId.value = null; // 型号改变时，清空已选择的个体
  cmgInstances.value = []; // 清空个体列表
  
  if (selectedCmgModel.value) {
    // 获取选中型号的CMG个体
    await fetchCmgIndividuals(selectedCmgModel.value);
    const selectedModel = cmgModels.value.find(model => model.value === selectedCmgModel.value);
    ElMessage.success(`已选择型号: ${selectedModel?.label || selectedCmgModel.value}`);
  }
}

function selectCmg(id) {
  console.log('选择CMG个体，id:', id, '当前模式:', selectedMode.value);
  selectedCmgId.value = id;
  
  // 找到对应的CMG个体，显示cmg_id而不是数据库ID
  const selectedCmg = cmgInstances.value.find(cmg => cmg.id === id);
  const displayId = selectedCmg ? selectedCmg.cmg_id : id;
  console.log('选择的CMG个体详情:', selectedCmg);
  
  // 调试：检查型号信息和图片路径
  if (selectedCmg) {
    console.log('CMG型号名称:', selectedCmg.cmg_model_name);
    const imagePath = getCmgImagePath(selectedCmg.cmg_model_name);
    console.log('计算的图片路径:', imagePath);
  }
  
  // 根据模式决定后续操作
  if (!selectedMode.value) {
    ElMessage.warning('请先选择操作模式');
    return;
  }
  
  if (selectedMode.value === 'history') {
    // 历史模式：弹出时间选择对话框
    ElMessage.info(`已选择CMG个体: ${displayId}，请选择时间范围`);
    openTimeSelectDialog();
  } else if (selectedMode.value === 'upload') {
    // 上传模式：弹出文件上传对话框
    ElMessage.info(`已选择CMG个体: ${displayId}，请上传文件`);
    openFileUploadDialog();
  }
}

// 新增：打开时间选择对话框（复用原有的时间选择器）
async function openTimeSelectDialog() {
  // 直接调用原有的openTimeSelector函数，它包含完整的时间轴功能
  await openTimeSelector();
}

// 新增：打开文件上传对话框
function openFileUploadDialog() {
  uploadedFile.value = null;
  detectionProgress.value = 0;
  detectionStatus.value = '';
  detectionMessage.value = '';
  isDetecting.value = false;
  fileUploadDialogVisible.value = true;
}

// 新增：文件选择处理
function handleFileChange(file) {
  uploadedFile.value = file.raw;
  console.log('选择的文件:', file.name, '大小:', (file.size / 1024 / 1024).toFixed(2), 'MB');
}

// 新增：文件移除处理
function handleFileRemove() {
  uploadedFile.value = null;
  console.log('文件已移除');
}

// 新增：开始检测
async function startDetection() {
  if (!uploadedFile.value) {
    ElMessage.warning('请先上传文件');
    return;
  }
  
  if (!selectedCmgId.value) {
    ElMessage.warning('请先选择CMG个体');
    return;
  }
  
  try {
    isDetecting.value = true;
    detectionProgress.value = 0;
    detectionStatus.value = 'active';
    detectionMessage.value = '正在上传文件...';
    
    // 构建FormData
    const formData = new FormData();
    formData.append('file', uploadedFile.value);
    formData.append('cmg_id', selectedCmgId.value);
    formData.append('detection_mode', detectionConfig.value.mode);
    formData.append('save_results', detectionConfig.value.saveResults);
    formData.append('return_memory_results', 'true'); // 关键：要求返回内存结果
    
    // 添加数据处理配置
    if (detectionConfig.value.uploadMode === 'partial') {
      formData.append('max_rows', detectionConfig.value.maxRows);
    }
    formData.append('add_milliseconds', detectionConfig.value.addMilliseconds);
    
    // 调用后端API
    detectionMessage.value = '正在执行检测...';
    detectionProgress.value = 10;
    
    const response = await api.post('/data/realtime-detection/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    detectionProgress.value = 90;
    const data = response.data;
    
    // 检查是否有错误
    if (data.error) {
      throw new Error(data.error);
    }
    
    if (!data.results) {
      throw new Error('未返回检测结果');
    }
    
    // 关键：直接使用返回的内存结果
    memoryDetectionResults.value = data.results;
    
    // 更新显示数据（不从数据库读取）
    updateDisplayFromMemory(data.results);
    
    // 设置时间段为文件的时间范围（供其他模块使用）
    if (data.results.time_range) {
      timeRange.value = [
        new Date(data.results.time_range.start),
        new Date(data.results.time_range.end)
      ];
      console.log('自动设置时间段:', timeRange.value);
    }
    
    detectionProgress.value = 100;
    detectionStatus.value = 'success';
    detectionMessage.value = '检测完成！';
    
    // 立即设置状态，不要等待
    hasSelectedCmgAndTime.value = true; // 标记为已有数据
    isDetecting.value = false; // 立即重置检测状态
    
    ElMessage.success(`检测完成！共处理 ${data.results.total_frames} 帧数据，检测到 ${data.results.anomaly_count} 个异常`);
    
    // 延迟关闭对话框（给用户看到成功消息）
    setTimeout(() => {
      fileUploadDialogVisible.value = false;
    }, 1500);
    
  } catch (error) {
    console.error('检测失败:', error);
    ElMessage.error('检测失败: ' + error.message);
    detectionStatus.value = 'exception';
    detectionMessage.value = '检测失败';
    isDetecting.value = false;
  }
}

// 新增：从内存结果更新显示
function updateDisplayFromMemory(results) {
  console.log('从内存更新显示数据:', results);
  
  // 更新异常检测结果
  anomalyRatio.value = results.anomaly_ratio || 0;
  totalFrames.value = results.total_frames || 0;
  anomalyCount.value = results.anomaly_count || 0;
  
  // 转换anomaly_frames格式（后端用anomaly_score，前端显示用score）
  anomalyFrames.value = (results.anomaly_frames || []).map(frame => ({
    ...frame,
    score: frame.anomaly_score || frame.score || 0  // 兼容两种字段名
  }));
  
  // 更新部件健康状态（如果有）
  if (results.component_health && Object.keys(results.component_health).length > 0) {
    console.log('更新部件健康数据:', results.component_health);
    
    // 将内存中的部件健康数据转换为subComponents格式
    const leftComponents = [];
    const rightComponents = [];
    
    Object.entries(results.component_health).forEach(([compName, compData], index) => {
      const componentItem = {
        id: `comp_${index}`,
        name: compName,
        healthScore: compData.health_score || compData.avg_score || 1.0,
        scoreCount: compData.sample_count || 0,
        minScore: compData.min_score || compData.health_score || 0,
        maxScore: compData.max_score || compData.health_score || 1.0
      };
      
      // 交替分配到左右两侧
      if (index % 2 === 0) {
        leftComponents.push(componentItem);
      } else {
        rightComponents.push(componentItem);
      }
    });
    
    // 更新subComponents
    subComponents.value = {
      left: leftComponents,
      right: rightComponents
    };
    
    console.log('部件健康状态已更新:', subComponents.value);
  }
  
  // 更新整体健康度（如果有）
  if (results.overall_health !== undefined) {
    console.log('整体健康度:', results.overall_health);
    // 如果需要显示整体健康度，可以在这里更新相关变量
  }
  
  console.log('显示数据更新完成，hasSelectedCmgAndTime:', hasSelectedCmgAndTime.value);
}

// 时间轴相关的计算属性
const timelineMarks = computed(() => {
  if (!timelineData.value || !timelineData.value.timeline) return {};
  
  const marks = {};
  const timeline = timelineData.value.timeline;
  
  // 只显示首尾时间标记
  if (timeline.length > 0) {
    const startTimestamp = new Date(timeline[0].timestamp);
    const endTimestamp = new Date(timeline[timeline.length - 1].timestamp);
    
    marks[0] = startTimestamp.toLocaleDateString();
    marks[timeline.length - 1] = endTimestamp.toLocaleDateString();
  }
  
  return marks;
});

// 辅助方法
function formatTimestamp(timestamp) {
  // 将时间戳格式化为 YYYY-MM-DD HH:MM:SS 格式
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).replace(/\//g, '-');
}

function getSelectedCmgName() {
  if (!selectedCmgId.value) return '';
  const selectedCmg = cmgInstances.value.find(cmg => cmg.id === selectedCmgId.value);
  return selectedCmg ? selectedCmg.cmg_id : '';
}

function getSelectedCmgModelName() {
  if (!selectedCmgId.value) return '';
  const selectedCmg = cmgInstances.value.find(cmg => cmg.id === selectedCmgId.value);
  return selectedCmg ? selectedCmg.cmg_model_name : '';
}

function formatTimeRange(timeRange) {
  if (!timeRange) return '无数据';
  const start = new Date(timeRange.start).toLocaleString();
  const end = new Date(timeRange.end).toLocaleString();
  return `${start} - ${end}`;
}

function formatTimelineTooltip(value) {
  if (!timelineData.value || !timelineData.value.timeline) return '';
  const timeline = timelineData.value.timeline;
  if (value >= 0 && value < timeline.length) {
    return new Date(timeline[value].timestamp).toLocaleString();
  }
  return '';
}

function getSelectedStartTime() {
  if (!timelineData.value || !timelineData.value.timeline) return '';
  const timeline = timelineData.value.timeline;
  const startIndex = timelineRange.value[0];
  if (startIndex >= 0 && startIndex < timeline.length) {
    return new Date(timeline[startIndex].timestamp).toLocaleString();
  }
  return '';
}

function getSelectedEndTime() {
  if (!timelineData.value || !timelineData.value.timeline) return '';
  const timeline = timelineData.value.timeline;
  const endIndex = timelineRange.value[1];
  if (endIndex >= 0 && endIndex < timeline.length) {
    return new Date(timeline[endIndex].timestamp).toLocaleString();
  }
  return '';
}

async function openTimeSelector() {
  if (!selectedCmgId.value) {
    ElMessage.warning('请先选择一个CMG个体');
    return;
  }
  
  console.log('打开时间选择器，selectedCmgId:', selectedCmgId.value, typeof selectedCmgId.value);
  console.log('当前CMG个体列表:', cmgInstances.value);
  
  // 找到对应的CMG个体，获取cmg_id
  const selectedCmg = cmgInstances.value.find(cmg => cmg.id === selectedCmgId.value);
  if (!selectedCmg) {
    ElMessage.error('未找到选择的CMG个体');
    return;
  }
  
  console.log('找到的CMG个体:', selectedCmg);
  console.log('准备传递的数据库ID:', selectedCmg.id);
  
  // 获取时间轴数据 - 传递CMG个体的数据库ID
  await fetchCmgTimeline(selectedCmg.id);
  showTimeSelector.value = true;
}

async function confirmTimeRange() {
  let startTime, endTime;
  
  if (timelineData.value && timelineData.value.timeline && timelineData.value.timeline.length > 0) {
    // 使用时间轴选择
    const timeline = timelineData.value.timeline;
    startTime = new Date(timeline[timelineRange.value[0]].timestamp);
    endTime = new Date(timeline[timelineRange.value[1]].timestamp);
    
    timeRange.value = [startTime, endTime];
    ElMessage.success(`时间范围已设置: ${startTime.toLocaleString()} - ${endTime.toLocaleString()}`);
  } else if (timeRange.value && timeRange.value.length === 2) {
    // 使用手动时间选择
    startTime = timeRange.value[0];
    endTime = timeRange.value[1];
    ElMessage.success(`时间范围已设置: ${startTime.toLocaleString()} - ${endTime.toLocaleString()}`);
  } else {
    ElMessage.warning('请选择一个完整的时间范围');
    return;
  }
  
  showTimeSelector.value = false;
  
  // 设置页面状态：已选择CMG和时间段
  hasSelectedCmgAndTime.value = true;
  isDataLoading.value = true;
  
  // 自动加载异常检测结果、部件分数和寿命趋势
  if (selectedCmgId.value) {
    const selectedCmg = cmgInstances.value.find(cmg => cmg.id === selectedCmgId.value);
      if (selectedCmg) {
        try {
          // 只调用异常检测结果和部件分数API，不自动刷新寿命预测
          await Promise.all([
            fetchAnomalyResults(selectedCmg.id, startTime.toISOString(), endTime.toISOString()),
            fetchComponentScores(selectedCmg.id, startTime.toISOString(), endTime.toISOString())
          ]);
          
          // 清空之前的寿命预测数据，提示用户需要设置参数
          remainingLife.value = null;
          if (myChart) {
            myChart.clear(); // 清空趋势图
          }
          
          console.log('已加载异常检测和部件分数数据，寿命预测需要用户设置参数后手动刷新');
        } catch (error) {
          console.error('数据加载失败:', error);
          ElMessage.error('数据加载失败，请重试');
        } finally {
          isDataLoading.value = false;
        }
      }
  }
}

// 新增：获取异常分数标签类型
function getScoreTagType(score) {
  if (score >= 0.75) return 'danger';  // 0.75以上显示红色
  if (score >= 0.5) return 'warning';  // 0.5-0.75显示橙色
  return 'success';                    // 0.5以下显示绿色
}

// 新增：获取健康分数标签类型（按照新的颜色规则：1-0.75绿色，0.75-0.5橙色，0.5以下红色）
function getHealthScoreTagType(score) {
  if (score < 0.5) return 'danger';   // 0.5以下 - 红色
  if (score < 0.75) return 'warning'; // 0.5-0.75 - 橙色
  return 'success';                   // 0.75-1 - 绿色
}

// 新增：获取CMG个体健康状态颜色
function getCmgHealthColor(healthScore) {
  if (healthScore === null || healthScore === undefined) {
    return '#c0c4cc'; // 灰色 - 无数据
  }
  // 按照新的颜色规则：1-0.75绿色，0.75-0.5橙色，0.5以下红色
  if (healthScore >= 0.75) {
    return '#67c23a'; // 绿色 - 0.75-1.0
  }
  if (healthScore >= 0.5) {
    return '#e6a23c'; // 橙色 - 0.5-0.75
  }
  return '#f56c6c'; // 红色 - 0.5以下
}

// 新增：获取健康分数文本
function getHealthScoreText(score) {
  // 按照新的颜色规则：1-0.75正常，0.75-0.5退化，0.5以下故障
  if (score < 0.5) return '故障';   // 0.5以下
  if (score < 0.75) return '退化';  // 0.5-0.75
  return '正常';                   // 0.75-1
}

// 辅助函数：从部件健康数据提取TOP3
function extractTop3Components(componentHealth) {
  if (!componentHealth || Object.keys(componentHealth).length === 0) {
    return [];
  }
  
  // 转换为数组并按健康分数排序（从低到高，问题最严重的在前）
  const components = Object.entries(componentHealth).map(([name, data]) => ({
    name: name,
    score: data.health_score || 1.0
  }));
  
  components.sort((a, b) => a.score - b.score);
  
  // 取前3个（最不健康的）
  return components.slice(0, 3);
}

// 辅助函数：根据健康分数计算风险等级
function calculateRiskLevel(healthScore) {
  if (healthScore >= 0.9) return '低风险';
  if (healthScore >= 0.75) return '中低风险';
  if (healthScore >= 0.5) return '中风险';
  if (healthScore >= 0.3) return '高风险';
  return '严重风险';
}

// 新增：显示异常详情
async function showAnomalyDetails(frame) {
  console.log('显示异常详情，当前模式:', selectedMode.value, '异常帧:', frame);
  
  // 先使用模拟数据初始化
  selectedAnomalyFrame.value = { ...frame, ...mockDetails };
  
  // 默认选中第一个TOP3组件
  if (selectedAnomalyFrame.value.msfg.top3.length > 0) {
    activeMsfgComponent.value = selectedAnomalyFrame.value.msfg.top3[0];
  }
  
  // 显示对话框
  showAnomalyDetailDialog.value = true;
  
  // 根据模式决定如何获取详情
  if (selectedMode.value === 'upload' && memoryDetectionResults.value) {
    // 上传模式：从内存中的frame_details获取详情
    console.log('=== 从内存获取检测详情 ===');
    
    try {
      const frameDetail = memoryDetectionResults.value.frame_details?.find(
        f => f.timestamp === frame.timestamp || f.frame_number === frame.frame_number
      );
      
      if (frameDetail) {
        console.log('找到帧详情:', frameDetail);
        
        // 更新显示数据
        if (frameDetail.ims_result) {
          selectedAnomalyFrame.value.ims_scores = frameDetail.ims_result.parameter_scores || {};
          selectedAnomalyFrame.value.ims_details = frameDetail.ims_result.detection_details || {};
        }
        
        if (frameDetail.rule_result) {
          selectedAnomalyFrame.value.rules = frameDetail.rule_result.triggered_rules || [];
        }
        
        if (frameDetail.msfg_result) {
          selectedAnomalyFrame.value.msfg = {
            overall_score: frameDetail.msfg_result.overall_health_score || frameDetail.msfg_result.overall_health || 1.0,
            component_health: frameDetail.msfg_result.component_health || {},
            top3: extractTop3Components(frameDetail.msfg_result.component_health),
            risk_level: calculateRiskLevel(frameDetail.msfg_result.overall_health_score || 1.0)
          };
          
          // 更新选中的组件
          if (selectedAnomalyFrame.value.msfg.top3.length > 0) {
            activeMsfgComponent.value = selectedAnomalyFrame.value.msfg.top3[0];
          }
        }
        
        console.log('内存数据更新完成');
        return; // 直接返回，不调用API
      } else {
        console.warn('未在内存中找到该帧详情，尝试从数据库获取');
      }
    } catch (error) {
      console.error('从内存获取详情失败:', error);
    }
  }
  
  // 历史模式或内存中没有数据：从数据库异步获取
  try {
    console.log('=== 从数据库获取检测详情 ===');
    console.log('异常帧ID:', frame.id);
    
    // 并行获取IMS、规则和MSFG检测详情
    const [imsResponse, ruleResponse, msfgResponse] = await Promise.all([
      fetch(`/api/v1/data/detection-overview/?action=ims_details&frame_id=${frame.id}`),
      fetch(`/api/v1/data/detection-overview/?action=rule_details&frame_id=${frame.id}`),
      fetch(`/api/v1/data/detection-overview/?action=msfg_details&frame_id=${frame.id}`)
    ]);
    
    console.log('API响应状态:', {
      ims: imsResponse.status,
      rule: ruleResponse.status,
      msfg: msfgResponse.status
    });
    
    let imsData = null;
    let ruleData = null;
    let msfgData = null;
    
    // 处理IMS检测详情
    if (imsResponse.ok) {
      imsData = await imsResponse.json();
      console.log('✅ IMS检测详情数据:', imsData);
    } else {
      const errorText = await imsResponse.text();
      console.error('❌ IMS检测详情API错误:', imsResponse.status, errorText);
    }
    
    // 处理规则检测详情
    if (ruleResponse.ok) {
      ruleData = await ruleResponse.json();
      console.log('✅ 规则检测详情数据:', ruleData);
    } else {
      const errorText = await ruleResponse.text();
      console.error('❌ 规则检测详情API错误:', ruleResponse.status, errorText);
    }
    
    // 处理MSFG检测详情
    if (msfgResponse.ok) {
      msfgData = await msfgResponse.json();
      console.log('✅ MSFG检测详情数据:', msfgData);
      console.log('MSFG数据中的msfg字段:', msfgData.msfg);
      if (msfgData.msfg) {
        console.log('MSFG top3组件:', msfgData.msfg.top3);
        console.log('MSFG整体健康分数:', msfgData.msfg.overall_health_score);
        console.log('MSFG top3组件数量:', msfgData.msfg.top3?.length || 0);
      } else {
        console.log('⚠️ MSFG数据中的msfg字段为空');
      }
    } else {
      const errorText = await msfgResponse.text();
      console.error('❌ MSFG检测详情API错误:', msfgResponse.status, errorText);
      console.error('MSFG API URL:', `/api/v1/data/detection-overview/?action=msfg_details&frame_id=${frame.id}`);
    }
    
    // 更新数据
    console.log('=== 开始更新数据 ===');
    const updatedData = { ...selectedAnomalyFrame.value };
    console.log('更新前的数据:', updatedData);
    
    if (imsData) {
      updatedData.ims = imsData.ims;
      updatedData.cmg_id = imsData.cmg_id;
      updatedData.timestamp = imsData.timestamp;
      console.log('✅ 已更新IMS数据');
    }
    
    if (ruleData) {
      updatedData.rules = ruleData.rules;
      console.log('✅ 已更新规则数据，规则数量:', ruleData.rules?.length || 0);
    }
    
    if (msfgData && msfgData.msfg) {
      updatedData.msfg = msfgData.msfg;
      console.log('✅ 已更新MSFG数据:', updatedData.msfg);
    } else {
      console.log('⚠️ MSFG数据为空或无效');
    }
    
    console.log('更新后的完整数据:', updatedData);
    selectedAnomalyFrame.value = updatedData;
    
  // 自动加载可用的遥测参数
  await fetchAvailableTelemetryParameters();
  
  // 自动选择前三个遥测量并加载数据
  if (availableTelemetryParameters.value.length > 0) {
    selectedTelemetryParameters.value = availableTelemetryParameters.value.slice(0, 3);
    // 自动加载遥测数据
    await loadTelemetryData();
  }
    
    const successMessages = [];
    if (imsData) successMessages.push('IMS检测详情');
    if (ruleData) successMessages.push('规则检测详情');
    if (msfgData && msfgData.msfg) successMessages.push('MSFG检测详情');
    
    console.log('成功加载的模块:', successMessages);
    
    if (successMessages.length > 0) {
      ElMessage.success(`成功加载${successMessages.join('、')}`);
    } else {
      ElMessage.warning('获取检测详情失败，使用模拟数据');
    }
    
  } catch (error) {
    console.error('❌ 获取检测详情失败:', error);
    ElMessage.warning('获取检测详情失败，使用模拟数据');
    // 保持使用模拟数据，不进行任何更改
  }
}

// 恢复显示MSFG详情的方法
function showMsfgDetails(component) {
  activeMsfgComponent.value = component;
  showMsfgDetailDialog.value = true;
}

function getConfidenceColor(confidence) {
  if (confidence > 90) return '#f56c6c';
  if (confidence > 80) return '#e6a23c';
  return '#67c23a';
}

// 新增：格式化参数分数用于表格
function formatParameterScores(scores) {
  if (!scores) return [];
  return Object.entries(scores).map(([parameter, score]) => ({
    parameter,
    score: score.toFixed(4)
  }));
}


// 初始化扇形图
function initPieChart() {
  if (!pieChartRef.value || !componentDetailData.value) {
    console.log('扇形图容器或数据不可用');
    return;
  }

  // 销毁已存在的图表实例
  if (pieChartInstance) {
    pieChartInstance.dispose();
    pieChartInstance = null;
  }

  // 准备扇形图数据
  const pieData = preparePieChartData();
  
  if (!pieData || pieData.length === 0) {
    console.log('没有可用的扇形图数据');
    return;
  }

  // 创建扇形图实例
  pieChartInstance = echarts.init(pieChartRef.value);
  
  const option = {
    title: {
      text: `${componentDetailData.value.center_component?.name || '部件'} - 测点与故障分数分布`,
      left: 'center',
      top: 20,
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        const percentage = (params.percent).toFixed(1);
        return `${params.name}<br/>
                分数: ${params.value.toFixed(3)}<br/>
                占比: ${percentage}%<br/>
                类型: ${params.data.category}`;
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle',
      formatter: function(name) {
        const item = pieData.find(d => d.name === name);
        return `${name} (${item?.value?.toFixed(3) || 0})`;
      }
    },
    series: [
      {
        name: '分数分布',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '55%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold',
            formatter: function(params) {
              return `${params.name}\n${params.value.toFixed(3)}`;
            }
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        labelLine: {
          show: false
        },
        data: pieData
      }
    ]
  };

  pieChartInstance.setOption(option);
  
  // 响应式调整
  window.addEventListener('resize', () => {
    if (pieChartInstance) {
      pieChartInstance.resize();
    }
  });
  
  console.log('扇形图初始化完成，数据点数量:', pieData.length);
}

// 准备扇形图数据
function preparePieChartData() {
  if (!componentDetailData.value) return [];
  
  const data = [];
  
  // 添加所有测点数据（用深蓝色表示）
  if (componentDetailData.value.surrounding_testpoints) {
    componentDetailData.value.surrounding_testpoints.forEach(testpoint => {
      const score = testpoint.average_score || 0;
      // 显示所有测点，包括分数为0的
        data.push({
          name: `[测点] ${testpoint.name}`,
          value: score,
          category: '测点',
          itemStyle: {
          color: '#3498db' // 明亮蓝色
          }
        });
    });
  }
  
  // 添加所有故障数据（用橙色表示）
  if (componentDetailData.value.surrounding_faults) {
    componentDetailData.value.surrounding_faults.forEach(fault => {
      const score = fault.average_score || 0;
      // 显示所有故障，包括分数为0的
        data.push({
          name: `[故障] ${fault.name}`,
          value: score,
          category: '故障',
          itemStyle: {
          color: '#e67e22' // 橙色
          }
        });
    });
  }
  
  // 如果没有数据，返回空数组
  if (data.length === 0) {
    return [];
  }
  
  // 按分数降序排序（分数越大，扇形越大）
  data.sort((a, b) => b.value - a.value);
  
  return data;
}

// 根据分数和类型获取颜色
function getScoreColor(score, type) {
  const colors = {
    testpoint: {
      high: '#f56c6c',     // 红色 - 高异常
      medium: '#e6a23c',   // 橙色 - 中异常
      low: '#409eff',      // 蓝色 - 低异常
      normal: '#67c23a'    // 绿色 - 正常
    },
    fault: {
      high: '#909399',     // 深灰色 - 高异常
      medium: '#c0c4cc',   // 浅灰色 - 中异常  
      low: '#e4e7ed',      // 更浅灰色 - 低异常
      normal: '#f0f2f5'    // 最浅灰色 - 正常
    }
  };
  
  const colorSet = colors[type] || colors.testpoint;
  const numScore = Number(score || 0);
  
  if (numScore >= 0.8) return colorSet.high;
  if (numScore >= 0.5) return colorSet.medium;
  if (numScore >= 0.2) return colorSet.low;
  return colorSet.normal;
}

// 新增方法
function showTelemetryDialog() {
  // 重置遥测数据状态
  telemetryCharts.value = [];
  selectedTelemetryParameters.value = [];
  availableTelemetryParameters.value = [];
  
  // 显示对话框
  telemetryDialogVisible.value = true;
  
  // 先测试API是否工作
  testAPI();
  
  // 如果有选中的异常帧，自动获取可用的遥测量
  if (selectedAnomalyFrame.value?.id) {
    fetchAvailableTelemetryParameters();
  }
}

// 测试API是否工作
async function testAPI() {
  try {
    console.log('测试API连接...');
    const response = await fetch('/api/v1/data/detection-overview/?action=test');
    console.log('测试API响应状态:', response.status);
    
    if (response.ok) {
      const data = await response.json();
      console.log('测试API成功:', data);
    } else {
      const errorText = await response.text();
      console.error('测试API失败:', errorText);
    }
  } catch (error) {
    console.error('测试API连接失败:', error);
  }
}

// 获取可用的遥测量参数
async function fetchAvailableTelemetryParameters() {
  if (!selectedAnomalyFrame.value?.id) {
    ElMessage.warning('请先选择一个异常帧');
    return;
  }
  
  console.log('开始获取遥测量参数，异常帧ID:', selectedAnomalyFrame.value.id);
  
  try {
    const url = `/api/v1/data/detection-overview/?action=telemetry_data&frame_id=${selectedAnomalyFrame.value.id}&frames_before=1&frames_after=1`;
    console.log('请求URL:', url);
    
    const response = await fetch(url);
    console.log('响应状态:', response.status, response.statusText);
    
    if (!response.ok) {
      // 尝试获取错误响应内容
      const errorText = await response.text();
      console.error('错误响应内容:', errorText);
      throw new Error(`HTTP error! status: ${response.status}, response: ${errorText}`);
    }
    
    const data = await response.json();
    console.log('遥测数据响应:', data);
    
    availableTelemetryParameters.value = data.available_parameters || [];
    console.log('可用遥测量参数:', availableTelemetryParameters.value);
  } catch (error) {
    console.error('获取遥测量参数失败:', error);
    ElMessage.error(`获取遥测量参数失败: ${error.message}`);
  }
}

// 加载内联遥测数据（用于详情对话框中的遥测图表）
async function loadTelemetryData() {
  if (!selectedAnomalyFrame.value?.id) {
    ElMessage.warning('请先选择一个异常帧');
    return;
  }
  
  if (selectedTelemetryParameters.value.length === 0) {
    ElMessage.warning('请选择要显示的遥测量');
    return;
  }
  
  telemetryLoading.value = true;
  
  try {
    const params = new URLSearchParams({
      action: 'telemetry_data',
      frame_id: selectedAnomalyFrame.value.id,
      frames_before: telemetryFramesBefore.value,
      frames_after: telemetryFramesBefore.value,  // 使用相同的前后帧数
    });
    
    // 添加选中的遥测量参数
    selectedTelemetryParameters.value.forEach(param => {
      params.append('parameters', param);
    });
    
    const response = await fetch(`/api/v1/data/detection-overview/?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('内联遥测数据响应:', data);
    
    // 处理遥测数据并生成内联图表
    processInlineTelemetryData(data);
    
    ElMessage.success(`成功获取 ${data.total_frames} 帧遥测数据`);
  } catch (error) {
    console.error('获取内联遥测数据失败:', error);
    ElMessage.error('获取遥测数据失败');
  } finally {
    telemetryLoading.value = false;
  }
}

// 获取遥测数据（用于独立的遥测数据对话框）
async function fetchTelemetryData() {
  if (!selectedAnomalyFrame.value?.id) {
    ElMessage.warning('请先选择一个异常帧');
    return;
  }
  
  if (selectedTelemetryParameters.value.length === 0) {
    ElMessage.warning('请选择要显示的遥测量');
    return;
  }
  
  telemetryLoading.value = true;
  
  try {
    const params = new URLSearchParams({
      action: 'telemetry_data',
      frame_id: selectedAnomalyFrame.value.id,
      frames_before: telemetryFramesBefore.value,
      frames_after: telemetryFramesAfter.value,
    });
    
    // 添加选中的遥测量参数
    selectedTelemetryParameters.value.forEach(param => {
      params.append('parameters', param);
    });
    
    const response = await fetch(`/api/v1/data/detection-overview/?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('遥测数据响应:', data);
    
    // 处理遥测数据并生成图表
    processTelemetryData(data);
    
    ElMessage.success(`成功获取 ${data.total_frames} 帧遥测数据`);
  } catch (error) {
    console.error('获取遥测数据失败:', error);
    ElMessage.error('获取遥测数据失败');
  } finally {
    telemetryLoading.value = false;
  }
}

// 处理内联遥测数据并生成图表
function processInlineTelemetryData(data) {
  console.log('开始处理内联遥测数据:', data);
  telemetryCharts.value = [];
  
  console.log('选中的遥测量参数:', selectedTelemetryParameters.value);
  console.log('遥测数据点数量:', data.telemetry_data.length);
  
  // 为每个选中的遥测量创建图表数据
  selectedTelemetryParameters.value.forEach(parameter => {
    console.log(`处理遥测量: ${parameter}`);
    const dataPoints = [];
    const timestamps = [];
    
    data.telemetry_data.forEach((point, index) => {
      if (point.parameters[parameter] !== null && point.parameters[parameter] !== undefined) {
        dataPoints.push(point.parameters[parameter]);
        timestamps.push(point.timestamp);
      }
    });
    
    console.log(`遥测量 ${parameter} 有效数据点:`, dataPoints.length);
    
    if (dataPoints.length > 0) {
      const targetIndex = data.telemetry_data.findIndex(p => p.is_target);
      console.log(`遥测量 ${parameter} 目标帧索引:`, targetIndex);
      
      telemetryCharts.value.push({
        parameter,
        dataPoints,
        timestamps,
        targetIndex
      });
    }
  });
  
  console.log('生成的内联图表数量:', telemetryCharts.value.length);
  
  // 在下一个tick渲染图表
  setTimeout(() => {
    console.log('开始渲染内联图表...');
    renderInlineTelemetryCharts();
  }, 100);
}

// 处理遥测数据并生成图表
function processTelemetryData(data) {
  console.log('开始处理遥测数据:', data);
  telemetryCharts.value = [];
  
  console.log('选中的遥测量参数:', selectedTelemetryParameters.value);
  console.log('遥测数据点数量:', data.telemetry_data.length);
  
  // 为每个选中的遥测量创建图表数据
  selectedTelemetryParameters.value.forEach(parameter => {
    console.log(`处理遥测量: ${parameter}`);
    const dataPoints = [];
    const timestamps = [];
    
    data.telemetry_data.forEach((point, index) => {
      if (point.parameters[parameter] !== null && point.parameters[parameter] !== undefined) {
        dataPoints.push(point.parameters[parameter]);
        timestamps.push(point.timestamp);
      }
    });
    
    console.log(`遥测量 ${parameter} 有效数据点:`, dataPoints.length);
    
    if (dataPoints.length > 0) {
      const targetIndex = data.telemetry_data.findIndex(p => p.is_target);
      console.log(`遥测量 ${parameter} 目标帧索引:`, targetIndex);
      
      telemetryCharts.value.push({
        parameter,
        dataPoints,
        timestamps,
        targetIndex
      });
    }
  });
  
  console.log('生成的图表数量:', telemetryCharts.value.length);
  
  // 在下一个tick渲染图表
  setTimeout(() => {
    console.log('开始渲染图表...');
    renderTelemetryCharts();
  }, 100);
}

// 渲染遥测图表
function renderTelemetryCharts() {
  console.log('开始渲染遥测图表，图表数量:', telemetryCharts.value.length);
  
  telemetryCharts.value.forEach((chart, index) => {
    console.log(`渲染第${index + 1}个图表:`, chart.parameter);
    console.log('图表数据点数量:', chart.dataPoints.length);
    console.log('图表时间戳数量:', chart.timestamps.length);
    console.log('目标帧索引:', chart.targetIndex);
    
    const chartId = `telemetry-chart-${chart.parameter}`;
    const chartElement = document.getElementById(chartId);
    
    console.log('查找图表容器:', chartId, '找到元素:', !!chartElement);
    
    if (!chartElement) {
      console.warn(`图表容器未找到: ${chartId}`);
      return;
    }
    
    // 销毁已存在的图表实例
    if (telemetryChartInstances.value[chart.parameter]) {
      console.log('销毁已存在的图表实例:', chart.parameter);
      telemetryChartInstances.value[chart.parameter].dispose();
    }
    
    // 创建新的图表实例
    console.log('创建新的图表实例:', chart.parameter);
    const chartInstance = echarts.init(chartElement);
    telemetryChartInstances.value[chart.parameter] = chartInstance;
    
    // 准备图表数据
    const xAxisData = chart.timestamps.map(ts => {
      const date = new Date(ts);
      return date.toLocaleTimeString();
    });
    
    const seriesData = chart.dataPoints.map((value, index) => ({
      value: value,
      itemStyle: {
        color: index === chart.targetIndex ? '#ff4d4f' : '#1890ff'
      }
    }));
    
    console.log('X轴数据:', xAxisData.slice(0, 5), '...');
    console.log('Y轴数据:', seriesData.slice(0, 5), '...');
    
    // 配置图表选项
    const option = {
      title: {
        text: chart.parameter,
        left: 'center',
        textStyle: {
          fontSize: 14,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          const dataIndex = params[0].dataIndex;
          const timestamp = chart.timestamps[dataIndex];
          const value = params[0].value;
          const isTarget = dataIndex === chart.targetIndex;
          return `
            <div>
              <strong>${chart.parameter}</strong><br/>
              时间: ${new Date(timestamp).toLocaleString()}<br/>
              值: ${value}<br/>
              ${isTarget ? '<span style="color: #ff4d4f;">● 目标帧</span>' : ''}
            </div>
          `;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        axisLabel: {
          rotate: 45,
          fontSize: 10
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          fontSize: 10
        }
      },
      series: [{
        name: chart.parameter,
        type: 'line',
        data: seriesData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: {
          width: 2
        },
        markLine: chart.targetIndex >= 0 ? {
          data: [{
            xAxis: chart.targetIndex,
            lineStyle: {
              color: '#ff4d4f',
              type: 'dashed',
              width: 2
            },
            label: {
              show: true,
              position: 'end',
              formatter: '目标帧'
            }
          }]
        } : undefined
      }]
    };
    
    // 设置图表选项
    console.log('设置图表选项:', chart.parameter);
    chartInstance.setOption(option);
    console.log('图表设置完成:', chart.parameter);
    
    // 响应式调整
    window.addEventListener('resize', () => {
      chartInstance.resize();
    });
  });
  
  console.log('所有图表渲染完成');
}

// 渲染内联遥测图表
function renderInlineTelemetryCharts() {
  console.log('开始渲染内联遥测图表，图表数量:', telemetryCharts.value.length);
  
  telemetryCharts.value.forEach((chart, index) => {
    console.log(`渲染第${index + 1}个内联图表:`, chart.parameter);
    
    const chartId = `inline-chart-${chart.parameter}`;
    const chartElement = document.getElementById(chartId);
    
    console.log('查找内联图表容器:', chartId, '找到元素:', !!chartElement);
    
    if (!chartElement) {
      console.warn(`内联图表容器未找到: ${chartId}`);
      return;
    }
    
    // 销毁已存在的图表实例
    if (telemetryChartInstances.value[chart.parameter]) {
      console.log('销毁已存在的图表实例:', chart.parameter);
      telemetryChartInstances.value[chart.parameter].dispose();
    }
    
    // 创建新的图表实例
    const chartInstance = echarts.init(chartElement);
    telemetryChartInstances.value[chart.parameter] = chartInstance;
    
    // 准备图表数据
    const xAxisData = chart.timestamps.map(ts => {
      const date = new Date(ts);
      return date.toLocaleTimeString();
    });
    
    const seriesData = chart.dataPoints.map((value, index) => ({
      value: value,
      itemStyle: {
        color: index === chart.targetIndex ? '#ff4d4f' : '#1890ff'
      }
    }));
    
    // 配置图表选项（内联版本，更紧凑）
    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: function(params) {
          const dataIndex = params[0].dataIndex;
          const timestamp = chart.timestamps[dataIndex];
          const value = params[0].value;
          const isTarget = dataIndex === chart.targetIndex;
          return `
            <div>
              <strong>${chart.parameter}</strong><br/>
              时间: ${new Date(timestamp).toLocaleString()}<br/>
              值: ${value}<br/>
              ${isTarget ? '<span style="color: #ff4d4f;">● 目标帧</span>' : ''}
            </div>
          `;
        }
      },
      grid: {
        left: '8%',
        right: '5%',
        top: '10%',
        bottom: '15%',
        containLabel: false
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        axisLabel: {
          rotate: 30,
          fontSize: 9
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          fontSize: 9
        }
      },
      series: [{
        name: chart.parameter,
        type: 'line',
        data: seriesData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 3,
        lineStyle: {
          width: 1.5
        },
        markLine: chart.targetIndex >= 0 ? {
          data: [{
            xAxis: chart.targetIndex,
            lineStyle: {
              color: '#ff4d4f',
              type: 'dashed',
              width: 2
            },
            label: {
              show: true,
              position: 'end',
              formatter: '目标',
              fontSize: 10
            }
          }]
        } : undefined
      }]
    };
    
    // 设置图表选项
    chartInstance.setOption(option);
    
    // 响应式调整
    window.addEventListener('resize', () => {
      chartInstance.resize();
    });
  });
  
  console.log('所有内联图表渲染完成');
}

// 遥测量参数选择变化处理
function onTelemetryParametersChange() {
  console.log('选中的遥测量参数:', selectedTelemetryParameters.value);
}

// 获取部件分数
async function fetchComponentScores(cmgId, startTime, endTime) {
  try {
    console.log('开始获取部件分数:', { cmgId, startTime, endTime });
    
    const response = await fetch(`/api/v1/data/detection-overview/?action=component_scores&cmg_id=${cmgId}&start_time=${startTime}&end_time=${endTime}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('部件分数响应:', data);
    
    // 更新右侧部件显示
    updateComponentScores(data.component_scores);
    
    ElMessage.success(`成功获取 ${data.total_components} 个部件的分数数据`);
  } catch (error) {
    console.error('获取部件分数失败:', error);
    ElMessage.error('获取部件分数失败');
  }
}

// 获取可用的算法列表
async function fetchAvailableAlgorithms() {
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

// 打开剩余寿命设置对话框
function openLifetimeSettings() {
  // 检查是否已选择CMG和时间段
  if (!selectedCmgId.value) {
    ElMessage.warning('请先选择CMG个体');
    return;
  }
  
  if (!timeRange.value || timeRange.value.length !== 2) {
    ElMessage.warning('请先选择数据时间段');
    return;
  }
  
  // 获取算法列表
  fetchAvailableAlgorithms();
  
  // 设置默认值
  lifetimeSettings.value.designLife = 10;
  
  // 如果有时间轴数据，使用最早的时间戳作为默认启用时间
  if (timelineData.value && timelineData.value.timeline && timelineData.value.timeline.length > 0) {
    const earliestTime = new Date(timelineData.value.timeline[0].timestamp);
    lifetimeSettings.value.startUseTime = earliestTime.toISOString().replace('T', ' ').split('.')[0];
  } else if (timeRange.value && timeRange.value.length === 2) {
    // 使用选择的时间段的开始时间作为默认启用时间
    const startTime = new Date(timeRange.value[0]);
    lifetimeSettings.value.startUseTime = startTime.toISOString().replace('T', ' ').split('.')[0];
  } else {
    // 如果没有任何时间数据，使用当前时间
    const now = new Date();
    lifetimeSettings.value.startUseTime = now.toISOString().replace('T', ' ').split('.')[0];
  }
  
  showLifetimeSettingsDialog.value = true;
}

// 确认剩余寿命设置
async function confirmLifetimeSettings() {
  if (!lifetimeSettings.value.designLife || !lifetimeSettings.value.startUseTime) {
    ElMessage.warning('请设置设计寿命和启用时间');
    return;
  }
  
  showLifetimeSettingsDialog.value = false;
  lifetimePredicting.value = true; // 开始预测，显示加载状态
  
  console.log('用户确认更新寿命预测参数:', {
    designLife: lifetimeSettings.value.designLife,
    startUseTime: lifetimeSettings.value.startUseTime,
    algorithm: lifetimeSettings.value.algorithm,
    selectedCmgId: selectedCmgId.value,
    timeRange: timeRange.value
  });
  
  // 重新获取寿命趋势数据
  if (selectedCmgId.value && timeRange.value && timeRange.value.length === 2) {
    const selectedCmg = cmgInstances.value.find(cmg => cmg.id === selectedCmgId.value);
    if (selectedCmg) {
      const startTime = timeRange.value[0].toISOString();
      const endTime = timeRange.value[1].toISOString();
      
      console.log('开始重新获取寿命趋势数据，新参数:', {
        cmgId: selectedCmg.id,
        startTime,
        endTime,
        designLife: lifetimeSettings.value.designLife,
        startUseTime: lifetimeSettings.value.startUseTime,
        algorithm: lifetimeSettings.value.algorithm
      });
      
      try {
        await fetchLifetimeTrendWithSettings(
          selectedCmg.id, 
          startTime, 
          endTime, 
          lifetimeSettings.value.designLife,
          lifetimeSettings.value.startUseTime,
          lifetimeSettings.value.algorithm
        );
        
        console.log('寿命趋势数据重新获取完成');
        
        // 确保图表已经更新（额外的保险措施）
        setTimeout(() => {
          if (healthChart.value && myChart) {
            console.log('设置参数更新后，确保图表正确显示');
            myChart.resize(); // 触发图表重新渲染
          }
        }, 200);
        
      } catch (error) {
        console.error('重新获取寿命趋势数据失败:', error);
        ElMessage.error('更新寿命预测参数失败，请重试');
        return;
      } finally {
        lifetimePredicting.value = false; // 预测完成，关闭加载状态
      }
    }
  }
  
  ElMessage.success('剩余寿命预测参数已更新');
}

// 关闭剩余寿命设置对话框
function handleLifetimeSettingsClose() {
  // 如果正在预测中，阻止关闭对话框
  if (lifetimePredicting.value) {
    ElMessage.warning('正在进行寿命预测，请等待完成...');
    return;
  }
  showLifetimeSettingsDialog.value = false;
}

// 获取剩余寿命和趋势图数据（使用默认设置）
async function fetchLifetimeTrend(cmgId, startTime, endTime) {
  return await fetchLifetimeTrendWithSettings(cmgId, startTime, endTime, 10, null, 'strategy0');
}

// 获取剩余寿命和趋势图数据（带自定义设置）
async function fetchLifetimeTrendWithSettings(cmgId, startTime, endTime, designLife, startUseTime, algorithm = 'strategy0') {
  try {
    console.log('开始获取寿命趋势数据:', { cmgId, startTime, endTime, designLife, startUseTime, algorithm });
    
    let url = `/api/v1/data/detection-overview/?action=lifetime_trend&cmg_id=${cmgId}&start_time=${startTime}&end_time=${endTime}&design_life=${designLife}`;
    if (startUseTime) {
      url += `&start_use_time=${encodeURIComponent(startUseTime)}`;
    }
    if (algorithm) {
      url += `&algorithm=${algorithm}`;
    }
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('寿命趋势响应:', data);
    
    if (data.status === 'success') {
      // 更新剩余寿命显示 - 后端返回的RUL单位是年
      remainingLife.value = data.remaining_life_years; // 使用正确的字段名
      
      // 更新当前算法信息
      if (algorithm && availableAlgorithms.value.length > 0) {
        currentAlgorithmInfo.value = availableAlgorithms.value.find(algo => algo.key === algorithm);
      }
      
      // 更新趋势图数据 - 使用更可靠的方式确保图表容器存在
      console.log('准备更新健康趋势图，当前状态:', {
        myChart: !!myChart,
        healthChart: !!healthChart.value,
        containerExists: !!document.querySelector('.chart-container')
      });
      
      // 使用更可靠的延迟策略和容错机制
      const updateChartWithRetry = (retryCount = 0) => {
        const maxRetries = 10; // 增加重试次数
        
        if (retryCount >= maxRetries) {
          console.error('健康趋势图更新重试次数过多，放弃更新');
          return;
        }
        
        // 确保图表实例和容器都存在
        if (myChart && healthChart.value) {
          // 使用 nextTick 确保 DOM 更新完成
          nextTick(() => {
            updateHealthTrendChart(data.trend_data);
          });
        } else if (healthChart.value && !myChart) {
          // 容器存在但图表实例不存在，尝试初始化
          console.log(`容器存在但图表实例不存在，尝试初始化... (重试${retryCount + 1})`);
          nextTick(() => {
            initHealthChart();
            setTimeout(() => updateChartWithRetry(retryCount + 1), 150);
          });
        } else {
          // 容器不存在，继续等待
          console.log(`图表容器未就绪，等待中... (重试${retryCount + 1})`);
          setTimeout(() => updateChartWithRetry(retryCount + 1), 200);
        }
      };
      
      // 如果当前正在加载状态，保存数据待加载完成后更新
      if (isDataLoading.value) {
        console.log('当前正在加载状态，保存趋势数据待后续更新');
        pendingTrendData.value = data.trend_data;
        return;
      }
      
      updateChartWithRetry();
      
      console.log('寿命预测数据更新:', {
        remaining_life_years: data.remaining_life_years,
        trend_data_count: data.trend_data ? data.trend_data.length : 0
      });
      
      ElMessage.success(`成功获取寿命预测数据，剩余寿命: ${data.remaining_life_years.toFixed(2)} 年`);
    } else {
      // 针对特定错误提供更友好的提示
      const errorMessage = data.error || '获取寿命趋势数据失败'
      if (errorMessage.includes('使用起点时间不能晚于数据起点时间')) {
        ElMessage.error('设置的启用时间晚于数据起始时间，请重新设置剩余寿命参数')
        throw new Error('时间设置错误')
      } else if (errorMessage.includes('数据终点时间已经超过设计寿命')) {
        ElMessage.error('数据时间范围已超过设计寿命，请调整设计寿命或数据时间范围')
        throw new Error('设计寿命设置错误')
      } else {
        throw new Error(errorMessage)
      }
    }
  } catch (error) {
    console.error('获取寿命趋势数据失败:', error);
    
    // 针对不同类型的错误提供不同的用户提示
    if (error.message === '时间设置错误') {
      // 已经在上面显示了具体的错误信息，这里不再重复
      remainingLife.value = 0; // 设置为0表示需要重新配置
    } else if (error.message === '设计寿命设置错误') {
      // 已经在上面显示了具体的错误信息，这里不再重复
      remainingLife.value = 0; // 设置为0表示需要重新配置
    } else if (error.message && error.message.includes('使用起点时间不能晚于数据起点时间')) {
      ElMessage.error('设置的启用时间晚于数据起始时间，请重新设置剩余寿命参数');
      remainingLife.value = 0;
    } else if (error.message && error.message.includes('数据终点时间已经超过设计寿命')) {
      ElMessage.error('数据时间范围已超过设计寿命，请调整设计寿命或数据时间范围');
      remainingLife.value = 0;
    } else {
      ElMessage.error('获取寿命趋势数据失败，请检查设置或稍后重试');
      // 使用默认值（年）
      remainingLife.value = 2.12;
    }
  }
}

// 更新部件分数显示
function updateComponentScores(componentScores) {
  console.log('更新部件分数显示:', componentScores);
  
  if (!componentScores || componentScores.length === 0) {
    console.log('没有部件分数数据，使用默认数据');
    return;
  }
  
  // 将部件分数数据转换为subComponents格式
  const leftComponents = [];
  const rightComponents = [];
  
  componentScores.forEach((component, index) => {
    const componentData = {
      id: `comp_${index}`,
      name: component.component_name,
      healthScore: component.average_score,
      scoreCount: component.score_count,
      minScore: component.min_score,
      maxScore: component.max_score
    };
    
    // 交替分配到左右两侧
    if (index % 2 === 0) {
      leftComponents.push(componentData);
    } else {
      rightComponents.push(componentData);
    }
  });
  
  // 更新subComponents数据
  subComponents.value = {
    left: leftComponents,
    right: rightComponents
  };
  
  console.log('更新后的subComponents:', subComponents.value);
  console.log('部件总数:', totalComponents.value);
  console.log('当前部件方块样式:', componentBoxStyle.value);
  console.log('是否启用滚动:', totalComponents.value > 6);
}

// 更新健康趋势图
function updateHealthTrendChart(trendData, retryCount = 0) {
  const maxRetries = 3; // 减少内部重试次数，因为外部已有重试逻辑
  
  console.log('=== 更新健康趋势图 ===');
  console.log('数据点数:', trendData ? trendData.length : 0);
  console.log('图表实例存在:', !!myChart);
  console.log('图表容器存在:', !!healthChart.value);
  console.log('内部重试次数:', retryCount);
  
  // 如果重试次数过多，停止重试
  if (retryCount >= maxRetries) {
    console.error('图表内部更新重试次数过多，停止重试');
    return;
  }
  
  // 如果图表容器不存在，延迟执行（减少延迟时间）
  if (!healthChart.value) {
    console.warn('图表容器元素不存在，延迟50ms后重试...');
    setTimeout(() => {
      updateHealthTrendChart(trendData, retryCount + 1);
    }, 50);
    return;
  }
  
  // 如果图表实例不存在，尝试重新初始化
  if (!myChart) {
    console.warn('图表实例不存在，尝试重新初始化...');
    initHealthChart();
    if (!myChart) {
      console.error('图表重新初始化失败，延迟50ms后重试...');
      setTimeout(() => {
        updateHealthTrendChart(trendData, retryCount + 1);
      }, 50);
      return;
    }
  }
  
  // 确保图表实例有效
  if (!ensureChartInstance()) {
    console.error('无法确保图表实例存在，延迟50ms后重试...');
    setTimeout(() => {
      updateHealthTrendChart(trendData, retryCount + 1);
    }, 50);
    return;
  }
  
  // 检查容器尺寸
  if (healthChart.value) {
    console.log('当前容器尺寸:', {
      width: healthChart.value.offsetWidth,
      height: healthChart.value.offsetHeight,
      clientWidth: healthChart.value.clientWidth,
      clientHeight: healthChart.value.clientHeight
    });
  }

  if (!trendData || trendData.length === 0) {
    console.log('没有趋势数据，清空图表');
    // 使用 setOption 传入一个空系列来清空图表，而不是 clear，以保留配置
    myChart.setOption({ series: [] });
    return;
  }
  
  // 准备 ECharts 需要的数据格式 [timestamp, value]
  const chartData = trendData.map(item => {
    const value = parseFloat(item.health_index);
    // 将无效数据处理为 null，ECharts 会自动在该点断开
    return [item.timestamp, isNaN(value) ? null : value];
  });

  console.log(`数据处理完成，共 ${chartData.length} 个点`);

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function (params) {
        const point = params[0];
        const date = new Date(point.value[0]).toLocaleString('zh-CN');
        const value = point.value[1];
        return `时间: ${date}<br/>健康指数: ${value.toFixed(4)}`;
      }
    },
    xAxis: {
      type: 'time', // 使用时间轴
      axisLabel: {
        hideOverlap: true, // 自动隐藏重叠的标签
        formatter: '{yyyy}-{MM}-{dd}\n{HH}:{mm}:{ss}', // 格式化时间显示
        fontSize: 10, // 减小字体大小
        margin: 5 // 减少标签与轴线的距离
      }
    },
    yAxis: {
      type: 'value',
      scale: true, // 核心：允许Y轴根据数据动态缩放，不局限于0-1
      axisLabel: {
        formatter: '{value}',
        fontSize: 10, // 减小字体大小
        margin: 5 // 减少标签与轴线的距离
      }
    },
    grid: {
      left: '3%',   // 减少左边距，让图表更宽
      right: '2%',  // 减少右边距
      bottom: '2%', // 减少底部边距
      top: '8%',    // 增加顶部边距，让标题往上移动
      containLabel: true
      },
      series: [
        {
          name: '健康指数',
          type: 'line',
        data: chartData,
          smooth: true,
        symbol: 'none', // 数据量大时隐藏标记点
        lineStyle: {
          color: '#409eff',
          width: 2
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      }
    ]
  };
    
  myChart.setOption(option, true); // `true` 表示不与之前的配置合并
  console.log('健康趋势图已更新');
  console.log('最终图表配置:', option);
  console.log('图表实例尺寸:', myChart.getWidth(), 'x', myChart.getHeight());
}

// 计算部件总数
const totalComponents = computed(() => {
  return (subComponents.value.left?.length || 0) + (subComponents.value.right?.length || 0);
});

// 圆形布局相关计算属性
const layoutSize = computed(() => {
  return {
    width: 600,
    height: 450
  };
});

const centerPosition = computed(() => {
  return {
    x: layoutSize.value.width / 2,
    y: layoutSize.value.height / 2
  };
});

const centerRadius = computed(() => {
  return 45;
});

// 限制显示的节点数量
const maxDisplayNodes = 10; // 最多显示15个节点（测点+故障）

const limitedTestpoints = computed(() => {
  if (!componentDetailData.value?.surrounding_testpoints) return [];
  return componentDetailData.value.surrounding_testpoints.slice(0, Math.min(8, maxDisplayNodes));
});

const limitedFaults = computed(() => {
  if (!componentDetailData.value?.surrounding_faults) return [];
  const remainingSlots = maxDisplayNodes - limitedTestpoints.value.length;
  return componentDetailData.value.surrounding_faults.slice(0, Math.max(0, remainingSlots));
});

const connections = computed(() => {
  if (!componentDetailData.value) return [];
  
  const conns = [];
  const center = centerPosition.value;
  
  // 测点连线（只连接显示的测点）
  limitedTestpoints.value.forEach((testpoint, index) => {
    if (testpoint.position) {
      conns.push({
        from: 'center',
        to: `testpoint-${index}`,
        x1: center.x,
        y1: center.y,
        x2: testpoint.position.x,
        y2: testpoint.position.y,
        color: '#409eff',
        width: 2,
        dashed: false
      });
    }
  });
  
  // 故障连线（只连接显示的故障）
  limitedFaults.value.forEach((fault, index) => {
    if (fault.position) {
      conns.push({
        from: 'center',
        to: `fault-${index}`,
        x1: center.x,
        y1: center.y,
        x2: fault.position.x,
        y2: fault.position.y,
        color: '#f56c6c',
        width: 2,
        dashed: true
      });
    }
  });
  
  return conns;
});

// 根据部件数量动态调整样式
const componentBoxStyle = computed(() => {
  const count = totalComponents.value;
  
  if (count <= 4) {
    // 部件较少时，使用较大尺寸
    return {
      width: '260px', // 再次增加宽度
      padding: '12px',
      fontSize: '14px',
      gap: '15px'
    };
  } else if (count <= 6) {
    // 部件中等时，使用中等尺寸
    return {
      width: '240px', // 再次增加宽度
      padding: '10px',
      fontSize: '13px',
      gap: '12px'
    };
  } else {
    // 部件较多时，启用滚动并使用固定尺寸
    return {
      width: '220px', // 再次增加宽度
      padding: '8px',
      fontSize: '13px',
      gap: '10px'
    };
  }
});

function getHealthColor(score) {
  // 按照新的颜色规则：1-0.75绿色，0.75-0.5橙色，0.5以下红色
  if (score >= 0.75) return '#67c23a'; // 绿色：1-0.75
  if (score >= 0.5) return '#e6a23c';  // 橙色：0.75-0.5
  return '#f56c6c'; // 红色：0.5以下
}

// 获取健康状态样式类
function getHealthStatusClass(score) {
  if (score >= 0.75) return 'status-healthy';
  if (score >= 0.5) return 'status-warning';
  return 'status-danger';
}

// 获取寿命状态样式类
function getLifeStatusClass(lifeYears) {
  if (lifeYears >= 5) return 'life-healthy';
  if (lifeYears >= 2) return 'life-warning';
  if (lifeYears >= 0.5) return 'life-danger';
  return 'life-critical';
}

// 获取寿命状态文本
function getLifeStatusText(lifeYears) {
  if (lifeYears >= 5) return '健康';
  if (lifeYears >= 2) return '注意';
  if (lifeYears >= 0.5) return '危险';
  return '紧急';
}

// 刷新寿命预测图表
async function refreshLifetimeChart() {
  if (!selectedCmgId.value || !timeRange.value || timeRange.value.length !== 2) {
    ElMessage.warning('请先选择CMG个体和时间段');
    return;
  }
  
  const selectedCmg = cmgInstances.value.find(cmg => cmg.id === selectedCmgId.value);
  if (!selectedCmg) {
    ElMessage.error('未找到选择的CMG个体');
    return;
  }
  
  try {
    lifetimePredicting.value = true;
    const startTime = new Date(timeRange.value[0]);
    const endTime = new Date(timeRange.value[1]);
    
    await fetchLifetimeTrendWithSettings(
      selectedCmg.id,
      startTime.toISOString(),
      endTime.toISOString(),
      lifetimeSettings.value.designLife,
      lifetimeSettings.value.startUseTime,
      lifetimeSettings.value.algorithm
    );
    
    ElMessage.success('寿命预测图表已刷新');
  } catch (error) {
    console.error('刷新寿命预测图表失败:', error);
    ElMessage.error('刷新失败，请重试');
  } finally {
    lifetimePredicting.value = false;
  }
}

// 圆形布局相关方法
function getNodeColor(score, type) {
  // 确保score是数字类型
  const numScore = parseFloat(score) || 0;
  
  // 根据分数和类型返回颜色
  if (type === 'component') {
    // 部件：按照新的颜色规则：1-0.75绿色，0.75-0.5橙色，0.5以下红色
    if (numScore >= 0.75) return '#67c23a'; // 绿色 - 健康
    if (numScore >= 0.5) return '#e6a23c'; // 橙色 - 警告
    return '#f56c6c'; // 红色 - 故障
  } else if (type === 'testpoint' || type === 'fault') {
    // 测点和故障：0.75-1红色，0.5-0.75橙色，0.1-0.5绿色
    // 对于测点和故障，0分或极低分数应该显示为绿色（正常状态）
    if (numScore >= 0.75) return '#f56c6c'; // 红色 - 严重异常/故障
    if (numScore >= 0.5) return '#e6a23c'; // 橙色 - 警告
    // 0.1以下也显示为绿色，表示正常状态（无故障）
    return '#67c23a'; // 绿色 - 正常状态
  }
  return '#67c23a'; // 默认绿色（正常状态）
}

function getNodeBorderColor(score, type) {
  // 使用与节点颜色相同的逻辑
  return getNodeColor(score, type);
}

function getScoreTextColor(score, type) {
  // 使用与节点颜色相同的逻辑
  return getNodeColor(score, type);
}

function getNodeFontSize(name) {
  // 根据名称长度调整字体大小
  if (name.length <= 6) return 10;
  if (name.length <= 10) return 9;
  return 8;
}

function calculateCircularPositions() {
  if (!componentDetailData.value) return;
  
  const center = centerPosition.value;
  const radius = 150; // 周围节点的半径（缩小以适应更小的布局）
  
  // 计算测点位置（只处理显示的测点）
  const testpoints = limitedTestpoints.value;
  const faults = limitedFaults.value;
  const totalDisplayNodes = testpoints.length + faults.length;
  
  testpoints.forEach((testpoint, index) => {
    const angle = (2 * Math.PI * index) / totalDisplayNodes;
    testpoint.position = {
      x: center.x + radius * Math.cos(angle),
      y: center.y + radius * Math.sin(angle)
    };
    testpoint.radius = 25; // 测点圆圈半径（调大）
    testpoint.shape = 'circle'; // 测点用圆形
  });
  
  // 计算故障位置（只处理显示的故障）
  faults.forEach((fault, index) => {
    const angle = (2 * Math.PI * (testpoints.length + index)) / totalDisplayNodes;
    fault.position = {
      x: center.x + radius * Math.cos(angle),
      y: center.y + radius * Math.sin(angle)
    };
    fault.radius = 30; // 故障圆圈半径（调大）
    fault.shape = 'square'; // 故障用方形
  });
}

async function showInferenceDialog(component) {
  selectedComponent.value = component;
  inferenceDialogVisible.value = true;
  
  // 重置数据
  componentDetailData.value = null;
  componentDetailLoading.value = true;
  
  try {
    // 检查是否有必要的时间范围数据
    if (!hasSelectedCmgAndTime.value || !timeRange.value || timeRange.value.length !== 2) {
      ElMessage.warning('请先选择CMG个体和时间段');
      componentDetailLoading.value = false;
      return;
    }
    
    // 获取选中的CMG个体
    const selectedCmg = cmgInstances.value.find(cmg => cmg.id === selectedCmgId.value);
    if (!selectedCmg) {
      ElMessage.error('未找到选中的CMG个体');
      componentDetailLoading.value = false;
      return;
    }
    
    // 构建API请求参数
    const params = new URLSearchParams({
      action: 'component_details',
      cmg_id: selectedCmg.id,
      component_name: component.name,
      start_time: timeRange.value[0].toISOString(),
      end_time: timeRange.value[1].toISOString()
    });
    
    console.log('获取部件详情，参数:', {
      cmg_id: selectedCmg.id,
      component_name: component.name,
      start_time: timeRange.value[0].toISOString(),
      end_time: timeRange.value[1].toISOString()
    });
    
    // 调用API
    const response = await fetch(`/api/v1/data/detection-overview/?${params}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('部件详情响应:', data);
    
    // 更新数据
    componentDetailData.value = data;
    
    // 初始化饼状图
    setTimeout(() => {
      initPieChart();
    }, 100);
    
    ElMessage.success(`成功获取部件 '${component.name}' 的详细信息`);
    
  } catch (error) {
    console.error('获取部件详情失败:', error);
    ElMessage.error(`获取部件详情失败: ${error.message}`);
  } finally {
    componentDetailLoading.value = false;
  }
}

// ECharts 初始化函数
function initHealthChart() {
  if (healthChart.value) {
    console.log('=== 初始化健康趋势图 ===');
    console.log('图表容器元素:', healthChart.value);
    console.log('容器尺寸:', {
      width: healthChart.value.offsetWidth,
      height: healthChart.value.offsetHeight,
      clientWidth: healthChart.value.clientWidth,
      clientHeight: healthChart.value.clientHeight
    });
    
    // 如果容器尺寸为0，等待下一个事件循环再初始化
    if (healthChart.value.offsetWidth === 0 || healthChart.value.offsetHeight === 0) {
      console.log('容器尺寸为0，延迟初始化...');
      setTimeout(() => {
        initHealthChart();
      }, 50);  // 减少延迟时间
      return;
    }
    
    // 如果已存在图表实例，先销毁
    if (myChart) {
      myChart.dispose();
      myChart = null;
    }
    
    myChart = echarts.init(healthChart.value);
    const option = {
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'time',
        axisLabel: {
          fontSize: 10,
          margin: 5
        }
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLabel: {
          fontSize: 10,
          margin: 5
        }
      },
      grid: {
        left: '3%',
        right: '2%',
        bottom: '2%',
        top: '8%',
        containLabel: true
      },
      series: [] // 初始时没有数据
    };
    myChart.setOption(option);
    console.log('图表初始化完成，当前配置:', option);
  } else {
    console.error('图表容器元素不存在!');
  }
}

// 确保图表实例存在的辅助函数
function ensureChartInstance() {
  if (!myChart && healthChart.value) {
    console.log('图表实例不存在，尝试重新初始化...');
    initHealthChart();
  }
  return !!myChart;
}

// 图表自适应调整
const resizeChart = () => {
  if (myChart) {
    console.log('=== 图表自适应调整 ===');
    console.log('调整前图表尺寸:', myChart.getWidth(), 'x', myChart.getHeight());
    if (healthChart.value) {
      console.log('容器当前尺寸:', {
        width: healthChart.value.offsetWidth,
        height: healthChart.value.offsetHeight
      });
    }
    myChart.resize();
    console.log('调整后图表尺寸:', myChart.getWidth(), 'x', myChart.getHeight());
  } else {
    // 如果图表实例不存在，尝试重新初始化
    ensureChartInstance();
  }
};

// 监听加载状态变化，在加载完成后更新待处理的趋势数据
watch(isDataLoading, (newValue, oldValue) => {
  console.log('isDataLoading 状态变化:', { from: oldValue, to: newValue });
  
  if (!newValue && oldValue) {
    console.log('加载完成，检查是否需要处理待更新的健康趋势数据');
    
    // 使用 nextTick 确保 DOM 已经更新（容器已经渲染）
    nextTick(() => {
      // 延迟一点时间确保图表容器完全渲染
      setTimeout(() => {
        // 首先确保图表已经初始化（无论是否有待处理数据）
        if (healthChart.value && !myChart) {
          console.log('加载完成后发现图表未初始化，进行初始化');
          initHealthChart();
        }
        
        // 如果有待处理的趋势数据，进行更新
        if (pendingTrendData.value) {
          console.log('开始更新待处理的健康趋势数据');
          
          const updateChartWithRetry = (retryCount = 0) => {
          const maxRetries = 5;
          
          if (retryCount >= maxRetries) {
            console.error('待处理趋势数据更新重试次数过多，放弃更新');
            return;
          }
          
          if (healthChart.value && myChart) {
            // 图表实例和容器都存在，直接更新
            updateHealthTrendChart(pendingTrendData.value);
            pendingTrendData.value = null; // 清空待处理数据
            console.log('成功更新待处理的健康趋势数据');
          } else if (healthChart.value && !myChart) {
            // 容器存在但图表实例不存在，先初始化图表
            console.log(`容器存在但图表实例不存在，初始化图表... (重试${retryCount + 1})`);
            initHealthChart();
            
            // 给图表初始化一些时间
            setTimeout(() => {
              if (myChart) {
                updateHealthTrendChart(pendingTrendData.value);
                pendingTrendData.value = null; // 清空待处理数据
                console.log('初始化图表后成功更新待处理的健康趋势数据');
              } else {
                updateChartWithRetry(retryCount + 1);
              }
            }, 50);
          } else {
            console.log(`待处理数据更新重试 ${retryCount + 1} (容器存在: ${!!healthChart.value}, 图表实例存在: ${!!myChart})`);
            setTimeout(() => updateChartWithRetry(retryCount + 1), 100);
          }
        };
        
          updateChartWithRetry();
        }
      }, 100);
    });
  }
});

onMounted(() => {
  // 延迟初始化图表，确保DOM完全渲染
  setTimeout(() => {
    initHealthChart();
  }, 200);  // 稍微增加初始化延迟，确保组件完全挂载
  
  window.addEventListener('resize', resizeChart);
  
  // 调试CSS样式
  setTimeout(() => {
    if (healthChart.value) {
      const computedStyle = window.getComputedStyle(healthChart.value);
      console.log('=== CSS样式调试 ===');
      console.log('健康趋势图容器样式:', {
        height: computedStyle.height,
        maxHeight: computedStyle.maxHeight,
        minHeight: computedStyle.minHeight,
        flex: computedStyle.flex,
        display: computedStyle.display,
        flexDirection: computedStyle.flexDirection
      });
      
      // 检查父容器样式
      const parentElement = healthChart.value.parentElement;
      if (parentElement) {
        const parentStyle = window.getComputedStyle(parentElement);
        console.log('父容器样式:', {
          height: parentStyle.height,
          maxHeight: parentStyle.maxHeight,
          flex: parentStyle.flex,
          display: parentStyle.display
        });
      }
    }
  }, 1000);
  
  // 页面加载时获取CMG型号
  fetchCmgModels();
});

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart);
  if (myChart) {
    myChart.dispose();
  }
});
</script>

<style scoped>
.detection-overview-page {
  /* 父容器cmg-main已经计算好高度，我们只需继承即可 */
  height: 100%;
  width: 100%;
  /* 移除padding，由父容器cmg-main控制 */
  padding: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.operation-steps {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.steps-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.step-item {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.steps-content .el-icon {
  color: #909399;
  font-size: 14px;
}

.page-main-content {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 20px;
  width: 100%;
}

.left-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1; /* 分配1个单位的宽度 */
  min-width: 400px; /* 增加一个最小宽度防止过度压缩 */
}

.right-panel {
  flex: 2; /* 分配2个单位的宽度 */
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: 16px; /* 添加卡片间距 */
}

.main-container {
  display: flex;
  flex-direction: column;
  gap: 15px; /* 减小卡片间距 */
  height: 100%;
  flex: 1; /* 新增：让主容器填满页面剩余空间 */
  min-height: 0; /* 新增：flex布局关键属性 */
}

.top-left-container {
  width: 100%;
  flex: 2; /* 调整高度比例为2 */
  min-height: 0;
}
  
.anomaly-results-container {
  width: 100%;
  flex: 3; /* 调整高度比例为3 */
  min-height: 0;
}

.box-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-card__body) {
  flex-grow: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 12px; /* 减小内边距 */
}

.actions-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px; /* 减小下边距 */
}

.mode-selection {
  flex: 1; /* 模式选择和CMG选择等宽 */
  min-width: 0; /* 允许收缩 */
}

.cmg-selection {
  flex: 1; /* 模式选择和CMG选择等宽 */
  min-width: 0; /* 允许收缩 */
}

:deep(.el-card__header) {
  padding: 12px 20px;
}

.cmg-instances-container {
  margin-top: 5px; /* 减小上边距 */
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 关键，让内部的滚动生效 */
}

:deep(.el-divider--horizontal) {
  margin: 10px 0; /* 减小分割线边距 */
}

.instances-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px; /* 减小网格间距 */
  margin-top: 5px; /* 减小上边距 */
  overflow-y: auto; /* 当内容超出时显示滚动条 */
}

.cmg-instance-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px; /* 减小内边距 */
  border: 1px solid rgba(255, 255, 255, 0.3); /* 半透明白色边框 */
  border-radius: 6px; /* 减小圆角 */
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #fff; /* 默认背景色，会被动态样式覆盖 */
  color: white; /* 默认文字颜色为白色 */
  font-weight: 500; /* 增加字体粗细以提高可读性 */
}

.cmg-instance-item:hover {
  border-color: #409eff;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.cmg-instance-item.selected {
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.8), 0 4px 12px rgba(0, 0, 0, 0.2);
  transform: scale(1.05);
  border-color: rgba(64, 158, 255, 0.8);
}

.cmg-instance-icon {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.cmg-instance-item .cmg-id {
  margin-top: 6px; /* 减小上边距 */
  font-size: 13px; /* 减小字体 */
  color: white; /* 确保文字为白色 */
  font-weight: 600; /* 增加字体粗细 */
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3); /* 添加文字阴影提高可读性 */
}

.cmg-instance-item .health-score {
  margin-top: 4px;
  font-size: 11px;
  color: white;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  background-color: rgba(0, 0, 0, 0.2); /* 半透明黑色背景 */
  padding: 2px 6px;
  border-radius: 3px;
}

.placeholder-text {
  text-align: center;
  padding: 20px;
  color: #c0c4cc;
  flex-grow: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.placeholder-content span {
  color: #909399;
  font-size: 14px;
}

.time-picker-container {
  padding: 20px 0;
}

.cmg-info {
  margin-bottom: 20px;
}

.timeline-container {
  margin-top: 20px;
  padding: 0;
}

.timeline-header {
  margin-bottom: 20px;
  padding: 0;
}

.timeline-header h4 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.timeline-header h4::before {
  content: "📅";
  font-size: 18px;
}

.timeline-header p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.timeline-slider {
  margin: 20px 0;
  padding: 0 10px;
}

/* 时间轴滑块样式优化 */
.timeline-slider :deep(.el-slider__runway) {
  background: #e4e7ed;
  height: 6px;
  border-radius: 3px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.timeline-slider :deep(.el-slider__bar) {
  background: #909399;
  height: 6px;
  border-radius: 3px;
  box-shadow: 0 2px 4px rgba(144, 147, 153, 0.3);
}

.timeline-slider :deep(.el-slider__button) {
  width: 20px;
  height: 20px;
  border: 3px solid #909399;
  background: #ffffff;
  box-shadow: 0 2px 8px rgba(144, 147, 153, 0.4);
  transition: all 0.3s ease;
}

.timeline-slider :deep(.el-slider__button:hover) {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(144, 147, 153, 0.6);
}

.timeline-slider :deep(.el-slider__button-wrapper) {
  top: -7px;
}

/* 时间轴标记样式 */
.timeline-slider :deep(.el-slider__marks-text) {
  color: #606266;
  font-size: 12px;
  font-weight: 500;
  margin-top: 8px;
}

.selected-time-info {
  margin-top: 20px;
  padding: 0;
}

.selected-time-info :deep(.el-descriptions__label) {
  font-weight: 600;
  color: #2c3e50;
}

.selected-time-info :deep(.el-descriptions__content) {
  color: #409eff;
  font-weight: 500;
}

.fallback-time-picker {
  margin-top: 20px;
}

/* 异常检测结果样式 */
.frequency-stats {
  margin-bottom: 8px; /* 进一步减小下边距 */
  display: flex;
  gap: 10px;
}

.stat-item {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 6px;
  background-color: #f9fafc;
  border-radius: 4px;
}

.stat-label {
  font-size: 12px;
  color: #606266;
}

.stat-value {
  font-size: 14px;
  font-weight: bold;
}

.stat-value.low-anomaly {
  color: #67c23a;
}
.stat-value.medium-anomaly {
  color: #e6a23c;
}
.stat-value.high-anomaly {
  color: #f56c6c;
}

.anomaly-frames-container {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.frames-list {
  flex-grow: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 5px; /* 进一步减小列表项间距 */
  padding-right: 10px; /* for scrollbar */
}

.frame-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.frame-item:hover {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.timestamp {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  color: #303133;
  font-size: 13px;
  font-weight: 500;
  flex-shrink: 0;
}

.abnormal-params-section {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.param-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.abnormal-params {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.param-tag {
  font-size: 11px !important;
  padding: 0 4px !important;
  height: 20px !important;
  line-height: 20px !important;
}

.score-section {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.score-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.score {
  font-weight: bold;
}

/* 重构详情对话框样式 */
.detail-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding-right: 15px; /* 为滚动条留出空间 */
}

/* 主布局：左右布局 */
.main-layout-section {
  display: flex;
  gap: 15px;
  align-items: stretch;
}

/* 左侧模块区域：IMS + 规则 + MSFG 垂直堆叠 */
.left-modules-section {
  flex: 0 0 45%; /* 左侧占45%宽度 */
  display: flex;
  flex-direction: column;
  gap: 15px;
}

/* 右侧遥测数据区域：高度自动等于左侧 */
.right-telemetry-section {
  flex: 0 0 53%; /* 右侧占53%宽度 */
  display: flex;
  flex-direction: column;
}

/* 遥测数据卡片：高度填充整个右侧区域 */
.telemetry-full-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.telemetry-full-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 遥测内容容器 */
.telemetry-inline-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 10px;
}

/* 遥测图表可滚动区域 */
.telemetry-charts-scrollable {
  flex: 1;
  min-height: 0; /* 关键：允许flex子元素缩小 */
  overflow: hidden;
}

.telemetry-charts-scrollable :deep(.el-scrollbar) {
  height: 100%;
}

.telemetry-charts-scrollable :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

.upper-details-section .detail-card {
  flex: 1;
  min-width: 0;
}

.msfg-content {
  display: flex;
  gap: 15px;
}

.msfg-left {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.msfg-right {
  flex: 2;
}

.msfg-top3-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
}

.msfg-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 8px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.msfg-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.msfg-item.active {
  border-color: #409eff;
  background-color: #ecf5ff;
}

.msfg-rank {
  font-weight: bold;
}

/* 重构MSFG区域样式 */
.msfg-summary-content {
  display: flex;
  flex-direction: column;
}

.msfg-top3-horizontal {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  flex-wrap: wrap;
}

.msfg-item-horizontal {
  flex: 1;
  min-width: 200px;
  transition: all 0.3s;
}

.msfg-item-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
  transition: all 0.3s;
}


.msfg-rank {
  background-color: #409eff;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 8px;
}

.msfg-component {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
  text-align: center;
  line-height: 1.4;
}

.msfg-score-tag {
  font-weight: bold;
}

.msfg-no-data {
  text-align: center;
  color: #999;
  padding: 20px;
  width: 100%;
}

/* 遥测数据对话框样式 */
.telemetry-controls {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 15px;
}

/* 内联遥测数据控制面板样式 */
.telemetry-controls-inline {
  background: #f5f7fa;
  padding: 10px 12px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  flex-shrink: 0; /* 防止控制面板被压缩 */
}

.control-row-inline {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.control-item-inline {
  display: flex;
  align-items: center;
  gap: 6px;
}

.control-item-inline label {
  font-weight: 500;
  color: #606266;
  font-size: 13px;
  white-space: nowrap;
}

.telemetry-charts-inline {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 5px;
}

.no-telemetry-data {
  padding: 20px;
  text-align: center;
}

.telemetry-chart-item-inline {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
  background: white;
}

.chart-header-inline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #fafbfc;
  border-bottom: 1px solid #e4e7ed;
}

.chart-title-inline {
  font-weight: 600;
  color: #303133;
  font-size: 13px;
}

.chart-container-inline {
  width: 100%;
  height: 180px; /* 较小的图表高度 */
  padding: 5px;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-item label {
  font-weight: 500;
  color: #606266;
  white-space: nowrap;
}

.telemetry-plots-container {
  padding: 10px;
}

.loading-container,
.no-data-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #999;
  gap: 10px;
}

.telemetry-chart-item {
  margin-bottom: 20px; /* 减少图表项之间的间距 */
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px; /* 进一步减少头部内边距 */
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.chart-title {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

/* 遥测数据图表的容器样式 */
.telemetry-chart-item .chart-container {
  width: 100%;
  height: 100%;
  min-height: 250px; /* 减小高度以便显示更多图表 */
  max-height: 280px; /* 限制最大高度 */
}

/* 优化图表在较小高度下的显示 */
.telemetry-chart-item .chart-container :deep(.echarts) {
  font-size: 12px; /* 减小字体大小以适应较小高度 */
}

/* 图表标题样式优化 */
.chart-title {
  font-weight: 600;
  color: #303133;
  font-size: 13px; /* 稍微减小标题字体 */
}

/* 新增：对话框内部样式 */
.detail-dialog-content {
  max-height: 70vh;
}

.detail-card {
  margin-bottom: 15px;
}

:deep(.detail-card .el-card__header) {
  padding: 10px 15px;
  font-weight: bold;
  background-color: #fafafa;
}

:deep(.detail-card .el-card__body) {
  padding: 15px;
}

.ims-details-content .el-descriptions__label {
  font-weight: bold;
}

.msfg-inference-details .el-descriptions__label {
  font-weight: bold;
}

/* 滚动条美化 */
.frames-list::-webkit-scrollbar {
  width: 6px;
}
.frames-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}
.frames-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}
.frames-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.large-display-card .el-card__body {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 部件推理结果卡片样式 */
.component-inference-card {
  flex: 0 0 50%; /* 占50%高度 */
}

.component-inference-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 寿命预测卡片样式 */
.lifetime-prediction-card {
  flex: 0 0 48%; /* 占48%高度 */
}

.lifetime-prediction-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 增强的CMG装配视图 */
.enhanced-cmg-assembly-view {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  position: relative;
}

/* 左右部件组容器 */
.sub-components {
  display: flex;
  flex-direction: column;
  justify-content: flex-start; /* 改为从顶部开始对齐 */
  align-items: center;
  flex: 1; /* 让左右两侧平均分配空间 */
  max-width: 40%; /* 减少最大宽度，为中间CMG留出更多空间 */
  padding-top: 10px; /* 添加顶部内边距，避免紧贴边缘 */
}

.sub-components.scrollable {
  overflow-y: auto;
  max-height: 100%;
}

/* 设置滚动条为透明 */
.sub-components.scrollable::-webkit-scrollbar {
  width: 6px;
}

.sub-components.scrollable::-webkit-scrollbar-track {
  background: transparent;
}

.sub-components.scrollable::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.sub-components.scrollable::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.2);
}

/* 确保部件框能够更好地填充垂直空间 */
.sub-components .enhanced-component-box {
  flex-shrink: 0; /* 防止部件框被压缩 */
  margin-bottom: 2px; /* 添加小间距 */
}

/* 增强的部件框 */
.enhanced-component-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: white;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.enhanced-component-box:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  border-color: #409eff;
}

.component-icon {
  position: absolute;
  top: 8px;
  right: 8px;
  color: #909399;
  font-size: 14px;
}

.component-status-indicator {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 2px solid white;
}

.status-healthy {
  background-color: #67c23a;
}

.status-warning {
  background-color: #e6a23c;
}

.status-danger {
  background-color: #f56c6c;
}

/* CMG主体增强样式 */
.cmg-main-unit {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 2;
  flex: 0 0 auto; /* 不伸缩，保持固定尺寸 */
  min-width: 180px; /* 增加最小宽度 */
  max-width: 250px; /* 增加最大宽度 */
}

.cmg-image-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.cmg-overlay {
  position: absolute;
  bottom: -30px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  text-align: center;
  min-width: 120px;
}

.cmg-name {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 4px;
}

.cmg-connection-lines {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  z-index: 1;
}

.connection-line {
  position: absolute;
  top: 0;
  height: 2px;
  background: linear-gradient(90deg, #409eff, #67c23a);
  border-radius: 1px;
}

.connection-line.left {
  left: 0;
  width: 30%;
}

.connection-line.right {
  right: 0;
  width: 30%;
}

/* 增强的部件框 */
.enhanced-component-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: white;
  border: 2px solid #e4e7ed;
  border-radius: 8px; /* 减小圆角 */
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  min-width: 100px; /* 设置最小宽度 */
  min-height: 80px; /* 设置最小高度 */
}

.enhanced-component-box:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  border-color: #409eff;
}

.component-icon {
  position: absolute;
  top: 6px; /* 调整位置 */
  right: 6px; /* 调整位置 */
  color: #909399;
  font-size: 12px; /* 减小图标大小 */
}

.component-status-indicator {
  position: absolute;
  top: 3px; /* 调整位置 */
  left: 3px; /* 调整位置 */
  width: 6px; /* 减小尺寸 */
  height: 6px; /* 减小尺寸 */
  border-radius: 50%;
  border: 1px solid white; /* 减小边框 */
}

.status-healthy {
  background-color: #67c23a;
}

.status-warning {
  background-color: #e6a23c;
}

.status-danger {
  background-color: #f56c6c;
}

/* CMG主体增强样式 */
.cmg-main-unit {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 2;
}

.cmg-image-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.cmg-overlay {
  position: absolute;
  bottom: -25px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 6px 10px; /* 减小内边距 */
  border-radius: 4px;
  text-align: center;
  min-width: 80px; /* 减小最小宽度 */
  font-size: 12px; /* 减小字体 */
}

.cmg-name {
  font-size: 11px; /* 减小字体 */
  font-weight: 600;
  margin-bottom: 2px; /* 减小间距 */
}

.cmg-connection-lines {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  z-index: 1;
}

.connection-line {
  position: absolute;
  top: 0;
  height: 2px;
  background: linear-gradient(90deg, #409eff, #67c23a);
  border-radius: 1px;
}

.connection-line.left {
  left: 0;
  width: 20%; /* 缩短连接线 */
}

.connection-line.right {
  right: 0;
  width: 20%; /* 缩短连接线 */
}

/* 寿命预测布局 */
.lifetime-prediction-layout {
  display: flex;
  height: 100%;
  gap: 20px;
}

.lifetime-params-section {
  flex: 0 0 35%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.params-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.params-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.current-params {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.param-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.param-item label {
  font-weight: 500;
  color: #606266;
  font-size: 13px;
}

.param-value {
  font-weight: 600;
  color: #303133;
  font-size: 13px;
}

.lifetime-result {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #0ea5e9;
  border-radius: 8px;
  padding: 12px; /* 减小内边距 */
  text-align: center;
}

.result-header {
  font-size: 14px;
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 8px; /* 减小底部间距 */
}

.result-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px; /* 减小间距 */
}

.remaining-life-display {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.life-value {
  font-size: 24px;
  font-weight: 700;
  color: #0369a1;
}

.life-unit {
  font-size: 14px;
  color: #0369a1;
  font-weight: 500;
}

.life-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.life-healthy {
  background-color: #dcfce7;
  color: #166534;
}

.life-warning {
  background-color: #fef3c7;
  color: #92400e;
}

.life-danger {
  background-color: #fecaca;
  color: #991b1b;
}

.life-critical {
  background-color: #fca5a5;
  color: #7f1d1d;
}

.lifetime-chart-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 16px;
}

.chart-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.chart-container-wrapper {
  flex: 1;
  position: relative;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 200px;
}

.chart-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  z-index: 10;
  border-radius: 4px;
}

.chart-loading-overlay span {
  color: #409eff;
  font-size: 14px;
  font-weight: 500;
}

.life-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.life-healthy {
  background-color: #dcfce7;
  color: #166534;
}

.life-warning {
  background-color: #fef3c7;
  color: #92400e;
}

.life-danger {
  background-color: #fecaca;
  color: #991b1b;
}

.life-critical {
  background-color: #fca5a5;
  color: #7f1d1d;
}

.lifetime-chart-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 16px;
}

.chart-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.chart-container-wrapper {
  flex: 1;
  position: relative;
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 200px;
}

.chart-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  z-index: 10;
  border-radius: 4px;
}

.chart-loading-overlay span {
  color: #409eff;
  font-size: 14px;
  font-weight: 500;
}

.large-display-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  /* 确保这个flex容器能正确分配高度 */
  min-height: 0; 
}

.cmg-assembly-view {
  display: flex;
  justify-content: center; /* 改为居中对齐，减少中间留白 */
  align-items: center;
  padding: 3px 8px; /* 进一步减小内边距 */
  flex-shrink: 0; /* 防止此区域被压缩 */
  gap: 75px; /* 调整间距，让布局更加紧凑 */
}

.sub-components {
  display: flex;
  flex-direction: column;
  /* gap 现在通过动态样式设置 */
}

/* 可滚动部件容器样式 */
.sub-components.scrollable {
  max-height: 300px; /* 设置最大高度 */
  overflow-y: auto; /* 垂直滚动 */
  overflow-x: hidden; /* 隐藏水平滚动 */
  padding-right: 8px; /* 为滚动条留出空间 */
}

/* 滚动条美化 */
.sub-components.scrollable::-webkit-scrollbar {
  width: 6px;
}

.sub-components.scrollable::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.sub-components.scrollable::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.sub-components.scrollable::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.component-box {
  /* width 和 padding 现在通过动态样式设置 */
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.component-box:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.component-name {
  /* font-size 现在通过动态样式设置 */
  margin-bottom: 4px; /* 减少部件名称下方的间距 */
}

.component-health {
  padding: 3px; /* 减少健康分数区域的内边距 */
  color: white;
  border-radius: 4px;
  font-weight: bold;
}

.cmg-main-unit {
  text-align: center;
}

.cmg-image {
  width: 160px; /* 减小图片宽度 */
  height: auto;
}

.remaining-life {
  margin-top: 5px; /* 进一步减小上方外边距 */
  padding: 6px; /* 减小内边距 */
  background-color: #f4f4f5;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.health-trend-chart {
  flex: 1; 
  display: flex;
  flex-direction: column;
  min-height: 0;
  margin-top: 10px; /* 减少上边距 */
}

.health-trend-chart :deep(.el-divider) {
  margin: 5px 0; /* 减少分割线的上下边距 */
}

.right-panel .chart-container {
  flex: 1;
  width: 100%;
  height: 100%; /* 添加height 100% 确保ECharts有渲染目标 */
}

/* 页面状态样式 */
.no-selection-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}

.loading-content {
  text-align: center;
  color: #409eff;
}

.loading-content p {
  margin-top: 15px;
  font-size: 16px;
  color: #606266;
}

.chart-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #c0c4cc;
  font-size: 20px;
  background-color: #fafafa;
  border-radius: 4px;
  margin: 0 10px 10px;
}

.detail-dialog-header-toolbar {
  margin-bottom: 15px;
}

.telemetry-plots-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-right: 15px; /* 为滚动条留出空间 */
}

.telemetry-plot-item {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: hidden;
}

.plot-header {
  padding: 10px 15px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  font-weight: 500;
  font-size: 14px;
}

.plot-placeholder {
  height: 220px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #909399;
  font-size: 16px;
  gap: 10px;
}

.custom-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.custom-dialog-header .header-timestamp {
  color: #409eff;
  font-weight: 600;
  margin-left: 8px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* 部件详情对话框样式 */
.component-detail-dialog .el-dialog__body {
  padding: 20px;
  max-height: 80vh;
  overflow-y: auto;
}

.component-detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.component-detail-content .info-card {
  margin-bottom: 0;
}

.component-detail-content .info-card .el-card__header {
  padding: 12px 16px;
  font-weight: bold;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
}

.component-detail-content .info-card .el-card__body {
  padding: 16px;
}

.component-detail-content .el-descriptions {
  margin-bottom: 0;
}

.component-detail-content .el-table {
  margin-bottom: 0;
}

.component-detail-content .el-divider {
  margin: 15px 0 10px 0;
}

/* 饼状图容器样式 */
.pie-chart-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.component-info-header {
  text-align: center;
  margin-bottom: 20px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.component-info-header h3 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 20px;
  font-weight: 600;
}

.component-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.score-count {
  color: #606266;
  font-size: 14px;
}

.pie-charts-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.pie-chart-wrapper {
  width: 100%;
}

.pie-chart-title {
  text-align: center;
  margin-bottom: 16px;
}

.pie-chart-title h4 {
  margin: 0 0 8px 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
}

.chart-description {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #909399;
  font-size: 12px;
}

.pie-chart {
  min-height: 400px;
  width: 100%;
}

.detail-tables {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table-section {
  margin-bottom: 20px;
}

.table-section:last-child {
  margin-bottom: 0;
}

.table-section h4 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-section h4::before {
  content: "📊";
  font-size: 16px;
}

/* 圆形布局样式 */
.circular-layout-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.layout-header {
  margin-bottom: 25px;
  text-align: center;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.layout-header h3 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.layout-info {
  display: flex;
  justify-content: center;
  gap: 25px;
  color: #606266;
  font-size: 14px;
  flex-wrap: wrap;
}

.layout-info span {
  background: #f8f9fa;
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid #e9ecef;
  font-weight: 500;
}

.circular-layout {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: white;
  border-radius: 16px;
  margin-bottom: 25px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border: 1px solid #e9ecef;
}

.circular-svg {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 16px;
}

.connection-line {
  opacity: 0.7;
  transition: all 0.3s ease;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}

.connection-line:hover {
  opacity: 1;
  stroke-width: 3;
}

.node-group {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.node-group:hover {
  transform: scale(1.1);
}

.node-circle {
  transition: all 0.3s ease;
}

.node-square {
  transition: all 0.3s ease;
}

.node-group:hover .node-circle,
.node-group:hover .node-square {
  stroke-width: 3;
}

.node-label {
  font-weight: 600;
  fill: #2c3e50;
  text-anchor: middle;
  dominant-baseline: middle;
  font-size: 11px;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

.node-score {
  font-weight: bold;
  text-anchor: middle;
  dominant-baseline: middle;
  font-size: 10px;
  fill: #000000;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

.center-circle {
  transition: transform 0.2s ease;
}

.center-component:hover .center-circle {
  transform: scale(1.05);
}

.center-label {
  fill: #2c3e50;
  text-anchor: middle;
  dominant-baseline: middle;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(255, 255, 255, 0.8);
}

.center-score {
  text-anchor: middle;
  dominant-baseline: middle;
  font-weight: 800;
  fill: #000000;
  text-shadow: 0 2px 4px rgba(255, 255, 255, 0.8);
}

.center-info {
  text-anchor: middle;
  dominant-baseline: middle;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

.legend {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 30px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  flex-wrap: wrap;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #2c3e50;
  font-weight: 500;
  background: #f8f9fa;
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid #e9ecef;
}

.legend-shape {
  width: 16px;
  height: 16px;
  border: 2px solid #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.legend-line {
  width: 20px;
  height: 3px;
  border-radius: 2px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.testpoint-line {
  background: #409eff; /* 蓝色实线 */
}

.fault-line {
  background: #f56c6c; /* 红色虚线 */
  background-image: repeating-linear-gradient(
    90deg,
    #f56c6c,
    #f56c6c 3px,
    transparent 3px,
    transparent 6px
  );
}

.component-shape {
  background: #67c23a;
  border-radius: 50%; /* 圆形 */
}

.legend-score-range {
  font-size: 12px;
  color: #909399;
  font-style: italic;
}

/* 算法选择样式 */
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

/* 寿命信息显示样式 */
.lifetime-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.lifetime-value {
  font-size: 14px;
}

.algorithm-info {
  font-size: 12px;
  color: #606266;
  font-style: italic;
}

/* 寿命预测加载状态样式 */
.lifetime-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
  font-size: 14px;
}

.lifetime-loading .loading-icon {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>

