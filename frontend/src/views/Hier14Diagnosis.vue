<template>
  <div class="analysis-page">
    <h2>故障诊断分析</h2>
    <div class="controls"><el-select v-model="id" filterable placeholder="选择 CSV 数据集" @change="clear"><el-option v-for="d in datasets" :key="d.id" :label="d.name" :value="d.id"/></el-select><el-button type="primary" :loading="loading" :disabled="!id" @click="run">运行 Hier14 诊断</el-button></div>
    <el-descriptions v-if="selected" :column="2" border><el-descriptions-item label="数据来源">{{selected.source==='simulation'?'仿真':'离线上传'}}</el-descriptions-item><el-descriptions-item label="系统 / 部件">{{selected.system||'未记录'}} / {{selected.component||'未记录'}}</el-descriptions-item><el-descriptions-item label="故障标签（录入信息）">{{selected.fault_type||'未标注'}}</el-descriptions-item><el-descriptions-item label="注入时间（录入信息）">{{selected.injection_time??'未记录'}}</el-descriptions-item></el-descriptions>
    <el-alert v-if="error" title="诊断未完成，尚无模型结论" type="error" :closable="false" show-icon><p>{{failureReason}}</p><p>补齐 Hier14 源码、权重及符合模型字段要求的 CSV 后重新运行。数据集的故障标签不代表预测结果。</p><details><summary>技术详情</summary><pre>{{error}}</pre></details></el-alert>
    <el-empty v-if="!result&&!error" description="尚无诊断结果"/>
    <template v-if="result">
      <div class="metrics"><div><small>末窗口预测</small><strong>{{result.pred_name}}</strong></div><div><small>全程聚合类别</small><strong>{{result.aggregate_pred_name}}</strong></div><div><small>末窗口最高概率</small><strong>{{percent(last?.confidence)}}</strong></div><div><small>诊断窗口数</small><strong>{{result.n_windows}}</strong></div></div>
      <p>末窗口反映最新状态，聚合类别反映全程窗口平均概率。当前数据已完成一次诊断运算，共生成 {{result.n_windows}} 个窗口；数据不足一个模型窗口时仅显示最后一个窗口。模型概率不等同于经过校准的可靠性保证。</p>
      <h3>类别概率比较</h3><ReportChart :option="probabilityChart"/>
      <h3>窗口置信度与时间</h3><ReportChart :option="timeline"/>
      <h3>窗口诊断明细</h3>
      <el-table :data="pageRows" stripe><el-table-column prop="window_index" label="窗口" width="90"/><el-table-column prop="time_start" label="起始时间 (s)"/><el-table-column prop="time_end" label="结束时间 (s)"/><el-table-column prop="pred_name" label="预测类别"/><el-table-column label="最高概率"><template #default="s">{{percent(s.row.confidence)}}</template></el-table-column></el-table>
      <el-pagination v-model:current-page="page" :page-size="10" :total="windows.length" layout="prev, pager, next"/>
      <h3>运行依据</h3><el-descriptions :column="2" border><el-descriptions-item label="模型">Hier14</el-descriptions-item><el-descriptions-item label="窗口长度">{{result.seq_len}} 样本</el-descriptions-item><el-descriptions-item label="滑动步长">{{result.window_stride}} 样本</el-descriptions-item><el-descriptions-item label="采样间隔">{{result.sample_dt}} s</el-descriptions-item></el-descriptions>
      <details><summary>原始模型输出</summary><pre>{{JSON.stringify(result,null,2)}}</pre></details>
    </template>
  </div>
</template>
<script setup>
import {ref,computed,onMounted} from 'vue'
import ReportChart from '../components/ReportChart.vue'
const datasets=ref([]),id=ref(),result=ref(null),error=ref(''),loading=ref(false),page=ref(1)
const selected=computed(()=>datasets.value.find(d=>d.id===id.value)),windows=computed(()=>result.value?.window_series||[]),last=computed(()=>windows.value.at(-1)),pageRows=computed(()=>windows.value.slice((page.value-1)*10,page.value*10))
const percent=v=>v==null?'未提供':(100*Number(v)).toFixed(1)+'%'
const failureReason=computed(()=>/repo not found|不存在|Missing.*artifact/i.test(error.value)?'诊断运行依赖缺失，模型未执行。':/columns|rows|CSV/i.test(error.value)?'输入数据不符合模型要求。':'模型执行失败，请检查技术详情。')
const probabilityChart=computed(()=>{const p=result.value?.class_probs||[],a=result.value?.aggregate_class_probs||[];return {tooltip:{trigger:'axis'},legend:{data:['末窗口','全程平均']},grid:{bottom:100,containLabel:true},xAxis:{type:'category',data:p.map(x=>x.name),axisLabel:{rotate:30}},yAxis:{type:'value',name:'概率 (%)',min:0,max:100},series:[{name:'末窗口',type:'bar',data:p.map(x=>x.prob*100),color:'#247bba'},{name:'全程平均',type:'bar',data:p.map(x=>(a.find(y=>y.name===x.name)?.prob??0)*100),color:'#239477'}]}})
const timeline=computed(()=>({tooltip:{trigger:'axis'},grid:{containLabel:true,left:55,right:40,bottom:70},xAxis:{type:'value',name:'窗口结束时间 (s)'},yAxis:{type:'value',name:'最高类别概率 (%)',min:0,max:100},dataZoom:[{type:'inside'},{type:'slider'}],series:[{name:'窗口置信度',type:'line',data:windows.value.map(w=>[w.time_end,w.confidence*100]),color:'#247bba'}]}))
function clear(){result.value=null;error.value='';page.value=1}
onMounted(async()=>{try{const r=await fetch('/api/v1/datasets/');if(!r.ok)throw Error('数据集加载失败');datasets.value=await r.json()}catch(e){error.value=e.message}})
async function run(){clear();loading.value=true;try{const r=await fetch('/api/v1/fault-diagnosis/predict/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dataset_id:id.value})});const j=await r.json();if(!r.ok||!j.ok)throw Error(j.error||'诊断失败');result.value=j.result}catch(e){error.value=e.message}finally{loading.value=false}}
</script>
<style scoped>
.analysis-page{max-width:1250px;min-width:0;color:#253448}.controls{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}.controls .el-select{width:360px;max-width:100%}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-block:1px solid #dce4ec;margin:24px 0;padding:24px 0;gap:20px}.metrics small,.metrics strong{display:block}.metrics strong{font-size:22px;margin-top:10px;overflow-wrap:anywhere}.el-alert{margin-top:20px}h3{font-size:17px;margin-top:28px}p{line-height:1.7}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:400px;overflow:auto}details{margin:20px 0}.el-pagination{margin:16px 0}@media(max-width:800px){.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
