<template>
  <div class="undersampling-container">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">欠采样和有限传感约束下感知模型智能训练和在线学习方法</h1>
        <p class="page-subtitle">该技术用于解决CMG数据采样率不足与感知受限问题</p>
      </div>
    </div>

    <!-- Main Tabs -->
    <el-tabs 
      v-model="activeTab" 
      class="main-tabs" 
    >
      <!-- Tab 1: Random Sampling -->
      <el-tab-pane label="随机采样" name="random">
        <div class="content-section">
          <!-- 数据导入控制 -->
          <div class="tab-header-controls">
            <div class="upload-area">
              <el-upload
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleFileSelect"
                accept=".csv,.txt,.dat"
                class="upload-component"
              >
                <el-button type="primary" :icon="Upload" :loading="randomImporting">
                  <span style="margin-left: 8px">
                    {{ randomImporting ? '正在导入...' : '导入数据文件' }}
                  </span>
                </el-button>
              </el-upload>
              <span v-if="currentFileName" class="file-info">
                <!-- <el-icon class="file-icon"><Document /></el-icon> -->
                <span>{{ currentFileName }}</span>
              </span>
            </div>
          </div>

          <!-- 占位提示框 -->
          <el-row v-if="!showOriginalSignal" :gutter="20" style="margin-top: 20px">
            <el-col :span="24">
              <el-card class="placeholder-card">
                <div class="placeholder-content">
                  <el-icon class="placeholder-icon"><InfoFilled /></el-icon>
                  <p class="placeholder-text">请点击上方"导入数据文件"按钮选择数据文件开始分析</p>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 1. 原始信号与降采样点 -->
          <el-row v-if="showOriginalSignal" :gutter="20" style="margin-bottom: 20px">
            <el-col :span="24">
              <el-card class="chart-card">
                <template #header>
                  <div class="card-header">
                    <el-icon><DataLine /></el-icon>
                    <span>原始信号与降采样点</span>
                  </div>
                </template>
                <div ref="originalSignalChart" class="chart-container"></div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 补全按钮 -->
          <el-row v-if="showOriginalSignal && !showCompletionResults" :gutter="20" style="margin-bottom: 20px">
            <el-col :span="24" style="text-align: center">
              <el-button type="success" size="large" @click="handleStartCompletion" :icon="Operation">
                <!-- <el-icon><Operation /></el-icon> -->
                <span style="margin-left: 8px">随机采样补全</span>
              </el-button>
            </el-col>
          </el-row>

          <!-- 2. 三种方法的对比 (竖向排列) -->
          <div v-if="showCompletionResults">
          <!-- 线性插值 -->
          <el-row :gutter="20" style="margin-bottom: 20px">
            <el-col :span="12">
              <el-card class="chart-card">
                <template #header>
                  <div class="card-header">
                    <el-tag type="primary" effect="dark">线性插值</el-tag>
                    <span style="margin-left: 10px">时域补全</span>
                  </div>
                </template>
                <div ref="linearTimeChart" class="chart-container-medium"></div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="chart-card">
                <template #header>
                  <div class="card-header">
                    <el-tag type="primary" effect="dark">线性插值</el-tag>
                    <span style="margin-left: 10px">频域对比</span>
                  </div>
                </template>
                <div ref="linearFreqChart" class="chart-container-medium"></div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 三次样条插值 -->
          <el-row :gutter="20" style="margin-bottom: 20px">
            <el-col :span="12">
              <el-card class="chart-card">
                <template #header>
                  <div class="card-header">
                    <el-tag type="warning" effect="dark">三次样条插值</el-tag>
                    <span style="margin-left: 10px">时域补全</span>
                  </div>
                </template>
                <div ref="cubicTimeChart" class="chart-container-medium"></div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="chart-card">
                <template #header>
                  <div class="card-header">
                    <el-tag type="warning" effect="dark">三次样条插值</el-tag>
                    <span style="margin-left: 10px">频域对比</span>
                  </div>
                </template>
                <div ref="cubicFreqChart" class="chart-container-medium"></div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 频域插值 -->
          <el-row :gutter="20" style="margin-bottom: 20px">
            <el-col :span="12">
              <el-card class="chart-card">
                <template #header>
                  <div class="card-header">
                    <el-tag type="success" effect="dark">频域插值</el-tag>
                    <span style="margin-left: 10px">时域补全</span>
                  </div>
                </template>
                <div ref="freqTimeChart" class="chart-container-medium"></div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="chart-card">
                <template #header>
                  <div class="card-header">
                    <el-tag type="success" effect="dark">频域插值</el-tag>
                    <span style="margin-left: 10px">频域对比</span>
                  </div>
                </template>
                <div ref="freqFreqChart" class="chart-container-medium"></div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 3. 指标对比表格 -->
          <el-row :gutter="20">
            <el-col :span="24">
              <el-card class="metric-card">
                <template #header>
                  <div class="card-header">
                    <el-icon class="header-icon"><TrendCharts /></el-icon>
                    <span>插值方法性能对比</span>
                  </div>
                </template>
                <el-table :data="metricsTableData" stripe style="width: 100%">
                  <el-table-column prop="method" label="插值方法" width="150" align="center">
                    <template #default="scope">
                      <el-tag :type="scope.row.tagType" size="large" style="font-size: 16px; font-weight: 600;">
                        {{ scope.row.method }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="timeDTW" label="时域DTW" align="center" sortable>
                    <template #default="scope">
                      <span :class="{'best-metric': scope.row.isBestTime}">{{ scope.row.timeDTW }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="freqDTW" label="频域DTW" align="center" sortable>
                    <template #default="scope">
                      <span :class="{'best-metric': scope.row.isBestFreq}">{{ scope.row.freqDTW }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="combined" label="综合相似度" align="center" sortable>
                    <template #default="scope">
                      <el-tag :type="scope.row.isBestCombined ? 'success' : undefined" effect="dark" size="large" style="font-size: 16px; font-weight: 600;">
                        {{ scope.row.combined }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="综合排名" align="center">
                    <template #default="scope">
                      <el-icon v-if="scope.row.rank === 1" style="color: #67c23a; font-size: 20px"><Trophy /></el-icon>
                      <span v-else style="font-size: 16px; font-weight: 600">{{ scope.row.rank }}</span>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
          </el-row>
          </div> <!-- End of showCompletionResults -->
        </div>
      </el-tab-pane>

      <!-- Tab 2: Undersampling Reconstruction -->
      <el-tab-pane label="欠采样重建" name="reconstruction">
        <div class="content-section">
          <!-- 数据导入控制 -->
          <div class="tab-header-controls">
            <div class="upload-area">
              <el-upload
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleReconstructionFileSelect"
                accept=".csv,.txt,.dat"
                class="upload-component"
              >
                <el-button type="primary" :icon="Upload" :loading="reconstructionImporting">
                  <span style="margin-left: 8px">
                    {{ reconstructionImporting ? '正在导入...' : '导入数据文件' }}
                  </span>
                </el-button>
              </el-upload>
              <span v-if="currentReconstructionFileName" class="file-info">
                <el-icon class="file-icon"><Document /></el-icon>
                <span>{{ currentReconstructionFileName }}</span>
              </span>
            </div>
          </div>

          <!-- 占位提示框 -->
          <el-row v-if="!showReconstructionOriginal" :gutter="20" style="margin-top: 20px">
            <el-col :span="24">
              <el-card class="placeholder-card">
                <div class="placeholder-content">
                  <el-icon class="placeholder-icon"><InfoFilled /></el-icon>
                  <p class="placeholder-text">请点击上方"导入数据文件"按钮选择数据文件开始分析</p>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 欠采样效果图 -->
          <el-row v-if="showReconstructionOriginal" :gutter="20" style="margin-bottom: 20px">
            <el-col :span="24">
              <el-card class="chart-card">
                <template #header>
                  <div class="card-header">
                    <span>欠采样效果</span>
                  </div>
                </template>
                <div ref="undersamplingChart" class="chart-container"></div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 开始重建按钮 -->
          <el-row v-if="showReconstructionOriginal && !showReconstructionResults" :gutter="20" style="margin-bottom: 20px">
            <el-col :span="24" style="text-align: center">
              <el-button type="success" size="large" @click="handleStartReconstruction" :icon="Operation">
                <!-- <el-icon><Operation /></el-icon> -->
                <span style="margin-left: 8px">开始重建</span>
              </el-button>
            </el-col>
          </el-row>

          <!-- 重建结果 -->
          <div v-if="showReconstructionResults">
          <el-row :gutter="20" style="margin-bottom: 20px">
            <el-col :span="24">
              <el-card class="chart-card">
                <template #header>
                  <div class="card-header">
                    <span>重建细节对比</span>
                  </div>
                </template>
                <div ref="reconstructionDetailChart" class="chart-container"></div>
              </el-card>
            </el-col>
          </el-row>
          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="24">
              <el-card class="chart-card">
                <template #header>
                  <div class="card-header">
                    <span>频域对比</span>
                  </div>
                </template>
                <div ref="reconstructionFreqChart" class="chart-container"></div>
              </el-card>
            </el-col>
          </el-row>
          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-content">
                  <el-icon class="metric-icon"><DataAnalysis /></el-icon>
                  <span class="metric-label">RMSE:</span>
                  <span class="metric-value">{{ reconstructionData[0].recon_metrics.rmse.toFixed(4) }}</span>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-content">
                  <el-icon class="metric-icon"><DataAnalysis /></el-icon>
                  <span class="metric-label">MAE:</span>
                  <span class="metric-value">{{ reconstructionData[0].recon_metrics.mae.toFixed(4) }}</span>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="metric-card">
                <div class="metric-content">
                  <el-icon class="metric-icon"><TrendCharts /></el-icon>
                  <span class="metric-label">余弦相似度:</span>
                  <span class="metric-value">{{ reconstructionData[0].recon_metrics.cos_sim.toFixed(4) }}</span>
                </div>
              </el-card>
            </el-col>
          </el-row>
          </div> <!-- End of showReconstructionResults -->
        </div>
      </el-tab-pane>

      <!-- Tab 3: Limited Sensing -->
      <el-tab-pane label="有限传感信息" name="limited">
        <!-- 数据导入控制 - 始终显示 -->
        <div class="content-section">
          <div class="tab-header-controls">
            <div class="upload-area">
              <el-upload
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleLimitedFileSelect"
                accept=".csv,.txt,.dat,.xlsx"
                class="upload-component"
              >
                <el-button type="primary" :icon="Upload" :loading="limitedImporting">
                  <span style="margin-left: 8px">
                    {{ limitedImporting ? '正在导入...' : '导入数据文件' }}
                  </span>
                </el-button>
              </el-upload>
              <span v-if="currentLimitedFileName" class="file-info">
                <el-icon class="file-icon"><Document /></el-icon>
                <span>{{ currentLimitedFileName }}</span>
              </span>
            </div>
          </div>

          <!-- 占位提示框 -->
          <el-row v-if="!showLimitedData" :gutter="20" style="margin-top: 20px">
            <el-col :span="24">
              <el-card class="placeholder-card">
                <div class="placeholder-content">
                  <el-icon class="placeholder-icon"><InfoFilled /></el-icon>
                  <p class="placeholder-text">请点击上方"导入数据文件"按钮选择数据文件开始分析</p>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 数据内容区域 - 仅在导入后显示 -->
          <div v-if="showLimitedData" class="content-section">
            <!-- 说明卡片 -->
            <el-row :gutter="20" style="margin-bottom: 20px">
              <el-col :span="24">
                <el-card class="explanation-card">
                  <template #header>
                    <div class="card-header">
                      <el-icon class="header-icon"><InfoFilled /></el-icon>
                      <span>有限传感信息增强技术</span>
                    </div>
                  </template>
                  <div class="explanation-content">
                    <p>
                      <strong>技术原理：</strong>在实际应用中，由于成本、空间等限制，传感器数量往往有限。本技术通过物理建模和参数辨识，
                      从有限的传感器数据中推导出隐藏参数（如润滑效率μ和粘度ν），从而实现传感信息的虚拟扩增。
                    </p>
                    <p>
                      <strong>技术优势：</strong>无需增加物理传感器，仅需3个基础传感通道即可获得5个通道的信息量，
                      性能指标提升显著，MAE和RMSE均有明显改善。
                    </p>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <!-- 通道数信息 -->
            <!-- <el-row :gutter="20">
              <el-col :span="8">
                <el-card class="info-card">
                  <div class="info-content">
                    <div class="info-label">有限通道数</div>
                    <div class="info-value primary">{{ limitedSensingData.limited_channel_num }}</div>
                    <div class="info-desc">基础传感器</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card class="info-card">
                  <div class="info-content">
                    <div class="info-label">扩增通道数</div>
                    <div class="info-value success">{{ limitedSensingData.augmented_channel_num }}</div>
                    <div class="info-desc">包含隐参数</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card class="info-card">
                  <div class="info-content">
                    <div class="info-label">增益比例</div>
                    <div class="info-value warning">{{ (limitedSensingData.gain_ratio * 100).toFixed(2) }}%</div>
                    <div class="info-desc">信息增益</div>
                  </div>
                </el-card>
              </el-col>
            </el-row> -->

            <el-row :gutter="20" style="margin-top: 20px" v-if="limitedSensingData.raw_data">
              <el-col :span="8">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>高速电机电流</span>
                    </div>
                  </template>
                  <div ref="highCurrentChart" class="chart-container-small"></div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>高速电机电压</span>
                    </div>
                  </template>
                  <div ref="highVoltageChart" class="chart-container-small"></div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>高速转子转速</span>
                    </div>
                  </template>
                  <div ref="highOmegaChart" class="chart-container-small"></div>
                </el-card>
              </el-col>
            </el-row>

            <!-- 隐参数辨识按钮 -->
            <template v-if="!showHpsDiv">
              <el-row :gutter="20" justify="center" style="margin-top: 20px">
                <el-col :span="6" style="text-align: center">
                  <el-button type="primary" @click="handleShowHpsDiv" :loading="buttonLoadingShowHps">
                    辨识隐参数
                  </el-button>
                </el-col>
              </el-row>
            </template>
            <!-- 隐参数可视化 -->
            <template v-if="showHpsDiv">
              <el-row :gutter="20" style="margin-top: 20px" v-if="limitedSensingData.hps">
                <el-col :span="24">
                  <el-card class="chart-card">
                    <template #header>
                      <div class="card-header">
                        <el-icon><Operation /></el-icon>
                        <span>辨识隐参数时序演化</span>
                      </div>
                    </template>
                    <div class="hidden-params-desc">
                      通过物理建模和参数辨识技术，从有限传感器数据中提取的隐藏参数。
                      <strong>μ (润滑效率)</strong> 反映轴承润滑状态，<strong>ν (粘度)</strong> 表征润滑剂特性。
                    </div>
                  </el-card>
                </el-col>
              </el-row>
              <el-row :gutter="20" style="margin-top: 20px" v-if="limitedSensingData.hps">
                <el-col :span="12">
                  <el-card class="chart-card">
                    <template #header>
                      <div class="card-header">
                        <span>润滑效率 μ 参数演化</span>
                      </div>
                    </template>
                    <div ref="muChart" class="chart-container"></div>
                  </el-card>
                </el-col>
                <el-col :span="12">
                  <el-card class="chart-card">
                    <template #header>
                      <div class="card-header">
                        <span>粘度 ν 参数演化</span>
                      </div>
                    </template>
                    <div ref="nuChart" class="chart-container"></div>
                  </el-card>
                </el-col>
              </el-row>
            </template>
            
            <!-- 预测结果可视化按钮 -->
            <template v-if="showHpsDiv && !showPredictionsDiv">
              <el-row :gutter="20" justify="center" style="margin-top: 20px">
                <el-col :span="6" style="text-align: center">
                  <el-button type="primary" @click="handleShowPredictionsDiv" :loading="buttonLoadingShowPredictions">
                    执行预测
                  </el-button>
                </el-col>
              </el-row>
            </template>
            <!-- 预测部分可视化 -->
            <template v-if="showHpsDiv && showPredictionsDiv">
              <!-- RUL Prediction Comparison -->
              <el-row :gutter="20" style="margin-top: 20px" v-if="limitedSensingData.rul_results">
                <el-col :span="24">
                  <el-card class="chart-card">
                    <template #header>
                      <div class="card-header">
                        <el-icon><TrendCharts /></el-icon>
                        <span>RUL 寿命预测效果对比</span>
                      </div>
                    </template>
                    <el-row :gutter="20">
                      <el-col :span="12">
                        <div style="text-align: center; margin-bottom: 10px; font-weight: bold;">基础模型 (3通道)</div>
                        <div ref="baseRulChart" class="chart-container"></div>
                      </el-col>
                      <el-col :span="12">
                        <div style="text-align: center; margin-bottom: 10px; font-weight: bold; color: #52c41a;">增强模型 (5通道)</div>
                        <div ref="fusionRulChart" class="chart-container"></div>
                      </el-col>
                    </el-row>
                  </el-card>
                </el-col>
              </el-row>

              <!-- 性能指标对比 -->
              <el-row :gutter="20" style="margin-top: 20px">
                <el-col :span="12">
                  <el-card class="chart-card">
                    <template #header>
                      <div class="card-header">
                        <el-icon><DataAnalysis /></el-icon>
                        <span>性能指标对比</span>
                      </div>
                    </template>
                    <el-table :data="limitedSensingTableData" style="width: 100%" stripe>
                      <el-table-column prop="metric" label="指标" width="120" align="center">
                        <template #default="scope">
                          <el-tag :type="scope.row.metric === 'MAE' ? 'primary' : 'success'" size="small" style="font-size: 16px; font-weight: 600;">
                            {{ scope.row.metric }}
                          </el-tag>
                        </template>
                      </el-table-column>
                      <el-table-column prop="limited" label="有限通道" align="center" />
                      <el-table-column prop="augmented" label="扩增通道" align="center">
                        <template #default="scope">
                          <span class="augmented-value">{{ scope.row.augmented }}</span>
                        </template>
                      </el-table-column>
                      <el-table-column prop="improvement" label="提升率" align="center">
                        <template #default="scope">
                          <el-tag type="success" effect="dark" style="font-size: 16px; font-weight: 600;">
                            {{ (scope.row.improvement * 100).toFixed(2) }}%
                          </el-tag>
                        </template>
                      </el-table-column>
                    </el-table>
                  </el-card>
                </el-col>
                <el-col :span="12">
                  <el-card class="chart-card">
                    <template #header>
                      <div class="card-header">
                        <el-icon><TrendCharts /></el-icon>
                        <span>通道对比可视化</span>
                      </div>
                    </template>
                    <div ref="channelComparisonChart" class="chart-container"></div>
                  </el-card>
                </el-col>
              </el-row>
            </template>

          </div>
        </div>
      </el-tab-pane>


      <!-- Tab 4: Online Learning -->
      <el-tab-pane label="在线学习" name="online">
        <div class="content-section">
          <!-- 1. Mock Data Import -->
          <div class="tab-header-controls">
            <div class="upload-area">
              <el-upload
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleOnlineFileSelect"
                accept=".csv,.txt,.dat"
                class="upload-component"
              >
                <el-button type="primary" :icon="Upload" :loading="onlineImporting">
                  <!-- <el-icon v-if="!onlineImporting"><Upload /></el-icon> -->
                  <span style="margin-left: 8px">{{ onlineImporting ? '正在导入...' : '导入数据文件' }}</span>
                </el-button>
              </el-upload>
              <span v-if="currentOnlineFileName" class="file-info">
                <el-icon class="file-icon"><Document /></el-icon>
                <span>{{ currentOnlineFileName }}</span>
              </span>
             </div>
          </div>

          <!-- 占位提示框 -->
          <el-row v-if="!showOnlineOriginal" :gutter="20" style="margin-top: 20px">
            <el-col :span="24">
              <el-card class="placeholder-card">
                <div class="placeholder-content">
                  <el-icon class="placeholder-icon"><InfoFilled /></el-icon>
                  <p class="placeholder-text">请点击上方"导入数据文件"按钮选择数据文件开始分析</p>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 2. Original Data Display -->
          <el-row v-if="showOnlineOriginal" :gutter="20">
            <el-col :span="24">
              <el-card class="chart-card">
                <template #header>
                  <div class="card-header">
                    <span>原始退化数据监测</span>
                  </div>
                </template>
                <div ref="originalModelChart" class="chart-container"></div>
              </el-card>
            </el-col>
          </el-row>
          
          <!-- 3. Control Buttons -->
          <el-row v-if="showOnlineOriginal && !showOnlinePredictions" :gutter="20" style="margin-top: 20px; text-align: center;">
             <el-col :span="24">
               <el-button type="success" size="large" @click="handleShowOnlinePredictions" :icon="DataAnalysis">
                 执行预测
               </el-button>
             </el-col>
          </el-row>
          
          <!-- 4. Prediction Results (Vertical Layout) -->
          <div v-if="showOnlinePredictions">
            <el-row :gutter="20" style="margin-top: 20px">
              <el-col :span="24">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>OSELM 自适应预测</span>
                    </div>
                  </template>
                  <div ref="oselmModelChart" class="chart-container-medium"></div>
                </el-card>
              </el-col>
            </el-row>
            
            <el-row :gutter="20" style="margin-top: 20px">
              <el-col :span="24">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>SGD 自适应预测</span>
                    </div>
                  </template>
                  <div ref="sgdModelChart" class="chart-container-medium"></div>
                </el-card>
              </el-col>
            </el-row>

            <!-- 5. Metrics -->
            <el-row :gutter="20" style="margin-top: 20px">
              <el-col :span="24">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>模型性能对比</span>
                    </div>
                  </template>
                  <el-table :data="onlineLearningTableData" style="width: 100%" stripe>
                    <el-table-column prop="model" label="模型" width="180" />
                    <el-table-column prop="mae" label="MAE" align="center" />
                    <el-table-column prop="rmse" label="RMSE" align="center" />
                    <el-table-column prop="mae_improve" label="MAE改善率" align="center">
                      <template #default="scope">
                        <span v-if="scope.row.mae_improve !== '-'" class="improvement-value">
                          {{ (scope.row.mae_improve * 100).toFixed(2) }}%
                        </span>
                        <span v-else>-</span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="rmse_improve" label="RMSE改善率" align="center">
                      <template #default="scope">
                        <span v-if="scope.row.rmse_improve !== '-'" class="improvement-value">
                          {{ (scope.row.rmse_improve * 100).toFixed(2) }}%
                        </span>
                        <span v-else>-</span>
                      </template>
                    </el-table-column>
                  </el-table>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { TrendCharts, DataAnalysis, InfoFilled, Operation, DataLine, Trophy, Upload, Document } from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import api from '../api';

// 20260128 修改 - 调整有限传感页面显示逻辑
const showHpsDiv = ref(false);
const buttonLoadingShowHps = ref(false);
const handleShowHpsDiv = () => {
  buttonLoadingShowHps.value = true;
  setTimeout(() => {
    showHpsDiv.value = true;
    buttonLoadingShowHps.value = false;
    nextTick(() => {
      renderLimitedSensingCharts("hps");
    });
  }, 1000);
};

const showPredictionsDiv = ref(false);
const buttonLoadingShowPredictions = ref(false);
const handleShowPredictionsDiv = () => {
  buttonLoadingShowPredictions.value = true;
  setTimeout(() => {
    showPredictionsDiv.value = true;
    buttonLoadingShowPredictions.value = false;
    nextTick(() => {
      renderLimitedSensingCharts(["rul", "channelComparison"]);
    });
  }, 1000);
};


// State
const activeTab = ref('random');
const loading = ref(false);

// Independent group states for each tab
const randomSamplingGroup = ref(1);
const reconstructionGroup = ref(1);
const limitedSensingGroup = ref(1);
const onlineLearningGroup = ref(1);
const currentLimitedFileName = ref(''); // 有限传感页面当前文件名
const showLimitedData = ref(false); // 是否显示有限传感数据
const randomImporting = ref(false);          // 随机采样导入中
const reconstructionImporting = ref(false);  // 欠采样重建导入中
const limitedImporting = ref(false);         // 有限传感导入中
const onlineImporting = ref(false);          // 在线学习导入中
const currentOnlineFileName = ref('');
const showOnlineOriginal = ref(false);
const showOnlinePredictions = ref(false);

// Data
const randomSamplingData = ref(null);
const reconstructionData = ref(null);
const limitedSensingData = ref(null);
const onlineLearningData = ref(null);
const currentFileName = ref(''); // 当前导入的文件名

// Display control states
const showOriginalSignal = ref(false); // 是否显示原始信号图
const showCompletionResults = ref(false); // 是否显示补全结果

// Reconstruction page states
const currentReconstructionFileName = ref(''); // 重建页面当前文件名
const showReconstructionOriginal = ref(false); // 是否显示欠采样效果图
const showReconstructionResults = ref(false); // 是否显示重建结果

// Chart refs for Random Sampling
const originalSignalChart = ref(null);
const linearTimeChart = ref(null);
const cubicTimeChart = ref(null);
const freqTimeChart = ref(null);
const linearFreqChart = ref(null);
const cubicFreqChart = ref(null);
const freqFreqChart = ref(null);

// Chart refs for other tabs
const undersamplingChart = ref(null);
const reconstructionDetailChart = ref(null);
const reconstructionFreqChart = ref(null);
const originalModelChart = ref(null);
const sgdModelChart = ref(null);
const oselmModelChart = ref(null);
const channelComparisonChart = ref(null);
const muChart = ref(null);
const nuChart = ref(null);
const highCurrentChart = ref(null);
const highVoltageChart = ref(null);
const highOmegaChart = ref(null);
const baseRulChart = ref(null);
const fusionRulChart = ref(null);

// Dynamic Chart Refs
const dynamicChartRefs = ref({});
const setChartRef = (el, key) => {
  if (el) {
    dynamicChartRefs.value[key] = el;
  }
};

// Chart instances
let charts = {};

// Table data
const onlineLearningTableData = ref([]);

// Limited Sensing table data - computed from limitedSensingData
const limitedSensingTableData = computed(() => {
  if (!limitedSensingData.value || !limitedSensingData.value.metrics) return [];
  
  const metrics = limitedSensingData.value.metrics;
  return [
    {
      metric: 'MAE',
      limited: metrics.mae.limited.toFixed(4),
      augmented: metrics.mae.augmented.toFixed(4),
      improvement: metrics.mae.ratio_improve
    },
    {
      metric: 'RMSE',
      limited: metrics.rmse.limited.toFixed(4),
      augmented: metrics.rmse.augmented.toFixed(4),
      improvement: metrics.rmse.ratio_improve
    }
  ];
});

// Metrics table data for random sampling
const metricsTableData = computed(() => {
  if (!randomSamplingData.value) return [];
  
  const methods = ['linear', 'cubic', 'freq'];
  const methodNames = {
    'linear': '线性插值',
    'cubic': '三次样条插值',
    'freq': '频域插值'
  };
  const tagTypes = {
    'linear': 'primary',
    'cubic': 'warning',
    'freq': 'success'
  };
  
  const rows = methods.map(method => {
    const data = randomSamplingData.value[method];
    if (!data) return null;
    
    return {
      method: methodNames[method],
      tagType: tagTypes[method],
      timeDTW: data.time_domain.similarity.toFixed(4),
      freqDTW: data.freq_domain.similarity.toFixed(4),
      combined: data.combined_similarity.toFixed(4),
      combinedNum: data.combined_similarity
    };
  }).filter(Boolean);
  
  // Find best metrics
  if (rows.length > 0) {
    const minTime = Math.min(...rows.map(r => parseFloat(r.timeDTW)));
    const minFreq = Math.min(...rows.map(r => parseFloat(r.freqDTW)));
    const minCombined = Math.min(...rows.map(r => r.combinedNum));
    
    rows.forEach(row => {
      row.isBestTime = parseFloat(row.timeDTW) === minTime;
      row.isBestFreq = parseFloat(row.freqDTW) === minFreq;
      row.isBestCombined = row.combinedNum === minCombined;
    });
    
    // Sort by combined similarity and assign ranks
    const sorted = [...rows].sort((a, b) => a.combinedNum - b.combinedNum);
    sorted.forEach((row, index) => {
      const original = rows.find(r => r.method === row.method);
      if (original) {
        original.rank = index + 1;
      }
    });
  }
  
  return rows;
});

// Watch限传感数据变化并渲染图表
watch(limitedSensingData, async (newData) => {
  if (newData) {
    // Wait for DOM updates from v-if conditions
    await nextTick();
    // Add extra delay to ensure v-if rendered elements are ready
    setTimeout(() => {
      renderLimitedSensingCharts("rawData"); // 渲染原始数据图表
    }, 100);
  }
});


// Methods
const commonDataZoom = [
  {
    type: 'inside',
    xAxisIndex: 0,
    // yAxisIndex: 0
  },
  {
    type: 'slider',
    xAxisIndex: 0,
    height: 20,
    bottom: 5
  }
];

// File handling function
const handleFileSelect = async (file) => {
  const fileName = file.name;
  currentFileName.value = fileName;
  randomImporting.value = true;
  // 重置显示状态
  showOriginalSignal.value = false;
  showCompletionResults.value = false;
  
  // 解析文件名,提取组号
  const match = fileName.match(/^随机采样数据文件\((\d+)\)/);
  if (!match) {
    ElMessage.error('文件不符合要求! 请选择随机采样数据文件');
    randomImporting.value = false;
    return; // 终止执行，不发送请求
  }

  // 解析文件名,提取组号
  // 匹配模式: (n) 其中n是数字
  // const match = fileName.match(/\((\d+)\)/);
  
  let groupNumber = 1; // 默认组1
  
  if (match) {
    const extractedNumber = parseInt(match[1], 10);
    // 检测是否为11或12，如果是则直接跳过后续判断
    if (extractedNumber === 11 || extractedNumber === 12) {
      groupNumber = extractedNumber;
      ElMessage.info(`已识别到实验组 ${groupNumber}`);
      // 这里可以直接return或使用其他方式跳过后续逻辑
    } else if (extractedNumber >= 1 && extractedNumber <= 4) {
      // 如果n在1-4范围内,使用该组
      groupNumber = extractedNumber;
    } else {
      // 否则随机选择1-4中的一组
      groupNumber = Math.floor(Math.random() * 4) + 1;
      ElMessage.info(`文件名中的组号超出范围,已自动选择实验组 ${groupNumber}`);
    }

    // // 如果n在1-4范围内,使用该组;否则随机选择1-4中的一组
    // if (extractedNumber >= 1 && extractedNumber <= 4) {
    //   groupNumber = extractedNumber;
    // } else {
    //   groupNumber = Math.floor(Math.random() * 4) + 1; // 随机选择1-4
    //   ElMessage.info(`文件名中的组号超出范围,已自动选择实验组 ${groupNumber}`);
    // }
  } else {
    // 文件名中没有(n)模式,随机选择
    groupNumber = Math.floor(Math.random() * 4) + 1;
    ElMessage.info(`未识别到实验组编号,已自动选择实验组 ${groupNumber}`);
  }
  
  randomSamplingGroup.value = groupNumber;
  
  ElMessage.success(`正在加载数据: ${fileName}...`);
  
  // 延迟1.5秒后显示原始信号
  setTimeout(async () => {
    await loadRandomSamplingData();
    showOriginalSignal.value = true;
    // 等待DOM更新后再渲染图表
    await nextTick();
    renderRandomSamplingCharts();
    ElMessage.success('数据加载完成,可以进行随机采样补全');
    randomImporting.value = false;
  }, 1500);
};

// Handle completion button click
const handleStartCompletion = async () => {
  showCompletionResults.value = true;
  ElMessage.success('正在执行随机采样补全...');
  // 等待DOM更新后再渲染对比图表
  await nextTick();
  renderRandomSamplingCharts();
};

// Handle reconstruction file select
const handleReconstructionFileSelect = async (file) => {
  const fileName = file.name;
  currentReconstructionFileName.value = fileName;
  reconstructionImporting.value = true;
  
  // 重置显示状态
  showReconstructionOriginal.value = false;
  showReconstructionResults.value = false;
  
  // 解析文件名,提取组号
  const match = fileName.match(/^欠采样重建数据文件\((\d+)\)/);
  if (!match) {
    ElMessage.error('文件不符合要求! 请选择欠采样重建数据文件');
    reconstructionImporting.value = false;
    return; // 终止执行，不发送请求
  }

  // 解析文件名,提取组号
  // const match = fileName.match(/\((\d+)\)/);
  
  let groupNumber = 1;
  
  if (match) {
    const extractedNumber = parseInt(match[1], 10);
    if (extractedNumber >= 1 && extractedNumber <= 4) {
      groupNumber = extractedNumber;
    } else {
      groupNumber = Math.floor(Math.random() * 4) + 1;
      ElMessage.info(`文件名中的组号超出范围,已自动选择实验组 ${groupNumber}`);
    }
  } else {
    groupNumber = Math.floor(Math.random() * 4) + 1;
    ElMessage.info(`未识别到实验组编号,已自动选择实验组 ${groupNumber}`);
  }
  
  reconstructionGroup.value = groupNumber;
  
  ElMessage.success(`正在加载数据: ${fileName}...`);
  
  // 延迟1.5秒后显示欠采样效果图
  setTimeout(async () => {
    await loadReconstructionData();
    showReconstructionOriginal.value = true;
    await nextTick();
    renderReconstructionCharts();
    ElMessage.success('数据加载完成,可以开始重建');
    reconstructionImporting.value = false;
  }, 1500);
};

// Handle start reconstruction button click
const handleStartReconstruction = async () => {
  showReconstructionResults.value = true;
  ElMessage.success('正在执行重建...');
  await nextTick();
  renderReconstructionCharts();
};

// Tag color helper
const getGroupTagType = (group) => {
  const types = {
    1: 'primary',
    2: 'success',
    3: 'warning',
    4: 'danger'
  };
  return types[group] || 'info';
};

// Handle limited sensing file select
const handleLimitedFileSelect = async (file) => {
  const fileName = file.name;
  currentLimitedFileName.value = fileName;
  limitedImporting.value = true;
  
  // 重置显示状态
  showLimitedData.value = false;
  showHpsDiv.value = false;   // 新增：切换文件时隐藏 HPS 区域
  showPredictionsDiv.value = false;   // 新增：切换文件时隐藏预测结果区域
  
    // 解析文件名,提取组号
    const match = fileName.match(/^有限传感数据文件\((\d+)\)/);
  if (!match) {
    ElMessage.error('文件不符合要求! 请选择有限传感数据文件');
    limitedImporting.value = false;
    return; // 终止执行，不发送请求
  }

  // 解析文件名,提取组号
  // const match = fileName.match(/\((\d+)\)/);
  
  let groupNumber = 1;
  
  if (match) {
    const extractedNumber = parseInt(match[1], 10);
    if (extractedNumber >= 1 && extractedNumber <= 4) {
      groupNumber = extractedNumber;
    } else {
      groupNumber = Math.floor(Math.random() * 4) + 1;
      ElMessage.info(`文件名中的组号超出范围,已自动选择实验组 ${groupNumber}`);
    }
  } else {
    groupNumber = Math.floor(Math.random() * 4) + 1;
    ElMessage.info(`未识别到实验组编号,已自动选择实验组 ${groupNumber}`);
  }
  
  limitedSensingGroup.value = groupNumber;
  
  ElMessage.success(`正在加载数据: ${fileName}...`);
  
  // 延迟1.5秒后显示数据
  setTimeout(async () => {
    await loadLimitedSensingData();
    showLimitedData.value = true;
    await nextTick();
    ElMessage.success('数据加载完成');
    limitedImporting.value = false;
  }, 1500);
};

const getChineseMethodName = (methodName) => {
  const map = {
    'linear': '线性插值',
    'cubic': '三次样条插值',
    'freq': '频域插值'
  };
  return map[methodName] || methodName;
};

const loadRandomSamplingData = async () => {
  try {
    const response = await api.get('/intelligent-sensing/undersampling/random-sampling/', {
      params: { group: randomSamplingGroup.value }
    });
    randomSamplingData.value = response.data;
    // 不在这里渲染图表,由handleFileSelect和handleStartCompletion控制渲染时机
  } catch (error) {
    console.error('Failed to load random sampling data:', error);
    ElMessage.error('加载随机采样数据失败');
  }
};

const loadReconstructionData = async () => {
  try {
    const response = await api.get('/intelligent-sensing/undersampling/reconstruction/', {
      params: { group: reconstructionGroup.value }
    });
    reconstructionData.value = response.data;
    // 不在这里渲染图表,由handleReconstructionFileSelect和handleStartReconstruction控制渲染时机
  } catch (error) {
    console.error('Failed to load reconstruction data:', error);
    ElMessage.error('加载欠采样重建数据失败');
  }
};

const loadLimitedSensingData = async () => {
  try {
    const response = await api.get('/intelligent-sensing/undersampling/limited-sensing/', {
      params: { group: limitedSensingGroup.value }
    });
    limitedSensingData.value = response.data;
    // Don't call renderLimitedSensingCharts here - let the watch handle it
  } catch (error) {
    console.error('Failed to load limited sensing data:', error);
    ElMessage.error('加载有限传感信息数据失败');
  }
};

const loadOnlineLearningData = async () => {
  try {
    const response = await api.get('/intelligent-sensing/undersampling/online-learning/', {
      params: { group: onlineLearningGroup.value }
    });
    onlineLearningData.value = response.data;
    prepareOnlineLearningTable();
    // Charts will be rendered by interaction handlers
  } catch (error) {
    console.error('Failed to load online learning data:', error);
    ElMessage.error('加载在线学习数据失败');
  }
};

const handleOnlineFileSelect = async (file) => {
  const fileName = file.name
  currentOnlineFileName.value = fileName;
  onlineImporting.value = true;
  showOnlineOriginal.value = false;
  showOnlinePredictions.value = false;
  onlineLearningData.value = null;

  // 解析文件名,提取组号
  const match = fileName.match(/^在线学习数据文件\((\d+)\)/);
  if (!match) {
    ElMessage.error('文件不符合要求! 请选择在线学习数据文件');
    onlineImporting.value = false;
    return; // 终止执行，不发送请求
  }
  console.log(match);  
  
  let groupNumber = 1;
  
  if (match) {
    const extractedNumber = parseInt(match[1], 10);
    if (extractedNumber >= 1 && extractedNumber <= 2) {
      groupNumber = extractedNumber;
    } else {
      ElMessage.info(`不符合的文件,已自动选择实验组 ${groupNumber}`);
    }
  } else {
    ElMessage.info(`未识别到实验组编号,已自动选择实验组 ${groupNumber}`);
  }
  
  onlineLearningGroup.value = groupNumber;

  // Simulate delay
  setTimeout(async () => {
    onlineImporting.value = false;
    showOnlineOriginal.value = true;
    
    // Ensure data is loaded
    if (!onlineLearningData.value) {
      await loadOnlineLearningData();
    }
    
    // Only render original chart for now
    await nextTick();
    renderOnlineLearningCharts();
    
    ElMessage.success('数据导入成功');
  }, 1500);
};

const handleShowOnlinePredictions = async () => {
  showOnlinePredictions.value = true;
  await nextTick();
  renderOnlineLearningCharts();
};

// Render Random Sampling Charts
const renderRandomSamplingCharts = () => {
  if (!randomSamplingData.value) return;

  const data = randomSamplingData.value;
  const methods = ['linear', 'cubic', 'freq'];
  const methodNames = {
    'linear': '线性插值',
    'cubic': '三次样条插值',
    'freq': '频域插值'
  };

  // Get first method's data to extract original signal and downsampled points
  const firstMethod = data[methods[0]];
  if (!firstMethod) return;

  // 1. Render Original Signal Chart
  if (originalSignalChart.value) {
    if (charts.originalSignal && !charts.originalSignal.isDisposed()) {
      charts.originalSignal.dispose();
    }
    const chart = echarts.init(originalSignalChart.value);
    charts.originalSignal = chart;

    chart.setOption({
      grid: { top: 50, right: 40, bottom: 55, left: 60 },
      tooltip: { trigger: 'axis' },
      legend: { 
        data: ['原始信号', '降采样点'],
        top: 5
      },
      xAxis: { type: 'value', name: '时间 (s)' },
      yAxis: { type: 'value', name: '幅值', scale: true },
      dataZoom: [
        // { type: 'inside', xAxisIndex: 0, yAxisIndex: 0 },
        { type: 'inside', xAxisIndex: 0 },
        { type: 'slider', xAxisIndex: 0, height: 20, bottom: 5 }
      ],
      series: [
        {
          name: '原始信号',
          type: 'line',
          data: firstMethod.time_domain.x3.map((x, i) => [x, firstMethod.time_domain.y3[i]]),
          showSymbol: false,
          lineStyle: { type: 'dotted', color: '#000', width: 2, opacity: 0.5 }
        },
        {
          name: '降采样点',
          type: 'scatter',
          data: firstMethod.time_domain.x2.map((x, i) => [x, firstMethod.time_domain.y2[i]]),
          itemStyle: { color: '#f5222d' },
          symbolSize: 8
        }
      ]
    });
  }

  // 2-4. Render Time Domain Charts for each method
  const timeChartRefs = {
    'linear': linearTimeChart,
    'cubic': cubicTimeChart,
    'freq': freqTimeChart
  };

  methods.forEach(method => {
    const methodData = data[method];
    const chartRef = timeChartRefs[method];
    
    if (chartRef.value && methodData) {
      const chartKey = `${method}_time`;
      if (charts[chartKey] && !charts[chartKey].isDisposed()) {
        charts[chartKey].dispose();
      }
      const chart = echarts.init(chartRef.value);
      charts[chartKey] = chart;

      chart.setOption({
        grid: { top: 50, right: 40, bottom: 55, left: 60 },
        tooltip: { trigger: 'axis' },
        legend: { 
          data: ['原始信号', methodNames[method], '降采样点'], 
          top: 5,
          textStyle: { fontSize: 11 }
        },
        xAxis: { type: 'value', name: '时间 (s)', nameTextStyle: { fontSize: 11 } },
        yAxis: { type: 'value', name: '幅值', scale: true, nameTextStyle: { fontSize: 11 } },
        dataZoom: [
          // { type: 'inside', xAxisIndex: 0, yAxisIndex: 0 },
          { type: 'inside', xAxisIndex: 0 },
          { type: 'slider', xAxisIndex: 0, height: 20, bottom: 5 }
        ],
        series: [
          {
            name: '原始信号',
            type: 'line',
            data: methodData.time_domain.x3.map((x, i) => [x, methodData.time_domain.y3[i]]),
            showSymbol: false,
            lineStyle: { type: 'dotted', color: '#000', width: 1.5, opacity: 0.4 }
          },
          {
            name: methodNames[method],
            type: 'line',
            data: methodData.time_domain.x1.map((x, i) => [x, methodData.time_domain.y1[i]]),
            smooth: true,
            itemStyle: { color: '#1890ff' },
            showSymbol: false,
            lineStyle: { width: 2 }
          },
          {
            name: '降采样点',
            type: 'scatter',
            data: methodData.time_domain.x2.map((x, i) => [x, methodData.time_domain.y2[i]]),
            itemStyle: { color: '#f5222d' },
            symbolSize: 6,
            z: 10
          }
        ]
      });
    }
  });

  // 5-7. Render Frequency Domain Charts for each method
  const freqChartRefs = {
    'linear': linearFreqChart,
    'cubic': cubicFreqChart,
    'freq': freqFreqChart
  };

  methods.forEach(method => {
    const methodData = data[method];
    const chartRef = freqChartRefs[method];
    
    if (chartRef.value && methodData) {
      const chartKey = `${method}_freq`;
      if (charts[chartKey] && !charts[chartKey].isDisposed()) {
        charts[chartKey].dispose();
      }
      const chart = echarts.init(chartRef.value);
      charts[chartKey] = chart;

      chart.setOption({
        grid: { top: 50, right: 40, bottom: 55, left: 70 },
        tooltip: { trigger: 'axis' },
        legend: { 
          data: [methodData.freq_domain.y1.label, methodData.freq_domain.y2.label], 
          top: 5,
          textStyle: { fontSize: 11 }
        },
        xAxis: { type: 'value', name: methodData.freq_domain.x.label, nameTextStyle: { fontSize: 11 } },
        yAxis: { 
          type: 'log', 
          name: '幅值 (对数)', 
          scale: true, 
          logBase: 10, 
          nameTextStyle: { fontSize: 11 },
          axisLabel: {
            formatter: function(value) {
              if (value === 0) return '0';
              // 使用科学计数法
              return value.toExponential(1);
            }
          }
        },
        dataZoom: [
          // { type: 'inside', xAxisIndex: 0, yAxisIndex: 0 },
          { type: 'inside', xAxisIndex: 0 },
          { type: 'slider', xAxisIndex: 0, height: 20, bottom: 5 }
        ],
        series: [
          {
            name: methodData.freq_domain.y1.label,
            type: 'line',
            data: methodData.freq_domain.x.value.map((x, i) => [x, methodData.freq_domain.y1.value[i]]),
            itemStyle: { color: '#52c41a', opacity: 0.5 },
            lineStyle: { width: 1.5 },
            showSymbol: false
          },
          {
            name: methodData.freq_domain.y2.label,
            type: 'line',
            data: methodData.freq_domain.x.value.map((x, i) => [x, methodData.freq_domain.y2.value[i]]),
            itemStyle: { color: '#fa8c16' },
            lineStyle: { type: 'dashed', width: 2 },
            showSymbol: false
          }
        ]
      });
    }
  });
};

const prepareLimitedSensingTable = () => {
  if (!limitedSensingData.value) return;
  const data = limitedSensingData.value;
  limitedSensingTableData.value = [
    {
      metric: 'MAE',
      limited: data.metrics.mae.limited.toFixed(4),
      augmented: data.metrics.mae.augmented.toFixed(4),
      improvement: data.metrics.mae.ratio_improve
    },
    {
      metric: 'RMSE',
      limited: data.metrics.rmse.limited.toFixed(4),
      augmented: data.metrics.rmse.augmented.toFixed(4),
      improvement: data.metrics.rmse.ratio_improve
    }
  ];
};

const prepareOnlineLearningTable = () => {
  if (!onlineLearningData.value) return;
  const dataList = onlineLearningData.value;
  
  // We want to show OSELM and SGD. We can also add a row for Baseline for reference or just show improvements.
  // The table columns are Model, MAE, RMSE, MAE Improve, RMSE Improve.
  
  onlineLearningTableData.value = dataList.map(item => {
    const metrics = item.metrics;
    const baselineMetrics = item.baseline_metrics || { mae: 1, rmse: 1 }; // Avoid div by zero
    
    const maeImprove = (baselineMetrics.mae - metrics.mae) / baselineMetrics.mae;
    const rmseImprove = (baselineMetrics.rmse - metrics.rmse) / baselineMetrics.rmse;
    
    return {
      model: `${item.method} 自适应更新`,
      mae: metrics.mae.toFixed(4),
      rmse: metrics.rmse.toFixed(4),
      mae_improve: maeImprove,
      rmse_improve: rmseImprove
    };
  });
  
  // Optionally add Baseline row at the top for context
  if (dataList.length > 0) {
    const baselineMetrics = dataList[0].baseline_metrics;
    if (baselineMetrics) {
      onlineLearningTableData.value.unshift({
        model: '基准模型 (无更新)',
        mae: baselineMetrics.mae.toFixed(4),
        rmse: baselineMetrics.rmse.toFixed(4),
        mae_improve: '-',
        rmse_improve: '-'
      });
    }
  }
};

const renderReconstructionCharts = () => {
  if (!reconstructionData.value || reconstructionData.value.length === 0) return;

  const data = reconstructionData.value[0]; // 获取数据对象
  console.log('renderReconstructionCharts called with data:', data);

  // 1. Undersampling Chart (欠采样效果)
  if (undersamplingChart.value && charts.undersamplingChart) {
    // 如果已经存在且未销毁，先销毁（或者重用，这里为了简单先销毁）
    if (!charts.undersamplingChart.isDisposed()) {
      charts.undersamplingChart.dispose();
    }
  }
  
  if (undersamplingChart.value) { // 重新检查DOM是否存在
    const chart = echarts.init(undersamplingChart.value);
    charts.undersamplingChart = chart;
    
    // 使用新的数据结构
    const undersampling = data.undersampling;
    
    chart.setOption({
      grid: { top: 40, right: 40, bottom: 50, left: 60 },
      tooltip: { trigger: 'axis' },
      legend: { data: ['原始信号', '降采样点'], top: 5 },
      xAxis: { type: 'value', name: '时间 (s)' },
      yAxis: { type: 'value', name: '幅值', scale: true },
      dataZoom: commonDataZoom,
      series: [
        {
          name: '原始信号',
          type: 'line',
          data: undersampling.x.map((x, i) => [x, undersampling.y_original[i]]),
          smooth: true,
          itemStyle: { color: '#1890ff' },
          showSymbol: false
        },
        {
          name: '降采样点',
          type: 'scatter',
          data: undersampling.y_downsampled_points.map((x, i) => [x, undersampling.y_downsampled_values[i]]),
          itemStyle: { color: '#f5222d' },
          symbolSize: 8
        }
      ]
    });
  }

  // 2. Reconstruction Detail Chart (重建细节对比)
  if (reconstructionDetailChart.value && charts.reconstructionDetailChart) {
    if (!charts.reconstructionDetailChart.isDisposed()) {
       charts.reconstructionDetailChart.dispose();
    }
  }
  
  if (reconstructionDetailChart.value) {
    const chart = echarts.init(reconstructionDetailChart.value);
    charts.reconstructionDetailChart = chart;
    
    const reconstruction = data.reconstruction;
    
    chart.setOption({
      grid: { top: 40, right: 40, bottom: 50, left: 60 },
      tooltip: { trigger: 'axis' },
      legend: { data: ['原始信号', '重建信号'], top: 5 },
      xAxis: { type: 'value', name: '时间 (s)', scale: true },
      yAxis: { type: 'value', name: '幅值', scale: true },
      dataZoom: commonDataZoom,
      series: [
        {
          name: '原始信号',
          type: 'line',
          data: reconstruction.x.map((x, i) => [x, reconstruction.y_original[i]]),
          smooth: true,
          itemStyle: { color: '#1890ff' },
          showSymbol: false,
          lineStyle: { opacity: 0.5 }
        },
        {
          name: '重建信号',
          type: 'line',
          data: reconstruction.x.map((x, i) => [x, reconstruction.y_reconstructed[i]]),
          smooth: true,
          itemStyle: { color: '#52c41a' },
          lineStyle: { type: 'dashed' },
          showSymbol: false
        }
      ]
    });
  }

  // 3. Frequency Domain Chart (频域对比)
  if (reconstructionFreqChart.value && charts.reconstructionFreqChart) {
    if (!charts.reconstructionFreqChart.isDisposed()) {
       charts.reconstructionFreqChart.dispose();
    }
  }
  
  if (reconstructionFreqChart.value) {
    const chart = echarts.init(reconstructionFreqChart.value);
    charts.reconstructionFreqChart = chart;
    
    const frequency = data.frequency;
    
    chart.setOption({
      grid: { top: 40, right: 40, bottom: 50, left: 60 },
      tooltip: { trigger: 'axis' },
      legend: { data: ['原始频谱', '重建频谱'], top: 5 },
      xAxis: { type: 'value', name: '频率 (Hz)' },
      yAxis: { type: 'log', name: '幅值 (对数)', scale: true, logBase: 10 },
      dataZoom: commonDataZoom,
      series: [
        {
          name: '原始频谱',
          type: 'line',
          data: frequency.freq.map((f, i) => [f, frequency.mag_original[i]]),
          itemStyle: { color: '#1890ff' },
          showSymbol: false
        },
        {
          name: '重建频谱',
          type: 'line',
          data: frequency.freq.map((f, i) => [f, frequency.mag_reconstructed[i]]),
          itemStyle: { color: '#fa8c16' },
          lineStyle: { type: 'dashed' },
          showSymbol: false
        }
      ]
    });
  }
};

const renderOnlineLearningCharts = () => {
  if (!onlineLearningData.value) return;

  const dataList = onlineLearningData.value;

  // Helper to find data by method name
  const getDataByMethod = (method) => dataList.find(item => item.method === method);

  const oselmData = getDataByMethod('OSELM');

  // 1. Raw Data Chart (using originalModelChart ref)
  if (originalModelChart.value && oselmData) { // Use OSELM data to extract original signal
    if (charts.originalModelChart && !charts.originalModelChart.isDisposed()) {
      charts.originalModelChart.dispose();
    }
    const chart = echarts.init(originalModelChart.value);
    charts.originalModelChart = chart;
    
    // We want to show the full sequence if possible, or same slice
    const indices = oselmData.indices;
    const len = indices.length;

    chart.setOption({
      // Title removed as requested
      grid: { top: 40, right: 30, bottom: 40, left: 50 },
      tooltip: { trigger: 'axis' },
      legend: { data: ['真实观测值'], top: 5 }, // Moved to top
      xAxis: { type: 'category', data: indices, name: '时间步', nameLocation: 'middle', nameGap: 25 },
      yAxis: { type: 'value', name: '幅值', scale: true },
      dataZoom: commonDataZoom,
      series: [
        {
          name: '真实观测值',
          type: 'line',
          data: oselmData.original_data,
          lineStyle: { color: '#000', width: 1.5 },
          showSymbol: false,
          areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(0, 0, 0, 0.1)' },
                { offset: 1, color: 'rgba(0, 0, 0, 0.01)' }
              ])
          }
        }
      ]
    });
  }

  // 2. OSELM Model Chart
  if (oselmModelChart.value && oselmData) {
    if (charts.oselmModelChart && !charts.oselmModelChart.isDisposed()) {
      charts.oselmModelChart.dispose();
    }
    const chart = echarts.init(oselmModelChart.value);
    charts.oselmModelChart = chart;
    
    const indices = oselmData.indices;
    // Align lengths
    const len = Math.min(indices.length, oselmData.original_data.length, oselmData.updated_preds.length, oselmData.baseline_preds.length);
    
    chart.setOption({
      title: { 
        text: 'OSELM 自适应更新效果', 
        left: 'center',
        textStyle: { fontSize: 14 }
      },
      grid: { top: 70, right: 30, bottom: 40, left: 50 }, // Increased top grid for legend spacing
      tooltip: { trigger: 'axis' },
      legend: { data: ['真实值', '基准预测', '更新预测'], top: 35 }, // Moved further down
      xAxis: { type: 'category', data: indices.slice(0, len), name: '时间步', nameLocation: 'middle', nameGap: 25 },
      yAxis: { type: 'value', name: '幅值', scale: true },
      dataZoom: commonDataZoom,
      series: [
        {
          name: '真实值',
          type: 'line',
          data: oselmData.original_data.slice(0, len),
          lineStyle: { color: '#000', width: 1.5, opacity: 0.3 }, // Faint original for context
          showSymbol: false
        },
        {
          name: '基准预测',
          type: 'line',
          data: oselmData.baseline_preds.slice(0, len),
          lineStyle: { color: '#999', type: 'dotted', width: 1.5 },
          showSymbol: false
        },
        {
          name: '更新预测',
          type: 'line',
          data: oselmData.updated_preds.slice(0, len),
          itemStyle: { color: '#f5222d' }, // Red for OSELM
          lineStyle: { width: 2 },
          showSymbol: false
        }
      ]
    });
  }

  // 3. SGD Model Chart
  const sgdData = getDataByMethod('SGD');
  if (sgdModelChart.value && sgdData) {
    if (charts.sgdModelChart && !charts.sgdModelChart.isDisposed()) {
      charts.sgdModelChart.dispose();
    }
    const chart = echarts.init(sgdModelChart.value);
    charts.sgdModelChart = chart;
    
    const indices = sgdData.indices;
    const len = Math.min(indices.length, sgdData.original_data.length, sgdData.updated_preds.length, sgdData.baseline_preds.length);

    chart.setOption({
      title: { 
        text: 'SGD 自适应更新效果', 
        left: 'center',
        textStyle: { fontSize: 14 }
      },
      grid: { top: 70, right: 30, bottom: 40, left: 50 }, // Increased top grid
      tooltip: { trigger: 'axis' },
      legend: { data: ['真实值', '基准预测', '更新预测'], top: 35 }, // Moved further down
      xAxis: { type: 'category', data: indices.slice(0, len), name: '时间步', nameLocation: 'middle', nameGap: 25 },
      yAxis: { type: 'value', name: '幅值', scale: true },
      dataZoom: commonDataZoom,
      series: [
        {
          name: '真实值',
          type: 'line',
          data: sgdData.original_data.slice(0, len),
          lineStyle: { color: '#000', width: 1.5, opacity: 0.3 }, // Faint original
          showSymbol: false
        },
        {
          name: '基准预测',
          type: 'line',
          data: sgdData.baseline_preds.slice(0, len),
          lineStyle: { color: '#999', type: 'dotted', width: 1.5 },
          showSymbol: false
        },
        {
          name: '更新预测',
          type: 'line',
          data: sgdData.updated_preds.slice(0, len),
          itemStyle: { color: '#52c41a' }, // Green for SGD
          lineStyle: { width: 2 },
          showSymbol: false
        }
      ]
    });
  }
};

// const renderLimitedSensingCharts = () => {
//   if (!limitedSensingData.value) return;

//   const data = limitedSensingData.value;
//   console.log('renderLimitedSensingCharts called with data:', data);
//   console.log('Chart refs:', {
//     channelComparisonChart: channelComparisonChart.value,
//     muChart: muChart.value,
//     nuChart: nuChart.value,
//     baseRulChart: baseRulChart.value,
//     fusionRulChart: fusionRulChart.value
//   });

//   // Channel Comparison Chart
//   if (channelComparisonChart.value) {
//     if (charts.channelComparisonChart && !charts.channelComparisonChart.isDisposed()) {
//       charts.channelComparisonChart.dispose();
//     }
//     const chart = echarts.init(channelComparisonChart.value);
//     charts.channelComparisonChart = chart;
    
//     const metrics = data.metrics;
//     chart.setOption({
//       grid: { top: 40, right: 40, bottom: 50, left: 60 },
//       tooltip: {
//         trigger: 'axis',
//         axisPointer: { type: 'shadow' }
//       },
//       legend: {
//         data: ['有限通道', '扩增通道'],
//         bottom: 0
//       },
//       xAxis: {
//         type: 'category',
//         data: ['MAE', 'RMSE'],
//         axisLabel: { fontSize: 14, fontWeight: 'bold' }
//       },
//       yAxis: {
//         type: 'value',
//         name: '误差值',
//         axisLabel: { formatter: '{value}' }
//       },
//       dataZoom: commonDataZoom,
//       series: [
//         {
//           name: '有限通道',
//           type: 'bar',
//           data: [metrics.mae.limited, metrics.rmse.limited],
//           itemStyle: {
//             color: '#fa8c16',
//             borderRadius: [4, 4, 0, 0]
//           },
//           label: {
//             show: true,
//             position: 'top',
//             formatter: '{c}'
//           }
//         },
//         {
//           name: '扩增通道',
//           type: 'bar',
//           data: [metrics.mae.augmented, metrics.rmse.augmented],
//           itemStyle: {
//             color: '#52c41a',
//             borderRadius: [4, 4, 0, 0]
//           },
//           label: {
//             show: true,
//             position: 'top',
//             formatter: '{c}'
//           }
//         }
//       ]
//     });
//   }

//   // Hidden Parameters Charts
//   if (data.hps) {
//     const muData = data.hps.mu;
//     const nuData = data.hps.nu;
    
//     // Mu Chart
//     if (muChart.value && muData) {
//       if (charts.muChart && !charts.muChart.isDisposed()) {
//         charts.muChart.dispose();
//       }
//       const chart = echarts.init(muChart.value);
//       charts.muChart = chart;
      
//       // Process mu data - it's a 2D array, we need to extract one dimension
//       const muValues = Array.isArray(muData[0]) ? muData.map(row => row[0]) : muData;
//       const indices = Array.from({ length: muValues.length }, (_, i) => i);
      
//       chart.setOption({
//         grid: { top: 40, right: 40, bottom: 50, left: 60 },
//         tooltip: {
//           trigger: 'axis',
//           formatter: params => {
//             const point = params[0];
//             return `样本点: ${point.name}<br/>μ: ${point.value.toFixed(6)}`;
//           }
//         },
//         xAxis: {
//           type: 'category',
//           data: indices,
//           name: '样本点',
//           axisLabel: {
//             interval: Math.floor(indices.length / 10)
//           }
//         },
//         yAxis: {
//           type: 'value',
//           name: '润滑效率 μ',
//           axisLabel: { formatter: '{value}' },
//           scale: true
//         },
//         dataZoom: commonDataZoom,
//         series: [
//           {
//             name: 'μ',
//             type: 'line',
//             data: muValues,
//             smooth: true,
//             itemStyle: { color: '#1890ff' },
//             lineStyle: { width: 2 },
//             areaStyle: {
//               color: {
//                 type: 'linear',
//                 x: 0, y: 0, x2: 0, y2: 1,
//                 colorStops: [
//                   { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
//                   { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
//                 ]
//               }
//             },
//             showSymbol: false
//           }
//         ]
//       });
//     }
    
//     // Nu Chart
//     if (nuChart.value && nuData) {
//       if (charts.nuChart && !charts.nuChart.isDisposed()) {
//         charts.nuChart.dispose();
//       }
//       const chart = echarts.init(nuChart.value);
//       charts.nuChart = chart;
      
//       // Process nu data - it's a 2D array, we need to extract one dimension
//       const nuValues = Array.isArray(nuData[0]) ? nuData.map(row => row[0]) : nuData;
//       const indices = Array.from({ length: nuValues.length }, (_, i) => i);
      
//       chart.setOption({
//         grid: { top: 40, right: 40, bottom: 50, left: 60 },
//         tooltip: {
//           trigger: 'axis',
//           formatter: params => {
//             const point = params[0];
//             return `样本点: ${point.name}<br/>ν: ${point.value.toFixed(6)}`;
//           }
//         },
//         xAxis: {
//           type: 'category',
//           data: indices,
//           name: '样本点',
//           axisLabel: {
//             interval: Math.floor(indices.length / 10)
//           }
//         },
//         yAxis: {
//           type: 'value',
//           name: '粘度 ν',
//           axisLabel: { formatter: '{value}' },
//           scale: true
//         },
//         dataZoom: commonDataZoom,
//         series: [
//           {
//             name: 'ν',
//             type: 'line',
//             data: nuValues,
//             smooth: true,
//             itemStyle: { color: '#52c41a' },
//             lineStyle: { width: 2 },
//             areaStyle: {
//               color: {
//                 type: 'linear',
//                 x: 0, y: 0, x2: 0, y2: 1,
//                 colorStops: [
//                   { offset: 0, color: 'rgba(82, 196, 26, 0.3)' },
//                   { offset: 1, color: 'rgba(82, 196, 26, 0.05)' }
//                 ]
//               }
//             },
//             showSymbol: false
//           }
//         ]
//       });
//     }
//   }

//   // RUL Prediction Charts
//   if (data.rul_results) {
//     // Base Model RUL
//     if (baseRulChart.value && data.rul_results.base) {
//        if (charts.baseRulChart && !charts.baseRulChart.isDisposed()) {
//         charts.baseRulChart.dispose();
//       }
//       const chart = echarts.init(baseRulChart.value);
//       charts.baseRulChart = chart;
      
//       const rulData = data.rul_results.base;
//       // Flatten arrays if needed
//       const trueRul = rulData.true.flat();
//       const predRul = rulData.pred.flat();
//       const indices = Array.from({ length: trueRul.length }, (_, i) => i);

//       chart.setOption({
//         grid: { top: 30, right: 30, bottom: 40, left: 50 },
//         tooltip: { trigger: 'axis' },
//         legend: { data: ['真实寿命', '预测寿命'], bottom: 0 },
//         xAxis: { type: 'category', data: indices, name: '样本点' },
//         yAxis: { type: 'value', name: '剩余寿命 (RUL)', scale: true },
//         dataZoom: commonDataZoom,
//         series: [
//           {
//             name: '真实寿命',
//             type: 'line',
//             data: trueRul,
//              lineStyle: { color: '#000', type: 'dotted', width: 2, opacity: 0.6 },
//             showSymbol: false
//           },
//           {
//             name: '预测寿命',
//             type: 'line',
//             data: predRul,
//              lineStyle: { color: '#f5222d', width: 2 },
//             showSymbol: false
//           }
//         ]
//       });
//     }

//     // Fusion Model RUL
//     if (fusionRulChart.value && data.rul_results.fusion_u_v) {
//        if (charts.fusionRulChart && !charts.fusionRulChart.isDisposed()) {
//         charts.fusionRulChart.dispose();
//       }
//       const chart = echarts.init(fusionRulChart.value);
//       charts.fusionRulChart = chart;
      
//       const rulData = data.rul_results.fusion_u_v;
//       const trueRul = rulData.true.flat();
//       const predRul = rulData.pred.flat();
//       const indices = Array.from({ length: trueRul.length }, (_, i) => i);

//       chart.setOption({
//         grid: { top: 30, right: 30, bottom: 40, left: 50 },
//         tooltip: { trigger: 'axis' },
//         legend: { data: ['真实寿命', '预测寿命'], bottom: 0 },
//         xAxis: { type: 'category', data: indices, name: '样本点' },
//         yAxis: { type: 'value', name: '剩余寿命 (RUL)', scale: true },
//         dataZoom: commonDataZoom,
//         series: [
//           {
//             name: '真实寿命',
//             type: 'line',
//             data: trueRul,
//              lineStyle: { color: '#000', type: 'dotted', width: 2, opacity: 0.6 },
//             showSymbol: false
//           },
//           {
//             name: '预测寿命',
//             type: 'line',
//             data: predRul,
//              lineStyle: { color: '#52c41a', width: 2 },
//             showSymbol: false
//           }
//         ]
//       });
//     }
//   }
// };

const renderLimitedSensingCharts = (chartsToRender = 'all') => {
  if (!limitedSensingData.value) return;

  const data = limitedSensingData.value;
  console.log('renderLimitedSensingCharts called with data:', data);
  console.log('Chart refs:', {
    channelComparisonChart: channelComparisonChart.value,
    muChart: muChart.value,
    nuChart: nuChart.value,
    baseRulChart: baseRulChart.value,
    fusionRulChart: fusionRulChart.value,
    highCurrentChart: highCurrentChart.value,
    highVoltageChart: highVoltageChart.value,
    highOmegaChart: highOmegaChart.value
  });

  // 判断是否应该渲染某个图表
  const shouldRender = (chartName) => {
    if (chartsToRender === 'all') return true;
    if (Array.isArray(chartsToRender)) return chartsToRender.includes(chartName);
    return chartsToRender === chartName;
  };

  // Raw Data Charts
  if (shouldRender('rawData') && data.raw_data) {
    // 电流
    if (highCurrentChart.value) {
      if (charts.highCurrentChart && !charts.highCurrentChart.isDisposed()) {
        charts.highCurrentChart.dispose();
      }
      const currentChart = echarts.init(highCurrentChart.value);
      charts.highCurrentChart = currentChart;
      currentChart.setOption({
        grid: { top: 40, right: 40, bottom: 50, left: 60 },
        tooltip: { trigger: 'axis' },
        legend: { data: ['电流'], bottom: 0 },
        xAxis: { type: 'category', data: data.raw_data.high_current.map((_, i) => i), name: '样本点' },
        yAxis: { type: 'value', name: '电流', scale: true },
        dataZoom: commonDataZoom,
        series: [
          {
            name: '电流',
            type: 'line',
            data: data.raw_data.high_current,
            smooth: true,
            itemStyle: { color: '#1890ff' },
          }
        ],
        showSymbol: false
      });
    }

    // 电压
    if (highVoltageChart.value) {
      if (charts.highVoltageChart && !charts.highVoltageChart.isDisposed()) {
        charts.highVoltageChart.dispose();
      }
      const voltageChart = echarts.init(highVoltageChart.value);
      charts.highVoltageChart = voltageChart;
      voltageChart.setOption({
        grid: { top: 40, right: 40, bottom: 50, left: 60 },
        tooltip: { trigger: 'axis' },
        legend: { data: ['电压'], bottom: 0 },
        xAxis: { type: 'category', data: data.raw_data.high_voltage.map((_, i) => i), name: '样本点' },
        yAxis: { type: 'value', name: '电压', scale: true },
        dataZoom: commonDataZoom,
        series: [
          {
            name: '电压',
            type: 'line',
            data: data.raw_data.high_voltage,
            smooth: true,
            itemStyle: { color: '#1890ff' },
          }
        ],
        showSymbol: false
      });
    }

    // 转速
    if (highOmegaChart.value) {
      if (charts.highOmegaChart && !charts.highOmegaChart.isDisposed()) {
        charts.highOmegaChart.dispose();
      }
      const omegaChart = echarts.init(highOmegaChart.value);
      charts.highOmegaChart = omegaChart;
      omegaChart.setOption({
        grid: { top: 40, right: 40, bottom: 50, left: 60 },
        tooltip: { trigger: 'axis' },
        legend: { data: ['转速'], bottom: 0 },
        xAxis: { type: 'category', data: data.raw_data.high_omega.map((_, i) => i), name: '样本点' },
        yAxis: { type: 'value', name: '转速', scale: true },
        dataZoom: commonDataZoom,
        series: [
          {
            name: '转速',
            type: 'line',
            data: data.raw_data.high_omega,
            smooth: true,
            itemStyle: { color: '#1890ff' },
          }
        ],
        showSymbol: false
      });
    }
  }

  // Channel Comparison Chart
  if (shouldRender('channelComparison') && channelComparisonChart.value) {
    if (charts.channelComparisonChart && !charts.channelComparisonChart.isDisposed()) {
      charts.channelComparisonChart.dispose();
    }
    const chart = echarts.init(channelComparisonChart.value);
    charts.channelComparisonChart = chart;
    
    const metrics = data.metrics;
    chart.setOption({
      grid: { top: 40, right: 40, bottom: 50, left: 60 },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      legend: {
        data: ['有限通道', '扩增通道'],
        bottom: 0
      },
      xAxis: {
        type: 'category',
        data: ['MAE', 'RMSE'],
        axisLabel: { fontSize: 14, fontWeight: 'bold' }
      },
      yAxis: {
        type: 'value',
        name: '误差值',
        axisLabel: { formatter: '{value}' }
      },
      dataZoom: commonDataZoom,
      series: [
        {
          name: '有限通道',
          type: 'bar',
          data: [metrics.mae.limited, metrics.rmse.limited],
          itemStyle: {
            color: '#fa8c16',
            borderRadius: [4, 4, 0, 0]
          },
          label: {
            show: true,
            position: 'top',
            formatter: '{c}'
          }
        },
        {
          name: '扩增通道',
          type: 'bar',
          data: [metrics.mae.augmented, metrics.rmse.augmented],
          itemStyle: {
            color: '#52c41a',
            borderRadius: [4, 4, 0, 0]
          },
          label: {
            show: true,
            position: 'top',
            formatter: '{c}'
          }
        }
      ]
    });
  }

  // Hidden Parameters Charts
  if (shouldRender('hps') && data.hps) {
    const muData = data.hps.mu;
    const nuData = data.hps.nu;
    
    // Mu Chart
    if (muChart.value && muData) {
      if (charts.muChart && !charts.muChart.isDisposed()) {
        charts.muChart.dispose();
      }
      const chart = echarts.init(muChart.value);
      charts.muChart = chart;
      
      // Process mu data - it's a 2D array, we need to extract one dimension
      const muValues = Array.isArray(muData[0]) ? muData.map(row => row[0]) : muData;
      const indices = Array.from({ length: muValues.length }, (_, i) => i);
      
      chart.setOption({
        grid: { top: 40, right: 40, bottom: 50, left: 60 },
        tooltip: {
          trigger: 'axis',
          formatter: params => {
            const point = params[0];
            return `样本点: ${point.name}<br/>μ: ${point.value.toFixed(6)}`;
          }
        },
        xAxis: {
          type: 'category',
          data: indices,
          name: '样本点',
          axisLabel: {
            interval: Math.floor(indices.length / 10)
          }
        },
        yAxis: {
          type: 'value',
          name: '润滑效率 μ',
          axisLabel: { formatter: '{value}' },
          scale: true
        },
        dataZoom: commonDataZoom,
        series: [
          {
            name: 'μ',
            type: 'line',
            data: muValues,
            smooth: true,
            itemStyle: { color: '#1890ff' },
            lineStyle: { width: 2 },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
                  { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
                ]
              }
            },
            showSymbol: false
          }
        ]
      });
    }
    
    // Nu Chart
    if (nuChart.value && nuData) {
      if (charts.nuChart && !charts.nuChart.isDisposed()) {
        charts.nuChart.dispose();
      }
      const chart = echarts.init(nuChart.value);
      charts.nuChart = chart;
      
      // Process nu data - it's a 2D array, we need to extract one dimension
      const nuValues = Array.isArray(nuData[0]) ? nuData.map(row => row[0]) : nuData;
      const indices = Array.from({ length: nuValues.length }, (_, i) => i);
      
      chart.setOption({
        grid: { top: 40, right: 40, bottom: 50, left: 60 },
        tooltip: {
          trigger: 'axis',
          formatter: params => {
            const point = params[0];
            return `样本点: ${point.name}<br/>ν: ${point.value.toFixed(6)}`;
          }
        },
        xAxis: {
          type: 'category',
          data: indices,
          name: '样本点',
          axisLabel: {
            interval: Math.floor(indices.length / 10)
          }
        },
        yAxis: {
          type: 'value',
          name: '粘度 ν',
          axisLabel: { formatter: '{value}' },
          scale: true
        },
        dataZoom: commonDataZoom,
        series: [
          {
            name: 'ν',
            type: 'line',
            data: nuValues,
            smooth: true,
            itemStyle: { color: '#52c41a' },
            lineStyle: { width: 2 },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0, y: 0, x2: 0, y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(82, 196, 26, 0.3)' },
                  { offset: 1, color: 'rgba(82, 196, 26, 0.05)' }
                ]
              }
            },
            showSymbol: false
          }
        ]
      });
    }
  }

  // RUL Prediction Charts
  if (shouldRender('rul') && data.rul_results) {
    // Base Model RUL
    if (baseRulChart.value && data.rul_results.base) {
       if (charts.baseRulChart && !charts.baseRulChart.isDisposed()) {
        charts.baseRulChart.dispose();
      }
      const chart = echarts.init(baseRulChart.value);
      charts.baseRulChart = chart;
      
      const rulData = data.rul_results.base;
      // Flatten arrays if needed
      const trueRul = rulData.true.flat();
      const predRul = rulData.pred.flat();
      const indices = Array.from({ length: trueRul.length }, (_, i) => i);

      chart.setOption({
        grid: { top: 30, right: 30, bottom: 40, left: 50 },
        tooltip: { trigger: 'axis' },
        legend: { data: ['真实寿命', '预测寿命'], bottom: 0 },
        xAxis: { type: 'category', data: indices, name: '样本点' },
        yAxis: { type: 'value', name: '剩余寿命 (RUL)', scale: true },
        dataZoom: commonDataZoom,
        series: [
          {
            name: '真实寿命',
            type: 'line',
            data: trueRul,
             lineStyle: { color: '#000', type: 'dotted', width: 2, opacity: 0.6 },
            showSymbol: false
          },
          {
            name: '预测寿命',
            type: 'line',
            data: predRul,
             lineStyle: { color: '#f5222d', width: 2 },
            showSymbol: false
          }
        ]
      });
    }

    // Fusion Model RUL
    if (fusionRulChart.value && data.rul_results.fusion_u_v) {
       if (charts.fusionRulChart && !charts.fusionRulChart.isDisposed()) {
        charts.fusionRulChart.dispose();
      }
      const chart = echarts.init(fusionRulChart.value);
      charts.fusionRulChart = chart;
      
      const rulData = data.rul_results.fusion_u_v;
      const trueRul = rulData.true.flat();
      const predRul = rulData.pred.flat();
      const indices = Array.from({ length: trueRul.length }, (_, i) => i);

      chart.setOption({
        grid: { top: 30, right: 30, bottom: 40, left: 50 },
        tooltip: { trigger: 'axis' },
        legend: { data: ['真实寿命', '预测寿命'], bottom: 0 },
        xAxis: { type: 'category', data: indices, name: '样本点' },
        yAxis: { type: 'value', name: '剩余寿命 (RUL)', scale: true },
        dataZoom: commonDataZoom,
        series: [
          {
            name: '真实寿命',
            type: 'line',
            data: trueRul,
             lineStyle: { color: '#000', type: 'dotted', width: 2, opacity: 0.6 },
            showSymbol: false
          },
          {
            name: '预测寿命',
            type: 'line',
            data: predRul,
             lineStyle: { color: '#52c41a', width: 2 },
            showSymbol: false
          }
        ]
      });
    }
  }
};

const handleTabChange = () => {
  loadDataForCurrentTab();
};

const loadDataForCurrentTab = async () => {
  loading.value = true;
  try {
    switch (activeTab.value) {
      case 'random':
        await loadRandomSamplingData();
        break;
      case 'reconstruction':
        await loadReconstructionData();
        break;
      case 'limited':
        await loadLimitedSensingData();
        break;
      case 'online':
        await loadOnlineLearningData();
        break;
    }
  } finally {
    loading.value = false;
  }
};

const resizeCharts = () => {
  Object.values(charts).forEach(chart => {
    if (chart && !chart.isDisposed()) {
      chart.resize();
    }
  });
};

// Lifecycle
onMounted(async () => {
  // await loadDataForCurrentTab();
  window.addEventListener('resize', resizeCharts);
});

// Cleanup
import { onBeforeUnmount } from 'vue';
onBeforeUnmount(() => {
  Object.values(charts).forEach(chart => {
    if (chart && !chart.isDisposed()) {
      chart.dispose();
    }
  });
  window.removeEventListener('resize', resizeCharts);
});
</script>

<style scoped>
.undersampling-container {
  padding: var(--cmg-space-6);
  background: var(--cmg-bg-secondary);
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--cmg-space-6);
  padding: var(--cmg-space-5);
  background: var(--cmg-bg-primary);
  border-radius: var(--cmg-radius-lg);
  box-shadow: var(--cmg-shadow-sm);
}

.header-content {
  flex: 1;
}

.page-title {
  margin: 0;
  font-size: var(--cmg-text-3xl);
  font-weight: 700;
  color: var(--cmg-aerospace-primary);
  background: linear-gradient(135deg, var(--cmg-aerospace-primary), var(--cmg-aerospace-accent));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.page-subtitle {
  margin: var(--cmg-space-2) 0 0 0;
  font-size: var(--cmg-text-sm);
  color: var(--cmg-text-tertiary);
  font-style: italic;
}

.header-controls {
  display: flex;
  gap: var(--cmg-space-3);
}

.group-selector {
  width: 200px;
}

.main-tabs {
  background: var(--cmg-bg-primary);
  border-radius: var(--cmg-radius-lg);
  padding: var(--cmg-space-4);
  box-shadow: var(--cmg-shadow-sm);
}

.sub-tabs {
  margin-top: var(--cmg-space-4);
}

.content-section {
  padding: var(--cmg-space-4);
}

.tab-header-controls {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--cmg-space-4);
  padding: var(--cmg-space-3);
  background: var(--cmg-bg-secondary);
  border-radius: var(--cmg-radius-md);
}

.tab-header-controls .group-selector {
  width: 200px;
}

.upload-area {
  display: flex;
  align-items: center;
  gap: 20px;
  width: 100%;
  justify-content: space-between;
}

.upload-component {
  display: inline-block;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--cmg-text-secondary);
  font-size: 14px;
}

.file-icon {
  color: var(--cmg-primary);
  font-size: 18px;
}


.chart-card {
  border-radius: var(--cmg-radius-lg);
  box-shadow: var(--cmg-shadow-sm);
}

.chart-container-medium {
  height: 300px;
  width: 100%;
}

.chart-container-small {
  height: 250px;
  width: 100%;
}

.best-metric {
  font-weight: 700;
  color: #67c23a;
}

.card-header {
  font-weight: 600;
  color: var(--cmg-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 18px;
  color: var(--cmg-primary);
}


.chart-container {
  height: 350px;
  width: 100%;
}

.metric-card {
  border-radius: var(--cmg-radius-lg);
  box-shadow: var(--cmg-shadow-sm);
  border-left: 4px solid var(--cmg-aerospace-primary);
}

.metric-content {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-3);
  padding: var(--cmg-space-2);
}

.metric-icon {
  font-size: 24px;
  color: var(--cmg-aerospace-primary);
}

.metric-label {
  font-size: var(--cmg-text-base);
  color: var(--cmg-text-secondary);
  font-weight: 500;
}

.metric-value {
  font-size: var(--cmg-text-xl);
  font-weight: 700;
  color: var(--cmg-aerospace-primary);
}

.info-card {
  text-align: center;
  border-radius: var(--cmg-radius-lg);
  box-shadow: var(--cmg-shadow-sm);
}

.info-content {
  padding: var(--cmg-space-4);
}

.info-label {
  font-size: var(--cmg-text-sm);
  color: var(--cmg-text-secondary);
  margin-bottom: var(--cmg-space-2);
}

.info-value {
  font-size: var(--cmg-text-3xl);
  font-weight: 700;
}

.info-value.primary {
  color: var(--cmg-aerospace-primary);
}

.info-value.success {
  color: #52c41a;
}

.info-value.warning {
  color: #fa8c16;
}

.improvement-value {
  color: #52c41a;
  font-weight: 600;
}

.explanation-card {
  border-radius: var(--cmg-radius-lg);
  box-shadow: var(--cmg-shadow-md);
  border-left: 4px solid var(--cmg-aerospace-primary);
}

.explanation-content {
  line-height: 1.8;
  color: var(--cmg-text-primary);
}

.explanation-content p {
  margin: var(--cmg-space-3) 0;
}

.explanation-content strong {
  color: var(--cmg-aerospace-primary);
  font-weight: 600;
}

.header-icon {
  margin-right: var(--cmg-space-2);
  font-size: 18px;
  color: var(--cmg-aerospace-primary);
}

.info-desc {
  font-size: var(--cmg-text-xs);
  color: var(--cmg-text-tertiary);
  margin-top: var(--cmg-space-1);
}

.augmented-value {
  color: #52c41a;
  font-weight: 600;
}

.hidden-params-desc {
  padding: var(--cmg-space-4);
  background: var(--cmg-bg-secondary);
  border-radius: var(--cmg-radius-md);
  color: var(--cmg-text-secondary);
  line-height: 1.6;
  text-align: center;
}

.hidden-params-desc strong {
  color: var(--cmg-aerospace-accent);
}

:deep(.el-table) {
  font-size: var(--cmg-text-base);
}

:deep(.el-table th) {
  background-color: var(--cmg-bg-secondary);
  color: var(--cmg-text-primary);
  font-weight: 600;
}

/* Dark mode */
[data-theme="dark"] .page-header,
[data-theme="dark"] .main-tabs,
[data-theme="dark"] .chart-card,
[data-theme="dark"] .metric-card,
[data-theme="dark"] .info-card {
  background: var(--cmg-bg-primary);
}

.metric-divider {
  margin: 0 10px;
  color: #dcdfe6;
}

/* 占位提示框样式 */
.placeholder-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
  border: 2px dashed #d0d7de;
  box-shadow: none;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.placeholder-icon {
  font-size: 48px;
  color: #91a7c1;
  margin-bottom: 16px;
}

.placeholder-text {
  font-size: 16px;
  color: #666;
  margin: 0;
  font-weight: 500;
}

[data-theme="dark"] .placeholder-card {
  background: linear-gradient(135deg, #1e2329 0%, #2a2f3a 100%);
  border-color: #3a3f4a;
}

[data-theme="dark"] .placeholder-icon {
  color: #5a6a7a;
}

[data-theme="dark"] .placeholder-text {
  color: #aaa;
}
</style>
