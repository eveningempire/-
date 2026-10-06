// 图表相关功能
export const chartUtils = {
    // 初始化基本图表区域
    initZone(ref, title, timeData, data, dataName, markLineData, visualConfig) {
        // 确保能获取到DOM引用
        let chartElement;
        if (Array.isArray(ref)) {
            chartElement = ref[0];
        } else {
            chartElement = ref;
        }

        // 创建图表实例
        const chart = echarts.init(chartElement);
        
        // 基本配置
        let options = {
            title: {
                text: title,
                textStyle: {
                    color: "#096dd9",
                    fontSize: 18,
                    fontWeight: 'normal'
                },
                left: '1%'
            },
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                borderColor: '#40a9ff',
                textStyle: {
                    color: '#2c3e50'
                },
                axisPointer: {
                    type: 'line',
                    lineStyle: {
                        color: '#1890ff'
                    }
                }
            },
            grid: {
                left: '10%',
                right: '25%',
                bottom: '25%'
            },
            toolbox: {
                right: 10,
                feature: {
                    dataZoom: {
                        yAxisIndex: 'none',
                        iconStyle: {
                            borderColor: '#1890ff'
                        }
                    },
                    restore: {
                        iconStyle: {
                            borderColor: '#1890ff'
                        }
                    },
                    saveAsImage: {
                        iconStyle: {
                            borderColor: '#1890ff'
                        }
                    }
                }
            },
            dataZoom: [
                {
                    backgroundColor: '#f0f5ff',
                    dataBackgroundColor: '#bae7ff',
                    fillerColor: 'rgba(64, 169, 255, 0.2)',
                    handleColor: '#1890ff',
                    handleStyle: {
                        borderColor: '#1890ff'
                    },
                    textStyle: {
                        color: '#2c3e50'
                    }
                },
                {
                    type: 'inside'
                }
            ],
        };

        // 根据数据类型设置不同的配置
        if (dataName) {
            options.series = {
                name: dataName,
                type: 'line',
                data: data,
                lineStyle: {
                    color: '#1890ff',
                    width: 2
                },
                itemStyle: {
                    color: '#1890ff'
                }
            };
            options.xAxis = {
                name: '测试日期',
                data: timeData,
                axisLabel: { color: '#2c3e50' },
                axisLine: { lineStyle: { color: "#40a9ff" } }
            };
            options.yAxis = {
                name: '健康状态',
                type: 'value',
                min: 0,
                max: 100,
                axisLabel: { color: '#2c3e50' },
                axisLine: { lineStyle: { color: "#40a9ff" } },
                splitLine: {
                    lineStyle: {
                        color: ['#e6f7ff']
                    }
                }
            };
        } else {
            options.series = data;
            options.legend = {
                orient: 'vertical',
                x: 'right',
                y: 'center',
            };
            options.xAxis = {
                name: '测试时间',
                data: timeData,
                axisLabel: { color: 'black' },
                axisLine: { lineStyle: { color: "black" } }
            };
            options.yAxis = {
                name: '参数数值',
                type: 'value',
                axisLabel: { color: 'black' },
                axisLine: { lineStyle: { color: "black" } }
            };
        }

        // 添加标记线
        if (markLineData) {
            options.series.markLine = {
                silent: true,
                lineStyle: { color: '#333' },
                data: markLineData.map(itm => ({ yAxis: itm })),
            };
        }

        // 设置视觉映射
        if (visualConfig) {
            options.visualMap = {
                top: 50,
                right: 10,
                pieces: visualConfig,
            };
        }

        // 应用配置并返回图表实例
        chart.setOption(options);
        return chart;
    },
    
    // 初始化参数图表
    initItemZone(ref, pname, timeData, paraData, supportData, supportLabel) {
        let itemData = [{
            name: pname + '|参数曲线',
            type: 'line',
            data: paraData[pname],
        }];

        // 添加支持数据线
        if (supportData) {
            supportData.forEach((paraItem, count) => {
                itemData.push({
                    name: supportLabel ? supportLabel[count] : '辅助线' + count,
                    type: 'line',
                    data: supportData[count],
                });
            });
        }

        // 调用基本图表初始化方法
        return this.initZone(ref + pname, pname, timeData, itemData, null);
    }
};

// 色彩和视觉辅助功能
export const visualUtils = {
    // 获取状态对应的颜色 - 使用蓝色科技风格
    getItemColor(score) {
        // 确保 score 是有效数值
        score = Number(score);
        if (isNaN(score)) {
            score = 0;
        }
        
        if (score > 0.9) {
            return "#ff4d4f"; // 红色
        } else if (score > 0.6) {
            return "#faad14"; // 橙色
        } else if (score > 0.3) {
            return "#52c41a"; // 绿色
        } else {
            return "#1890ff"; // 蓝色
        }
    },
    
    // 获取状态对应的类型
    getItemType(ratio) {
        if (ratio > 0.9) {
            return "danger";
        } else if (ratio > 0.6) {
            return "warning";
        } else if (ratio > 0.3) {
            return "warning";
        } else {
            return "success";
        }
    },
    
    // 格式化状态显示 - 使用更简洁的显示格式
    getItemState(score) {
        score = Number(score);
        if (isNaN(score)) {
            score = 0;
        }
        
        if (score < 10) {
            return score + "%\n状态恶劣";
        } else if (score < 50) {
            return score + "%\n状态较差";
        } else if (score < 70) {
            return score + "%\n状态一般";
        } else {
            return score + "%\n状态良好";
        }
    }
};
