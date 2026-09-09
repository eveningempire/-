<template>
  <div class="ims-results-page">
    <el-card class="toolbar">
      <el-form :model="query" inline>
        <el-form-item label="CMG">
          <el-select v-model="query.cmgId" placeholder="选择 CMG" style="min-width: 260px;">
            <el-option v-for="c in cmgList" :key="c.id" :label="c.name + '(' + c.cmg_id + ')'" :value="c.cmg_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker v-model="query.dates" type="datetimerange" range-separator="-" start-placeholder="开始" end-placeholder="结束" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="query.anomalyOnly">仅显示异常</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadResults">查询</el-button>
          <el-button @click="refresh" style="margin-left:8px;">刷新</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <div style="margin-bottom: 16px;">
        <span>共找到 {{ statistics.ims_results?.count || totalCount }} 条IMS检测结果</span>
        <el-tag v-if="statistics.ims_results?.last_updated" size="small" type="info" style="margin-left: 8px;">
          更新时间: {{ new Date(statistics.ims_results.last_updated).toLocaleString() }}
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
      <el-table :data="rows" v-loading="loading" size="small" border>
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="scope">
            {{ new Date(scope.row.timestamp).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="cmg_id" label="CMG" width="140" />
        <el-table-column prop="ims_model_name" label="模型" width="180" />
        <el-table-column prop="anomaly_score" label="分数" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.is_anomaly ? 'danger' : 'success'">{{ Number(scope.row.anomaly_score).toFixed(3) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_anomaly" label="是否异常" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_anomaly ? 'danger' : 'success'">{{ scope.row.is_anomaly ? '异常' : '正常' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="参数分数">
          <template #default="scope">
            <el-popover placement="top-start" trigger="click" width="400">
              <template #reference>
                <el-button size="small" text>查看</el-button>
              </template>
              <el-table :data="paramScores(scope.row)" size="small" height="240">
                <el-table-column prop="parameter" label="参数" />
                <el-table-column prop="score" label="分数">
                  <template #default="ps">
                    {{ Number(ps.row.score).toFixed(3) }}
                  </template>
                </el-table-column>
              </el-table>
            </el-popover>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div style="margin-top: 16px; text-align: center;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[50, 100, 200, 500, 1000]"
          :total="totalCount"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api';

defineOptions({ name: 'IMSResults' });

const loading = ref(false);
const rows = ref([]);
const cmgList = ref([]);
const query = ref({ cmgId: null, dates: [], anomalyOnly: false });
const currentPage = ref(1);
const pageSize = ref(100);  // 修改默认每页显示100条
const totalCount = ref(0);
const statistics = ref({});
const statsLoading = ref(false);

async function loadCmgs() {
  const res = await api.get('/data/cmgs/');
  cmgList.value = Array.isArray(res.data) ? res.data : [];
}

function paramScores(row) {
  const ps = row.parameter_scores || {};
  return Object.entries(ps).map(([parameter, score]) => ({ parameter, score: Number(score) || 0 }));
}

async function loadStatistics() {
  try {
    const params = {};
    if (query.value.cmgId) params.cmg_id = query.value.cmgId;
    const res = await api.get('/data/data/statistics/', { params });
    console.log('统计API响应:', res.data);
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
    if (query.value.cmgId) params.cmg_id = query.value.cmgId;
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

async function loadResults() {
  loading.value = true;
  try {
    const params = { 
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value 
    };
    if (query.value.cmgId) params.cmg_id = query.value.cmgId;
    if (query.value.anomalyOnly) params.anomaly_only = 'true';
    if (query.value.dates.length === 2) {
      params.start_time = new Date(query.value.dates[0]).toISOString();
      params.end_time = new Date(query.value.dates[1]).toISOString();
    }
    const res = await api.get('/health/ims-results/', { params });
    
    // 假设后端返回 {results: [], count: 总数} 格式
    if (res.data.results) {
      rows.value = Array.isArray(res.data.results) ? res.data.results : [];
      totalCount.value = res.data.count || 0;
    } else {
      // 兼容旧格式
      rows.value = Array.isArray(res.data) ? res.data : [];
      totalCount.value = rows.value.length;
    }
    
    // 同时加载统计信息
    await loadStatistics();
  } catch (e) {
    rows.value = [];
    totalCount.value = 0;
  } finally {
    loading.value = false;
  }
}

function handleSizeChange(size) {
  pageSize.value = size;
  currentPage.value = 1;
  loadResults();
}

function handleCurrentChange(page) {
  currentPage.value = page;
  loadResults();
}

function refresh() { loadResults(); }

onMounted(async () => {
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
.ims-results-page { padding: 12px; }
.toolbar { margin-bottom: 12px; }
</style>


