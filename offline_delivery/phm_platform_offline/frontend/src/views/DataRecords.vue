<template>
  <div class="page">
    <h2>数据集构建和管理</h2>
    <el-form v-if="isAdmin" :model="form" inline>
      <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
      <el-form-item label="故障类型"><el-input v-model="form.fault_type" /></el-form-item>
      <el-form-item label="注入时间"><el-input-number v-model="form.injection_time" /></el-form-item>
      <el-form-item label="发射次数"><el-input-number v-model="form.launch_number" /></el-form-item>
      <el-form-item label="退化程度"><el-input-number v-model="form.degradation" :min="0" :max="1" :step=".1" /></el-form-item>
      <el-form-item label="系统"><el-input v-model="form.system" /></el-form-item>
      <el-form-item label="部件"><el-input v-model="form.component" /></el-form-item>
      <el-form-item><input type="file" accept=".csv" @change="form.file=$event.target.files[0]" /><el-button type="primary" @click="upload">上传</el-button></el-form-item>
    </el-form>
    <el-card shadow="never" class="filters">
      <template #header><div class="filter-head"><b>筛选数据集</b><span>可按条件查询后批量选择训练数据</span></div></template>
      <el-form :model="filters" inline @submit.prevent="search">
        <el-form-item label="关键字"><el-input v-model="filters.q" clearable placeholder="文件名" @keyup.enter="search" /></el-form-item>
        <el-form-item label="来源"><el-input v-model="filters.source" clearable placeholder="如 offline" /></el-form-item>
        <el-form-item label="系统"><el-input v-model="filters.system" clearable /></el-form-item>
        <el-form-item label="部件"><el-input v-model="filters.component" clearable /></el-form-item>
        <el-form-item label="故障类型"><el-input v-model="filters.fault_type" clearable /></el-form-item>
        <el-form-item><el-button type="primary" @click="search">查询</el-button><el-button @click="resetFilters">清空</el-button></el-form-item>
      </el-form>
    </el-card>
    <div class="selection-toolbar"><span>当前筛选结果 {{ rows.length }} 条,已选择 {{ selectedRows.length }} 条</span><el-button type="primary" plain :disabled="!selectedRows.length" @click="saveTrainingSelection">加入训练数据集</el-button><el-button text :disabled="!savedTrainingIds.length" @click="clearTrainingSelection">清除训练选择</el-button></div>
    <el-table :data="rows" row-key="id" v-loading="loading" @selection-change="selectedRows=$event">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="name" label="文件" min-width="180" /><el-table-column prop="source" label="来源" width="100" /><el-table-column prop="fault_type" label="故障类型" min-width="120" /><el-table-column prop="injection_time" label="注入时间" width="100" /><el-table-column prop="launch_number" label="发射次数" width="100" /><el-table-column prop="degradation" label="退化程度" width="100" /><el-table-column prop="system" label="系统" min-width="110" /><el-table-column prop="component" label="部件" min-width="110" />
      <el-table-column label="操作" width="180"><template #default="s"><el-button link type="primary" @click="download(s.row)">下载 CSV</el-button><el-button v-if="isAdmin" link type="danger" @click="remove(s.row)">删除</el-button></template></el-table-column>
    </el-table>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
const rows=ref([]), selectedRows=ref([]), loading=ref(false), isAdmin=ref(false), form=ref({source:'offline'}), filters=ref({q:'',source:'',fault_type:'',system:'',component:''}), savedTrainingIds=ref(JSON.parse(localStorage.getItem('phm.trainingDatasetIds')||'[]'))
const csrfHeaders=()=>{const token=document.cookie.split('; ').find(x=>x.startsWith('csrftoken='))?.slice(10);return token?{'X-CSRFToken':decodeURIComponent(token)}:{}}
async function load(){loading.value=true;try{const params=new URLSearchParams({_:`${Date.now()}`});Object.entries(filters.value).forEach(([k,v])=>{if(v)params.set(k,v)});const r=await fetch(`/api/v1/datasets/?${params}`,{credentials:'include',cache:'no-store'});if(!r.ok)throw Error('数据集加载失败');rows.value=await r.json()}finally{loading.value=false}}
function search(){load().catch(e=>ElMessage.error(e.message))}function resetFilters(){filters.value={q:'',source:'',fault_type:'',system:'',component:''};search()}
function saveTrainingSelection(){savedTrainingIds.value=[...new Set([...savedTrainingIds.value,...selectedRows.value.map(x=>x.id)])];localStorage.setItem('phm.trainingDatasetIds',JSON.stringify(savedTrainingIds.value));ElMessage.success(`已保存 ${savedTrainingIds.value.length} 条训练数据集选择,可在 IMS 模型训练中使用`)}
function clearTrainingSelection(){savedTrainingIds.value=[];localStorage.removeItem('phm.trainingDatasetIds');ElMessage.success('训练数据集选择已清除')}
async function upload(){const f=new FormData();Object.entries(form.value).forEach(([k,v])=>v!==undefined&&v!==null&&f.append(k,v));const r=await fetch('/api/v1/datasets/',{method:'POST',credentials:'include',headers:csrfHeaders(),body:f});if(!r.ok)return ElMessage.error('上传失败:权限不足或文件无效');form.value={source:'offline'};await load();ElMessage.success('数据集已上传')}
function download(row){window.open(`/api/v1/datasets/${row.id}/download/`,'_blank')}
async function remove(row){try{await ElMessageBox.confirm(`将永久删除"${row.name}"及其 CSV 文件。`,'删除数据集',{type:'warning'});const r=await fetch(`/api/v1/datasets/${row.id}/`,{method:'DELETE',credentials:'include',headers:csrfHeaders(),cache:'no-store'});if(!r.ok)throw Error('删除失败');savedTrainingIds.value=savedTrainingIds.value.filter(id=>String(id)!==String(row.id));localStorage.setItem('phm.trainingDatasetIds',JSON.stringify(savedTrainingIds.value));await load();ElMessage.success('数据集已删除')}catch(e){if(e!=='cancel'&&e!=='close')ElMessage.error(e.message||'删除失败')}}
onMounted(async()=>{try{const r=await fetch('/api/v1/permissions/profile/',{credentials:'include'});if(r.ok)isAdmin.value=(await r.json()).role==='admin';await load()}catch(e){ElMessage.error(e.message)}})
</script>
<style scoped>.page{max-width:1400px}.el-form{padding:14px;background:#f7f9fc;margin-bottom:18px}.el-form-item{margin-bottom:12px}.filters{margin-bottom:16px}.filters .el-form{background:transparent;padding:0;margin:0}.filter-head{display:flex;gap:16px;align-items:center}.filter-head span{color:#718198;font-size:13px}.selection-toolbar{display:flex;gap:12px;align-items:center;margin:12px 0;color:#60728a}.selection-toolbar span{margin-right:auto}</style>
