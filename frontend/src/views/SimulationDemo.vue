<template>
  <div class="demo"><h1>仿真数据与故障注入演示</h1><p>生成仿真数据并查看告警、诊断及健康指标结果。</p>
    <el-card><el-form inline><el-form-item label="子系统"><el-select v-model="subsystem" @change="mode=''" style="width:140px"><el-option v-for="s in Object.keys(options)" :key="s" :label="s" :value="s"/></el-select></el-form-item><el-form-item label="故障模式"><el-select v-model="mode" style="width:170px"><el-option v-for="m in (options[subsystem]||[])" :key="m" :label="m" :value="m"/></el-select></el-form-item><el-form-item label="严重度"><el-slider v-model="severity" :min="0" :max="1" :step=".1" style="width:140px"/></el-form-item><el-button type="primary" :loading="loading" @click="run">生成并分析</el-button></el-form></el-card>
    <el-card v-if="result" class="result"><el-alert :title="result.diagnosis.alarm?'检测到异常告警':'数据正常'" :type="result.diagnosis.alarm?'error':'success'" show-icon/><el-descriptions :column="3" border><el-descriptions-item label="诊断子系统">{{result.diagnosis.subsystem}}</el-descriptions-item><el-descriptions-item label="故障模式">{{result.diagnosis.fault}}</el-descriptions-item><el-descriptions-item label="置信度">{{result.diagnosis.confidence}}</el-descriptions-item><el-descriptions-item label="健康指数">{{result.summary.health_index}}</el-descriptions-item><el-descriptions-item label="样本数">{{result.summary.sample_count}}</el-descriptions-item></el-descriptions><el-table :data="result.data.slice(-10)" stripe><el-table-column prop="time" label="时间"/><el-table-column prop="pressure" label="压力"/><el-table-column prop="temperature" label="温度"/><el-table-column prop="attitude_error" label="姿态误差"/><el-table-column prop="control_error" label="控制误差"/></el-table></el-card>
  </div>
</template>
<script setup>
import {ref,onMounted} from 'vue'; import {ElMessage} from 'element-plus';
const options=ref({}),subsystem=ref('动力'),mode=ref('泄漏'),severity=ref(.6),loading=ref(false),result=ref(null)
onMounted(async()=>{const d=await (await fetch('/api/v1/simulation-demo/sample/')).json(); options.value=d.subsystems||{动力:['泄漏','泵效率下降'],控制:['传感器偏置','执行器迟滞']}})
async function run(){loading.value=true;try{const r=await fetch('/api/v1/simulation-demo/run/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fault:{subsystem:subsystem.value,mode:mode.value,severity:severity.value,start:20}})});const d=await r.json();if(!r.ok)throw Error(d.error);result.value=d}catch(e){ElMessage.error(e.message)}finally{loading.value=false}}
</script>
<style scoped>.demo{padding:24px;max-width:1200px}.result{margin-top:18px}.el-alert{margin-bottom:16px}.el-table{margin-top:18px}</style>
