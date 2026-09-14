<template>
<div class="analysis-page">
<h2>寿命预测报告</h2>
<div class="controls"><el-select v-model="id" filterable placeholder="选择包含 HI 的 CSV" @change="clear"><el-option v-for="d in datasets" :key="d.id" :label="d.name" :value="d.id"/></el-select><label>失效阈值 <el-input-number v-model="threshold" :min=".01" :max=".99" :step=".05" @change="clear"/></label><label>预测间隔数 <el-input-number v-model="horizon" :min="1" :max="1000" @change="clear"/></label><el-button type="primary" :disabled="!id" :loading="loading" @click="run">计算趋势预测</el-button></div>
<el-alert title="当前算法：线性 HI 趋势外推（基线）" description="使用 0–1 健康指数，越高越健康。此结果不是已训练寿命模型的推理结果，不能直接作为检修期限。" type="info" :closable="false"/>
<el-alert v-if="error" title="未生成有效寿命预测" :description="error" type="error" show-icon :closable="false"/>
<el-alert v-if="result?.model_fallback_error" title="已使用可解释趋势算法生成报告" :description="result.model_fallback_error" type="warning" :closable="false"/>
<el-empty v-if="!result&&!error" description="尚无预测报告"/>
<template v-if="result">
<div class="metrics"><div><small>预计剩余间隔</small><strong>{{result.rul_value??'无法估计'}}</strong><span>{{result.unit}}</span></div><div><small>当前 HI</small><strong>{{result.current_hi.toFixed(4)}}</strong><span>阈值 {{result.threshold}}</span></div><div><small>趋势</small><strong>{{result.degradation_trend}}</strong><span>每间隔变化 {{result.slope_per_window.toFixed(6)}}</span></div><div><small>历史拟合 R²</small><strong>{{result.r_squared==null?'不适用':result.r_squared.toFixed(4)}}</strong><span>非预测准确率</span></div></div>
<el-alert :title="result.conclusion" :type="result.rul_value===0?'warning':'info'" :closable="false"/>
<h3>健康指数观测、拟合与外推</h3><ReportChart :option="chart"/>
<p>实线为历史观测；拟合线基于全部 HI 样本；虚线从最新 HI 沿拟合斜率外推。横轴是样本序号，不表示小时或发射次数。</p>
<h3>预测依据与限制</h3><el-descriptions border :column="2"><el-descriptions-item label="输入数据集">{{reportName}}</el-descriptions-item><el-descriptions-item label="有效样本数">{{result.hi_sequence.length}}</el-descriptions-item><el-descriptions-item label="算法">{{result.algorithm}}</el-descriptions-item><el-descriptions-item label="置信区间">未提供：未进行不确定性校准</el-descriptions-item><el-descriptions-item label="外推范围">{{result.forecast.length-1}} 个样本间隔</el-descriptions-item><el-descriptions-item label="阈值含义">用户设定的 HI 判定边界，需结合部件标准确认</el-descriptions-item></el-descriptions>
<p>{{result.limitation}}</p>
<details><summary>计算数据</summary><pre>{{JSON.stringify(result,null,2)}}</pre></details>
</template>
</div>
</template>
<script setup>
import {ref,computed,onMounted} from 'vue'
import ReportChart from '../components/ReportChart.vue'
const datasets=ref([]),id=ref(),result=ref(null),error=ref(''),loading=ref(false),threshold=ref(.2),horizon=ref(100),reportName=ref('')
const chart=computed(()=>{const r=result.value;if(!r)return {};const n=r.hi_sequence.length;return {tooltip:{trigger:'axis'},legend:{data:['观测 HI','历史拟合','趋势外推']},grid:{containLabel:true,left:45,right:40,bottom:75},xAxis:{type:'value',name:'样本序号',min:0},yAxis:{type:'value',name:'健康指数 HI',min:0,max:1},dataZoom:[{type:'inside'},{type:'slider'}],series:[{name:'观测 HI',type:'line',data:r.hi_sequence.map((v,i)=>[i,v]),showSymbol:false,color:'#267db8'},{name:'历史拟合',type:'line',data:r.fitted.map((v,i)=>[i,v]),showSymbol:false,color:'#78909c'},{name:'趋势外推',type:'line',data:r.forecast.map((v,i)=>[n-1+i,v]),showSymbol:false,lineStyle:{type:'dashed'},color:'#239477',markLine:{symbol:'none',data:[{yAxis:r.threshold,name:'失效阈值',label:{formatter:'阈值 '+r.threshold},lineStyle:{color:'#d64c4c'}}]}}]}})
function clear(){result.value=null;error.value=''}
onMounted(async()=>{try{const r=await fetch('/api/v1/datasets/');if(!r.ok)throw Error('数据集加载失败');datasets.value=await r.json()}catch(e){error.value=e.message}})
async function run(){clear();loading.value=true;reportName.value=datasets.value.find(x=>x.id===id.value)?.name;try{const r=await fetch('/api/v1/rul/predict/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dataset_id:id.value,threshold:threshold.value,horizon:horizon.value})});const j=await r.json();if(!r.ok||j.status==='error')throw Error(j.message||'预测失败');result.value=j}catch(e){error.value=e.message}finally{loading.value=false}}
</script>
<style scoped>
.analysis-page{max-width:1250px;min-width:0;color:#253448}.controls{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:20px 0}.controls .el-select{width:300px;max-width:100%}.controls label{display:flex;gap:8px;align-items:center;font-size:14px}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-block:1px solid #dce4ec;margin:24px 0;padding:24px 0;gap:20px}.metrics small,.metrics strong,.metrics span{display:block}.metrics strong{font-size:24px;margin:10px 0;overflow-wrap:anywhere}.metrics span{font-size:12px;color:#627181}.el-alert{margin-top:16px}h3{font-size:17px;margin-top:28px}p{line-height:1.7}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:400px;overflow:auto}details{margin-top:20px}@media(max-width:800px){.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
