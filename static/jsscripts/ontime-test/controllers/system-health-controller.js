import { visualUtils } from '/static/jsscripts/ontime-test/charts.js';
import { utils } from '/static/jsscripts/ontime-test/data-store.js';

export const systemHealthController = {
    // 获取系统状态
    getSystemState(name) {
        let system = this.systemData.find(item => item.name === name);
        return system ? system.state : 0;
    },
    
    // 获取系统状态（数据驱动）
    getSystemStateDD(name) {
        let system = this.systemData_dd.find(item => item.name === name);
        return system ? system.state : 0;
    },
    
    // 获取状态文本 - 美化版本
    getState(score) {
        // 确保 score 是有效数字
        score = Number(score);
        if (isNaN(score) || score < 0) {
            score = 0;
        } else if (score > 100) {
            score = 100;
        }
        
        // 修改为使用obj，不再使用instname
        const displayName = this.obj.split("#")[0];
        
        if (score < 10) {
            return displayName + "\n\n故障率显著\n(" + score.toFixed(2) + "%)";
        } else if (score < 50) {
            return displayName + "\n\n故障率较高\n(" + score.toFixed(2) + "%)";
        } else if (score < 70) {
            return displayName + "\n\n故障率一般\n(" + score.toFixed(2) + "%)";
        } else {
            return displayName + "\n\n故障率较低\n(" + score.toFixed(2) + "%)";
        }
    },
    
    // 获取子系统状态文本 - 美化版本
    getSubState(k) {
        return score => {
            // 确保 score 是有效数字
            score = Number(score);
            if (isNaN(score) || score < 0) {
                score = 0;
            } else if (score > 100) {
                score = 100;
            }
            
            // 简化文本显示，使其更适合进度条内显示
            return score.toFixed(1) + "%";
        };
    },
    
    // 获取子系统名称
    getSubsystemNames() {
        this.subsystemNames = [...new Set(this.result222.map(item => item.subsystem_name))];
    },
    
    // 选择子系统并渲染图表
    selectSubsystem(subsys) {
        const chartData = this.result222.filter(item => item.subsystem_name === subsys);
        const testTimes = [...new Set(chartData.map(item => item.test_time))];
        const numberOfFlights = testTimes.length;
        const totalPoints = 1000;
        const pointsPerFlight = Math.floor(totalPoints / numberOfFlights);

        if (this.chart) {
            this.chart.clear();
        }

        const seriesData = testTimes.map((testTime, index) => {
            const batchData = chartData.filter(item => item.test_time === testTime);
            let stateRanges = batchData.map(item => JSON.parse(item.stateRange)).flat();

            if (stateRanges.length < pointsPerFlight) {
                stateRanges = utils.upsampleData(stateRanges, pointsPerFlight);
            } else if (stateRanges.length > pointsPerFlight) {
                stateRanges = utils.downsampleData(stateRanges, pointsPerFlight);
            }

            const xData = Array.from({ length: pointsPerFlight }, (_, i) => index * pointsPerFlight + i);

            return {
                name: `架次 ${index + 1}`,
                type: 'line',
                data: xData.map((x, i) => [x, stateRanges[i]]),
                smooth: true
            };
        });

        this.chart = echarts.init(document.getElementById('chart-container'));
        const option = {
            title: { text: `子系统: ${subsys}` },
            tooltip: { trigger: 'axis' },
            xAxis: {
                type: 'value',
                min: 0,
                max: totalPoints,
                splitLine: { show: false },
                axisLabel: { formatter: () => '' }
            },
            yAxis: {
                type: 'value',
                min: 0,
                max: 1
            },
            series: seriesData
        };
        this.chart.setOption(option);
    },
    
    // 切换视图
    changeView(view) {
        this.currentView = view;
    },
    
    // 获取状态对应的颜色 - 使用多彩配色方案
    getItemColor(score) {
        // 确保 score 是有效数值
        score = Number(score);
        if (isNaN(score)) {
            score = 0;
        }
        
        if (score > 0.9) {
            return "#ff4d4f"; // 红色 - 危险
        } else if (score > 0.6) {
            return "#fa8c16"; // 橙色 - 警告
        } else if (score > 0.3) {
            return "#52c41a"; // 绿色 - 良好
        } else {
            return "#1890ff"; // 蓝色 - 优秀
        }
    },
    
    // 获取状态对应的类型
    getItemType(ratio) {
        if (ratio > 0.9) {
            return "danger";
        } else if (ratio > 0.6) {
            return "warning";
        } else if (ratio > 0.3) {
            return "success";
        } else {
            return "info";
        }
    },
    
    // 格式化状态显示 - 使用更生动的描述
    getItemState(score) {
        score = Number(score);
        if (isNaN(score)) {
            score = 0;
        }
        
        if (score < 10) {
            return score + "%\n状态极佳";
        } else if (score < 50) {
            return score + "%\n状态良好";
        } else if (score < 70) {
            return score + "%\n需要注意";
        } else {
            return score + "%\n需要维护";
        }
    },
    
    // 更新数据驱动实际行数
    updateDatadrivenRowActual(val) {
        if (this.subsysname) {
            let rows_all = Math.ceil(this.allDetectInfoDDs.length / this.datadriven_columns) - this.datadriven_rows;
            this.datadriven_row_actual = Math.round(rows_all * (1 - this.datadriven_row_actual_ratio / 100));
        } else {
            this.datadriven_row_actual = 0;
        }
    },
    
    // 更新规则实际行数
    updateRuleRowActual(val) {
        if (this.subsysname) {
            let rows_all = Math.ceil(this.allDetectInfoRules.length / this.rule_columns) - this.rule_rows;
            this.rule_row_actual = Math.round(rows_all * (1 - this.ruleRowActualRatio / 100));
        } else {
            this.rule_row_actual = 0;
        }
    }
};
