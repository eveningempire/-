// 图表与表格协同联动 composable
import { ref, computed, nextTick, onUnmounted } from 'vue';
import * as echarts from 'echarts';

/**
 * 图表与表格协同联动功能
 * 
 * 主要功能：
 * 1. 点击表格记录，图表自动定位并高亮对应时间点
 * 2. 图表框选时间区间时，同步更新表格筛选
 * 3. 图表缩放时，表格也会相应筛选数据
 * 4. 表格排序/筛选时，图表数据同步更新
 */
export function useChartTableSync(options = {}) {
  const {
    // 图表容器或实例的引用
    chartInstances = {},
    // 表格数据
    tableData = [],
    // 时间字段名
    timestampField = 'timestamp',
    // 联动选项
    enableHighlight = true,
    enableZoomSync = true,
    enableFilterSync = true,
    // 防抖延迟
    debounceDelay = 100
  } = options;

  // 状态管理
  const selectedTimeRange = ref(null);
  const selectedDataPoint = ref(null);
  const highlightedRows = ref(new Set());
  const chartSyncEnabled = ref(true);
  const tableSyncEnabled = ref(true);

  // 防抖定时器
  let debounceTimer = null;

  // 计算属性：过滤后的表格数据
  const filteredTableData = computed(() => {
    if (!selectedTimeRange.value || !tableSyncEnabled.value) {
      return tableData.value || tableData;
    }

    const [startTime, endTime] = selectedTimeRange.value;
    return (tableData.value || tableData).filter(row => {
      const timestamp = new Date(row[timestampField]).getTime();
      return timestamp >= startTime && timestamp <= endTime;
    });
  });

  // 图表高亮配置
  const highlightConfig = {
    emphasis: {
      itemStyle: {
        color: '#ff4d4f',
        borderColor: '#ffffff',
        borderWidth: 3,
        shadowColor: 'rgba(255, 77, 79, 0.6)',
        shadowBlur: 8
      },
      label: {
        show: true,
        formatter: '{b}\n{c}',
        position: 'top',
        color: '#ff4d4f',
        fontWeight: 'bold'
      }
    }
  };

  // 防抖执行函数
  function debounce(func, delay = debounceDelay) {
    return function(...args) {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => func.apply(this, args), delay);
    };
  }

  // 1. 表格行点击事件：高亮对应的图表数据点
  function handleTableRowClick(row, column, event) {
    if (!chartSyncEnabled.value || !row) return;

    const timestamp = new Date(row[timestampField]).getTime();
    selectedDataPoint.value = {
      timestamp,
      row: { ...row },
      index: (tableData.value || tableData).indexOf(row)
    };

    // 高亮所有图表中的对应数据点
    highlightChartPoint(timestamp, row);
    
    // 滚动到对应时间位置
    scrollChartsToTime(timestamp);

    // 触发自定义事件
    emitSyncEvent('table-row-select', {
      row,
      timestamp,
      chartPoint: selectedDataPoint.value
    });
  }

  // 2. 图表数据点点击事件：高亮对应的表格行
  function handleChartPointClick(params) {
    if (!tableSyncEnabled.value || !params.value) return;

    const timestamp = params.value[0]; // 假设第一个值是时间戳
    const matchedRows = (tableData.value || tableData).filter(row => {
      const rowTime = new Date(row[timestampField]).getTime();
      // 允许一定的时间误差（比如1秒）
      return Math.abs(rowTime - timestamp) < 1000;
    });

    if (matchedRows.length > 0) {
      const targetRow = matchedRows[0];
      selectedDataPoint.value = {
        timestamp,
        row: { ...targetRow },
        chartParams: params
      };

      // 高亮表格行
      highlightTableRows([targetRow]);

      // 滚动表格到对应行
      scrollTableToRow(targetRow);

      emitSyncEvent('chart-point-select', {
        params,
        timestamp,
        matchedRows
      });
    }
  }

  // 3. 图表区域选择/缩放事件：筛选表格数据
  function handleChartDataZoom(params) {
    if (!tableSyncEnabled.value) return;

    const batch = params.batch || [params];
    const xAxisZoom = batch.find(item => item.dataZoomId && item.dataZoomId.includes('x'));
    
    if (xAxisZoom) {
      const { start, end } = xAxisZoom;
      const totalData = tableData.value || tableData;
      
      if (totalData.length > 0) {
        const sortedData = [...totalData].sort((a, b) => 
          new Date(a[timestampField]).getTime() - new Date(b[timestampField]).getTime()
        );
        
        const startIndex = Math.floor(start / 100 * sortedData.length);
        const endIndex = Math.floor(end / 100 * sortedData.length);
        
        const startTime = new Date(sortedData[startIndex][timestampField]).getTime();
        const endTime = new Date(sortedData[Math.min(endIndex, sortedData.length - 1)][timestampField]).getTime();
        
        selectedTimeRange.value = [startTime, endTime];

        emitSyncEvent('chart-zoom', {
          timeRange: selectedTimeRange.value,
          startIndex,
          endIndex,
          filteredData: filteredTableData.value
        });
      }
    }
  }

  // 4. 图表框选事件：筛选表格数据
  function handleChartBrush(params) {
    if (!tableSyncEnabled.value || !params.areas || params.areas.length === 0) return;

    const area = params.areas[0];
    const { range } = area;
    
    if (range && range.length >= 2) {
      const [startTime, endTime] = range.sort((a, b) => a - b);
      selectedTimeRange.value = [startTime, endTime];

      emitSyncEvent('chart-brush', {
        timeRange: selectedTimeRange.value,
        area,
        filteredData: filteredTableData.value
      });
    }
  }

  // 高亮图表中的数据点
  function highlightChartPoint(timestamp, row) {
    Object.values(chartInstances.value || chartInstances).forEach(chart => {
      if (!chart || typeof chart.dispatchAction !== 'function') return;

      try {
        // 取消之前的高亮
        chart.dispatchAction({
          type: 'downplay',
          seriesIndex: 'all'
        });

        // 找到匹配的数据点并高亮
        const option = chart.getOption();
        if (option && option.series) {
          option.series.forEach((series, seriesIndex) => {
            if (series.data) {
              series.data.forEach((point, pointIndex) => {
                if (Array.isArray(point) && Math.abs(point[0] - timestamp) < 1000) {
                  chart.dispatchAction({
                    type: 'highlight',
                    seriesIndex,
                    dataIndex: pointIndex
                  });
                }
              });
            }
          });
        }
      } catch (error) {
        console.warn('Failed to highlight chart point:', error);
      }
    });
  }

  // 高亮表格行
  function highlightTableRows(rows) {
    highlightedRows.value.clear();
    rows.forEach(row => {
      const index = (tableData.value || tableData).indexOf(row);
      if (index !== -1) {
        highlightedRows.value.add(index);
      }
    });
  }

  // 滚动图表到指定时间
  function scrollChartsToTime(timestamp) {
    Object.values(chartInstances.value || chartInstances).forEach(chart => {
      if (!chart || typeof chart.dispatchAction !== 'function') return;

      try {
        // 计算时间在数据中的百分比位置
        const option = chart.getOption();
        if (option && option.series && option.series[0] && option.series[0].data) {
          const data = option.series[0].data;
          const timestamps = data.map(point => Array.isArray(point) ? point[0] : point.value[0]);
          const minTime = Math.min(...timestamps);
          const maxTime = Math.max(...timestamps);
          
          if (maxTime > minTime) {
            const position = ((timestamp - minTime) / (maxTime - minTime)) * 100;
            const zoomSize = 10; // 缩放窗口大小（百分比）
            
            chart.dispatchAction({
              type: 'dataZoom',
              start: Math.max(0, position - zoomSize / 2),
              end: Math.min(100, position + zoomSize / 2)
            });
          }
        }
      } catch (error) {
        console.warn('Failed to scroll chart to time:', error);
      }
    });
  }

  // 滚动表格到指定行
  function scrollTableToRow(targetRow) {
    // 这个需要与具体的表格组件集成
    // 可以通过表格组件的 ref 调用 scrollToRow 或类似方法
    nextTick(() => {
      emitSyncEvent('table-scroll-to', { targetRow });
    });
  }

  // 设置图表实例的事件监听
  function setupChartEventListeners(chartInstance, chartKey) {
    if (!chartInstance || typeof chartInstance.on !== 'function') return;

    // 数据点点击事件
    chartInstance.on('click', debounce(handleChartPointClick));
    
    // 数据缩放事件
    chartInstance.on('datazoom', debounce(handleChartDataZoom));
    
    // 框选事件
    chartInstance.on('brush', debounce(handleChartBrush));
    
    // 鼠标悬停事件（可选）
    chartInstance.on('mouseover', (params) => {
      if (enableHighlight) {
        // 可以添加悬停高亮逻辑
      }
    });
  }

  // 移除图表事件监听
  function removeChartEventListeners(chartInstance) {
    if (!chartInstance || typeof chartInstance.off !== 'function') return;

    chartInstance.off('click');
    chartInstance.off('datazoom');
    chartInstance.off('brush');
    chartInstance.off('mouseover');
  }

  // 批量设置图表监听器
  function setupAllChartListeners() {
    Object.entries(chartInstances.value || chartInstances).forEach(([key, chart]) => {
      setupChartEventListeners(chart, key);
    });
  }

  // 批量移除图表监听器
  function removeAllChartListeners() {
    Object.values(chartInstances.value || chartInstances).forEach(chart => {
      removeChartEventListeners(chart);
    });
  }

  // 清除所有选择和高亮
  function clearSelection() {
    selectedTimeRange.value = null;
    selectedDataPoint.value = null;
    highlightedRows.value.clear();

    // 清除图表高亮
    Object.values(chartInstances.value || chartInstances).forEach(chart => {
      if (chart && typeof chart.dispatchAction === 'function') {
        try {
          chart.dispatchAction({
            type: 'downplay',
            seriesIndex: 'all'
          });
        } catch (error) {
          console.warn('Failed to clear chart highlight:', error);
        }
      }
    });

    emitSyncEvent('selection-clear', {});
  }

  // 事件发射器
  const eventCallbacks = {};
  
  function emitSyncEvent(eventName, data) {
    if (eventCallbacks[eventName]) {
      eventCallbacks[eventName].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in sync event callback for ${eventName}:`, error);
        }
      });
    }
  }

  function onSyncEvent(eventName, callback) {
    if (!eventCallbacks[eventName]) {
      eventCallbacks[eventName] = [];
    }
    eventCallbacks[eventName].push(callback);
    
    // 返回取消监听的函数
    return () => {
      const index = eventCallbacks[eventName].indexOf(callback);
      if (index > -1) {
        eventCallbacks[eventName].splice(index, 1);
      }
    };
  }

  // 同步图表和表格的数据缩放范围
  function syncDataZoomRange(startPercent, endPercent) {
    Object.values(chartInstances.value || chartInstances).forEach(chart => {
      if (chart && typeof chart.dispatchAction === 'function') {
        try {
          chart.dispatchAction({
            type: 'dataZoom',
            start: startPercent,
            end: endPercent
          });
        } catch (error) {
          console.warn('Failed to sync data zoom:', error);
        }
      }
    });
  }

  // 获取当前选择的状态
  function getSelectionState() {
    return {
      selectedTimeRange: selectedTimeRange.value,
      selectedDataPoint: selectedDataPoint.value,
      highlightedRows: Array.from(highlightedRows.value),
      filteredData: filteredTableData.value
    };
  }

  // 应用表格筛选到图表
  function applyTableFilterToCharts(filterConfig) {
    if (!chartSyncEnabled.value) return;

    // 根据筛选配置更新图表数据显示
    Object.values(chartInstances.value || chartInstances).forEach(chart => {
      if (!chart || typeof chart.setOption !== 'function') return;

      try {
        const option = chart.getOption();
        if (option && option.series) {
          // 应用筛选逻辑到图表数据
          // 这里可以根据具体需求实现筛选逻辑
          chart.setOption(option, { notMerge: false });
        }
      } catch (error) {
        console.warn('Failed to apply table filter to chart:', error);
      }
    });
  }

  // 清理函数
  function cleanup() {
    clearTimeout(debounceTimer);
    removeAllChartListeners();
    Object.keys(eventCallbacks).forEach(key => {
      eventCallbacks[key] = [];
    });
  }

  // 组件卸载时清理
  onUnmounted(() => {
    cleanup();
  });

  return {
    // 状态
    selectedTimeRange,
    selectedDataPoint,
    highlightedRows,
    filteredTableData,
    chartSyncEnabled,
    tableSyncEnabled,

    // 方法
    handleTableRowClick,
    handleChartPointClick,
    handleChartDataZoom,
    handleChartBrush,
    setupChartEventListeners,
    removeChartEventListeners,
    setupAllChartListeners,
    removeAllChartListeners,
    clearSelection,
    syncDataZoomRange,
    applyTableFilterToCharts,

    // 事件系统
    onSyncEvent,
    emitSyncEvent,

    // 工具方法
    getSelectionState,
    cleanup,

    // 配置方法
    setChartSyncEnabled: (enabled) => { chartSyncEnabled.value = enabled; },
    setTableSyncEnabled: (enabled) => { tableSyncEnabled.value = enabled; },
    
    // 高级功能
    highlightChartPoint,
    highlightTableRows,
    scrollChartsToTime,
    scrollTableToRow
  };
}