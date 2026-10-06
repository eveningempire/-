<template>
  <div class="page">
    <h2>健康评估 · {{level==='single'?'单机级':'系统级'}}</h2>
    <p class="note">单机级 CDPCA-GA / AE-GMM；系统级 GCN + RBD。图表使用本次运行的真实返回序列。</p>
    <el-tabs v-model="level"><el-tab-pane label="单机级" name="single"/><el-tab-pane label="系统级" name="system"/></el-tabs>
    <div class="controls">
      <el-select v-if="level==='single'" v-model="id" filterable placeholder="选择数据集" @change="clear"><el-option v-for="item in datasets" :key="item.id" :label="item.name" :value="item.id"/></el-select>
      <template v-else><el-select v-model="system" filterable placeholder="选择系统" @change="systemDatasetIds=[];clear()"><el-option v-for="name in systems" :key="name" :label="name" :value="name"/></el-select><el-select v-model="systemDatasetIds" multiple collapse-tags filterable placeholder="选择该系统的数据集" @change="clear"><el-option v-for="item in systemDatasets" :key="item.id" :label="item.name" :value="item.id"/></el-select></template>
      <el-select v-model="algorithm" @change="clear"><template v-if="level==='single'"><el-option label="CDPCA-GA 特征融合" value="cdpca_ga"/><el-option label="AE-GMM 数据驱动" value="ae_gmm"/></template><el-option v-else label="GCN + RBD 系统健康评估" value="gcn_rbd"/></el-select>
      <el-button type="primary" :disabled="level==='single'?!id:!systemDatasetIds.length" :loading="loading" @click="run">运行评估</el-button>
    </div>
    <el-alert v-if="error" type="error" :title="error" :closable="false" show-icon/>
    <el-card v-if="result" shadow="never" class="report">
      <template #header><div class="report-head"><b>{{result.algorithm}} 评估报告</b><span>{{activeDatasets.map(item=>item.name).join('、')}}</span></div></template>
      <el-descriptions border :column="2"><el-descriptions-item label="评估层级">{{levelLabels[result.level]||result.level}}</el-descriptions-item><el-descriptions-item label="当前健康指数">{{format(result.health_index)}}</el-descriptions-item><el-descriptions-item label="健康等级">{{grade}}</el-descriptions-item><el-descriptions-item label="样本数">{{result.hi_sequence?.length||0}}</el-descriptions-item><el-descriptions-item label="PBS 对应">{{pbsNames||'未关联 PBS 单机产品'}}</el-descriptions-item><el-descriptions-item label="结果属性">当前 CSV 内相对评估，尚未按型号与工况标定</el-descriptions-item></el-descriptions>
      <el-alert v-if="!pbsNames" type="warning" title="数据集尚未关联 PBS；结构树不会自动改变健康评估计算。" :closable="false"/>
      <el-alert type="info" title="此处 HI 由当前数据集内的算法计算；寿命预测模型要求输入 CSV 中另有符合其定义的 HI 列，不能直接将本图数值当作寿命模型输入。" :closable="false"/>
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

const route = useRoute()
const levelLabels = { single:'单机级', component:'单机级', system:'系统级' }
const datasets = ref([]), level = ref('single'), id = ref(null), system = ref(''), systemDatasetIds = ref([]), algorithm = ref('cdpca_ga'), result = ref(null), loading = ref(false), error = ref(''), runKey = ref(0), activeIds = ref([])
const systems = computed(() => [...new Set(datasets.value.map(item => item.system).filter(Boolean))])
const systemDatasets = computed(() => datasets.value.filter(item => item.system === system.value))
const activeDatasets = computed(() => datasets.value.filter(item => activeIds.value.some(value => String(value) === String(item.id))))
const pbsNames = computed(() => [...new Set(activeDatasets.value.map(item => item.structure_node_name).filter(Boolean))].join('、'))
const grade = computed(() => { const value = Number(result.value?.health_index); return value >= .8 ? '健康' : value >= .5 ? '关注' : '异常' })
const format = value => Number.isFinite(Number(value)) ? Number(value).toFixed(4) : '—'
const xValues = computed(() => result.value?.time_sequence?.length === result.value?.hi_sequence?.length ? result.value.time_sequence : (result.value?.hi_sequence||[]).map((_,index)=>index))
const baseChart = (name,series) => ({ legend:{data:series.map(item=>item.name),type:'scroll',top:8},tooltip:{trigger:'axis'},grid:{top:65,bottom:105,left:55,right:40,containLabel:true},xAxis:{type:'value',name:name,scale:true},yAxis:{type:'value',name:'健康指数 HI',min:0,max:1},dataZoom:[{type:'inside'},{type:'slider',bottom:18}],series })
const healthChart = computed(() => baseChart(result.value?.time_sequence?.length ? '时间 / 样本' : '样本序号',[{name:'健康指数',type:'line',data:(result.value?.hi_sequence||[]).map((value,index)=>[xValues.value[index],value])}]))
const componentChart = computed(() => baseChart('时间 / 样本',Object.entries(result.value?.component_hi_sequences||{}).map(([name,values])=>({name,type:'line',data:values.map((value,index)=>[xValues.value[index]??index,value])}))))
function clear(){result.value=null;error.value='';activeIds.value=[]}
watch(level,value=>{algorithm.value=value==='system'?'gcn_rbd':'cdpca_ga';clear()})
onMounted(async()=>{try{const response=await fetch('/api/v1/datasets/',{credentials:'include'});if(!response.ok)throw Error('数据集加载失败');datasets.value=await response.json();const requested=Number(route.query.dataset_id);if(datasets.value.some(item=>item.id===requested))id.value=requested}catch(exc){error.value=exc.message}})
async function run(){if(loading.value)return;clear();loading.value=true;const selectedIds=level.value==='single'?[id.value]:[...systemDatasetIds.value];try{const payload=level.value==='single'?{dataset_id:id.value,algorithm:algorithm.value}:{dataset_ids:selectedIds,algorithm:'gcn_rbd',component_ids:selectedIds.map(datasetId=>{const item=datasets.value.find(value=>String(value.id)===String(datasetId));return item?.structure_node_key||`dataset_${datasetId}`})};const response=await fetch('/api/v1/health-assessment/evaluate/',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const body=await response.json();if(!response.ok||!body.ok)throw Error(body.error||'评估失败');result.value=body.result;activeIds.value=selectedIds;runKey.value++}catch(exc){error.value=exc.message}finally{loading.value=false}}
</script>

<style scoped>
.page{max-width:1300px;min-width:0}.note{color:#60728a}.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:16px 0}.controls .el-select{width:280px;max-width:100%}.report{margin-top:18px}.report-head{display:flex;justify-content:space-between;gap:12px}.report-head span{font-size:12px;color:#718198}.report .el-alert{margin-top:14px}.report h3{margin:26px 0 12px}.report details{margin-top:20px}.report pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:360px;overflow:auto}@media(max-width:700px){.report-head{display:block}}
</style>
