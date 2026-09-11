<template>
<div class="page"><h1>寿命预测演示</h1><p>使用仿真健康指数序列运行基础 RUL 算法。</p><el-card><el-input v-model="text" type="textarea" :rows="4"/><div class="actions"><el-button type="primary" :loading="loading" @click="runDemo">运行内置仿真</el-button><el-button @click="runInput">运行当前序列</el-button></div></el-card><el-card v-if="result"><el-descriptions :column="2" border><el-descriptions-item label="RUL估计">{{ result.rul_value }}</el-descriptions-item><el-descriptions-item label="置信区间">{{ result.confidence_interval?.join(' ~ ') }}</el-descriptions-item><el-descriptions-item label="当前HI">{{ result.current_hi }}</el-descriptions-item><el-descriptions-item label="趋势">{{ result.degradation_trend }}</el-descriptions-item></el-descriptions></el-card></div>
</template>
<script setup>
import {ref} from 'vue'; import {ElMessage} from 'element-plus';
const text=ref('0.98,0.96,0.94,0.91,0.88,0.84,0.81,0.77,0.73,0.69,0.65,0.60'),result=ref(null),loading=ref(false);
async function runDemo(){loading.value=true;try{result.value=(await (await fetch('/api/v1/rul/demo/')).json()).result}catch(e){ElMessage.error('演示失败')}finally{loading.value=false}}
async function runInput(){try{const r=await fetch('/api/v1/rul/predict/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({hi_sequence:text.value.split(',')})});const d=await r.json();if(!r.ok)throw Error(d.message);result.value=d}catch(e){ElMessage.error(e.message)}}
</script>
<style scoped>.page{padding:24px;max-width:900px}.actions{margin-top:16px;display:flex;gap:12px}.el-card{margin-top:18px}</style>
