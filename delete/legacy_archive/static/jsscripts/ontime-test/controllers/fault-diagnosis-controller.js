import { apiService } from '/static/jsscripts/ontime-test/api-service.js';
import { chartUtils } from '/static/jsscripts/ontime-test/charts.js';

export const faultDiagnosisController = {
    // 初始化信号流图
    async initGraph() {
        let loading = this.$loading({
            lock: true,
            text: '加载中，请稍候...',
            spinner: 'el-icon-loading',
            background: 'rgba(0, 10, 0, 0.5)'
        });
        
        try {
            const graphData = await apiService.getGraphConfig(this.obj);
            if (this.$refs.multiFlowShow) {
                this.$refs.multiFlowShow.handleUpdatImportData({
                    value: {
                        "SystemData": graphData
                    },
                    type: "global"
                });
            }
        } catch (err) {
            this.$message.error("初始化信号流图失败");
        } finally {
            loading.close();
        }
    },
    
    // 获取实时分析结果
    async getResult222() {
        let loading = this.$loading({
            lock: true,
            text: '加载中，请稍候...',
            spinner: 'el-icon-loading',
            background: 'rgba(0, 10, 0, 0.5)'
        });
        
        try {
            this.result222 = await apiService.getResult222(this.obj);
        } catch (err) {
            this.$message.error("获取趋势分析数据失败");
        } finally {
            loading.close();
        }
    },
    
    // 刷新实例列表
    async refreshInstances(loading) {
        try {
            this.instances = await apiService.getInstances(this.obj);
        } catch (err) {
            this.$message.error("更新测试列表失败");
        } finally {
            if (loading) loading.close();
        }
    },
    
    // 改变多信号流图模式
    change_msfg_mode() {
        if (!this.$refs.multiFlowShow) return;
        
        if (this.showDDmsfg) {
            this.$refs.multiFlowShow.handleUpdatImportData({
                value: {
                    "SystemData": this.$refs.multiFlowShow.renderStructColor(this.detectInfoMfsgDD, "analyse")
                },
                type: "global"
            });
        } else {
            this.$refs.multiFlowShow.handleUpdatImportData({
                value: {
                    "SystemData": this.$refs.multiFlowShow.renderStructColor(this.detectInfoMfsg, "analyse")
                },
                type: "global"
            });
        }
    },
    
    // 重置测试计数
    resetTestCount() {
        // 保存文件引用
        this.lastFile = this.$refs.dataFile.files[0];
        
        // 重置按钮状态，允许再次获取结果
        this.isFileInputDisabled = false;
        this.isGetResultDisabled = false;
    },
    
    // 获取结果
    getResult() {
        if (this.lastFile !== this.$refs.dataFile.files[0]) {
            this.resetTestCount();
        }
        
        // 直接调用 fetchResult 方法
        this.fetchResult(false);
    },
    
    // 从服务器获取结果
    async fetchResult(isViewChange) {
        let loading = this.$loading({
            lock: true,
            text: '加载中，请稍候...',
            spinner: 'el-icon-loading',
            background: 'rgba(0, 10, 0, 0.5)'
        });
        
        try {
            // 确保有文件被选择
            if (!this.$refs.dataFile || !this.$refs.dataFile.files || !this.$refs.dataFile.files[0]) {
                this.$message.error("请选择数据文件");
                loading.close();
                return;
            }
            
            // 自动生成唯一的测试编号
            const timestamp = new Date().getTime();
            const randomStr = Math.random().toString(36).substring(2, 8);
            const autoInstName = `test_${timestamp}_${randomStr}`;
            
            // 调用API分析数据
            const result = await apiService.analyzeData(
                this.obj,
                autoInstName,  // 使用自动生成的测试编号
                this.user,
                this.$refs.dataFile.files[0]
            );
            
            // 更新视图数据
            this.state = result.state || 0;
            this.state_dd = result.state_dd || 0;
            this.compMap = result.compMap || {};
            this.stateRange = result.stateRange || [];
            this.detectInfo = result.detectInfo || { rule: [], ml: [] };
            this.systemData = result.systemData || [];
            this.systemData_dd = result.systemData_dd || [];
            this.timeData = result.timeData || [];
            this.pnames = result.pnames || {};
            this.paraData = result.paraData || {};
            
            // 更新规则和数据驱动检测结果
            this.detectInfoRules = this.detectInfo.rule || [];
            this.allDetectInfoRules = this.detectInfo.rule || [];
            this.detectInfoDDs = this.detectInfo.ml || [];
            this.allDetectInfoDDs = this.detectInfo.ml || [];
            this.detectInfoMfsg = this.detectInfo.mfsg || [];
            this.detectInfoMfsgDD = this.detectInfo.mfsg_dd || [];
            
            // 更新视图
            this.change_msfg_mode();
            this.actinstitm.state = this.state;
            this.actinstitm.state_dd = this.state_dd || 0;
            this.$forceUpdate();
            
            this.$message.success("当前测试数据诊断完成");
            
            this.$nextTick(() => {
                this.adjustLayout();
            });
        } catch (error) {
            console.error("故障诊断失败:", error);
            this.$message.error("故障诊断失败");
        } finally {
            loading.close();
        }
    },
    
    // 初始化图表区域
    initZone(refName, title, timeData, data, dataName, markLineData, visualConfig) {
        return chartUtils.initZone(this.$refs[refName], title, timeData, data, dataName, markLineData, visualConfig);
    },
    
    // 初始化参数图表区域
    initItemZone(refName, pname, timeData, paraData, supportData, supportLabel) {
        return chartUtils.initItemZone(this.$refs[refName], pname, timeData, paraData, supportData, supportLabel);
    }
};
