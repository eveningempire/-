<template>
  <div class="big-screen-container">
    <!-- 宇宙背景 -->
    <div class="universe-background">
      <div class="stars-field"></div>
      <div class="nebula-overlay"></div>
      <div class="grid-overlay"></div>
    </div>

    <!-- 顶部标题栏 -->
    <div class="top-header">
      <div class="header-left">
        <h1 class="system-title">
          <span class="title-icon">🛰️</span>
          基于模型的寿命预测系统
        </h1>
      </div>
      <div class="header-right">
        <div class="time-display">
          <span class="time-label">系统当前时间：</span>
          <span class="current-time">{{ currentTime }}</span>
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧面板 -->
      <div class="left-panel">
        <!-- 型号个体选择 -->
        <div class="model-selection-panel">
          <div class="panel-header">
            <h3>CMG型号个体选择</h3>
            <div class="panel-indicator">
              <span class="indicator-dot"></span>
            </div>
          </div>
          <div class="panel-content">
            <!-- 加载状态 -->
            <div v-if="isLoadingModels" class="loading-state">
              <div class="loading-spinner"></div>
              <p>正在加载型号...</p>
            </div>
            
            <!-- 型号列表 -->
            <div v-else class="model-tree">
              <div 
                v-for="model in cmgModels" 
                :key="model.value"
                class="model-item"
              >
                <!-- 型号标题 - 可点击展开/收起 -->
                <div 
                  class="model-header"
                  @click="toggleModel(model.value)"
                >
                  <span class="expand-icon" :class="{ 'expanded': expandedModels[model.value] }">
                    ▶
                  </span>
                  <span class="model-name">
                    <span class="label-prefix">星体名称：</span>{{ model.label }}
                  </span>
                  <span class="instance-count">
                    {{ getModelInstanceCount(model.value) }}
                  </span>
                </div>
                
                <!-- 个体列表 - 展开时显示 -->
                <div 
                  v-if="expandedModels[model.value]" 
                  class="instances-list"
                >
                  <!-- 加载中 -->
                  <div v-if="loadingModels[model.value]" class="loading-instances">
                    <div class="loading-spinner-small"></div>
                    <span>加载中...</span>
                  </div>
                  
                  <!-- 个体列表 -->
                  <div 
                    v-else
                    v-for="cmg in modelInstances[model.value] || []" 
                    :key="cmg.id"
                    class="instance-item"
                    :class="{ 'selected': selectedCmgId === cmg.id }"
                    :style="{ borderLeftColor: getCmgHealthColor(cmg.health_score) }"
                    @click.stop="selectCmg(cmg.id)"
                  >
                    <div class="instance-info">
                      <span class="instance-id">
                        <span class="label-prefix">CMG个体名称：</span>{{ cmg.cmg_id }}
                      </span>
                      <span 
                        v-if="cmg.health_score !== null && cmg.health_score !== undefined" 
                        class="instance-health"
                        :style="{ color: getCmgHealthColor(cmg.health_score) }"
                      >
                        <span class="health-label">健康状态：</span>{{ cmg.health_score.toFixed(3) }}
                      </span>
                      <span v-else class="instance-health no-data">
                        <span class="health-label">健康状态：</span>无数据
                      </span>
                    </div>
                  </div>
                  
                  <!-- 空状态 -->
                  <div v-if="!loadingModels[model.value] && (!modelInstances[model.value] || modelInstances[model.value].length === 0)" class="empty-instances">
                    暂无个体数据
                  </div>
                </div>
              </div>
              
              <!-- 空状态 -->
              <div v-if="cmgModels.length === 0" class="empty-models">
                <el-empty description="暂无型号数据" :image-size="60" />
              </div>
            </div>
          </div>
        </div>

        <!-- 异常检测结果 -->
        <div class="anomaly-results-panel">
          <div class="panel-header">
            <h3>CMG异常检测结果</h3>
            <div class="panel-indicator">
              <span class="indicator-dot"></span>
            </div>
          </div>
          <div class="panel-content">
            <!-- 未选择状态 -->
            <div v-if="!hasSelectedCmgAndTime" class="no-selection-state">
              <el-empty description="请选择CMG个体和时间段" :image-size="80" />
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
              <!-- 异常比例统计 -->
              <div class="anomaly-stats">
                <div class="stat-item">
                  <span class="stat-label">异常比例</span>
                  <span class="stat-value" :class="getAnomalyRatioClass(anomalyRatio)">
                    {{ (anomalyRatio * 100).toFixed(2) }}%
                  </span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">总帧数</span>
                  <span class="stat-value">{{ totalFrames }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">异常帧数</span>
                  <span class="stat-value">{{ anomalyCount }}</span>
                </div>
              </div>
              
              <!-- 异常帧列表 -->
              <div class="anomaly-frames-list">
                <div class="frames-header">
                  <span>异常帧详情</span>
                  <span class="frames-count">{{ anomalyFrames.length }} 条</span>
                </div>
                <div class="frames-container">
                  <div 
                    v-for="frame in anomalyFrames.slice(0, 15)" 
                    :key="frame.id"
                    class="frame-item"
                    @click="selectAnomalyFrame(frame)"
                  >
                    <div class="frame-time">{{ formatTimestamp(frame.timestamp) }}</div>
                    <div class="frame-score" :class="getScoreClass(frame.score)">
                      <span class="score-label">异常分数：</span>{{ frame.score.toFixed(4) }}
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- 中央3D展示区 -->
      <div class="center-panel">
        <div class="earth-container" ref="earthContainer">
          <!-- Three.js 3D场景将在这里渲染 -->
          <div class="loading-overlay" v-if="isLoading">
            <div class="loading-spinner"></div>
            <span>正在加载3D场景...</span>
          </div>
        </div>
        
        <!-- 场景控制按钮 -->
        <div class="scene-controls">
          <button class="control-btn" @click="toggleFullscreen">
            <span class="btn-icon">{{ isFullscreen ? '🔲' : '⛶' }}</span>
            {{ isFullscreen ? '退出全屏' : '全屏显示' }}
          </button>
          <button class="control-btn" @click="toggleAnimation">
            <span class="btn-icon">{{ isAnimating ? '⏸️' : '▶️' }}</span>
            {{ isAnimating ? '暂停' : '播放' }}
          </button>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="right-panel">
        <!-- CMG故障信号流图建模&推理 -->
        <div class="msfg-inference-panel">
          <div class="panel-header">
            <h3>CMG故障信号流图建模&推理</h3>
            <div class="panel-indicator">
              <span class="indicator-dot"></span>
            </div>
          </div>
          <div class="panel-content">
            <!-- 未选择状态 -->
            <div v-if="!hasSelectedCmgAndTime" class="no-selection-state">
              <el-empty description="请选择CMG个体和时间段" :image-size="80" />
            </div>
            
            <!-- 加载状态 -->
            <div v-else-if="isDataLoading" class="loading-state">
              <div class="loading-content">
                <el-icon class="is-loading" size="30" color="#409eff"><Loading /></el-icon>
                <p>正在加载MSFG推理结果...</p>
              </div>
            </div>
            
            <!-- 已选择状态：显示子部件健康分数 -->
            <template v-else>
              <div class="msfg-components-container">
                <div 
                  v-for="comp in componentScores" 
                  :key="comp.id"
                  class="component-box"
                  :style="{ backgroundColor: getHealthColorWithAlpha(comp.healthScore) }"
                  @click="showInferenceDialog(comp)"
                >
                  <div class="component-name">{{ comp.name }}</div>
                  <div class="component-score" :style="{ color: getHealthColor(comp.healthScore) }">
                    {{ comp.healthScore.toFixed(2) }}
                  </div>
                </div>
                
                <!-- 无数据提示 -->
                <div v-if="componentScores.length === 0" class="no-data-hint">
                  <el-empty description="暂无部件数据" :image-size="60" />
                </div>
              </div>
            </template>
          </div>
        </div>

          <!-- 寿命预测与更新 -->
          <div class="lifetime-update-panel">
            <div class="panel-header">
              <h3>CMG寿命预测&自扩展动态更新</h3>
              <div class="panel-indicator">
                <span class="indicator-dot"></span>
              </div>
            </div>
            <div class="panel-content">
              <!-- 未选择状态 -->
              <div v-if="!hasSelectedCmgAndTime" class="no-selection-state">
                <el-empty description="请先选择CMG个体和时间段" :image-size="60">
                  <template #image>
                    <el-icon size="60" color="#c0c4cc"><Timer /></el-icon>
                  </template>
                </el-empty>
              </div>
              
              <!-- 已选择状态：显示寿命预测 -->
              <div v-else class="lifetime-prediction-layout">
                <!-- 上部：参数设置和预测结果 -->
                <div class="lifetime-top-section">
                  <!-- 左侧：参数设置 -->
                  <div class="lifetime-params-section">
                    <div class="params-header">
                      <h4>预测参数</h4>
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
                        <span class="param-value">{{ lifetimeSettings.startUseTime || '数据开始时间' }}</span>
                      </div>
                      <div class="param-item">
                        <label>预测算法:</label>
                        <span class="param-value">{{ currentAlgorithmInfo?.name || '默认算法' }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 右侧：预测结果 -->
                  <div class="lifetime-result-section">
                    <div v-if="lifetimePredicting" class="loading-state">
                      <el-icon class="is-loading" size="24"><Loading /></el-icon>
                      <span>正在预测...</span>
                    </div>
                    
                    <div v-else-if="remainingLife !== null" class="lifetime-result">
                      <div class="result-header">
                        <h4>剩余寿命</h4>
                      </div>
                      <div class="result-value">
                        <span class="life-years">{{ remainingLife.toFixed(2) }}</span>
                        <span class="life-unit">年</span>
                      </div>
                    </div>
                    
                    <div v-else class="no-result-state">
                      <el-icon size="40" color="#c0c4cc"><Warning /></el-icon>
                      <span>暂无预测结果</span>
                      <small>请检查参数设置</small>
                    </div>
                  </div>
                </div>
                
                <!-- 下部：健康趋势图 -->
                <div class="lifetime-chart-section">
                  <div v-if="lifetimePredicting" class="chart-loading">
                    <el-icon class="is-loading" size="20"><Loading /></el-icon>
                    <span>加载趋势图...</span>
                  </div>
                  
                  <!-- 图表容器始终存在，这样可以正确初始化 -->
                  <div v-else class="chart-container">
                    <div ref="lifetimeChartRef" class="lifetime-trend-chart"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
      </div>
    </div>

    <!-- 底部管理功能区域 -->
    <div class="bottom-management-area">
      <!-- 数据&系统管理 -->
      <div class="management-panel">
        <div class="panel-header">
          <h3>数据&系统管理</h3>
          <div class="panel-indicator">
            <span class="indicator-dot"></span>
          </div>
        </div>
        <div class="management-grid">
          <div class="management-item" @click="openPage('/data-import')">
            <el-icon size="24"><Upload /></el-icon>
            <span>数据文件导入</span>
          </div>
          <div class="management-item" @click="openPage('/data-records')">
            <el-icon size="24"><Search /></el-icon>
            <span>数据查询分析</span>
          </div>
          <div class="management-item" @click="openPage('/model-management')">
            <el-icon size="24"><Setting /></el-icon>
            <span>型号/个体管理</span>
          </div>
          <div class="management-item" @click="openPage('/system-status')">
            <el-icon size="24"><Monitor /></el-icon>
            <span>系统状态</span>
          </div>
          <div class="management-item" @click="openPage('/user-management')">
            <el-icon size="24"><User /></el-icon>
            <span>用户管理</span>
          </div>
        </div>
      </div>

      <!-- 检测配置 -->
      <div class="management-panel">
        <div class="panel-header">
          <h3>模型配置</h3>
          <div class="panel-indicator">
            <span class="indicator-dot"></span>
          </div>
        </div>
        <div class="management-grid">
          <div class="management-item" @click="openPage('/ims-management')">
            <el-icon size="24"><DataAnalysis /></el-icon>
            <span>CMG异常检测模型管理</span>
          </div>
          <div class="management-item" @click="openPage('/rule-editor')">
            <el-icon size="24"><EditPen /></el-icon>
            <span>CMG专家规则规则编辑</span>
          </div>
          <div class="management-item" @click="openPage('/msfg-editor')">
            <el-icon size="24"><Connection /></el-icon>
            <span>CMG故障信号流图建模</span>
          </div>
          <div class="management-item" @click="openPage('/msfg-testpoint-rules')">
            <el-icon size="24"><Tools /></el-icon>
            <span>CMG流图测点规则配置</span>
          </div>
        </div>
      </div>

      <!-- 寿命预测 -->
      <div class="management-panel">
        <div class="panel-header">
          <h3>寿命预测</h3>
          <div class="panel-indicator">
            <span class="indicator-dot"></span>
          </div>
        </div>
        <div class="management-grid">
          <div class="management-item" @click="openPage('/lifetime-prediction')">
            <el-icon size="24"><TrendCharts /></el-icon>
            <span>CMG寿命预测系统</span>
          </div>
          <div class="management-item" @click="openPage('/model-finetune')">
            <el-icon size="24"><Refresh /></el-icon>
            <span>CMG自扩展动态更新</span>
          </div>
          <div class="management-item" @click="openPage('/modeling-overview')">
            <el-icon size="24"><DataAnalysis /></el-icon>
            <span>CMG寿命预测建模</span>
          </div>
        </div>
      </div>

      <!-- 预研内容 -->
      <div class="management-panel">
        <div class="panel-header">
          <h3>预研内容</h3>
          <div class="panel-indicator">
            <span class="indicator-dot"></span>
          </div>
        </div>
        <div class="management-grid">
          <div class="management-item" @click="openPage('/degradation-simulation')">
            <el-icon size="24"><TrendCharts /></el-icon>
            <span>CMG健康演化模型</span>
          </div>
          <div class="management-item" @click="openPage('/health-assessment')">
            <el-icon size="24"><DataAnalysis /></el-icon>
            <span>CMG特征提取与智能评估</span>
          </div>
          <div class="management-item" @click="openPage('/smart-sensing')">
            <el-icon size="24"><TrendCharts /></el-icon>
            <span>CMG智能感知方法</span>
          </div>
          <div class="management-item" @click="openPage('/undersampling')">
            <el-icon size="24"><DataLine /></el-icon>
            <span>CMG欠采样与有限传感</span>
          </div>
        </div>
      </div>
    </div>

      <!-- 时间选择对话框 -->
      <el-dialog
        v-model="showTimeSelector"
        title="选择时间范围"
        width="700px"
        :close-on-click-modal="false"
        :modal="false"
        class="time-selector-dialog"
      >
        <div v-if="timelineData && timelineData.timeline && timelineData.timeline.length > 0">
          <div class="timeline-info">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="数据范围">
                {{ timelineData.time_range?.start }} ~ {{ timelineData.time_range?.end }}
              </el-descriptions-item>
              <el-descriptions-item label="数据点数量">
                {{ timelineData.timeline.length }}
              </el-descriptions-item>
              <el-descriptions-item label="开始时间">
                {{ getSelectedStartTime() }}
              </el-descriptions-item>
              <el-descriptions-item label="结束时间">
                {{ getSelectedEndTime() }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
          
          <div class="timeline-slider">
            <el-slider
              v-model="timelineRange"
              range
              :min="0"
              :max="timelineData.timeline.length - 1"
              :marks="timelineMarks"
            />
          </div>
        </div>
        
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
        
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showTimeSelector = false">取消</el-button>
            <el-button type="primary" @click="confirmTimeRange">确定</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 异常帧详情对话框 -->
      <el-dialog
        v-model="showAnomalyDetailDialog"
        width="90%"
        top="3vh"
        :modal="false"
        class="detail-dialog bigscreen-detail-dialog"
        :close-on-click-modal="false"
      >
        <template #header="{ close, titleId, titleClass }">
          <div class="custom-dialog-header">
            <h4 :id="titleId" :class="titleClass">
              异常详情: <span class="header-timestamp">{{ formatTimestamp(selectedAnomalyFrame?.timestamp) }}</span>
            </h4>
            <el-button 
              type="warning" 
              size="small" 
              @click="handleManualJudgment"
              :loading="isDeleting"
              class="manual-judgment-btn"
            >
              人工判定
            </el-button>
          </div>
        </template>
        <el-scrollbar max-height="75vh">
          <div class="detail-dialog-content">
            <!-- 左右布局：左侧三个模块堆叠，右侧遥测数据 -->
            <div class="main-layout-section">
              <!-- 左侧：IMS + 规则 + MSFG 垂直堆叠 -->
              <div class="left-modules-section">
                <!-- 异常检测详细结果 -->
                <el-card class="detail-card" shadow="never">
                  <template #header>
                    <div class="card-header">
                      <span>异常检测详细结果</span>
                    </div>
                  </template>
                  <div class="ims-details-content">
                    <el-descriptions :column="2" border size="small">
                      <el-descriptions-item label="异常分数">
                        <el-tag :type="getScoreTagType(selectedAnomalyFrame?.ims?.anomaly_score || selectedAnomalyFrame?.score)">
                          {{ (selectedAnomalyFrame?.ims?.anomaly_score || selectedAnomalyFrame?.score || 0).toFixed(4) }}
                        </el-tag>
                      </el-descriptions-item>
                      <el-descriptions-item label="CMG名称">{{ selectedAnomalyFrame?.cmg_id || selectedCmgId }}</el-descriptions-item>
                      <el-descriptions-item label="IMS模型">{{ selectedAnomalyFrame?.ims?.model_name || '未知' }}</el-descriptions-item>
                      <el-descriptions-item label="异常状态">
                        <el-tag :type="selectedAnomalyFrame?.ims?.is_anomaly ? 'danger' : 'success'">
                          {{ selectedAnomalyFrame?.ims?.is_anomaly ? '异常' : '正常' }}
                        </el-tag>
                      </el-descriptions-item>
                    </el-descriptions>
                    <el-divider content-position="left">遥测量分数</el-divider>
                    <el-table :data="formatParameterScores(selectedAnomalyFrame?.ims?.parameter_scores || {})" border size="small" height="200">
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

                <!-- 专家规则检测结果 -->
                <el-card class="detail-card" shadow="never">
                  <template #header>
                    <div class="card-header">
                      <span>专家规则检测结果</span>
                    </div>
                  </template>
                  <el-table :data="selectedAnomalyFrame?.rules || []" border size="small" max-height="250">
                    <el-table-column prop="name" label="规则名称" min-width="120" />
                    <el-table-column prop="fault_name" label="故障类型" min-width="150" />
                    <el-table-column prop="fault_level" label="故障等级" min-width="80" align="center" />
                    <el-table-column prop="is_triggered" label="是否触发" min-width="80" align="center">
                      <template #default="{ row }">
                        <el-tag :type="row.is_triggered ? 'danger' : 'success'">
                          {{ row.is_triggered ? '是' : '否' }}
                        </el-tag>
                      </template>
                    </el-table-column>
                  </el-table>
                </el-card>
                
                <!-- 故障信号流图推理结果 -->
                <el-card class="detail-card" shadow="never">
                  <template #header>
                    <div class="card-header">
                      <span>故障信号流图推理结果</span>
                    </div>
                  </template>
                  <div class="msfg-summary-content">
                    <!-- 整机分数 + TOP3列表 -->
                    <el-descriptions :column="2" border size="small">
                      <el-descriptions-item label="整机健康分">{{ (selectedAnomalyFrame?.msfg?.overall_health_score || selectedAnomalyFrame?.msfg?.overall_score || 0).toFixed(4) }}</el-descriptions-item>
                      <el-descriptions-item label="风险等级">
                        <el-tag :type="getHealthScoreTagType(selectedAnomalyFrame?.msfg?.overall_health_score || selectedAnomalyFrame?.msfg?.overall_score || 0)">
                          {{ getHealthScoreText(selectedAnomalyFrame?.msfg?.overall_health_score || selectedAnomalyFrame?.msfg?.overall_score || 0) }}
                        </el-tag>
                      </el-descriptions-item>
                    </el-descriptions>
                    <el-divider content-position="left">TOP3 故障部件</el-divider>
                    <div class="msfg-top3-horizontal">
                      <div 
                        v-for="(item, index) in selectedAnomalyFrame?.msfg?.top3 || []" 
                        :key="item.component || index" 
                        class="msfg-item-horizontal"
                      >
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
                      <div v-if="!selectedAnomalyFrame?.msfg?.top3?.length" class="msfg-no-data">
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
                            popper-class="bigscreen-telemetry-select-dropdown"
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
      </el-dialog>

    <!-- 寿命预测参数设置对话框 -->
    <el-dialog
      v-model="showLifetimeSettingsDialog"
      title="设置寿命预测参数"
      width="500px"
      class="lifetime-settings-dialog bigscreen-detail-dialog"
      :before-close="handleLifetimeSettingsClose"
      :close-on-click-modal="!lifetimePredicting"
      :close-on-press-escape="!lifetimePredicting"
    >
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
          <span style="margin-left: 10px; color: #93c5fd;">年</span>
        </el-form-item>
        <el-form-item label="启用时间">
          <el-date-picker
            v-model="lifetimeSettings.startUseTime"
            type="datetime"
            placeholder="选择启用时间"
            format="YYYY/MM/DD HH:mm:ss"
            value-format="YYYY/MM/DD HH:mm:ss"
            popper-class="lifetime-settings-date-picker"
            style="width: 200px">
          </el-date-picker>
        </el-form-item>
        <el-form-item label="预测算法">
          <el-select
            v-model="lifetimeSettings.algorithm"
            placeholder="请选择预测算法"
            popper-class="lifetime-settings-select-dropdown"
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
            确定并预测
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 部件详细信息对话框 -->
    <el-dialog
      v-model="inferenceDialogVisible"
      title=""
      width="47%"
      top="12vh"
      class="component-detail-dialog bigscreen-detail-dialog"
      :close-on-click-modal="false"
      :modal="false"
    >
        <div v-loading="componentDetailLoading" class="component-detail-content">
          <!-- 饼状图可视化 -->
          <div v-if="componentDetailData" class="pie-chart-container">
            
            <!-- 部件基本信息 -->
            <div class="component-info-header">
              <h3>{{ componentDetailData.center_component?.name || '部件详情' }}</h3>
              <el-tag :type="getHealthScoreTagType(componentDetailData.center_component?.average_score || 0)" size="large">
                平均分数: {{ (componentDetailData.center_component?.average_score || 0).toFixed(3) }}
              </el-tag>
              <span class="score-count">
                (基于 {{ componentDetailData.center_component?.score_count || 0 }} 个数据点)
              </span>
            </div>
            
            <!-- 饼状图展示区域 -->
            <div class="pie-charts-section">
              <div class="pie-chart-wrapper">
                <div class="pie-chart-title">
                  <h4>测点与故障分数分布图</h4>
                </div>
                 <div ref="pieChartRef" class="pie-chart" style="width: 100%; height: 350px;"></div>
              </div>
            </div>
            
            <!-- 详细数据表格 -->
            <div class="detail-tables">
              <div class="table-section">
                <h4>测点异常分数</h4>
                <div class="table-wrapper">
                  <el-table 
                    :data="limitedTestpoints" 
                    size="small" 
                    border
                    max-height="150"
                    style="margin-bottom: 16px;"
                  >
                    <el-table-column prop="name" label="测点名称" width="240" />
                    <el-table-column prop="average_score" label="异常分数" width="140" align="center">
                      <template #default="{ row }">
                        <el-tag :type="getScoreTagType(row.average_score)" size="small">
                          {{ (row.average_score || 0).toFixed(3) }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="score_count" label="数据点数" width="120" align="center" />
                    <el-table-column prop="min_score" label="最小值" width="120" align="center">
                      <template #default="{ row }">
                        {{ (row.min_score || 0).toFixed(3) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="max_score" label="最大值" width="120" align="center">
                      <template #default="{ row }">
                        {{ (row.max_score || 0).toFixed(3) }}
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
              
              <div class="table-section">
                <h4>故障异常分数</h4>
                <div class="table-wrapper">
                  <el-table 
                    :data="limitedFaults" 
                    size="small" 
                    border
                    max-height="150"
                  >
                    <el-table-column prop="name" label="故障名称" width="240" />
                    <el-table-column prop="average_score" label="异常分数" width="140" align="center">
                      <template #default="{ row }">
                        <el-tag :type="getScoreTagType(row.average_score)" size="small">
                          {{ (row.average_score || 0).toFixed(3) }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="score_count" label="数据点数" width="120" align="center" />
                    <el-table-column prop="min_score" label="最小值" width="120" align="center">
                      <template #default="{ row }">
                        {{ (row.min_score || 0).toFixed(3) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="max_score" label="最大值" width="120" align="center">
                      <template #default="{ row }">
                        {{ (row.max_score || 0).toFixed(3) }}
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
            </div>
            </div>
          </div>
        </div>
      </el-dialog>

  </div>

  <!-- 3D模型详情弹窗 -->
  <div v-if="show3DModelDialog" class="model-dialog-overlay">
    <div class="model-dialog">
      <div class="model-dialog-header">
        <h3>{{ selected3DModel?.name || '模型详情' }}</h3>
        <button class="close-btn" @click="show3DModelDialog = false">×</button>
      </div>
      <div class="model-dialog-content">
        <div class="model-info">
          <div class="model-type">
            <span class="type-label">类型：</span>
            <span class="type-value" :class="selected3DModel?.type">
              {{ selected3DModel?.type === 'space_station' ? '空间站' : '卫星' }}
            </span>
          </div>
          <div class="model-instances-count">
            <span class="count-label">个体数量：</span>
            <span class="count-value">{{ selected3DModel?.instances?.length || 0 }}</span>
          </div>
        </div>
        
        <!-- CMG个体列表 - 卡片网格布局 -->
        <div class="model-instances-list">
          <div class="instances-header">个体列表</div>
          <div class="instances-grid-container">
            <div 
              v-for="cmg in selected3DModel?.instances || []" 
              :key="cmg.id"
              class="cmg-card"
              :style="{ backgroundColor: getCmgHealthBackgroundColor(cmg.health_score) }"
              @click="selectCmgFromDialog(cmg.id)"
            >
              <!-- CMG图片 -->
              <div class="cmg-card-image">
                <img 
                  :src="getCmgImagePath(cmg.cmg_model_name)" 
                  :alt="cmg.cmg_id"
                  @error="handleImageError"
                />
              </div>
              
              <!-- CMG信息 -->
              <div class="cmg-card-info">
                <div class="cmg-card-name">{{ cmg.cmg_id }}</div>
                <div class="cmg-card-health">
                  <span class="health-label">健康状态：</span>
                  <span 
                    v-if="cmg.health_score !== null && cmg.health_score !== undefined" 
                    class="health-value"
                    :style="{ color: getCmgHealthColor(cmg.health_score) }"
                  >
                    {{ cmg.health_score.toFixed(3) }}
                  </span>
                  <span v-else class="health-value no-data">
                    无数据
                  </span>
                </div>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div v-if="!selected3DModel?.instances || selected3DModel.instances.length === 0" class="empty-instances-dialog">
              暂无个体数据
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { ElSelect, ElOption, ElEmpty, ElIcon, ElMessage, ElMessageBox, ElDialog, ElForm, ElFormItem, ElInputNumber, ElDatePicker, ElButton, ElText, ElTag } from 'element-plus'
import { Loading, Timer, Setting, Warning, Upload, Search, DataAnalysis, EditPen, Connection, Tools, Monitor, User, List, Share, TrendCharts, Refresh, DataLine } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

// 响应式数据
const currentTime = ref('')
const selectedCmg = ref(null)
const isLoading = ref(true)

// CMG型号和个体相关数据
const selectedCmgModel = ref('')
const selectedCmgId = ref(null)
const cmgModels = ref([])
const cmgInstances = ref([])
const isLoadingModels = ref(false)
const expandedModels = ref({}) // 记录哪些型号被展开
const modelInstances = ref({}) // 存储每个型号的个体列表 { modelId: [instances] }
const loadingModels = ref({}) // 记录哪些型号正在加载个体数据

// 异常检测结果数据
const hasSelectedCmgAndTime = ref(false)
const isDataLoading = ref(false)
const anomalyRatio = ref(0)
const totalFrames = ref(0)
const anomalyCount = ref(0)
const anomalyFrames = ref([])

// MSFG部件分数数据
const componentScores = ref([])

// 部件详情对话框相关
const inferenceDialogVisible = ref(false)
const selectedComponent = ref(null)
const componentDetailData = ref(null)
const componentDetailLoading = ref(false)
const pieChartRef = ref(null)

// 寿命预测相关
const remainingLife = ref(null) // 剩余寿命（年）
const lifetimePredicting = ref(false) // 预测加载状态
const showLifetimeSettingsDialog = ref(false) // 参数设置对话框
const availableAlgorithms = ref([]) // 可用算法列表
const loadingAlgorithms = ref(false) // 算法加载状态
const currentAlgorithmInfo = ref(null) // 当前算法信息

// 寿命预测参数设置
const lifetimeSettings = ref({
  designLife: 10, // 设计寿命（年）
  startUseTime: null, // 启用时间
  algorithm: 'strategy0' // 预测算法
})

// 寿命预测趋势图相关
const lifetimeTrendData = ref([]) // 健康趋势数据
const lifetimeChartRef = ref(null) // 图表容器引用
let lifetimeChart = null // ECharts实例

// 🔧 监听预测状态变化，及时清理图表实例
watch(lifetimePredicting, (newVal) => {
  if (newVal === true) {
    // 进入预测状态，销毁图表实例（因为DOM会被v-if切换）
    if (lifetimeChart) {
      console.log('预测开始，销毁现有图表实例')
      lifetimeChart.dispose()
      lifetimeChart = null
    }
  }
})

// 时间选择相关数据
const showTimeSelector = ref(false)
const timelineData = ref(null)
const timelineRange = ref([0, 0])
const timeRange = ref([])
const selectedAnomalyFrame = ref(null)

// 异常帧详情对话框相关数据
const showAnomalyDetailDialog = ref(false)
const isAnimating = ref(true)
const isFullscreen = ref(false)
const timelineProgress = ref(30)
const currentTimeValue = ref(0)
const totalTime = ref(29)
const isDeleting = ref(false) // 删除加载状态

// 遥测数据相关
const telemetryFramesBefore = ref(100) // 前后帧数
const selectedTelemetryParameters = ref([]) // 选中的遥测量
const availableTelemetryParameters = ref([]) // 可用的遥测量列表
const telemetryLoading = ref(false) // 加载状态
const telemetryCharts = ref([]) // 图表数据
const telemetryChartInstances = ref({}) // 图表实例

// 计算属性
const filteredCmgs = computed(() => {
  return cmgInstances.value;
});

// 部件详情对话框的计算属性
const limitedTestpoints = computed(() => {
  if (!componentDetailData.value || !componentDetailData.value.surrounding_testpoints) return [];
  return componentDetailData.value.surrounding_testpoints.slice(0, 10); // 只显示前10个
});

const limitedFaults = computed(() => {
  if (!componentDetailData.value || !componentDetailData.value.surrounding_faults) return [];
  return componentDetailData.value.surrounding_faults.slice(0, 10); // 只显示前10个
});

// 时间滑块的标记点 - 显示具体时间
const timelineMarks = computed(() => {
  if (!timelineData.value || !timelineData.value.timeline || timelineData.value.timeline.length === 0) {
    return {};
  }
  
  const timeline = timelineData.value.timeline;
  const maxIndex = timeline.length - 1;
  const midIndex = Math.floor(maxIndex / 2);
  
  // 格式化时间为简洁格式
  const formatMarkTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).replace(/\//g, '-');
  };
  
  return {
    0: formatMarkTime(timeline[0].timestamp),
    [midIndex]: formatMarkTime(timeline[midIndex].timestamp),
    [maxIndex]: formatMarkTime(timeline[maxIndex].timestamp)
  };
});

// 分类展开状态
const expandedCategories = ref({
  highOrbit: true,
  lowOrbit: true
})

// 模拟数据
const highOrbitCmgs = ref([
  { id: 1, name: '风云四号', status: '正常', statusColor: '#4CAF50' },
  { id: 2, name: '北斗G1', status: '正常', statusColor: '#4CAF50' },
  { id: 3, name: '通信卫星三号', status: '警告', statusColor: '#FF9800' },
  { id: 4, name: '高分卫星', status: '正常', statusColor: '#4CAF50' }
])

const lowOrbitCmgs = ref([
  { id: 5, name: '天宫空间站', status: '正常', statusColor: '#4CAF50' },
  { id: 6, name: '星链-124', status: '异常', statusColor: '#F44336' },
  { id: 7, name: '资源三号', status: '正常', statusColor: '#4CAF50' },
  { id: 8, name: '环境卫星', status: '正常', statusColor: '#4CAF50' }
])

// Three.js 相关
let scene, camera, renderer, earth, satellites = []
let animationId
  let raycaster, mouse  // 用于点击检测
  
  // 3D模型点击交互相关
  const show3DModelDialog = ref(false)
  const selected3DModel = ref(null)

// 方法
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const toggleCategory = (category) => {
  expandedCategories.value[category] = !expandedCategories.value[category]
}

const toggleAnimation = () => {
  isAnimating.value = !isAnimating.value
}

// API调用函数
async function fetchCmgModels() {
  try {
    isLoadingModels.value = true;
    console.log('开始获取CMG型号列表');
    
    const response = await fetch('/api/v1/data/detection-overview/?action=cmg_models');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    console.log('API返回的型号数据:', data);
    
    cmgModels.value = data.cmg_models.map(model => ({
      label: model.model_name,
      value: model.id
    }));
    console.log('成功加载CMG型号，总数:', cmgModels.value.length);
  } catch (error) {
    console.error('获取CMG型号失败:', error);
  } finally {
    isLoadingModels.value = false;
  }
}

async function fetchCmgIndividuals(cmgModelId) {
  try {
    loadingModels.value[cmgModelId] = true;
    console.log('开始获取CMG个体，型号ID:', cmgModelId);
    
    const response = await fetch(`/api/v1/data/detection-overview/?action=cmg_individuals&cmg_model_id=${cmgModelId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    console.log('API返回的原始数据:', data);
    
    // 获取每个CMG个体的最新MSFG健康分数
    const cmgIndividualsWithHealth = await Promise.all(
      data.cmg_individuals.map(async (individual) => {
        let healthScore = null;
        try {
          const healthResponse = await fetch(`/api/v1/data/detection-overview/?action=latest_msfg_health&cmg_id=${individual.id}`);
          if (healthResponse.ok) {
            const healthData = await healthResponse.json();
            healthScore = healthData.health_score;
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
    
    // 存储到对应型号下
    modelInstances.value[cmgModelId] = cmgIndividualsWithHealth;
    console.log(`成功加载型号 ${cmgModelId} 的个体，总数:`, cmgIndividualsWithHealth.length);
  } catch (error) {
    console.error('获取CMG个体失败:', error);
    modelInstances.value[cmgModelId] = [];
  } finally {
    loadingModels.value[cmgModelId] = false;
  }
}

async function fetchCmgTimeline(cmgId) {
  try {
    console.log('获取时间轴数据，cmgId:', cmgId);
    const response = await fetch(`/api/v1/data/detection-overview/?action=cmg_timeline&cmg_id=${cmgId}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('API错误响应:', errorData);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    
    timelineData.value = data;
    
    if (data.timeline && data.timeline.length > 0) {
      timelineRange.value = [0, data.timeline.length - 1];
      console.log('时间轴数据加载成功，数据点数量:', data.timeline.length);
    } else {
      console.warn('时间轴数据为空');
    }
  } catch (error) {
    console.error('获取时间轴数据失败:', error);
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
    
    console.log('成功加载异常检测结果');
  } catch (error) {
    console.error('获取异常检测结果失败:', error);
    // 重置数据
    anomalyRatio.value = 0;
    totalFrames.value = 0;
    anomalyCount.value = 0;
    anomalyFrames.value = [];
  }
}

async function fetchComponentScores(cmgId, startTime, endTime) {
  try {
    console.log('获取MSFG部件分数，cmgId:', cmgId, 'startTime:', startTime, 'endTime:', endTime);
    const response = await fetch(`/api/v1/data/detection-overview/?action=component_scores&cmg_id=${cmgId}&start_time=${startTime}&end_time=${endTime}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('API错误响应:', errorData);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    
    console.log('API返回的部件分数数据:', data);
    
    // 转换数据格式为前端需要的格式
    if (data.component_scores && data.component_scores.length > 0) {
      componentScores.value = data.component_scores.map((comp, index) => ({
        id: `comp_${index}`,
        name: comp.component_name,
        healthScore: comp.average_score,
        scoreCount: comp.score_count,
        minScore: comp.min_score,
        maxScore: comp.max_score
      }));
      console.log('成功加载MSFG部件分数，部件数量:', componentScores.value.length);
    } else {
      console.log('没有部件分数数据');
      componentScores.value = [];
    }
  } catch (error) {
    console.error('获取MSFG部件分数失败:', error);
    componentScores.value = [];
  }
}

// CMG选择相关函数
async function toggleModel(modelId) {
  console.log('点击型号:', modelId);
  
  // 切换展开/收起状态
  expandedModels.value[modelId] = !expandedModels.value[modelId];
  
  // 如果是展开，且还没有加载过该型号的个体数据，则加载
  if (expandedModels.value[modelId] && !modelInstances.value[modelId]) {
    await fetchCmgIndividuals(modelId);
  }
}

function getModelInstanceCount(modelId) {
  const instances = modelInstances.value[modelId];
  if (!instances) return '';
  return `(${instances.length})`;
}

async function selectCmg(id) {
  console.log('选择CMG个体，id:', id);
  
  selectedCmgId.value = id;
  
  // 从所有型号的个体列表中查找
  let selectedCmg = null;
  for (const modelId in modelInstances.value) {
    const found = modelInstances.value[modelId].find(cmg => cmg.id === id);
    if (found) {
      selectedCmg = found;
      break;
    }
  }
  
  console.log('选择的CMG个体详情:', selectedCmg);
  
  // 打开时间选择器
  await openTimeSelector();
}

// 健康分数相关函数
function getCmgHealthColor(healthScore) {
  if (healthScore === null || healthScore === undefined) {
    return '#c0c4cc'; // 灰色 - 无数据
  }
  if (healthScore >= 0.8) {
    return '#67c23a'; // 绿色 - 0.8以上
  }
  if (healthScore >= 0.5) {
    return '#e6a23c'; // 橙色 - 0.5-0.8
  }
  return '#f56c6c'; // 红色 - 0.5以下
}

// 获取健康分数对应的高透明度背景色（用于卡片背景）
function getCmgHealthBackgroundColor(healthScore) {
  if (healthScore === null || healthScore === undefined) {
    return 'rgba(192, 196, 204, 0.15)'; // 灰色透明 - 无数据
  }
  if (healthScore >= 0.8) {
    return 'rgba(103, 194, 58, 0.2)'; // 绿色透明 - 0.8以上
  }
  if (healthScore >= 0.5) {
    return 'rgba(230, 162, 60, 0.2)'; // 橙色透明 - 0.5-0.8
  }
  return 'rgba(245, 108, 108, 0.2)'; // 红色透明 - 0.5以下
}

// CMG图片模糊匹配函数
function getCmgImagePath(cmgModelName) {
  if (!cmgModelName) {
    return '/images/CMG.png'; // 默认图片
  }
  
  const modelNameUpper = cmgModelName.toUpperCase();
  
  // 支持的图片映射（按数字大小降序，避免误匹配）
  const imageMap = [
    { pattern: '500NMS', path: '/images/500NMS.png' },
    { pattern: '500NM', path: '/images/500NMS.png' },
    { pattern: '15NMS', path: '/images/15NMS.png' },
    { pattern: '15NM', path: '/images/15NMS.png' },
    { pattern: '5NMS', path: '/images/5NMS.jpg' },
    { pattern: '5NM', path: '/images/5NMS.jpg' },
    { pattern: '2NMS', path: '/images/2NMS.jpg' },
    { pattern: '2NM', path: '/images/2NMS.jpg' },
  ];
  
  // 尝试匹配
  for (const item of imageMap) {
    if (modelNameUpper.includes(item.pattern)) {
      console.log(`CMG图片匹配: '${cmgModelName}' -> '${item.path}'`);
      return item.path;
    }
  }
  
  // 如果没有匹配到，尝试提取数字
  const numbers = modelNameUpper.match(/\d+/g);
  if (numbers) {
    for (const num of numbers) {
      // 尝试数字+NMS格式
      const candidate = num + 'NMS';
      const found = imageMap.find(item => item.pattern === candidate);
      if (found) {
        console.log(`CMG图片数字推断: '${cmgModelName}' -> '${found.path}' (从数字 ${num})`);
        return found.path;
      }
    }
  }
  
  // 默认图片
  console.log(`CMG图片使用默认: '${cmgModelName}' -> '/images/CMG.png'`);
  return '/images/CMG.png';
}

// 图片加载错误处理
function handleImageError(event) {
  console.warn('CMG图片加载失败，使用默认图片');
  event.target.src = '/images/CMG.png';
}

// 从3D模型弹窗选择CMG个体
async function selectCmgFromDialog(id) {
  console.log('从3D模型弹窗选择CMG个体，id:', id);
  
  // 关闭3D模型弹窗
  show3DModelDialog.value = false;
  
  // 调用原有的选择逻辑
  await selectCmg(id);
}

// 获取健康分数对应的颜色（用于子部件方块）
function getHealthColor(score) {
  // 按照颜色规则：0.75-1绿色，0.25-0.75橙色，0.25以下红色
  if (score >= 0.75) return '#67c23a'; // 绿色：0.75-1
  if (score >= 0.25) return '#e6a23c';  // 橙色：0.25-0.75
  return '#f56c6c'; // 红色：0.25以下
}

// 获取健康分数对应的高透明度颜色（用于方块背景）
function getHealthColorWithAlpha(score) {
  // 按照颜色规则，但使用高透明度（0.15）
  if (score >= 0.75) return 'rgba(103, 194, 58, 0.15)'; // 绿色透明：0.75-1
  if (score >= 0.25) return 'rgba(230, 162, 60, 0.15)';  // 橙色透明：0.25-0.75
  return 'rgba(245, 108, 108, 0.15)'; // 红色透明：0.25以下
}

// 异常检测结果相关函数
function getAnomalyRatioClass(ratio) {
  if (ratio >= 0.1) return 'high-risk';
  if (ratio >= 0.05) return 'medium-risk';
  return 'low-risk';
}

function getScoreClass(score) {
  if (score >= 0.9) return 'high-score';
  if (score >= 0.7) return 'medium-score';
  return 'low-score';
}

function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', { 
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
}

async function selectAnomalyFrame(frame) {
  console.log('选择异常帧:', frame);
  
  // 先显示对话框
  showAnomalyDetailDialog.value = true;
  
  // 初始化为基础数据
  selectedAnomalyFrame.value = { ...frame };
  
  // 调试：延迟检查对话框样式
  setTimeout(() => {
    const dialog = document.querySelector('.el-dialog.bigscreen-detail-dialog');
    if (dialog) {
      const styles = window.getComputedStyle(dialog);
      console.log('=== 异常帧详情对话框样式调试信息 ===');
      console.log('对话框背景色:', styles.backgroundColor);
      console.log('对话框边框:', styles.border);
      console.log('对话框类名:', dialog.className);
      console.log('对话框元素:', dialog);
      
      // 检查Card组件
      const cards = dialog.querySelectorAll('.el-card');
      if (cards.length > 0) {
        const cardStyles = window.getComputedStyle(cards[0]);
        console.log('Card背景色:', cardStyles.backgroundColor);
        console.log('Card边框:', cardStyles.border);
      }
      
      // 检查表格
      const tables = dialog.querySelectorAll('.el-table');
      if (tables.length > 0) {
        const tableStyles = window.getComputedStyle(tables[0]);
        console.log('表格背景色:', tableStyles.backgroundColor);
      }
      
      console.log('===================================');
    } else {
      console.error('未找到对话框元素！');
    }
  }, 300);
  
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
      console.error('❌ IMS检测详情API错误:', imsResponse.status);
    }
    
    // 处理规则检测详情
    if (ruleResponse.ok) {
      ruleData = await ruleResponse.json();
      console.log('✅ 规则检测详情数据:', ruleData);
    } else {
      console.error('❌ 规则检测详情API错误:', ruleResponse.status);
    }
    
    // 处理MSFG检测详情
    if (msfgResponse.ok) {
      msfgData = await msfgResponse.json();
      console.log('✅ MSFG检测详情数据:', msfgData);
    } else {
      console.error('❌ MSFG检测详情API错误:', msfgResponse.status);
    }
    
    // 更新数据
    const updatedData = { ...selectedAnomalyFrame.value };
    
    if (imsData) {
      updatedData.ims = imsData.ims;
      updatedData.cmg_id = imsData.cmg_id;
      updatedData.timestamp = imsData.timestamp;
    }
    
    if (ruleData) {
      updatedData.rules = ruleData.rules;
    }
    
    if (msfgData && msfgData.msfg) {
      updatedData.msfg = msfgData.msfg;
    }
    
    selectedAnomalyFrame.value = updatedData;
    console.log('数据加载完成:', updatedData);
    
    // 自动加载可用的遥测参数
    await fetchAvailableTelemetryParameters();
    
    // 自动选择前三个遥测量并加载数据
    if (availableTelemetryParameters.value.length > 0) {
      selectedTelemetryParameters.value = availableTelemetryParameters.value.slice(0, 3);
      // 自动加载遥测数据
      await loadTelemetryData();
    }
    
  } catch (error) {
    console.error('❌ 获取检测详情失败:', error);
  }
}

// 时间选择相关函数
async function openTimeSelector() {
  if (!selectedCmgId.value) {
    console.warn('未选择CMG个体');
    return;
  }
  
  console.log('打开时间选择器，selectedCmgId:', selectedCmgId.value);
  
  // 获取时间轴数据
  await fetchCmgTimeline(selectedCmgId.value);
  showTimeSelector.value = true;
  
  // 调试：延迟检查对话框样式
  setTimeout(() => {
    console.log('=== 时间选择对话框样式调试信息 ===');
    
    // 查找所有对话框相关元素
    const allDialogs = document.querySelectorAll('.el-dialog');
    const allWrappers = document.querySelectorAll('.el-dialog__wrapper');
    const customClass = document.querySelectorAll('.time-selector-dialog');
    
    console.log('找到 .el-dialog 元素数量:', allDialogs.length);
    console.log('找到 .el-dialog__wrapper 元素数量:', allWrappers.length);
    console.log('找到 .time-selector-dialog 元素数量:', customClass.length);
    
    allDialogs.forEach((d, i) => {
      console.log(`el-dialog ${i} 类名:`, d.className);
      const styles = window.getComputedStyle(d);
      console.log(`  背景色:`, styles.backgroundColor);
    });
    
    customClass.forEach((d, i) => {
      console.log(`time-selector-dialog ${i} 类名:`, d.className);
      console.log(`  标签名:`, d.tagName);
      const styles = window.getComputedStyle(d);
      console.log(`  背景色:`, styles.backgroundColor);
    });
    
    // 尝试查找最新打开的对话框（通常是最后一个）
    if (allDialogs.length > 0) {
      const lastDialog = allDialogs[allDialogs.length - 1];
      console.log('\n最后一个对话框（可能是刚打开的）:');
      console.log('类名:', lastDialog.className);
      const styles = window.getComputedStyle(lastDialog);
      console.log('背景色:', styles.backgroundColor);
      console.log('边框:', styles.border);
      
      // 检查是否有自定义类名
      if (lastDialog.classList.contains('time-selector-dialog')) {
        console.log('✅ 包含 time-selector-dialog 类名');
      } else {
        console.log('❌ 不包含 time-selector-dialog 类名');
        console.log('需要手动添加类名到这个元素');
      }
    }
    
    console.log('===================================');
  }, 500);
}

async function confirmTimeRange() {
  let startTime, endTime;
  
  if (timelineData.value && timelineData.value.timeline && timelineData.value.timeline.length > 0) {
    // 使用时间轴选择
    const timeline = timelineData.value.timeline;
    startTime = new Date(timeline[timelineRange.value[0]].timestamp);
    endTime = new Date(timeline[timelineRange.value[1]].timestamp);
    
    timeRange.value = [startTime, endTime];
    console.log(`时间范围已设置: ${startTime.toLocaleString()} - ${endTime.toLocaleString()}`);
  } else if (timeRange.value && timeRange.value.length === 2) {
    // 使用手动时间选择
    startTime = timeRange.value[0];
    endTime = timeRange.value[1];
    console.log(`时间范围已设置: ${startTime.toLocaleString()} - ${endTime.toLocaleString()}`);
  } else {
    console.warn('请选择一个完整的时间范围');
    return;
  }
  
  showTimeSelector.value = false;
  
  // 设置页面状态：已选择CMG和时间段
  hasSelectedCmgAndTime.value = true;
  isDataLoading.value = true;
  
  // 并行加载异常检测结果和MSFG部件分数
  if (selectedCmgId.value) {
    try {
      // 并行加载异常检测结果和MSFG部件分数（快速加载）
      await Promise.all([
        fetchAnomalyResults(selectedCmgId.value, startTime.toISOString(), endTime.toISOString()),
        fetchComponentScores(selectedCmgId.value, startTime.toISOString(), endTime.toISOString())
      ]);
      console.log('异常检测结果和MSFG部件分数加载完成');
      
      // 独立加载寿命预测（不阻塞其他模块）
      executeLifetimePredictionWithDefaults(selectedCmgId.value, startTime.toISOString(), endTime.toISOString()).catch(error => {
        console.error('寿命预测失败:', error);
        // 寿命预测失败不影响其他数据的加载
      });
      
    } catch (error) {
      console.error('数据加载失败:', error);
    } finally {
      isDataLoading.value = false;
    }
  }
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

// 人工判定处理函数
async function handleManualJudgment() {
  console.log('=== 人工判定按钮被点击 ===');
  console.log('selectedAnomalyFrame:', selectedAnomalyFrame.value);
  
  if (!selectedAnomalyFrame.value || !selectedAnomalyFrame.value.id) {
    console.warn('未选择异常帧');
    ElMessage.warning('未选择异常帧');
    return;
  }
  
  console.log('准备显示确认对话框，frame_id:', selectedAnomalyFrame.value.id);
  
  try {
    // 显示确认对话框
    console.log('调用 ElMessageBox.confirm...');
    await ElMessageBox.confirm(
      '确认判定此帧为虚警并从数据库删除吗？',
      '人工判定',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'bigscreen-confirm-dialog',
        distinguishCancelAndClose: true
      }
    );
    
    console.log('用户确认删除');
    
    // 用户确认，执行删除
    isDeleting.value = true;
    
    const frameId = selectedAnomalyFrame.value.id;
    console.log('准备删除异常帧，ID:', frameId);
    
    // 调用删除API
    const response = await fetch(`/api/v1/data/detection-overview/?action=delete_anomaly_frame&frame_id=${frameId}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('删除成功:', result);
    
    ElMessage.success('虚警帧已成功删除');
    
    // 关闭详情对话框
    showAnomalyDetailDialog.value = false;
    
    // 从异常帧列表中移除该帧
    const frameIndex = anomalyFrames.value.findIndex(f => f.id === frameId);
    if (frameIndex !== -1) {
      anomalyFrames.value.splice(frameIndex, 1);
      anomalyCount.value--;
      
      // 重新计算异常比例
      if (totalFrames.value > 0) {
        anomalyRatio.value = anomalyCount.value / totalFrames.value;
      }
    }
    
    // 清空选中的异常帧
    selectedAnomalyFrame.value = null;
    
  } catch (error) {
    if (error === 'cancel') {
      console.log('用户取消了删除操作');
    } else {
      console.error('删除异常帧失败:', error);
      ElMessage.error(`删除失败: ${error.message || '未知错误'}`);
    }
  } finally {
    isDeleting.value = false;
  }
}

// 异常帧详情相关辅助函数
function getScoreTagType(score) {
  if (score >= 0.75) return 'danger';  // 0.75以上显示红色
  if (score >= 0.5) return 'warning';  // 0.5-0.75显示橙色
  return 'success';                    // 0.5以下显示绿色
}

function getHealthScoreTagType(score) {
  if (score < 0.5) return 'danger';   // 0.5以下 - 红色
  if (score < 0.75) return 'warning'; // 0.5-0.75 - 橙色
  return 'success';                   // 0.75-1 - 绿色
}

function getHealthScoreText(score) {
  if (score < 0.5) return '故障';   // 0.5以下
  if (score < 0.75) return '退化';  // 0.5-0.75
  return '正常';                   // 0.75-1
}

// 部件详情对话框相关函数
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
    
    // 构建API请求参数
    const params = new URLSearchParams({
      action: 'component_details',
      cmg_id: selectedCmgId.value,
      component_name: component.name,
      start_time: timeRange.value[0].toISOString(),
      end_time: timeRange.value[1].toISOString()
    });
    
    console.log('获取部件详情，参数:', {
      cmg_id: selectedCmgId.value,
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
    console.log('测点数量:', data.surrounding_testpoints?.length || 0);
    console.log('故障数量:', data.surrounding_faults?.length || 0);
    
    // 更新数据
    componentDetailData.value = data;
    
    // 初始化饼状图
    nextTick(() => {
      setTimeout(() => {
        console.log('准备初始化饼图...');
        initPieChart();
      }, 200);
    });
    
    ElMessage.success(`成功获取部件 '${component.name}' 的详细信息`);
    
  } catch (error) {
    console.error('获取部件详情失败:', error);
    ElMessage.error(`获取部件详情失败: ${error.message}`);
  } finally {
    componentDetailLoading.value = false;
  }
}

// 初始化饼状图
function initPieChart() {
  if (!pieChartRef.value || !componentDetailData.value) {
    console.log('饼状图容器或数据未准备好');
    return;
  }
  
  const chart = echarts.init(pieChartRef.value);
  
  // 准备单个饼图数据 - 合并测点和故障数据
  const pieData = preparePieChartData();
  
  console.log('初始化饼图，数据数量:', pieData.length);
  
  // 如果没有数据，显示空状态
  if (pieData.length === 0) {
    console.log('没有可显示的数据');
    return;
  }
  
  const option = {
    title: {
      text: `${componentDetailData.value.center_component?.name || '部件'} - 测点与故障分数分布`,
      left: 'center',
      top: 10,  // 调整到更靠上的位置
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#ffffff'
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
      },
      backgroundColor: 'rgba(30, 58, 138, 0.9)',
      borderColor: 'rgba(147, 197, 253, 0.5)',
      textStyle: { color: '#ffffff' }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle',
      textStyle: { color: '#ffffff' },
      formatter: function(name) {
        const item = pieData.find(d => d.name === name);
        return `${name} (${item?.value?.toFixed(3) || 0})`;
      }
    },
    series: [
      {
        name: '分数分布',
        type: 'pie',
        radius: ['35%', '65%'],  // 稍微缩小饼图，从['40%', '70%']改为['35%', '65%']
        center: ['60%', '58%'],  // 调整饼图中心位置，从['60%', '55%']改为['60%', '58%']
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}\n{d}%',
          color: '#ffffff',
          fontSize: 11
        },
        labelLine: {
          show: true,
          lineStyle: { color: '#ffffff' }
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        data: pieData
      }
    ]
  };
  
  chart.setOption(option);
  console.log('饼图初始化完成');
}

// 准备饼图数据 - 合并测点和故障数据
function preparePieChartData() {
  if (!componentDetailData.value) return [];
  
  const data = [];
  
  // 添加所有测点数据（用蓝色表示）
  if (componentDetailData.value.surrounding_testpoints) {
    componentDetailData.value.surrounding_testpoints.forEach(testpoint => {
      const score = testpoint.average_score || 0;
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

function getNodeColor(score, type) {
  // 根据分数返回颜色（分数越高越危险）
  if (score >= 0.7) return '#f56c6c';  // 红色
  if (score >= 0.4) return '#e6a23c';  // 橙色
  return '#67c23a';  // 绿色
}

// 寿命预测相关函数
async function fetchAvailableAlgorithms() {
  if (loadingAlgorithms.value) return
  
  loadingAlgorithms.value = true
  try {
    const response = await fetch('/api/v1/lifetime/algorithms/')
    console.log('获取算法列表响应状态:', response.status, response.statusText)
    
    if (response.ok) {
      const contentType = response.headers.get('content-type')
      console.log('响应内容类型:', contentType)
      
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json()
        if (data.status === 'success') {
          availableAlgorithms.value = data.data
          console.log('成功获取算法列表:', availableAlgorithms.value)
        } else {
          console.error('获取算法列表失败:', data.message)
          throw new Error(data.message || '算法列表API返回错误')
        }
      } else {
        // 如果返回的不是JSON，可能是HTML错误页面
        const text = await response.text()
        console.error('API返回非JSON内容:', text.substring(0, 200))
        throw new Error('算法列表API返回了HTML页面，可能是路由错误')
      }
    } else {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
  } catch (error) {
    console.error('获取算法列表错误:', error)
    console.log('使用默认算法列表作为备选')
    
    // 使用默认算法列表，不显示错误消息给用户
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

// 执行寿命预测（使用默认参数）
async function executeLifetimePredictionWithDefaults(cmgId, startTime, endTime) {
  console.log('使用默认参数执行寿命预测:', { cmgId, startTime, endTime })
  
  // 设置加载状态
  lifetimePredicting.value = true
  
  try {
    // 设置默认参数
    const defaultDesignLife = 10 // 默认10年设计寿命
    const defaultAlgorithm = 'strategy0' // 默认算法
    
    // 如果没有设置启用时间，使用数据开始时间
    let defaultStartUseTime = lifetimeSettings.value.startUseTime
    if (!defaultStartUseTime) {
      defaultStartUseTime = new Date(startTime).toISOString().replace('T', ' ').split('.')[0]
    }
    
    const result = await executeLifetimePrediction(cmgId, startTime, endTime, defaultDesignLife, defaultStartUseTime, defaultAlgorithm)
    return result
  } catch (error) {
    console.error('默认参数寿命预测失败:', error)
    throw error
  } finally {
    // 无论成功还是失败，都要取消加载状态
    lifetimePredicting.value = false
  }
}

// 执行寿命预测（带自定义参数）
async function executeLifetimePrediction(cmgId, startTime, endTime, designLife, startUseTime, algorithm) {
  try {
    console.log('执行寿命预测:', { cmgId, startTime, endTime, designLife, startUseTime, algorithm })
    
    const params = new URLSearchParams({
      action: 'lifetime_trend',
      cmg_id: cmgId,
      start_time: startTime,
      end_time: endTime,
      design_life: designLife,
      algorithm: algorithm
    })
    
    if (startUseTime) {
      params.append('start_use_time', startUseTime)
    }
    
    const response = await fetch(`/api/v1/data/detection-overview/?${params}`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('寿命预测响应:', data)
    
    if (data.status === 'success') {
      // 更新剩余寿命显示
      remainingLife.value = data.remaining_life_years
      
      // 更新趋势数据
      lifetimeTrendData.value = data.trend_data || []
      
      // 更新当前算法信息
      if (algorithm && availableAlgorithms.value.length > 0) {
        currentAlgorithmInfo.value = availableAlgorithms.value.find(algo => algo.key === algorithm)
      }
      
      console.log('寿命预测成功:', {
        remaining_life_years: data.remaining_life_years,
        trend_data_count: lifetimeTrendData.value.length,
        algorithm: algorithm
      })
      
      // 🔧 修复：检查图表实例是否真正有效
      nextTick(() => {
        setTimeout(() => {
          // 检查图表实例是否存在且未被销毁
          const isChartValid = lifetimeChart && !lifetimeChart.isDisposed()
          
          if (!isChartValid) {
            console.log('图表实例不存在或已失效，重新初始化')
            initLifetimeChart()
          } else {
            console.log('图表实例有效，直接更新数据')
            updateLifetimeChart()
          }
        }, 300) // 稍微增加延迟确保DOM完全渲染
      })
      
      ElMessage.success(`寿命预测完成，剩余寿命: ${data.remaining_life_years.toFixed(2)} 年`)
      return data
    } else {
      throw new Error(data.error || '寿命预测失败')
    }
  } catch (error) {
    console.error('寿命预测失败:', error)
    
    // 根据错误类型提供友好提示
    if (error.message.includes('使用起点时间不能晚于数据起点时间')) {
      ElMessage.error('设置的启用时间晚于数据起始时间，请重新设置参数')
    } else if (error.message.includes('数据终点时间已经超过设计寿命')) {
      ElMessage.error('数据时间范围已超过设计寿命，请调整参数')
    } else {
      ElMessage.error(`寿命预测失败: ${error.message}`)
    }
    
    remainingLife.value = null
    throw error
  }
}

// 寿命预测对话框相关函数
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
  
  // 获取可用算法列表
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

// 确认寿命预测设置
async function confirmLifetimeSettings() {
  if (!lifetimeSettings.value.designLife || !lifetimeSettings.value.startUseTime) {
    ElMessage.warning('请设置设计寿命和启用时间');
    return;
  }
  
  showLifetimeSettingsDialog.value = false;
  lifetimePredicting.value = true;
  
  console.log('用户确认更新寿命预测参数:', {
    designLife: lifetimeSettings.value.designLife,
    startUseTime: lifetimeSettings.value.startUseTime,
    algorithm: lifetimeSettings.value.algorithm,
    selectedCmgId: selectedCmgId.value,
    timeRange: timeRange.value
  });
  
  // 重新执行寿命预测
  if (selectedCmgId.value && timeRange.value && timeRange.value.length === 2) {
    try {
      await executeLifetimePrediction(
        selectedCmgId.value,
        timeRange.value[0].toISOString(),
        timeRange.value[1].toISOString(),
        lifetimeSettings.value.designLife,
        lifetimeSettings.value.startUseTime,
        lifetimeSettings.value.algorithm
      );
      
      ElMessage.success('寿命预测参数已更新');
    } catch (error) {
      console.error('重新执行寿命预测失败:', error);
      ElMessage.error('更新寿命预测参数失败，请重试');
    } finally {
      lifetimePredicting.value = false;
    }
  }
}

// 关闭寿命预测设置对话框
function handleLifetimeSettingsClose() {
  // 如果正在预测中，阻止关闭对话框
  if (lifetimePredicting.value) {
    ElMessage.warning('正在进行寿命预测，请等待完成...');
    return;
  }
  showLifetimeSettingsDialog.value = false;
}

// 初始化寿命趋势图
function initLifetimeChart() {
  console.log('开始初始化寿命趋势图:', {
    chartRef: !!lifetimeChartRef.value,
    trendDataLength: lifetimeTrendData.value?.length || 0,
    containerElement: lifetimeChartRef.value
  })
  
  if (!lifetimeChartRef.value) {
    console.log('图表容器不存在，无法初始化')
    return
  }
  
  // 检查容器尺寸
  const containerWidth = lifetimeChartRef.value.offsetWidth
  const containerHeight = lifetimeChartRef.value.offsetHeight
  const clientWidth = lifetimeChartRef.value.clientWidth
  const clientHeight = lifetimeChartRef.value.clientHeight
  
  console.log('容器尺寸详情:', { 
    offsetWidth: containerWidth, 
    offsetHeight: containerHeight,
    clientWidth: clientWidth,
    clientHeight: clientHeight,
    parentElement: lifetimeChartRef.value.parentElement,
    parentWidth: lifetimeChartRef.value.parentElement?.offsetWidth,
    parentHeight: lifetimeChartRef.value.parentElement?.offsetHeight
  })
  
  if (containerWidth === 0 || containerHeight === 0) {
    console.log('容器尺寸为0，尝试强制设置尺寸')
    // 强制设置容器尺寸
    lifetimeChartRef.value.style.width = '100%'
    lifetimeChartRef.value.style.height = '200px'
    lifetimeChartRef.value.style.minHeight = '200px'
    
    // 再次检查尺寸
    setTimeout(() => {
      const newWidth = lifetimeChartRef.value.offsetWidth
      const newHeight = lifetimeChartRef.value.offsetHeight
      console.log('强制设置后的容器尺寸:', { width: newWidth, height: newHeight })
      
      if (newWidth > 0 && newHeight > 0) {
        initLifetimeChart() // 重新尝试初始化
      } else {
        console.log('强制设置尺寸失败，延迟重试')
        setTimeout(() => initLifetimeChart(), 200)
      }
    }, 50)
    return
  }

  try {
    // 销毁现有图表实例
    if (lifetimeChart) {
      lifetimeChart.dispose()
      lifetimeChart = null
    }

    // 创建新的图表实例
    lifetimeChart = echarts.init(lifetimeChartRef.value)
    console.log('ECharts实例创建成功:', lifetimeChart)

    // 创建基础图表配置（不包含数据）
    const option = {
      title: {
        text: '健康指数趋势',
        left: 'center',
        top: 10,
        textStyle: {
          fontSize: 14,
          fontWeight: 'bold',
          color: '#ffffff'
        }
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(30, 58, 138, 0.9)',
        borderColor: 'rgba(147, 197, 253, 0.5)',
        textStyle: { color: '#ffffff' },
        formatter: function(params) {
          if (params && params[0]) {
            const param = params[0]
            const date = new Date(param.value[0]).toLocaleString('zh-CN')
            const value = param.value[1]
            return `时间: ${date}<br/>健康指数: ${value.toFixed(4)}`
          }
          return ''
        }
      },
      grid: {
        left: '8%',
        right: '5%',
        top: '25%', /* 增加顶部空间给标题 */
        bottom: '10%', /* 减少底部空间 */
        containLabel: true
      },
      xAxis: {
        type: 'time',
        axisLabel: {
          color: '#ffffff',
          fontSize: 10,
          formatter: '{MM}-{dd}\n{HH}:{mm}'
        },
        axisLine: {
          lineStyle: { color: 'rgba(255, 255, 255, 0.3)' }
        },
        splitLine: {
          show: false
        }
      },
      yAxis: {
        type: 'value',
        name: '健康指数',
        nameTextStyle: {
          color: '#ffffff',
          fontSize: 12
        },
        axisLabel: {
          color: '#ffffff',
          fontSize: 10
        },
        axisLine: {
          lineStyle: { color: 'rgba(255, 255, 255, 0.3)' }
        },
        splitLine: {
          lineStyle: { color: 'rgba(255, 255, 255, 0.1)' }
        }
      },
      series: [] // 初始时为空，后续通过updateLifetimeChart更新数据
    }

    lifetimeChart.setOption(option)
    console.log('寿命趋势图基础配置设置完成')
    
    // 如果有数据，立即更新
    if (lifetimeTrendData.value && lifetimeTrendData.value.length > 0) {
      updateLifetimeChart()
    }
    
    console.log('寿命趋势图初始化完成')
  } catch (error) {
    console.error('寿命趋势图初始化失败:', error)
  }
}

// 更新寿命趋势图数据
function updateLifetimeChart() {
  console.log('开始更新寿命趋势图数据')
  
  if (!lifetimeChart) {
    console.log('图表实例不存在，尝试初始化')
    initLifetimeChart()
    return
  }
  
  if (!lifetimeTrendData.value || lifetimeTrendData.value.length === 0) {
    console.log('没有趋势数据，清空图表')
    lifetimeChart.setOption({
      series: []
    })
    return
  }
  
  // 准备数据：转换为ECharts时间轴需要的格式 [timestamp, value]
  const chartData = lifetimeTrendData.value.map(item => {
    const timestamp = new Date(item.timestamp).getTime()
    const value = parseFloat(item.health_index)
    return [timestamp, isNaN(value) ? null : value]
  })
  
  console.log('趋势数据处理完成:', {
    原始数据点: lifetimeTrendData.value.length,
    处理后数据点: chartData.length,
    样本数据: chartData.slice(0, 3),
    时间范围: chartData.length > 0 ? {
      开始: new Date(chartData[0][0]).toLocaleString(),
      结束: new Date(chartData[chartData.length - 1][0]).toLocaleString()
    } : null
  })
  
  // 更新图表数据和坐标轴范围
  const updateOption = {
    xAxis: {
      // 强制重新计算时间轴范围
      min: null,
      max: null
    },
    yAxis: {
      // 强制重新计算数值轴范围
      min: null,
      max: null
    },
    series: [{
      name: '健康指数',
      type: 'line',
      data: chartData,
      smooth: true,
      lineStyle: {
        color: '#00d4ff',
        width: 2
      },
      itemStyle: {
        color: '#00d4ff'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(0, 212, 255, 0.3)' },
            { offset: 1, color: 'rgba(0, 212, 255, 0.05)' }
          ]
        }
      },
      symbol: 'circle',
      symbolSize: 4
    }]
  }
  
  // 使用默认合并模式更新，保留样式配置，只更新数据和范围
  // 设置 min/max 为 null 强制 ECharts 根据新数据重新计算坐标轴范围
  lifetimeChart.setOption(updateOption)
  console.log('寿命趋势图数据更新完成')
}

// 页面跳转函数
function openPage(path) {
  console.log('跳转到页面:', path)
  // 在新窗口中打开页面
  const baseUrl = window.location.origin
  const fullUrl = `${baseUrl}${path}`
  window.open(fullUrl, '_blank')
}

function formatParameterScores(scores) {
  if (!scores) return [];
  return Object.entries(scores).map(([parameter, score]) => ({
    parameter,
    score: score.toFixed(4)
  }));
}

function extractTop3Components(componentHealth) {
  if (!componentHealth || Object.keys(componentHealth).length === 0) {
    return [];
  }
  
  // 转换为数组并按健康分数排序（从低到高，问题最严重的在前）
  const components = Object.entries(componentHealth).map(([name, data]) => ({
    component: name,
    score: data.health_score || 1.0
  }));
  
  components.sort((a, b) => a.score - b.score);
  
  // 返回前3个
  return components.slice(0, 3);
}

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

const closeBigScreen = () => {
  window.close()
}

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 初始化3D场景
const initThreeJS = () => {
  const container = document.querySelector('.earth-container')
  if (!container) return

  // 创建场景
  scene = new THREE.Scene()
  scene.background = null // 设置为透明，让宇宙背景显示

  // 创建相机
  camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000)
  camera.position.set(0, 0, 5)

  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(container.clientWidth, container.clientHeight)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  container.appendChild(renderer.domElement)
    
    // 初始化Raycaster用于点击检测
    raycaster = new THREE.Raycaster()
    mouse = new THREE.Vector2()
    
    // 添加点击事件监听
    renderer.domElement.addEventListener('click', onModelClick, false)

  // 创建地球
  createEarth()
  
  // 注意：createSatellites()和createOrbits()将在型号数据加载完成后调用

  // 添加光照 - 增强整体亮度
  const ambientLight = new THREE.AmbientLight(0xcccccc, 1.8)  // 提高环境光亮度和颜色
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 2.0)  // 增强主光源
  directionalLight.position.set(5, 5, 5)
  directionalLight.castShadow = true
  scene.add(directionalLight)
  
  // 添加额外的光照来增强地球亮度
  const fillLight = new THREE.DirectionalLight(0xffffff, 1.2)  // 增强补光
  fillLight.position.set(-3, -2, 3)
  scene.add(fillLight)

  // 开始渲染循环
  animate()
  
  isLoading.value = false
}

const createEarth = () => {
  const geometry = new THREE.SphereGeometry(1.5, 64, 64)
  
  // 创建地球材质 - 优化参数去除灰色
  const material = new THREE.MeshPhongMaterial({
    color: 0xffffff,        // 设置为纯白色，让纹理颜色完全显示
    shininess: 25,          // 降低反光度，更自然（原来是100）
    emissive: 0x111111,     // 添加轻微自发光，提升亮度
    emissiveIntensity: 0.15 // 自发光强度
  })
  
  // 使用本地地球纹理
  const textureLoader = new THREE.TextureLoader()
  
  // 加载本地地球表面纹理
  const earthTexture = textureLoader.load(
    '/textures/earth_atmos_2048.jpg',
    (texture) => {
      // 纹理加载成功后设置色彩空间
      texture.colorSpace = THREE.SRGBColorSpace  // 使用sRGB色彩空间，颜色更鲜艳
      material.needsUpdate = true
      console.log('地球纹理加载成功')
    },
    undefined, // onProgress
    (error) => {
      console.warn('地球纹理加载失败，使用备用方案:', error)
      // 如果本地纹理加载失败，使用程序化纹理作为备用
      material.map = createFallbackEarthTexture()
      material.needsUpdate = true
    }
  )
  material.map = earthTexture
  
  // 加载本地地球法线贴图
  const normalTexture = textureLoader.load(
    '/textures/earth_normal_2048.jpg',
    (texture) => {
      console.log('地球法线贴图加载成功')
      material.needsUpdate = true
    },
    undefined,
    (error) => {
      console.warn('地球法线贴图加载失败:', error)
    }
  )
  material.normalMap = normalTexture
  material.normalScale = new THREE.Vector2(0.8, 0.8)  // 增强法线效果（原来是0.5）
  
  // 云层纹理已移除
  
  earth = new THREE.Mesh(geometry, material)
  earth.castShadow = true
  earth.receiveShadow = true
  scene.add(earth)
  
  // 云层已移除
  
  // 添加大气层效果
  createAtmosphere()
}

const createCloudLayer = (cloudTexture) => {
  const cloudGeometry = new THREE.SphereGeometry(1.52, 32, 32)
  const cloudMaterial = new THREE.MeshPhongMaterial({
    map: cloudTexture,
    transparent: true,
    opacity: 0.4
  })
  
  const cloudLayer = new THREE.Mesh(cloudGeometry, cloudMaterial)
  cloudLayer.userData = { rotationSpeed: 0.0005 }
  scene.add(cloudLayer)
  
  // 将云层添加到动画循环中
  if (!scene.userData.cloudLayers) {
    scene.userData.cloudLayers = []
  }
  scene.userData.cloudLayers.push(cloudLayer)
}

const createFallbackEarthTexture = () => {
  const canvas = document.createElement('canvas')
  canvas.width = 1024
  canvas.height = 512
  const ctx = canvas.getContext('2d')
  
  // 创建更真实的地球纹理
  const gradient = ctx.createLinearGradient(0, 0, 0, 512)
  gradient.addColorStop(0, '#1e3a8a')
  gradient.addColorStop(0.3, '#3b82f6')
  gradient.addColorStop(0.7, '#1e40af')
  gradient.addColorStop(1, '#0f172a')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, 1024, 512)
  
  // 添加更真实的大陆轮廓
  ctx.fillStyle = '#22c55e'
  
  // 北美洲
  ctx.beginPath()
  ctx.ellipse(200, 120, 80, 60, 0, 0, 2 * Math.PI)
  ctx.fill()
  
  // 南美洲
  ctx.beginPath()
  ctx.ellipse(250, 280, 40, 80, 0, 0, 2 * Math.PI)
  ctx.fill()
  
  // 欧洲
  ctx.beginPath()
  ctx.ellipse(480, 100, 60, 40, 0, 0, 2 * Math.PI)
  ctx.fill()
  
  // 非洲
  ctx.beginPath()
  ctx.ellipse(500, 200, 50, 100, 0, 0, 2 * Math.PI)
  ctx.fill()
  
  // 亚洲
  ctx.beginPath()
  ctx.ellipse(700, 120, 120, 80, 0, 0, 2 * Math.PI)
  ctx.fill()
  
  // 澳洲
  ctx.beginPath()
  ctx.ellipse(800, 300, 60, 40, 0, 0, 2 * Math.PI)
  ctx.fill()
  
  const texture = new THREE.CanvasTexture(canvas)
  texture.wrapS = THREE.RepeatWrapping
  texture.wrapT = THREE.RepeatWrapping
  return texture
}

const createFallbackCloudLayer = () => {
  const canvas = document.createElement('canvas')
  canvas.width = 512
  canvas.height = 256
  const ctx = canvas.getContext('2d')
  
  // 创建云层纹理
  ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
  for (let i = 0; i < 50; i++) {
    const x = Math.random() * 512
    const y = Math.random() * 256
    const size = Math.random() * 40 + 10
    ctx.beginPath()
    ctx.arc(x, y, size, 0, 2 * Math.PI)
    ctx.fill()
  }
  
  const cloudTexture = new THREE.CanvasTexture(canvas)
  createCloudLayer(cloudTexture)
}

const createAtmosphere = () => {
  const atmosphereGeometry = new THREE.SphereGeometry(1.58, 32, 32)
  const atmosphereMaterial = new THREE.MeshPhongMaterial({
    color: 0x88ccff,       // 使用更亮的蓝色
    transparent: true,
    opacity: 0.08,         // 降低透明度，避免遮挡地球（原来是0.1）
    side: THREE.BackSide
  })
  
  const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial)
  scene.add(atmosphere)
}

const createSatellites = () => {
  // 根据cmgModels动态创建卫星和空间站
  if (cmgModels.value.length === 0) {
    console.log('暂无CMG型号，跳过3D模型创建')
    return
  }
  
  console.log('开始创建3D模型，型号列表:', cmgModels.value)
  
  cmgModels.value.forEach((model, index) => {
    const modelName = model.label || ''
    console.log(`处理型号 ${index + 1}/${cmgModels.value.length}: ${modelName}`)
    
    // 判断是空间站还是卫星
    if (modelName.includes('TG')) {
      console.log(`  → 识别为空间站（包含TG）`)
      createDynamicSpaceStation(model, index)
    } else if (modelName.includes('JB')) {
      console.log(`  → 识别为卫星（包含JB）`)
      createDynamicSatellite(model, index)
    } else {
      console.log(`  → 默认创建为卫星`)
      createDynamicSatellite(model, index)
    }
  })
  
  // 不显示轨道线
  // setTimeout(() => {
  //   console.log('创建轨道线，当前卫星数量:', satellites.length)
  //   createOrbits()
  // }, 1000)
}

// 动态创建空间站（基于型号）
const createDynamicSpaceStation = (model, index) => {
  const loader = new GLTFLoader()
  const totalModels = cmgModels.value.length
  
  // 计算轨道参数
  const baseRadius = 1.8
  const radiusIncrement = 0.15
  const radius = baseRadius + index * radiusIncrement
  
  // 轨道倾角数组（提供多样性）
  const inclinations = [Math.PI / 6, Math.PI / 4, Math.PI / 3, Math.PI / 5, Math.PI / 8]
  const orbitInclination = inclinations[index % inclinations.length]
  
  loader.load(
    '/images/tiangongtS.glb',
    (gltf) => {
      const spaceStation = gltf.scene
      
      // 设置空间站属性
      spaceStation.userData = {
        modelId: model.value,
        modelName: model.label,
        name: model.label,
        type: 'space_station',
        radius: radius,
        speed: 0.002 + index * 0.0003,
        angle: (index / totalModels) * Math.PI * 2,
        orbitInclination: orbitInclination,
        isClickable: true  // 标记为可点击
      }
      
      // 缩放空间站
      spaceStation.scale.setScalar(1.5)
      
      // 设置初始位置
      const { angle, radius: r, orbitInclination: inc } = spaceStation.userData
      const x = Math.cos(angle) * r
      const y = Math.sin(angle) * r
      const z = 0
      spaceStation.position.set(
        x,
        y * Math.cos(inc) - z * Math.sin(inc),
        y * Math.sin(inc) + z * Math.cos(inc)
      )
      
      // 添加发光效果
      spaceStation.traverse((child) => {
        if (child.isMesh) {
          child.material.emissive = new THREE.Color(0x001122)
          child.material.emissiveIntensity = 0.1
          // 为每个mesh添加userData，方便点击检测
          child.userData = spaceStation.userData
        }
      })
      
      satellites.push(spaceStation)
      scene.add(spaceStation)
      console.log(`创建空间站: ${model.label}，轨道半径: ${radius.toFixed(2)}`)
    },
    (progress) => {
      console.log(`空间站${model.label}加载进度:`, (progress.loaded / progress.total * 100) + '%')
    },
    (error) => {
      console.error(`空间站${model.label}加载失败:`, error)
      // 如果加载失败，创建简单的空间站模型
      createFallbackModel(model, index, 'space_station')
    }
  )
}

// 动态创建卫星（基于型号）
const createDynamicSatellite = (model, index) => {
  const loader = new GLTFLoader()
  const totalModels = cmgModels.value.length
  
  // 计算轨道参数
  const baseRadius = 2.0
  const radiusIncrement = 0.15
  const radius = baseRadius + index * radiusIncrement
  
  // 轨道倾角数组
  const inclinations = [Math.PI / 12, Math.PI / 4, Math.PI / 3, Math.PI / 2.5, Math.PI / 8]
  const orbitInclination = inclinations[index % inclinations.length]
  
  // 卫星颜色数组
  const colors = [0x22c55e, 0xf59e0b, 0xef4444, 0x8b5cf6, 0x06b6d4]
  const color = colors[index % colors.length]
  
  loader.load(
    '/images/glbfile.glb',
    (gltf) => {
      const satellite = gltf.scene
      
      // 设置卫星属性
      satellite.userData = {
        modelId: model.value,
        modelName: model.label,
        name: model.label,
        type: 'satellite',
        radius: radius,
        speed: 0.002 + index * 0.0003,
        angle: (index / totalModels) * Math.PI * 2,
        orbitInclination: orbitInclination,
        color: color,
        isClickable: true  // 标记为可点击
      }
      
      // 缩放卫星
      satellite.scale.setScalar(0.08)
      
      // 设置初始位置
      const { angle, radius: r, orbitInclination: inc } = satellite.userData
      const x = Math.cos(angle) * r
      const y = Math.sin(angle) * r
      const z = 0
      satellite.position.set(
        x,
        y * Math.cos(inc) - z * Math.sin(inc),
        y * Math.sin(inc) + z * Math.cos(inc)
      )
      
      // 添加发光效果
      satellite.traverse((child) => {
        if (child.isMesh) {
          child.material.emissive = new THREE.Color(color)
          child.material.emissiveIntensity = 0.05
          // 为每个mesh添加userData
          child.userData = satellite.userData
        }
      })
      
      satellites.push(satellite)
      scene.add(satellite)
      console.log(`创建卫星: ${model.label}，轨道半径: ${radius.toFixed(2)}`)
    },
    (progress) => {
      console.log(`卫星${model.label}加载进度:`, (progress.loaded / progress.total * 100) + '%')
    },
    (error) => {
      console.error(`卫星${model.label}加载失败:`, error)
      // 如果加载失败，创建简单的卫星模型
      createFallbackModel(model, index, 'satellite')
    }
  )
}

// 创建备用简单模型
const createFallbackModel = (model, index, type) => {
  const totalModels = cmgModels.value.length
  const baseRadius = type === 'space_station' ? 1.8 : 2.0
  const radiusIncrement = 0.15
  const radius = baseRadius + index * radiusIncrement
  
  const inclinations = [Math.PI / 12, Math.PI / 4, Math.PI / 3, Math.PI / 2.5, Math.PI / 8]
  const orbitInclination = inclinations[index % inclinations.length]
  
  const colors = [0x22c55e, 0xf59e0b, 0xef4444, 0x8b5cf6, 0x06b6d4]
  const color = colors[index % colors.length]
  
  const fallbackModel = createSatelliteModel(type, color)
  fallbackModel.userData = {
    modelId: model.value,
    modelName: model.label,
    name: model.label,
    type: type,
    radius: radius,
    speed: 0.002 + index * 0.0003,
    angle: (index / totalModels) * Math.PI * 2,
    orbitInclination: orbitInclination,
    color: color,
    isClickable: true
  }
  
  // 设置初始位置
  const { angle, radius: r, orbitInclination: inc } = fallbackModel.userData
  const x = Math.cos(angle) * r
  const y = Math.sin(angle) * r
  const z = 0
  fallbackModel.position.set(
    x,
    y * Math.cos(inc) - z * Math.sin(inc),
    y * Math.sin(inc) + z * Math.cos(inc)
  )
  
  satellites.push(fallbackModel)
  scene.add(fallbackModel)
  console.log(`创建备用${type === 'space_station' ? '空间站' : '卫星'}: ${model.label}`)
}

const createRealSpaceStation = () => {
  const loader = new GLTFLoader()
  
  loader.load(
    '/images/tiangongtS.glb',
    (gltf) => {
      const spaceStation = gltf.scene
      
      // 设置空间站属性
      spaceStation.userData = {
        name: '天宫空间站',
        type: 'space_station',
        radius: 1.8,  // 减小轨道半径（原2.5）
        speed: 0.003,
        angle: 0,
        orbitInclination: Math.PI / 6 // 轨道倾角30度
      }
      
      // 缩放空间站到合适大小 - 通过这个参数控制大小
      spaceStation.scale.setScalar(0.002)
      
      // 设置初始位置（考虑轨道倾角）- 与animate函数逻辑一致
      const { angle, radius, orbitInclination } = spaceStation.userData
      const x = Math.cos(angle) * radius
      const y = Math.sin(angle) * radius
      const z = 0
      spaceStation.position.set(
        x,
        y * Math.cos(orbitInclination) - z * Math.sin(orbitInclination),
        y * Math.sin(orbitInclination) + z * Math.cos(orbitInclination)
      )
      
      // 添加发光效果
      spaceStation.traverse((child) => {
        if (child.isMesh) {
          child.material.emissive = new THREE.Color(0x001122)
          child.material.emissiveIntensity = 0.1
        }
      })
      
      satellites.push(spaceStation)
      scene.add(spaceStation)
    },
    (progress) => {
      console.log('天宫空间站加载进度:', (progress.loaded / progress.total * 100) + '%')
    },
    (error) => {
      console.error('天宫空间站模型加载失败:', error)
      // 如果加载失败，创建一个简单的空间站作为备用
      createFallbackSpaceStation()
    }
  )
}

const createFallbackSpaceStation = () => {
  const group = new THREE.Group()
  
  // 简单的空间站结构
  const coreGeometry = new THREE.CylinderGeometry(0.1, 0.1, 0.8, 12)
  const coreMaterial = new THREE.MeshPhongMaterial({ color: 0x4a90e2 })
  const core = new THREE.Mesh(coreGeometry, coreMaterial)
  group.add(core)
  
  const solarPanelGeometry = new THREE.BoxGeometry(1.2, 0.02, 0.6)
  const solarMaterial = new THREE.MeshPhongMaterial({ color: 0x1a1a1a })
  
  const leftPanel = new THREE.Mesh(solarPanelGeometry, solarMaterial)
  leftPanel.position.set(0.7, 0, 0)
  group.add(leftPanel)
  
  const rightPanel = new THREE.Mesh(solarPanelGeometry, solarMaterial)
  rightPanel.position.set(-0.7, 0, 0)
  group.add(rightPanel)
  
  group.userData = {
    name: '天宫空间站',
    type: 'space_station',
    radius: 1.8,  // 减小轨道半径（原2.5）
    speed: 0.003,
    angle: 0,
    orbitInclination: Math.PI / 6 // 轨道倾角30度
  }
  
  const { angle, radius, orbitInclination } = group.userData
  const x = Math.cos(angle) * radius
  const y = Math.sin(angle) * radius
  const z = 0
  group.position.set(
    x,
    y * Math.cos(orbitInclination) - z * Math.sin(orbitInclination),
    y * Math.sin(orbitInclination) + z * Math.cos(orbitInclination)
  )
  
  satellites.push(group)
  scene.add(group)
}

const createSimpleSatellites = () => {
  const satelliteCount = 4
  const satelliteTypes = [
    { name: '北斗卫星', type: 'navigation', color: 0x22c55e },
    { name: '风云卫星', type: 'weather', color: 0xf59e0b },
    { name: '通信卫星', type: 'communication', color: 0xef4444 },
    { name: '科学卫星', type: 'science', color: 0x8b5cf6 }
  ]
  
  for (let i = 0; i < satelliteCount; i++) {
    const satelliteInfo = satelliteTypes[i]
    createRealSatellite(satelliteInfo, i, satelliteCount)
  }
}

const createRealSatellite = (satelliteInfo, index, totalCount) => {
  const loader = new GLTFLoader()
  
  loader.load(
    '/images/glbfile.glb',
    (gltf) => {
      const satellite = gltf.scene
      
      // 设置卫星属性，每个卫星有不同的轨道倾角
      const orbitInclinations = [Math.PI / 12, Math.PI / 4, Math.PI / 3, Math.PI / 2.5] // 15度、45度、60度、72度
      satellite.userData = { 
        name: satelliteInfo.name,
        type: satelliteInfo.type,
        radius: 2.0 + index * 0.2, // 减小轨道半径：2.0, 2.2, 2.4, 2.6（原3.0-3.9）
        speed: 0.002 + index * 0.0005, // 速度递增
        angle: (index / totalCount) * Math.PI * 2,
        orbitInclination: orbitInclinations[index] // 不同的轨道倾角
      }
      
      // 缩放卫星到合适大小 - 通过这个参数控制大小
      satellite.scale.setScalar(0.1)
      
      // 设置初始位置（考虑轨道倾角）- 与animate函数逻辑一致
      const { angle, radius, orbitInclination } = satellite.userData
      const x = Math.cos(angle) * radius
      const y = Math.sin(angle) * radius
      const z = 0
      satellite.position.set(
        x,
        y * Math.cos(orbitInclination) - z * Math.sin(orbitInclination),
        y * Math.sin(orbitInclination) + z * Math.cos(orbitInclination)
      )
      
      // 添加发光效果
      satellite.traverse((child) => {
        if (child.isMesh) {
          child.material.emissive = new THREE.Color(satelliteInfo.color)
          child.material.emissiveIntensity = 0.05
        }
      })
      
      satellites.push(satellite)
      scene.add(satellite)
    },
    (progress) => {
      console.log(`卫星${satelliteInfo.name}加载进度:`, (progress.loaded / progress.total * 100) + '%')
    },
    (error) => {
      console.error(`卫星${satelliteInfo.name}加载失败:`, error)
      // 如果加载失败，创建一个简单的卫星作为备用
      const orbitInclinations = [Math.PI / 12, Math.PI / 4, Math.PI / 3, Math.PI / 2.5]
      const fallbackSatellite = createSatelliteModel(satelliteInfo.type, satelliteInfo.color)
      fallbackSatellite.userData = { 
        name: satelliteInfo.name,
        type: satelliteInfo.type,
        radius: 2.0 + index * 0.2,  // 减小轨道半径：2.0, 2.2, 2.4, 2.6（原3.0-3.9）
        speed: 0.002 + index * 0.0005,
        angle: (index / totalCount) * Math.PI * 2,
        orbitInclination: orbitInclinations[index]
      }
      
      const { angle, radius, orbitInclination } = fallbackSatellite.userData
      const x = Math.cos(angle) * radius
      const y = Math.sin(angle) * radius
      const z = 0
      fallbackSatellite.position.set(
        x,
        y * Math.cos(orbitInclination) - z * Math.sin(orbitInclination),
        y * Math.sin(orbitInclination) + z * Math.cos(orbitInclination)
      )
      
      satellites.push(fallbackSatellite)
      scene.add(fallbackSatellite)
    }
  )
}

const createSatelliteModel = (type, color) => {
  const group = new THREE.Group()
  
  switch (type) {
    case 'space_station':
      // 天宫空间站 - 更真实的结构
      // 核心舱
      const coreModule = new THREE.CylinderGeometry(0.15, 0.15, 0.6, 12)
      const coreMaterial = new THREE.MeshPhongMaterial({ color: 0x4a90e2 })
      const core = new THREE.Mesh(coreModule, coreMaterial)
      group.add(core)
      
      // 实验舱
      const labModule = new THREE.CylinderGeometry(0.12, 0.12, 0.4, 12)
      const labMaterial = new THREE.MeshPhongMaterial({ color: 0x3b82f6 })
      const lab = new THREE.Mesh(labModule, labMaterial)
      lab.position.set(0.5, 0, 0)
      group.add(lab)
      
      // 太阳能板 - 更真实的形状
      const solarPanelGeometry = new THREE.BoxGeometry(0.8, 0.02, 0.4)
      const solarMaterial = new THREE.MeshPhongMaterial({ color: 0x1a1a1a })
      
      const leftPanel = new THREE.Mesh(solarPanelGeometry, solarMaterial)
      leftPanel.position.set(0.6, 0, 0)
      group.add(leftPanel)
      
      const rightPanel = new THREE.Mesh(solarPanelGeometry, solarMaterial)
      rightPanel.position.set(-0.6, 0, 0)
      group.add(rightPanel)
      
      // 机械臂
      const armGeometry = new THREE.CylinderGeometry(0.02, 0.02, 0.3, 8)
      const armMaterial = new THREE.MeshPhongMaterial({ color: 0x666666 })
      const arm = new THREE.Mesh(armGeometry, armMaterial)
      arm.position.set(0.2, 0, 0.3)
      arm.rotation.z = Math.PI / 4
      group.add(arm)
      
      // 对接舱
      const dockGeometry = new THREE.CylinderGeometry(0.08, 0.08, 0.15, 8)
      const dockMaterial = new THREE.MeshPhongMaterial({ color: 0x888888 })
      const dock = new THREE.Mesh(dockGeometry, dockMaterial)
      dock.position.set(0, 0, 0.4)
      group.add(dock)
      break
      
    case 'navigation':
      // 北斗导航卫星 - 更真实的设计
      const navBody = new THREE.BoxGeometry(0.25, 0.2, 0.4)
      const navMaterial = new THREE.MeshPhongMaterial({ color: 0x22c55e })
      const navMesh = new THREE.Mesh(navBody, navMaterial)
      group.add(navMesh)
      
      // 太阳能板
      const navPanelGeometry = new THREE.BoxGeometry(0.6, 0.02, 0.3)
      const navPanelMaterial = new THREE.MeshPhongMaterial({ color: 0x1a1a1a })
      const navLeftPanel = new THREE.Mesh(navPanelGeometry, navPanelMaterial)
      navLeftPanel.position.set(0.4, 0, 0)
      group.add(navLeftPanel)
      
      const navRightPanel = new THREE.Mesh(navPanelGeometry, navPanelMaterial)
      navRightPanel.position.set(-0.4, 0, 0)
      group.add(navRightPanel)
      
      // 导航天线阵列
      for (let i = 0; i < 4; i++) {
        const antennaGeometry = new THREE.CylinderGeometry(0.01, 0.01, 0.2, 6)
        const antennaMaterial = new THREE.MeshPhongMaterial({ color: 0x888888 })
        const antenna = new THREE.Mesh(antennaGeometry, antennaMaterial)
        antenna.position.set((i - 1.5) * 0.1, 0, 0.25)
        group.add(antenna)
      }
      break
      
    case 'weather':
      // 风云气象卫星
      const weatherBody = new THREE.CylinderGeometry(0.12, 0.12, 0.5, 12)
      const weatherMaterial = new THREE.MeshPhongMaterial({ color: 0xf59e0b })
      const weatherMesh = new THREE.Mesh(weatherBody, weatherMaterial)
      group.add(weatherMesh)
      
      // 圆形太阳能板
      const weatherPanelGeometry = new THREE.CylinderGeometry(0.3, 0.3, 0.02, 16)
      const weatherPanelMaterial = new THREE.MeshPhongMaterial({ color: 0x1a1a1a })
      const weatherTopPanel = new THREE.Mesh(weatherPanelGeometry, weatherPanelMaterial)
      weatherTopPanel.position.set(0, 0.25, 0)
      group.add(weatherTopPanel)
      
      const weatherBottomPanel = new THREE.Mesh(weatherPanelGeometry, weatherPanelMaterial)
      weatherBottomPanel.position.set(0, -0.25, 0)
      group.add(weatherBottomPanel)
      
      // 气象传感器
      const sensorGeometry = new THREE.SphereGeometry(0.05, 8, 8)
      const sensorMaterial = new THREE.MeshPhongMaterial({ color: 0x666666 })
      const sensor = new THREE.Mesh(sensorGeometry, sensorMaterial)
      sensor.position.set(0, 0, 0.3)
      group.add(sensor)
      break
      
    case 'communication':
      // 通信卫星
      const commBody = new THREE.BoxGeometry(0.3, 0.25, 0.4)
      const commMaterial = new THREE.MeshPhongMaterial({ color: 0xef4444 })
      const commMesh = new THREE.Mesh(commBody, commMaterial)
      group.add(commMesh)
      
      // 大型太阳能板
      const commPanelGeometry = new THREE.BoxGeometry(0.8, 0.02, 0.4)
      const commPanelMaterial = new THREE.MeshPhongMaterial({ color: 0x1a1a1a })
      const commLeftPanel = new THREE.Mesh(commPanelGeometry, commPanelMaterial)
      commLeftPanel.position.set(0.5, 0, 0)
      group.add(commLeftPanel)
      
      const commRightPanel = new THREE.Mesh(commPanelGeometry, commPanelMaterial)
      commRightPanel.position.set(-0.5, 0, 0)
      group.add(commRightPanel)
      
      // 通信天线
      const commAntennaGeometry = new THREE.CylinderGeometry(0.15, 0.15, 0.1, 12)
      const commAntennaMaterial = new THREE.MeshPhongMaterial({ color: 0x888888 })
      const commAntenna = new THREE.Mesh(commAntennaGeometry, commAntennaMaterial)
      commAntenna.position.set(0, 0, 0.25)
      group.add(commAntenna)
      break
      
    case 'science':
    case 'reconnaissance':
      // 科学/侦察卫星 - 圆柱体带太阳能板
      const cylinderBody = new THREE.CylinderGeometry(0.1, 0.1, 0.4, 8)
      const cylinderMaterial = new THREE.MeshPhongMaterial({ color: color })
      const cylinderMesh = new THREE.Mesh(cylinderBody, cylinderMaterial)
      group.add(cylinderMesh)
      
      // 圆形太阳能板
      const circularPanel = new THREE.CylinderGeometry(0.25, 0.25, 0.02, 16)
      const circularMaterial = new THREE.MeshPhongMaterial({ color: 0x1a1a1a })
      const topPanel = new THREE.Mesh(circularPanel, circularMaterial)
      topPanel.position.set(0, 0.2, 0)
      group.add(topPanel)
      
      const bottomPanel = new THREE.Mesh(circularPanel, circularMaterial)
      bottomPanel.position.set(0, -0.2, 0)
      group.add(bottomPanel)
      break
      
    default:
      // 默认卫星 - 简单立方体
      const defaultGeometry = new THREE.BoxGeometry(0.15, 0.15, 0.25)
      const defaultMaterial = new THREE.MeshPhongMaterial({ color: color })
      const defaultMesh = new THREE.Mesh(defaultGeometry, defaultMaterial)
      group.add(defaultMesh)
      
      // 简单太阳能板
      const simplePanel = new THREE.BoxGeometry(0.3, 0.02, 0.15)
      const simplePanelMaterial = new THREE.MeshPhongMaterial({ color: 0x1a1a1a })
      const leftSimplePanel = new THREE.Mesh(simplePanel, simplePanelMaterial)
      leftSimplePanel.position.set(0.2, 0, 0)
      group.add(leftSimplePanel)
      
      const rightSimplePanel = new THREE.Mesh(simplePanel, simplePanelMaterial)
      rightSimplePanel.position.set(-0.2, 0, 0)
      group.add(rightSimplePanel)
  }
  
  // 添加发光效果
  const glowGeometry = new THREE.SphereGeometry(0.3, 16, 16)
  const glowMaterial = new THREE.MeshBasicMaterial({
    color: color,
    transparent: true,
    opacity: 0.1,
    side: THREE.BackSide
  })
  const glow = new THREE.Mesh(glowGeometry, glowMaterial)
  group.add(glow)
  
  return group
}

const createOrbits = () => {
  satellites.forEach((satellite, index) => {
    const { radius, type, orbitInclination } = satellite.userData
    
    // 根据类型设置不同的轨道样式
    let orbitColor = 0xffffff
    let orbitOpacity = 0.4
    let orbitWidth = 0.02
    
    if (type === 'space_station') {
      orbitColor = 0x4a90e2 // 蓝色轨道
      orbitOpacity = 0.5
      orbitWidth = 0.03
    } else {
      // 为不同类型的卫星设置不同颜色
      const colors = [0x22c55e, 0xf59e0b, 0xef4444, 0x8b5cf6]
      orbitColor = colors[index % colors.length]
      orbitOpacity = 0.45
    }
    
    // 使用TorusGeometry创建圆环轨道
    const orbitGeometry = new THREE.TorusGeometry(radius, orbitWidth, 16, 100)
    const orbitMaterial = new THREE.MeshBasicMaterial({
      color: orbitColor,
      transparent: true,
      opacity: orbitOpacity
    })
    
    const orbit = new THREE.Mesh(orbitGeometry, orbitMaterial)
    
    // 根据轨道倾角旋转轨道
    orbit.rotation.x = orbitInclination || 0
    orbit.rotation.y = (index * Math.PI / 8) // 每个轨道有不同的旋转角度，更好地分散
    
    scene.add(orbit)
  })
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  
  if (isAnimating.value) {
    // 地球自转
    if (earth) {
      earth.rotation.y += 0.005
    }
    
    // 云层已移除
    
    // 卫星轨道运动 - 正确的圆形轨道，围绕地球中心旋转
    satellites.forEach(satellite => {
      const { radius, speed, orbitInclination } = satellite.userData
      satellite.userData.angle += speed
      
      const angle = satellite.userData.angle
      
      // 先在XY平面计算标准圆形轨道（地球在原点）
      const x = Math.cos(angle) * radius
      const y = Math.sin(angle) * radius
      const z = 0
      
      // 应用轨道倾角：绕X轴旋转
      satellite.position.set(
        x,
        y * Math.cos(orbitInclination) - z * Math.sin(orbitInclination),
        y * Math.sin(orbitInclination) + z * Math.cos(orbitInclination)
      )
      
      // 卫星自转（朝向运动方向）
      satellite.rotation.y += 0.005
    })
  }
  
  renderer.render(scene, camera)
}

// 3D模型点击检测
const onModelClick = async (event) => {
  if (!raycaster || !mouse) return
  
  // 计算鼠标位置
  const rect = renderer.domElement.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  
  // 更新raycaster
  raycaster.setFromCamera(mouse, camera)
  
  // 检测与卫星/空间站的交互
  const intersects = raycaster.intersectObjects(satellites, true)
  
  if (intersects.length > 0) {
    const clickedObject = intersects[0].object
    const userData = clickedObject.userData
    
    if (userData && userData.isClickable) {
      console.log('点击了3D模型:', userData.name)
      
      // 获取该型号下所有个体数据
      let instances = modelInstances.value[userData.modelId] || []
      
      // 如果还没加载，则加载
      if (instances.length === 0) {
        await fetchCmgIndividuals(userData.modelId)
        instances = modelInstances.value[userData.modelId] || []
      }
      
      // 设置选中的模型信息
      selected3DModel.value = {
        name: userData.name,
        type: userData.type,
        modelId: userData.modelId,
        modelName: userData.modelName,
        instances: instances  // 包含所有个体数据
      }
      
      console.log('该型号下的个体数量:', instances.length)
      
      // 显示弹窗
      show3DModelDialog.value = true
    }
  }
}

// 处理窗口大小变化
const handleResize = () => {
  if (camera && renderer) {
    const container = document.querySelector('.earth-container')
    camera.aspect = container.clientWidth / container.clientHeight
    camera.updateProjectionMatrix()
    renderer.setSize(container.clientWidth, container.clientHeight)
  }
}

// 调试函数：检查样式表加载情况
function debugStyleSheets() {
  console.log('=== 页面加载的样式表调试信息 ===');
  console.log('样式表总数:', document.styleSheets.length);
  
  for (let i = 0; i < document.styleSheets.length; i++) {
    const sheet = document.styleSheets[i];
    console.log(`样式表 ${i}:`, sheet.href || '内联样式');
    
    try {
      // 查找与对话框相关的规则
      const rules = sheet.cssRules || sheet.rules;
      if (rules) {
        for (let j = 0; j < rules.length; j++) {
          const rule = rules[j];
          if (rule.selectorText && 
              (rule.selectorText.includes('time-selector-dialog') || 
               rule.selectorText.includes('bigscreen-detail-dialog') ||
               rule.selectorText.includes('.el-dialog'))) {
            console.log('  找到相关规则:', rule.selectorText);
            console.log('    background:', rule.style.backgroundColor || rule.style.background);
          }
        }
      }
    } catch (e) {
      console.log('  无法访问该样式表规则（跨域限制）');
    }
  }
  console.log('===================================');
}

// ==================== 遥测数据相关函数 ====================

// 获取可用的遥测量参数
async function fetchAvailableTelemetryParameters() {
  if (!selectedAnomalyFrame.value?.id) {
    return;
  }
  
  console.log('开始获取遥测量参数，异常帧ID:', selectedAnomalyFrame.value.id);
  
  try {
    const url = `/api/v1/data/detection-overview/?action=telemetry_data&frame_id=${selectedAnomalyFrame.value.id}&frames_before=1&frames_after=1`;
    const response = await fetch(url);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('错误响应内容:', errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    availableTelemetryParameters.value = data.available_parameters || [];
    console.log('可用遥测量参数:', availableTelemetryParameters.value);
  } catch (error) {
    console.error('获取遥测量参数失败:', error);
  }
}

// 加载遥测数据
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
    console.log('遥测数据响应:', data);
    
    // 处理遥测数据并生成图表
    processInlineTelemetryData(data);
    
    ElMessage.success(`成功获取 ${data.total_frames} 帧遥测数据`);
  } catch (error) {
    console.error('获取遥测数据失败:', error);
    ElMessage.error('获取遥测数据失败');
  } finally {
    telemetryLoading.value = false;
  }
}

// 处理遥测数据并生成图表
function processInlineTelemetryData(data) {
  console.log('开始处理遥测数据:', data);
  telemetryCharts.value = [];
  
  // 为每个选中的遥测量创建图表数据
  selectedTelemetryParameters.value.forEach(parameter => {
    const dataPoints = [];
    const timestamps = [];
    
    data.telemetry_data.forEach((point, index) => {
      if (point.parameters[parameter] !== null && point.parameters[parameter] !== undefined) {
        dataPoints.push(point.parameters[parameter]);
        timestamps.push(point.timestamp);
      }
    });
    
    if (dataPoints.length > 0) {
      const targetIndex = data.telemetry_data.findIndex(p => p.is_target);
      
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
    renderInlineTelemetryCharts();
  }, 100);
}

// 渲染遥测图表
function renderInlineTelemetryCharts() {
  console.log('开始渲染遥测图表，图表数量:', telemetryCharts.value.length);
  
  telemetryCharts.value.forEach((chart, index) => {
    const chartId = `inline-chart-${chart.parameter}`;
    const chartElement = document.getElementById(chartId);
    
    if (!chartElement) {
      console.warn(`图表容器未找到: ${chartId}`);
      return;
    }
    
    // 销毁已存在的图表实例
    if (telemetryChartInstances.value[chart.parameter]) {
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
        color: index === chart.targetIndex ? '#ff4d4f' : '#60a5fa'  // 异常帧用红色，其他用浅蓝色
      }
    }));
    
    // 配置图表选项
    const option = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(30, 58, 138, 0.9)',
        borderColor: 'rgba(147, 197, 253, 0.5)',
        textStyle: {
          color: '#ffffff'
        },
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
      // Y轴数据缩放滑块（侧边）
      dataZoom: [{
        type: 'slider',
        yAxisIndex: 0,
        show: true,
        right: '2%',
        width: 15,
        start: 0,
        end: 100,
        backgroundColor: 'rgba(30, 58, 138, 0.3)',
        fillerColor: 'rgba(96, 165, 250, 0.3)',
        borderColor: 'rgba(147, 197, 253, 0.3)',
        handleStyle: {
          color: 'rgba(96, 165, 250, 0.8)'
        },
        textStyle: {
          color: '#ffffff',
          fontSize: 10
        },
        moveHandleSize: 5
      }, {
        type: 'inside',
        yAxisIndex: 0,
        zoomOnMouseWheel: true,
        moveOnMouseMove: false,
        moveOnMouseWheel: true
      }],
      grid: {
        left: '8%',
        right: '8%',  // 增加右边距为滑块留空间
        top: '10%',
        bottom: '15%',
        containLabel: false
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        axisLabel: {
          rotate: 30,
          fontSize: 9,
          color: '#ffffff'
        },
        axisLine: {
          lineStyle: {
            color: 'rgba(147, 197, 253, 0.3)'
          }
        }
      },
      yAxis: {
        type: 'value',
        scale: true,  // 核心：允许Y轴根据数据动态缩放，不局限于从0开始
        axisLabel: {
          fontSize: 9,
          color: '#ffffff'
        },
        axisLine: {
          lineStyle: {
            color: 'rgba(147, 197, 253, 0.3)'
          }
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(147, 197, 253, 0.1)'
          }
        }
      },
      series: [{
        name: chart.parameter,
        type: 'line',
        data: seriesData,
        smooth: true,
        lineStyle: {
          color: '#60a5fa',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0,
              color: 'rgba(96, 165, 250, 0.3)'
            }, {
              offset: 1,
              color: 'rgba(96, 165, 250, 0.05)'
            }]
          }
        },
        // 添加目标帧标记线
        markLine: chart.targetIndex >= 0 ? {
          symbol: 'none',
          label: {
            show: true,
            position: 'end',
            formatter: '目标帧',
            color: '#ffffff',
            fontSize: 10
          },
          lineStyle: {
            type: 'solid',
            color: '#ff4d4f',
            width: 2
          },
          data: [{
            xAxis: chart.targetIndex,
            name: '目标帧'
          }]
        } : undefined
      }]
    };
    
    chartInstance.setOption(option);
  });
}

// 全屏状态变化监听
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
  console.log('全屏状态变化:', isFullscreen.value)
}

// 生命周期
onMounted(async () => {
  updateTime()
  setInterval(updateTime, 1000)
  
  window.addEventListener('resize', handleResize)
  
  // 监听全屏状态变化（用户按ESC退出全屏时更新状态）
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.addEventListener('mozfullscreenchange', handleFullscreenChange)
  document.addEventListener('MSFullscreenChange', handleFullscreenChange)
  
  // 先加载CMG型号数据
  await fetchCmgModels()
  
  console.log('型号数据加载完成，开始初始化3D场景')
  console.log('cmgModels:', cmgModels.value)
  
  // 然后初始化Three.js场景（包括创建卫星）
  nextTick(() => {
    initThreeJS()
    
    // 在Three.js初始化后创建卫星
    setTimeout(() => {
      console.log('准备创建卫星，型号数量:', cmgModels.value.length)
      createSatellites()
    }, 100)
  })
  
  // 调试：检查样式表
  setTimeout(() => {
    debugStyleSheets();
  }, 1000);
  
  // 延迟初始化寿命趋势图容器（确保DOM完全渲染）
  setTimeout(() => {
    if (lifetimeChartRef.value && !lifetimeChart) {
      console.log('页面加载完成，初始化寿命趋势图容器')
      initLifetimeChart()
    }
  }, 2000);
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (renderer) {
    renderer.dispose()
  }
  if (lifetimeChart) {
    lifetimeChart.dispose()
  }
  window.removeEventListener('resize', handleResize)
  
  // 移除全屏状态监听
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.removeEventListener('mozfullscreenchange', handleFullscreenChange)
  document.removeEventListener('MSFullscreenChange', handleFullscreenChange)
})
</script>

<style scoped>
.big-screen-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #000011;
  color: #ffffff;
  font-family: 'Microsoft YaHei', sans-serif;
  overflow: hidden;
  z-index: 9999;
}

/* 宇宙背景 - 纯粹的宇宙图像 */
.universe-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  background: 
    url('/images/stars-galaxy-3440x1440-10307.jpg') center/cover no-repeat;
  background-attachment: fixed;
}

.stars-field {
  display: none;
}

.nebula-overlay {
  display: none;
}

.grid-overlay {
  display: none;
}

/* 顶部标题栏 */
.top-header {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 30px;  /* 减少上下内边距，从20px改为12px */
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 255, 255, 0.3);
  z-index: 10;
}

.system-title {
  font-size: 24px;  /* 减小字体，从28px改为24px */
  font-weight: 700;
  margin: 0;
  background: linear-gradient(45deg, #00ffff, #0080ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: flex;
  align-items: center;
  gap: 12px;  /* 减少间距，从15px改为12px */
}

.title-icon {
  font-size: 26px;  /* 减小图标，从32px改为26px */
  filter: drop-shadow(0 0 10px rgba(0, 255, 255, 0.5));
}

.time-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time-label {
  font-size: 14px;  /* 减小字体，从16px改为14px */
  font-weight: 500;
  color: #93c5fd;
}

.current-time {
  font-size: 16px;  /* 减小字体，从18px改为16px */
  font-weight: 600;
  color: #00ffff;
}

/* 主内容区域 */
.main-content {
  display: flex;
  height: calc(100vh - 90px);  /* 优化高度，避免与底部管理区域重叠 */
  gap: 20px;
  padding: 20px;
}

/* 左侧面板 */
.left-panel {
  width: 450px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(0, 255, 255, 0.2);
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
  color: #00ffff;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #4CAF50;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4CAF50;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.category-section {
  margin-bottom: 15px;
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: rgba(0, 255, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.category-header:hover {
  background: rgba(0, 255, 255, 0.2);
}

.category-title {
  font-weight: 600;
  color: #ffffff;
}

.expand-icon {
  transition: transform 0.3s ease;
  color: #00ffff;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.category-content {
  margin-top: 10px;
}

.cmg-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.cmg-item:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(0, 255, 255, 0.3);
}

.cmg-item.selected {
  background: rgba(0, 255, 255, 0.2);
  border-color: #00ffff;
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
}

.cmg-icon {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 0 10px currentColor;
}

.cmg-name {
  flex: 1;
  font-weight: 500;
  color: #ffffff;
}

.cmg-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.1);
  color: #cccccc;
}

/* 中央3D展示区 */
.center-panel {
  flex: 1;
  position: relative;
  background: transparent;
  overflow: hidden;
}

.earth-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: transparent;
  z-index: 100;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(0, 255, 255, 0.3);
  border-top: 3px solid #00ffff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.scene-controls {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  gap: 10px;
  z-index: 10;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 15px;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 8px;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
}

.control-btn:hover {
  background: rgba(0, 255, 255, 0.2);
  border-color: #00ffff;
  box-shadow: 0 0 15px rgba(0, 255, 255, 0.3);
}

.btn-icon {
  font-size: 16px;
}

/* 右侧面板 */
.right-panel {
  width: 450px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.data-panel,
.health-panel,
.lifetime-panel,
.msfg-inference-panel,
.lifetime-update-panel {
  background: rgba(59, 130, 246, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 15px;
  padding: 20px;
}

.msfg-inference-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-height: 50%;
}

.msfg-inference-panel .panel-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.lifetime-update-panel {
  flex: 1;
  max-height: 50%;
}

.panel-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00ffff;
  animation: pulse 2s infinite;
}

.chart-placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 255, 255, 0.05);
  border-radius: 10px;
  border: 2px dashed rgba(0, 255, 255, 0.3);
}

.placeholder-content {
  text-align: center;
  color: #888;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 10px;
  opacity: 0.5;
}

.health-metrics {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-label {
  font-size: 14px;
  color: #cccccc;
}

.metric-value {
  display: flex;
  align-items: center;
  gap: 15px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
  box-shadow: 0 0 10px currentColor;
}

.metric-text {
  font-size: 12px;
  color: #ffffff;
  min-width: 80px;
}

.lifetime-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.lifetime-item {
  text-align: center;
}

.lifetime-label {
  font-size: 14px;
  color: #cccccc;
  margin-bottom: 10px;
}

.lifetime-value {
  font-size: 24px;
  font-weight: 700;
  color: #00ffff;
  margin-bottom: 15px;
}

.progress-circle {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, #00ffff var(--progress, 0%), rgba(255, 255, 255, 0.1) var(--progress, 0%));
  display: flex;
  align-items: center;
  justify-content: center;
}

.circle-fill {
  position: absolute;
  top: 5px;
  left: 5px;
  right: 5px;
  bottom: 5px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.circle-text {
  font-size: 14px;
  font-weight: 600;
  color: #00ffff;
}

/* MSFG部件推理结果样式 */
.msfg-components-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
  margin-top: 10px;
  overflow-y: auto;
  flex: 1;
  padding: 10px 5px;
  align-content: flex-start;
}

.component-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 15px 10px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 90px;
  backdrop-filter: blur(5px);
}

.component-box:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 255, 255, 0.2);
  border-color: rgba(0, 255, 255, 0.4);
}

.component-box .component-name {
  font-size: 13px;
  color: #ffffff;
  font-weight: 500;
  text-align: center;
  margin-bottom: 8px;
  word-break: break-word;
  line-height: 1.3;
}

.component-box .component-score {
  font-size: 18px;
  font-weight: 700;
  text-shadow: 0 0 8px currentColor;
}

.no-data-hint {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px 20px;
}

/* 底部控制栏 */
.bottom-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(15px);
  border-top: 1px solid rgba(0, 255, 255, 0.3);
  z-index: 10;
}

.control-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.control-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.timeline-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.timeline-btn {
  width: 40px;
  height: 40px;
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.timeline-btn:hover {
  background: rgba(0, 255, 255, 0.2);
  border-color: #00ffff;
}

.timeline-progress {
  display: flex;
  align-items: center;
  gap: 15px;
}

.progress-track {
  width: 200px;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  position: relative;
  cursor: pointer;
}

.progress-thumb {
  position: absolute;
  top: -6px;
  width: 16px;
  height: 16px;
  background: #00ffff;
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
  transition: left 0.3s ease;
}

.time-display {
  font-size: 14px;
  color: #cccccc;
  min-width: 80px;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 255, 255, 0.5);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 255, 255, 0.7);
}

/* 时间选择对话框内容样式 */
.time-selector-dialog .el-dialog__title {
  color: #ffffff;
  font-weight: 600;
  font-size: 18px;
}

.time-selector-dialog .el-button {
  background: rgba(59, 130, 246, 0.6);
  border: 1px solid rgba(147, 197, 253, 0.5);
  color: #ffffff;
  font-weight: 500;
  transition: all 0.2s ease;
}

.time-selector-dialog .el-button:hover {
  background: rgba(59, 130, 246, 0.8);
  border-color: rgba(147, 197, 253, 0.7);
  color: #ffffff;
}

.time-selector-dialog .el-button--primary {
  background: rgba(96, 165, 250, 0.9);
  border: 1px solid rgba(147, 197, 253, 0.8);
  color: white;
}

.time-selector-dialog .el-button--primary:hover {
  background: rgba(96, 165, 250, 1);
  border-color: rgba(147, 197, 253, 1);
}

.timeline-info {
  margin-bottom: 20px;
  background: rgba(59, 130, 246, 0.3);
  padding: 16px;
  border-radius: 6px;
  border: 1px solid rgba(147, 197, 253, 0.3);
}

.timeline-info .el-descriptions {
  --el-descriptions-item-bordered-label-background: rgba(15, 30, 70, 0.7);  /* 深蓝色 70%透明 */
  --el-descriptions-item-bordered-content-background: rgba(10, 20, 50, 0.7); /* 更深的蓝色 70%透明 */
  --el-border-color: rgba(147, 197, 253, 0.3);
}

.timeline-info .el-descriptions__label {
  color: #ffffff !important;  /* 改为纯白色 */
  font-weight: 500;
}

.timeline-info .el-descriptions__content {
  color: #ffffff !important;
}

.timeline-slider {
  margin-top: 20px;
  padding: 20px;
  background: rgba(59, 130, 246, 0.25);
  border-radius: 6px;
  border: 1px solid rgba(147, 197, 253, 0.3);
}

.timeline-slider .el-slider__runway {
  background: rgba(30, 58, 138, 0.6);
  height: 6px;
}

.timeline-slider .el-slider__bar {
  background: rgba(96, 165, 250, 0.9);
}

.timeline-slider .el-slider__button {
  background: #60a5fa;
  border: 2px solid #93c5fd;
  width: 16px;
  height: 16px;
}

.timeline-slider .el-slider__marks-text {
  color: #ffffff !important;
  font-size: 11px;
  white-space: nowrap;
}

.fallback-time-picker {
  margin-top: 20px;
  padding: 20px;
  background: rgba(59, 130, 246, 0.25);
  border-radius: 6px;
  border: 1px solid rgba(147, 197, 253, 0.3);
}

.fallback-time-picker .el-alert {
  background: rgba(251, 191, 36, 0.2);
  border: 1px solid rgba(251, 191, 36, 0.5);
  color: #fbbf24;
}

.fallback-time-picker .el-date-editor {
  --el-fill-color-blank: rgba(30, 58, 138, 0.6);
  --el-border-color: rgba(147, 197, 253, 0.4);
  --el-text-color-regular: #ffffff;
}

.fallback-time-picker .el-input__inner {
  background: rgba(30, 58, 138, 0.6) !important;
  border-color: rgba(147, 197, 253, 0.4) !important;
  color: #ffffff !important;
}

/* 异常帧详情对话框内容样式 */

.custom-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 20px;
}

.custom-dialog-header h4 {
  color: #ffffff;
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  flex: 1;
}

.header-timestamp {
  color: #dbeafe;
  font-weight: normal;
  font-size: 15px;
  margin-left: 10px;
}

.manual-judgment-btn {
  flex-shrink: 0;
  margin-left: 20px;
}

.detail-dialog-content {
  padding: 0;
  background: transparent;
}

.main-layout-section {
  display: flex;
  gap: 20px;
  min-height: 500px;
}

.left-modules-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.bigscreen-detail-dialog .card-header {
  font-weight: bold;  /* 加粗 */
  font-size: 14px;  /* 字体稍小（原16px） */
  color: #ffffff;
  line-height: 1.2;  /* 紧凑行高 */
}

.bigscreen-detail-dialog .ims-details-content {
  padding: 16px;
}

.bigscreen-detail-dialog .msfg-summary-content {
  padding: 16px;
}

/* Element Plus 组件样式变量在全局样式中定义 */

.bigscreen-detail-dialog .msfg-top3-horizontal {
  display: flex;
  flex-direction: row;  /* 改为横向排列 */
  gap: 10px;
  flex-wrap: wrap;  /* 如果空间不够允许换行 */
}

.bigscreen-detail-dialog .msfg-item-horizontal {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(59, 130, 246, 0.25);
  border: 1px solid rgba(147, 197, 253, 0.3);
  border-radius: 6px;
  padding: 12px;
  transition: all 0.2s ease;
  flex: 1;  /* 让三个方块平均分配宽度 */
  min-width: 0;  /* 允许flex收缩 */
}

.bigscreen-detail-dialog .msfg-item-horizontal:hover {
  background: rgba(59, 130, 246, 0.35);
  border-color: rgba(147, 197, 253, 0.5);
}

.bigscreen-detail-dialog .msfg-rank {
  background: rgba(96, 165, 250, 0.8);
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.bigscreen-detail-dialog .msfg-component {
  flex: 1;
  font-weight: 500;
  color: #ffffff;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;  /* 部件名称过长时用省略号 */
}

.bigscreen-detail-dialog .msfg-score-tag {
  font-weight: 600;
  font-size: 13px;
}

.bigscreen-detail-dialog .msfg-no-data {
  text-align: center;
  color: #93c5fd;
  font-style: italic;
  padding: 16px;
  font-size: 13px;
}

/* ==================== 详情对话框布局样式 ==================== */

/* 主布局：左右布局 */
.bigscreen-detail-dialog .main-layout-section {
  display: flex;
  gap: 20px;
  align-items: stretch;
}

/* 左侧模块区域：IMS + 规则 + MSFG 垂直堆叠 */
.bigscreen-detail-dialog .left-modules-section {
  flex: 0 0 45%; /* 左侧占45%宽度 */
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 右侧遥测数据区域：高度自动等于左侧 */
.bigscreen-detail-dialog .right-telemetry-section {
  flex: 0 0 53%; /* 右侧占53%宽度 */
  display: flex;
  flex-direction: column;
}

/* 遥测数据卡片：高度填充整个右侧区域 */
.bigscreen-detail-dialog .telemetry-full-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.bigscreen-detail-dialog .telemetry-full-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 遥测内容容器 */
.bigscreen-detail-dialog .telemetry-inline-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 10px;
}

/* 遥测控制面板 */
.bigscreen-detail-dialog .telemetry-controls-inline {
  flex-shrink: 0;
  background: rgba(30, 58, 138, 0.2);
  padding: 12px;
  border-radius: 6px;
  border: 1px solid rgba(147, 197, 253, 0.3);
}

.bigscreen-detail-dialog .control-row-inline {
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.bigscreen-detail-dialog .control-item-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bigscreen-detail-dialog .control-item-inline label {
  color: #ffffff;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
}

/* 遥测图表可滚动区域 */
.bigscreen-detail-dialog .telemetry-charts-scrollable {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.bigscreen-detail-dialog .telemetry-charts-scrollable :deep(.el-scrollbar) {
  height: 100%;
}

.bigscreen-detail-dialog .telemetry-charts-scrollable :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

/* 遥测图表列表 */
.bigscreen-detail-dialog .telemetry-charts-inline {
  padding: 10px;
}

.bigscreen-detail-dialog .no-telemetry-data {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

/* 单个图表项 */
.bigscreen-detail-dialog .telemetry-chart-item-inline {
  margin-bottom: 20px;
  background: rgba(30, 58, 138, 0.15);
  border-radius: 8px;
  padding: 15px;
  border: 1px solid rgba(147, 197, 253, 0.2);
}

.bigscreen-detail-dialog .chart-header-inline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(147, 197, 253, 0.2);
}

.bigscreen-detail-dialog .chart-title-inline {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

.bigscreen-detail-dialog .chart-container-inline {
  width: 100%;
  height: 170px;  /* 降低为原始的2/3（原250px） */
}

/* 部件详情对话框样式 */
.component-detail-dialog.bigscreen-detail-dialog .el-dialog__body {
  max-height: 70vh;  /* 限制最大高度为视口高度的70% */
  overflow-y: auto;  /* 添加垂直滚动条 */
  overflow-x: hidden;  /* 隐藏水平滚动条 */
  padding-right: 15px;  /* 为滚动条留出空间 */
}

/* 自定义滚动条样式 */
.component-detail-dialog.bigscreen-detail-dialog .el-dialog__body::-webkit-scrollbar {
  width: 8px;
}

.component-detail-dialog.bigscreen-detail-dialog .el-dialog__body::-webkit-scrollbar-track {
  background: rgba(15, 30, 80, 0.3);
  border-radius: 4px;
}

.component-detail-dialog.bigscreen-detail-dialog .el-dialog__body::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.5);
  border-radius: 4px;
  transition: background 0.3s;
}

.component-detail-dialog.bigscreen-detail-dialog .el-dialog__body::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.8);
}

.component-detail-dialog.bigscreen-detail-dialog .component-detail-content {
  min-height: 280px;
}

/* 寿命预测布局样式 */
.lifetime-prediction-layout {
  display: flex;
  flex-direction: column;
  gap: 15px;
  height: 100%;
}

.lifetime-top-section {
  display: flex;
  gap: 20px;
  flex: 0 0 auto;
}

.lifetime-params-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.lifetime-result-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lifetime-chart-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 180px;
  max-height: 200px; /* 限制最大高度 */
  width: 100%;
  overflow: hidden; /* 防止内容溢出 */
}

.lifetime-chart-section .chart-container {
  flex: 1;
  width: 100%;
  min-height: 180px;
  max-height: 200px; /* 限制最大高度 */
}

.params-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.params-header h4 {
  margin: 0;
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
}

.current-params {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.param-item label {
  color: #b3d9ff;
  font-size: 12px;
  font-weight: 500;
}

.param-value {
  color: #ffffff;
  font-size: 12px;
  font-weight: 600;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 寿命预测结果样式 */
.lifetime-result {
  text-align: center;
  padding: 20px;
}

.result-header h4 {
  margin: 0 0 15px 0;
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
}

.result-value {
  margin-bottom: 15px;
}

.life-years {
  font-size: 36px;
  font-weight: 700;
  color: #00d4ff;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.life-unit {
  font-size: 18px;
  color: #ffffff;
  margin-left: 8px;
}

.result-status {
  display: flex;
  justify-content: center;
}

/* 加载状态样式 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #ffffff;
  font-size: 14px;
  padding: 20px;
  background: rgba(0, 212, 255, 0.05);
  border-radius: 8px;
  border: 1px dashed rgba(0, 212, 255, 0.3);
  animation: pulse-loading 2s ease-in-out infinite;
}

.loading-state .el-icon {
  color: #00d4ff;
  font-size: 32px;
}

.loading-state span {
  font-size: 15px;
  font-weight: 500;
}

@keyframes pulse-loading {
  0%, 100% {
    background: rgba(0, 212, 255, 0.05);
    border-color: rgba(0, 212, 255, 0.3);
  }
  50% {
    background: rgba(0, 212, 255, 0.1);
    border-color: rgba(0, 212, 255, 0.5);
  }
}

/* 无结果状态样式 */
.no-result-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #c0c4cc;
  text-align: center;
}

.no-result-state span {
  font-size: 14px;
  color: #ffffff;
}

.no-result-state small {
  font-size: 12px;
  color: #b3d9ff;
}

/* 算法选项样式 */
.algorithm-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.algorithm-name {
  font-weight: 600;
  font-size: 14px;
}

.algorithm-description {
  font-size: 12px;
  color: #666;
  line-height: 1.3;
}

/* 寿命趋势图样式 */
.lifetime-trend-chart {
  width: 100%;
  height: 180px; /* 减少高度避免超出 */
}

.chart-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #ffffff;
  font-size: 13px;
  width: 100%;
  height: 100%;
  min-height: 180px;
  max-height: 200px; /* 限制最大高度 */
  background: rgba(0, 212, 255, 0.05);
  border-radius: 8px;
  border: 1px dashed rgba(0, 212, 255, 0.3);
  animation: pulse-loading 2s ease-in-out infinite;
}

.chart-loading .el-icon {
  color: #00d4ff;
  font-size: 28px;
}

.chart-loading span {
  font-weight: 500;
}

.chart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #c0c4cc;
  text-align: center;
  width: 100%;
  height: 100%;
  min-height: 180px;
  max-height: 200px; /* 限制最大高度 */
}

.chart-empty span {
  font-size: 12px;
  color: #ffffff;
}

/* 底部管理功能区域样式 */
.bottom-management-area {
  position: fixed;
  bottom: 15px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 15px;
  z-index: 100;
  max-width: 90vw; /* 限制最大宽度 */
}

.management-panel {
  background: rgba(59, 130, 246, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 12px;
  padding: 12px;
  min-width: 180px;
  flex: 1; /* 让面板平均分配宽度 */
}

.management-panel .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(147, 197, 253, 0.2);
}

.management-panel .panel-header h3 {
  margin: 0;
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
}

.management-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

/* 数据管理特殊布局：3个项目 */
.management-panel:nth-child(1) .management-grid {
  grid-template-columns: repeat(3, 1fr);
}

/* 检测配置特殊布局：4个项目，2x2网格 */
.management-panel:nth-child(2) .management-grid {
  grid-template-columns: repeat(2, 1fr);
}

/* 数据库查询&管理特殊布局：3个项目 */
.management-panel:nth-child(3) .management-grid {
  grid-template-columns: repeat(3, 1fr);
}

/* 系统&用户管理特殊布局：2个项目 */
.management-panel:nth-child(4) .management-grid {
  grid-template-columns: repeat(2, 1fr);
}

.management-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px 6px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 60px;
  text-align: center;
}

.management-item:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
}

.management-item .el-icon {
  color: #00d4ff;
  margin-bottom: 4px;
}

.management-item span {
  color: #ffffff;
  font-size: 10px;
  font-weight: 500;
  line-height: 1.2;
  word-break: break-word;
}

.management-item:hover span {
  color: #ffffff;
  text-shadow: 0 0 8px rgba(0, 212, 255, 0.5);
}

.component-detail-dialog.bigscreen-detail-dialog .component-info-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(147, 197, 253, 0.3);
  display: flex;  /* 添加flex布局 */
  align-items: center;  /* 垂直居中对齐 */
  gap: 15px;  /* 元素间距 */
}

.component-detail-dialog.bigscreen-detail-dialog .component-info-header h3 {
  color: #ffffff;
  margin: 0;  /* 移除下边距，从 '0 0 10px 0' 改为 '0' */
  font-size: 18px;
}

.component-detail-dialog.bigscreen-detail-dialog .score-count {
  color: #93c5fd;
  font-size: 14px;
}

.component-detail-dialog.bigscreen-detail-dialog .pie-charts-section {
  margin-bottom: 30px;
}

.component-detail-dialog.bigscreen-detail-dialog .pie-chart-title h4 {
  color: #ffffff;
  margin: 0 0 15px 0;
  font-size: 16px;
}

.component-detail-dialog.bigscreen-detail-dialog .detail-tables {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.component-detail-dialog.bigscreen-detail-dialog .table-section h4 {
  color: #ffffff;
  margin: 0 0 10px 0;
  font-size: 15px;
}

.component-detail-dialog.bigscreen-detail-dialog .table-wrapper {
  display: flex;
  justify-content: center;
  width: 100%;
}

.component-detail-dialog.bigscreen-detail-dialog .table-wrapper .el-table {
  width: auto;
  min-width: 640px;
  max-width: 100%;
}

/* 型号个体选择面板样式 */
.model-selection-panel {
  background: rgba(59, 130, 246, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 15px;
  padding: 20px;
  flex: 1;
  max-height: 50%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.model-selection-panel .panel-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.anomaly-results-panel {
  background: rgba(59, 130, 246, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 15px;
  padding: 20px;
  flex: 1;
  max-height: 50%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.anomaly-results-panel .panel-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 型号树样式 */
.model-tree {
  flex: 1;
  overflow-y: auto;
}

.model-item {
  margin-bottom: 8px;
}

.model-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.model-header:hover {
  background: rgba(0, 255, 255, 0.1);
  border-color: #00ffff;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
}

.expand-icon {
  font-size: 10px;
  color: #00ffff;
  margin-right: 10px;
  transition: transform 0.3s ease;
  display: inline-block;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.model-name {
  flex: 1;
  font-size: 14px;
  font-weight: bold;
  color: #fff;
}

.model-name .label-prefix {
  color: #93c5fd;  /* 浅蓝色标签 */
  font-weight: 500;
  margin-right: 4px;
}

.instance-count {
  font-size: 12px;
  color: #00ffff;
}

/* 个体列表样式 */
.instances-list {
  margin-top: 8px;
  margin-left: 20px;
  border-left: 2px solid rgba(0, 255, 255, 0.2);
  padding-left: 10px;
}

.loading-instances {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  color: #888;
  font-size: 12px;
}

.loading-spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 255, 255, 0.2);
  border-top-color: #00ffff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.instance-item {
  padding: 8px 12px;
  margin-bottom: 6px;
  background: rgba(0, 0, 0, 0.2);
  border-left: 3px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.instance-item:hover {
  background: rgba(0, 255, 255, 0.1);
  transform: translateX(3px);
}

.instance-item.selected {
  background: rgba(0, 255, 255, 0.15);
  border-left-color: #00ffff !important;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
}

.instance-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.instance-id {
  font-size: 13px;
  color: #fff;
  font-weight: 500;
}

.instance-id .label-prefix {
  color: #93c5fd;  /* 浅蓝色标签 */
  font-weight: 500;
  margin-right: 4px;
}

.instance-health {
  font-size: 12px;
  font-weight: bold;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.3);
}

.instance-health .health-label {
  color: #93c5fd;  /* 浅蓝色标签，与label-prefix一致 */
  font-weight: 500;
  margin-right: 2px;
}

.instance-health.no-data {
  color: #888;
}

.instance-health.no-data .health-label {
  color: #93c5fd;  /* 即使无数据，标签也保持浅蓝色 */
}

.empty-instances {
  padding: 10px;
  text-align: center;
  color: #888;
  font-size: 12px;
}

.empty-models {
  padding: 20px;
  text-align: center;
}

/* 异常检测结果样式 */
.no-selection-state {
  text-align: center;
  padding: 20px;
  color: #888;
}

.loading-state {
  text-align: center;
  padding: 20px;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.anomaly-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 15px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.stat-item:hover {
  background: rgba(0, 0, 0, 0.4);
  border-color: rgba(0, 255, 255, 0.5);
  transform: translateY(-2px);
}

.stat-label {
  font-size: 11px;
  color: #aaaaaa;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: #00ffff;
  text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

.stat-value.high-risk {
  color: #ff4757;
}

.stat-value.medium-risk {
  color: #ffa502;
}

.stat-value.low-risk {
  color: #2ed573;
}

/* 异常帧列表样式 */
.anomaly-frames-list {
  max-height: 350px;  /* 增加高度，从150px改为350px */
  overflow-y: auto;
  flex: 1;  /* 让列表区域占据剩余空间 */
}

.frames-header {
  font-size: 14px;
  font-weight: bold;
  color: #00ffff;
  margin-bottom: 10px;
  padding-bottom: 5px;
  border-bottom: 1px solid rgba(0, 255, 255, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.frames-count {
  font-size: 12px;
  color: #93c5fd;
  font-weight: normal;
}

.frames-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.frame-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
}

.frame-item:hover {
  background: rgba(0, 255, 255, 0.1);
  border-color: #00ffff;
}

.frame-time {
  font-size: 12px;
  color: #cccccc;
}

.frame-score {
  font-size: 12px;
  font-weight: bold;
  padding: 2px 6px;
  border-radius: 4px;
}

.frame-score .score-label {
  color: #93c5fd;  /* 浅蓝色标签，与其他标签一致 */
  font-weight: 500;
  margin-right: 2px;
}

.frame-score.high-score {
  color: #ff4757;                     /* 红色 - 高异常分数（≥0.9），危险 */
  background: rgba(255, 71, 87, 0.2);
}

.frame-score.medium-score {
  color: #ffa502;                      /* 橙色 - 中等异常分数（0.7-0.9），警告 */
  background: rgba(255, 165, 2, 0.2);
}

.frame-score.low-score {
  color: #2ed573;                      /* 绿色 - 低异常分数（<0.7），较正常 */
  background: rgba(46, 213, 115, 0.2);
}
</style>

<style>
/* ==================== 大屏弹出框统一样式 ==================== */
/* 注意：这些样式需要覆盖全局的灰白色背景设置 */

/* 人工判定确认对话框样式 - 必须在全局样式中，因为MessageBox挂载到body */
.bigscreen-confirm-dialog.el-message-box {
  background: rgba(30, 58, 138, 0.95) !important;
  border: 2px solid rgba(59, 130, 246, 0.5) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7) !important;
  backdrop-filter: blur(20px) !important;
  z-index: 10000 !important;  /* 确保在最上层 */
}

.bigscreen-confirm-dialog .el-message-box__header {
  background: transparent !important;
  border-bottom: 1px solid rgba(147, 197, 253, 0.3);
}

.bigscreen-confirm-dialog .el-message-box__title {
  color: #ffffff !important;
  font-weight: 600;
}

.bigscreen-confirm-dialog .el-message-box__content {
  color: #ffffff !important;
}

.bigscreen-confirm-dialog .el-message-box__message {
  color: #ffffff !important;
  font-size: 14px;
}

.bigscreen-confirm-dialog .el-message-box__btns {
  border-top: 1px solid rgba(147, 197, 253, 0.3);
  padding-top: 15px;
}

.bigscreen-confirm-dialog .el-button {
  background-color: rgba(59, 130, 246, 0.6) !important;
  border-color: rgba(147, 197, 253, 0.5) !important;
  color: #ffffff !important;
}

.bigscreen-confirm-dialog .el-button:hover {
  background-color: rgba(59, 130, 246, 0.8) !important;
  border-color: rgba(147, 197, 253, 0.7) !important;
}

.bigscreen-confirm-dialog .el-button--primary {
  background-color: rgba(230, 162, 60, 0.8) !important;
  border-color: rgba(251, 191, 36, 0.6) !important;
}

.bigscreen-confirm-dialog .el-button--primary:hover {
  background-color: rgba(230, 162, 60, 1) !important;
  border-color: rgba(251, 191, 36, 0.8) !important;
}

/* MessageBox的遮罩层样式 */
.el-overlay:has(.bigscreen-confirm-dialog) {
  z-index: 9999 !important;
  backdrop-filter: blur(3px);
}

/* ==================== 寿命预测参数设置弹窗的全局组件样式 ==================== */
/* 下拉菜单面板样式（挂载到body，需要全局样式） */
.el-select-dropdown.lifetime-settings-select-dropdown,
.el-popper.lifetime-settings-select-dropdown {
  background: rgba(30, 58, 138, 0.95) !important;
  border: 1px solid rgba(59, 130, 246, 0.5) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5) !important;
  backdrop-filter: blur(20px) !important;
  z-index: 9999 !important;
}

.el-select-dropdown.lifetime-settings-select-dropdown .el-select-dropdown__item,
.el-popper.lifetime-settings-select-dropdown .el-select-dropdown__item {
  color: #ffffff !important;
  background: transparent !important;
}

.el-select-dropdown.lifetime-settings-select-dropdown .el-select-dropdown__item:hover,
.el-popper.lifetime-settings-select-dropdown .el-select-dropdown__item:hover {
  background: rgba(59, 130, 246, 0.4) !important;
  color: #ffffff !important;
}

.el-select-dropdown.lifetime-settings-select-dropdown .el-select-dropdown__item.selected,
.el-popper.lifetime-settings-select-dropdown .el-select-dropdown__item.selected {
  background: rgba(59, 130, 246, 0.6) !important;
  color: #ffffff !important;
}

/* 增强下拉框样式优先级 - 覆盖所有可能的Element Plus默认样式 */
.el-select-dropdown.lifetime-settings-select-dropdown .el-scrollbar__view,
.el-popper.lifetime-settings-select-dropdown .el-scrollbar__view {
  background: transparent !important;
}

.el-select-dropdown.lifetime-settings-select-dropdown .el-select-dropdown__wrap,
.el-popper.lifetime-settings-select-dropdown .el-select-dropdown__wrap {
  background: transparent !important;
}

/* 强制覆盖Element Plus默认样式 */
.el-select-dropdown.lifetime-settings-select-dropdown,
.el-popper.lifetime-settings-select-dropdown,
div.el-select-dropdown.lifetime-settings-select-dropdown,
div.el-popper.lifetime-settings-select-dropdown {
  background: rgba(30, 58, 138, 0.95) !important;
  border: 1px solid rgba(59, 130, 246, 0.5) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5) !important;
  backdrop-filter: blur(20px) !important;
  z-index: 9999 !important;
}

/* 强制覆盖所有下拉选项样式 */
.el-select-dropdown.lifetime-settings-select-dropdown .el-select-dropdown__item,
.el-popper.lifetime-settings-select-dropdown .el-select-dropdown__item,
div.el-select-dropdown.lifetime-settings-select-dropdown .el-select-dropdown__item,
div.el-popper.lifetime-settings-select-dropdown .el-select-dropdown__item {
  color: #ffffff !important;
  background: transparent !important;
  border: none !important;
}

.el-select-dropdown.lifetime-settings-select-dropdown .el-select-dropdown__item:hover,
.el-popper.lifetime-settings-select-dropdown .el-select-dropdown__item:hover,
div.el-select-dropdown.lifetime-settings-select-dropdown .el-select-dropdown__item:hover,
div.el-popper.lifetime-settings-select-dropdown .el-select-dropdown__item:hover {
  background: rgba(59, 130, 246, 0.4) !important;
  color: #ffffff !important;
}

.el-select-dropdown.lifetime-settings-select-dropdown .el-select-dropdown__item.selected,
.el-popper.lifetime-settings-select-dropdown .el-select-dropdown__item.selected,
div.el-select-dropdown.lifetime-settings-select-dropdown .el-select-dropdown__item.selected,
div.el-popper.lifetime-settings-select-dropdown .el-select-dropdown__item.selected {
  background: rgba(59, 130, 246, 0.6) !important;
  color: #ffffff !important;
}

/* 日期选择器面板样式（挂载到body，需要全局样式） */
.el-picker-panel.lifetime-settings-date-picker {
  background: rgba(30, 58, 138, 0.95) !important;
  border: 1px solid rgba(59, 130, 246, 0.5) !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5) !important;
  backdrop-filter: blur(20px) !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-picker-panel__body {
  background: transparent !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-date-picker__header {
  color: #ffffff !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-date-picker__header-label {
  color: #ffffff !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-date-table th {
  color: #93c5fd !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-date-table td {
  color: #ffffff !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-date-table td.available:hover {
  background: rgba(59, 130, 246, 0.4) !important;
  color: #ffffff !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-date-table td.current {
  background: rgba(96, 165, 250, 0.6) !important;
  color: #ffffff !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-date-table td.today {
  color: #60a5fa !important;
  font-weight: bold;
}

.el-picker-panel.lifetime-settings-date-picker .el-picker-panel__icon-btn {
  color: #93c5fd !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-picker-panel__icon-btn:hover {
  color: #ffffff !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-time-panel {
  background: transparent !important;
  border-color: rgba(59, 130, 246, 0.4) !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-time-spinner__item {
  color: #ffffff !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-time-spinner__item:hover {
  background: rgba(59, 130, 246, 0.4) !important;
}

.el-picker-panel.lifetime-settings-date-picker .el-time-spinner__item.active {
  color: #ffffff !important;
  font-weight: bold;
}

/* 时间选择对话框 - 多种选择器确保样式生效 */
.el-dialog.time-selector-dialog,
.time-selector-dialog.el-dialog,
.el-dialog__wrapper .time-selector-dialog,
div.time-selector-dialog.el-dialog {
  background: rgba(30, 58, 138, 0.15) !important;  /* 深蓝色更透明背景 */
  border: 2px solid rgba(59, 130, 246, 0.5) !important;  /* 浅蓝色边框 */
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
  backdrop-filter: blur(30px) !important;  /* 进一步增强毛玻璃效果 */
  --el-dialog-bg-color: rgba(30, 58, 138, 0.15) !important;  /* 覆盖CSS变量 */
}

/* 覆盖全局样式对对话框内Element Plus组件的影响 */
.el-dialog.time-selector-dialog .el-input__wrapper,
.el-dialog.time-selector-dialog .el-textarea__inner,
.el-dialog.time-selector-dialog .el-select .el-input__wrapper,
.el-dialog.time-selector-dialog .el-date-editor,
.el-dialog.time-selector-dialog .el-range-editor,
.el-dialog.time-selector-dialog .el-picker-panel,
.el-dialog.time-selector-dialog .el-date-editor .el-range-input,
.el-dialog.time-selector-dialog .el-select-dropdown,
.el-dialog.time-selector-dialog .el-select-dropdown__item {
  background-color: rgba(30, 58, 138, 0.15) !important;  /* 更透明 */
  color: #ffffff !important;
  border-color: rgba(147, 197, 253, 0.4) !important;
}

.el-dialog.time-selector-dialog .el-dialog__header {
  background: transparent !important;
  color: #ffffff !important;
  border-bottom: 1px solid rgba(147, 197, 253, 0.3);
}

.el-dialog.time-selector-dialog .el-dialog__title {
  color: #ffffff !important;
}

.el-dialog.time-selector-dialog .el-dialog__body {
  background: transparent !important;
  color: #ffffff !important;
}

.el-dialog.time-selector-dialog .el-dialog__footer {
  background: transparent !important;
  border-top: 1px solid rgba(147, 197, 253, 0.3);
}

/* 按钮样式 */
.el-dialog.time-selector-dialog .el-button {
  background-color: rgba(59, 130, 246, 0.6) !important;
  border-color: rgba(147, 197, 253, 0.5) !important;
  color: #ffffff !important;
}

.el-dialog.time-selector-dialog .el-button:hover {
  background-color: rgba(59, 130, 246, 0.8) !important;
  border-color: rgba(147, 197, 253, 0.7) !important;
}

.el-dialog.time-selector-dialog .el-button--primary {
  background-color: rgba(96, 165, 250, 0.9) !important;
  border-color: rgba(147, 197, 253, 0.8) !important;
}

.el-dialog.time-selector-dialog .el-button--primary:hover {
  background-color: rgba(96, 165, 250, 1) !important;
  border-color: rgba(147, 197, 253, 1) !important;
}

/* 异常帧详情对话框 - 多种选择器确保样式生效 */
.el-dialog.bigscreen-detail-dialog,
.bigscreen-detail-dialog.el-dialog,
.el-dialog__wrapper .bigscreen-detail-dialog,
div.bigscreen-detail-dialog.el-dialog,
.el-dialog.detail-dialog.bigscreen-detail-dialog {
  background: rgba(30, 58, 138, 0.15) !important;  /* 深蓝色更透明背景 */
  border: 2px solid rgba(59, 130, 246, 0.5) !important;  /* 浅蓝色边框 */
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
  backdrop-filter: blur(30px) !important;  /* 进一步增强毛玻璃效果 */
  --el-dialog-bg-color: rgba(30, 58, 138, 0.15) !important;  /* 覆盖CSS变量 */
}

/* 覆盖全局样式对对话框内Element Plus组件的影响 */
.el-dialog.bigscreen-detail-dialog .el-input__wrapper,
.el-dialog.bigscreen-detail-dialog .el-textarea__inner,
.el-dialog.bigscreen-detail-dialog .el-select .el-input__wrapper,
.el-dialog.bigscreen-detail-dialog .el-date-editor,
.el-dialog.bigscreen-detail-dialog .el-range-editor,
.el-dialog.bigscreen-detail-dialog .el-picker-panel,
.el-dialog.bigscreen-detail-dialog .el-date-editor .el-range-input {
  background-color: rgba(15, 30, 80, 0.8) !important;  /* 更深的蓝色背景，80%不透明度 */
  color: #ffffff !important;
  border-color: rgba(147, 197, 253, 0.6) !important;  /* 更亮的边框 */
}

/* 确保输入框内的文字是白色 */
.el-dialog.bigscreen-detail-dialog .el-input__inner,
.el-dialog.bigscreen-detail-dialog .el-select .el-input__inner {
  color: #ffffff !important;
}

/* 选择框的标签（已选中的tag） */
.el-dialog.bigscreen-detail-dialog .el-select .el-tag {
  background-color: rgba(96, 165, 250, 0.5) !important;
  border-color: rgba(147, 197, 253, 0.5) !important;
  color: #ffffff !important;
}

/* 选择框的关闭图标 */
.el-dialog.bigscreen-detail-dialog .el-tag__close {
  color: #ffffff !important;
}

.el-dialog.bigscreen-detail-dialog .el-tag__close:hover {
  background-color: rgba(255, 255, 255, 0.2) !important;
}

/* 遥测量选择下拉框专用样式 - 使用 popper-class */
/* 增强选择器优先级以覆盖全局样式 */
.el-popper.bigscreen-telemetry-select-dropdown,
.bigscreen-telemetry-select-dropdown.el-popper,
.el-select-dropdown.bigscreen-telemetry-select-dropdown {
  background-color: rgba(15, 30, 80, 0.5) !important;  /* 更深的蓝色，95%不透明度 */
  border: 1px solid rgba(147, 197, 253, 0.6) !important;  /* 更亮的边框 */
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.7) !important;  /* 更深的阴影 */
  backdrop-filter: blur(20px) !important;  /* 增强毛玻璃效果 */
  z-index: 9999 !important;  /* 确保在对话框之上 */
}

/* 下拉框内部容器 */
.bigscreen-telemetry-select-dropdown .el-select-dropdown__wrap,
.bigscreen-telemetry-select-dropdown .el-scrollbar__view {
  background-color: transparent !important;
}

/* 下拉选项样式 */
.bigscreen-telemetry-select-dropdown .el-select-dropdown__item,
.bigscreen-telemetry-select-dropdown.el-select-dropdown .el-select-dropdown__item {
  background-color: transparent !important;
  color: #ffffff !important;
}

/* 下拉选项悬停样式 */
.bigscreen-telemetry-select-dropdown .el-select-dropdown__item:hover,
.bigscreen-telemetry-select-dropdown.el-select-dropdown .el-select-dropdown__item:hover {
  background-color: rgba(96, 165, 250, 0.4) !important;  /* 悬停时稍微亮一点 */
  color: #ffffff !important;
}

/* 下拉选项选中样式 */
.bigscreen-telemetry-select-dropdown .el-select-dropdown__item.selected,
.bigscreen-telemetry-select-dropdown .el-select-dropdown__item.is-selected,
.bigscreen-telemetry-select-dropdown.el-select-dropdown .el-select-dropdown__item.selected,
.bigscreen-telemetry-select-dropdown.el-select-dropdown .el-select-dropdown__item.is-selected {
  background-color: rgba(96, 165, 250, 0.6) !important;  /* 选中项更亮 */
  color: #ffffff !important;
  font-weight: 600 !important;
}

.el-dialog.bigscreen-detail-dialog .el-dialog__header {
  background: transparent !important;
  color: #ffffff !important;
  border-bottom: 1px solid rgba(147, 197, 253, 0.3);
}

.el-dialog.bigscreen-detail-dialog .el-dialog__title {
  color: #ffffff !important;
}

.el-dialog.bigscreen-detail-dialog .el-dialog__body {
  background: transparent !important;
  color: #ffffff !important;
}

.el-dialog.bigscreen-detail-dialog .el-dialog__footer {
  background: transparent !important;
  border-top: 1px solid rgba(147, 197, 253, 0.3);
}

/* 按钮样式 */
.el-dialog.bigscreen-detail-dialog .el-button {
  background-color: rgba(59, 130, 246, 0.6) !important;
  border-color: rgba(147, 197, 253, 0.5) !important;
  color: #ffffff !important;
}

.el-dialog.bigscreen-detail-dialog .el-button:hover {
  background-color: rgba(59, 130, 246, 0.8) !important;
  border-color: rgba(147, 197, 253, 0.7) !important;
}

.el-dialog.bigscreen-detail-dialog .el-button--primary {
  background-color: rgba(96, 165, 250, 0.9) !important;
  border-color: rgba(147, 197, 253, 0.8) !important;
}

.el-dialog.bigscreen-detail-dialog .el-button--primary:hover {
  background-color: rgba(96, 165, 250, 1) !important;
  border-color: rgba(147, 197, 253, 1) !important;
}

/* ==================== 寿命预测参数设置弹窗样式 ==================== */
.lifetime-settings-dialog.bigscreen-detail-dialog .el-form {
  padding: 10px 0;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-form-item__label {
  color: #93c5fd !important;
  font-weight: 500;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-input-number {
  background: transparent;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-input-number .el-input__wrapper {
  background-color: rgba(15, 30, 80, 0.5) !important;
  border-color: rgba(59, 130, 246, 0.4) !important;
  box-shadow: none !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-input-number .el-input__wrapper:hover {
  border-color: rgba(59, 130, 246, 0.6) !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-input-number .el-input__wrapper.is-focus {
  border-color: rgba(96, 165, 250, 0.8) !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-input-number .el-input__inner {
  color: #ffffff !important;
  text-align: left;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-input-number__decrease,
.lifetime-settings-dialog.bigscreen-detail-dialog .el-input-number__increase {
  background-color: rgba(59, 130, 246, 0.3) !important;
  border-left-color: rgba(59, 130, 246, 0.4) !important;
  color: #93c5fd !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-input-number__decrease:hover,
.lifetime-settings-dialog.bigscreen-detail-dialog .el-input-number__increase:hover {
  background-color: rgba(59, 130, 246, 0.5) !important;
  color: #ffffff !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-date-editor .el-input__wrapper {
  background-color: rgba(15, 30, 80, 0.5) !important;
  border-color: rgba(59, 130, 246, 0.4) !important;
  box-shadow: none !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-date-editor .el-input__wrapper:hover {
  border-color: rgba(59, 130, 246, 0.6) !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-date-editor .el-input__wrapper.is-focus {
  border-color: rgba(96, 165, 250, 0.8) !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-date-editor .el-input__inner {
  color: #ffffff !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-date-editor .el-icon {
  color: #93c5fd !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-select .el-input__wrapper {
  background-color: rgba(15, 30, 80, 0.5) !important;
  border-color: rgba(59, 130, 246, 0.4) !important;
  box-shadow: none !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-select .el-input__wrapper:hover {
  border-color: rgba(59, 130, 246, 0.6) !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-select .el-input__wrapper.is-focus {
  border-color: rgba(96, 165, 250, 0.8) !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-select .el-input__inner {
  color: #ffffff !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-select .el-icon {
  color: #93c5fd !important;
}

.lifetime-settings-dialog.bigscreen-detail-dialog .el-text {
  color: #93c5fd !important;
}

/* 算法选择下拉选项样式 */
.algorithm-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.algorithm-name {
  color: #ffffff;
  font-weight: 500;
  font-size: 14px;
}

.algorithm-description {
  color: #93c5fd;
  font-size: 12px;
  line-height: 1.3;
}

/* ==================== 内容区域 - 透明的浅蓝色 ==================== */

/* 时间选择对话框内容 */
.el-dialog.time-selector-dialog .timeline-info {
  background: rgba(30, 58, 138, 0.15) !important;  /* 更透明 */
  border: 1px solid rgba(147, 197, 253, 0.3);
}

.el-dialog.time-selector-dialog .timeline-slider {
  background: rgba(30, 58, 138, 0.15) !important;  /* 更透明 */
  border: 1px solid rgba(147, 197, 253, 0.3);
}

.el-dialog.time-selector-dialog .fallback-time-picker {
  background: rgba(30, 58, 138, 0.15) !important;  /* 更透明 */
  border: 1px solid rgba(147, 197, 253, 0.3);
}

/* 异常帧详情对话框内容 */
.el-dialog.bigscreen-detail-dialog .el-card {
  background: rgba(30, 58, 138, 0.15) !important;  /* 更透明 */
  border: 1px solid rgba(147, 197, 253, 0.3);
}

.el-dialog.bigscreen-detail-dialog .el-card__header {
  background: rgba(15, 30, 70, 0.75) !important;  /* 深蓝色透明背景 */
  border-bottom: 1px solid rgba(147, 197, 253, 0.3);
  color: #ffffff;
  font-weight: bold;  /* 题头文字加粗 */
  padding: 10px 16px !important;  /* 减少内边距（默认约18px），降低高度 */
}

.el-dialog.bigscreen-detail-dialog .el-card__body {
  background: transparent !important;
  color: #ffffff;
}

/* 表格样式 */
.el-dialog.bigscreen-detail-dialog .el-table {
  background: transparent !important;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: rgba(10, 20, 50, 0.5);  /* 深蓝色数据行 */
  --el-table-header-bg-color: rgba(15, 30, 70, 0.7);  /* 深蓝色表头 */
  --el-table-row-hover-bg-color: rgba(30, 58, 138, 0.4);  /* 悬停时稍亮 */
  --el-table-border-color: rgba(147, 197, 253, 0.3);
  --el-table-text-color: #ffffff;
  --el-table-header-text-color: #ffffff;
}

.el-dialog.bigscreen-detail-dialog .el-table__inner-wrapper,
.el-dialog.bigscreen-detail-dialog .el-table__body-wrapper {
  background: transparent !important;
}

.el-dialog.bigscreen-detail-dialog .el-table th.el-table__cell {
  background: rgba(15, 30, 70, 0.7) !important;  /* 深蓝色表头 */
  color: #ffffff;
  font-weight: 600;  /* 表头文字加粗 */
}

.el-dialog.bigscreen-detail-dialog .el-table tr {
  background: rgba(10, 20, 50, 0.5) !important;  /* 深蓝色数据行 */
}

.el-dialog.bigscreen-detail-dialog .el-table tr:hover {
  background: rgba(30, 58, 138, 0.4) !important;  /* 悬停时稍亮 */
}

/* Element Plus 组件内部样式 */
.el-dialog.bigscreen-detail-dialog .el-descriptions {
  --el-descriptions-item-bordered-label-background: rgba(15, 30, 70, 0.7);   /* 深蓝色 70%透明 */
  --el-descriptions-item-bordered-content-background: rgba(10, 20, 50, 0.7); /* 更深的蓝色 70%透明 */
  --el-border-color: rgba(147, 197, 253, 0.3);
}

.el-dialog.bigscreen-detail-dialog .el-descriptions__label {
  color: #ffffff !important;  /* 白色字体 */
  font-weight: 500;
  font-size: 13px;
}

.el-dialog.bigscreen-detail-dialog .el-descriptions__content {
  color: #ffffff !important;  /* 白色字体 */
  font-size: 13px;
}

/* 确保descriptions的单元格也是深蓝色透明背景 - 统一颜色 */
.el-dialog.bigscreen-detail-dialog .el-descriptions__cell {
  background-color: rgba(10, 20, 50, 0.7) !important;  /* 深蓝色 70%透明 */
  color: #ffffff !important;
}

.el-dialog.bigscreen-detail-dialog .el-descriptions__label.el-descriptions__cell {
  background-color: rgba(15, 30, 70, 0.7) !important;  /* 标签稍微浅一点但仍是深色 */
}

.el-dialog.bigscreen-detail-dialog .el-divider__text {
  background-color: transparent;
  color: #dbeafe;
  font-weight: 500;
  font-size: 13px;
}

/* 时间选择对话框内部组件样式 */
.el-dialog.time-selector-dialog .el-descriptions {
  --el-descriptions-item-bordered-label-background: rgba(15, 30, 70, 0.7);   /* 深蓝色 70%透明 */
  --el-descriptions-item-bordered-content-background: rgba(10, 20, 50, 0.7); /* 更深的蓝色 70%透明 */
  --el-border-color: rgba(147, 197, 253, 0.3);
}

.el-dialog.time-selector-dialog .el-descriptions__label {
  color: #ffffff !important;  /* 白色字体 */
  font-weight: 500;
}

.el-dialog.time-selector-dialog .el-descriptions__content {
  color: #ffffff !important;  /* 白色字体 */
}

/* 确保descriptions的单元格也是深蓝色透明背景 */
.el-dialog.time-selector-dialog .el-descriptions__cell {
  background-color: rgba(10, 20, 50, 0.7) !important;  /* 深蓝色 70%透明 */
  color: #ffffff !important;
}

.el-dialog.time-selector-dialog .el-descriptions__label.el-descriptions__cell {
  background-color: rgba(15, 30, 70, 0.7) !important;  /* 标签稍微浅一点但仍是深色 */
}

/* 时间滑块标记文字样式 */
.el-dialog.time-selector-dialog .el-slider__marks-text {
  color: #ffffff !important;
  font-size: 11px;
  white-space: nowrap;
}

/* 3D模型详情弹窗样式 */
.model-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: transparent;  /* 完全透明，无遮蔽层 */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  backdrop-filter: none;  /* 不模糊背景 */
  pointer-events: none;  /* 允许点击穿透到背景 */
}

.model-dialog {
  pointer-events: auto;  /* 弹窗本身可以点击 */
  background: rgba(30, 58, 138, 0.15);
  border: 2px solid rgba(59, 130, 246, 0.5);
  border-radius: 12px;
  padding: 0;
  max-width: 650px;  /* 增加宽度以容纳两列卡片布局 */
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(20px);
}

.model-dialog-header {
  background: rgba(30, 58, 138, 0.3);
  padding: 16px 20px;
  border-bottom: 1px solid rgba(59, 130, 246, 0.3);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-dialog-header h3 {
  color: #ffffff;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: #ffffff;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.3s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.model-dialog-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 8px;  /* 减少间距，从12px改为8px */
}

.model-type, .model-instances-count {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-label, .count-label {
  color: #ffffff;  /* 改为白色 */
  font-size: 15px;  /* 略微调大，从14px改为15px */
  font-weight: 600;  /* 加粗 */
  min-width: 80px;
}

.type-value, .count-value {
  color: #ffffff;  /* 保持白色 */
  font-size: 15px;  /* 略微调大，从14px改为15px */
  font-weight: 600;  /* 加粗，从500改为600 */
}

.type-value.space_station {
  color: #22c55e;
}

.type-value.satellite {
  color: #3b82f6;
}

/* CMG个体列表样式 - 卡片网格布局 */
.model-instances-list {
  margin-top: 8px;  /* 减少间距，从15px改为8px */
}

.instances-header {
  color: #ffffff;  /* 改为白色 */
  font-size: 15px;  /* 略微调大，从13px改为15px */
  font-weight: 600;  /* 加粗 */
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(59, 130, 246, 0.2);
}

.instances-grid-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);  /* 一行两个卡片 */
  gap: 15px;
  max-height: 400px;
  overflow-y: auto;
  padding: 5px;
}

/* CMG卡片样式 */
.cmg-card {
  display: flex;
  flex-direction: column;
  border: 2px solid rgba(147, 197, 253, 0.3);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  position: relative;
}

.cmg-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: inherit;  /* 继承父元素的背景色 */
  opacity: 1;
  z-index: -1;
  transition: opacity 0.3s ease;
}

.cmg-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 255, 255, 0.4);
  border-color: rgba(0, 255, 255, 0.8);
}

.cmg-card:hover::before {
  opacity: 1.3;  /* 悬停时稍微加深背景 */
}

/* CMG图片区域 */
.cmg-card-image {
  width: 100%;
  height: 100px;  /* 减少高度，从140px改为100px */
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.4), rgba(30, 58, 138, 0.3));
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

.cmg-card-image::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  border: 2px solid rgba(0, 255, 255, 0.3);
  border-top-color: #00ffff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}

.cmg-card-image.loading::after {
  opacity: 1;
}

.cmg-card-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;  /* 保持图片比例 */
  padding: 6px;  /* 减少内边距，从10px改为6px */
  transition: opacity 0.3s ease;
}

.cmg-card-image img:not([src]), 
.cmg-card-image img[src=""] {
  opacity: 0;
}

/* CMG信息区域 */
.cmg-card-info {
  padding: 8px;  /* 减少内边距，从12px改为8px */
  background: rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  gap: 6px;  /* 减少间距，从8px改为6px */
}

.cmg-card-name {
  font-size: 14px;
  color: #ffffff;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cmg-card-health {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  font-size: 12px;
}

.cmg-card-health .health-label {
  color: #93c5fd;
  font-weight: 500;
}

.cmg-card-health .health-value {
  font-weight: bold;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.3);
}

.cmg-card-health .health-value.no-data {
  color: #888;
}

.empty-instances-dialog {
  grid-column: 1 / -1;  /* 占满整行 */
  padding: 40px 20px;
  text-align: center;
  color: #888;
  font-size: 12px;
}

/* 滚动条样式 */
.instances-grid-container::-webkit-scrollbar {
  width: 4px;
}

.instances-grid-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 2px;
}

.instances-grid-container::-webkit-scrollbar-thumb {
  background: rgba(0, 255, 255, 0.3);
  border-radius: 2px;
}

.instances-grid-container::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 255, 255, 0.5);
}
</style>

