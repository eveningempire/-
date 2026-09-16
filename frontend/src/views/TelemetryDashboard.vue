<template>
<div class="telemetry">
 <header><h2>实时状态监测</h2><el-button @click="openSelector">选择数据源</el-button></header>
 <div class="toolbar"><el-tag>{{ mode === 'live' ? 'MATLAB 实时采集' : mode === 'replay' ? 'CSV 历史回放' : '未选择数据源' }}</el-tag><b>{{name}}</b><span>{{status}}</span>
  <template v-if="mode==='replay'"><el-button :disabled="busy||ended" @click="toggle">{{playing?'暂停回放':'开始回放'}}</el-button><el-button :disabled="busy" @click="reset">从头回放</el-button><el-select v-model="speed" class="speed"><el-option v-for="s in [1,2,5,10]" :key="s" :value="s" :label="`${s} 条/秒`"/></el-select></template>
  <el-button v-if="mode" :disabled="mode==='live'&&!total" @click="download">导出 CSV</el-button><el-button v-if="mode==='live'&&admin&&state!=='closed'" type="danger" plain @click="closeSession">结束采集</el-button>
 </div>
 <el-alert v-if="error" :title="error" type="error" :closable="false"/>
 <p v-if="mode">{{mode==='live'?'已采集':'已播放'}} {{total}} 条<span v-if="received"> · 最后接收 {{new Date(received).toLocaleString()}}</span></p>
 <el-empty v-if="!rows.length" :description="mode==='live'?'等待 MATLAB 上报数据':'请选择数据后开始回放'"/>
 <template v-else><div class="metrics"><div v-for="k in signals.slice(0,4)" :key="k"><small>{{k}}</small><strong>{{rows.at(-1)[k]??'—'}}</strong></div></div><div class="chart-title"><h3>信号趋势（最近 1000 条）</h3><el-select v-model="signal"><el-option v-for="k in signals" :key="k" :value="k" :label="k"/></el-select></div><ReportChart :option="chart"/><h3>最新采样</h3><el-table :data="rows.slice(-20).reverse()" stripe max-height="400"><el-table-column v-for="k in columns" :key="k" :prop="k" :label="k" min-width="130"/></el-table></template>
 <el-dialog v-model="selector" title="选择监测数据源" width="min(680px,94vw)" :close-on-click-modal="false">
  <el-radio-group v-model="choice"><el-radio-button label="replay">CSV 历史回放</el-radio-button><el-radio-button label="live">MATLAB 实时采集</el-radio-button></el-radio-group>
  <el-form label-position="top"><el-form-item v-if="choice==='replay'" label="选择一次仿真或离线上传的数据"><el-select v-model="datasetId" filterable><el-option v-for="d in datasets" :key="d.id" :value="d.id" :label="`${d.name} / ${d.source==='simulation'?'仿真':'离线'} / ${d.fault_type||'未标注'}`"/></el-select></el-form-item>
   <template v-else><el-alert title="实时采集操作流程" type="info" :closable="false" description="管理员先创建采集会话并复制令牌；在 MATLAB/Simulink 中调用 phm_send_telemetry 上报；回到异常告警中心选择同一会话并打开实时检测。"/><el-form-item label="采集会话"><div class="session-row"><el-select v-model="sessionId" filterable placeholder="请选择已有会话"><el-option v-for="s in sessions" :key="s.id" :value="s.id" :label="`${s.name} / ${labels[s.state]} / ${s.sample_count} 条`"/></el-select><el-button @click="refreshSessions">刷新</el-button></div></el-form-item><el-form-item v-if="admin" label="新建本次采集"><div class="session-row"><el-input v-model="sessionName" maxlength="200" placeholder="本次试验名称，如：发动机热试车-2026-09-16"/><el-button type="primary" :loading="creating" :disabled="!sessionName.trim()" @click="createSession">创建并获取 MATLAB 参数</el-button></div></el-form-item><el-alert v-if="!admin" title="当前账号为查看用户，不能创建采集会话；请联系管理员创建并提供会话。" type="warning" :closable="false"/></template>
  </el-form><el-alert v-if="error" :title="error" type="error" :closable="false"/>
  <template #footer><el-button @click="selector=false">取消</el-button><el-button type="primary" :disabled="choice==='replay'?!datasetId:!sessionId" @click="selectSource">{{choice==='replay'?'载入，等待播放':'查看实时采集'}}</el-button></template>
 </el-dialog>
 <el-dialog v-model="connectionDialog" title="MATLAB 连接参数" width="min(760px,94vw)" :close-on-click-modal="false"><p>将 phm_send_telemetry.m 加入 MATLAB 路径，在仿真采样回调中调用下方代码。令牌仅在创建时返回，请保存。远程 MATLAB 请把地址中的 localhost 替换为平台服务器地址。</p><pre>{{connectionCode}}</pre><el-button @click="copy">复制连接参数</el-button></el-dialog>
</div>
</template>
<script setup>
import {ref,computed,onMounted,onUnmounted} from 'vue'
import {ElMessage,ElMessageBox} from 'element-plus'
import ReportChart from '../components/ReportChart.vue'
const datasets=ref([]),sessions=ref([]),datasetId=ref(null),sessionId=ref(null),admin=ref(false),sessionName=ref(''),creating=ref(false)
const selector=ref(true),choice=ref('replay'),mode=ref(''),id=ref(null),name=ref(''),rows=ref([]),columns=ref([]),signal=ref(''),playing=ref(false),ended=ref(false),busy=ref(false),speed=ref(1),error=ref(''),total=ref(0),received=ref(null),state=ref('waiting')
const connection=ref(null),connectionDialog=ref(false)
let timer,generation=0,offset=0,cursor=0,buffer=[],pos=0,more=true,shown=0
const labels={waiting:'等待数据',live:'正在接收',stale:'超过 5 秒未收到数据',closed:'采集已结束'}
const status=computed(()=>error.value?'读取失败':mode.value==='live'?labels[state.value]:ended.value?'回放结束':playing.value?'正在回放':'未播放')
const numeric=v=>v!==null&&v!==undefined&&String(v).trim()!==''&&Number.isFinite(Number(v))?Number(v):null
const timeKey=computed(()=>columns.value.find(k=>k.toLowerCase()==='time'))
const signals=computed(()=>columns.value.filter(k=>k!==timeKey.value&&rows.value.some(r=>numeric(r[k])!==null)))
const chart=computed(()=>({tooltip:{trigger:'axis'},grid:{containLabel:true,left:60,right:35,bottom:75},xAxis:{type:'value',name:timeKey.value||'样本序号'},yAxis:{type:'value',name:signal.value,scale:true},dataZoom:[{type:'inside'},{type:'slider'}],series:[{name:signal.value,type:'line',showSymbol:rows.value.length<2,symbolSize:8,connectNulls:false,data:rows.value.map((r,i)=>[timeKey.value?numeric(r[timeKey.value]):shown-rows.value.length+i,numeric(r[signal.value])])}]}))
const connectionCode=computed(()=>connection.value?`phm_send_telemetry('${new URL(connection.value.ingest_path,location.origin).href}', ...\n  '${connection.value.token}', ...\n  struct('time', t, 'pressure', pressure, 'temperature', temperature));`:'')
async function api(url,body){const token=document.cookie.split('; ').find(x=>x.startsWith('csrftoken='))?.slice(10);const r=await fetch(url,{credentials:'include',...(body!==undefined?{method:'POST',headers:{'Content-Type':'application/json',...(token?{'X-CSRFToken':decodeURIComponent(token)}:{})},body:JSON.stringify(body)}:{})});const j=await r.json();if(!r.ok)throw Error(j.detail||j.error||`请求失败 ${r.status}`);return j}
async function choices(){datasets.value=await api('/api/v1/datasets/');await refreshSessions()}
async function refreshSessions(){sessions.value=await api('/api/v1/phm/telemetry/sessions/');if(!sessionId.value&&sessions.value.length)sessionId.value=sessions.value[0].id}
async function openSelector(){selector.value=true;try{await choices()}catch(e){error.value=e.message}}
function reset(){clearTimeout(timer);generation++;rows.value=[];columns.value=[];signal.value='';playing.value=false;ended.value=false;busy.value=false;error.value='';offset=0;cursor=0;buffer=[];pos=0;more=true;total.value=0;shown=0;received.value=null;state.value='waiting'}
function selectSource(){reset();mode.value=choice.value;id.value=mode.value==='replay'?datasetId.value:sessionId.value;name.value=(mode.value==='replay'?datasets.value:sessions.value).find(x=>x.id===id.value)?.name||'';selector.value=false;if(mode.value==='live')poll(generation)}
function append(batch){shown+=batch.length;rows.value=[...rows.value,...batch].slice(-1000);if(!signals.value.includes(signal.value))signal.value=signals.value[0]||''}
async function step(g){if(g!==generation||!playing.value)return;busy.value=true;try{if(pos>=buffer.length&&more){const j=await api(`/api/v1/datasets/${id.value}/samples/?offset=${offset}&limit=500`);if(g!==generation)return;columns.value=j.columns;buffer=j.rows;pos=0;offset=j.next_offset;more=j.has_more}if(g!==generation||!playing.value)return;if(pos<buffer.length){append([buffer[pos++]]);total.value++}if(pos>=buffer.length&&!more){ended.value=true;playing.value=false;return}timer=setTimeout(()=>step(g),1000/speed.value)}catch(e){if(g===generation){error.value=e.message;playing.value=false}}finally{if(g===generation)busy.value=false}}
function toggle(){clearTimeout(timer);playing.value=!playing.value;if(playing.value){error.value='';step(generation)}}
async function poll(g){try{const j=await api(`/api/v1/phm/telemetry/sessions/${id.value}/samples/?after=${cursor}&limit=500`);if(g!==generation)return;columns.value=j.columns;cursor=j.next_cursor;append(j.rows);total.value=j.sample_count;received.value=j.last_received_at;state.value=j.state;error.value='';if(j.has_more||j.state!=='closed')timer=setTimeout(()=>poll(g),j.has_more?30:1000)}catch(e){if(g===generation){error.value=e.message;timer=setTimeout(()=>poll(g),3000)}}}
async function createSession(){creating.value=true;try{connection.value=await api('/api/v1/phm/telemetry/sessions/',{name:sessionName.value});sessionId.value=connection.value.id;connectionDialog.value=true;sessions.value=await api('/api/v1/phm/telemetry/sessions/')}catch(e){error.value=e.message}finally{creating.value=false}}
async function closeSession(){try{await ElMessageBox.confirm('结束后本会话不再接收数据，仍可导出已采集的 CSV。','结束采集',{type:'warning'});await api(`/api/v1/phm/telemetry/sessions/${id.value}/close/`,{});clearTimeout(timer);generation++;poll(generation)}catch(e){if(e!=='cancel'&&e!=='close')error.value=e.message}}
async function copy(){try{await navigator.clipboard.writeText(connectionCode.value);ElMessage.success('已复制')}catch{ElMessage.error('请选中复制连接参数')}}
function download(){window.open(mode.value==='replay'?`/api/v1/datasets/${id.value}/download/`:`/api/v1/phm/telemetry/sessions/${id.value}/export/`,'_blank')}
onMounted(async()=>{try{admin.value=(await api('/api/v1/permissions/profile/')).role==='admin';await choices()}catch(e){error.value=e.message}})
onUnmounted(()=>{generation++;clearTimeout(timer)})
</script>
<style scoped>
.telemetry{max-width:1400px;min-width:0}header,.toolbar,.chart-title,.session-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap}header,.chart-title{justify-content:space-between}.toolbar{padding:16px 0;border-bottom:1px solid #dde4ed}.speed{width:120px}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:20px;margin:24px 0}.metrics small,.metrics strong{display:block;overflow-wrap:anywhere}.metrics strong{font-size:24px;margin-top:8px}.chart-title .el-select{width:260px}.el-form{margin-top:24px}.el-form .el-select{width:100%}.session-row .el-select,.session-row .el-input{flex:1;min-width:220px}.el-alert{margin:12px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:16px;background:#edf2f7}p{color:#627080;line-height:1.7}@media(max-width:700px){.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
