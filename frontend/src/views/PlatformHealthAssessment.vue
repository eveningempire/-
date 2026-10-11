<template>
  <div class="page">
    <h2>健康评估 · {{level==='single'?'单机级':'系统级'}}</h2>
    <el-tabs v-model="level"><el-tab-pane label="单机级" name="single" :disabled="loading"/><el-tab-pane label="系统级" name="system" :disabled="loading"/></el-tabs>
    <el-radio-group v-if="level==='single'" v-model="mode" :disabled="loading" @change="clear"><el-radio-button label="single">单个评估</el-radio-button><el-radio-button label="batch">批量评估</el-radio-button></el-radio-group>
    <div class="controls">
      <template v-if="level==='single'"><el-select v-if="mode==='single'" v-model="id" :disabled="loading" filterable placeholder="选择数据集" @change="clear"><el-option v-for="item in selectableDatasets" :key="item.id" :label="item.name" :value="item.id"/></el-select><el-select v-else v-model="batchIds" :disabled="loading" multiple collapse-tags collapse-tags-tooltip :multiple-limit="100" filterable placeholder="选择批量评估数据集" @change="clear"><el-option v-for="item in selectableDatasets" :key="item.id" :label="item.name" :value="item.id"/></el-select></template>
      <template v-else><el-select v-model="system" :disabled="loading" placeholder="选择系统" @change="systemDatasetIds=[];clear()"><el-option v-for="name in systems" :key="name" :label="name" :value="name"/></el-select><el-select v-model="systemDatasetIds" :disabled="loading" multiple collapse-tags filterable placeholder="选择该系统的数据集" @change="clear"><el-option v-for="item in systemDatasets" :key="item.id" :label="item.name" :value="item.id"/></el-select></template>
      <el-select v-model="algorithm" :disabled="loading" @change="clear"><template v-if="level==='single'"><el-option label="CDPCA-GA 特征融合" value="cdpca_ga"/><el-option label="AE-GMM 数据驱动" value="ae_gmm"/></template><el-option v-else label="GCN + RBD 系统健康评估" value="gcn_rbd"/></el-select>
      <el-button type="primary" :disabled="!canRun" :loading="loading" @click="run">{{isBatch?'批量评估':'运行评估'}}</el-button>
    </div>
    <el-alert v-if="error" type="error" :title="error" :closable="false" show-icon/>
    <section v-if="isBatch&&batchReport" class="batch-results">
      <h3>批量评估结果</h3>
      <el-alert type="info" :title="`评估完成：共 ${batchReport.total} 份，成功 ${batchReport.success}，失败 ${batchReport.failed}`" :closable="false"/>
      <el-table :data="batchReport.results" row-key="dataset_id" highlight-current-row :current-row-key="activeIds[0]" @row-click="showBatchResult">
        <el-table-column label="数据集" min-width="210"><template #default="scope">{{datasetName(scope.row.dataset_id)}}</template></el-table-column>
        <el-table-column label="状态" width="90"><template #default="scope"><el-tag :type="scope.row.status==='success'?'success':'danger'">{{scope.row.status==='success'?'成功':'失败'}}</el-tag></template></el-table-column>
        <el-table-column label="健康指数" width="110"><template #default="scope">{{scope.row.result?format(scope.row.result.health_index):'未评估'}}</template></el-table-column>
        <el-table-column label="健康等级" width="100"><template #default="scope">{{scope.row.result?healthGrade(scope.row.result.health_index):'未评估'}}</template></el-table-column>
        <el-table-column label="样本数" width="100"><template #default="scope">{{scope.row.result?.hi_sequence?.length??'未评估'}}</template></el-table-column>
        <el-table-column label="详情" min-width="190"><template #default="scope"><el-button v-if="scope.row.status==='success'" link type="primary" @click.stop="showBatchResult(scope.row)">查看详情</el-button><span v-else class="batch-error">{{scope.row.error}}</span></template></el-table-column>
      </el-table>
    </section>
    <el-alert v-if="selectedBatchError" type="error" :title="selectedBatchError" :closable="false" show-icon/>
    <el-card v-if="result" shadow="never" class="report">
      <template #header><div class="report-head"><b>{{result.algorithm}} 评估报告</b><span>{{activeDatasets.map(item=>item.name).join('、')}}</span></div></template>
      <el-descriptions border :column="2"><el-descriptions-item label="评估层级">{{levelLabels[result.level]||result.level}}</el-descriptions-item><el-descriptions-item label="当前健康指数">{{format(result.health_index)}}</el-descriptions-item><el-descriptions-item label="健康等级">{{grade}}</el-descriptions-item><el-descriptions-item label="样本数">{{result.hi_sequence?.length||0}}</el-descriptions-item><el-descriptions-item label="PBS 对应">{{pbsNames||'未关联 PBS 单机产品'}}</el-descriptions-item><el-descriptions-item label="结果属性">相对正常参考的状态评估，尚未按型号标定</el-descriptions-item><el-descriptions-item label="正常参考" :span="2">{{referenceLabel}}</el-descriptions-item></el-descriptions>
      <el-alert v-if="!pbsNames" type="warning" title="数据集尚未关联 PBS；结构树不会自动改变健康评估计算。" :closable="false"/>
      <el-alert type="info" title="HI 越接近 1 越健康，偏离正常参考时下降，状态恢复时可回升。寿命预测使用其训练模型配套的预处理。" :closable="false"/>
      <h3>健康指数趋势</h3><ReportChart :key="`health-${runKey}`" :option="healthChart" :height="450"/>
      <template v-if="result.component_hi_sequences&&Object.keys(result.component_hi_sequences).length"><h3>各部件健康趋势</h3><ReportChart :key="`components-${runKey}`" :option="componentChart" :height="450"/></template>
      <details><summary>查看评估输出</summary><pre>{{JSON.stringify(result,null,2)}}</pre></details>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import ReportChart from '../components/ReportChart.vue'
import { isSelectableDataset } from '../utils/datasetVisibility.js'

const route = useRoute()
const levelLabels = { single:'单机级', component:'单机级', system:'系统级' }
const datasets = ref([]), level = ref('single'), mode = ref('single'), id = ref(null), batchIds = ref([]), batchReport = ref(null), selectedBatchError = ref(''), system = ref(''), systemDatasetIds = ref([]), algorithm = ref('cdpca_ga'), result = ref(null), loading = ref(false), error = ref(''), runKey = ref(0), activeIds = ref([])
const systems = ['控制', '动力']
const isBatch = computed(() => level.value==='single'&&mode.value==='batch')
const canRun = computed(() => level.value==='system'?systems.includes(system.value)&&systemDatasetIds.value.length>0:isBatch.value?batchIds.value.length>0:!!id.value)
const selectableDatasets = computed(() => datasets.value.filter(isSelectableDataset))
const systemDatasets = computed(() => selectableDatasets.value.filter(item => item.system === system.value))
const activeDatasets = computed(() => datasets.value.filter(item => activeIds.value.some(value => String(value) === String(item.id))))
const pbsNames = computed(() => [...new Set(activeDatasets.value.map(item => item.structure_node_name).filter(Boolean))].join('、'))
const healthGrade = value => Number(value)>=.8?'健康':Number(value)>=.5?'关注':'异常'
const grade = computed(() => healthGrade(result.value?.health_index))
const referenceText = reference => reference?.kind==='normal_dataset'?`${reference.dataset_name}（按时间对齐）`:reference?.kind==='initial_segment'?`初始 ${reference.sample_count} 个样本，假定正常；后续工况变化可能影响结果`:'未提供'
const referenceLabel = computed(() => result.value?.level==='system'?(result.value.component_results||[]).map(item=>`${datasetName(item.dataset_id)}：${referenceText(item.reference)}`).join('；'):referenceText(result.value?.reference))
const format = value => Number.isFinite(Number(value)) ? Number(value).toFixed(4) : '—'
const datasetName = datasetId => datasets.value.find(item=>String(item.id)===String(datasetId))?.name||`数据集 #${datasetId}`
const xValues = computed(() => result.value?.time_sequence?.length === result.value?.hi_sequence?.length ? result.value.time_sequence : (result.value?.hi_sequence||[]).map((_,index)=>index))
const baseChart = (name,series) => ({ legend:{data:series.map(item=>item.name),type:'scroll',top:8},tooltip:{trigger:'axis'},grid:{top:65,bottom:105,left:55,right:40,containLabel:true},xAxis:{type:'value',name:name,scale:true},yAxis:{type:'value',name:'健康指数 HI',min:0,max:1},dataZoom:[{type:'inside'},{type:'slider',bottom:18}],series })
const healthChart = computed(() => baseChart(result.value?.time_sequence?.length ? '时间 / 样本' : '样本序号',[{name:'健康指数',type:'line',data:(result.value?.hi_sequence||[]).map((value,index)=>[xValues.value[index],value])}]))
const componentChart = computed(() => baseChart('时间 / 样本',Object.entries(result.value?.component_hi_sequences||{}).map(([name,values])=>({name,type:'line',data:values.map((value,index)=>[xValues.value[index]??index,value])}))))
function clear(){result.value=null;error.value='';activeIds.value=[];batchReport.value=null;selectedBatchError.value=''}
function showBatchResult(item){activeIds.value=[item.dataset_id];result.value=item.status==='success'?item.result:null;selectedBatchError.value=item.status==='success'?'':`${datasetName(item.dataset_id)}：${item.error}`;runKey.value++}
watch(level,value=>{algorithm.value=value==='system'?'gcn_rbd':'cdpca_ga';clear()})
onMounted(async()=>{try{const response=await fetch('/api/v1/datasets/',{credentials:'include'});if(!response.ok)throw Error('数据集加载失败');datasets.value=await response.json();const requested=Number(route.query.dataset_id);if(selectableDatasets.value.some(item=>item.id===requested))id.value=requested}catch(exc){error.value=exc.message}})
async function run(){
  if(loading.value||!canRun.value)return
  const batch=isBatch.value
  const selectedIds=level.value==='single'?(batch?[...batchIds.value]:[id.value]):[...systemDatasetIds.value]
  clear();loading.value=true
  try{
    const payload=level.value==='single'?(batch?{dataset_ids:selectedIds,algorithm:algorithm.value}:{dataset_id:id.value,algorithm:algorithm.value}):{dataset_ids:selectedIds,system:system.value,algorithm:'gcn_rbd',component_ids:selectedIds.map(datasetId=>{const item=datasets.value.find(value=>String(value.id)===String(datasetId));return item?.structure_node_key||`dataset_${datasetId}`})}
    const response=await fetch(`/api/v1/health-assessment/${batch?'batch-evaluate':'evaluate'}/`,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    const body=await response.json()
    if(!response.ok||!body.ok)throw Error(body.error||'评估失败')
    if(batch){batchReport.value=body;const first=body.results.find(item=>item.status==='success')||body.results[0];if(first)showBatchResult(first)}
    else{result.value=body.result;activeIds.value=selectedIds;runKey.value++}
  }catch(exc){error.value=exc.message}finally{loading.value=false}
}
</script>

<style scoped>
.page{max-width:1300px;min-width:0}.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:16px 0}.controls .el-select{width:280px;max-width:100%}.batch-results{margin:24px 0}.batch-results .el-alert{margin-bottom:12px}.batch-error{color:#c45656;overflow-wrap:anywhere}.report{margin-top:18px}.report-head{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;min-width:0}.report-head span{font-size:12px;color:#718198;overflow-wrap:anywhere;min-width:0}.report .el-alert{margin-top:14px}.report h3{margin:26px 0 12px}.report details{margin-top:20px}.report pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:360px;overflow:auto}@media(max-width:700px){.report-head{display:block}}
</style>
