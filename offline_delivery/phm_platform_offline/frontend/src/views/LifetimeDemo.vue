<template>
  <div class="analysis-page">
    <h2>寿命预测报告</h2>
    <el-radio-group v-model="mode" :disabled="busy" @change="reset"><el-radio-button label="single">单个预测</el-radio-button><el-radio-button label="batch">批量预测</el-radio-button></el-radio-group>
    <div class="controls">
      <el-select v-if="mode==='single'" v-model="id" :disabled="busy" filterable placeholder="选择预测数据集" @change="onDatasetChange"><el-option v-for="d in selectableDatasets" :key="d.id" :label="d.name" :value="d.id"/></el-select>
      <el-select v-else v-model="batchIds" :disabled="busy" multiple collapse-tags filterable placeholder="批量选择预测数据集" @change="onDatasetChange"><el-option v-for="d in selectableDatasets" :key="`batch-${d.id}`" :label="d.name" :value="d.id"/></el-select>
      <el-select v-model="algorithm" :disabled="busy" placeholder="选择寿命算法" @change="onAlgorithmChange"><el-option v-for="item in algorithmOptions" :key="item.key" :label="item.name" :value="item.key"/></el-select>
      <label v-if="algorithm==='health_main_ensemble'">部件模型 <el-select v-model="componentId" :disabled="busy" placeholder="选择部件模型" @change="reset"><el-option v-for="x in componentOptions" :key="x.id" :label="`${x.name} (模型 ${x.id} · ${x.signal})`" :value="x.id"/></el-select></label>
      <el-button v-if="mode==='single'" type="primary" :disabled="!id||(algorithm==='health_main_ensemble'&&(!componentId||componentMismatch))" :loading="loading" @click="run">运行预测</el-button>
      <el-button v-else type="success" :disabled="!batchIds.length||batchIds.length>100||(algorithm==='health_main_ensemble'&&(!componentId||componentMismatch))" :loading="batchLoading" @click="runBatch">批量预测</el-button>
    </div>
    <div v-if="algorithm==='health_main_ensemble'&&selectedComponent" class="model-contract"><span>部件参数：<b>{{selectedComponent.signal}}</b></span><span>特征窗口：2 秒</span><span>步长：1 秒</span><span>模型序列：50 个 HI</span></div>
    <el-alert v-if="mode==='batch'&&batchIds.length>100" type="warning" :closable="false" title="单次最多预测 100 个数据集"/>
    <el-alert v-if="algorithm==='health_main_ensemble'&&componentId&&componentMismatch" type="warning" :closable="false" :title="`所选模型“${selectedComponentName}”与数据集的 PBS 部件关联不一致`" description="请核对数据集所属单机后重新选择模型；模型不一致时不能运行。"/>
    <el-alert v-if="algorithm==='health_main_ensemble'&&selectedDatasets.length&&selectedDatasets.some(item=>!item.structure_node_id)" type="warning" :closable="false" title="部分数据集尚未关联 PBS 单机产品" description="可在数据管理中建立关联，再核对寿命模型对应的实际部件。"/>
    <el-alert v-if="selectedAlgorithm?.source==='plugin'" :title="`${selectedAlgorithm.name} · 插件 ${selectedAlgorithm.version}`" :description="selectedAlgorithm.description||'本地安装的寿命预测算法'" type="info" :closable="false"/>
    <el-form v-if="selectedAlgorithm?.source==='plugin'&&pluginFields.length" class="plugin-parameters" inline label-position="top"><el-form-item v-for="field in pluginFields" :key="field.name" :label="field.name"><el-select v-if="field.definition.enum" v-model="pluginParameters[field.name]"><el-option v-for="choice in field.definition.enum" :key="String(choice)" :label="String(choice)" :value="choice"/></el-select><el-switch v-else-if="field.definition.type==='boolean'" v-model="pluginParameters[field.name]"/><el-input-number v-else-if="field.definition.type==='number'||field.definition.type==='integer'" v-model="pluginParameters[field.name]" :min="field.definition.minimum" :max="field.definition.maximum" :precision="field.definition.type==='integer'?0:undefined"/><el-input v-else v-model="pluginParameters[field.name]"/></el-form-item></el-form>
    <el-alert v-if="error" title="预测未完成" :description="error" type="error" show-icon :closable="false"/>
    <template v-if="mode==='batch'&&batchReport">
      <el-alert type="info" :closable="false" :title="`批量预测完成：成功 ${batchReport.success}，失败 ${batchReport.failed}`"/>
      <el-card class="batch-results" shadow="never"><template #header><b>批量预测结果</b></template>
        <el-table :data="batchReport.results||[]" stripe row-key="dataset_id" highlight-current-row :current-row-key="activeDatasetId" @row-click="showBatchResult">
          <el-table-column label="数据集" min-width="210"><template #default="s">{{datasetName(s.row.dataset_id)}}</template></el-table-column>
          <el-table-column label="状态" width="100"><template #default="s"><el-tag :type="s.row.status==='success'?'success':'danger'">{{s.row.status==='success'?'成功':'失败'}}</el-tag></template></el-table-column>
          <el-table-column label="RUL" width="150"><template #default="s">{{s.row.status==='success'?formatRul(s.row.result):'—'}}</template></el-table-column>
          <el-table-column label="输入参数" width="115"><template #default="s">{{s.row.result?.hi_source?.input_signal||'—'}}</template></el-table-column>
          <el-table-column label="错误 / 操作" min-width="220"><template #default="s"><el-button v-if="s.row.status==='success'" link type="primary" @click.stop="showBatchResult(s.row)">查看详情</el-button><span v-else class="row-error">{{s.row.error||s.row.result?.message||s.row.message||'预测失败'}}</span></template></el-table-column>
        </el-table>
      </el-card>
    </template>
    <el-alert v-if="selectedBatchError" type="error" :closable="false" :title="`${datasetName(activeDatasetId)}：${selectedBatchError}`"/>
    <el-empty v-if="!result&&!error&&!batchReport" description="尚无预测报告"/>
    <el-card v-if="result" :key="activeDatasetId" class="report" shadow="never">
      <template #header><b>当前详情：{{datasetName(activeDatasetId)}}</b></template>
      <el-alert v-if="result.model_fallback_error" title="已使用可解释趋势算法生成报告" :description="result.model_fallback_error" type="warning" :closable="false"/>
      <el-alert v-if="hiSource.clipped_fraction>0" type="warning" :closable="false" title="部分 HI 超出训练归一化范围" :description="`${formatNumber(hiSource.clipped_fraction*100,1)}% 的窗口已裁剪至 0–1；该数据上的寿命输出需要进一步核验。`"/>
      <div class="metrics"><div><small>剩余寿命 (RUL)</small><strong>{{formatNumber(result.rul_value,3)}}</strong><span>{{result.unit_label||unitLabels[result.unit]||result.unit||'未提供'}}</span></div><div><small>当前健康指数 (HI)</small><strong>{{formatNumber(result.current_hi,4)}}</strong><span>0–1 健康指数</span></div><div><small>寿命模型</small><strong>{{algorithm==='health_main_ensemble'?activeComponentName:(result.algorithm||selectedAlgorithm?.name)}}</strong><span>共 {{result.hi_sequence?.length??result.sample_count??'—'}} 个 HI 样本</span></div><div><small>序列窗口</small><strong>{{result.sequence_length??'—'}}</strong><span>HI 样本 / 窗口</span></div></div>
      <template v-if="hasHi"><h3>健康指数趋势</h3><ReportChart :key="`hi-${activeDatasetId}`" :option="hiChart"/></template>
      <template v-if="hasSeries"><h3>五模型及集成剩余寿命输出</h3><ReportChart :key="`chart-${activeDatasetId}`" :option="chart"/></template>
      <h3>预测依据与限制</h3>
      <el-descriptions border :column="reportColumns">
        <el-descriptions-item label="输入数据集">{{datasetName(activeDatasetId)}}</el-descriptions-item>
        <el-descriptions-item label="PBS 单机产品">{{activeDataset?.structure_node_name||'未关联'}}</el-descriptions-item>
        <el-descriptions-item label="HI 来源">{{hiSourceLabel}}</el-descriptions-item>
        <el-descriptions-item label="实际使用数据">{{hiSource.source_dataset_name||datasetName(hiSource.source_dataset_id||activeDatasetId)}}</el-descriptions-item>
        <el-descriptions-item label="输入参数">{{hiSource.input_signal||'未提供'}}</el-descriptions-item>
        <el-descriptions-item v-if="hiSource.feature_order?.length" label="特征顺序">{{hiSource.feature_order.join(' → ')}}</el-descriptions-item>
        <el-descriptions-item label="有效 HI 样本数">{{result.hi_sequence?.length??result.sample_count??'—'}}</el-descriptions-item>
        <el-descriptions-item label="算法">{{result.algorithm||selectedAlgorithm?.name}}</el-descriptions-item>
        <el-descriptions-item v-if="algorithm==='health_main_ensemble'" label="寿命模型">{{activeComponentName}}（模型 {{activeComponentId}}）</el-descriptions-item>
        <el-descriptions-item label="输出单位">{{result.unit_label||unitLabels[result.unit]||result.unit||'未提供'}}</el-descriptions-item>
        <el-descriptions-item label="置信区间">{{result.confidence_interval??'未提供校准区间'}}</el-descriptions-item>
      </el-descriptions>
      <p v-if="result.limitation">{{result.limitation}}</p><details><summary>计算数据</summary><pre>{{JSON.stringify(result,null,2)}}</pre></details>
    </el-card>
  </div>
</template>
<script setup>
import {ref,computed,onMounted,onBeforeUnmount} from 'vue'
import {useRoute} from 'vue-router'
import ReportChart from '../components/ReportChart.vue'
import {isSelectableDataset} from '../utils/datasetVisibility.js'
const route=useRoute()
const unitLabels={s:'秒 (s)',h:'小时 (h)',hour:'小时 (h)',hours:'小时 (h)',sample_interval:'样本间隔'}
const componentOptions=[['液氧泵','P1'],['液氧涡轮','P2'],['煤油管路','P3'],['煤油阀门','P4'],['燃气发生器','P5'],['燃烧室','P6'],['喷管','P7'],['TVC','P8'],['RCS','P10'],['栅格舵','P9'],['传感器','P12'],['液氧管路','P14'],['液氧阀门','P15'],['煤油泵','P16'],['煤油涡轮','P17']].map(([name,signal],index)=>({name,signal,id:String(index+1)}))
const datasets=ref([]),mode=ref('single'),id=ref(),batchIds=ref([]),activeDatasetId=ref(null),result=ref(null),batchReport=ref(null),selectedBatchError=ref(''),error=ref(''),loading=ref(false),batchLoading=ref(false),componentId=ref(''),activeComponentId=ref(''),algorithm=ref('health_main_ensemble'),algorithmOptions=ref([{key:'health_main_ensemble',name:'health-main RUL 集成模型',source:'builtin'}]),pluginParameters=ref({})
const mobileQuery=window.matchMedia('(max-width: 650px)'),reportColumns=ref(mobileQuery.matches?1:2)
const updateColumns=event=>{reportColumns.value=event.matches?1:2}
const busy=computed(()=>loading.value||batchLoading.value)
const selectableDatasets=computed(()=>datasets.value.filter(isSelectableDataset))
const selectedComponent=computed(()=>componentOptions.find(x=>x.id===componentId.value))
const activeComponentName=computed(()=>componentOptions.find(x=>x.id===activeComponentId.value)?.name||`模型 ${activeComponentId.value}`)
const selectedComponentName=computed(()=>componentOptions.find(x=>x.id===componentId.value)?.name||'')
const selectedDatasets=computed(()=>mode.value==='single'?datasets.value.filter(item=>String(item.id)===String(id.value)):datasets.value.filter(item=>batchIds.value.some(value=>String(value)===String(item.id))))
const activeDataset=computed(()=>datasets.value.find(item=>String(item.id)===String(activeDatasetId.value)))
const componentMismatch=computed(()=>selectedDatasets.value.some(item=>{if(!item.structure_node_name||!selectedComponentName.value)return false;const aliases={'氧涡轮':'液氧涡轮'};return (aliases[item.structure_node_name]||item.structure_node_name)!==selectedComponentName.value}))
const selectedAlgorithm=computed(()=>algorithmOptions.value.find(item=>item.key===algorithm.value)),pluginFields=computed(()=>Object.entries(selectedAlgorithm.value?.parameters||{}).map(([name,definition])=>({name,definition})))
const hiSource=computed(()=>result.value?.hi_source||{})
const hiSourceLabel=computed(()=>hiSource.value.method==='trained_pca'?(hiSource.value.paired_dataset?'同次仿真派生参数 · 训练 scaler / PCA':'派生参数 · 训练 scaler / PCA'):hiSource.value.method==='provided_hi'?'CSV 健康指数列':'未提供')
const datasetName=datasetId=>datasets.value.find(x=>String(x.id)===String(datasetId))?.name||`数据集 #${datasetId}`
const formatNumber=(value,digits)=>value==null||!Number.isFinite(Number(value))?'—':Number(value).toFixed(digits)
const formatRul=value=>`${formatNumber(value?.rul_value,3)} ${value?.unit_label||unitLabels[value?.unit]||value?.unit||''}`
const hasSeries=computed(()=>Array.isArray(result.value?.ensemble_rul?.RF)&&Array.isArray(result.value?.ensemble_rul?.Ada))
const hasHi=computed(()=>Array.isArray(result.value?.hi_sequence)&&result.value.hi_sequence.length>0)
const chartAxes=(timed,yName)=>({tooltip:{trigger:'axis'},grid:{containLabel:true,left:35,right:25,bottom:75},xAxis:{type:'value',name:timed?'仿真时间 (s)':'样本窗口',nameLocation:'middle',nameGap:30},yAxis:{type:'value',name:yName,scale:true},dataZoom:[{type:'inside'},{type:'slider'}]})
const hiChart=computed(()=>{const r=result.value;if(!hasHi.value)return {};const times=r.hi_times,timed=Boolean(hiSource.value.time_column)&&Array.isArray(times)&&times.length===r.hi_sequence.length;return {...chartAxes(timed,'HI'),yAxis:{type:'value',name:'HI',min:0,max:1},series:[{name:'HI',type:'line',showSymbol:false,data:r.hi_sequence.map((v,i)=>[timed?times[i]:i,v])}]}})
const chart=computed(()=>{const r=result.value;if(!hasSeries.value)return {};const names=['CNN','BiRNN','BiLSTM','BiGRU','SRNN'],times=r.rul_times,timed=Boolean(hiSource.value.time_column)&&Array.isArray(times)&&times.length===r.ensemble_rul.RF.length;const points=values=>(values||[]).map((v,i)=>[timed?times[i]:i,v]);return {...chartAxes(timed,`剩余寿命 (${r.unit||'未提供'})`),legend:{data:[...names,'RF','Ada']},series:[...names.map(n=>({name:n,type:'line',showSymbol:false,data:points(r.model_predictions?.[n])})),{name:'RF',type:'line',showSymbol:false,lineStyle:{width:3},data:points(r.ensemble_rul.RF)},{name:'Ada',type:'line',showSymbol:false,lineStyle:{width:3,type:'dashed'},data:points(r.ensemble_rul.Ada)}]}})
function clearDetail(){result.value=null;activeDatasetId.value=null;selectedBatchError.value='';error.value=''}
function reset(){clearDetail();batchReport.value=null}
function onDatasetChange(){reset();const aliases={'氧涡轮':'液氧涡轮'};const names=[...new Set(selectedDatasets.value.filter(item=>item.structure_node_name).map(item=>aliases[item.structure_node_name]||item.structure_node_name))];if(names.length===1){const match=componentOptions.find(item=>item.name===names[0]);if(match)componentId.value=match.id}}
function onAlgorithmChange(){reset();pluginParameters.value=Object.fromEntries(pluginFields.value.map(({name,definition})=>[name,definition.default??(definition.type==='boolean'?false:definition.type==='string'?'':definition.minimum??0)]))}
function showBatchResult(row){activeDatasetId.value=row.dataset_id;result.value=row.status==='success'?row.result:null;activeComponentId.value=String(row.result?.component_id||componentId.value);selectedBatchError.value=row.status==='success'?'':row.error||row.result?.message||row.message||'预测失败';error.value=''}
const csrfHeaders=()=>{const token=document.cookie.split('; ').find(x=>x.startsWith('csrftoken='))?.slice(10);return token?{'X-CSRFToken':decodeURIComponent(token)}:{}}
onMounted(async()=>{mobileQuery.addEventListener('change',updateColumns);try{const [datasetResponse,catalogResponse]=await Promise.all([fetch('/api/v1/datasets/',{credentials:'include'}),fetch('/api/v1/integrations/algorithm-assets/algorithms/?category=rul',{credentials:'include'})]);if(!datasetResponse.ok)throw Error('数据集加载失败');datasets.value=await datasetResponse.json();const requested=Number(route.query.dataset_id);if(selectableDatasets.value.some(item=>item.id===requested)){id.value=requested;onDatasetChange()}if(catalogResponse.ok){const body=await catalogResponse.json();const choices=(body.results||[]).filter(item=>item.key==='health_main_ensemble'||item.source==='plugin');if(choices.length)algorithmOptions.value=choices}}catch(e){error.value=e.message}})
onBeforeUnmount(()=>mobileQuery.removeEventListener('change',updateColumns))
async function run(){if(mode.value!=='single'||algorithm.value==='health_main_ensemble'&&(!componentId.value||componentMismatch.value))return;clearDetail();loading.value=true;const datasetId=id.value,selectedComponentId=componentId.value,algorithmKey=algorithm.value;try{const plugin=selectedAlgorithm.value?.source==='plugin';const url=plugin?`/api/v1/integrations/algorithm-assets/algorithms/${algorithmKey}/run/`:'/api/v1/rul/predict/';const payload=plugin?{dataset_id:datasetId,parameters:pluginParameters.value}:{dataset_id:datasetId,algorithm:'health_main_ensemble',component_id:selectedComponentId};const response=await fetch(url,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json',...csrfHeaders()},body:JSON.stringify(payload)});const body=await response.json();if(!response.ok||body.status==='error'||plugin&&!body.ok)throw Error(body.message||body.error||'预测失败');if(mode.value!=='single'||algorithm.value!==algorithmKey||id.value!==datasetId)return;activeDatasetId.value=datasetId;activeComponentId.value=selectedComponentId;result.value=plugin?body.result:body}catch(e){if(mode.value==='single'&&algorithm.value===algorithmKey&&id.value===datasetId)error.value=e.message}finally{loading.value=false}}
async function runBatch(){if(mode.value!=='batch'||algorithm.value==='health_main_ensemble'&&(!componentId.value||componentMismatch.value))return;clearDetail();batchReport.value=null;batchLoading.value=true;const selectedComponentId=componentId.value,algorithmKey=algorithm.value;try{const plugin=selectedAlgorithm.value?.source==='plugin';const url=plugin?`/api/v1/integrations/algorithm-assets/algorithms/${algorithmKey}/batch-run/`:'/api/v1/rul/predict/';const payload=plugin?{dataset_ids:batchIds.value,parameters:pluginParameters.value}:{dataset_ids:batchIds.value,algorithm:'health_main_ensemble',component_id:selectedComponentId};const response=await fetch(url,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json',...csrfHeaders()},body:JSON.stringify(payload)});const body=await response.json();if(!response.ok||body.status==='error'||plugin&&!body.ok)throw Error(body.message||body.error||'批量预测失败');if(mode.value!=='batch'||algorithm.value!==algorithmKey)return;batchReport.value=body;activeComponentId.value=selectedComponentId;const first=body.results?.find(item=>item.status==='success')||body.results?.[0];if(first)showBatchResult(first)}catch(e){if(mode.value==='batch'&&algorithm.value===algorithmKey)error.value=e.message}finally{batchLoading.value=false}}
</script>
<style scoped>.analysis-page{max-width:1250px;min-width:0;color:#253448}.controls{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:20px 0}.controls .el-select{width:300px;max-width:100%}.controls label{display:flex;gap:8px;align-items:center;font-size:14px;min-width:0;max-width:100%}.controls label .el-select{flex:1;min-width:0}.model-contract{display:flex;flex-wrap:wrap;gap:12px 24px;font-size:13px;color:#627181}.plugin-parameters{margin:16px 0;padding:12px;background:#f6f9fc}.plugin-parameters .el-select,.plugin-parameters .el-input{width:190px}.batch-results,.report{margin-top:20px;min-width:0}.row-error{color:#c45656}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-block:1px solid #dce4ec;margin:24px 0;padding:24px 0;gap:20px}.metrics small,.metrics strong,.metrics span{display:block}.metrics strong{font-size:24px;margin:10px 0;overflow-wrap:anywhere}.metrics span{font-size:12px;color:#627181}.el-alert{margin-top:16px}:deep(.el-alert__content),:deep(.el-descriptions__content){min-width:0;overflow-wrap:anywhere}h3{font-size:17px;margin-top:28px}p{line-height:1.7}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:400px;overflow:auto}details{margin-top:20px}@media(max-width:800px){.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:450px){.controls{gap:12px}.controls>.el-select,.controls label{width:100%}.report :deep(.el-card__body){padding:14px}.metrics{gap:16px}.metrics strong{font-size:21px}}</style>
