// 导入模块和组件
import { msfgComp } from '/static/jsscripts/msfgComponent/index.mjs';
import { dataStore, utils } from '/static/jsscripts/ontime-test/data-store.js';
import { layoutController } from '/static/jsscripts/ontime-test/layout-controller.js';
import { faultDiagnosisController } from './fault-diagnosis-controller.js';
import { lifePredictionController } from './life-prediction-controller.js';
import { systemHealthController } from './system-health-controller.js';
import { uiController } from './ui-controller.js';

// 主视图控制器
const vm = new Vue({
    el: "#result-display",
    components: {
        'ate-multi-signal-flow-graph': msfgComp,
    },
    data() {
        return dataStore;
    },
    computed: {
        allHeight() {
            return (window.innerHeight - 100) || 700;
        },
        windowLen() {
            return window.innerWidth;
        },
    },
    created() {
        // 解析URL并初始化数据
        const urlParams = utils.resolveUrl(window.name);
        this.admin = urlParams.admin;
        this.usrname = urlParams.usrname;
        this.usrdes = urlParams.usrdes;
        this.user = urlParams.user;
        this.obj = urlParams.obj;
        
        window.name = "现场排故工具";
        
        if (this.obj) {
            faultDiagnosisController.initGraph.call(this);
        }
    },
    mounted() {
        if (this.obj) {
            faultDiagnosisController.initGraph.call(this);
        }
        
        // 使用布局控制器调整内容高度
        this.$nextTick(() => {
            layoutController.adjustContentHeight();
        });

        // 默认显示分系统完好率
        this.currentView = 'systemHealth';
    },
    beforeDestroy() {
        // 清理布局控制器的事件监听器
        layoutController.cleanup();
    },
    watch: {
        datadriven_row_actual_ratio(val) {
            systemHealthController.updateDatadrivenRowActual.call(this, val);
        },
        ruleRowActualRatio(val) {
            systemHealthController.updateRuleRowActual.call(this, val);
        },
        showDDmsfg() {
            faultDiagnosisController.change_msfg_mode.call(this);
        },
        // 监听文件选择，同步到右侧预测区域
        lastFile() {
            // 重置预测结果
            lifePredictionController.resetPredictionResults.call(this);
        }
    },
    methods: {
        // UI相关方法
        adjustLayout: uiController.adjustLayout,
        
        // 故障诊断相关方法
        initGraph: faultDiagnosisController.initGraph,
        getResult222: faultDiagnosisController.getResult222,
        refreshInstances: faultDiagnosisController.refreshInstances,
        change_msfg_mode: faultDiagnosisController.change_msfg_mode,
        resetTestCount: faultDiagnosisController.resetTestCount,
        getResult: faultDiagnosisController.getResult,
        fetchResult: faultDiagnosisController.fetchResult,
        initZone: faultDiagnosisController.initZone,
        initItemZone: faultDiagnosisController.initItemZone,
        
        // 系统健康状态相关方法
        getSystemState: systemHealthController.getSystemState,
        getSystemStateDD: systemHealthController.getSystemStateDD,
        getState: systemHealthController.getState,
        getSubState: systemHealthController.getSubState,
        getItemColor: systemHealthController.getItemColor,
        getItemState: systemHealthController.getItemState,
        getItemType: systemHealthController.getItemType,
        getSubsystemNames: systemHealthController.getSubsystemNames,
        selectSubsystem: systemHealthController.selectSubsystem,
        
        // 寿命预测相关方法
        formatLifePrediction: lifePredictionController.formatLifePrediction,
        formatHealthEvolution: lifePredictionController.formatHealthEvolution,
        resetPredictionResults: lifePredictionController.resetPredictionResults,
        runLifePrediction: lifePredictionController.runLifePrediction,
        generateTrendData: lifePredictionController.generateTrendData
    }
});

// 导出视图控制器，供外部访问
export default vm;
