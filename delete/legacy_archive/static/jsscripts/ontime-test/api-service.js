// API服务模块
export const apiService = {
    // 获取历史测试结果列表
    async getInstances(obj) {
        try {
            const formData = new FormData();
            formData.append("obj", obj);
            const response = await axios.post("/ontime-test/get-inst-all", formData);
            
            // 解析返回数据
            let data = response.data;
            if (typeof data === 'string') {
                data = JSON.parse(data);
            }
            return Array.isArray(data) ? data : [];
        } catch (error) {
            console.error("获取测试列表失败:", error);
            return [];
        }
    },
    
    // 获取单个测试结果详情
    async getInstanceDetail(obj, instname) {
        try {
            const formData = new FormData();
            formData.append("obj", obj);
            formData.append("instname", instname);
            const response = await axios.post("/ontime-test/get-inst-one", formData);
            
            // 解析返回数据
            let result = response.data;
            if (typeof result === 'string') {
                result = JSON.parse(result);
            }
            return result || {};
        } catch (error) {
            console.error("获取测试详情失败:", error);
            return {};
        }
    },
    
    // 获取多信号流图配置
    async getGraphConfig(obj) {
        try {
            const formData = new FormData();
            formData.append("obj", obj);
            const response = await axios.post("/multi-info-edit/init-graph1/", formData);
            return response.data;
        } catch (error) {
            console.error("获取流图配置失败:", error);
            return null;
        }
    },
    
    // 提交数据进行故障诊断分析
    async analyzeData(obj, instname, editor, dataFile) {
        try {
            const formData = new FormData();
            formData.append("obj", obj);
            formData.append("instname", instname);
            formData.append("editor", editor);
            formData.append("dataFile", dataFile);
            
            const response = await axios.post("/ontime-test/analyse-data", formData);
            
            // 解析返回数据
            let result = response.data;
            if (typeof result === 'string') {
                result = JSON.parse(result);
            }
            
            // 确保数据结构完整
            if (!result.detectInfo) {
                result.detectInfo = { rule: [], ml: [] };
            }
            if (!result.detectInfo.rule) {
                result.detectInfo.rule = [];
            }
            
            return result;
        } catch (error) {
            console.error("故障诊断分析失败:", error);
            throw error;
        }
    },
    
    // 获取实时诊断结果
    async getResult222(obj) {
        try {
            const formData = new FormData();
            formData.append("obj", obj);
            const response = await axios.post("/ontime-test/get-result222", formData);
            
            // 解析返回数据
            let result = response.data;
            if (typeof result === 'string') {
                result = JSON.parse(result);
            }
            return result;
        } catch (error) {
            console.error("获取实时诊断结果失败:", error);
            return {
                state: 0,
                detectInfo: { rule: [], ml: [] },
                costtime: 0
            };
        }
    },
    
    // 寿命预测与健康演化
    async predictLifeAndHealth(obj, model, data) {
        try {
            const formData = new FormData();
            formData.append("obj", obj);
            formData.append("model", JSON.stringify(model));
            formData.append("dataFile", data);
            
            // 此处是模拟的API端点，实际实现时，应指向正确的服务器端点
            // const response = await axios.post("/prediction/life-health", formData);
            
            // 模拟预测结果
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // 构造模拟返回数据
            return {
                lifePrediction: {
                    score: 85 + Math.random() * 10,
                    remainingLife: 1200 + Math.random() * 500,
                },
                healthEvolution: {
                    score: 80 + Math.random() * 15,
                    evolutionIndex: 4.2 + Math.random(),
                    trend: Array.from({length: 20}, (_, i) => ({
                        time: `周期${i+1}`,
                        value: Math.max(0, 0.9 - i * 0.04 * (1 + Math.random() * 0.2 - 0.1))
                    }))
                }
            };
        } catch (error) {
            console.error("寿命预测失败:", error);
            throw error;
        }
    }
};
