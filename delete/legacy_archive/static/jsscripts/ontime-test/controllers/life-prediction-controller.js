import { layoutController } from '/static/jsscripts/ontime-test/layout-controller.js';

export const lifePredictionController = {
    // 格式化寿命预测
    formatLifePrediction(score) {
        score = Number(score);
        if (isNaN(score)) {
            score = 0;
        }
        
        return score.toFixed(1) + "%\n剩余寿命";
    },
    
    // 格式化健康演化
    formatHealthEvolution(score) {
        score = Number(score);
        if (isNaN(score)) {
            score = 0;
        }
        
        return score.toFixed(1) + "%\n健康演化";
    },
    
    // 重置预测结果
    resetPredictionResults() {
        this.lifePredictionScore = 0;
        this.lifePredictionState = 0;
        this.remainingLife = null;
        this.healthEvolutionScore = 0;
        this.healthEvolutionState = 0;
        this.evolutionIndex = null;
        this.showTrends = false;
        this.trendData = [];
    },
    
    // 运行预测模型
    async runLifePrediction() {
        if (!this.$refs.dataFile || !this.$refs.dataFile.files || !this.$refs.dataFile.files[0]) {
            this.$message.error("请先选择数据文件");
            return;
        }
        
        let loading = this.$loading({
            lock: true,
            text: '模型预测中，请稍候...',
            spinner: 'el-icon-loading',
            background: 'rgba(0, 10, 0, 0.5)'
        });
        
        try {
            // 模拟异步分析过程
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // 根据所选模型计算模拟结果
            // 寿命预测
            let lifeScoreFactor;
            if (this.selectedLifeModel === "deep_learning") {
                lifeScoreFactor = 0.85;
            } else if (this.selectedLifeModel === "physical") {
                lifeScoreFactor = 0.75;
            } else {
                lifeScoreFactor = 0.65;
            }
            
            // 健康演化
            let evolutionScoreFactor;
            if (this.selectedEvolutionModel === "dynamic_health") {
                evolutionScoreFactor = 0.82;
            } else if (this.selectedEvolutionModel === "markov") {
                evolutionScoreFactor = 0.78;
            } else {
                evolutionScoreFactor = 0.72;
            }
            
            // 基于故障状态计算寿命预测参数
            const baseScore = 100 * (1 - this.state);
            const baseEvolution = 100 * (1 - this.state * 0.8);
            
            // 随机波动
            const randomFactor = () => 1 + (Math.random() * 0.15 - 0.075);
            
            // 设置预测结果
            this.lifePredictionScore = Math.min(100, Math.max(0, baseScore * lifeScoreFactor * randomFactor()));
            this.lifePredictionState = 1 - this.lifePredictionScore / 100;
            
            // 计算剩余寿命（小时）
            this.remainingLife = Math.round(this.lifePredictionScore * 35 + Math.random() * 100);
            
            // 设置健康演化评估
            this.healthEvolutionScore = Math.min(100, Math.max(0, baseEvolution * evolutionScoreFactor * randomFactor()));
            this.healthEvolutionState = 1 - this.healthEvolutionScore / 100;
            
            // 健康演化指数
            this.evolutionIndex = (this.healthEvolutionScore / 20).toFixed(2);
            
            // 生成趋势数据
            this.generateTrendData();
            
            this.$message.success("预测完成");
            
            this.$nextTick(() => {
                layoutController.adjustContentHeight();
            });
        } catch (error) {
            console.error("预测失败:", error);
            this.$message.error("预测过程发生错误");
        } finally {
            loading.close();
        }
    },
    
    // 生成趋势数据并绘制图表
    generateTrendData() {
        // 生成模拟趋势数据
        const points = 20;
        const currentScore = this.healthEvolutionScore / 100;
        const degradeRate = (1 - currentScore) / points * 1.5;
        
        this.trendData = [];
        
        // 生成未来趋势
        for (let i = 0; i < points; i++) {
            // 添加随机波动
            const randomFactor = 1 + (Math.random() * 0.1 - 0.05);
            const value = Math.max(0, Math.min(1, currentScore - (i * degradeRate * randomFactor)));
            this.trendData.push({
                time: `未来${i + 1}周期`,
                value: Math.round(value * 100) / 100
            });
        }
        
        this.showTrends = true;
        
        // 在DOM更新后初始化图表
        this.$nextTick(() => {
            const chartDom = document.getElementById('trend-chart');
            if (!chartDom) return;
            
            const chart = echarts.init(chartDom);
            const option = {
                tooltip: {
                    trigger: 'axis',
                    formatter: function(params) {
                        return params[0].name + '<br/>' + 
                               params[0].seriesName + ': ' + 
                               (params[0].value * 100).toFixed(1) + '%';
                    },
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    borderColor: '#9254de',
                    textStyle: {
                        color: '#2c3e50'
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
                    boundaryGap: false,
                    data: this.trendData.map(d => d.time),
                    axisLine: {
                        lineStyle: {
                            color: '#9254de'
                        }
                    },
                    axisLabel: {
                        color: '#2c3e50'
                    }
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    max: 1,
                    axisLabel: {
                        formatter: value => (value * 100).toFixed(0) + '%',
                        color: '#2c3e50'
                    },
                    axisLine: {
                        lineStyle: {
                            color: '#9254de'
                        }
                    },
                    splitLine: {
                        lineStyle: {
                            color: ['#efdbff']
                        }
                    }
                },
                visualMap: {
                    top: 10,
                    right: 10,
                    pieces: [
                        { gt: 0.7, lte: 1, color: '#1890ff' },  // 蓝色 良好
                        { gt: 0.4, lte: 0.7, color: '#52c41a' }, // 绿色 一般
                        { gt: 0.1, lte: 0.4, color: '#fa8c16' }, // 橙色 较差
                        { gte: 0, lte: 0.1, color: '#ff4d4f' }   // 红色 恶劣
                    ],
                    outOfRange: {
                        color: '#999'
                    },
                    show: false
                },
                series: [
                    {
                        name: '健康度',
                        type: 'line',
                        data: this.trendData.map(d => d.value),
                        smooth: true,
                        lineStyle: {
                            width: 2
                        },
                        markLine: {
                            silent: true,
                            lineStyle: {
                                color: '#9254de'
                            },
                            data: [
                                {
                                    yAxis: 0.7,
                                    label: {
                                        formatter: '良好',
                                        position: 'end'
                                    }
                                },
                                {
                                    yAxis: 0.4,
                                    label: {
                                        formatter: '一般',
                                        position: 'end'
                                    }
                                },
                                {
                                    yAxis: 0.1,
                                    label: {
                                        formatter: '较差',
                                        position: 'end'
                                    }
                                }
                            ]
                        }
                    }
                ]
            };
            
            chart.setOption(option);
            
            // 监听窗口大小变化，重绘图表
            window.addEventListener('resize', () => chart.resize());
        });
    }
};
