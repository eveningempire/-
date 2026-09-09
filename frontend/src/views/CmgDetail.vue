<template>
  <div class="cmg-detail-page">
    <!-- 数据筛选与控制（不再悬浮） -->
    <SectionCard 
      title="数据筛选与控制"
      icon="Filter"
      size="small"
      class="cmg-filters-card"
    >
        <template #actions>
          <RealtimeIndicator 
            v-if="mode === 'realtime'"
            :status="wsConnected ? 'connected' : (wsConnecting ? 'connecting' : 'disconnected')"
            :last-update-time="lastUpdateTime"
            :ws-url="wsUrl"
            :reconnect-count="wsReconnectAttempts"
            :error="wsError"
          />
        </template>
        
        <div class="cmg-toolbar-content">
          <!-- 模式切换：历史 | 实时 -->
          <div class="cmg-mode-switch">
            <el-radio-group v-model="mode" size="small">
              <el-radio-button label="history">历史</el-radio-button>
              <el-radio-button label="realtime">实时</el-radio-button>
            </el-radio-group>
            <el-text v-if="mode === 'realtime' && !hasCmgSelected" type="warning" class="cmg-light-hint">请选择 CMG</el-text>
          </div>

          <el-form :model="query" inline class="cmg-filter-form">
            <el-form-item label="CMG">
              <el-select 
                v-model="query.cmgId" 
                placeholder="选择 CMG" 
                :style="{ minWidth: '260px' }" 
                @change="onCmgChange"
                clearable
                filterable
              >
                <el-option 
                  v-for="c in cmgList" 
                  :key="c.id" 
                  :label="c.name + '(' + c.cmg_id + ')'" 
                  :value="c.cmg_id" 
                />
              </el-select>
            </el-form-item>
            
            <el-form-item v-if="mode === 'history'" label="时间范围">
              <el-date-picker 
                v-model="query.dates" 
                type="datetimerange" 
                range-separator="-" 
                start-placeholder="开始时间" 
                end-placeholder="结束时间"
                @change="onDateChange"
                :style="{ minWidth: '320px' }"
                :shortcuts="timeShortcuts"
              />
            </el-form-item>
            
            <el-form-item class="cmg-actions-item">
              <template v-if="mode === 'history'">
                <el-button-group>
                  <el-button type="primary" @click="loadData" :loading="loading" :disabled="!hasCmgSelected || loading">
                    <el-icon><Search /></el-icon>
                    查询
                  </el-button>
                  <el-button @click="resetFilters" :disabled="!hasCmgSelected || loading">
                    <el-icon><RefreshLeft /></el-icon>
                    重置
                  </el-button>
                </el-button-group>
              </template>
              <template v-else>
                <el-button type="primary" @click="toggleLive" :loading="wsConnecting" :disabled="!hasCmgSelected || wsConnecting">
                  <el-icon>
                    <VideoPause v-if="live" />
                    <VideoPlay v-else />
                  </el-icon>
                  {{ live ? '停止实时' : '开始实时' }}
                </el-button>
              </template>
            </el-form-item>
          </el-form>
          
          <!-- 时间轴和推荐时间段 -->
          <div v-if="mode === 'history'" class="cmg-time-controls">
            <!-- 时间轴 -->
            <div class="cmg-timeline-section">
              <div class="cmg-timeline-header">
                <label class="cmg-timeline-label">数据时间轴：</label>
                <el-button 
                  size="small" 
                  type="primary" 
                  text 
                  @click="refreshTimeline"
                  :loading="timelineLoading"
                  title="刷新时间轴"
                >
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
              <div class="cmg-timeline-container" v-loading="timelineLoading">
                <div 
                  v-if="timelineData.length > 0" 
                  class="cmg-timeline"
                  ref="timelineRef"
                >
                  <div 
                    class="cmg-timeline-track"
                    @mousedown="onTimelineMouseDown"
                    @mousemove="onTimelineMouseMove"
                    @mouseup="onTimelineMouseUp"
                    @mouseleave="onTimelineMouseLeave"
                  >
                    <div 
                      v-for="(segment, index) in timelineData" 
                      :key="index"
                      class="cmg-timeline-segment"
                      :style="getTimelineSegmentStyle(segment)"
                      :title="formatTimelineSegment(segment)"
                    ></div>
                    <div 
                      v-if="selectedTimeRange.start && selectedTimeRange.end"
                      class="cmg-timeline-selection"
                      :style="getTimelineSelectionStyle()"
                    ></div>
                  </div>
                  <div class="cmg-timeline-labels">
                    <span>{{ formatDateTime(timelineStart) }}</span>
                    <span>{{ formatDateTime(timelineEnd) }}</span>
                  </div>
                </div>
                <div v-else class="cmg-timeline-empty">
                  <el-empty description="暂无数据，请先查询数据" :image-size="60" />
                </div>
              </div>
            </div>
            
            <!-- 推荐时间段 -->
            <div v-if="recommendedSegments.length > 0" class="cmg-recommended-segments">
              <label class="cmg-recommended-label">推荐时间段：</label>
              <el-space wrap>
                <el-tag
                  v-for="(seg, i) in recommendedSegments"
                  :key="i"
                  type="info"
                  effect="plain"
                  class="cmg-segment-tag"
                  @click="pickSegment(seg)"
                >
                  <el-icon><Clock /></el-icon>
                  {{ formatSegment(seg) }}
                </el-tag>
              </el-space>
            </div>
          </div>
        </div>
      </SectionCard>

      <!-- MSFG 详情弹窗（替代跳转） -->
      <el-dialog v-model="msfgDetailDialogVisible" title="MSFG 结果详情" width="70%" :close-on-click-modal="false">
        <div v-if="selectedMsfg">
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="时间">{{ formatDateTime(selectedMsfg.timestamp || selectedMsfg.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="CMG">{{ selectedMsfg.cmg_id || currentCmg?.cmg_id }}</el-descriptions-item>
            <el-descriptions-item label="配置">{{ selectedMsfg.msfg_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="健康分">
              {{ getMsfgHealthScore(selectedMsfg).toFixed(3) }}
            </el-descriptions-item>
          </el-descriptions>

          <h4 style="margin-top:12px;">测试点分数</h4>
          <div style="margin-bottom: 8px; font-size: 12px; color: #666;">
            <el-icon><InfoFilled /></el-icon>
            <span style="margin-left: 4px;">分数越高表示异常程度越严重（0=正常，1=严重异常）</span>
          </div>
          <el-table :data="msfgKv(selectedMsfg.test_results)" size="small" border>
            <el-table-column prop="k" label="测试点" width="240" />
            <el-table-column prop="v" label="分数">
              <template #default="s">
                <el-tag :type="getTestScoreTag(Number(s.row.v||0))" size="small">
                  {{ Number(s.row.v||0).toFixed(3) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <h4 style="margin-top:12px;">故障分数</h4>
          <div style="margin-bottom: 8px; font-size: 12px; color: #666;">
            <el-icon><InfoFilled /></el-icon>
            <span style="margin-left: 4px;">分数越高表示故障概率越大（0=无故障，1=确定故障）</span>
          </div>
          <el-table :data="msfgKv(selectedMsfg.fault_results)" size="small" border>
            <el-table-column prop="k" label="故障" width="240" />
            <el-table-column prop="v" label="分数">
              <template #default="s">
                <el-tag :type="getFaultScoreTag(Number(s.row.v||0))" size="small">
                  {{ Number(s.row.v||0).toFixed(3) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <h4 style="margin-top:12px;">部件健康分析详情</h4>
          <div v-if="selectedMsfg.component_results && Object.keys(selectedMsfg.component_results).length > 0">
            <el-table :data="msfgKvComponent(selectedMsfg.component_results)" size="small" border>
              <el-table-column prop="component" label="部件" width="160" />
              <el-table-column prop="health_score" label="健康分数" width="120">
                <template #default="s"><el-tag :type="getHealthTag(s.row.health_score)">{{ Number(s.row.health_score||1).toFixed(3) }}</el-tag></template>
              </el-table-column>
            </el-table>
          </div>
          <div v-else>
            <el-empty description="暂无部件分析数据" />
          </div>

          
        </div>
        <template #footer>
          <el-button @click="msfgDetailDialogVisible = false">关闭</el-button>
        </template>
      </el-dialog>
    <!-- 参数选择卡片 -->
    <SectionCard 
      title="遥测参数选择"
      icon="Menu"
      size="small"
      class="cmg-metrics-card"
    >
      <template #actions>
        <el-button text size="small" @click="selectAllMetrics" :disabled="availableMetrics.length === 0">
          <el-icon><Select /></el-icon>
          全选
        </el-button>
        <el-button text size="small" @click="clearMetrics" :disabled="selectedMetrics.length === 0">
          <el-icon><Close /></el-icon>
          清空
        </el-button>
      </template>

      
      <div class="cmg-metrics-content">
        <el-select 
          v-model="selectedMetrics" 
          multiple 
          filterable 
          collapse-tags 
          collapse-tags-tooltip
          placeholder="选择参数（可多选）" 
          :style="{ width: '100%' }" 
          :disabled="availableMetrics.length === 0"
          :loading="loading"
         :max-collapse-tags="3"
        >
          <el-option 
            v-for="m in availableMetrics" 
            :key="m" 
            :label="m" 
            :value="m" 
          >
            <span class="cmg-metric-option">
              <el-icon><TrendCharts /></el-icon>
              {{ m }}
            </span>
          </el-option>
        </el-select>
        
        <div class="cmg-metrics-hint">
          <el-icon><InfoFilled /></el-icon>
          <span>未选择参数时将展示全部可用遥测量（当前 {{ availableMetrics.length }} 个）</span>
        </div>
      </div>
    </SectionCard>

    <!-- 图表展示区域 -->
    <SectionCard 
      title="遥测数据趋势图"
      icon="TrendCharts"
      :loading="loading"
      :is-empty="metricsToPlot.length === 0"
      empty-title="暂无数据"
      empty-description="请选择 CMG 并查询数据后查看图表"
      :no-padding="true"
      class="cmg-charts-card"
    >
      <template #actions>
        <div class="cmg-chart-actions">
          <el-button-group size="small">
            <el-button @click="exportCharts" :disabled="metricsToPlot.length === 0">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <el-button @click="toggleFullscreen">
              <el-icon><FullScreen /></el-icon>
              全屏
            </el-button>
          </el-button-group>
          
          <el-divider direction="vertical" />
          
          <el-switch
            v-model="chartSyncZoom"
            active-text="同步缩放"
            size="small"
          />
          <el-divider direction="vertical" />
          <el-button type="primary" size="small" @click="compareDialogVisible = true">对比分析</el-button>
        </div>
      </template>
      
      <div class="cmg-charts-container">
        <div 
          v-for="m in metricsToPlot" 
          :key="m" 
          class="cmg-chart-item"
        >
          <div class="cmg-chart-header">
            <h4 class="cmg-chart-title">
              <el-icon><TrendCharts /></el-icon>
              {{ m }}
            </h4>
            <div class="cmg-chart-controls">
              <el-button text size="small" @click="resetChartZoom(m)">
                <el-icon><Refresh /></el-icon>
                重置
              </el-button>
            </div>
          </div>
          <div class="cmg-chart-wrapper">
            <div class="cmg-chart-box" :ref="el => setChartRef(m, el)"></div>
            <div v-if="live" class="cmg-chart-live-indicator">
              <div class="cmg-realtime-dot"></div>
              <span>实时更新</span>
            </div>
          </div>
        </div>
      </div>
    </SectionCard>

    <el-dialog 
        v-model="compareDialogVisible" 
        title="对比分析" 
        width="90%" 
        @opened="onCompareDialogOpen" 
        @close="onCompareDialogClose"
      >
        <div class="cmg-compare-controls">
          <!-- 第一行：对比模式选择 -->
          <div class="cmg-compare-row">
            <div class="cmg-compare-label">对比模式：</div>
            <el-radio-group v-model="compareMode" size="small">
              <el-radio-button label="multiCmg">多CMG同一参数</el-radio-button>
              <el-radio-button label="multiMetric">同一CMG多参数</el-radio-button>
            </el-radio-group>
          </div>
          
          <!-- 第二行：数据选择 -->
          <div class="cmg-compare-row">
            <template v-if="compareMode === 'multiCmg'">
              <div class="cmg-compare-item">
                <div class="cmg-compare-label">选择CMG：</div>
                <el-select v-model="compareSelectedCmgs" multiple filterable collapse-tags :max-collapse-tags="3" :style="{ minWidth: '260px' }" placeholder="选择多个 CMG">
                  <el-option v-for="c in cmgList" :key="c.cmg_id" :label="c.name + '(' + c.cmg_id + ')'" :value="c.cmg_id" />
                </el-select>
              </div>
              <div class="cmg-compare-item">
                <div class="cmg-compare-label">选择参数：</div>
                <el-select v-model="compareSelectedMetric" filterable :style="{ minWidth: '220px' }" placeholder="选择参数">
                  <el-option v-for="m in availableMetrics" :key="m" :label="m" :value="m" />
                </el-select>
              </div>
            </template>
            <template v-else>
              <div class="cmg-compare-item">
                <div class="cmg-compare-label">选择CMG：</div>
                <el-select v-model="query.cmgId" filterable clearable :style="{ minWidth: '260px' }" placeholder="选择 CMG">
                  <el-option v-for="c in cmgList" :key="c.cmg_id" :label="c.name + '(' + c.cmg_id + ')'" :value="c.cmg_id" />
                </el-select>
              </div>
              <div class="cmg-compare-item">
                <div class="cmg-compare-label">选择参数：</div>
                <el-select v-model="compareSelectedMetrics" multiple filterable collapse-tags :max-collapse-tags="3" :style="{ minWidth: '260px' }" placeholder="选择多个参数">
                  <el-option v-for="m in availableMetrics" :key="m" :label="m" :value="m" />
                </el-select>
              </div>
            </template>
          </div>
          
          <!-- 第三行：时间模式选择 -->
          <div class="cmg-compare-row">
            <div class="cmg-compare-label">时间模式：</div>
            <el-radio-group v-model="compareTimeMode" size="small">
              <el-radio-button label="realtime">实时对比</el-radio-button>
              <el-radio-button label="history">历史对比</el-radio-button>
            </el-radio-group>
          </div>
          
          <!-- 第四行：时间配置 -->
          <div class="cmg-compare-row">
            <template v-if="compareTimeMode === 'realtime'">
              <div class="cmg-compare-item">
                <div class="cmg-compare-label">时间窗口：</div>
                <el-select v-model="compareWindowMinutes" :style="{ width: '140px' }" placeholder="窗口">
                  <el-option v-for="m in [1,5,15,30]" :key="m" :label="`近 ${m} 分钟`" :value="m" />
                </el-select>
              </div>
              <div class="cmg-compare-item">
                <el-switch v-model="compareAutoRefresh" active-text="自动刷新" size="small" />
              </div>
            </template>
            <template v-else>
              <div class="cmg-compare-item">
                <div class="cmg-compare-label">时间范围：</div>
                <el-date-picker v-model="compareDates" type="datetimerange" range-separator="-" start-placeholder="开始" end-placeholder="结束" :style="{ minWidth: '320px' }" />
              </div>
              <div class="cmg-compare-item">
                <el-button text size="small" @click="useRecommendedForCompare" :disabled="recommendedSegments.length === 0">用推荐时间段</el-button>
                <el-button text size="small" @click="refreshCompareTimeline" :loading="compareTimelineLoading" title="刷新时间轴">
                  <el-icon><Refresh /></el-icon>
                  刷新时间轴
                </el-button>
              </div>
            </template>
            
            <!-- 对比分析时间轴 -->
            <div v-if="compareTimeMode === 'history'" class="cmg-compare-timeline">
              <div class="cmg-compare-timeline-header">
                <label class="cmg-compare-timeline-label">数据时间轴：</label>
              </div>
              <div class="cmg-compare-timeline-container" v-loading="compareTimelineLoading">
                <div 
                  v-if="compareTimelineData.length > 0" 
                  class="cmg-compare-timeline-track"
                  ref="compareTimelineRef"
                  @mousedown="onCompareTimelineMouseDown"
                  @mousemove="onCompareTimelineMouseMove"
                  @mouseup="onCompareTimelineMouseUp"
                  @mouseleave="onCompareTimelineMouseLeave"
                >
                  <div 
                    v-for="(segment, index) in compareTimelineData" 
                    :key="index"
                    class="cmg-compare-timeline-segment"
                    :style="getCompareTimelineSegmentStyle(segment)"
                    :title="formatTimelineSegment(segment)"
                  ></div>
                  <div 
                    v-if="compareSelectedTimeRange.start && compareSelectedTimeRange.end"
                    class="cmg-compare-timeline-selection"
                    :style="getCompareTimelineSelectionStyle()"
                  ></div>
                </div>
                <div v-else class="cmg-compare-timeline-empty">
                  <el-empty description="暂无数据，请先查询数据" :image-size="60" />
                </div>
              </div>
            </div>
          </div>
          
          <!-- 第五行：操作按钮 -->
          <div class="cmg-compare-row">
            <el-button type="primary" @click="drawCompareChart" :disabled="!canDrawCompare">绘制对比图</el-button>
            <el-button @click="clearCompareChart" :disabled="!compareChartInst">清空图表</el-button>
          </div>
        </div>
        <div class="cmg-compare-chart" ref="compareChartRef"></div>
      </el-dialog>

    <!-- 结果面板区域 -->
    <div class="cmg-results-grid">
      <!-- IMS 异常检测结果 -->
      <SectionCard 
        title="IMS 异常检测"
        icon="Warning"
        size="small"
        :loading="imsLoading"
        :is-empty="imsList.length === 0"
        empty-title="暂无检测结果"
        empty-description="系统尚未检测到异常数据"
        class="cmg-ims-card"
      >
        <template #actions>
          <div class="cmg-ims-actions">
            <el-switch 
              v-model="showImsOnlyAbnormal" 
              size="small" 
              active-text="仅异常" 
              active-color="var(--cmg-aerospace-danger)"
            />
            <el-button size="small" @click="refreshIMS" :loading="imsLoading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>
        
        <div class="cmg-ims-content">
          <el-scrollbar class="cmg-ims-list" max-height="320px">
            <el-timeline>
              <el-timeline-item
                v-for="(item, idx) in imsList"
                :key="idx"
                :timestamp="formatTimestamp(item.timestamp)"
                :type="(item.ims_detection?.is_anomaly || item.is_anomaly) ? 'danger' : 'success'"
                :hollow="false"
                size="normal"
              >
                <div class="cmg-ims-item" @click="openIMSDetail(item)">
                  <div class="cmg-ims-item-header">
                    <el-tag 
                      :type="(item.ims_detection?.is_anomaly || item.is_anomaly) ? 'danger' : 'success'"
                      size="small"
                      class="cmg-ims-score-tag"
                    >
                      {{ formatScore(item.ims_detection?.anomaly_score ?? item.anomaly_score) }}
                    </el-tag>
                    <span class="cmg-ims-model-name">
                      {{ item.ims_detection?.model_name || item.ims_model_name || 'IMS' }}
                    </span>
                    <el-button size="small" type="primary" text>
                      <el-icon><View /></el-icon>
                    </el-button>
                  </div>
                  <div v-if="topParameter(item)" class="cmg-ims-item-param">
                    <el-icon><TrendCharts /></el-icon>
                    {{ topParameter(item) }}
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-scrollbar>
        </div>
      </SectionCard>
      <!-- 规则检测结果 -->
      <SectionCard 
        title="规则检测结果"
        icon="List"
        size="small"
        :loading="ruleLoading"
        :is-empty="displayedRuleFrames.length === 0"
        empty-title="暂无检测结果"
        empty-description="系统尚未检测到规则触发"
        class="cmg-rules-card"
      >
        <template #actions>
          <div class="cmg-rules-actions">
            <el-switch 
              v-model="showRuleOnlyAbnormal" 
              size="small" 
              active-text="仅异常"
              active-color="var(--cmg-aerospace-danger)"
            />
            <el-button size="small" @click="refreshRules" :loading="ruleLoading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>
        
        <div class="cmg-rules-content">
          <el-scrollbar class="cmg-rules-list" max-height="320px">
            <el-timeline>
              <el-timeline-item
                v-for="(frame, idx) in displayedRuleFrames"
                :key="frame.timestamp + '-' + idx"
                :timestamp="formatTimestamp(frame.timestamp)"
                :type="frame.isAbnormal ? 'danger' : 'success'"
                :hollow="false"
                size="normal"
              >
                <div 
                  class="cmg-rules-item" 
                  @click="openRuleFrameDetail(frame)"
                >
                  <div class="cmg-rules-item-header">
                    <el-tag :type="frame.isAbnormal ? 'danger' : 'success'" size="small">
                      {{ frame.isAbnormal ? '异常帧' : '正常帧' }}
                    </el-tag>
                    <span class="cmg-rules-item-count">
                      <el-icon><Document /></el-icon>
                      {{ frame.items.length }} 条规则
                    </span>
                    <el-button size="small" type="primary" text>
                      <el-icon><View /></el-icon>
                    </el-button>
                  </div>
                  <div v-if="frame.isAbnormal && frame.items.some(item => item.detection_details?.component_health_score < 1.0)" class="cmg-rules-item-health">
                    <el-icon><Warning /></el-icon>
                    <span>检测到部件健康度异常</span>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-scrollbar>

        </div>
      </SectionCard>
      <!-- 多信号流图结果 -->
      <SectionCard 
        title="多信号流图分析"
        icon="Share"
        size="small"
        :is-empty="!msfgResults.length"
        empty-title="暂无分析结果"
        empty-description="当系统检测到异常时，会自动生成多信号流图分析结果"
        class="cmg-msfg-card"
      >
        <template #actions v-if="msfgResults.length">
          <el-button @click="loadMsfgResults(true)" size="small" :loading="msfgLoading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </template>

        <div class="cmg-ims-content" v-if="msfgResults.length">
          <el-scrollbar class="cmg-ims-list" max-height="420px">
            <el-timeline>
              <el-timeline-item
                v-for="(res, i) in msfgResults"
                :key="res.id || ((res.timestamp||res.created_at) + '-' + i)"
                :timestamp="formatDateTime(res.timestamp || res.created_at)"
                :type="(Number(res.system_results?.average_fault_score||0) > 0.5) ? 'danger' : (Number(res.system_results?.average_fault_score||0) > 0.2 ? 'warning' : 'success')"
                :hollow="false"
                size="normal"
              >
                <div class="cmg-ims-item">
                  <div class="cmg-ims-item-header">
                    <el-tag 
                      :type="getHealthTag(getMsfgHealthScore(res))"
                      size="small"
                      class="cmg-ims-score-tag"
                    >
                      {{ getMsfgHealthScore(res).toFixed(3) }}
                    </el-tag>
                    <span class="cmg-ims-model-name">
                      {{ topMsfgComponent(res) || '未检测到高风险部件' }}
                    </span>
                    <el-button size="small" type="primary" text @click="openMsfgDetail(res)">
                      <el-icon><View /></el-icon>
                    </el-button>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-scrollbar>
        </div>
      </SectionCard>
      
      <!-- 寿命预测 -->
      <SectionCard 
        title="寿命预测"
        icon="Timer"
        size="small"
        :loading="lifetimeLoading"
        class="cmg-lifetime-card"
      >
        <template #actions>
          <div class="cmg-lifetime-actions">
            <el-button 
              size="small" 
              type="primary" 
              @click="predictLifetime" 
              :loading="lifetimeLoading"
              :disabled="!hasCmgSelected || !hasTimelineSelection || !isLifetimeParamsValid"
            >
              <el-icon><TrendCharts /></el-icon>
              预测寿命
            </el-button>
            <el-button size="small" @click="clearLifetimeResult" :disabled="!lifetimeResult">
              <el-icon><Refresh /></el-icon>
              清除
            </el-button>
          </div>
        </template>
        
        <!-- 简化的参数设置 -->
        <div class="cmg-lifetime-params">
          <div class="cmg-lifetime-param-row">
            <el-form :inline="true" :model="lifetimeParams" size="small">
              <el-form-item label="设计寿命">
                <el-input-number 
                  v-model="lifetimeParams.designLife" 
                  :min="1" 
                  :max="50" 
                  :precision="1"
                  placeholder="年"
                  style="width: 120px;"
                />
              </el-form-item>
              <el-form-item label="启用时间">
                <el-date-picker 
                  v-model="lifetimeParams.startTime"
                  type="datetime"
                  placeholder="选择启用时间"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  style="width: 180px;"
                />
              </el-form-item>
            </el-form>
          </div>
          <div class="cmg-lifetime-info" v-if="hasTimelineSelection">
            <el-text size="small" type="info">
              <el-icon><Clock /></el-icon>
              数据时间段: {{ formatDateTime(selectedTimeRange.start) }} ~ {{ formatDateTime(selectedTimeRange.end) }}
            </el-text>
          </div>
        </div>

        <div v-if="lifetimeResult" class="cmg-lifetime-content">
          <div class="cmg-lifetime-result-simple">
            <div class="cmg-lifetime-rul-main">
              <span class="cmg-lifetime-rul-number">{{ lifetimeResult.rul_value }}</span>
              <span class="cmg-lifetime-rul-unit">年</span>
            </div>
            <div class="cmg-lifetime-rul-label">预计剩余使用寿命</div>
            <div class="cmg-lifetime-prediction-time">
              预测时间: {{ formatTime(lifetimeResult.prediction_time) }}
            </div>
          </div>
        </div>
        
        <div v-else class="cmg-lifetime-empty">
          <div class="cmg-lifetime-hint">
            <el-icon><InfoFilled /></el-icon>
            <span>请设置预测参数并选择时间轴数据段，然后点击预测按钮</span>
          </div>
          <div class="cmg-lifetime-tips" style="margin-top: 10px; font-size: 12px; color: #666;">
            <p>💡 使用说明：</p>
            <p>• 通过上方时间轴选择分析数据的时间段</p>
            <p>• 设置CMG的设计寿命和启用时间</p>
            <p>• 确保选择的时间段内有足够的遥测数据</p>
          </div>
        </div>
      </SectionCard>
    </div>



    <!-- IMS异常详情对话框 -->
    <el-dialog 
      v-model="anomalyDialogVisible" 
      title="IMS异常检测详情" 
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedAnomaly">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="检测时间">
            {{ new Date(selectedAnomaly.timestamp).toLocaleString() }}
          </el-descriptions-item>
          <el-descriptions-item label="参数名称">
            {{ selectedAnomaly.metric }}
          </el-descriptions-item>
          <el-descriptions-item label="参数值">
            {{ selectedAnomaly.value }}
          </el-descriptions-item>
          <el-descriptions-item label="异常分数">
            <el-tag :type="selectedAnomaly.anomaly_score > 0.8 ? 'danger' : 'warning'">
              {{ selectedAnomaly.anomaly_score?.toFixed(3) || 'N/A' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="检测模型">
            {{ selectedAnomaly.ims_model_name || 'Unknown' }}
          </el-descriptions-item>
          <el-descriptions-item label="异常状态">
            <el-tag :type="selectedAnomaly.is_anomaly ? 'danger' : 'success'">
              {{ selectedAnomaly.is_anomaly ? '异常' : '正常' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 参数异常分数详情 -->
        <div :style="{ marginTop: 'var(--cmg-space-5)' }" v-if="selectedAnomaly.parameter_scores">
          <h4>各参数异常分数</h4>
          <el-table :data="parameterScoresList" size="small" max-height="200">
            <el-table-column prop="parameter" label="参数名称" />
            <el-table-column prop="score" label="异常分数">
              <template #default="scope">
                <el-progress 
                  :percentage="Math.min(scope.row.score * 100, 100)" 
                  :color="scope.row.score > 0.5 ? 'var(--cmg-aerospace-danger)' : 'var(--cmg-aerospace-success)'"
                  :show-text="false"
                  :style="{ width: '80px' }"
                />
                <span :style="{ marginLeft: 'var(--cmg-space-2)' }">{{ scope.row.score.toFixed(3) }}</span>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 检测详细信息 -->
        <div :style="{ marginTop: 'var(--cmg-space-5)' }" v-if="selectedAnomaly.detection_details">
          <h4>检测详细信息</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="算法类型">
              {{ selectedAnomaly.detection_details.detectType || 'IMS' }}
            </el-descriptions-item>
            <el-descriptions-item label="检测结果" v-if="selectedAnomaly.detection_details.result">
              <pre :style="{ fontSize: 'var(--cmg-text-xs)', maxHeight: '150px', overflowY: 'auto' }">{{ JSON.stringify(selectedAnomaly.detection_details.result, null, 2) }}</pre>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="anomalyDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 规则帧详情对话框 -->
    <el-dialog 
      v-model="ruleFrameDialogVisible" 
      title="规则检测帧详情" 
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedRuleFrameForDialog">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="检测时间">
            {{ new Date(selectedRuleFrameForDialog.timestamp).toLocaleString() }}
          </el-descriptions-item>
          <el-descriptions-item label="帧状态">
            <el-tag :type="selectedRuleFrameForDialog.isAbnormal ? 'danger' : 'success'">
              {{ selectedRuleFrameForDialog.isAbnormal ? '异常帧' : '正常帧' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="规则数量">
            {{ selectedRuleFrameForDialog.items.length }} 条
          </el-descriptions-item>
          <el-descriptions-item label="触发规则">
            {{ selectedRuleFrameForDialog.items.filter(item => item.is_triggered).length }} 条
          </el-descriptions-item>
        </el-descriptions>

        <!-- 规则详细列表 -->
        <div :style="{ marginTop: 'var(--cmg-space-5)' }">
          <h4>所有规则检测详情</h4>
          <el-table 
            :data="selectedRuleFrameForDialog.items.sort((a, b) => {
              // 触发的规则排在前面
              if (a.is_triggered && !b.is_triggered) return -1;
              if (!a.is_triggered && b.is_triggered) return 1;
                          // 同状态按检测分数降序排列
            return (b.confidence_score || 0) - (a.confidence_score || 0);
            })" 
            size="small" 
            max-height="400"
              :row-key="(row, i) => (row.rule_definition?.rule_id || row.rule_id || row.rule_definition?.rule_id || i)"
            class="cmg-rules-frame-table"
          >
            <el-table-column label="规则ID" min-width="120">
              <template #default="scope">
                <span class="cmg-rule-name">
                  {{ scope.row.rule_definition?.rule_id || scope.row.rule_id || scope.row.rule_definition?.rule_id || '未知规则' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="故障名称" min-width="120">
              <template #default="scope">
                {{ scope.row.fault_name || scope.row.fault_definition?.fault_name || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="部件" width="100">
              <template #default="scope">
                {{ scope.row.component || scope.row.fault_definition?.component || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.is_triggered ? 'danger' : 'success'" size="small">
                  {{ scope.row.is_triggered ? '触发' : '正常' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="检测分数" width="100">
              <template #default="scope">
                <span :style="{ color: scope.row.is_triggered ? 'var(--el-color-danger)' : 'var(--el-color-success)' }">
                  {{ (scope.row.confidence_score || 0).toFixed(3) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="60">
              <template #default="scope">
                <el-button size="small" text type="primary" @click="openRuleDetail(scope.row)">
                  <el-icon><View /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 健康度统计 -->
        <div :style="{ marginTop: 'var(--cmg-space-5)' }" v-if="selectedRuleFrameForDialog.isAbnormal">
          <h4>异常部件健康度统计</h4>
          <div class="cmg-health-summary">
            <el-row :gutter="16">
              <el-col :span="6" v-for="(score, component) in getComponentHealthSummary(selectedRuleFrameForDialog.items)" :key="component">
                <el-card size="small" class="cmg-health-card-mini">
                  <div class="cmg-health-item">
                    <div class="cmg-health-component">{{ component || '未知部件' }}</div>
                    <el-tag 
                      type="danger"
                      size="small"
                      class="cmg-health-score-tag"
                    >
                      {{ formatScore(score) }}
                    </el-tag>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="ruleFrameDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 规则检测详情对话框 -->
    <el-dialog v-model="ruleDialogVisible" title="规则检测详情" width="600px">
      <div v-if="selectedRule">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="检测时间">
            {{ new Date(selectedRule.created_at).toLocaleString() }}
          </el-descriptions-item>
          <el-descriptions-item label="规则名称">
            {{ selectedRule.rule_definition?.rule_id || selectedRule.rule_id || '未知规则' }}
          </el-descriptions-item>
          <el-descriptions-item label="是否触发">
            <el-tag :type="selectedRule.is_triggered ? 'danger' : 'success'">
              {{ selectedRule.is_triggered ? '触发' : '正常' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="检测分数">
            {{ selectedRule.confidence_score?.toFixed(3) || '0.000' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 规则表达式 -->
        <div :style="{ marginTop: 'var(--cmg-space-5)' }" v-if="selectedRule.rule_definition?.rule_expression">
          <h4>规则表达式</h4>
          <p><code>{{ selectedRule.rule_definition.rule_expression }}</code></p>
        </div>

        <!-- 故障信息 -->
        <div :style="{ marginTop: 'var(--cmg-space-5)' }" v-if="selectedRule.is_triggered && selectedRule.fault_definition">
          <h4>故障信息</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="故障名称">
              {{ selectedRule.fault_definition.fault_name }}
            </el-descriptions-item>
            <el-descriptions-item label="故障等级">
              <el-tag :type="getFaultLevelType(selectedRule.fault_definition.fault_level)">
                等级 {{ selectedRule.fault_definition.fault_level || 1 }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="涉及部件">
              {{ selectedRule.fault_definition.component || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 部件健康度信息 -->
        <div :style="{ marginTop: 'var(--cmg-space-5)' }" v-if="selectedRule.detection_details?.component_health_score !== undefined">
          <h4>部件健康度</h4>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="健康度分数">
              <el-tag 
                :type="getHealthScoreType(selectedRule.detection_details.component_health_score)"
                size="large"
                class="cmg-health-score-tag"
              >
                {{ formatScore(selectedRule.detection_details.component_health_score) }}
              </el-tag>
              <span :style="{ marginLeft: 'var(--cmg-space-2)', fontSize: 'var(--cmg-text-sm)', color: 'var(--cmg-text-secondary)' }">
                (1.0 = 完全健康, 0.0 = 完全异常)
              </span>
            </el-descriptions-item>
            <el-descriptions-item label="涉及部件">
              {{ selectedRule.detection_details.component || selectedRule.fault_definition?.component || '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 检测详细信息 -->
        <div :style="{ marginTop: 'var(--cmg-space-5)' }" v-if="selectedRule.detection_details">
          <h4>检测详细信息</h4>
          <el-table :data="getRuleDetailsArray(selectedRule.detection_details)" size="small" max-height="200">
            <el-table-column prop="key" label="属性" width="120" />
            <el-table-column prop="value" label="值" />
          </el-table>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="ruleDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, nextTick, watch, onActivated, onDeactivated } from 'vue';
import { ElMessage } from 'element-plus';
import { 
  Connection, Search, VideoPause, VideoPlay, RefreshLeft, Clock, 
  Menu, Select, Close, TrendCharts, InfoFilled, Download, FullScreen,
  Refresh, View, Document, ArrowRight, ArrowDown, Plus, Monitor, Filter, Warning, Share, SuccessFilled, Timer, Setting
} from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import api from '../api';
import websocketService from '../services/websocket';

// 为 keep-alive 添加组件名称
defineOptions({
  name: 'CmgDetail'
});

// 模式：history | realtime
const mode = ref('history');

const cmgList = ref([]);
const query = ref({ cmgId: null, dates: [] });
const recommendedSegments = ref([]);

// 时间轴相关
const timelineData = ref([]);
const timelineLoading = ref(false);
const timelineRef = ref(null);
const timelineStart = ref(null);
const timelineEnd = ref(null);
const selectedTimeRange = ref({ start: null, end: null });
const isTimelineDragging = ref(false);
const dragStartX = ref(0);
const dragStartTime = ref(null);
const raw = ref([]); // 原始接口数据
const availableMetrics = ref([]);
const imsAnomalies = ref([]); // IMS异常检测结果
  const showImsOnlyAbnormal = ref(false);
const selectedMetrics = ref([]);
const live = ref(false);
const isActive = ref(true);
const loading = ref(false);
const imsLoading = ref(false);
const ruleLoading = ref(false);
const chartSyncZoom = ref(true);
let wsFlushTimer = null;
let wsBuffered = [];
let renderScheduled = false;
let liveTimer = null;
let lastTsMs = null; // 记录最新时间戳（毫秒）
let detectionPollTimer = null; // IMS/规则结果轮询定时器
let liveStartMs = null; // 实时模式开始时间戳（毫秒）

// 对比分析状态
const compareMode = ref('multiCmg'); // multiCmg | multiMetric
const compareSelectedCmgs = ref([]);
const compareSelectedMetric = ref(null);
const compareSelectedMetrics = ref([]);
const compareChartRef = ref(null);
let compareChartInst = null;
const compareDialogVisible = ref(false);
const compareAutoRefresh = ref(true);
const compareTimeMode = ref('realtime'); // realtime | history
const compareWindowMinutes = ref(5);
const compareDates = ref([]);
let compareTimer = null;

// 对比分析时间轴相关
const compareTimelineData = ref([]);
const compareTimelineLoading = ref(false);
const compareTimelineRef = ref(null);
const compareTimelineStart = ref(null);
const compareTimelineEnd = ref(null);
const compareSelectedTimeRange = ref({ start: null, end: null });
const isCompareTimelineDragging = ref(false);
const compareDragStartX = ref(0);
const compareDragStartTime = ref(null);

// MSFG相关状态
const msfgResults = ref([]);
const msfgLoading = ref(false);
const msfgTrendChart = ref(null);
const msfgDetailDialogVisible = ref(false);
const selectedMsfg = ref(null);

// 寿命预测相关状态
const lifetimeResult = ref(null);
const lifetimeLoading = ref(false);
const lifetimeParams = ref({
  designLife: 10, // 设计寿命 (年)
  startTime: null // 开始使用时间 (YYYY/MM/DD HH:mm:ss)
});


const canDrawCompare = computed(() => {
  if (compareMode.value === 'multiCmg') {
    return Array.isArray(compareSelectedCmgs.value) && compareSelectedCmgs.value.length >= 2 && !!compareSelectedMetric.value;
  }
  return !!query.value.cmgId && Array.isArray(compareSelectedMetrics.value) && compareSelectedMetrics.value.length >= 2;
});

// MSFG计算属性
const latestMsfgResult = computed(() => 
  msfgResults.value.length > 0 ? msfgResults.value[0] : null
);

// WebSocket连接状态
const wsConnected = ref(false);
const wsConnecting = ref(false);
const wsError = ref('');
const wsUrl = ref('');
const wsReconnectAttempts = ref(0);
const lastUpdateTime = ref(null);
function formatDateTime(val) {
  if (!val) return '';
  try {
    const d = new Date(val);
    return d.toLocaleString();
  } catch(e) { return String(val); }
}

// 统一的请求取消与状态守卫
const abortControllers = new Set();
function abortAllPending() {
  abortControllers.forEach(c => { try { c.abort(); } catch(e) {} });
  abortControllers.clear();
}
async function apiGet(url, config = {}) {
  const controller = new AbortController();
  abortControllers.add(controller);
  try {
    const cfg = { ...(config || {}), signal: controller.signal };
    return await api.get(url, cfg);
  } finally {
    abortControllers.delete(controller);
  }
}

// 是否已选择 CMG
const hasCmgSelected = computed(() => !!query.value.cmgId);
const currentCmg = computed(() => cmgList.value.find(c => c.cmg_id === query.value.cmgId) || null);
const currentCmgLabel = computed(() => currentCmg.value ? `${currentCmg.value.name} (${currentCmg.value.cmg_id})` : '未选择');

// 寿命预测相关计算属性
const hasTimeRange = computed(() => query.value.dates && query.value.dates.length === 2);
const hasTimelineSelection = computed(() => selectedTimeRange.value.start && selectedTimeRange.value.end);
const isLifetimeParamsValid = computed(() => {
  return lifetimeParams.value.designLife > 0 && lifetimeParams.value.startTime !== null;
});

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

// IMS异常详情弹窗相关
const anomalyDialogVisible = ref(false);
const selectedAnomaly = ref(null);

// 规则检测相关
const ruleResults = ref([]);
  const showRuleOnlyAbnormal = ref(false);
  const ruleFrames = computed(() => {
    // 将规则结果按时间戳（精确到毫秒）分组
    const groups = new Map();
    for (const r of ruleResults.value) {
      const ts = new Date(r.timestamp || r.created_at).getTime();
      if (!groups.has(ts)) groups.set(ts, []);
      groups.get(ts).push(r);
    }
    const frames = Array.from(groups.entries()).map(([ts, items]) => {
      const isAbnormal = items.some(it => it.is_triggered);
      return { timestamp: new Date(ts).toISOString(), items, isAbnormal };
    }).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    return frames;
  });
  const displayedRuleFrames = computed(() => showRuleOnlyAbnormal.value ? ruleFrames.value.filter(f => f.isAbnormal) : ruleFrames.value);
const selectedRule = ref({});
const ruleDialogVisible = ref(false);
const ruleFrameDialogVisible = ref(false);
const selectedRuleFrameForDialog = ref(null);

// IMS 列表展示（支持仅异常筛选，且正常帧也保留记录）
const imsList = computed(() => {
  const list = Array.isArray(imsAnomalies.value) ? imsAnomalies.value : [];
  return showImsOnlyAbnormal.value ? list.filter(x => (x.ims_detection?.is_anomaly || x.is_anomaly)) : list;
});

const charts = new Map(); // metric -> echarts instance
function setChartRef(metric, el) {
  // 处理卸载：当元素被移除时 el 为 null
  if (!el) {
    const inst = charts.get(metric);
    if (inst) { 
      try { inst.dispose(); } catch(e) {} 
      charts.delete(metric); 
    }
    return;
  }
  
  // 检查是否已有该metric的图表实例
  const existing = charts.get(metric);
  if (existing) {
    try {
      const existingDom = existing.getDom();
      // 如果DOM元素相同，不需要重新创建
      if (existingDom === el) {
        return;
      }
    } catch(e) {
      // 实例可能已损坏，清理
      charts.delete(metric);
    }
  }
  
  // 延迟处理，确保DOM完全渲染
  nextTick(() => {
    if (!el.isConnected) return; // DOM已被移除
    
    // 清理该DOM上可能存在的旧实例
    const domInst = echarts.getInstanceByDom(el);
    if (domInst) {
      try { domInst.dispose(); } catch(e) {}
    }
    
    // 确保元素有尺寸
    if (el.offsetWidth === 0 || el.offsetHeight === 0) {
      const retryCount = (setChartRef.retryCount || {})[metric] || 0;
      if (retryCount < 10) {
        setChartRef.retryCount = setChartRef.retryCount || {};
        setChartRef.retryCount[metric] = retryCount + 1;
        setTimeout(() => setChartRef(metric, el), 100);
      }
      return;
    }
    
    // 重置重试计数
    if (setChartRef.retryCount) {
      delete setChartRef.retryCount[metric];
    }
    
    // 创建新的图表实例
    try {
      const chart = echarts.init(el, 'light', { 
        renderer: 'canvas',
        useDirtyRect: true // 启用脏矩形优化
      });
      charts.set(metric, chart);
      
      // 立即渲染，不延迟
      if (raw.value.length > 0) {
        renderChart(metric);
      }
    } catch (e) {
      console.error(`Failed to create chart for ${metric}:`, e);
    }
  });
}

const metricsToPlot = computed(() => {
  if (selectedMetrics.value.length > 0) return selectedMetrics.value;
  return availableMetrics.value;
});

// 计算参数异常分数列表
const parameterScoresList = computed(() => {
  if (!selectedAnomaly.value?.parameter_scores) return [];
  return Object.entries(selectedAnomaly.value.parameter_scores).map(([parameter, score]) => ({
    parameter,
    score: parseFloat(score) || 0
  }));
});

// 获取故障等级类型
function getFaultLevelType(level) {
  if (level >= 4) return 'danger';
  if (level >= 3) return 'warning';
  if (level >= 2) return 'info';
  return 'success';
}

// 获取健康度分数类型
function getHealthScoreType(score) {
  const healthScore = Number(score || 0);
  // 规则检测逻辑：分数越低越健康（与MSFG相反）
  if (healthScore < 0.5) return 'success';    // 健康
  if (healthScore < 0.9) return 'warning';    // 预警
  return 'danger';                            // 故障
}

// 获取规则详情数组
function getRuleDetailsArray(details) {
  if (!details || typeof details !== 'object') return [];
  return Object.entries(details).map(([key, value]) => ({
    key,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value)
  }));
}

// 时间格式化
function formatTimestamp(timestamp) {
  return new Date(timestamp).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

// 分数格式化
function formatScore(score) {
  if (score === null || score === undefined) return '0.000';
  return Number(score).toFixed(3);
}

// 格式化时间段
function formatSegment(seg) {
  const start = new Date(seg.start);
  const end = new Date(seg.end);
  const duration = Math.round((end - start) / 60000); // 分钟
  return `${start.toLocaleDateString()} (${duration}分钟)`;
}

// 计算主要异常参数
function topParameter(anomaly) {
  if (!anomaly?.ims_detection?.parameter_scores) return null;
  const scores = anomaly.ims_detection.parameter_scores;
  const entries = Object.entries(scores);
  if (entries.length === 0) return null;
  const sorted = entries.sort((a, b) => parseFloat(b[1]) - parseFloat(a[1]));
  return sorted[0][0];
}

// 参数选择操作
function selectAllMetrics() {
  selectedMetrics.value = [...availableMetrics.value];
}

function clearMetrics() {
  selectedMetrics.value = [];
}

// 重置筛选条件
function resetFilters() {
  query.value.dates = [];
  selectedMetrics.value = [];
  live.value = false;
  stopLive();
}

// 图表操作
function exportCharts() {
  try {
    const instances = Array.from(charts.values());
    if (instances.length === 0) return;
    instances.forEach((inst, idx) => {
      const url = inst.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#ffffff' });
      const a = document.createElement('a');
      a.href = url;
      a.download = `cmg_chart_${idx + 1}.png`;
      a.click();
    });
  } catch (e) { console.error('导出失败', e); }
}

function toggleFullscreen() {
  try {
    const container = document.querySelector('.cmg-charts-card');
    if (!container) return;
    if (!document.fullscreenElement) {
      container.requestFullscreen && container.requestFullscreen();
    } else {
      document.exitFullscreen && document.exitFullscreen();
    }
  } catch (e) { console.error('全屏失败', e); }
}

function resetChartZoom(metric) {
  const chart = charts.get(metric);
  if (chart) {
    chart.dispatchAction({ type: 'dataZoom', start: 0, end: 100 });
  }
}

// 对比分析绘图
async function drawCompareChart() {
  if (!compareChartInst || !canDrawCompare.value) return;
  if (compareTimer) { clearInterval(compareTimer); compareTimer = null; }

  const buildSeriesForMultiCmg = async () => {
    const metric = compareSelectedMetric.value;
    const cmgIds = compareSelectedCmgs.value;
    const now = new Date();
    const startIso = compareTimeMode.value === 'realtime' 
      ? new Date(Date.now() - compareWindowMinutes.value * 60 * 1000).toISOString() 
      : (compareDates?.value?.[0] ? new Date(compareDates.value[0]).toISOString() : (query.value.dates?.[0] ? new Date(query.value.dates[0]).toISOString() : undefined));
    const endIso = compareTimeMode.value === 'realtime' 
      ? now.toISOString() 
      : (compareDates?.value?.[1] ? new Date(compareDates.value[1]).toISOString() : (query.value.dates?.[1] ? new Date(query.value.dates[1]).toISOString() : undefined));
    const series = [];
    const legends = [];
    for (const id of cmgIds) {
      const params = { cmg_id: id, limit: 2000 };
      if (startIso && endIso) { params.start = startIso; params.end = endIso; }
      const res = await apiGet('/data/data/', { params });
      const rows = buildRows(extractDataArray(res));
      const data = rows.map(r => [new Date(r.timestamp).getTime(), Number(r[metric])]).filter(d => Number.isFinite(d[1]));
      legends.push(`${id}-${metric}`);
      series.push({ name: `${id}-${metric}`, type: 'line', symbol: 'none', data });
    }
    return { series, legends };
  };

  const buildSeriesForMultiMetric = async () => {
    const cmgId = query.value.cmgId;
    const metrics = compareSelectedMetrics.value;
    const now = new Date();
    const startIso = compareTimeMode.value === 'realtime' 
      ? new Date(Date.now() - compareWindowMinutes.value * 60 * 1000).toISOString() 
      : (compareDates?.value?.[0] ? new Date(compareDates.value[0]).toISOString() : (query.value.dates?.[0] ? new Date(query.value.dates[0]).toISOString() : undefined));
    const endIso = compareTimeMode.value === 'realtime' 
      ? now.toISOString() 
      : (compareDates?.value?.[1] ? new Date(compareDates.value[1]).toISOString() : (query.value.dates?.[1] ? new Date(query.value.dates[1]).toISOString() : undefined));
    const params = { cmg_id: cmgId, limit: 2000 };
    if (startIso && endIso) { params.start = startIso; params.end = endIso; }
    const res = await apiGet('/data/data/', { params });
    const rows = buildRows(extractDataArray(res));
    const legends = [];
    const series = [];
    const yAxes = [];
    metrics.forEach((m, idx) => {
      const data = rows.map(r => [new Date(r.timestamp).getTime(), Number(r[m])]).filter(d => Number.isFinite(d[1]));
      legends.push(m);
      yAxes.push({ type: 'value', scale: true, splitLine: { lineStyle: { type: 'dashed', opacity: 0.3 } } });
      series.push({ name: m, type: 'line', yAxisIndex: idx, symbol: 'none', data });
    });
    return { series, legends, yAxes };
  };

  const render = async () => {
    try {
      let legends = [], series = [], yAxes = undefined;
      if (compareMode.value === 'multiCmg') {
        const s = await buildSeriesForMultiCmg();
        legends = s.legends; series = s.series; yAxes = [{ type: 'value', scale: true, splitLine: { lineStyle: { type: 'dashed', opacity: 0.3 } } }];
      } else {
        const s = await buildSeriesForMultiMetric();
        legends = s.legends; series = s.series; yAxes = s.yAxes;
      }
      const option = {
        animation: false,
        grid: { left: 60, right: 40, top: 35, bottom: 50 },
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
        legend: { data: legends, top: 5 },
        dataZoom: [ { type: 'inside', xAxisIndex: 0 }, { type: 'slider', xAxisIndex: 0, height: 20, bottom: 5 } ],
        xAxis: { type: 'time', splitLine: { show: false } },
        yAxis: yAxes,
        series
      };
      compareChartInst && compareChartInst.setOption(option, { notMerge: true });
    } catch (e) {
      console.error('Failed to draw compare chart:', e);
    }
  };

  render();
  if (compareTimeMode.value === 'realtime' && compareAutoRefresh.value) {
    compareTimer = setInterval(render, 5000);
  }
}

// 清空对比图表
function clearCompareChart() {
  if (compareChartInst) {
    compareChartInst.clear();
    compareChartInst.setOption({
      grid: { left: 60, right: 40, top: 35, bottom: 50 },
      xAxis: { type: 'time', splitLine: { show: false } },
      yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', opacity: 0.3 } } },
      series: []
    });
  }
  if (compareTimer) {
    clearInterval(compareTimer);
    compareTimer = null;
  }
}

function onCompareDialogOpen() {
  nextTick(() => {
    try {
      if (isActive.value && compareDialogVisible.value && compareChartRef.value && compareChartRef.value.isConnected) {
        compareChartInst = echarts.init(compareChartRef.value, 'light', { renderer: 'canvas', useDirtyRect: true });
        if (canDrawCompare.value) drawCompareChart();
      }
    } catch (e) {}
  });
}

function onCompareDialogClose() {
  if (compareTimer) { clearInterval(compareTimer); compareTimer = null; }
  if (compareChartInst) { try { compareChartInst.dispose(); } catch(e) {} compareChartInst = null; }
}

function useRecommendedForCompare() {
  if (recommendedSegments.value.length > 0) {
    const seg = recommendedSegments.value[0];
    compareDates.value = [new Date(seg.start), new Date(seg.end)];
    compareSelectedTimeRange.value = { start: new Date(seg.start), end: new Date(seg.end) };
  }
}

// 对比分析时间轴功能
async function refreshCompareTimeline() {
  compareTimelineLoading.value = true;
  compareTimelineData.value = [];
  
  try {
    // 获取当前选中CMG的时间轴数据
    const cmgId = compareMode.value === 'multiCmg' ? 
      (compareSelectedCmgs.value.length > 0 ? compareSelectedCmgs.value[0] : null) : 
      query.value.cmgId;
    
    if (!cmgId) {
      ElMessage.warning('请先选择CMG');
      return;
    }
    
    const res = await api.get('/data/data/', { 
      params: { cmg_id: cmgId, limit: 5000000 },
      timeout: 300000 // 5分钟超时
    });
    const rows = extractDataArray(res);
    if (rows.length < 2) return;
    
    const sorted = rows
      .filter(r => r && r.timestamp)
      .slice()
      .sort((a,b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    if (sorted.length < 2) return;

    // 设置时间轴范围
    compareTimelineStart.value = new Date(sorted[0].timestamp);
    compareTimelineEnd.value = new Date(sorted[sorted.length - 1].timestamp);

    // 计算相邻间隔的中位数
    const deltas = [];
    for (let i = 1; i < sorted.length; i++) {
      const prev = new Date(sorted[i-1].timestamp).getTime();
      const cur = new Date(sorted[i].timestamp).getTime();
      const d = cur - prev;
      if (Number.isFinite(d) && d > 0) deltas.push(d);
    }
    deltas.sort((a,b) => a - b);
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
        if (segmentDataCount >= 10) {
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
    
    if (segmentDataCount >= 10) {
      segments.push({ 
        start: new Date(segStartMs).toISOString(), 
        end: new Date(prevMs).toISOString(),
        dataCount: segmentDataCount
      });
    }

    compareTimelineData.value = segments;
    ElMessage.success('对比时间轴已刷新');
    
  } catch (e) {
    console.error('获取对比时间轴数据失败:', e);
    ElMessage.error('获取时间轴数据失败');
  } finally {
    compareTimelineLoading.value = false;
  }
}

// 对比分析时间轴交互功能
function onCompareTimelineMouseDown(event) {
  if (!compareTimelineRef.value || !compareTimelineStart.value || !compareTimelineEnd.value) return;
  
  const rect = compareTimelineRef.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const time = getCompareTimeFromPosition(x);
  
  isCompareTimelineDragging.value = true;
  compareDragStartX.value = x;
  compareDragStartTime.value = time;
  compareSelectedTimeRange.value = { start: time, end: time };
}

function onCompareTimelineMouseMove(event) {
  if (!isCompareTimelineDragging.value || !compareTimelineRef.value) return;
  
  const rect = compareTimelineRef.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const time = getCompareTimeFromPosition(x);
  
  if (time && compareDragStartTime.value) {
    const start = new Date(Math.min(compareDragStartTime.value.getTime(), time.getTime()));
    const end = new Date(Math.max(compareDragStartTime.value.getTime(), time.getTime()));
    compareSelectedTimeRange.value = { start, end };
  }
}

function onCompareTimelineMouseUp(event) {
  if (!isCompareTimelineDragging.value) return;
  
  isCompareTimelineDragging.value = false;
  
  // 应用选择的时间范围到对比条件
  if (compareSelectedTimeRange.value.start && compareSelectedTimeRange.value.end) {
    compareDates.value = [compareSelectedTimeRange.value.start, compareSelectedTimeRange.value.end];
    ElMessage.success('已选择对比时间段');
  }
}

function onCompareTimelineMouseLeave(event) {
  if (isCompareTimelineDragging.value) {
    onCompareTimelineMouseUp(event);
  }
}

function getCompareTimeFromPosition(x) {
  if (!compareTimelineRef.value || !compareTimelineStart.value || !compareTimelineEnd.value) return null;
  
  const rect = compareTimelineRef.value.getBoundingClientRect();
  const width = rect.width;
  const ratio = Math.max(0, Math.min(1, x / width));
  
  const startTime = compareTimelineStart.value.getTime();
  const endTime = compareTimelineEnd.value.getTime();
  const time = startTime + ratio * (endTime - startTime);
  
  return new Date(time);
}

function getCompareTimelineSegmentStyle(segment) {
  if (!compareTimelineStart.value || !compareTimelineEnd.value) return {};
  
  const startTime = compareTimelineStart.value.getTime();
  const endTime = compareTimelineEnd.value.getTime();
  const totalDuration = endTime - startTime;
  
  const segmentStart = new Date(segment.start).getTime();
  const segmentEnd = new Date(segment.end).getTime();
  
  const left = ((segmentStart - startTime) / totalDuration) * 100;
  const width = ((segmentEnd - segmentStart) / totalDuration) * 100;
  
  return {
    left: `${left}%`,
    width: `${width}%`
  };
}

function getCompareTimelineSelectionStyle() {
  if (!compareSelectedTimeRange.value.start || !compareSelectedTimeRange.value.end || !compareTimelineStart.value || !compareTimelineEnd.value) return {};
  
  const startTime = compareTimelineStart.value.getTime();
  const endTime = compareTimelineEnd.value.getTime();
  const totalDuration = endTime - startTime;
  
  const selectionStart = compareSelectedTimeRange.value.start.getTime();
  const selectionEnd = compareSelectedTimeRange.value.end.getTime();
  
  const left = ((selectionStart - startTime) / totalDuration) * 100;
  const width = ((selectionEnd - selectionStart) / totalDuration) * 100;
  
  return {
    left: `${left}%`,
    width: `${width}%`
  };
}

// 打开IMS详情
function openIMSDetail(anomaly) {
  selectedAnomaly.value = {
    timestamp: anomaly.timestamp,
    ims_model_name: anomaly.ims_detection?.model_name || 'Unknown',
    is_anomaly: anomaly.ims_detection?.is_anomaly || false,
    anomaly_score: anomaly.ims_detection?.anomaly_score || 0,
    parameter_scores: anomaly.ims_detection?.parameter_scores || {},
    detection_details: anomaly.ims_detection?.detection_details || {}
  };
  anomalyDialogVisible.value = true;
}

async function loadCmgs() {
  const res = await apiGet('/data/cmgs/');
  cmgList.value = Array.isArray(res.data) ? res.data : [];
}

function isFiniteNumber(v) {
  return typeof v === 'number' && Number.isFinite(v);
}

function extractDataArray(resp) {
  if (!resp) return [];
  const d = resp.data !== undefined ? resp.data : resp;
  if (Array.isArray(d)) return d;
  if (d && Array.isArray(d.results)) return d.results;
  return [];
}

function buildRows(records) {
  // 将接口返回的记录扁平化为 {timestamp, ...data}
  const rows = records.map(r => ({ timestamp: r.timestamp, ...(r.data || {}) }));
  // 统计可绘制的数值型参数（至少在一行是有效数字）
  const numeric = new Set();
  rows.forEach(r => {
    for (const [k, v] of Object.entries(r)) {
      if (k === 'timestamp') continue;
      const num = typeof v === 'number' ? v : Number(v);
      if (Number.isFinite(num)) numeric.add(k);
    }
  });
  availableMetrics.value = Array.from(numeric);
  return rows;
}

async function loadLatest(initial = false) {
  if (!query.value.cmgId) return;
  
  try {
    let data;
    // 实时模式下仅从 liveStartMs 之后取数；历史模式保持原逻辑
    const res = await apiGet('/data/data/realtime/', { 
      params: { 
        cmg_id: query.value.cmgId,
        since_ms: live.value ? liveStartMs : lastTsMs,
        limit: live.value ? 2000 : 1000
      } 
    });
    data = extractDataArray(res) || res.data;
    
    const rows = buildRows(data);
    
    if (initial || raw.value.length === 0) {
      raw.value = rows;
    } else if (rows.length > 0) {
      // 合并增量，使用毫秒时间戳进行精确去重
      const existingMs = new Set(raw.value.map(r => new Date(r.timestamp).getTime()));
      rows.forEach(r => { 
        const ms = new Date(r.timestamp).getTime();
        if (!existingMs.has(ms)) {
          raw.value.push(r);
          existingMs.add(ms);
        }
      });
      raw.value.sort((a,b) => new Date(a.timestamp) - new Date(b.timestamp));
      
      // 移除数据限制，确保所有数据都被保留
      // 限制内存中的数据量，保留最近的5000条
      // if (raw.value.length > 5000) {
      //   raw.value = raw.value.slice(-5000);
      // }
    }
    
    // 更新最新时间戳
    if (raw.value.length > 0) {
      lastTsMs = new Date(raw.value[raw.value.length - 1].timestamp).getTime();
    }
    
    // 初次加载时同步拉取IMS异常列表和规则检测结果
    if (!live.value) {
      // 历史模式首轮加载时同步拉取检测结果
      await loadIMSAnomalies();
      await loadRuleResults();
    }
    await nextTick();
    renderAll();
  } catch (error) {
    console.error('Failed to load realtime data:', error);
    // 降级到传统API
    const params = { cmg_id: query.value.cmgId };
    if (!initial && lastTsMs) {
      params.since = new Date(lastTsMs).toISOString();
    }
    const res = await apiGet('/data/data/', { params });
    const rows = buildRows(extractDataArray(res));
    raw.value = rows;
    if (raw.value.length > 0) {
      lastTsMs = new Date(raw.value[raw.value.length - 1].timestamp).getTime();
    }
    await nextTick();
    renderAll();
  }

  // 移除错误位置定义的 imsList（已在顶层正确定义）
}

async function loadData() {
  if (!query.value.cmgId) return;
  loading.value = true;
  try {
    const params = { cmg_id: query.value.cmgId };
    if (query.value.dates.length === 2) {
      // 使用带时区的 ISO 字符串（保留毫秒），确保后端严格过滤
      const start = new Date(query.value.dates[0]);
      const end = new Date(query.value.dates[1]);
      params.start = start.toISOString();
      params.end = end.toISOString();
          // 历史模式下获取时间段内的所有数据，不限制数量
    params.limit = 100000; // 大幅增加限制，确保获取完整数据
    } else {
      // 如果没有时间范围，限制数据量
      params.limit = 2000;
    }
    
    const res = await apiGet('/data/data/', { params });
    const rawData = extractDataArray(res);
    
    // 确保数据按时间排序
    rawData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    raw.value = buildRows(rawData);
    
    // 同时加载IMS异常检测结果、规则检测结果和MSFG结果（any失败不阻塞）
    const tasks = [loadIMSAnomalies(), loadRuleResults(), loadMsfgResults()];
    await Promise.allSettled(tasks);
    
    // 退出实时模式
    stopLive();
    lastUpdateTime.value = new Date();
    await nextTick();
    renderAll();
  } catch (error) {
    console.error('Failed to load data:', error);
  } finally {
    loading.value = false;
  }
}

async function loadIMSAnomalies(showSpinner = false) {
  if (!query.value.cmgId) return;
  imsLoading.value = !!showSpinner;
  try {
    const params = { cmg_id: query.value.cmgId, limit: 1000 };
    if (showImsOnlyAbnormal.value) {
      params.anomaly_only = 'true';
    }
    if (query.value.dates.length === 2) {
      params.start_time = new Date(query.value.dates[0]).toISOString();
      params.end_time = new Date(query.value.dates[1]).toISOString();
    }
    const res = await apiGet('/health/ims-results/anomaly-data/', { params });
    imsAnomalies.value = extractDataArray(res) || res.data || [];
    
    // 重新渲染所有图表以显示最新的异常点
    metricsToPlot.value.forEach(metric => {
      if (charts.has(metric)) {
        renderChart(metric);
      }
    });
  } catch (error) {
    console.error('Failed to load IMS anomalies:', error);
    imsAnomalies.value = [];
  } finally {
    imsLoading.value = false;
  }
}

// 加载规则检测结果
async function loadRuleResults(showSpinner = false) {
  if (!query.value.cmgId) return;
  ruleLoading.value = !!showSpinner;
  try {
    const params = { cmg_id: query.value.cmgId, limit: 50 };
    if (query.value.dates.length === 2) {
      params.start_time = new Date(query.value.dates[0]).toISOString();
      params.end_time = new Date(query.value.dates[1]).toISOString();
    }
    const res = await apiGet('/rules/results/', { params });
    ruleResults.value = extractDataArray(res);
  } catch (error) {
    console.error('Failed to load rule results:', error);
    ruleResults.value = [];
  } finally {
    ruleLoading.value = false;
  }
}

// 刷新规则检测结果
  function refreshRules() { loadRuleResults(true); }

// 寿命预测相关函数
async function predictLifetime() {
  if (!query.value.cmgId || !hasTimelineSelection.value) {
    ElMessage.warning('请先选择CMG并通过时间轴选择数据时间段');
    return;
  }
  
  if (!isLifetimeParamsValid.value) {
    ElMessage.warning('请填写完整的设计寿命和启用时间');
    return;
  }
  
  lifetimeLoading.value = true;
  try {
    // 获取当前CMG的ID（需要从cmgList中找到对应的数据库ID）
    const cmg = cmgList.value.find(c => c.cmg_id === query.value.cmgId);
    if (!cmg) {
      ElMessage.error('未找到对应的CMG信息');
      return;
    }
    
    console.log('寿命预测参数:', {
      cmg_db_id: cmg.id,
      cmg_id: cmg.cmg_id,
      design_life: lifetimeParams.value.designLife,
      start_time: lifetimeParams.value.startTime,
      timeline_selection: {
        start: selectedTimeRange.value.start,
        end: selectedTimeRange.value.end
      }
    });
    
    // 使用时间轴选择的时间段进行数据查询
    const dataStartTime = selectedTimeRange.value.start.toISOString();
    const dataEndTime = selectedTimeRange.value.end.toISOString();
    
    // 转换启用时间格式
    let formattedStartTime = lifetimeParams.value.startTime;
    if (formattedStartTime && formattedStartTime.includes('/')) {
      formattedStartTime = formattedStartTime.replace(/\//g, '-');
    }
    
    console.log('API调用参数:', {
      data_start: dataStartTime,
      data_end: dataEndTime,
      cmg_start_time: formattedStartTime
    });
    
    // 调用寿命预测API
    const response = await api.post('/lifetime/predict/', {
      cmg_id: cmg.cmg_id,  // 使用CMG标识符，不是数据库ID
      design_life: lifetimeParams.value.designLife,
      start_time: formattedStartTime,  // CMG启用时间
      data_start_time: dataStartTime,  // 数据查询开始时间（来自时间轴选择）
      end_time: dataEndTime  // 数据查询结束时间（来自时间轴选择）
    });
    
    if (response.data.status === 'success') {
      lifetimeResult.value = response.data.data;
      ElMessage.success('寿命预测完成');
    } else {
      // 显示详细的错误信息
      const errorMessage = response.data.message || '预测失败';
      if (errorMessage.includes('没有可用的遥测数据')) {
        ElMessage.error('所选时间段内没有找到遥测数据，请通过时间轴选择其他时间段');
      } else if (errorMessage.includes('数据长度不足')) {
        ElMessage.error('数据量不足，请通过时间轴选择更长的时间段');
      } else {
        ElMessage.error(errorMessage);
      }
    }
  } catch (error) {
    console.error('寿命预测失败:', error);
    ElMessage.error('寿命预测失败，请检查网络连接或稍后重试');
  } finally {
    lifetimeLoading.value = false;
  }
}

function clearLifetimeResult() {
  lifetimeResult.value = null;
}



function formatTime(timeStr) {
  if (!timeStr) return '未知';
  return new Date(timeStr).toLocaleString('zh-CN');
}

// 打开规则帧详情
function openRuleFrameDetail(frame) {
  selectedRuleFrameForDialog.value = frame;
  ruleFrameDialogVisible.value = true;
}

// 打开规则详情
function openRuleDetail(rule) {
  selectedRule.value = rule;
  ruleDialogVisible.value = true;
}

// 获取部件健康度统计
function getComponentHealthSummary(items) {
  const componentScores = {};
  // 只处理触发的规则，因为只有触发的规则才表示部件异常
  const triggeredItems = items.filter(item => item.is_triggered);
  
  triggeredItems.forEach(item => {
    const component = item.component || item.fault_definition?.component || item.detection_details?.component || '未知部件';
    const healthScore = item.detection_details?.component_health_score ?? 1.0;
    
    // 如果同一个部件有多个规则，取最低的健康度分数
    if (componentScores[component] === undefined || healthScore < componentScores[component]) {
      componentScores[component] = healthScore;
    }
  });
  return componentScores;
}

// 显示异常详情
function showAnomalyDetail(anomalyInfo, metric, timestamp, value) {
  selectedAnomaly.value = {
    ...anomalyInfo,
    metric,
    timestamp,
    value
  };
  anomalyDialogVisible.value = true;
}

function onCmgChange() {
  selectedMetrics.value = [];
  availableMetrics.value = [];
  raw.value = [];
  lastTsMs = null;
  
  // 清理检测结果状态
  imsAnomalies.value = [];
  ruleResults.value = [];
  msfgResults.value = [];
  
  // 断开之前的WebSocket连接
  disconnectWebSocket();
  
  // 实时模式下，选择 CMG 即开始实时
  if (mode.value === 'realtime' && hasCmgSelected.value) {
    startLive();
    startDetectionPolling(5000);
  }
  
  // 加载时间轴数据
  if (query.value.cmgId) {
    fetchTimelineData();
  } else {
    // 清空时间轴数据
    timelineData.value = [];
    recommendedSegments.value = [];
    selectedTimeRange.value = { start: null, end: null };
  }
}

function scheduleRender() {
  if (renderScheduled) return;
  renderScheduled = true;
  requestAnimationFrame(() => {
    renderScheduled = false;
    renderAll();
  });
}

function renderAll() { 
  if (!isActive.value) {
    console.log('组件已卸载，跳过图表渲染');
    return;
  }
  
  const metricsToRender = [...metricsToPlot.value];
  metricsToRender.forEach(m => {
    nextTick(() => {
      if (isActive.value) {
        renderChart(m);
      }
    });
  });
}

function renderChart(metric) {
  const chart = charts.get(metric);
  if (!chart) return;
  
  // 检查图表是否已被销毁
  try {
    const dom = chart.getDom();
    if (!dom || !dom.isConnected) {
      charts.delete(metric);
      return;
    }
  } catch (e) {
    charts.delete(metric);
    return;
  }
  
  // 显示所有点，避免漏点引起的稀疏
  let rawData = raw.value;
  
  // 优化数据处理：确保所有有效数据都被包含
  const data = rawData
    .map((r, index) => {
      const y = typeof r[metric] === 'number' ? r[metric] : Number(r[metric]);
      const timestamp = new Date(r.timestamp).getTime();
      return [timestamp, y, index];
    })
    .filter(d => Number.isFinite(d[1]) && d[1] !== null && d[1] !== undefined)
    .map(d => [d[0], d[1]]);
    
  // 如果没有有效数据，显示空图表
  if (data.length === 0) {
    chart.setOption({
      animation: false,
      grid: { left: 50, right: 20, top: 25, bottom: 40 },
      xAxis: { type: 'time' },
      yAxis: { type: 'value' },
      series: [{ name: metric, type: 'line', data: [] }]
    }, true);
    return;
  }
  
  // 获取IMS异常帧的时间戳，用于标记异常点
  const anomalyTimestamps = new Set();
  if (imsAnomalies.value && Array.isArray(imsAnomalies.value)) {
    imsAnomalies.value.forEach(anomaly => {
      if (anomaly.ims_detection?.is_anomaly || anomaly.is_anomaly) {
        const timestamp = new Date(anomaly.timestamp).getTime();
        anomalyTimestamps.add(timestamp);
      }
    });
  }
  
  // 创建异常点数据
  const anomalyPoints = [];
  data.forEach(point => {
    if (anomalyTimestamps.has(point[0])) {
      anomalyPoints.push(point);
    }
  });

  // 优化图表配置，确保数据完整性
  const option = {
    animation: false,
    grid: { left: 60, right: 30, top: 35, bottom: 50 },
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'cross' },
      formatter: function(params) {
        if (params && params.length > 0) {
          const time = new Date(params[0].value[0]).toLocaleString();
          const value = params[0].value[1];
          let tooltipText = `${metric}<br/>${time}<br/>值: ${value}`;
          
          // 如果是异常点，添加异常标记
          if (anomalyTimestamps.has(params[0].value[0])) {
            tooltipText += '<br/><span style="color: #f56c6c;">⚠️ IMS异常检测</span>';
          }
          
          return tooltipText;
        }
        return '';
      }
    },
    legend: { show: false },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, zoomOnMouseWheel: true },
      { type: 'slider', xAxisIndex: 0, height: 20, bottom: 5 },
      { type: 'inside', yAxisIndex: 0, zoomOnMouseWheel: true },
      { type: 'slider', yAxisIndex: 0, width: 20, right: 5 }
    ],
    xAxis: {
      type: 'time',
      min: live.value && typeof liveStartMs === 'number' ? liveStartMs : (query.value.dates?.[0] ? new Date(query.value.dates[0]).getTime() : null),
      max: !live.value && query.value.dates?.[1] ? new Date(query.value.dates[1]).getTime() : null,
      axisLabel: { 
        formatter: (val) => new Date(val).toLocaleTimeString(),
        rotate: 0
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLine: { onZero: false },
      scale: true,
      splitLine: { lineStyle: { type: 'dashed', opacity: 0.3 } }
    },
    series: [
      {
        name: metric,
        type: 'line',
        symbol: 'none',
        symbolSize: 1,
        lineStyle: { width: 1.5 },
        sampling: undefined, // 禁用采样，确保所有数据点都显示
        large: true, // 启用大数据量优化
        largeThreshold: 5000, // 降低阈值，提高渲染性能
        data,
        // 确保数据连续性
        connectNulls: false,
        // 优化大数据量渲染
        progressive: 2000, // 增加渐进渲染批次
        progressiveThreshold: 5000 // 提高渐进渲染阈值
      },
      {
        name: '异常点',
        type: 'scatter',
        symbol: 'circle',
        symbolSize: 10,
        itemStyle: {
          color: '#d32f2f',
          borderColor: '#fff',
          borderWidth: 2
        },
        data: anomalyPoints,
        tooltip: {
          formatter: function(params) {
            const time = new Date(params.value[0]).toLocaleString();
            const value = params.value[1];
            return `异常点<br/>${time}<br/>值: ${value}<br/>IMS异常检测`;
          }
        }
      }
    ]
  };
  
  try {
    chart.setOption(option, { notMerge: false, lazyUpdate: true, silent: true });
  } catch (e) {
    console.warn(`Failed to render chart for metric ${metric}:`, e);
    charts.delete(metric);
  }
}

async function startLive() {
  live.value = true;
  if (liveTimer) clearInterval(liveTimer);
  // 进入实时模式时，从当前时间开始显示
  raw.value = [];
  lastTsMs = Date.now();
  liveStartMs = lastTsMs;
  
  // 尝试建立WebSocket连接
  if (query.value.cmgId) {
    await connectWebSocket();
    
    // 如果WebSocket连接成功，使用WebSocket获取实时数据
    if (wsConnected.value) {
      // 不做历史回填，仅从当前开始接收
      websocketService.startStream(1.0);
      // 保险起见拉一次增量（即使为空），保证渲染启动
      await loadLatest(false);
      return;
    }
  }
  
  // WebSocket连接失败，降级到轮询模式
  console.log('WebSocket not available, using polling mode');
  // 根据数据更新频率调整轮询间隔，减少不必要的请求（从当前时间起增量拉取）
  liveTimer = setInterval(() => loadLatest(false), 1500);
}

function stopLive() {
  live.value = false;
  
  // 停止WebSocket数据流
  if (wsConnected.value) {
    websocketService.stopStream();
  }
  
  // 停止轮询
  if (liveTimer) { 
    clearInterval(liveTimer); 
    liveTimer = null; 
  }
  // 停止对比自动刷新
  if (compareTimer) { clearInterval(compareTimer); compareTimer = null; }
}

function toggleLive() {
  if (!query.value.cmgId) return;
  if (live.value) stopLive(); else startLive();
}

// 当选择时间段时，退出实时模式
function onDateChange() {
  if (query.value.dates && query.value.dates.length === 2) {
    if (mode.value === 'realtime') {
      mode.value = 'history';
      ElMessage.info('已切换到历史模式');
    }
    if (live.value) stopLive();
  }
}

// 获取时间轴数据
async function fetchTimelineData() {
  timelineLoading.value = true;
  timelineData.value = [];
  if (!query.value.cmgId) return;
  
  try {
    // 获取所有数据用于构建时间轴
    const res = await api.get('/data/data/', { 
      params: { cmg_id: query.value.cmgId, limit: 5000000 },
      timeout: 300000 // 5分钟超时
    });
    const rows = extractDataArray(res);
    if (rows.length < 2) return;
    
    const sorted = rows
      .filter(r => r && r.timestamp)
      .slice()
      .sort((a,b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    if (sorted.length < 2) return;

    // 设置时间轴范围
    timelineStart.value = new Date(sorted[0].timestamp);
    timelineEnd.value = new Date(sorted[sorted.length - 1].timestamp);

    // 计算相邻间隔的中位数，作为采样周期的估计
    const deltas = [];
    for (let i = 1; i < sorted.length; i++) {
      const prev = new Date(sorted[i-1].timestamp).getTime();
      const cur = new Date(sorted[i].timestamp).getTime();
      const d = cur - prev;
      if (Number.isFinite(d) && d > 0) deltas.push(d);
    }
    deltas.sort((a,b) => a - b);
    const medianDelta = deltas.length > 0 ? deltas[Math.floor(deltas.length / 2)] : 60 * 1000;
    
    // 定义"断点"阈值：5倍中位间隔，至少5分钟，确保能包含更多数据
    const gapThreshold = Math.max(5 * medianDelta, 5 * 60 * 1000);

    const segments = [];
    let segStartMs = new Date(sorted[0].timestamp).getTime();
    let prevMs = segStartMs;
    let segmentDataCount = 1;
    
    for (let i = 1; i < sorted.length; i++) {
      const curMs = new Date(sorted[i].timestamp).getTime();
      if (curMs - prevMs > gapThreshold) {
        // 只有当段内数据量足够多时才添加
        if (segmentDataCount >= 10) {
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
    
    // 添加最后一个段
    if (segmentDataCount >= 10) {
      segments.push({ 
        start: new Date(segStartMs).toISOString(), 
        end: new Date(prevMs).toISOString(),
        dataCount: segmentDataCount
      });
    }

    timelineData.value = segments;
    
    // 同时更新推荐时间段
    await fetchRecommendedSegments(sorted);
    
  } catch (e) {
    console.error('获取时间轴数据失败:', e);
  } finally {
    timelineLoading.value = false;
  }
}

// 刷新时间轴
async function refreshTimeline() {
  await fetchTimelineData();
  ElMessage.success('时间轴已刷新');
}

// 推荐连续有数据的时间段：基于相邻时间差的中位数自适应分段，确保连续
async function fetchRecommendedSegments(sortedData = null) {
  recommendedSegments.value = [];
  if (!query.value.cmgId) return;
  
  try {
    let sorted;
    if (sortedData) {
      sorted = sortedData;
    } else {
      const res = await api.get('/data/data/', { 
        params: { cmg_id: query.value.cmgId, limit: 5000000 },
        timeout: 300000 // 5分钟超时
      });
      const rows = extractDataArray(res);
      if (rows.length < 2) return;
      sorted = rows
        .filter(r => r && r.timestamp)
        .slice()
        .sort((a,b) => new Date(a.timestamp) - new Date(b.timestamp));
    }
    
    if (sorted.length < 2) return;

    // 计算相邻间隔的中位数，作为采样周期的估计
    const deltas = [];
    for (let i = 1; i < sorted.length; i++) {
      const prev = new Date(sorted[i-1].timestamp).getTime();
      const cur = new Date(sorted[i].timestamp).getTime();
      const d = cur - prev;
      if (Number.isFinite(d) && d > 0) deltas.push(d);
    }
    deltas.sort((a,b) => a - b);
    const medianDelta = deltas.length > 0 ? deltas[Math.floor(deltas.length / 2)] : 60 * 1000;
    
    // 定义"断点"阈值：5倍中位间隔，至少5分钟，确保能包含更多数据
    const gapThreshold = Math.max(5 * medianDelta, 5 * 60 * 1000);

    const segments = [];
    let segStartMs = new Date(sorted[0].timestamp).getTime();
    let prevMs = segStartMs;
    let segmentDataCount = 1;
    
    for (let i = 1; i < sorted.length; i++) {
      const curMs = new Date(sorted[i].timestamp).getTime();
      if (curMs - prevMs > gapThreshold) {
        // 只有当段内数据量足够多时才添加
        if (segmentDataCount >= 50) {
          segments.push({ start: new Date(segStartMs).toISOString(), end: new Date(prevMs).toISOString() });
        }
        segStartMs = curMs;
        segmentDataCount = 1;
      } else {
        segmentDataCount++;
      }
      prevMs = curMs;
    }
    
    // 添加最后一个段
    if (segmentDataCount >= 50) {
      segments.push({ start: new Date(segStartMs).toISOString(), end: new Date(prevMs).toISOString() });
    }

    // 选取最近的几个连续片段，但确保每个片段都有足够的数据
    segments.sort((a,b) => new Date(b.end) - new Date(a.end));
    recommendedSegments.value = segments.slice(0, 5); // 增加到5个推荐
  } catch (e) {
    console.error('获取推荐时间段失败:', e);
  }
}

function pickSegment(seg) {
  query.value.dates = [new Date(seg.start), new Date(seg.end)];
  selectedTimeRange.value = { start: new Date(seg.start), end: new Date(seg.end) };
  if (mode.value === 'realtime') {
    mode.value = 'history';
    ElMessage.info('已切换到历史模式');
  }
}

// 时间轴交互功能
function onTimelineMouseDown(event) {
  if (!timelineRef.value || !timelineStart.value || !timelineEnd.value) return;
  
  const rect = timelineRef.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const time = getTimeFromPosition(x);
  
  isTimelineDragging.value = true;
  dragStartX.value = x;
  dragStartTime.value = time;
  selectedTimeRange.value = { start: time, end: time };
}

function onTimelineMouseMove(event) {
  if (!isTimelineDragging.value || !timelineRef.value) return;
  
  const rect = timelineRef.value.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const time = getTimeFromPosition(x);
  
  if (time && dragStartTime.value) {
    const start = new Date(Math.min(dragStartTime.value.getTime(), time.getTime()));
    const end = new Date(Math.max(dragStartTime.value.getTime(), time.getTime()));
    selectedTimeRange.value = { start, end };
  }
}

function onTimelineMouseUp(event) {
  if (!isTimelineDragging.value) return;
  
  isTimelineDragging.value = false;
  
  // 应用选择的时间范围到查询条件
  if (selectedTimeRange.value.start && selectedTimeRange.value.end) {
    query.value.dates = [selectedTimeRange.value.start, selectedTimeRange.value.end];
    ElMessage.success('已选择时间段');
  }
}

function onTimelineMouseLeave(event) {
  if (isTimelineDragging.value) {
    onTimelineMouseUp(event);
  }
}

function getTimeFromPosition(x) {
  if (!timelineRef.value || !timelineStart.value || !timelineEnd.value) return null;
  
  const rect = timelineRef.value.getBoundingClientRect();
  const width = rect.width;
  const ratio = Math.max(0, Math.min(1, x / width));
  
  const startTime = timelineStart.value.getTime();
  const endTime = timelineEnd.value.getTime();
  const time = startTime + ratio * (endTime - startTime);
  
  return new Date(time);
}

function getTimelineSegmentStyle(segment) {
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
}

function getTimelineSelectionStyle() {
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
}

function formatTimelineSegment(segment) {
  const start = new Date(segment.start).toLocaleString('zh-CN');
  const end = new Date(segment.end).toLocaleString('zh-CN');
  const duration = Math.round((new Date(segment.end) - new Date(segment.start)) / 1000 / 60);
  return `${start} - ${end} (${duration}分钟, ${segment.dataCount || 0}帧)`;
}

function refreshIMS() {
  loadIMSAnomalies(true);
}

const onWindowResize = () => { charts.forEach(c => c.resize()); };
// WebSocket连接管理
function setupWebSocket() {
  // 设置WebSocket事件处理器
  websocketService.onConnect(() => {
    wsConnected.value = true;
    wsConnecting.value = false;
    console.log('WebSocket connected for CMG:', query.value.cmgId);
  });

  websocketService.onDisconnect(() => {
    wsConnected.value = false;
    wsConnecting.value = false;
    // 断线后主按钮切回"开始实时"
    live.value = false;
    // 保持对比图与检测轮询可继续（不改 compareTimer/detectionPollTimer）
  });

  websocketService.onError((error) => {
    wsConnecting.value = false;
    console.error('WebSocket error:', error);
    ElMessage.error('WebSocket连接异常，已降级到轮询模式');
    live.value = false;
  });

  // 监听实时数据消息
  websocketService.onMessage('realtime_data', (data) => {
    if (data.cmg_id !== query.value.cmgId || !data.data) return;
    // 页面非激活时丢弃或缓冲数据，避免堆积导致回到页面卡顿
    if (!isActive.value) {
      // 仅保留少量最新数据，避免内存占用
      wsBuffered = data.data.slice(-200);
      return;
    }
    enqueueWebsocketData(data.data);
  });

  // 监听系统通知
  websocketService.onMessage('notification', (data) => {
    if (data.level === 'error') {
      ElMessage.error(data.message);
    } else if (data.level === 'warning') {
      ElMessage.warning(data.message);
    } else {
      ElMessage.info(data.message);
    }
  });
}

function enqueueWebsocketData(newData) {
  if (!Array.isArray(newData) || newData.length === 0) return;
  wsBuffered.push(...newData);
  if (wsBuffered.length > 2000) {
    wsBuffered = wsBuffered.slice(-2000);
  }
  if (wsFlushTimer) return;
  wsFlushTimer = setTimeout(() => {
    wsFlushTimer = null;
    flushWebsocketBuffer();
  }, 120); // 批量合并，最多约 ~8fps
}

function flushWebsocketBuffer() {
  if (wsBuffered.length === 0) return;
  let rows = buildRows(wsBuffered);
  wsBuffered = [];
  if (rows.length === 0) return;
  // 实时模式下仅保留实时开始后的数据
  if (live.value && typeof liveStartMs === 'number') {
    rows = rows.filter(r => new Date(r.timestamp).getTime() >= liveStartMs);
  }
  const existingMs = new Set(raw.value.map(r => new Date(r.timestamp).getTime()));
  for (const r of rows) {
    const ms = new Date(r.timestamp).getTime();
    if (!existingMs.has(ms)) {
      raw.value.push(r);
      existingMs.add(ms);
    }
  }
      raw.value.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    // 移除数据限制，确保所有数据都被保留
    // if (raw.value.length > 5000) raw.value = raw.value.slice(-5000);
  if (raw.value.length > 0) lastTsMs = new Date(raw.value[raw.value.length - 1].timestamp).getTime();
  scheduleRender();
}

async function connectWebSocket() {
  if (!query.value.cmgId) return;
  
  wsConnecting.value = true;
  try {
    await websocketService.connect(query.value.cmgId);
  } catch (error) {
    wsConnecting.value = false;
    console.error('Failed to connect WebSocket:', error);
  }
}

function disconnectWebSocket() {
  websocketService.disconnect();
  wsConnected.value = false;
  wsConnecting.value = false;
}

onMounted(() => { 
  window.addEventListener('resize', onWindowResize);
  setupWebSocket();
  // 不在挂载时提前初始化对比图实例，避免对话框未挂载导致的空 DOM 引用
});

onBeforeUnmount(() => { 
  // 首先设置组件为非活跃状态，防止异步操作继续更新DOM
  isActive.value = false;
  // 终止所有未完成的请求
  try { abortAllPending(); } catch(e) {}
  
  stopLive();
  disconnectWebSocket();
  // 停止检测结果轮询
  if (detectionPollTimer) { clearInterval(detectionPollTimer); detectionPollTimer = null; }
  window.removeEventListener('resize', onWindowResize);
  charts.forEach(c => c.dispose && c.dispose());
  charts.clear();
  if (wsFlushTimer) { clearTimeout(wsFlushTimer); wsFlushTimer = null; }
  if (compareTimer) { clearInterval(compareTimer); compareTimer = null; }
  if (compareChartInst) { try { compareChartInst.dispose(); } catch(e) {}; compareChartInst = null; }
});

onMounted(loadCmgs);

// keep-alive 激活时的恢复机制
function handleActivated() {
  isActive.value = true;
  // 如果有选定的CMG且处于实时模式，恢复实时数据
  if (query.value.cmgId && live.value) {
    // 仅增量补齐，避免大批量渲染导致卡顿
    if (lastTsMs) {
      loadLatest(false);
    }
    // 确保实时流处于开启状态
    if (wsConnected.value) {
      websocketService.startStream(1.0);
    }
  }
  // 恢复检测结果轮询
  if (mode.value === 'realtime' && hasCmgSelected.value) {
    startDetectionPolling(5000);
  }
  // 重新渲染所有图表
  nextTick(() => {
    renderAll();
  });
}

// 组件停用时停止实时更新
function handleDeactivated() {
  isActive.value = false;
  if (liveTimer) { clearInterval(liveTimer); liveTimer = null; }
  // 暂停实时数据流，避免后台持续堆积
  if (wsConnected.value) {
    websocketService.stopStream();
  }
  // 暂停检测结果轮询
  if (detectionPollTimer) { clearInterval(detectionPollTimer); detectionPollTimer = null; }
}

// 注册 keep-alive 钩子
onActivated(handleActivated);
onDeactivated(handleDeactivated);

// 当选择的指标列表变化时，清理不再展示的图表实例，避免实例绑定到已卸载的 DOM 上
watch(metricsToPlot, (newList) => {
  const keep = new Set(newList);
  for (const [metric, inst] of Array.from(charts.entries())) {
    if (!keep.has(metric)) {
      try { inst.dispose(); } catch(e) {}
      charts.delete(metric);
    }
  }
  nextTick(() => renderAll());
});

// 启动/停止 IMS、规则检测和MSFG结果轮询（数据库拉取）
function startDetectionPolling(intervalMs = 5000) {
  if (detectionPollTimer) { clearInterval(detectionPollTimer); detectionPollTimer = null; }
  const tick = () => {
    if (!hasCmgSelected.value) return;
    if (!imsLoading.value) loadIMSAnomalies();
    if (!ruleLoading.value) loadRuleResults();
    if (!msfgLoading.value) loadMsfgResults();
  };
  // 立即拉一次，随后定时
  tick();
  detectionPollTimer = setInterval(tick, intervalMs);
}

function stopDetectionPolling() {
  if (detectionPollTimer) { clearInterval(detectionPollTimer); detectionPollTimer = null; }
}

// 监听模式切换：进入实时=开始实时；返回历史=停止并断开
watch(mode, (val) => {
  if (val === 'realtime') {
    if (!hasCmgSelected.value) {
      live.value = false;
      return;
    }
    startLive();
    startDetectionPolling(5000);
    // 若对比设置为实时且开启自动刷新，触发一次绘制
    if (compareTimeMode.value === 'realtime' && compareAutoRefresh.value && canDrawCompare.value) {
      drawCompareChart();
    }
  } else {
    stopLive();
    disconnectWebSocket();
    stopDetectionPolling();
    if (compareTimer) { clearInterval(compareTimer); compareTimer = null; }
  }
});

// MSFG相关方法
async function loadMsfgResults(showSpinner = false) {
  if (!query.value.cmgId) return;
  
  msfgLoading.value = !!showSpinner;
  try {
    const params = {
      cmg_id: query.value.cmgId,
      limit: 50,
      ordering: '-created_at'
    };
    
    // 添加时间范围过滤（如果在历史模式下有设置）
    if (query.value.dates.length === 2) {
      params.start_time = new Date(query.value.dates[0]).toISOString();
      params.end_time = new Date(query.value.dates[1]).toISOString();
    }
    
    const response = await api.get('/msfg/results/', { params });
    
    // 检查组件是否仍然活跃（防止异步操作在组件卸载后执行）
    if (!isActive.value) {
      console.log('组件已卸载，跳过MSFG结果更新');
      return;
    }
    
    // 改进的数据处理逻辑
    let results = [];
    if (Array.isArray(response.data)) {
      results = response.data;
    } else if (response.data && Array.isArray(response.data.results)) {
      results = response.data.results;
    } else if (response.data && response.data.count !== undefined) {
      // 分页响应格式
      results = response.data.results || [];
    }
    
    // 数据验证和清理
    const validResults = results.filter(result => {
      return result && 
             result.overall_health_score !== undefined && 
             result.created_at;
    });
    
    // 再次检查组件状态
    if (!isActive.value) {
      console.log('组件已卸载，跳过MSFG结果设置');
      return;
    }
    
    msfgResults.value = validResults;
    console.log(`加载了 ${msfgResults.value.length} 条MSFG分析结果`);
    
    // 加载完数据后更新趋势图
    await nextTick();
    if (isActive.value) {
      updateMsfgTrendChart();
    }
  } catch (error) {
    console.error('加载MSFG结果失败:', error);
    // 只在显示加载提示时才显示错误消息
    if (showSpinner && isActive.value) {
      ElMessage.error('加载多信号流图结果失败');
    }
    // 清空结果数组以防止显示错误数据
    if (isActive.value) {
      msfgResults.value = [];
    }
  } finally {
    if (isActive.value) {
      msfgLoading.value = false;
    }
  }
}

function getMsfgHealthTag(score) {
  if (score >= 0.8) return 'success';
  if (score >= 0.6) return 'warning';
  return 'danger';
}

function getTestScoreTag(score) {
  if (score <= 0.2) return 'success';  // 正常
  if (score <= 0.5) return 'warning';  // 轻微异常
  return 'danger';                     // 严重异常
}

function getFaultScoreTag(score) {
  if (score <= 0.2) return 'success';  // 无故障
  if (score <= 0.5) return 'warning';  // 可能故障
  return 'danger';                     // 确定故障
}

function getFaultCountTag(count) {
  if (count === 0) return 'success';   // 无故障
  if (count <= 2) return 'warning';    // 少量故障
  return 'danger';                     // 多个故障
}

function getSystemHealthTag(score) {
  if (score <= 0.2) return 'success';  // 系统健康
  if (score <= 0.5) return 'warning';  // 系统预警
  return 'danger';                     // 系统故障
}

function getHealthStatusText(score) {
  if (score >= 0.8) return '健康';
  if (score >= 0.6) return '预警';
  return '故障';
}

function getTopRiskyComponents(componentResults, topN = 2) {
  if (!componentResults) return [];
  
  // 将组件转换为数组并按风险程度排序
  const components = Object.entries(componentResults).map(([name, data]) => ({
    name,
    data,
    riskScore: calculateRiskScore(data)
  }));
  
  // 按风险分数降序排序，只返回有风险的组件
  return components
    .filter(comp => comp.riskScore > 0.2) // 只显示有一定风险的组件
    .sort((a, b) => b.riskScore - a.riskScore)
    .slice(0, topN);
}

// 计算MSFG结果的整体健康分（组件健康均值）
function getMsfgHealthScore(result) {
  try {
    const componentData = msfgKvComponent(result?.component_results || {});
    const vals = [];
    for (const item of componentData) {
      const healthScore = Number(item.health_score || 1);
      if (Number.isFinite(healthScore)) {
        vals.push(Math.min(1, Math.max(0, healthScore)));
      }
    }
    if (vals.length === 0) return 1.0;
    const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
    return avg;
  } catch(e) { return 1.0; }
}

function topMsfgComponent(result) {
  try {
    // 使用与MSFG结果页面相同的数据处理方式
    const componentData = msfgKvComponent(result?.component_results || {});
    
    // 转换为健康分数数组并排序
    const entries = componentData.map(item => ({
      name: item.component,
      health: Number(item.health_score || 1)
    }));
    
    // 按健康分数升序排序（分数越低越不健康），取第一个
    entries.sort((a, b) => a.health - b.health);
    return entries.length ? `${entries[0].name}: ${entries[0].health.toFixed(3)}` : null;
  } catch(e) { return null; }
}

function msfgKv(obj) {
  const out = [];
  if (!obj || typeof obj !== 'object') return out;
  for (const [k, v] of Object.entries(obj)) {
    // 处理嵌套对象：如果值是对象且包含score字段，则提取score
    let finalValue = v;
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      if (v.score !== undefined) {
        finalValue = v.score;  // 测试点结果
      } else if (v.fault_probability !== undefined) {
        finalValue = v.fault_probability;  // 故障结果
      } else if (v.fuzzy_probability !== undefined) {
        finalValue = v.fuzzy_probability;  // 备选故障结果
      }
    }
    out.push({ k, v: finalValue });
  }
  return out;
}

function msfgKvComponent(obj) {
  const out = [];
  if (!obj || typeof obj !== 'object') return out;
  for (const [component, data] of Object.entries(obj)) {
    out.push({ component, ...(data || {}) });
  }
  return out;
}

function getHealthTag(score) { 
  const healthScore = Number(score || 1);
  // 统一逻辑：健康分数越高越健康
  if (healthScore >= 0.8) return 'success';   // 健康
  if (healthScore >= 0.6) return 'warning';   // 预警
  return 'danger';                            // 故障
}

function calculateRiskScore(componentData) {
  // 综合考虑健康分数、活跃故障数量和最大故障分数
  const healthScore = Number(componentData.health_score || 1);
  const activeFaultCount = Number(componentData.active_fault_count || 0);
  const maxFaultScore = Number(componentData.max_fault_score || 0);
  
  // 风险分数 = (1 - 健康分数) + 活跃故障权重 + 最大故障分数权重
  const riskScore = (1 - healthScore) * 0.6 + 
                   (activeFaultCount / 10) * 0.2 + 
                   maxFaultScore * 0.2;
                   
  return Math.min(riskScore, 1.0); // 确保不超过1
}

function getComponentCardClass(score) {
  if (score >= 0.8) return 'component-healthy';
  if (score >= 0.6) return 'component-warning';
  return 'component-danger';
}

function openMsfgDetail(res) {
  try {
    selectedMsfg.value = res || latestMsfgResult.value || null;
    if (selectedMsfg.value) msfgDetailDialogVisible.value = true;
  } catch(_) {
    selectedMsfg.value = null;
  }
}

function updateMsfgTrendChart() {
  try {
    // 首先检查组件是否仍然活跃
    if (!isActive.value) {
      console.log('组件已卸载，跳过MSFG趋势图更新');
      return;
    }
    
    // 增强的安全检查
    if (!msfgTrendChart.value || !msfgResults.value || msfgResults.value.length === 0) return;
    
    // 检查DOM元素是否仍然有效
    const chartContainer = msfgTrendChart.value;
    if (!chartContainer || !chartContainer.isConnected) {
      console.warn('MSFG趋势图容器已断开连接，跳过更新');
      return;
    }
    
    const latestScore = latestMsfgResult.value?.system_results?.worst_fault_score ?? 0;
    const scoreText = latestScore.toFixed(3);
    
    // 安全地更新DOM内容
    requestAnimationFrame(() => {
      if (isActive.value && chartContainer && chartContainer.isConnected && msfgTrendChart.value) {
        chartContainer.innerHTML = `
          <div style="padding: 20px; text-align: center; color: #666;">
            <p>综合故障分趋势</p>
            <p>最新综合故障分: <span style="color: ${latestScore <= 0.2 ? '#67c23a' : latestScore <= 0.4 ? '#e6a23c' : '#f56c6c'}; font-weight: bold;">${scoreText}</span></p>
            <p>数据点数: ${msfgResults.value?.length || 0}</p>
            <p style="font-size: 12px; color: #999;">
              ${msfgResults.value?.length > 0 ? `时间范围: ${formatDateTime(msfgResults.value[msfgResults.value.length - 1].created_at)} ~ ${formatDateTime(msfgResults.value[0].created_at)}` : ''}
            </p>
          </div>
        `;
      }
    });
  } catch (error) {
    console.error('更新MSFG趋势图失败:', error);
    // 安全的错误处理
    if (msfgTrendChart.value && msfgTrendChart.value.isConnected) {
      try {
        msfgTrendChart.value.innerHTML = `
          <div style="padding: 20px; text-align: center; color: #f56c6c;">
            <p>趋势图加载失败</p>
          </div>
        `;
      } catch (e) {
        console.error('设置错误信息失败:', e);
      }
    }
  }
}
</script>

<style scoped>
/* 页面主容器 */
.cmg-detail-page {
  padding: 0;
  padding-top: var(--cmg-space-4);
  background: var(--cmg-bg-secondary);
  min-height: calc(100vh - 80px);
}

/* 统一卡片视觉 */
.cmg-filters-card {
  margin-bottom: var(--cmg-space-4);
}

.cmg-toolbar-content {
  padding: var(--cmg-space-4) var(--cmg-space-6);
}

.cmg-mode-switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--cmg-space-3);
}

.cmg-light-hint {
  margin-left: var(--cmg-space-3);
}

.cmg-actions-item {
  margin-left: auto;
}

.cmg-filter-form {
  margin-bottom: var(--cmg-space-3);
}

.cmg-filter-form :deep(.el-form-item) {
  margin-right: var(--cmg-space-4);
  margin-bottom: var(--cmg-space-3);
}

.cmg-recommended-segments {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-3);
  padding-top: var(--cmg-space-3);
  border-top: 1px solid var(--cmg-border-light);
}

.cmg-recommended-label {
  font-size: var(--cmg-text-sm);
  color: var(--cmg-text-secondary);
  font-weight: 500;
  white-space: nowrap;
}

.cmg-segment-tag {
  cursor: pointer;
  transition: var(--cmg-transition-all);
}

.cmg-segment-tag:hover {
  transform: translateY(-1px);
  box-shadow: var(--cmg-shadow-sm);
}

/* 参数选择卡片 */
.cmg-metrics-card {
  margin-bottom: var(--cmg-space-4);
}

.cmg-metrics-content {
  display: flex;
  flex-direction: column;
  gap: var(--cmg-space-3);
}

.cmg-metric-option {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
}

.cmg-metrics-hint {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
  font-size: var(--cmg-text-xs);
  color: var(--cmg-text-tertiary);
  padding: var(--cmg-space-2) var(--cmg-space-3);
  background: var(--cmg-bg-tertiary);
  border-radius: var(--cmg-radius-base);
}

/* 图表卡片 */
.cmg-charts-card {
  margin-bottom: var(--cmg-space-4);
}

/* 寿命预测卡片 */
.cmg-lifetime-card {
  margin-bottom: var(--cmg-space-4);
}

.cmg-lifetime-actions {
  display: flex;
  gap: var(--cmg-space-2);
}

.cmg-lifetime-params {
  margin-bottom: var(--cmg-space-3);
}

.cmg-lifetime-param-row {
  margin-bottom: var(--cmg-space-2);
}

.cmg-lifetime-info {
  padding: var(--cmg-space-2) var(--cmg-space-3);
  background-color: #f0f9ff;
  border-radius: var(--cmg-radius-base);
  border-left: 3px solid #409eff;
}

.cmg-lifetime-param-item {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
}

.cmg-lifetime-param-item label {
  font-size: var(--cmg-text-sm);
  font-weight: 500;
  color: var(--cmg-text-primary);
  white-space: nowrap;
}

.lifetime-params-form {
  padding: var(--cmg-space-3);
}

.dialog-footer {
  text-align: right;
}

.cmg-lifetime-content {
  padding: var(--cmg-space-3);
}

.cmg-lifetime-result {
  display: flex;
  flex-direction: column;
  gap: var(--cmg-space-4);
}

.cmg-lifetime-result-simple {
  text-align: center;
  padding: var(--cmg-space-5);
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  border-radius: var(--cmg-radius-lg);
  color: white;
}

.cmg-lifetime-rul-main {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: var(--cmg-space-2);
  margin-bottom: var(--cmg-space-2);
}

.cmg-lifetime-rul-main .cmg-lifetime-rul-number {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}

.cmg-lifetime-rul-main .cmg-lifetime-rul-unit {
  font-size: 18px;
  font-weight: 500;
}

.cmg-lifetime-result-simple .cmg-lifetime-rul-label {
  font-size: 16px;
  margin-bottom: var(--cmg-space-3);
  opacity: 0.95;
}

.cmg-lifetime-prediction-time {
  font-size: 13px;
  opacity: 0.8;
}

.cmg-lifetime-rul-display {
  text-align: center;
  padding: var(--cmg-space-4);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: var(--cmg-radius-lg);
  color: white;
}

.cmg-lifetime-rul-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: var(--cmg-space-2);
  margin-bottom: var(--cmg-space-2);
}

.cmg-lifetime-rul-number {
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.cmg-lifetime-rul-unit {
  font-size: 16px;
  font-weight: 500;
}

.cmg-lifetime-rul-label {
  font-size: 14px;
  opacity: 0.9;
}

.cmg-lifetime-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--cmg-space-3);
}

.cmg-lifetime-detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--cmg-space-3) var(--cmg-space-4);
  background: var(--cmg-bg-tertiary);
  border-radius: var(--cmg-radius-base);
}

.cmg-lifetime-detail-item .label {
  font-weight: 500;
  color: var(--cmg-text-secondary);
}

.cmg-lifetime-detail-item .value {
  color: var(--cmg-text-primary);
  font-family: 'Courier New', monospace;
}

.cmg-lifetime-empty {
  padding: var(--cmg-space-4);
  text-align: center;
}

.cmg-lifetime-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--cmg-space-2);
  color: var(--cmg-text-tertiary);
  font-size: var(--cmg-text-sm);
}

.cmg-chart-actions {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-3);
}

.cmg-charts-container {
  max-height: 70vh;
  overflow-y: auto;
  padding: var(--cmg-space-4);
}

.cmg-chart-item {
  margin-bottom: var(--cmg-space-6);
  border: 1px solid var(--cmg-border-light);
  border-radius: var(--cmg-radius-lg);
  background: var(--cmg-bg-primary);
  overflow: hidden;
}

.cmg-chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--cmg-space-3) var(--cmg-space-4);
  background: var(--cmg-bg-tertiary);
  border-bottom: 1px solid var(--cmg-border-light);
}

.cmg-chart-title {
  margin: 0;
  font-size: var(--cmg-text-base);
  font-weight: 600;
  color: var(--cmg-text-primary);
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
}

.cmg-chart-controls {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
}

.cmg-chart-wrapper {
  position: relative;
}

.cmg-chart-box {
  width: 100%;
  height: 180px;
  background: var(--cmg-bg-primary);
}

.cmg-chart-live-indicator {
  position: absolute;
  top: var(--cmg-space-3);
  right: var(--cmg-space-3);
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
  padding: var(--cmg-space-1) var(--cmg-space-2);
  background: var(--cmg-success-50);
  border: 1px solid var(--cmg-aerospace-success);
  border-radius: var(--cmg-radius-full);
  font-size: var(--cmg-text-xs);
  color: var(--cmg-aerospace-success);
  font-weight: 500;
}

.cmg-realtime-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--cmg-radius-full);
  background: var(--cmg-aerospace-success);
  animation: pulse 2s infinite;
}

/* 结果面板网格 */
.cmg-results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--cmg-space-4);
  margin-top: var(--cmg-space-4);
}

@media (min-width: 1200px) {
  .cmg-results-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 768px) and (max-width: 1199px) {
  .cmg-results-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* IMS 卡片 */
.cmg-ims-card,
.cmg-rules-card,
.cmg-msfg-card,
.cmg-health-card {
  height: 400px;
}

.cmg-ims-actions,
.cmg-rules-actions {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-3);
}

.cmg-ims-content,
.cmg-rules-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.cmg-ims-list,
.cmg-rules-list {
  flex: 1;
  padding: var(--cmg-space-2);
}

.cmg-ims-item,
.cmg-rules-item {
  cursor: pointer;
  padding: var(--cmg-space-2);
  border-radius: var(--cmg-radius-base);
  transition: var(--cmg-transition-colors);
}

.cmg-ims-item:hover,
.cmg-rules-item:hover {
  background: var(--cmg-bg-tertiary);
}



.cmg-ims-item-header,
.cmg-rules-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--cmg-space-2);
  margin-bottom: var(--cmg-space-1);
}

.cmg-ims-score-tag {
  font-family: var(--cmg-font-mono);
  font-weight: 600;
}

.cmg-ims-model-name,
.cmg-rules-item-count {
  flex: 1;
  color: var(--cmg-text-secondary);
  font-size: var(--cmg-text-sm);
  display: flex;
  align-items: center;
  gap: var(--cmg-space-1);
}

.cmg-ims-item-param {
  color: var(--cmg-text-primary);
  font-size: var(--cmg-text-sm);
  display: flex;
  align-items: center;
  gap: var(--cmg-space-1);
  font-family: var(--cmg-font-mono);
}

.cmg-rules-item-health {
  color: var(--cmg-aerospace-warning);
  font-size: var(--cmg-text-xs);
  display: flex;
  align-items: center;
  gap: var(--cmg-space-1);
  margin-top: var(--cmg-space-1);
  font-style: italic;
}



.cmg-rule-name {
  font-family: var(--cmg-font-mono);
  color: var(--cmg-aerospace-primary);
  font-weight: 500;
}

.cmg-confidence-score {
  font-family: var(--cmg-font-mono);
  font-weight: 600;
}

.cmg-health-score-tag {
  font-family: var(--cmg-font-mono);
  font-weight: 600;
  min-width: 60px;
  text-align: center;
}

/* 规则帧详情对话框样式 */
.cmg-rules-frame-table {
  font-size: var(--cmg-text-sm);
}

.cmg-health-summary {
  margin-top: var(--cmg-space-3);
}

.cmg-health-card-mini {
  text-align: center;
  margin-bottom: var(--cmg-space-2);
}

.cmg-health-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--cmg-space-2);
}

.cmg-health-component {
  font-size: var(--cmg-text-xs);
  color: var(--cmg-text-secondary);
  font-weight: 500;
  text-align: center;
  line-height: 1.2;
}

/* 对比分析 */
.cmg-compare-card {
  margin-bottom: var(--cmg-space-4);
}
.cmg-compare-controls {
  display: flex;
  flex-direction: column;
  gap: var(--cmg-space-4);
  margin-bottom: var(--cmg-space-4);
  padding: var(--cmg-space-4);
  background: var(--cmg-bg-secondary);
  border-radius: var(--cmg-radius-lg);
}

.cmg-compare-row {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-4);
  flex-wrap: wrap;
}

.cmg-compare-item {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
  flex-wrap: wrap;
}

.cmg-compare-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--cmg-text-primary);
  white-space: nowrap;
  min-width: 80px;
}
.cmg-compare-chart {
  width: 100%;
  height: 360px;
  background: var(--cmg-bg-primary);
  border: 1px solid var(--cmg-border-light);
  border-radius: var(--cmg-radius-lg);
}

/* 对比分析时间轴样式 */
.cmg-compare-timeline {
  margin-top: var(--cmg-space-4);
  padding: var(--cmg-space-3);
  background: var(--cmg-bg-primary);
  border: 1px solid var(--cmg-border-light);
  border-radius: var(--cmg-radius-sm);
}

.cmg-compare-timeline-header {
  margin-bottom: var(--cmg-space-3);
}

.cmg-compare-timeline-label {
  font-weight: 600;
  color: var(--cmg-text-primary);
  font-size: var(--cmg-text-sm);
}

.cmg-compare-timeline-container {
  background: var(--cmg-bg-secondary);
  border: 1px solid var(--cmg-border-light);
  border-radius: var(--cmg-radius-sm);
  padding: var(--cmg-space-3);
  min-height: 60px;
}

.cmg-compare-timeline-track {
  position: relative;
  height: 30px;
  background: var(--cmg-gray-100);
  border-radius: var(--cmg-radius-sm);
  cursor: crosshair;
  border: 1px solid var(--cmg-border-light);
  overflow: hidden;
}

.cmg-compare-timeline-segment {
  position: absolute;
  height: 100%;
  background: linear-gradient(90deg, var(--cmg-aerospace-warning), var(--cmg-aerospace-warning-light));
  border-radius: var(--cmg-radius-sm);
  transition: all 0.2s ease;
  cursor: pointer;
}

.cmg-compare-timeline-segment:hover {
  background: linear-gradient(90deg, var(--cmg-aerospace-warning-dark), var(--cmg-aerospace-warning));
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.cmg-compare-timeline-selection {
  position: absolute;
  height: 100%;
  background: rgba(103, 194, 58, 0.3);
  border: 2px solid var(--cmg-aerospace-success);
  border-radius: var(--cmg-radius-sm);
  pointer-events: none;
  z-index: 10;
}

.cmg-compare-timeline-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 60px;
}

/* 暗色主题适配 */
[data-theme="dark"] .cmg-compare-timeline-track {
  background: var(--cmg-gray-800);
  border-color: var(--cmg-gray-700);
}

[data-theme="dark"] .cmg-compare-timeline-container {
  background: var(--cmg-gray-900);
  border-color: var(--cmg-gray-700);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .cmg-detail-page {
    padding: 0;
    padding-top: var(--cmg-space-3);
  }
  
  .cmg-toolbar-content {
    padding: var(--cmg-space-3) var(--cmg-space-4);
  }
  
  .cmg-filter-form :deep(.el-form-item) {
    margin-right: var(--cmg-space-2);
    margin-bottom: var(--cmg-space-2);
  }
  
  .cmg-recommended-segments {
    flex-direction: column;
    align-items: stretch;
    gap: var(--cmg-space-2);
  }
  
  .cmg-chart-actions {
    flex-direction: column;
    align-items: stretch;
    gap: var(--cmg-space-2);
  }
  
  .cmg-charts-container {
    padding: var(--cmg-space-2);
  }
  
  .cmg-chart-box {
    height: 200px;
  }
  
  .cmg-results-grid {
    grid-template-columns: 1fr;
    gap: var(--cmg-space-3);
  }
  
  .cmg-ims-card,
  .cmg-rules-card,
  .cmg-msfg-card,
  .cmg-health-card {
    height: 350px;
  }
}

@media (max-width: 640px) {
  .cmg-filter-form {
    flex-direction: column;
  }
  
  .cmg-filter-form :deep(.el-form-item) {
    margin-right: 0;
    width: 100%;
  }
  
  .cmg-chart-header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--cmg-space-2);
  }
}

/* MSFG 相关样式 */
.msfg-results-content {
  padding: var(--cmg-space-3);
}

.msfg-latest-summary h4,
.msfg-component-status h4,
.msfg-critical-faults h4,
.msfg-trend-chart h4,
.msfg-fault-inference h4 {
  margin: 0 0 var(--cmg-space-3) 0;
  color: var(--cmg-text-primary);
  font-size: var(--cmg-text-lg);
  font-weight: 600;
}

/* 故障部件推理样式 */
.risky-components-alert {
  background: linear-gradient(135deg, #f8f4f4, #fff5f5);
  border: 2px solid #f56c6c;
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
}

.alert-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  font-weight: bold;
  color: #f56c6c;
}

.alert-header .el-icon {
  margin-right: 8px;
}

.risky-components-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.risky-component-item {
  background: white;
  border: 1px solid #f56c6c;
  border-radius: 6px;
  padding: 12px;
  min-width: 200px;
  flex: 1;
}

.component-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.component-rank {
  background: #f56c6c;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  margin-right: 8px;
}

.component-details {
  font-size: 12px;
  color: #666;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.component-faults {
  margin-top: 8px;
}

.alert-suggestion {
  margin-top: 12px;
  padding: 8px;
  background: #fef0f0;
  border-radius: 4px;
  font-size: 12px;
  color: #f56c6c;
  display: flex;
  align-items: center;
}

.alert-suggestion .el-icon {
  margin-right: 4px;
}

.healthy-status {
  padding: 16px;
  text-align: center;
  background: #f0f9ff;
  border: 1px solid #67c23a;
  border-radius: 8px;
  margin-top: 12px;
  color: #67c23a;
  font-weight: bold;
}

.healthy-status .el-icon {
  margin-right: 8px;
}

.component-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--cmg-space-3);
  margin-top: var(--cmg-space-3);
}

.component-card {
  border: 1px solid var(--cmg-border-light);
  border-radius: var(--cmg-radius-md);
  padding: var(--cmg-space-3);
  background: var(--cmg-bg-primary);
  transition: all 0.3s ease;
}

.component-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.component-card.component-healthy {
  border-left: 4px solid var(--cmg-aerospace-success);
}

.component-card.component-warning {
  border-left: 4px solid var(--cmg-aerospace-warning);
}

.component-card.component-danger {
  border-left: 4px solid var(--cmg-aerospace-danger);
}

.component-name {
  font-weight: 600;
  color: var(--cmg-text-primary);
  margin-bottom: var(--cmg-space-2);
}

.component-score {
  font-size: var(--cmg-text-xl);
  font-weight: 700;
  font-family: var(--cmg-font-mono);
  margin-bottom: var(--cmg-space-2);
}

.component-status {
  margin-bottom: var(--cmg-space-2);
}

.component-faults {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-1);
  color: var(--cmg-aerospace-danger);
  font-size: var(--cmg-text-sm);
}

.msfg-critical-faults {
  margin-top: var(--cmg-space-4);
}

.msfg-trend-chart {
  margin-top: var(--cmg-space-4);
  border: 1px solid var(--cmg-border-light);
  border-radius: var(--cmg-radius-md);
  background: var(--cmg-bg-primary);
}

/* 时间轴样式 */
.cmg-time-controls {
  margin-top: var(--cmg-space-4);
  padding: var(--cmg-space-4);
  background: var(--cmg-bg-secondary);
  border-radius: var(--cmg-radius-md);
  border: 1px solid var(--cmg-border-light);
}

.cmg-timeline-section {
  margin-bottom: var(--cmg-space-4);
}

.cmg-timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--cmg-space-3);
}

.cmg-timeline-label {
  font-weight: 600;
  color: var(--cmg-text-primary);
  font-size: var(--cmg-text-sm);
}

.cmg-timeline-container {
  background: var(--cmg-bg-primary);
  border: 1px solid var(--cmg-border-light);
  border-radius: var(--cmg-radius-sm);
  padding: var(--cmg-space-3);
  min-height: 80px;
}

.cmg-timeline {
  position: relative;
  width: 100%;
}

.cmg-timeline-track {
  position: relative;
  height: 40px;
  background: var(--cmg-gray-100);
  border-radius: var(--cmg-radius-sm);
  cursor: crosshair;
  border: 1px solid var(--cmg-border-light);
  overflow: hidden;
}

.cmg-timeline-segment {
  position: absolute;
  height: 100%;
  background: linear-gradient(90deg, var(--cmg-aerospace-primary), var(--cmg-aerospace-primary-light));
  border-radius: var(--cmg-radius-sm);
  transition: all 0.2s ease;
  cursor: pointer;
}

.cmg-timeline-segment:hover {
  background: linear-gradient(90deg, var(--cmg-aerospace-primary-dark), var(--cmg-aerospace-primary));
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.cmg-timeline-selection {
  position: absolute;
  height: 100%;
  background: rgba(103, 194, 58, 0.3);
  border: 2px solid var(--cmg-aerospace-success);
  border-radius: var(--cmg-radius-sm);
  pointer-events: none;
  z-index: 10;
}

.cmg-timeline-labels {
  display: flex;
  justify-content: space-between;
  margin-top: var(--cmg-space-2);
  font-size: var(--cmg-text-xs);
  color: var(--cmg-text-secondary);
}

.cmg-timeline-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 80px;
}

.cmg-recommended-segments {
  margin-top: var(--cmg-space-3);
}

.cmg-recommended-label {
  font-weight: 600;
  color: var(--cmg-text-primary);
  font-size: var(--cmg-text-sm);
  margin-bottom: var(--cmg-space-2);
  display: block;
}

.cmg-segment-tag {
  cursor: pointer;
  transition: all 0.2s ease;
}

.cmg-segment-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* 暗色主题适配 */
[data-theme="dark"] .cmg-timeline-track {
  background: var(--cmg-gray-800);
  border-color: var(--cmg-gray-700);
}

[data-theme="dark"] .cmg-timeline-segment {
  background: linear-gradient(90deg, var(--cmg-aerospace-primary), var(--cmg-aerospace-primary-light));
}

[data-theme="dark"] .cmg-timeline-segment:hover {
  background: linear-gradient(90deg, var(--cmg-aerospace-primary-dark), var(--cmg-aerospace-primary));
}

[data-theme="dark"] .cmg-timeline-container {
  background: var(--cmg-gray-900);
  border-color: var(--cmg-gray-700);
}</style>
