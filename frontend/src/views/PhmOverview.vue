<template>
  <div class="overview">
    <section class="hero"><div><span class="eyebrow">REUSABLE LAUNCH VEHICLE HEALTH MANAGEMENT PLATFORM</span><h2>综合健康态势</h2><p>监测、诊断、评估、预测与仿真统一工作台</p></div><el-button type="primary" :loading="loading" @click="loadStatus">刷新平台状态</el-button></section>
    <section class="panel"><header><div><h3>PHM能力链</h3><p>平台核心业务闭环</p></div><el-tag type="success">{{ readyCount }}/4 项已接入</el-tag></header><div class="chain"><div v-for="(c,i) in capabilities" :key="c.key" class="chain-item"><div class="step">0{{i+1}}</div><strong>{{c.name}}</strong><span>{{c.desc}}</span><el-tag size="small" :type="c.type">{{c.status}}</el-tag><el-button v-if="c.path" link type="primary" @click="$router.push(c.path)">进入模块 →</el-button></div></div></section>
    <section class="panel services"><header><div><h3>服务与数据状态</h3><p>实时检查后端算法和仿真数据</p></div></header><div class="service-grid"><div><span>故障诊断 Hier14</span><b :class="diag?'ok':'warn'" :title="diagError">{{diag?'已加载':'未启用'}}</b></div><div><span>健康评估适配器</span><b :class="health?'ok':'warn'">{{health?'已加载':'未启用'}}</b></div><div><span>寿命预测集成模型</span><b :class="rul?'ok':'warn'">{{rul?'模型与运行时就绪':'未就绪'}}</b></div><div><span>仿真数据回放</span><b :class="simulation?'ok':'warn'">{{simulation?'已接入':'待配置'}}</b></div><div><span>MATLAB 实时仿真</span><b :class="matlab?'ok':'warn'">{{matlab?'已配置':'需配置本机 MATLAB'}}</b></div></div><el-alert v-if="!diag && diagError" :title="`Hier14 加载原因:${diagError}`" type="warning" :closable="false" style="margin-top:14px" /></section>
  </div>
</template>
<script setup>
import {ref,computed,onMounted} from 'vue';import{ElMessage}from'element-plus';
const loading=ref(false),diag=ref(false),health=ref(false),rul=ref(false),matlab=ref(false),simulation=ref(false),diagError=ref('');
const capabilities=computed(()=>[{key:'monitor',name:'状态监测',desc:'多源遥测与趋势',status:'框架就绪',type:'success',path:'/telemetry'},{key:'diag',name:'故障诊断',desc:'Hier14 14类诊断模型',status:diag.value?'已加载':'模型未就绪',type:diag.value?'success':'warning',path:'/fault-diagnosis'},{key:'health',name:'平台算法评估',desc:'系统健康度与告警',status:health.value?'已接入(开发)':'模型未就绪',type:health.value?'success':'warning',path:'/platform-health'},{key:'rul',name:'寿命预测',desc:'集成模型与健康趋势',status:rul.value?'模型与运行时就绪':'模型未就绪',type:rul.value?'success':'warning',path:'/lifetime-prediction'}]);
const readyCount=computed(()=>[true,diag.value,health.value,rul.value].filter(Boolean).length);
async function loadStatus(){
  loading.value=true;
  try{
    const urls=['/api/v1/fault-diagnosis/status/','/api/v1/health-assessment/status/','/api/v1/phm/status/','/api/v1/rul/status/','/api/v1/simulation-demo/sample/'];
    const results=await Promise.allSettled(urls.map(async url=>{const response=await fetch(url);if(!response.ok)throw new Error(`${url}: HTTP ${response.status}`);return response.json()}));
    const [d,h,s,r,m]=results.map(result=>result.status==='fulfilled'?result.value:{});
    diag.value=!!d.available;diagError.value=d.error||(results[0].status==='rejected'?results[0].reason.message:'');
    health.value=!!h.available;rul.value=!!r.available;simulation.value=!!s.simulation_data_loaded;matlab.value=!!m.runtime?.available;
    if(!diag.value&&diagError.value)ElMessage.warning(`Hier14 未启用:${diagError.value}`);
    else if(results.slice(0,4).some(result=>result.status==='rejected'))ElMessage.warning('部分服务状态读取失败，请检查后端日志');
    else ElMessage.success('平台状态已更新');
  }finally{loading.value=false}
}onMounted(loadStatus)
</script>
<style scoped>.overview{padding:0}.hero{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.eyebrow{color:#2782e8;font-size:11px;font-weight:700;letter-spacing:1.5px}.hero h2{font-size:25px;margin:7px 0;color:#192d45}.hero p,.panel header p{margin:0;color:#8593a6;font-size:13px}.panel{background:#fff;border:1px solid #e7ebf1;border-radius:11px;box-shadow:0 5px 20px #18385b0a;padding:20px;margin-bottom:18px}.panel header{display:flex;justify-content:space-between;border-bottom:1px solid #edf0f4;padding-bottom:14px;margin-bottom:16px}.panel h3{margin:0 0 5px;font-size:18px}.chain{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.chain-item{background:#f7f9fc;border:1px solid #e9edf3;border-radius:9px;padding:16px}.step{font-size:11px;color:#3789e6;font-weight:800}.chain-item strong,.chain-item span{display:block}.chain-item strong{margin:8px 0 5px;font-size:17px}.chain-item span{height:32px;color:#7d8ca0;font-size:13px}.chain-item .el-button{display:block;padding-left:0;margin-top:8px}.service-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:0 30px}.service-grid div{display:flex;justify-content:space-between;padding:13px 0;border-bottom:1px dashed #e6eaf0;font-size:14px}.service-grid b{font-weight:500}.ok{color:#17a878}.warn{color:#d28a35}@media(max-width:900px){.chain{grid-template-columns:repeat(2,1fr)}}@media(max-width:600px){.chain,.service-grid{grid-template-columns:1fr}}
</style>
