<template>
  <div class="page">
    <el-card class="toolbar">
      <el-form :inline="true" :model="q">
        <el-form-item label="CMG">
          <el-select v-model="q.cmgId" filterable clearable placeholder="选择CMG" style="min-width:240px" @change="loadResults">
            <el-option v-for="c in cmgs" :key="c.cmg_id" :label="c.name + '(' + c.cmg_id + ')'" :value="c.cmg_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker v-model="q.range" type="datetimerange" range-separator="至" start-placeholder="开始" end-placeholder="结束" value-format="YYYY-MM-DD HH:mm:ss" @change="loadResults" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadResults">查询</el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <div style="margin-bottom: 16px;">
        <span>共找到 {{ statistics.msfg_results?.count || rows.length }} 条MSFG分析结果</span>
        <el-tag v-if="statistics.msfg_results?.last_updated" size="small" type="info" style="margin-left: 8px;">
          更新时间: {{ new Date(statistics.msfg_results.last_updated).toLocaleString() }}
        </el-tag>
        <el-button 
          size="small" 
          type="primary" 
          text 
          @click="refreshStatistics"
          :loading="statsLoading"
          style="margin-left: 8px;"
          title="刷新统计信息"
        >
          <el-icon><Refresh /></el-icon>
          刷新统计
        </el-button>
      </div>
      
      <el-table :data="pagedRows" border size="small" v-loading="loading" @row-dblclick="openDetail">
        <el-table-column type="index" width="60" label="#" />
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="cmg_id" label="CMG" width="160" />
        <el-table-column prop="msfg_name" label="配置" width="200" />
        <el-table-column label="健康分" width="120">
          <template #default="s">{{ healthScoreFromRow(s.row) }}</template>
        </el-table-column>
        <el-table-column label="故障TOP3 (部件)">
          <template #default="s">
            <span v-for="comp in topComponents(s.row, 3)" :key="comp.name" style="margin-right:8px;">
              <el-tag size="small" :type="getHealthTag(comp.health)">
                {{ comp.name }}: {{ comp.health.toFixed(3) }}
              </el-tag>
            </span>
          </template>
        </el-table-column>
        <el-table-column width="120" label="操作">
          <template #default="s">
            <el-button size="small" text type="primary" @click="openDetail(s.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div style="margin-top: 16px; text-align: center;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[50, 100, 200, 500, 1000]"
          :total="rows.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-drawer v-model="showDetail" title="MSFG 结果详情" size="50%">
      <div v-if="current">
        <el-descriptions :column="2" size="small" border>
          <el-descriptions-item label="时间">{{ current.timestamp }}</el-descriptions-item>
          <el-descriptions-item label="CMG">{{ current.cmg_id }}</el-descriptions-item>
          <el-descriptions-item label="配置">{{ current.msfg_name }}</el-descriptions-item>
          <el-descriptions-item label="健康分">{{ Number(current.overall_health_score||0).toFixed(3) }}</el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-top:12px;">测试点分数</h4>
        <div style="margin-bottom: 8px; font-size: 12px; color: #666;">
          <el-icon><InfoFilled /></el-icon>
          <span style="margin-left: 4px;">分数越高表示异常程度越严重（0=正常，1=严重异常）</span>
        </div>
        <el-table :data="kv(current.test_results)" size="small" border>
          <el-table-column prop="k" label="测试点" width="240" />
          <el-table-column prop="v" label="分数">
            <template #default="s">
              <el-tag :type="getTestScoreTag(Number(s.row.v||0))" size="small">
                {{ Number(s.row.v||0).toFixed(3) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <h4 style="margin-top:12px;">故障分数</h4>
        <div style="margin-bottom: 8px; font-size: 12px; color: #666;">
          <el-icon><InfoFilled /></el-icon>
          <span style="margin-left: 4px;">分数越高表示故障概率越大（0=无故障，1=确定故障）</span>
        </div>
        <el-table :data="kv(current.fault_results)" size="small" border>
          <el-table-column prop="k" label="故障" width="240" />
          <el-table-column prop="v" label="分数">
            <template #default="s">
              <el-tag :type="getFaultScoreTag(Number(s.row.v||0))" size="small">
                {{ Number(s.row.v||0).toFixed(3) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>



        <h4 style="margin-top:12px;">部件健康分析详情</h4>
        <div v-if="current.component_results && Object.keys(current.component_results).length > 0">
          <el-table :data="kvComponent(current.component_results)" size="small" border>
            <el-table-column prop="component" label="部件" width="160" />
            <el-table-column prop="health_score" label="健康分数" width="100">
              <template #default="s">
                <el-tag :type="getHealthTag(s.row.health_score)">
                  {{ Number(s.row.health_score||1).toFixed(3) }}
                </el-tag>
              </template>
            </el-table-column>
            
            
          </el-table>
        </div>
        <div v-else>
          <el-empty description="暂无部件分析数据" />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { InfoFilled, SuccessFilled, Refresh } from '@element-plus/icons-vue';
import api from '../api';

defineOptions({ name: 'MSFGResults' });

const loading = ref(false);
const rows = ref([]);
const cmgs = ref([]);
const showDetail = ref(false);
const current = ref(null);
const currentPage = ref(1);
const pageSize = ref(100);  // 默认每页显示100条
const statistics = ref({});
const statsLoading = ref(false);

const q = ref({
  cmgId: '',
  range: []
});

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return rows.value.slice(start, end);
});

function kv(obj){
  const out = [];
  if (!obj) return out;
  for (const k of Object.keys(obj)) {
    let v = obj[k];
    // 处理嵌套对象：如果值是对象且包含score字段，则提取score
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      if (v.score !== undefined) {
        v = v.score;  // 测试点结果
      } else if (v.fault_probability !== undefined) {
        v = v.fault_probability;  // 故障结果
      } else if (v.fuzzy_probability !== undefined) {
        v = v.fuzzy_probability;  // 备选故障结果
      }
    }
    out.push({k, v});
  }
  return out;
}

function kvComponent(obj){
  const out=[]; if(!obj) return out; 
  for(const [component, data] of Object.entries(obj)){ 
    out.push({component, ...data}); 
  } 
  return out;
}

function getTestScoreTag(score) {
  if (score <= 0.2) return 'success';  // 正常
  if (score <= 0.5) return 'warning';  // 轻微异常
  return 'danger';                     // 严重异常
}

function getFaultScoreTag(score) {
  if (score <= 0.2) return 'success';  // 无故障
  if (score <= 0.5) return 'warning';  // 可能故障
  return 'danger';                     // 确定故障
}

function getFaultCountTag(count) {
  if (count === 0) return 'success';   // 无故障
  if (count <= 2) return 'warning';    // 少量故障
  return 'danger';                     // 多个故障
}

function getSystemHealthTag(score) {
  if (score <= 0.2) return 'success';  // 系统健康
  if (score <= 0.5) return 'warning';  // 系统预警
  return 'danger';                     // 系统故障
}

function getHealthTag(score){
  const healthScore = Number(score || 1);
  // 统一逻辑：健康分数越高越健康
  if (healthScore >= 0.8) return 'success';   // 健康
  if (healthScore >= 0.6) return 'warning';   // 预警
  return 'danger';                            // 故障
}

function averageFault(row){
  const v = Number(row?.system_results?.average_fault_score || 0);
  return v.toFixed(3);
}

// 统一列表页“健康分”来源：取详情顶部同一口径（组件健康均值）
function healthScoreFromRow(row){
  const comp = row?.component_results || {};
  const vals = [];
  for (const data of Object.values(comp)) {
    let raw = (data && typeof data === 'object') ? data.health_score : data;
    if (typeof raw === 'string') raw = raw.trim();
    if (raw === '' || raw === null || raw === undefined) {
      // 空值视为健康(1.0)，以免被误判为0
      vals.push(1);
      continue;
    }
    const num = Number(raw);
    if (Number.isFinite(num)) vals.push(Math.min(1, Math.max(0, num)));
  }
  if (vals.length === 0) return '1.000';
  const avg = vals.reduce((a,b)=>a+b,0) / vals.length;
  return avg.toFixed(3);
}

function topComponents(row, n){
  // 使用与详情页面相同的数据处理方式
  const componentData = kvComponent(row?.component_results || {});
  
  // 转换为健康分数数组并排序
  const entries = componentData.map(item => ({
    name: item.component,
    health: Number(item.health_score || 1)
  }));
  
  // 按健康分数升序排序（分数越低越不健康），取前n个
  entries.sort((a, b) => a.health - b.health);
  return entries.slice(0, n);
}



function topFaults(obj, n){
  if(!obj) return {};
  const entries = Object.entries(obj).sort((a,b)=>Number(b[1]||0)-Number(a[1]||0)).slice(0,n);
  const res={}; for(const [k,v] of entries){ res[k]=v; } return res;
}

async function loadCmgs(){
  const res = await api.get('/data/cmgs/');
  cmgs.value = res.data || [];
}

async function loadStatistics() {
  try {
    const params = {};
    if (q.value.cmgId) params.cmg_id = q.value.cmgId;
    const res = await api.get('/data/data/statistics/', { params });
    statistics.value = res.data.statistics || {};
  } catch (e) {
    console.error('加载统计信息失败:', e);
    statistics.value = {};
  }
}

async function refreshStatistics() {
  statsLoading.value = true;
  try {
    const params = { refresh: 'true' };
    if (q.value.cmgId) params.cmg_id = q.value.cmgId;
    const res = await api.get('/data/data/statistics/', { params });
    statistics.value = res.data.statistics || {};
    ElMessage.success('统计信息已刷新');
  } catch (e) {
    console.error('刷新统计信息失败:', e);
    ElMessage.error('刷新统计信息失败');
  } finally {
    statsLoading.value = false;
  }
}

async function loadResults(){
  loading.value=true;
  try{
    const params={};
    if(q.value.cmgId) params.cmg_id = q.value.cmgId;
    if(Array.isArray(q.value.range) && q.value.range.length===2){
      params.start_time = q.value.range[0];
      params.end_time = q.value.range[1];
    }
    params.limit = 500;
    const res = await api.get('/msfg/results/', { params });
    rows.value = Array.isArray(res.data)? res.data : (res.data.results||[]);
    
    // 同时加载统计信息
    await loadStatistics();
  }finally{ loading.value=false; }
}

function openDetail(row){ current.value=row; showDetail.value=true; }
function reset(){ q.value={ cmgId:'', range:[] }; loadResults(); }

function handleSizeChange(newSize) {
  pageSize.value = newSize;
  currentPage.value = 1;
}

function handleCurrentChange(newPage) {
  currentPage.value = newPage;
}

onMounted(async()=>{ 
  await loadCmgs(); 
  // 初始加载时只加载第一页数据，提高加载速度
  currentPage.value = 1;
  await loadResults(); 
});

// 监听Dashboard的刷新事件
window.addEventListener('dashboard-refresh', async () => {
  await loadStatistics();
});
</script>

<style scoped>
.page { padding: 12px; }
.toolbar { margin-bottom: 12px; }
</style>


