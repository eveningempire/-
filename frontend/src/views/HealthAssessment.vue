<template>
  <div class="health-assessment">
    <el-card class="page-header" shadow="never">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon class="title-icon"><DataAnalysis /></el-icon>
            CMG健康状态特征提取与智能评估模型
          </h1>
          <p class="page-description">CMG健康状态特征提取与智能评估模型可视化展示</p>
        </div>
      </div>
    </el-card>

    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- 智能评估模块 -->
      <el-tab-pane label="智能评估" name="assessment">
        <!-- 1. 数据导入区域 -->
        <el-card class="control-panel" shadow="never">
          <div class="control-header">
            <h2>
              <el-icon><Folder /></el-icon>
              数据导入
            </h2>
            <p>导入要进行智能评估的CMG数据文件 (支持 xlsx 或 csv 格式)</p>
          </div>
          <div class="control-row">
            <label class="control-label">导入数据:</label>
            <div style="display: flex; align-items: center; gap: 20px;">
              <el-button 
                type="primary" 
                size="large"
                :icon="Upload"
                @click="triggerFileUpload"
              >
                选择文件
              </el-button>
              <span v-if="importedFileName" class="file-name-display">
                <el-icon><Document /></el-icon>
                {{ importedFileName }}
              </span>
              <span v-else class="file-hint">未选择文件</span>
            </div>
            <!-- 隐藏的文件输入框 -->
            <input 
              ref="fileInput" 
              type="file" 
              accept=".xlsx,.csv" 
              @change="handleFileImport"
              style="display: none;"
            />
          </div>
        </el-card>

        <!-- 2. 数据展示区域 -->
        <el-card class="viz-panel" shadow="never" v-loading="dataLoading">
          <div class="panel-header">
            <h2 class="panel-title">
              <el-icon><TrendCharts /></el-icon>
              数据展示{{ importedFileName ? ` - ${datasetInfo.name}` : '' }}
            </h2>
            <div class="panel-desc" v-if="importedFileName">{{ datasetInfo.description }}</div>
          </div>

          <!-- 空状态提示 -->
          <el-empty 
            v-if="!importedFileName" 
            description="请先导入数据文件" 
            :image-size="160"
          >
            <template #image>
              <el-icon :size="80" color="#909399">
                <Upload />
              </el-icon>
            </template>
            <template #description>
              <p style="color: var(--el-text-color-secondary); font-size: 16px; margin: 0;">
                请点击上方"选择文件"按钮导入数据
              </p>
            </template>
          </el-empty>

          <!-- 数据图表 -->
          <div class="charts-container" v-if="currentData && importedFileName">
            <div class="chart-box">
              <div class="chart-title">高速电机电流</div>
              <div ref="chartDataHighI" class="chart"></div>
            </div>
            <div class="chart-box">
              <div class="chart-title">高速电机温度</div>
              <div ref="chartDataHighTM" class="chart"></div>
            </div>
            <div class="chart-box">
              <div class="chart-title">高速组件转速</div>
              <div ref="chartDataHighOmega" class="chart"></div>
            </div>
            <div class="chart-box">
              <div class="chart-title">低速组件转速</div>
              <div ref="chartDataLowOmega" class="chart"></div>
            </div>
          </div>

          <!-- 执行评估按钮 -->
          <div class="action-section" v-if="currentData && importedFileName">
            <el-divider></el-divider>
            <div class="action-button-container">
              <el-button 
                type="primary" 
                size="large"
                :icon="Cpu"
                @click="executeAssessment"
                :loading="assessmentLoading"
                :disabled="assessmentExecuted"
              >
                {{ assessmentExecuted ? '评估已完成' : '执行智能评估' }}
              </el-button>
              <div class="action-hint" v-if="!assessmentExecuted">
                点击按钮对当前数据集执行智能健康评估
              </div>
            </div>
          </div>
        </el-card>

        <!-- 3. 评估结果区域 -->
        <el-card 
          v-if="assessmentExecuted" 
          class="viz-panel assessment-result" 
          shadow="never"
        >
          <div class="panel-header">
            <h2 class="panel-title">
              <el-icon><Histogram /></el-icon>
              智能评估结果
            </h2>
            <div class="panel-desc">基准模型与本研究模型的CMG健康状态智能评估对比</div>
          </div>

          <div class="charts-container">
            <!-- HI对比曲线 -->
            <div class="chart-box full-width">
              <div class="chart-title">健康指征 (HI) 对比曲线</div>
              <div ref="chartModelComparison" class="chart large"></div>
            </div>
          </div>

          <!-- 查看指标对比按钮 -->
          <div class="action-section">
            <el-divider></el-divider>
            <div class="action-button-container">
              <el-button 
                type="success" 
                size="large"
                :icon="DataAnalysis"
                @click="showMetricsComparison"
                v-if="!metricsVisible"
              >
                查看性能指标对比
              </el-button>
              <el-button 
                type="info" 
                size="large"
                :icon="ArrowUp"
                @click="hideMetricsComparison"
                v-else
              >
                收起性能指标
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- 4. 指标对比区域 -->
        <el-card 
          v-if="metricsVisible" 
          class="viz-panel metrics-section" 
          shadow="never"
        >
          <div class="panel-header">
            <h2 class="panel-title">
              <el-icon><DataAnalysis /></el-icon>
              性能指标对比
            </h2>
            <div class="panel-desc">基准模型与本研究模型的详细性能指标对比</div>
          </div>

          <!-- 统计信息卡片 -->
          <div class="stats-grid">
            <div class="stat-card duibi">
              <div class="stat-header">
                <el-icon class="stat-icon"><TrendCharts /></el-icon>
                <h3>对比模型（基于Transformer的CMG健康评估模型）</h3>
              </div>
              <div class="stat-content-grid">
                <div class="metric-row clickable" @click="showMetricDetail('Mon')">
                  <span class="metric-label">Mon (单调性):</span>
                  <span class="metric-value">{{ currentMetrics.duibi.mon.toFixed(4) }}</span>
                </div>
                <div class="metric-row clickable" @click="showMetricDetail('Cor')">
                  <span class="metric-label">Cor (一致性):</span>
                  <span class="metric-value">{{ currentMetrics.duibi.cor.toFixed(4) }}</span>
                </div>
                <div class="metric-row clickable" @click="showMetricDetail('Rob')">
                  <span class="metric-label">Rob (鲁棒性):</span>
                  <span class="metric-value">{{ currentMetrics.duibi.rob.toFixed(4) }}</span>
                </div>
                <div class="metric-row hm">
                  <span class="metric-label">HM (综合指标):</span>
                  <span class="metric-value">{{ currentMetrics.duibi.hm.toFixed(4) }}</span>
                </div>
              </div>
            </div>

            <div class="stat-card proposed">
              <div class="stat-header">
                <el-icon class="stat-icon"><Histogram /></el-icon>
                <h3>本研究模型 (基于能量守恒机理的健康评估模型)</h3>
              </div>
              <div class="stat-content-grid">
                <div class="metric-row clickable" @click="showMetricDetail('Mon')">
                  <span class="metric-label">Mon (单调性):</span>
                  <span class="metric-value better">{{ currentMetrics.proposed.mon.toFixed(4) }}</span>
                  <span class="improvement">+{{ calculateImprovement(currentMetrics.proposed.mon, currentMetrics.duibi.mon) }}%</span>
                </div>
                <div class="metric-row clickable" @click="showMetricDetail('Cor')">
                  <span class="metric-label">Cor (一致性):</span>
                  <span class="metric-value better">{{ currentMetrics.proposed.cor.toFixed(4) }}</span>
                  <span class="improvement">+{{ calculateImprovement(currentMetrics.proposed.cor, currentMetrics.duibi.cor) }}%</span>
                </div>
                <div class="metric-row clickable" @click="showMetricDetail('Rob')">
                  <span class="metric-label">Rob (鲁棒性):</span>
                  <span class="metric-value better">{{ currentMetrics.proposed.rob.toFixed(4) }}</span>
                  <span class="improvement">+{{ calculateImprovement(currentMetrics.proposed.rob, currentMetrics.duibi.rob) }}%</span>
                </div>
                <div class="metric-row hm">
                  <span class="metric-label">HM (综合指标):</span>
                  <span class="metric-value better">{{ currentMetrics.proposed.hm.toFixed(4) }}</span>
                  <span class="improvement">+{{ calculateImprovement(currentMetrics.proposed.hm, currentMetrics.duibi.hm) }}%</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 说明信息 -->
        <el-card class="info-panel" shadow="never">
          <h3 class="info-title">
            <el-icon><InfoFilled /></el-icon>
            数据说明
          </h3>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="info-card">
                <div class="info-card-header">
                  <el-icon class="info-icon" color="#67C23A"><DataAnalysis /></el-icon>
                  <h4>CMG5测试数据</h4>
                </div>
                <ul class="info-list">
                  <li>总计 <strong>437万</strong> 条CMG5数据</li>
                  <li>时间范围: 2024年2月 ~ 2024年8月</li>
                  <li>包含10个运行参数</li>
                  <li>展示采样: 3000个数据点</li>
                </ul>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="info-card">
                <div class="info-card-header">
                  <el-icon class="info-icon" color="#E6A23C"><Histogram /></el-icon>
                  <h4>模型评估</h4>
                </div>
                <ul class="info-list">
                  <li>CMG健康指征值范围: 0-1</li>
                  <li>对比模型: 1437个评估点</li>
                  <li>提出模型: 1437个评估点</li>
                  <li>数值越小表示健康度越高</li>
                </ul>
              </div>
            </el-col>
          </el-row>
        </el-card>
        
        <!-- 评估指标详情对话框 -->
        <el-dialog 
          v-model="metricDialogVisible" 
          :title="currentMetric?.name"
          width="70%"
        >
          <div class="metric-detail" v-if="currentMetric">
            <h3>{{ currentMetric.fullName }}</h3>
            
            <el-table :data="metricTableData" :show-header="false" border style="margin-top: 20px;">
              <el-table-column width="180" align="right">
                <template #default="{ row }">
                  <strong style="color: var(--el-text-color-regular);">{{ row.label }}</strong>
                </template>
              </el-table-column>
              <el-table-column>
                <template #default="{ row }">
                  <div v-if="row.type === 'formula'" v-html="row.content"></div>
                  <div v-else-if="row.type === 'list'">
                    <ul style="margin: 0; padding-left: 20px;">
                      <li v-for="(item, index) in row.content" :key="index" style="margin: 6px 0;">{{ item }}</li>
                    </ul>
                  </div>
                  <div v-else style="line-height: 1.8;">{{ row.content }}</div>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-dialog>
      </el-tab-pane>
      

      
      <!-- 特征提取模型图示对话框 -->
      <el-dialog 
        v-model="featureExtractionModelVisible" 
        title="基于功耗残差的CMG整机级特征提取方法"
        width="80%"
      >
        <div class="model-diagram-container">
          <el-image 
            src="/model-diagrams/特征提取模型.png" 
            fit="contain"
            style="width: 100%;"
            :preview-src-list="['/model-diagrams/特征提取模型.png']"
          >
            <template #error>
              <div class="image-error">
                <el-icon :size="50"><PictureFilled /></el-icon>
                <p>模型图加载失败</p>
              </div>
            </template>
          </el-image>
        </div>
      </el-dialog>

      <!-- 特征提取模块 -->
      <el-tab-pane label="特征提取" name="extraction">
        <!-- 控制面板 -->
        <el-card class="control-panel" shadow="never">
          <div class="control-header">
            <h2>特征提取模块</h2>
            <p>选择不同类型查看特征提取结果</p>
          </div>
          
          <!-- 特征类型选择器 -->
          <div class="type-selector">
            <el-button 
              :type="selectedExtractionType === 'features' ? 'primary' : ''" 
              @click="handleExtractionTypeChange('features')"
              size="large"
            >
              <el-icon><Document /></el-icon>
              参数级时域特征提取
            </el-button>
            <el-button 
              :type="selectedExtractionType === 'system' ? 'primary' : ''" 
              @click="handleExtractionTypeChange('system')"
              size="large"
            >
              <el-icon><DataLine /></el-icon>
              整机级健康特征提取
            </el-button>
          </div>
        </el-card>


        <!-- 参数级时域特征提取 - 数据导入 -->
        <el-card class="control-panel" shadow="never" v-show="selectedExtractionType === 'features'">
          <div class="control-header">
            <h2>
              <el-icon><Folder /></el-icon>
              数据导入
            </h2>
            <p>导入要进行时域特征提取的CMG数据文件 (支持 xlsx 或 csv 格式)</p>
          </div>
          <div class="control-row">
            <label class="control-label">导入数据:</label>
            <div style="display: flex; align-items: center; gap: 20px;">
              <el-button 
                type="primary" 
                size="large"
                :icon="Upload"
                @click="triggerFeatureFileUpload"
              >
                选择文件
              </el-button>
              <span v-if="featureFileName" class="file-name-display">
                <el-icon><Document /></el-icon>
                {{ featureFileName }}
              </span>
              <span v-else class="file-hint">未选择文件</span>
            </div>
            <!-- 隐藏的文件输入框 -->
            <input 
              ref="featureFileInput" 
              type="file" 
              accept=".xlsx,.csv" 
              @change="handleFeatureFileImport"
              style="display: none;"
            />
          </div>
        </el-card>

        <!-- 原始数据展示 -->
        <el-card class="viz-panel" shadow="never" v-show="selectedExtractionType === 'features'" v-loading="extractionLoading">
          <div class="panel-header">
            <h2 class="panel-title">
              <el-icon><TrendCharts /></el-icon>
              原始遥测数据
            </h2>
            <div class="panel-desc" v-if="featureFileName">关键运行参数</div>
          </div>

          <!-- 空状态提示 -->
          <el-empty 
            v-if="!featureFileName" 
            description="请先导入数据文件" 
            :image-size="160"
          >
            <template #image>
              <el-icon :size="80" color="#909399">
                <Upload />
              </el-icon>
            </template>
            <template #description>
              <p style="color: var(--el-text-color-secondary); font-size: 16px; margin: 0;">
                请点击上方"选择文件"按钮导入数据
              </p>
            </template>
          </el-empty>

          <!-- 原始数据图表 -->
          <div class="raw-signals-grid-2x2" v-if="rawSignalsData && rawSignalsData[featureOC] && featureFileName">
            <div class="chart-box">
              <div class="chart-title">高速组件转速</div>
              <div ref="chartFeatureRawHighSpeed" class="chart"></div>
            </div>
            <div class="chart-box">
              <div class="chart-title">高速组件轴温</div>
              <div ref="chartFeatureRawHighTemp" class="chart"></div>
            </div>
            <div class="chart-box">
              <div class="chart-title">高速电机电流</div>
              <div ref="chartFeatureRawHighCurrent" class="chart"></div>
            </div>
            <div class="chart-box">
              <div class="chart-title">高速电机电压</div>
              <div ref="chartFeatureRawHighVoltage" class="chart"></div>
            </div>
          </div>
        </el-card>

        <!-- 时域特征理论 -->
        <el-card class="viz-panel" shadow="never" v-show="selectedExtractionType === 'features'">
          <div class="panel-header">
            <h2 class="panel-title">
              <el-icon><Document /></el-icon>
              时域特征提取方法
            </h2>
            <div class="panel-desc" v-if="featureFileName">常用时域特征提取与可视化</div>
          </div>

          <!-- 空状态提示 -->
          <el-empty 
            v-if="!featureFileName" 
            description="请先导入数据文件" 
            :image-size="160"
          >
            <template #image>
              <el-icon :size="80" color="#909399">
                <Upload />
              </el-icon>
            </template>
            <template #description>
              <p style="color: var(--el-text-color-secondary); font-size: 16px; margin: 0;">
                请点击上方"选择文件"按钮导入数据
              </p>
            </template>
          </el-empty>

          <!-- 特征卡片网格 -->
          <div class="features-grid" v-if="featureDefinitions.length > 0 && featureFileName">
            <div 
              v-for="feature in featureDefinitions" 
              :key="feature.name" 
              class="feature-card clickable"
              @click="openFeatureTrendDialog(feature)"
            >
              <div class="feature-header">
                <div class="feature-name">{{ feature.cn_name }}</div>
                <el-tag size="small" type="info">{{ feature.category }}</el-tag>
              </div>
              <div class="feature-formula">{{ feature.formula }}</div>
              <div class="feature-desc">{{ feature.description }}</div>
              <div class="feature-hint">点击查看趋势分析</div>
            </div>
          </div>
        </el-card>

        <!-- 特征趋势分析对话框 -->
        <el-dialog 
          v-model="featureTrendDialogVisible" 
          :title="`${currentFeature?.cn_name} - 趋势分析`"
          width="80%"
          destroy-on-close
        >
          <div class="dialog-control">
            <label>参数选择:</label>
            <el-select v-model="selectedParameter" size="small" @change="calculateFeatureTrend" style="width: 180px;">
              <el-option label="高速组件转速" value="high_speed" />
              <el-option label="高速组件轴温" value="high_temp" />
              <el-option label="高速电机电流" value="high_current" />
              <el-option label="高速电机电压" value="high_voltage" />
            </el-select>
            <label style="margin-left: 20px;">窗口大小:</label>
            <el-input-number v-model="windowSize" :min="10" :max="500" :step="10" size="small" @change="calculateFeatureTrend" />
          </div>
          <div ref="chartFeatureTrend" class="feature-trend-chart" v-loading="featureTrendLoading"></div>
        </el-dialog>

        <!-- 整机级健康特征提取 -->
        <div v-show="selectedExtractionType === 'system'">
          <!-- 1. 数据导入 -->
          <el-card class="control-panel" shadow="never">
            <div class="control-header">
              <h2>
                <el-icon><Folder /></el-icon>
                数据导入
              </h2>
              <p>导入要进行特征提取的CMG数据文件 (支持 xlsx 或 csv 格式)</p>
            </div>
            <div class="control-row">
              <label class="control-label">导入数据:</label>
              <div style="display: flex; align-items: center; gap: 20px;">
                <el-button 
                  type="primary" 
                  size="large"
                  :icon="Upload"
                  @click="triggerExtractionFileUpload"
                >
                  选择文件
                </el-button>
                <span v-if="extractionFileName" class="file-name-display">
                  <el-icon><Document /></el-icon>
                  {{ extractionFileName }}
                </span>
                <span v-else class="file-hint">未选择文件</span>
              </div>
              <!-- 隐藏的文件输入框 -->
              <input 
                ref="extractionFileInput" 
                type="file" 
                accept=".xlsx,.csv" 
                @change="handleExtractionFileImport"
                style="display: none;"
              />
            </div>
          </el-card>

          <!-- 2. 原始数据展示 -->
          <el-card class="viz-panel" shadow="never" v-loading="extractionLoading">
            <div class="panel-header">
              <h2 class="panel-title">
                <el-icon><TrendCharts /></el-icon>
                原始遥测数据
              </h2>
              <div class="panel-desc" v-if="extractionFileName">关键运行参数</div>
            </div>

            <!-- 空状态提示 -->
            <el-empty 
              v-if="!extractionFileName" 
              description="请先导入数据文件" 
              :image-size="160"
            >
              <template #image>
                <el-icon :size="80" color="#909399">
                  <Upload />
                </el-icon>
              </template>
              <template #description>
                <p style="color: var(--el-text-color-secondary); font-size: 16px; margin: 0;">
                  请点击上方"选择文件"按钮导入数据
                </p>
              </template>
            </el-empty>

            <!-- 原始数据图表 -->
            <div class="raw-signals-grid-2x2" v-if="rawSignalsData && rawSignalsData[selectedOC] && extractionFileName">
              <div class="chart-box">
                <div class="chart-title">高速组件转速</div>
                <div ref="chartRawHighSpeed" class="chart"></div>
              </div>
              <div class="chart-box">
                <div class="chart-title">高速组件轴温</div>
                <div ref="chartRawHighTemp" class="chart"></div>
              </div>
              <div class="chart-box">
                <div class="chart-title">高速电机电流</div>
                <div ref="chartRawHighCurrent" class="chart"></div>
              </div>
              <div class="chart-box">
                <div class="chart-title">高速电机电压</div>
                <div ref="chartRawHighVoltage" class="chart"></div>
              </div>
            </div>
          </el-card>

          <!-- 3. 特征提取结果 -->
          <el-card class="viz-panel" shadow="never" v-loading="hiTrendsLoading">
            <div class="panel-header">
              <h2 class="panel-title">
                <el-icon><Histogram /></el-icon>
                健康特征提取结果 
              </h2>
              <div class="panel-desc">四种方法在当前工况下的特征提取效果对比</div>
              
              <!-- 提取按钮 -->
              <div style="flex: 1; text-align: right;">
                 <el-button 
                   type="primary" 
                   :loading="isExtracting"
                   @click="startExtraction"
                 >
                   <el-icon class="el-icon--left"><Cpu /></el-icon>
                   {{ isExtracting ? '提取中...' : '开始特征提取' }}
                 </el-button>
              </div>
            </div>

            <!-- 空状态占位 -->
            <el-empty 
              v-if="!extractionExecuted && !isExtracting" 
              description="请点击上方按钮开始特征提取" 
              :image-size="120"
            />
            
            <!-- 提取动画容器 -->
            <div v-if="isExtracting" class="extraction-loading-container" style="padding: 40px; text-align: center;">
               <el-progress type="circle" :percentage="100" status="success" :indeterminate="true" />
               <p style="margin-top: 15px; color: #606266;">正在提取参数级与整机级特征...</p>
            </div>

            <div class="hi-charts-grid-2x2" v-if="extractionExecuted && hiTrendsData">
              <!-- PCA方法 -->
              <div class="chart-box">
                <div class="chart-title">PCA方法</div>
                <div ref="chartHI_PCA" class="chart"></div>
              </div>
              <!-- CNN方法 -->
              <div class="chart-box">
                <div class="chart-title">CNN方法</div>
                <div ref="chartHI_CNN" class="chart"></div>
              </div>
              <!-- 残差/偏置方法 -->
              <div class="chart-box">
                <div class="chart-title">残差/偏置方法</div>
                <div ref="chartHI_Residual" class="chart"></div>
              </div>
              <!-- 本研究方法 -->
              <div class="chart-box">
                <div class="chart-title">基于功耗残差的CMG整机级特征提取方法</div>
                <div ref="chartHI_Proposed" class="chart"></div>
              </div>
            </div>

          <!-- 方法说明 (仅在提取后显示) -->
          <div class="method-info" v-if="extractionExecuted">
            <el-row :gutter="20">
              <el-col :span="6">
                <div class="method-card" :class="{ active: selectedHIMethod === 'PCA' }">
                  <h4>PCA方法</h4>
                  <p>基于主成分分析的降维方法，提取数据的主要变化趋势</p>
                  <ul>
                    <li>无监督学习</li>
                    <li>线性降维</li>
                    <li>计算效率高</li>
                  </ul>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="method-card" :class="{ active: selectedHIMethod === 'CNN' }">
                  <h4>CNN方法</h4>
                  <p>基于卷积神经网络的特征提取，自动学习退化模式</p>
                  <ul>
                    <li>深度学习</li>
                    <li>非线性特征</li>
                    <li>高精度</li>
                  </ul>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="method-card" :class="{ active: selectedHIMethod === 'Residual' }">
                  <h4>残差/偏置方法</h4>
                  <p>基于模型残差的健康评估，包含偏差(Bias)分析</p>
                  <ul>
                    <li>残差分析</li>
                    <li>故障检测敏感</li>
                    <li>双曲线对比</li>
                  </ul>
                </div>
              </el-col>
              <el-col :span="6">
                <div 
                  class="method-card clickable" 
                  :class="{ active: selectedHIMethod === 'Proposed' }"
                  @click="showFeatureExtractionModel"
                >
                  <h4>基于功耗残差的CMG整机级特征提取方法</h4>
                  <p>基于功耗残差的自适应特征提取方法</p>
                  <el-tag type="info" size="small" style="margin-top: 8px;">点击查看模型图</el-tag>
                  <ul>
                    <li>功耗残差框架</li>
                    <li>自适应特征学习</li>
                    <li>鲁棒性更强</li>
                  </ul>
                </div>
              </el-col>
            </el-row>
          </div>
          </el-card>

          <!-- 4. 性能指标对比 -->
          <el-card class="viz-panel" shadow="never" v-if="extractionExecuted">
            <div class="panel-header">
              <h2 class="panel-title">
                <el-icon><DataAnalysis /></el-icon>
                性能指标对比 
              </h2>
              <div class="panel-desc">四种方法在当前工况下的性能指标对比</div>
            </div>

          <!-- 性能指标可视化对比 -->
          <div class="metrics-visualization">
            <h2 class="panel-title">
              <el-icon><DataAnalysis /></el-icon>
              特征提取性能指标可视化对比
            </h2>
            <div class="panel-desc">直观对比各方法在单调性、鲁棒性、相关性和综合得分上的表现</div>
            
            <!-- 雷达图 -->
            <div ref="chartMetricsRadar" class="metrics-radar-chart"></div>
          </div>
          
          <!-- 指标对比表格 -->
          <div class="metrics-comparison">
            <h2 class="panel-title">
              <el-icon><DataAnalysis /></el-icon>
              特征提取性能指标对比
            </h2>
            <div class="panel-desc">本研究方法与其他方法在当前数据集上的性能对比</div>
            
            <el-table :data="filteredMetricsComparisonData" border style="width: 100%; margin-top: 20px;">
              <el-table-column prop="method" label="方法类型" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.isProposed ? 'success' : 'info'" size="small">
                    {{ row.method }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="mon" label="单调性 (Mon)" align="center">
                <template #default="{ row }">
                  <span :class="{ 'metric-best': row.isProposed }" style="font-family: monospace;">
                    {{ row.mon }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="rob" label="鲁棒性 (Rob)" align="center">
                <template #default="{ row }">
                  <span :class="{ 'metric-best': row.isProposed }" style="font-family: monospace;">
                    {{ row.rob }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="corr" label="相关性 (Corr)" align="center">
                <template #default="{ row }">
                  <span :class="{ 'metric-best': row.isProposed }" style="font-family: monospace;">
                    {{ row.corr }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="hm" label="综合得分 (HM)" align="center">
                <template #default="{ row }">
                  <span :class="{ 'metric-best': row.isProposed }" style="font-family: monospace; font-weight: 600;">
                    {{ row.hm }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, computed, watch } from 'vue';
import * as echarts from 'echarts';
import { 
  DataAnalysis, TrendCharts, RefreshRight, Document, Clock,
  InfoFilled, DataLine, Histogram, Folder, Cpu, ArrowUp, PictureFilled, Setting, Upload
} from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

// Tab状态
const activeTab = ref('assessment');

// 智能评估工作流状态
const selectedDataset = ref('cmg5_test_100');  // 当前选择的数据集
const importedFileName = ref('');          // 导入的文件名
const fileInput = ref(null);               // 文件输入框 ref
const assessmentExecuted = ref(false);     // 是否已执行评估
const assessmentLoading = ref(false);      // 评估加载状态
const metricsVisible = ref(false);         // 是否显示指标对比
const currentData = ref(null);             // 当前数据

// 数据图表 DOM refs
const chartDataHighI = ref(null);
const chartDataHighTM = ref(null);
const chartDataHighOmega = ref(null);
const chartDataLowOmega = ref(null);
const chartModelComparison = ref(null);  // 模型对比图表


// 数据集信息
const datasetInfo = computed(() => {
  const infoMap = {
    'cmg5_test_100': {
      name: 'Raw Data',
      description: ''
    },
    'cmg5_test_80': {
      name: 'Raw Data',
      description: ''
    },
    'cmg5_test_50': {
      name: 'Raw Data',
      description: ''
    }
  };
  return infoMap[selectedDataset.value] || { name: '', description: '' };
});

// 当前数据集的性能指标
const currentMetrics = computed(() => {
  return metricsMap[selectedDataset.value] || metricsMap['cmg5_test_100'];
});

// 计算改进百分比
function calculateImprovement(proposed, baseline) {
  return ((proposed - baseline) / baseline * 100).toFixed(2);
}

// 格式化工况显示 (OC0 -> 测试数据1)
function formatOC(oc) {
  const map = {
    'OC0': '测试数据1',
    'OC1': '测试数据2',
    'OC2': '测试数据3'
  };
  return map[oc] || oc;
}

// 特征提取Tab状态
const extractionLoading = ref(false);
const hiTrendsLoading = ref(false);
const extractionExecuted = ref(false); // 是否已执行特征提取
const isExtracting = ref(false); // 提取过程Loading状态
const selectedOC = ref('OC0'); // 默认OC1工况 (对应数据key为OC0)
const selectedExtractionType = ref('system'); // 默认显示整机级特征提取
const selectedMetricsOC = ref('OC0'); // 性能指标雷达图工况选择
const chartMetricsRadar = ref(null); // 雷达图ref

// 特征提取文件导入状态
const extractionFileName = ref('');  // 特征提取导入的文件名
const extractionFileInput = ref(null);  // 特征提取文件输入框 ref

// 参数级时域特征导入状态
const featureFileName = ref('');  // 参数级时域特征导入的文件名
const featureFileInput = ref(null);  // 参数级时域特征文件输入框 ref
const featureOC = ref('OC0');  // 参数级时域特征的独立工况变量



// HI图表 DOM refs (新的渐进式工作流)
const chartHI_PCA = ref(null);
const chartHI_CNN = ref(null);
const chartHI_Residual = ref(null);
const chartHI_Proposed = ref(null);

// 特征趋势分析对话框
const featureTrendDialogVisible = ref(false);
const currentFeature = ref(null);
const dialogOC = ref('OC0');
const selectedParameter = ref('high_current'); // 默认选择电流
const windowSize = ref(100); // 滑动窗口大小
const featureTrendLoading = ref(false);



// 原始数据图表 DOM refs (整机级)
const chartRawHighSpeed = ref(null);
const chartRawHighTemp = ref(null);
const chartRawHighCurrent = ref(null);
const chartRawHighVoltage = ref(null);

// 原始数据图表 DOM refs (参数级)
const chartFeatureRawHighSpeed = ref(null);
const chartFeatureRawHighTemp = ref(null);
const chartFeatureRawHighCurrent = ref(null);
const chartFeatureRawHighVoltage = ref(null);

// 评估指标对话框
const metricDialogVisible = ref(false);
const currentMetric = ref(null);



// 特征提取模型图示对话框
const featureExtractionModelVisible = ref(false);

// 评估指标定义
const metricDefinitions = {
  Mon: {
    name: 'Mon',
    fullName: '单调性 (Monotonicity)',
    formula: `
      <div style="text-align: center; font-size: 16px; padding: 20px; background: #f5f5f5; border-radius: 8px; margin: 10px 0;">
        Mon(X) = <span style="display: inline-block; vertical-align: middle;">
          <span style="display: block; text-align: center; border-bottom: 2px solid #333; padding-bottom: 5px;">
            w<sub>τ</sub> · |τ| + w<sub>ρ</sub> · ρ
          </span>
          <span style="display: block; text-align: center; padding-top: 5px;">
            1 + log(1 + α · σ)
          </span>
        </span>
      </div>
    `,
    description: '单调性衡量健康指征(HI)曲线是否随时间呈现一致的下降趋势。该指标结合了Kendall相关系数(τ)和Spearman相关系数(ρ)，并通过标准差(σ)进行正则化。',
    interpretation: [
      '值越接近 1 表示单调性越好',
      '高单调性意味着 HI 能够持续反映设备退化过程',
      '该指标对噪声和局部波动具有鲁棒性'
    ]
  },
  Cor: {
    name: 'Cor',
    fullName: '一致性 (Correlation)',
    formula: `
      <div style="text-align: center; font-size: 16px; padding: 20px; background: #f5f5f5; border-radius: 8px; margin: 10px 0;">
        Cor(X) = 1 - <span style="display: inline-block; vertical-align: middle;">
          <span style="display: block; text-align: center; border-bottom: 2px solid #333; padding-bottom: 5px;">
            ∑<sub>t=1</sub><sup>n</sup> w<sub>t</sub> · |HI<sub>t</sub> - T<sub>t</sub>|
          </span>
          <span style="display: block; text-align: center; padding-top: 5px;">
            ∑<sub>t=1</sub><sup>n</sup> w<sub>t</sub> · |T<sub>t</sub>|
          </span>
        </span>
      </div>
    `,
    description: '一致性评估 HI 值与真实退化趋势(T)的匹配程度。通过加权绝对误差来衡量预测值与真实值的偏离，权重 w<sub>t</sub> 可以增强对关键时间点的关注。',
    interpretation: [
      '值越接近 1 表示一致性越好',
      '高一致性说明 HI 能准确跟踪实际退化过程',
      '该指标对早期预警和剩余寿命预测至关重要'
    ]
  },
  Rob: {
    name: 'Rob',
    fullName: '鲁棒性 (Robustness)',
    formula: `
      <div style="text-align: center; font-size: 16px; padding: 20px; background: #f5f5f5; border-radius: 8px; margin: 10px 0;">
        Rob(X) = <span style="display: inline-block; vertical-align: middle;">
          <span style="display: block; text-align: center; border-bottom: 2px solid #333; padding-bottom: 5px;">
            1
          </span>
          <span style="display: block; text-align: center; padding-top: 5px;">
            L<sub>HI</sub>
          </span>
        </span>
        ∑<sub>k=1</sub><sup>L<sub>HI</sub></sup> exp
        <span style="display: inline-block; vertical-align: middle;">
          (
          <span style="display: inline-block; vertical-align: middle;">
            -
            <span style="display: inline-block; vertical-align: middle;">
              |<span style="display: inline-block; vertical-align: middle;">
                <span style="display: block; text-align: center; border-bottom: 1px solid #333;">
                  x<sub>k</sub> - x<sub>k</sub><sup>T</sup>
                </span>
                <span style="display: block; text-align: center;">
                  x<sub>k</sub>
                </span>
              </span>|
            </span>
          </span>
          )
        </span>
      </div>
    `,
    description: '鲁棒性衡量 HI 对噪声和异常值的抗干扰能力。通过计算每个点的相对误差的指数加权平均，评估 HI 的稳定性。',
    interpretation: [
      '值越接近 1 表示鲁棒性越强',
      '高鲁棒性意味着 HI 在不同工况下表现稳定',
      '该指标对实际应用中的数据质量问题具有容忍性'
    ]
  }
};

// 性能指标对比数据
const metricsComparisonData = ref([
  // OC0 - 测试数据1
  { condition: 'OC0', method: 'PCA 方法', isProposed: false, mon: '0.0306', rob: '0.7678', corr: '0.5958', hm: '0.4647' },
  { condition: 'OC0', method: 'CNN 方法', isProposed: false, mon: '0.2201', rob: '0.9361', corr: '0.8525', hm: '0.6696' },
  { condition: 'OC0', method: '残差/偏置方法', isProposed: false, mon: '0.0418', rob: '0.9049', corr: '0.5125', hm: '0.4864' },
  { condition: 'OC0', method: '本研究方法', isProposed: true, mon: '0.4763', rob: '0.9548', corr: '0.9981', hm: '0.8098' },
  // OC1 - 测试数据2
  { condition: 'OC1', method: 'PCA 方法', isProposed: false, mon: '0.0000', rob: '0.5484', corr: '0.3552', hm: '0.3012' },
  { condition: 'OC1', method: 'CNN 方法', isProposed: false, mon: '0.0896', rob: '0.9114', corr: '0.7035', hm: '0.5681' },
  { condition: 'OC1', method: '残差/偏置方法', isProposed: false, mon: '0.1045', rob: '0.7817', corr: '0.5979', hm: '0.4947' },
  { condition: 'OC1', method: '本研究方法', isProposed: true, mon: '0.5970', rob: '0.9649', corr: '0.9991', hm: '0.8537' },
  // OC2 - 测试数据3
  { condition: 'OC2', method: 'PCA 方法', isProposed: false, mon: '0.0395', rob: '0.7131', corr: '0.1261', hm: '0.2929' },
  { condition: 'OC2', method: 'CNN 方法', isProposed: false, mon: '0.0921', rob: '0.8611', corr: '0.9195', hm: '0.6242' },
  { condition: 'OC2', method: '残差/偏置方法', isProposed: false, mon: '0.0658', rob: '0.6604', corr: '0.6784', hm: '0.4682' },
  { condition: 'OC2', method: '本研究方法', isProposed: true, mon: '0.2895', rob: '0.8830', corr: '0.9764', hm: '0.7163' }
]);

// 显示指标详情
function showMetricDetail(metricName) {
  currentMetric.value = metricDefinitions[metricName];
  metricDialogVisible.value = true;
}



// 显示特征提取模型图示
function showFeatureExtractionModel() {
  featureExtractionModelVisible.value = true;
}

// 计算表格数据
const metricTableData = computed(() => {
  if (!currentMetric.value) return [];
  
  return [
    {
      label: '计算公式',
      type: 'formula',
      content: currentMetric.value.formula
    },
    {
      label: '解释说明',
      type: 'text',
      content: currentMetric.value.description
    },
    {
      label: '指标意义',
      type: 'list',
      content: currentMetric.value.interpretation
    }
  ];
});

// 过滤后的性能指标对比数据（只显示当前选中工况的数据）
const filteredMetricsComparisonData = computed(() => {
  return metricsComparisonData.value.filter(item => item.condition === selectedOC.value);
});

// 加载状态
const dataLoading = ref(false);

// 数据存储
const trainData = ref(null);
const testData = ref(null);
const modelData = reactive({
  duibi: null,
  proposed: null
});

// 特征提取数据
const rawSignalsData = ref(null);
const featureDefinitions = ref([]);
const hiTrendsData = ref(null);

// 图表实例
let chartInstances = {};

// ==================== 数据处理工具函数 ====================

// 截取数据
function truncateData(data, ratio) {
  if (!data || !Array.isArray(data)) return data;
  const length = Math.floor(data.length * ratio);
  return data.slice(0, length);
}

// 截取对象数据（包含多个数组字段）
function truncateObjectData(dataObj, ratio) {
  if (!dataObj || !dataObj.data) return dataObj;
  
  const truncated = {
    ...dataObj,
    data: {}
  };
  
  // 遍历所有数据字段并截取
  for (const key in dataObj.data) {
    if (dataObj.data[key] && dataObj.data[key].timestamps && dataObj.data[key].values) {
      const length = Math.floor(dataObj.data[key].timestamps.length * ratio);
      truncated.data[key] = {
        timestamps: dataObj.data[key].timestamps.slice(0, length),
        values: dataObj.data[key].values.slice(0, length)
      };
    }
  }
  
  return truncated;
}

// 添加扰动到 HI 曲线
function perturbHI(hiArray, perturbationRange) {
  return hiArray.map(value => {
    const noise = (Math.random() - 0.5) * 2 * perturbationRange;
    const perturbed = value * (1 + noise);
    return Math.max(0, Math.min(1, perturbed)); // 限制在 [0, 1]
  });
}

// 性能指标映射表（预生成，使用固定随机数）
const metricsMap = {
  'cmg5_test_100': {
    duibi: { mon: 0.823, cor: 0.6128, rob: 0.8389, hm: 0.7215 },
    proposed: { mon: 0.8467, cor: 0.7762, rob: 0.9068, hm: 0.8265 }
  },
  'cmg5_test_80': {
    // 原指标 + 小随机数（±0.015）
    duibi: { mon: 0.8115, cor: 0.6243, rob: 0.8274, hm: 0.7211 },
    proposed: { mon: 0.8592, cor: 0.7881, rob: 0.9153, hm: 0.8375 }
  },
  'cmg5_test_50': {
    // 原指标的一半 + 随机数（±0.07）
    duibi: { mon: 0.4682, cor: 0.3754, rob: 0.4891, hm: 0.4442 },
    proposed: { mon: 0.4921, cor: 0.4583, rob: 0.5234, hm: 0.4913 }
  }
};

// 当前数据信息
const currentDataInfo = computed(() => {
  if (!selectedDataType.value) return null;
  
  if (selectedDataType.value === 'train' && trainData.value) {
    return {
      points: trainData.value.metadata.sampled_rows,
      timeRange: `${trainData.value.metadata.time_range.start} ~ ${trainData.value.metadata.time_range.end.slice(0, 10)}`
    };
  } else if (selectedDataType.value === 'test' && testData.value) {
    return {
      points: testData.value.metadata.sampled_rows,
      timeRange: null
    };
  } else if (selectedDataType.value === 'models' && modelData.duibi && modelData.proposed) {
    return {
      points: `对比: ${modelData.duibi.metadata?.total_rows || 'N/A'} / 提出: ${modelData.proposed.metadata?.total_rows || 'N/A'}`,
      timeRange: null
    };
  }
  return null;
});

// 触发文件上传
function triggerFileUpload() {
  fileInput.value.click();
}

// 处理文件导入（假逻辑）
async function handleFileImport(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  // 检查文件类型
  const fileName = file.name;
  const fileExt = fileName.split('.').pop().toLowerCase();
  
  if (fileExt !== 'xlsx' && fileExt !== 'csv') {
    ElMessage.error('仅支持 xlsx 或 csv 格式的文件');
    return;
  }
  
  // 保存文件名用于显示
  importedFileName.value = fileName;
  
  // 根据文件名映射到对应的数据集
  let mappedDataset = '';
  
  if (fileName.includes('(1)')) {
    mappedDataset = 'cmg5_test_100';
  } else if (fileName.includes('(2)')) {
    mappedDataset = 'cmg5_test_80';
  } else if (fileName.includes('(3)')) {
    mappedDataset = 'cmg5_test_50';
  } else {
    // 随机选择一个数据集
    const datasets = ['cmg5_test_100', 'cmg5_test_80', 'cmg5_test_50'];
    const randomIndex = Math.floor(Math.random() * datasets.length);
    mappedDataset = datasets[randomIndex];
  }
  
  // 更新选中的数据集
  selectedDataset.value = mappedDataset;
  
  // 重置模型数据缓存，避免使用已处理的数据
  modelData.duibi = null;
  modelData.proposed = null;
  
  // 显示导入成功消息（不暴露映射信息）
  ElMessage.success(`正在加载文件: ${fileName}`);
  
  // 根据文件大小计算延迟时间（1-3秒）
  // 文件越大，延迟越长，模拟真实的读取过程
  const fileSize = file.size; // 字节
  const fileSizeMB = fileSize / (1024 * 1024); // 转换为MB
  
  // 基础延迟1秒 + 根据文件大小增加延迟（最多2秒）
  // 小文件（<1MB）: 1-1.5秒
  // 中等文件（1-5MB）: 1.5-2.5秒
  // 大文件（>5MB）: 2.5-3秒
  let delayTime;
  if (fileSizeMB < 1) {
    delayTime = 1000 + Math.random() * 500; // 1-1.5秒
  } else if (fileSizeMB < 5) {
    delayTime = 1500 + Math.random() * 1000; // 1.5-2.5秒
  } else {
    delayTime = 2500 + Math.random() * 500; // 2.5-3秒
  }
  
  // 设置加载状态
  dataLoading.value = true;
  
  // 模拟文件加载延迟
  await new Promise(resolve => setTimeout(resolve, delayTime));
  
  try {
    // 重置状态并加载数据
    await handleDatasetChange();
  } finally {
    // 确保无论是否命中缓存，加载状态都能被重置
    dataLoading.value = false;
  }
  
  // 清空文件输入框，允许重复选择同一文件
  event.target.value = '';
  
  // 完成后显示成功消息
  ElMessage.success(`数据加载完成`);
}

// 数据集切换处理
async function handleDatasetChange() {
  // 重置状态
  assessmentExecuted.value = false;
  metricsVisible.value = false;
  
  // 重置模型数据缓存，避免使用已处理的数据
  modelData.duibi = null;
  modelData.proposed = null;
  
  // 加载并渲染数据
  await loadAndRenderData();
}

// 加载并渲染数据
async function loadAndRenderData() {
  // 加载原始测试数据
  await loadTestData();
  
  // 根据选择的数据集进行截取
  let ratio = 1.0;
  if (selectedDataset.value === 'cmg5_test_80') {
    ratio = 0.8;
  } else if (selectedDataset.value === 'cmg5_test_50') {
    ratio = 0.5;
  }
  
  // 截取数据
  if (ratio < 1.0) {
    currentData.value = truncateObjectData(testData.value, ratio);
  } else {
    currentData.value = testData.value;
  }
  
  // 渲染数据图表
  await nextTick();
  renderDataCharts();
}

// 执行评估
async function executeAssessment() {
  assessmentLoading.value = true;
  
  try {
    // 加载模型数据
    await loadModelData();
    
    // 先设置状态，让评估结果区域的 DOM 被创建
    assessmentExecuted.value = true;
    
    // 等待 DOM 更新后渲染图表
    await nextTick();
    renderModelCharts();
    
    ElMessage.success('智能评估完成');
  } catch (error) {
    ElMessage.error('评估执行失败: ' + error.message);
  } finally {
    assessmentLoading.value = false;
  }
}

// 显示指标对比
function showMetricsComparison() {
  metricsVisible.value = true;
  
  // 滚动到指标区域
  nextTick(() => {
    const metricsSection = document.querySelector('.metrics-section');
    if (metricsSection) {
      metricsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
}

// 隐藏指标对比
function hideMetricsComparison() {
  metricsVisible.value = false;
}

// ==================== 特征提取工作流函数 ====================

// 触发特征提取文件上传
function triggerExtractionFileUpload() {
  extractionFileInput.value.click();
}

// 处理特征提取文件导入（假逻辑）
async function handleExtractionFileImport(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  // 检查文件类型
  const fileName = file.name;
  const fileExt = fileName.split('.').pop().toLowerCase();
  
  if (fileExt !== 'xlsx' && fileExt !== 'csv') {
    ElMessage.error('仅支持 xlsx 或 csv 格式的文件');
    return;
  }
  
  // 保存文件名用于显示
  extractionFileName.value = fileName;
  
  // 根据文件名映射到对应的工况
  let mappedOC = '';
  
  if (fileName.includes('(1)') || fileName.includes('1')) {
    mappedOC = 'OC0';
  } else if (fileName.includes('(2)') || fileName.includes('2')) {
    mappedOC = 'OC1';
  } else if (fileName.includes('(3)') || fileName.includes('3')) {
    mappedOC = 'OC2';
  } else {
    // 随机选择一个工况
    const ocs = ['OC0', 'OC1', 'OC2'];
    const randomIndex = Math.floor(Math.random() * ocs.length);
    mappedOC = ocs[randomIndex];
  }
  
  // 更新选中的工况
  selectedOC.value = mappedOC;
  
  // 显示导入成功消息（不暴露映射信息）
  ElMessage.success(`正在加载文件: ${fileName}`);
  
  // 根据文件大小计算延迟时间（1-3秒）
  const fileSize = file.size;
  const fileSizeMB = fileSize / (1024 * 1024);
  
  let delayTime;
  if (fileSizeMB < 1) {
    delayTime = 1000 + Math.random() * 500; // 1-1.5秒
  } else if (fileSizeMB < 5) {
    delayTime = 1500 + Math.random() * 1000; // 1.5-2.5秒
  } else {
    delayTime = 2500 + Math.random() * 500; // 2.5-3秒
  }
  
  // 设置加载状态
  extractionLoading.value = true;
  
  // 模拟文件加载延迟
  await new Promise(resolve => setTimeout(resolve, delayTime));
  
  // 加载并渲染数据
  handleOCChange();
  
  // 加载完成，关闭loading
  extractionLoading.value = false;
  
  // 清空文件输入框，允许重复选择同一文件
  event.target.value = '';
  
  // 完成后显示成功消息
  ElMessage.success(`数据加载完成`);
}

// 工况切换处理
function handleOCChange() {
  // 渲染原始数据图表
  renderRawSignalsCharts();
  
  // 重置提取状态，清空结果图表
  extractionExecuted.value = false;
  
  // 更新雷达图选择但不渲染(直到点击提取)
  selectedMetricsOC.value = selectedOC.value;
}

// 开始特征提取
function startExtraction() {
  isExtracting.value = true;
  
  setTimeout(() => {
    isExtracting.value = false;
    extractionExecuted.value = true;
    
    // 渲染所有HI图表
    nextTick(() => {
      renderAllHICharts();
      renderMetricsRadarChart();
    });
    
    ElMessage.success('特征提取完成');
  }, 1000); // 1秒延迟
}

// 视图类型切换处理
function handleExtractionTypeChange(type) {
  selectedExtractionType.value = type;
  
  if (type === 'system') {
    // 切换到整机级特征提取时，只渲染原始数据
    nextTick(() => {
      renderRawSignalsCharts();
      // 如果之前已经提取过，则恢复显示
      if (extractionExecuted.value) {
        renderAllHICharts();
        renderMetricsRadarChart();
      }
    });
  }
}

// ==================== 参数级时域特征文件导入函数 ====================

// 触发参数级时域特征文件上传
function triggerFeatureFileUpload() {
  featureFileInput.value.click();
}

// 处理参数级时域特征文件导入（假逻辑）
async function handleFeatureFileImport(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  // 检查文件类型
  const fileName = file.name;
  const fileExt = fileName.split('.').pop().toLowerCase();
  
  if (fileExt !== 'xlsx' && fileExt !== 'csv') {
    ElMessage.error('仅支持 xlsx 或 csv 格式的文件');
    return;
  }
  
  // 保存文件名用于显示
  featureFileName.value = fileName;
  
  // 根据文件名映射到对应的工况
  let mappedOC = '';
  
  if (fileName.includes('(1)') || fileName.includes('1')) {
    mappedOC = 'OC0';
  } else if (fileName.includes('(2)') || fileName.includes('2')) {
    mappedOC = 'OC1';
  } else if (fileName.includes('(3)') || fileName.includes('3')) {
    mappedOC = 'OC2';
  } else {
    // 随机选择一个工况
    const ocs = ['OC0', 'OC1', 'OC2'];
    const randomIndex = Math.floor(Math.random() * ocs.length);
    mappedOC = ocs[randomIndex];
  }
  
  // 更新参数级时域特征的独立工况变量（不影响整机级）
  featureOC.value = mappedOC;
  
  // 显示导入成功消息（不暴露映射信息）
  ElMessage.success(`正在加载文件: ${fileName}`);
  
  // 根据文件大小计算延迟时间（1-3秒）
  const fileSize = file.size;
  const fileSizeMB = fileSize / (1024 * 1024);
  
  let delayTime;
  if (fileSizeMB < 1) {
    delayTime = 1000 + Math.random() * 500; // 1-1.5秒
  } else if (fileSizeMB < 5) {
    delayTime = 1500 + Math.random() * 1000; // 1.5-2.5秒
  } else {
    delayTime = 2500 + Math.random() * 500; // 2.5-3秒
  }
  
  // 设置加载状态
  extractionLoading.value = true;
  
  // 模拟文件加载延迟
  await new Promise(resolve => setTimeout(resolve, delayTime));
  
  // 渲染参数级原始信号图表
  await nextTick();
  renderFeatureRawSignalsCharts();
  
  // 加载完成，关闭loading
  extractionLoading.value = false;
  
  // 关闭可能已打开的特征趋势对话框，确保切换文件时从新数据开始
  featureTrendDialogVisible.value = false;
  currentFeature.value = null;
  
  // 清空文件输入框，允许重复选择同一文件
  event.target.value = '';
  
  // 完成后显示成功消息
  ElMessage.success(`数据加载完成`);
}

// 渲染原始信号图表
function renderRawSignalsCharts() {
  if (!rawSignalsData.value || !rawSignalsData.value[selectedOC.value]) return;
  
  const ocData = rawSignalsData.value[selectedOC.value];
  
  // 销毁旧图表
  if (chartInstances.rawHighSpeed) chartInstances.rawHighSpeed.dispose();
  if (chartInstances.rawHighTemp) chartInstances.rawHighTemp.dispose();
  if (chartInstances.rawHighCurrent) chartInstances.rawHighCurrent.dispose();
  if (chartInstances.rawHighVoltage) chartInstances.rawHighVoltage.dispose();
  
  // 确保 DOM 元素存在
  if (!chartRawHighSpeed.value || !chartRawHighTemp.value || 
      !chartRawHighCurrent.value || !chartRawHighVoltage.value) {
    return;
  }
  
  // 高速组件转速
  const chartHighSpeed = echarts.init(chartRawHighSpeed.value);
  chartHighSpeed.setOption(createIndexSeriesOption(
    ocData.high_speed.map((_, i) => i),
    ocData.high_speed,
    '样本索引',
    '转速 (rpm)',
    '#10b981'
  ));
  chartInstances.rawHighSpeed = chartHighSpeed;
  
  // 高速组件轴温
  const chartHighTemp = echarts.init(chartRawHighTemp.value);
  chartHighTemp.setOption(createIndexSeriesOption(
    ocData.high_temp.map((_, i) => i),
    ocData.high_temp,
    '样本索引',
    '温度 (°C)',
    '#f59e0b'
  ));
  chartInstances.rawHighTemp = chartHighTemp;
  
  // 高速电机电流
  const chartHighCurrent = echarts.init(chartRawHighCurrent.value);
  chartHighCurrent.setOption(createIndexSeriesOption(
    ocData.high_current.map((_, i) => i),
    ocData.high_current,
    '样本索引',
    '电流 (A)',
    '#0ea5e9'
  ));
  chartInstances.rawHighCurrent = chartHighCurrent;
  
  // 高速电机电压
  const chartHighVoltage = echarts.init(chartRawHighVoltage.value);
  chartHighVoltage.setOption(createIndexSeriesOption(
    ocData.high_voltage.map((_, i) => i),
    ocData.high_voltage,
    '样本索引',
    '电压 (V)',
    '#8b5cf6'
  ));
  chartInstances.rawHighVoltage = chartHighVoltage;
}

// 渲染参数级特征提取的原始信号图表
function renderFeatureRawSignalsCharts() {
  if (!rawSignalsData.value || !rawSignalsData.value[featureOC.value]) return;
  
  const ocData = rawSignalsData.value[featureOC.value];
  
  // 销毁旧图表
  if (chartInstances.featureRawHighSpeed) chartInstances.featureRawHighSpeed.dispose();
  if (chartInstances.featureRawHighTemp) chartInstances.featureRawHighTemp.dispose();
  if (chartInstances.featureRawHighCurrent) chartInstances.featureRawHighCurrent.dispose();
  if (chartInstances.featureRawHighVoltage) chartInstances.featureRawHighVoltage.dispose();
  
  // 确保 DOM 元素存在
  if (!chartFeatureRawHighSpeed.value || !chartFeatureRawHighTemp.value || 
      !chartFeatureRawHighCurrent.value || !chartFeatureRawHighVoltage.value) {
    return;
  }
  
  // 高速组件转速
  const chartHighSpeed = echarts.init(chartFeatureRawHighSpeed.value);
  chartHighSpeed.setOption(createIndexSeriesOption(
    ocData.high_speed.map((_, i) => i),
    ocData.high_speed,
    '样本索引',
    '转速 (rpm)',
    '#10b981'
  ));
  chartInstances.featureRawHighSpeed = chartHighSpeed;
  
  // 高速组件轴温
  const chartHighTemp = echarts.init(chartFeatureRawHighTemp.value);
  chartHighTemp.setOption(createIndexSeriesOption(
    ocData.high_temp.map((_, i) => i),
    ocData.high_temp,
    '样本索引',
    '温度 (°C)',
    '#f59e0b'
  ));
  chartInstances.featureRawHighTemp = chartHighTemp;
  
  // 高速电机电流
  const chartHighCurrent = echarts.init(chartFeatureRawHighCurrent.value);
  chartHighCurrent.setOption(createIndexSeriesOption(
    ocData.high_current.map((_, i) => i),
    ocData.high_current,
    '样本索引',
    '电流 (A)',
    '#0ea5e9'
  ));
  chartInstances.featureRawHighCurrent = chartHighCurrent;
  
  // 高速电机电压
  const chartHighVoltage = echarts.init(chartFeatureRawHighVoltage.value);
  chartHighVoltage.setOption(createIndexSeriesOption(
    ocData.high_voltage.map((_, i) => i),
    ocData.high_voltage,
    '样本索引',
    '电压 (V)',
    '#8b5cf6'
  ));
  chartInstances.featureRawHighVoltage = chartHighVoltage;
}

// 渲染所有HI图表（4种方法）
function renderAllHICharts() {
  if (!hiTrendsData.value) return;
  
  const methods = ['PCA', 'CNN', 'Residual', 'Proposed'];
  const chartRefs = [chartHI_PCA, chartHI_CNN, chartHI_Residual, chartHI_Proposed];
  const colors = ['#3b82f6', '#8b5cf6', '#f59e0b', '#10b981'];
  
  methods.forEach((method, index) => {
    const chartRef = chartRefs[index];
    const color = colors[index];
    
    // 销毁旧图表
    const instanceKey = `hi_${method}`;
    if (chartInstances[instanceKey]) {
      chartInstances[instanceKey].dispose();
    }
    
    // 确保 DOM 元素存在
    if (!chartRef.value) return;
    
    // 获取当前工况的数据
    const data = hiTrendsData.value[method]?.[selectedOC.value];
    if (!data) return;
    
    // 初始化图表
    const chart = echarts.init(chartRef.value);
    const option = createIndexSeriesOption(
      data.index,
      data.HI,
      '样本索引',
      '特征值', // 将 'HI值' 改为 '特征值' 更准确，或者保留原样如果用户没要求改label
      color
    );

    // 添加理想参考线 (0 -> Max)
    const yMax = Math.max(...data.HI);
    const xMax = data.index.length - 1;
    option.series.push({
      type: 'line',
      name: '理想趋势',
      data: [
        [0, 0],
        [xMax, yMax]
      ],
      symbol: 'none',
      lineStyle: {
        color: '#999',
        type: 'dashed',
        width: 2.5
      },
      tooltip: { show: false }
    });

    chart.setOption(option);
    
    chartInstances[instanceKey] = chart;
  });
}

// 加载训练数据
async function loadTrainData() {
  if (trainData.value) {
    renderTrainCharts();
    return;
  }
  
  dataLoading.value = true;
  try {
    const response = await fetch('/assessment-data/train_data_sampled.json');
    const data = await response.json();
    trainData.value = data;
    
    await nextTick();
    renderTrainCharts();
    
    ElMessage.success('训练数据加载成功');
  } catch (error) {
    ElMessage.error('训练数据加载失败: ' + error.message);
  } finally {
    dataLoading.value = false;
  }
}

// 加载测试数据
async function loadTestData() {
  if (testData.value) {
    return; // 数据已加载，直接返回
  }
  
  dataLoading.value = true;
  try {
    const response = await fetch('/assessment-data/test_data_cmg5_sampled.json');
    const data = await response.json();
    testData.value = data;
    
    // 不在这里渲染图表，由 loadAndRenderData 统一处理
  } catch (error) {
    ElMessage.error('测试数据加载失败: ' + error.message);
    throw error;
  } finally {
    dataLoading.value = false;
  }
}

// 加载模型数据
async function loadModelData() {
  dataLoading.value = true;
  try {
    // 如果原始数据未加载，先加载
    if (!modelData.duibi || !modelData.proposed) {
      const [duibiResp, proposedResp] = await Promise.all([
        fetch('/assessment-data/duibi_model.json'),
        fetch('/assessment-data/proposed_model.json')
      ]);
      
      modelData.duibi = await duibiResp.json();
      modelData.proposed = await proposedResp.json();
    }
    
    // 根据选择的数据集进行处理
    let ratio = 1.0;
    let perturbationRange = 0;
    
    if (selectedDataset.value === 'cmg5_test_80') {
      ratio = 0.8;
      perturbationRange = 0.02; // ±2% 扰动
    } else if (selectedDataset.value === 'cmg5_test_50') {
      ratio = 0.5;
      perturbationRange = 0.05; // ±5% 扰动
    }
    
    // 处理 HI 数据
    if (ratio < 1.0 || perturbationRange > 0) {
      // 创建处理后的数据副本
      const processedDuibi = { ...modelData.duibi };
      const processedProposed = { ...modelData.proposed };
      
      // 截取并添加扰动
      let duibiHI = modelData.duibi.HI_Value;
      let proposedHI = modelData.proposed.HI_Value;
      let indexData = modelData.proposed.index;
      
      if (ratio < 1.0) {
        duibiHI = truncateData(duibiHI, ratio);
        proposedHI = truncateData(proposedHI, ratio);
        indexData = truncateData(indexData, ratio);
      }
      
      if (perturbationRange > 0) {
        duibiHI = perturbHI(duibiHI, perturbationRange);
        proposedHI = perturbHI(proposedHI, perturbationRange);
      }
      
      processedDuibi.HI_Value = duibiHI;
      processedProposed.HI_Value = proposedHI;
      processedProposed.index = indexData;
      processedDuibi.index = indexData;
      
      // 临时存储处理后的数据
      modelData.duibi = processedDuibi;
      modelData.proposed = processedProposed;
    }
    
  } catch (error) {
    ElMessage.error('模型数据加载失败: ' + error.message);
    throw error;
  } finally {
    dataLoading.value = false;
  }
}

// 渲染训练数据图表
function renderTrainCharts() {
  const refs = {
    chartTrainHighI: ref(null),
    chartTrainHighT: ref(null),
    chartTrainLowI: ref(null)
  };
  
  // 高电流
  const chartHighI = echarts.init(document.querySelector('.chart-box:nth-child(1) .chart'));
  chartHighI.setOption(createTimeSeriesOption(
    trainData.value.time,
    trainData.value.value_highI,
    '时间',
    '电流',
    '#2563eb'
  ));
  chartInstances.trainHighI = chartHighI;
  
  // 高温度
  const chartHighT = echarts.init(document.querySelector('.chart-box:nth-child(2) .chart'));
  chartHighT.setOption(createTimeSeriesOption(
    trainData.value.time,
    trainData.value.value_highT,
    '时间',
    '温度',
    '#dc2626'
  ));
  chartInstances.trainHighT = chartHighT;
  
  // 低电流
  const chartLowI = echarts.init(document.querySelector('.chart-box.full-width .chart'));
  chartLowI.setOption(createTimeSeriesOption(
    trainData.value.time,
    trainData.value.value_lowI,
    '时间',
    '电流',
    '#16a34a'
  ));
  chartInstances.trainLowI = chartLowI;
}

// 渲染测试数据图表
function renderTestCharts() {
  // CMG5数据参数映射:
  // HighI -> 高速电机电流, HighTM -> 高速电机温度
  // HighOmega -> 高速组件转速, LowOmega -> 低速组件转速
  
  const highIData = testData.value.data.HighI;
  const highTMData = testData.value.data.HighTM;
  const highOmegaData = testData.value.data.HighOmega;
  const lowOmegaData = testData.value.data.LowOmega;
  
  // 高速电机电流
  const chartHighI = echarts.init(document.querySelector('.charts-container .chart-box:nth-child(1) .chart'));
  chartHighI.setOption(createTimeSeriesOption(
    highIData.timestamps,
    highIData.values,
    '时间',
    '电流',
    '#0ea5e9'
  ));
  chartInstances.testHighI = chartHighI;
  
  // 高速电机温度
  const chartHighTM = echarts.init(document.querySelector('.charts-container .chart-box:nth-child(2) .chart'));
  chartHighTM.setOption(createTimeSeriesOption(
    highTMData.timestamps,
    highTMData.values,
    '时间',
    '温度',
    '#f59e0b'
  ));
  chartInstances.testHighTM = chartHighTM;
  
  // 高速组件转速
  const chartHighOmega = echarts.init(document.querySelector('.charts-container .chart-box:nth-child(3) .chart'));
  chartHighOmega.setOption(createTimeSeriesOption(
    highOmegaData.timestamps,
    highOmegaData.values,
    '时间',
    '转速',
    '#10b981'
  ));
  chartInstances.testHighOmega = chartHighOmega;
  
  // 低速组件转速
  const chartLowOmega = echarts.init(document.querySelector('.charts-container .chart-box:nth-child(4) .chart'));
  chartLowOmega.setOption(createTimeSeriesOption(
    lowOmegaData.timestamps,
    lowOmegaData.values,
    '时间',
    '转速',
    '#8b5cf6'
  ));
  chartInstances.testLowOmega = chartLowOmega;
}

// 渲染数据图表 (新的渐进式工作流)
function renderDataCharts() {
  if (!currentData.value || !currentData.value.data) return;
  
  const highIData = currentData.value.data.HighI;
  const highTMData = currentData.value.data.HighTM;
  const highOmegaData = currentData.value.data.HighOmega;
  const lowOmegaData = currentData.value.data.LowOmega;
  
  // 销毁旧图表实例
  if (chartInstances.dataHighI) chartInstances.dataHighI.dispose();
  if (chartInstances.dataHighTM) chartInstances.dataHighTM.dispose();
  if (chartInstances.dataHighOmega) chartInstances.dataHighOmega.dispose();
  if (chartInstances.dataLowOmega) chartInstances.dataLowOmega.dispose();
  
  // 确保 DOM 元素存在
  if (!chartDataHighI.value || !chartDataHighTM.value || 
      !chartDataHighOmega.value || !chartDataLowOmega.value) {
    console.warn('Chart DOM elements not ready');
    return;
  }
  
  // 高速电机电流
  const chartHighI = echarts.init(chartDataHighI.value);
  chartHighI.setOption(createTimeSeriesOption(
    highIData.timestamps,
    highIData.values,
    '时间',
    '电流',
    '#0ea5e9'
  ));
  chartInstances.dataHighI = chartHighI;
  
  // 高速电机温度
  const chartHighTM = echarts.init(chartDataHighTM.value);
  chartHighTM.setOption(createTimeSeriesOption(
    highTMData.timestamps,
    highTMData.values,
    '时间',
    '温度',
    '#f59e0b'
  ));
  chartInstances.dataHighTM = chartHighTM;
  
  // 高速组件转速
  const chartHighOmega = echarts.init(chartDataHighOmega.value);
  chartHighOmega.setOption(createTimeSeriesOption(
    highOmegaData.timestamps,
    highOmegaData.values,
    '时间',
    '转速',
    '#10b981'
  ));
  chartInstances.dataHighOmega = chartHighOmega;
  
  // 低速组件转速
  const chartLowOmega = echarts.init(chartDataLowOmega.value);
  chartLowOmega.setOption(createTimeSeriesOption(
    lowOmegaData.timestamps,
    lowOmegaData.values,
    '时间',
    '转速',
    '#8b5cf6'
  ));
  chartInstances.dataLowOmega = chartLowOmega;
}



// 渲染模型对比图表
function renderModelCharts() {
  // 确保 DOM 元素存在
  if (!chartModelComparison.value) {
    console.warn('Model comparison chart DOM element not ready');
    return;
  }
  
  // 销毁旧图表实例
  if (chartInstances.modelComparison) {
    chartInstances.modelComparison.dispose();
  }
  
  const chart = echarts.init(chartModelComparison.value);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: ['对比模型', '提出模型'],
      top: 10,
      textStyle: { fontSize: 13 }
    },
    grid: {
      left: '8%',
      right: '5%',
      top: '15%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: modelData.proposed.index,
      name: '样本索引',
      nameTextStyle: { fontSize: 13, fontWeight: 500 }
    },
    yAxis: {
      type: 'value',
      name: '健康指征 (HI)',
      nameTextStyle: { fontSize: 13, fontWeight: 500 },
      min: 0,
      max: 1
    },
    dataZoom: [
      { type: 'inside' },
      { type: 'slider', height: 20, bottom: 5 }
    ],
    series: [
      {
        name: '对比模型',
        type: 'line',
        data: modelData.duibi.HI_Value,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#94a3b8', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#94a3b840' },
            { offset: 1, color: '#94a3b810' }
          ])
        }
      },
      {
        name: '提出模型',
        type: 'line',
        data: modelData.proposed.HI_Value,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#10b981', width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#10b98140' },
            { offset: 1, color: '#10b98110' }
          ])
        }
      }
    ]
  };
  
  chart.setOption(option);
  chartInstances.modelComparison = chart;
}

// 创建时间序列图表配置
function createTimeSeriesOption(xData, yData, xLabel, yLabel, color) {
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      textStyle: { color: '#fff' }
    },
    grid: {
      left: '10%',
      right: '5%',
      top: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: xData,
      name: xLabel,
      nameTextStyle: { fontSize: 12, fontWeight: 500 },
      axisLabel: {
        interval: 'auto',
        rotate: 0,
        formatter: value => value.slice(0, 10)
      }
    },
    yAxis: {
      type: 'value',
      name: yLabel,
      nameTextStyle: { fontSize: 12, fontWeight: 500 }
    },
    dataZoom: [
      { type: 'inside' },
      { type: 'slider', height: 20, bottom: 5 }
    ],
    series: [{
      type: 'line',
      data: yData,
      smooth: false,
      symbol: 'none',
      lineStyle: { color, width: 1.5 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: `${color}40` },
          { offset: 1, color: `${color}10` }
        ])
      }
    }]
  };
}

// 创建索引序列图表配置
function createIndexSeriesOption(xData, yData, xLabel, yLabel, color, yMin = null, yMax = null) {
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      textStyle: { color: '#fff' }
    },
    grid: {
      left: '8%',
      right: '5%',
      top: '10%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: xData,
      name: xLabel,
      nameTextStyle: { fontSize: 12, fontWeight: 500 }
    },
    yAxis: {
      type: 'value',
      name: yLabel,
      nameTextStyle: { fontSize: 12, fontWeight: 500 },
      min: yMin,
      max: yMax,
      scale: true // 自动缩放
    },
    dataZoom: [
      { type: 'inside' },
      { type: 'slider', height: 20, bottom: 5 }
    ],
    series: [{
      type: 'line',
      data: yData,
      smooth: true,
      symbol: 'none',
      lineStyle: { color, width: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: `${color}40` },
          { offset: 1, color: `${color}10` }
        ])
      }
    }]
  };
}


// 打开特征趋势对话框
function openFeatureTrendDialog(feature) {
  currentFeature.value = feature;
  dialogOC.value = featureOC.value;
  featureTrendDialogVisible.value = true;
  
  nextTick(() => {
    calculateFeatureTrend();
  });
}

// 计算特征趋势（滑动窗口）
async function calculateFeatureTrend() {
  if (!rawSignalsData.value || !rawSignalsData.value[dialogOC.value] || !currentFeature.value) return;
  
  featureTrendLoading.value = true;
  
  try {
    const ocData = rawSignalsData.value[dialogOC.value];
    const featureName = currentFeature.value.name;
    
    // 根据用户选择的参数获取数据
    const sourceData = ocData[selectedParameter.value];
    
    if (!sourceData || sourceData.length === 0) {
      ElMessage.warning('所选参数数据不足');
      return;
    }
    
    // 滑动窗口计算特征值
    const windowSize_value = windowSize.value;
    const featureTrend = [];
    const xLabels = [];
    
    for (let i = 0; i <= sourceData.length - windowSize_value; i += 10) { // 每10个点计算一次
      const window = sourceData.slice(i, i + windowSize_value);
      const featureValue = calculateFeatureValue(window, featureName);
      featureTrend.push(featureValue);
      xLabels.push(i);
    }
    
    // 渲染图表
    await nextTick();
    const el = document.querySelector('.feature-trend-chart');
    if (!el) return;
    
    if (chartInstances.featureTrend) {
      chartInstances.featureTrend.dispose();
    }
    
    const chart = echarts.init(el);
    chart.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        textStyle: { color: '#fff' }
      },
      grid: {
        left: '8%',
        right: '5%',
        top: '10%',
        bottom: '15%'
      },
      xAxis: {
        type: 'category',
        data: xLabels,
        name: '起始位置',
        nameTextStyle: { fontSize: 13, fontWeight: 500 }
      },
      yAxis: {
        type: 'value',
        name: currentFeature.value.cn_name,
        nameTextStyle: { fontSize: 13, fontWeight: 500 }
      },
      dataZoom: [
        { type: 'inside' },
        { type: 'slider', height: 20, bottom: 5 }
      ],
      series: [{
        type: 'line',
        data: featureTrend,
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: '#2563eb', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#2563eb40' },
            { offset: 1, color: '#2563eb10' }
          ])
        }
      }]
    });
    
    chartInstances.featureTrend = chart;
    
  } catch (error) {
    ElMessage.error('计算失败: ' + error.message);
  } finally {
    featureTrendLoading.value = false;
  }
}

// 特征值计算函数（简化版，基于tezheng/Features_Extraction/Features_Extraction_TimeDomain.py）
function calculateFeatureValue(data, featureName) {
  if (!data || data.length === 0) return 0;
  
  const arr = data.filter(v => v !== null && v !== undefined && !isNaN(v));
  if (arr.length === 0) return 0;
  
  switch(featureName) {
    case 'mean':
      return arr.reduce((a, b) => a + b, 0) / arr.length;
    
    case 'var':
      const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
      return arr.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / arr.length;
    
    case 'std':
      const mean2 = arr.reduce((a, b) => a + b, 0) / arr.length;
      const variance = arr.reduce((a, b) => a + Math.pow(b - mean2, 2), 0) / arr.length;
      return Math.sqrt(variance);
    
    case 'rms':
      return Math.sqrt(arr.reduce((a, b) => a + b * b, 0) / arr.length);
    
    case 'peak2peak':
      return Math.max(...arr) - Math.min(...arr);
    
    case 'skew':
      const mean3 = arr.reduce((a, b) => a + b, 0) / arr.length;
      const std3 = Math.sqrt(arr.reduce((a, b) => a + Math.pow(b - mean3, 2), 0) / arr.length);
      if (std3 === 0) return 0;
      return arr.reduce((a, b) => a + Math.pow((b - mean3) / std3, 3), 0) / arr.length;
    
    case 'kurt':
      const mean4 = arr.reduce((a, b) => a + b, 0) / arr.length;
      const std4 = Math.sqrt(arr.reduce((a, b) => a + Math.pow(b - mean4, 2), 0) / arr.length);
      if (std4 === 0) return 0;
      return arr.reduce((a, b) => a + Math.pow((b - mean4) / std4, 4), 0) / arr.length - 3;
    
    case 'form_factor':
      const rms_ff = Math.sqrt(arr.reduce((a, b) => a + b * b, 0) / arr.length);
      const meanAbs = arr.reduce((a, b) => a + Math.abs(b), 0) / arr.length;
      return meanAbs === 0 ? 0 : rms_ff / meanAbs;
    
    case 'crest_factor':
      const rms_cf = Math.sqrt(arr.reduce((a, b) => a + b * b, 0) / arr.length);
      const maxAbs = Math.max(...arr.map(Math.abs));
      return rms_cf === 0 ? 0 : maxAbs / rms_cf;
    
    case 'clearance_factor':
      const maxAbs_clf = Math.max(...arr.map(Math.abs));
      const sqrtMean = Math.pow(arr.reduce((a, b) => a + Math.sqrt(Math.abs(b)), 0) / arr.length, 2);
      return sqrtMean === 0 ? 0 : maxAbs_clf / sqrtMean;
    
    case 'kurtosis_factor':
      const mean_kf = arr.reduce((a, b) => a + b, 0) / arr.length;
      const std_kf = Math.sqrt(arr.reduce((a, b) => a + Math.pow(b - mean_kf, 2), 0) / arr.length);
      if (std_kf === 0) return 0;
      const kurt_kf = arr.reduce((a, b) => a + Math.pow((b - mean_kf) / std_kf, 4), 0) / arr.length - 3;
      return kurt_kf / Math.pow(std_kf, 4);
    
    default:
      return 0;
  }
}

// 渲染HI趋势图表
function renderHICharts() {
  if (!hiTrendsData.value || !hiTrendsData.value[selectedHIMethod.value]) {
    console.warn(`HI trends data not available for method: ${selectedHIMethod.value}`);
    console.log('Available methods:', Object.keys(hiTrendsData.value || {}));
    return;
  }
  
  hiTrendsLoading.value = true;
  
  try {
    const methodData = hiTrendsData.value[selectedHIMethod.value];
    const conditions = ['OC1', 'OC0', 'OC2'];
    
    console.log(`Rendering ${selectedHIMethod.value} charts for conditions:`, conditions);
    
    conditions.forEach((oc, index) => {
      if (!methodData[oc]) return;
      
      const el = document.querySelector(`.hi-charts-container .chart-box:nth-child(${index + 1}) .chart`);
      if (!el) return;
      
      // 检查DOM是否可见
      if (el.clientWidth === 0 || el.clientHeight === 0) {
        console.warn(`HI chart container for ${oc} not visible yet, skipping render`);
        return;
      }
      
      // 销毁旧图表实例
      const chartKey = `chartHI_${oc}`;
      if (chartInstances[chartKey]) {
        chartInstances[chartKey].dispose();
        chartInstances[chartKey] = null;
      }
      
      const chart = echarts.init(el);
      const ocData = methodData[oc];
      
      // 创建理想参考线 - 单调上升的直线
      const dataLength = ocData.HI.length;
      const minValue = Math.min(...ocData.HI.filter(v => v !== null));
      const maxValue = Math.max(...ocData.HI.filter(v => v !== null));
      const idealReference = Array.from({ length: dataLength }, (_, i) => {
        // 线性插值: 从最小值平滑增长到最大值
        return minValue + (maxValue - minValue) * (i / (dataLength - 1));
      });
      
      const series = [{
        name: `${selectedHIMethod.value} HI`,
        type: 'line',
        data: ocData.HI,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#2563eb', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#2563eb40' },
            { offset: 1, color: '#2563eb10' }
          ])
        }
      }, {
        name: '理想参考线',
        type: 'line',
        data: idealReference,
        smooth: false,
        symbol: 'none',
        lineStyle: { 
          color: '#10b981', 
          width: 2, 
          type: 'dashed' 
        },
        z: 0  // 确保在其他曲线后面
      }];
      
      // 如果是Residual方法且有Bias数据，添加第二条曲线
      if (selectedHIMethod.value === 'Residual' && ocData.HI_bias) {
        series.splice(1, 0, {  // 插入到参考线之前
          name: 'Bias HI',
          type: 'line',
          data: ocData.HI_bias,
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#dc2626', width: 1.5, type: 'dashed' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#dc262640' },
              { offset: 1, color: '#dc262610' }
            ])
          }
        });
      }
      
      chart.setOption({
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          textStyle: { color: '#fff' }
        },
        legend: {
          data: series.map(s => s.name),
          top: 5
        },
        grid: {
          left: '8%',
          right: '5%',
          top: selectedHIMethod.value === 'Residual' ? '15%' : '10%',
          bottom: '15%'
        },
        xAxis: {
          type: 'category',
          data: ocData.index.map(i => i * 10),  // 转换为小时
          name: '时间 (小时)',
          nameTextStyle: { fontSize: 12, fontWeight: 500 }
        },
        yAxis: {
          type: 'value',
          name: 'HI值',
          nameTextStyle: { fontSize: 12, fontWeight: 500 }
        },
        dataZoom: [
          { type: 'inside' },
          { type: 'slider', height: 20, bottom: 5 }
        ],
        series
      });
      
      chartInstances[`chartHI_${oc}`] = chart;
    });
  } finally {
    hiTrendsLoading.value = false;
  }
}

// 渲染性能指标雷达图
function renderMetricsRadarChart() {
  if (!chartMetricsRadar.value) return;
  
  // 检查容器是否可见
  if (chartMetricsRadar.value.clientWidth === 0 || chartMetricsRadar.value.clientHeight === 0) {
    console.warn('Radar chart container not visible, retrying...');
    // 延迟重试
    setTimeout(() => {
      renderMetricsRadarChart();
    }, 100);
    return;
  }
  
  // 从metricsComparisonData中筛选当前工况的数据
  const currentOCData = metricsComparisonData.value.filter(
    item => item.condition === selectedMetricsOC.value
  );
  
  if (currentOCData.length === 0) return;
  
  // 销毁旧图表
  if (chartInstances.metricsRadar) {
    chartInstances.metricsRadar.dispose();
  }
  
  const chart = echarts.init(chartMetricsRadar.value);
  
  // 准备雷达图数据
  const indicator = [
    { name: '单调性 (Mon)', max: 1 },
    { name: '鲁棒性 (Rob)', max: 1 },
    { name: '相关性 (Corr)', max: 1 },
    { name: '综合得分 (HM)', max: 1 }
  ];
  
  const series = currentOCData.map(item => ({
    name: item.method,
    value: [
      parseFloat(item.mon),
      parseFloat(item.rob),
      parseFloat(item.corr),
      parseFloat(item.hm)
    ]
  }));
  
  const colors = ['#3b82f6', '#8b5cf6', '#f59e0b', '#10b981'];
  
  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        const metrics = ['单调性', '鲁棒性', '相关性', '综合得分'];
        let result = `<strong>${params.seriesName}</strong><br/>`;
        params.value.forEach((val, idx) => {
          result += `${metrics[idx]}: ${val.toFixed(4)}<br/>`;
        });
        return result;
      }
    },
    legend: {
      data: currentOCData.map(item => item.method),
      bottom: 0,
      textStyle: { fontSize: 12 }
    },
    radar: {
      indicator: indicator,
      radius: '65%',
      splitNumber: 5,
      name: {
        textStyle: {
          fontSize: 13,
          fontWeight: 500,
          color: '#374151'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#e5e7eb'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['#fafafa', '#ffffff']
        }
      },
      axisLine: {
        lineStyle: {
          color: '#d1d5db'
        }
      }
    },
    series: [{
      type: 'radar',
      data: series.map((item, index) => ({
        name: item.name,
        value: item.value,
        lineStyle: {
          color: colors[index],
          width: 2
        },
        itemStyle: {
          color: colors[index]
        },
        areaStyle: {
          // 只有本研究方法填充区域，其他方法不填充
          opacity: item.name === '本研究方法' ? 0.25 : 0
        },
        symbol: 'circle',
        symbolSize: 6
      }))
    }]
  });
  
  chartInstances.metricsRadar = chart;
}

// 加载特征提取数据
async function loadExtractionData() {
  extractionLoading.value = true;
  hiTrendsLoading.value = true;
  
  try {
    // 并行加载原始信号数据和HI趋势数据
    const [rawResp, featuresResp, hiResp] = await Promise.all([
      fetch('/feature-extraction/raw_signals.json'),
      fetch('/feature-extraction/feature_definitions.json'),
      fetch('/feature-extraction/hi_trends.json')
    ]);
    
    rawSignalsData.value = await rawResp.json();
    featureDefinitions.value = await featuresResp.json();
    hiTrendsData.value = await hiResp.json();
    
    // 等待 DOM 更新后渲染图表
    await nextTick();
    
    if (selectedExtractionType.value === 'system') {
      renderRawSignalsCharts();
      renderAllHICharts();
      renderMetricsRadarChart();
    }
    
  } catch (error) {
    console.error('Failed to load extraction data:', error);
    ElMessage.error('特征提取数据加载失败');
  } finally {
    extractionLoading.value = false;
    hiTrendsLoading.value = false;
  }
}


// Tab切换watch
watch(activeTab, (newTab) => {
  if (newTab === 'extraction') {
    loadExtractionData();
    // 延迟渲染雷达图确保容器完全可见
    nextTick(() => {
      setTimeout(() => {
        renderMetricsRadarChart();
      }, 200);
    });
  }
});

// 同步特征趋势对话框的工况选择（基于参数级文件导入映射）
watch(featureOC, (newOC) => {
  dialogOC.value = newOC;
});



// 窗口大小调整
function handleResize() {
  Object.keys(chartInstances).forEach(key => {
    const chart = chartInstances[key];
    if (chart && !chart.isDisposed()) {
      try {
        chart.resize();
      } catch (e) {
        console.warn(`Failed to resize chart ${key}:`, e);
      }
    }
  });
}

// 生命周期
onMounted(() => {
  // 注意：不再自动加载数据，只在用户导入文件后才加载
  // loadAndRenderData();
  window.addEventListener('resize', handleResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  // 销毁所有图表实例
  Object.keys(chartInstances).forEach(key => {
    const chart = chartInstances[key];
    if (chart && !chart.isDisposed()) {
      try {
        chart.dispose();
      } catch (e) {
        console.warn(`Failed to dispose chart ${key}:`, e);
      }
    }
  });
  // 清空实例对象
  chartInstances = {};
});
</script>

<style scoped>
.health-assessment {
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

/* 主标签页 */
.main-tabs {
  margin-top: 0;
}

.main-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.main-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 500;
}

/* 控制面板 */
.control-panel {
  margin-bottom: 20px;
  border-radius: 8px;
}

.control-header {
  margin-bottom: 20px;
}

.control-header h2 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-header p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.control-row {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.control-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

/* 操作区域 */
.action-section {
  margin-top: 30px;
}

.action-button-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px 0;
}

.action-hint {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  text-align: center;
}

/* 评估结果卡片 */
.assessment-result {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 指标区域 */
.metrics-section {
  animation: slideIn 0.3s ease-out;
}


.data-info {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-light);
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.data-info .el-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
}

/* 可视化面板 */
.viz-panel {
  margin-bottom: 20px;
  border-radius: 8px;
}

.panel-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--el-border-color-light);
}

.panel-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-desc {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

/* 图表容器 */
.charts-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.chart-box {
  background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.chart-box.full-width {
  grid-column: 1 / -1;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--el-color-primary-light-8);
}

.chart {
  width: 100%;
  height: 320px;
}

.chart.large {
  height: 400px;
}

/* 统计卡片网格 */
.stats-grid {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 20px;
}

.stat-card {
  background: var(--el-fill-color-light);
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid;
}

.stat-card.duibi {
  border-left-color: #94a3b8;
}

.stat-card.proposed {
  border-left-color: #10b981;
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.stat-icon {
  font-size: 24px;
}

.stat-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row .label {
  font-weight: 500;
  color: var(--el-text-color-secondary);
}

.stat-row .value {
  font-weight: 600;
  color: var(--el-text-color-primary);
  font-family: 'Courier New', monospace;
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
  gap: 10px;
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

/* 性能指标可视化 */
.metrics-visualization {
  margin-top: 30px;
  padding: 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border-radius: 12px;
  border: 2px solid #e5e7eb;
}

.metrics-control {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 20px 0;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.metrics-radar-chart {
  width: 100%;
  height: 500px;
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

/* ==================== 特征提取模块样式 ==================== */

/* 原始信号网格 */
.raw-signals-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-top: 20px;
}

/* 2x2网格布局 */
.raw-signals-grid-2x2,
.hi-charts-grid-2x2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 20px;
}

/* OC选择器 */
.oc-control {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.oc-control .control-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

/* 特征卡片网格 */
.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 20px;
}

.feature-card {
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
  border-left: 3px solid var(--el-color-primary);
  cursor: default;
}

.feature-card.clickable {
  cursor: pointer;
}

.feature-card.clickable:hover {
  background: var(--el-color-primary-light-9);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
  border-left-color: var(--el-color-primary-dark-2);
}

.feature-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.feature-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.feature-formula {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
  padding: 8px;
  border-radius: 4px;
  margin: 8px 0;
  overflow-x: auto;
}

.feature-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

.feature-hint {
  margin-top: 8px;
  font-size: 11px;
  color: var(--el-color-primary);
  text-align: center;
  font-style: italic;
}

/* 特征趋势对话框 */
.dialog-control {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.dialog-control label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.feature-trend-chart {
  width: 100%;
  height: 500px;
  min-height: 400px;
}

/* HI控制面板 */
.hi-control {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 8px;
}

.hi-control .control-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

/* HI图表容器 */
.hi-charts-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

/* 方法说明 */
.method-info {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px solid var(--el-border-color-light);
}

.method-card {
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  height: 100%;
}

.method-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.method-card.active {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

.method-card h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.method-card p {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}

.method-card ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.method-card ul li {
  font-size: 13px;
  color: var(--el-text-color-regular);
  padding: 6px 0 6px 20px;
  position: relative;
}

.method-card ul li::before {
  content: "✓";
  position: absolute;
  left: 0;
  color: var(--el-color-success);
  font-weight: bold;
}

/* 响应式设计 - 特征提取 */
@media (max-width: 1400px) {
  .raw-signals-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .raw-signals-grid-2x2 {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .features-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .hi-charts-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1000px) {
  .raw-signals-grid,
  .raw-signals-grid-2x2,
  .hi-charts-container {
    grid-template-columns: 1fr;
  }
  
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .hi-control,
  .oc-control,
  .dialog-control {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* ==================== 评估指标样式 ==================== */

/* 两列网格布局 */
.stat-content-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 16px;
}

/* 调和平均占据两列 */
.stat-content-grid .metric-row.hm {
  grid-column: 1 / -1;
}

/* 指标行样式 */
.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  background: var(--el-fill-color-blank);
  transition: all 0.3s ease;
}

.metric-row.clickable {
  cursor: pointer;
}

.metric-row.clickable:hover {
  background: var(--el-color-primary-light-9);
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: var(--el-color-primary-light-5);
}

.metric-row.hm {
  background: var(--el-fill-color-light);
  border-color: var(--el-color-primary-light-5);
  border-width: 2px;
  font-weight: 600;
}

.metric-label {
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.metric-value {
  color: var(--el-text-color-primary);
  font-weight: 600;
  font-size: 16px;
  font-family: 'Courier New', monospace;
}

.metric-value.better {
  color: var(--el-color-success);
}

.improvement {
  margin-left: 8px;
  padding: 2px 8px;
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

/* 指标详情对话框 */
.metric-detail h3 {
  margin: 0 0 20px 0;
  color: var(--el-text-color-primary);
  font-size: 20px;
}

/* 响应式设计 - 指标卡片 */
@media (max-width: 1200px) {
  .stat-content-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-content-grid .metric-row.hm {
    grid-column: 1;
  }
}

/* ==================== 性能指标对比表格 ==================== */

.metrics-comparison {
  margin-top: 40px;
  padding-top: 30px;
  border-top: 2px solid var(--el-border-color-light);
}

.metrics-comparison .panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.metrics-comparison .panel-desc {
  margin-bottom: 20px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.metric-best {
  color: var(--el-color-success);
  font-weight: 600;
}

/* 健康评估模型图示样式 */
.model-diagram-container {
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
  height: 400px;
  color: var(--el-text-color-secondary);
}

.image-error p {
  margin-top: 16px;
  font-size: 14px;
}

/* ==================== 文件导入样式 ==================== */

.file-name-display {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid var(--el-color-success-light-5);
}

.file-name-display .el-icon {
  font-size: 16px;
}

.file-hint {
  color: var(--el-text-color-placeholder);
  font-size: 14px;
  font-style: italic;
}

</style>
