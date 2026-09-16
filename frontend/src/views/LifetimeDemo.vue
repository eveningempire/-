<template>
<div class="analysis-page">
<h2>寿命预测报告</h2>
<div class="controls"><el-select v-model="id" filterable placeholder="选择包含 HI 的 CSV" @change="clear"><el-option v-for="d in datasets" :key="d.id" :label="d.name" :value="d.id"/></el-select><label>部件模型 <el-select v-model="componentId" @change="clear"><el-option v-for="x in modelIds" :key="x" :label="`部件 ${x}`" :value="x"/></el-select></label><el-button type="primary" :disabled="!id" :loading="loading" @click="run">运行训练模型</el-button></div>
<el-alert title="当前算法：项目组 health-main 寿命集成模型" description="使用 CNN、BiRNN、BiLSTM、BiGRU、SRNN 五个时序模型，并由 RF/Ada 集成输出 RUL。数据集需包含至少 51 行 HI。" type="success" :closable="false"/>
<el-alert v-if="error" title="未生成有效寿命预测" :description="error" type="error" show-icon :closable="false"/>
<el-alert v-if="result?.model_fallback_error" title="已使用可解释趋势算法生成报告" :description="result.model_fallback_error" type="warning" :closable="false"/>
<el-empty v-if="!result&&!error" description="尚无预测报告"/>
<template v-if="result">
<div class="metrics"><div><small>集成 RUL</small><strong>{{Number(result.rul_value).toFixed(3)}}</strong><span>{{result.unit}}</span></div><div><small>当前 HI</small><strong>{{Number(result.current_hi).toFixed(4)}}</strong><span>0–1健康指数</span></div><div><small>部件模型</small><strong>{{componentId}}</strong><span>共 {{result.sample_count}} 个样本</span></div><div><small>序列窗口</small><strong>{{result.sequence_length}}</strong><span>训练配置</span></div></div>
<h3>五模型及集成 RUL 输出</h3><ReportChart :option="chart"/>
<h3>预测依据与限制</h3><el-descriptions border :column="2"><el-descriptions-item label="输入数据集">{{reportName}}</el-descriptions-item><el-descriptions-item label="有效样本数">{{result.hi_sequence.length}}</el-descriptions-item><el-descriptions-item label="算法">{{result.algorithm}}</el-descriptions-item><el-descriptions-item label="部件模型编号">{{componentId}}</el-descriptions-item><el-descriptions-item label="集成方法">RF 与 AdaBoost</el-descriptions-item><el-descriptions-item label="置信区间">训练资产未提供校准区间</el-descriptions-item></el-descriptions>
<p>{{result.limitation}}</p>
<details><summary>计算数据</summary><pre>{{JSON.stringify(result,null,2)}}</pre></details>
</template>
</div>
</template>
<script setup>
import {ref,computed,onMounted} from 'vue'
import ReportChart from '../components/ReportChart.vue'
const datasets=ref([]),id=ref(),result=ref(null),error=ref(''),loading=ref(false),reportName=ref(''),componentId=ref('14'),modelIds=Array.from({length:15},(_,i)=>String(i+1))
const chart=computed(()=>{const r=result.value;if(!r)return {};const names=['CNN','BiRNN','BiLSTM','BiGRU','SRNN'];return {tooltip:{trigger:'axis'},legend:{data:[...names,'RF','Ada']},grid:{containLabel:true,left:45,right:40,bottom:75},xAxis:{type:'value',name:'预测窗口'},yAxis:{type:'value',name:'RUL',scale:true},dataZoom:[{type:'inside'},{type:'slider'}],series:[...names.map(n=>({name:n,type:'line',showSymbol:false,data:(r.model_predictions[n]||[]).map((v,i)=>[i,v])})),{name:'RF',type:'line',showSymbol:false,lineStyle:{width:3},data:r.ensemble_rul.RF.map((v,i)=>[i,v])},{name:'Ada',type:'line',showSymbol:false,lineStyle:{width:3,type:'dashed'},data:r.ensemble_rul.Ada.map((v,i)=>[i,v])}]}})
function clear(){result.value=null;error.value=''}
onMounted(async()=>{try{const r=await fetch('/api/v1/datasets/');if(!r.ok)throw Error('数据集加载失败');datasets.value=await r.json()}catch(e){error.value=e.message}})
async function run(){clear();loading.value=true;reportName.value=datasets.value.find(x=>x.id===id.value)?.name;try{const r=await fetch('/api/v1/rul/predict/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dataset_id:id.value,algorithm:'health_main_ensemble',component_id:componentId.value})});const j=await r.json();if(!r.ok||j.status==='error')throw Error(j.message||'预测失败');result.value=j}catch(e){error.value=e.message}finally{loading.value=false}}
</script>
<style scoped>
.analysis-page{max-width:1250px;min-width:0;color:#253448}.controls{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:20px 0}.controls .el-select{width:300px;max-width:100%}.controls label{display:flex;gap:8px;align-items:center;font-size:14px}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-block:1px solid #dce4ec;margin:24px 0;padding:24px 0;gap:20px}.metrics small,.metrics strong,.metrics span{display:block}.metrics strong{font-size:24px;margin:10px 0;overflow-wrap:anywhere}.metrics span{font-size:12px;color:#627181}.el-alert{margin-top:16px}h3{font-size:17px;margin-top:28px}p{line-height:1.7}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:400px;overflow:auto}details{margin-top:20px}@media(max-width:800px){.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
