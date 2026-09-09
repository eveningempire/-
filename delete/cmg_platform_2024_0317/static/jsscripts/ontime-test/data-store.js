// 全局数据存储对象
export const dataStore = {
    result222: [],
    w_dd: 0.3,
    // 移除instances相关变量
    // instances: [],
    markLineData: [30, 60, 90],
    visualConfig: [
        { gte: 90, lt: 100, color: '#93CE07' },
        { gte: 60, lt: 90, color: '#FBDB0F' },
        { gte: 30, lt: 60, color: '#FC7D02' },
        { gte: 0, lt: 30, color: '#FD0100' }
    ],
    showDD: true,
    showDDmsfg: true,
    detectInfoDDs: [],
    allDetectInfoDDs: [],
    detectInfoRules: [],
    allDetectInfoRules: [],
    detectInfoMfsg: [],
    rule_columns: 3,
    rule_rows: 3,
    rule_row_actual: 0,
    rule_row_actual_ratio: 100,
    datadriven_row_actual: 0,
    datadriven_row_actual_ratio: 100,
    datadriven_columns: 3,
    datadriven_rows: 3,
    actinstitm: {},
    state: 0,
    state_dd: 0,
    stateRange: [],
    paraData: {},
    pnames: {},
    systemData: [],
    systemData_dd: [],
    timeData: [],
    compMap: {},
    datadrivenClickItem: null,
    datadrivenDialog: false,
    subsysname: null,
    // 移除instname变量
    // instname: null,
    // 移除 newInstName 相关变量
    // newInstName: null,
    // checkNewInstNameOk: false,
    // isRedBorder: true,
    // isGreenBorder: false,
    // checkNewInstNameCss: {'border-color': 'green'},
    isGetResultDisabled: false, // 将默认值改为 false，因为不再需要输入测试编号
    isFileInputDisabled: false,
    obj: "",
    usrname: "",
    usrdes: "",
    user: "",
    admin: "admin",
    currentView: 'systemHealth',
    // 移除与时间相关的变量
    // startTime: '',
    // testTime: '',
    // costtime: null,
    lastFile: null,
    result: {
        state: 0,
        state_dd: 0,
        detectInfo: {
            rule: [],
            ml: []
        },
        costtime: 0
    },
    processPercent: 0,
    
    // 寿命预测和健康演化相关数据
    lifeModels: [
        { label: "深度学习模型", value: "deep_learning" },
        { label: "物理模型", value: "physical" },
        { label: "贝叶斯模型", value: "bayesian" }
    ],
    evolutionModels: [
        { label: "动态健康度模型", value: "dynamic_health" },
        { label: "马尔科夫链模型", value: "markov" },
        { label: "SVR模型", value: "svr" }
    ],
    selectedLifeModel: "deep_learning",
    selectedEvolutionModel: "dynamic_health",
    lifePredictionScore: 0,
    lifePredictionState: 0,
    remainingLife: null,
    healthEvolutionScore: 0,
    healthEvolutionState: 0,
    evolutionIndex: null,
    showTrends: false,
    trendData: []
};

// 工具方法
export const utils = {
    // 解析URL参数
    resolveUrl(urlStr) {
        let result = {
            admin: "editor",
            usrname: "未登录",
            usrdes: "",
            user: "",
            obj: ""
        };
        
        if (urlStr.includes("admin=")) {
            result.admin = urlStr.split("admin=")[1].split("&")[0];
        }
        
        if (urlStr.includes("usrname=")) {
            result.usrname = urlStr.split("usrname=")[1].split("&")[0];
        }
        
        if (urlStr.includes("usrname=")) {
            result.usrdes = urlStr.split("descript=")[1].split("?")[0];
        }
        
        if (urlStr.includes("usrid=")) {
            result.user = urlStr.split("usrid=")[1].split("?")[0];
        }
        
        if (urlStr.includes("obj=")) {
            result.obj = urlStr.split("obj=")[1].split("&")[0];
        }
        
        return result;
    },
    
    // 时间格式化
    convertDay(timestp) {
        if (timestp) {
            var time = new Date(timestp);
            var year = time.getFullYear();
            var month = time.getMonth() + 1;
            var day = time.getDate();
            var hour = time.getHours();
            var minute = time.getMinutes();
            var second = time.getSeconds();
            return year + '-' + (month < 10 ? '0' + month : month) + '-' + (day < 10 ? '0' + day : day) + ' ' + 
                   (hour < 10 ? '0' + hour : hour) + ':' + (minute < 10 ? '0' + minute : minute) + ':' + 
                   (second < 10 ? '0' + second : second);
        }
        return '--';
    },
    
    // 计算天数
    calDay(timestp) {
        if (timestp) {
            return Math.round((new Date().getTime() - timestp) / 86400000);
        }
        return "--";
    },
    
    // 重采样数据（上采样）
    upsampleData(data, targetLength) {
        const result = [];
        const factor = (data.length - 1) / (targetLength - 1);
        for (let i = 0; i < targetLength; i++) {
            const idx = i * factor;
            const lower = Math.floor(idx);
            const upper = Math.ceil(idx);
            if (upper >= data.length) {
                result.push(data[data.length - 1]);
            } else {
                const weight = idx - lower;
                const value = data[lower] * (1 - weight) + data[upper] * weight;
                result.push(value);
            }
        }
        return result;
    },
    
    // 重采样数据（下采样）
    downsampleData(data, targetLength) {
        const factor = data.length / targetLength;
        const result = [];
        for (let i = 0; i < targetLength; i++) {
            const idx = Math.floor(i * factor);
            result.push(data[idx]);
        }
        return result;
    }
};
