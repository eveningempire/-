// ECharts 主题配置 - CMG 健康管理平台
import * as echarts from 'echarts';

// 获取 CSS 变量值
function getCSSVariable(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// 航天科研风格主题
const cmgTheme = {
  color: [
    '#1890ff', // 主蓝色
    '#13c2c2', // 青绿色
    '#52c41a', // 成功绿
    '#faad14', // 警告橙
    '#f5222d', // 危险红
    '#722ed1', // 紫色
    '#eb2f96', // 粉色
    '#fa541c', // 橙色
    '#a0d911', // 青色
    '#1890ff'  // 循环回主色
  ],
  backgroundColor: 'transparent',
  textStyle: {},
  title: {
    textStyle: {
      color: '#303133',
      fontSize: 18,
      fontWeight: 600
    },
    subtextStyle: {
      color: '#606266',
      fontSize: 12
    }
  },
  line: {
    itemStyle: {
      borderWidth: 2
    },
    lineStyle: {
      width: 2
    },
    symbolSize: 4,
    symbol: 'circle',
    smooth: false
  },
  radar: {
    itemStyle: {
      borderWidth: 2
    },
    lineStyle: {
      width: 2
    },
    symbolSize: 4,
    symbol: 'circle',
    smooth: false
  },
  bar: {
    itemStyle: {
      barBorderWidth: 0,
      barBorderColor: '#ccc'
    }
  },
  pie: {
    itemStyle: {
      borderWidth: 0,
      borderColor: '#ccc'
    }
  },
  scatter: {
    itemStyle: {
      borderWidth: 0,
      borderColor: '#ccc'
    }
  },
  boxplot: {
    itemStyle: {
      borderWidth: 0,
      borderColor: '#ccc'
    }
  },
  parallel: {
    itemStyle: {
      borderWidth: 0,
      borderColor: '#ccc'
    }
  },
  sankey: {
    itemStyle: {
      borderWidth: 0,
      borderColor: '#ccc'
    }
  },
  funnel: {
    itemStyle: {
      borderWidth: 0,
      borderColor: '#ccc'
    }
  },
  gauge: {
    itemStyle: {
      borderWidth: 0,
      borderColor: '#ccc'
    }
  },
  candlestick: {
    itemStyle: {
      color: '#52c41a',
      color0: '#f5222d',
      borderColor: '#52c41a',
      borderColor0: '#f5222d',
      borderWidth: 1
    }
  },
  graph: {
    itemStyle: {
      borderWidth: 0,
      borderColor: '#ccc'
    },
    lineStyle: {
      width: 1,
      color: '#aaa'
    },
    symbolSize: 4,
    symbol: 'circle',
    smooth: false,
    color: [
      '#1890ff',
      '#13c2c2',
      '#52c41a',
      '#faad14',
      '#f5222d'
    ],
    label: {
      color: '#303133'
    }
  },
  map: {
    itemStyle: {
      areaColor: '#eee',
      borderColor: '#444',
      borderWidth: 0.5
    },
    label: {
      color: '#000'
    },
    emphasis: {
      itemStyle: {
        areaColor: 'rgba(255,215,0,0.8)',
        borderColor: '#444',
        borderWidth: 1
      },
      label: {
        color: 'rgb(100,0,0)'
      }
    }
  },
  geo: {
    itemStyle: {
      areaColor: '#eee',
      borderColor: '#444',
      borderWidth: 0.5
    },
    label: {
      color: '#000'
    },
    emphasis: {
      itemStyle: {
        areaColor: 'rgba(255,215,0,0.8)',
        borderColor: '#444',
        borderWidth: 1
      },
      label: {
        color: 'rgb(100,0,0)'
      }
    }
  },
  categoryAxis: {
    axisLine: {
      show: true,
      lineStyle: {
        color: '#e0e6ed'
      }
    },
    axisTick: {
      show: true,
      lineStyle: {
        color: '#e0e6ed'
      }
    },
    axisLabel: {
      show: true,
      color: '#606266',
      fontSize: 12
    },
    splitLine: {
      show: false,
      lineStyle: {
        color: ['#f0f2f5']
      }
    },
    splitArea: {
      show: false,
      areaStyle: {
        color: ['rgba(250,250,250,0.3)', 'rgba(200,200,200,0.3)']
      }
    }
  },
  valueAxis: {
    axisLine: {
      show: false,
      lineStyle: {
        color: '#e0e6ed'
      }
    },
    axisTick: {
      show: false,
      lineStyle: {
        color: '#e0e6ed'
      }
    },
    axisLabel: {
      show: true,
      color: '#606266',
      fontSize: 12
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: ['#f0f2f5'],
        type: 'dashed',
        opacity: 0.6
      }
    },
    splitArea: {
      show: false,
      areaStyle: {
        color: ['rgba(250,250,250,0.3)', 'rgba(200,200,200,0.3)']
      }
    }
  },
  logAxis: {
    axisLine: {
      show: false,
      lineStyle: {
        color: '#e0e6ed'
      }
    },
    axisTick: {
      show: false,
      lineStyle: {
        color: '#e0e6ed'
      }
    },
    axisLabel: {
      show: true,
      color: '#606266',
      fontSize: 12
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: ['#f0f2f5'],
        type: 'dashed'
      }
    },
    splitArea: {
      show: false,
      areaStyle: {
        color: ['rgba(250,250,250,0.3)', 'rgba(200,200,200,0.3)']
      }
    }
  },
  timeAxis: {
    axisLine: {
      show: true,
      lineStyle: {
        color: '#e0e6ed'
      }
    },
    axisTick: {
      show: true,
      lineStyle: {
        color: '#e0e6ed'
      }
    },
    axisLabel: {
      show: true,
      color: '#606266',
      fontSize: 12
    },
    splitLine: {
      show: false,
      lineStyle: {
        color: ['#f0f2f5']
      }
    },
    splitArea: {
      show: false,
      areaStyle: {
        color: ['rgba(250,250,250,0.3)', 'rgba(200,200,200,0.3)']
      }
    }
  },
  toolbox: {
    color: ['#606266', '#606266', '#606266', '#606266'],
    emphasis: {
      color: ['#1890ff', '#1890ff', '#1890ff', '#1890ff']
    }
  },
  legend: {
    textStyle: {
      color: '#606266',
      fontSize: 12
    }
  },
  tooltip: {
    axisPointer: {
      lineStyle: {
        color: '#1890ff',
        width: 1
      },
      crossStyle: {
        color: '#1890ff',
        width: 1
      }
    }
  },
  timeline: {
    lineStyle: {
      color: '#1890ff',
      width: 1
    },
    itemStyle: {
      color: '#1890ff',
      borderWidth: 1
    },
    controlStyle: {
      color: '#1890ff',
      borderColor: '#1890ff',
      borderWidth: 0.5
    },
    checkpointStyle: {
      color: '#1890ff',
      borderColor: '#ffffff'
    },
    label: {
      color: '#1890ff'
    },
    emphasis: {
      itemStyle: {
        color: '#13c2c2'
      },
      controlStyle: {
        color: '#1890ff',
        borderColor: '#1890ff',
        borderWidth: 0.5
      },
      label: {
        color: '#1890ff'
      }
    }
  },
  visualMap: {
    color: ['#f5222d', '#faad14', '#52c41a']
  },
  dataZoom: {
    backgroundColor: 'rgba(255,255,255,0)',
    dataBackgroundColor: 'rgba(24,144,255,0.3)',
    fillerColor: 'rgba(24,144,255,0.2)',
    handleColor: '#1890ff',
    handleSize: '100%',
    textStyle: {
      color: '#606266'
    }
  },
  markPoint: {
    label: {
      color: '#303133'
    },
    emphasis: {
      label: {
        color: '#303133'
      }
    }
  }
};

// 暗色主题
const cmgDarkTheme = {
  ...cmgTheme,
  backgroundColor: 'transparent',
  textStyle: {
    color: '#e2e8f0'
  },
  title: {
    textStyle: {
      color: '#e2e8f0',
      fontSize: 18,
      fontWeight: 600
    },
    subtextStyle: {
      color: '#94a3b8',
      fontSize: 12
    }
  },
  categoryAxis: {
    ...cmgTheme.categoryAxis,
    axisLine: {
      show: true,
      lineStyle: {
        color: '#475569'
      }
    },
    axisTick: {
      show: true,
      lineStyle: {
        color: '#475569'
      }
    },
    axisLabel: {
      show: true,
      color: '#94a3b8',
      fontSize: 12
    },
    splitLine: {
      show: false,
      lineStyle: {
        color: ['#334155']
      }
    }
  },
  valueAxis: {
    ...cmgTheme.valueAxis,
    axisLine: {
      show: false,
      lineStyle: {
        color: '#475569'
      }
    },
    axisTick: {
      show: false,
      lineStyle: {
        color: '#475569'
      }
    },
    axisLabel: {
      show: true,
      color: '#94a3b8',
      fontSize: 12
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: ['#334155'],
        type: 'dashed',
        opacity: 0.6
      }
    }
  },
  timeAxis: {
    ...cmgTheme.timeAxis,
    axisLine: {
      show: true,
      lineStyle: {
        color: '#475569'
      }
    },
    axisTick: {
      show: true,
      lineStyle: {
        color: '#475569'
      }
    },
    axisLabel: {
      show: true,
      color: '#94a3b8',
      fontSize: 12
    },
    splitLine: {
      show: false,
      lineStyle: {
        color: ['#334155']
      }
    }
  },
  legend: {
    textStyle: {
      color: '#94a3b8',
      fontSize: 12
    }
  },
  toolbox: {
    color: ['#94a3b8', '#94a3b8', '#94a3b8', '#94a3b8'],
    emphasis: {
      color: ['#40a9ff', '#40a9ff', '#40a9ff', '#40a9ff']
    }
  },
  dataZoom: {
    ...cmgTheme.dataZoom,
    textStyle: {
      color: '#94a3b8'
    }
  }
};

// 注册主题
export function registerChartThemes() {
  echarts.registerTheme('cmg-light', cmgTheme);
  echarts.registerTheme('cmg-dark', cmgDarkTheme);
}

// 获取当前主题名称
export function getCurrentTheme() {
  const theme = document.documentElement.getAttribute('data-theme');
  return theme === 'dark' ? 'cmg-dark' : 'cmg-light';
}

// 创建图表实例的统一方法
export function createChart(container, options = {}) {
  const theme = getCurrentTheme();
  const chart = echarts.init(container, theme, {
    renderer: 'canvas',
    useDirtyRect: true,
    ...options
  });
  
  // 监听主题变化
  const handleThemeChange = () => {
    const newTheme = getCurrentTheme();
    chart.dispose();
    const newChart = echarts.init(container, newTheme, options);
    return newChart;
  };
  
  // 添加主题变化监听器
  window.addEventListener('theme-change', handleThemeChange);
  
  // 返回图表实例和清理函数
  return {
    chart,
    dispose: () => {
      window.removeEventListener('theme-change', handleThemeChange);
      chart.dispose();
    }
  };
}

// 异常标注配置
export const anomalyMarkConfig = {
  // 异常点标记
  markPoint: {
    symbol: 'circle',
    symbolSize: 8,
    itemStyle: {
      color: '#ff4d4f',
      borderColor: '#ffffff',
      borderWidth: 2,
      shadowColor: 'rgba(255, 77, 79, 0.5)',
      shadowBlur: 4
    },
    label: {
      show: false
    },
    emphasis: {
      itemStyle: {
        color: '#ff7875',
        shadowBlur: 8
      },
      label: {
        show: true,
        position: 'top',
        formatter: '异常',
        color: '#ff4d4f',
        fontSize: 12,
        fontWeight: 'bold'
      }
    }
  },
  
  // 异常区域标记
  markArea: {
    itemStyle: {
      color: 'rgba(255, 77, 79, 0.1)',
      borderColor: '#ff4d4f',
      borderWidth: 1,
      borderType: 'dashed'
    },
    emphasis: {
      itemStyle: {
        color: 'rgba(255, 77, 79, 0.2)'
      }
    },
    label: {
      show: true,
      position: 'top',
      color: '#ff4d4f',
      fontSize: 12,
      fontWeight: 'bold'
    }
  },
  
  // 异常线标记
  markLine: {
    lineStyle: {
      color: '#ff4d4f',
      width: 2,
      type: 'dashed'
    },
    label: {
      show: true,
      position: 'end',
      color: '#ff4d4f',
      fontSize: 12,
      fontWeight: 'bold'
    }
  }
};

// 添加异常标注的辅助函数
export function addAnomalyMarks(option, anomalies = []) {
  if (!anomalies || anomalies.length === 0) return option;
  
  // 为每个系列添加异常标注
  if (option.series) {
    option.series.forEach((series, index) => {
      if (series.type === 'line' || series.type === 'scatter') {
        // 添加异常点标记
        const anomalyPoints = anomalies
          .filter(anomaly => anomaly.seriesIndex === index || anomaly.seriesIndex === undefined)
          .map(anomaly => ({
            coord: [anomaly.timestamp, anomaly.value],
            name: `异常: ${anomaly.score?.toFixed(3) || 'N/A'}`,
            value: anomaly.score || 0,
            itemStyle: {
              color: getAnomalySeverityColor(anomaly.score)
            }
          }));
        
        if (anomalyPoints.length > 0) {
          series.markPoint = {
            ...anomalyMarkConfig.markPoint,
            data: anomalyPoints
          };
        }
        
        // 添加异常区域标记（如果有时间范围）
        const anomalyAreas = anomalies
          .filter(anomaly => anomaly.startTime && anomaly.endTime)
          .map(anomaly => [
            { xAxis: anomaly.startTime },
            { xAxis: anomaly.endTime }
          ]);
        
        if (anomalyAreas.length > 0) {
          series.markArea = {
            ...anomalyMarkConfig.markArea,
            data: anomalyAreas
          };
        }
      }
    });
  }
  
  return option;
}

// 根据异常严重程度获取颜色
export function getAnomalySeverityColor(score) {
  if (score >= 0.8) return '#ff4d4f'; // 严重异常 - 红色
  if (score >= 0.6) return '#faad14'; // 中等异常 - 橙色
  if (score >= 0.4) return '#1890ff'; // 轻微异常 - 蓝色
  return '#52c41a'; // 正常 - 绿色
}

// 图表联动配置
export const chartLinkageConfig = {
  // 数据缩放联动
  connectDataZoom: true,
  
  // 工具箱配置
  toolbox: {
    show: true,
    orient: 'horizontal',
    left: 'right',
    top: 'top',
    feature: {
      dataZoom: {
        show: true,
        title: {
          zoom: '区域缩放',
          back: '缩放还原'
        }
      },
      restore: {
        show: true,
        title: '还原'
      },
      saveAsImage: {
        show: true,
        title: '保存为图片',
        type: 'png',
        backgroundColor: 'white'
      }
    },
    iconStyle: {
      borderColor: '#606266'
    },
    emphasis: {
      iconStyle: {
        borderColor: '#1890ff'
      }
    }
  }
};

// 响应式图表配置
export function getResponsiveOption(baseOption, containerWidth) {
  const isMobile = containerWidth < 768;
  const isTablet = containerWidth >= 768 && containerWidth < 1024;
  
  const responsiveOption = { ...baseOption };
  
  if (isMobile) {
    // 移动端适配
    responsiveOption.grid = {
      ...responsiveOption.grid,
      left: '10%',
      right: '5%',
      top: '15%',
      bottom: '15%'
    };
    
    if (responsiveOption.legend) {
      responsiveOption.legend = {
        ...responsiveOption.legend,
        orient: 'horizontal',
        bottom: 0,
        left: 'center',
        textStyle: {
          fontSize: 10
        }
      };
    }
    
    if (responsiveOption.toolbox) {
      responsiveOption.toolbox.show = false;
    }
  } else if (isTablet) {
    // 平板端适配
    responsiveOption.grid = {
      ...responsiveOption.grid,
      left: '8%',
      right: '8%',
      top: '12%',
      bottom: '12%'
    };
  }
  
  return responsiveOption;
}

// 初始化图表主题系统
export function initChartTheme() {
  registerChartThemes();
  
  // 监听主题变化，重新渲染所有图表
  window.addEventListener('theme-change', () => {
    // 获取所有 echarts 实例并重新设置主题
    echarts.getInstanceByDom && echarts.dispose();
  });
}

export default {
  registerChartThemes,
  getCurrentTheme,
  createChart,
  addAnomalyMarks,
  getAnomalySeverityColor,
  chartLinkageConfig,
  getResponsiveOption,
  initChartTheme
};
