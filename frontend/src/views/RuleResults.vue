<template>
  <div class="rule-results-page">
    <el-card class="toolbar">
      <el-form :model="query" inline>
        <el-form-item label="CMG">
          <el-select v-model="query.cmgId" placeholder="选择 CMG" style="min-width: 260px;" @change="loadResults">
            <el-option v-for="c in cmgList" :key="c.id" :label="c.name + '(' + c.cmg_id + ')'" :value="c.cmg_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker v-model="query.dates" type="datetimerange" range-separator="-" start-placeholder="开始" end-placeholder="结束" @change="loadResults" />
        </el-form-item>
        <el-form-item label="规则">
          <el-select v-model="query.ruleId" placeholder="选择规则ID" style="min-width: 240px;" clearable filterable @change="loadResults">
            <el-option 
              v-for="rule in rules" 
              :key="rule.rule_id || rule.id"
              :label="rule.rule_id || rule.id"
              :value="rule.rule_id || rule.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="query.triggeredOnly" @change="loadResults">仅显示触发</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadResults">查询</el-button>
          <el-button @click="refresh" style="margin-left:8px;">刷新</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <div style="margin-bottom: 16px;">
        <span>共找到 {{ statistics.rule_results?.count || results.length }} 条规则检测结果</span>
        <el-tag v-if="statistics.rule_results?.last_updated" size="small" type="info" style="margin-left: 8px;">
          更新时间: {{ new Date(statistics.rule_results.last_updated).toLocaleString() }}
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
      
      <el-table :data="results" v-loading="loading" size="small" border>
        <el-table-column prop="timestamp" label="时间" width="180">
          <template #default="scope">
            {{ new Date(scope.row.data_point?.timestamp || scope.row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column prop="cmg_id" label="CMG" width="140">
          <template #default="scope">
            {{ scope.row.data_point?.cmg_id || scope.row.cmg_id }}
          </template>
        </el-table-column>
        <el-table-column prop="rule_name" label="规则名称" width="200">
          <template #default="scope">
            {{ scope.row.rule_definition?.rule_id || scope.row.rule_id || '未知规则' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_triggered" label="是否触发" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_triggered ? 'danger' : 'success'">
              {{ scope.row.is_triggered ? '触发' : '未触发' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="fault_level" label="故障等级" width="100">
          <template #default="scope">
            <el-tag v-if="scope.row.is_triggered" :type="getFaultLevelType(scope.row.fault_definition?.fault_level)">
              等级 {{ scope.row.fault_definition?.fault_level || 1 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="component" label="涉及部件" width="120">
          <template #default="scope">
            {{ scope.row.fault_definition?.component || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="规则详情" min-width="200">
          <template #default="scope">
            <el-popover placement="top-start" trigger="click" width="500">
              <template #reference>
                <el-button size="small" text>查看详情</el-button>
              </template>
              <div>
                <h4>规则表达式</h4>
                <p><code>{{ scope.row.rule_definition?.rule_expression || '无' }}</code></p>
                <h4>检测详情</h4>
                <el-table :data="getDetailsArray(scope.row.detection_details)" size="small" max-height="200">
                  <el-table-column prop="key" label="属性" width="120" />
                  <el-table-column prop="value" label="值" />
                </el-table>
              </div>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column label="数据值" min-width="180">
          <template #default="scope">
            <el-popover placement="top-start" trigger="click" width="400">
              <template #reference>
                <el-button size="small" text>查看数据</el-button>
              </template>
              <el-table :data="getDataArray(scope.row.data_point?.data)" size="small" max-height="240">
                <el-table-column prop="parameter" label="参数" width="150" />
                <el-table-column prop="value" label="值" />
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
import { ref, onMounted, computed } from 'vue';
import api from '../api';

defineOptions({ name: 'RuleResults' });

const loading = ref(false);
const results = ref([]);
const cmgList = ref([]);
const rules = ref([]);
const currentPage = ref(1);
const pageSize = ref(100);  // 修改默认每页显示100条
const totalCount = ref(0);
const statistics = ref({});
const statsLoading = ref(false);

const query = ref({
  cmgId: null,
  dates: [],
  ruleId: null,
  triggeredOnly: false
});



async function loadCmgs() {
  try {
    const res = await api.get('/data/cmgs/');
    cmgList.value = Array.isArray(res.data) ? res.data : [];
  } catch (error) {
    console.error('加载CMG列表失败:', error);
  }
}

async function loadRules() {
  try {
    const params = {};
    // 若已选择CMG，则限定到该 CMG 的模型下的规则
    if (query.value.cmgId) {
      // 需要先获取 CMG 的 cmg_model_id
      if (cmgList.value.length === 0) {
        const cmgRes = await api.get('/data/cmgs/');
        cmgList.value = Array.isArray(cmgRes.data) ? cmgRes.data : [];
      }
      const cmg = cmgList.value.find(c => c.cmg_id === query.value.cmgId);
      if (cmg?.cmg_model) params.cmg_model_id = cmg.cmg_model;
    }
    const res = await api.get('/rules/rules/', { params });
    rules.value = Array.isArray(res.data) ? res.data : [];
  } catch (error) {
    console.error('加载规则列表失败:', error);
  }
}

async function loadStatistics() {
  try {
    const params = {};
    if (query.value.cmgId) params.cmg_id = query.value.cmgId;
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
    // 使用分页参数，避免一次性加载过多数据
    const offset = (currentPage.value - 1) * pageSize.value;
    const params = { 
      limit: pageSize.value,
      offset: offset
    };
    
    if (query.value.cmgId) {
      params.cmg_id = query.value.cmgId;
    }
    
    if (query.value.ruleId) {
      params.rule_id = query.value.ruleId;
    }
    
    if (query.value.triggeredOnly) {
      params.is_triggered = 'true';
    }
    
    if (query.value.dates.length === 2) {
      params.start_time = new Date(query.value.dates[0]).toISOString();
      params.end_time = new Date(query.value.dates[1]).toISOString();
    }
    
    const res = await api.get('/rules/results/', { params });
    
    // 处理分页响应
    if (res.data && typeof res.data === 'object' && 'results' in res.data) {
      // 分页响应格式
      results.value = Array.isArray(res.data.results) ? res.data.results : [];
      totalCount.value = res.data.count || 0;
    } else {
      // 兼容旧格式（非分页）
      results.value = Array.isArray(res.data) ? res.data : [];
      totalCount.value = results.value.length;
    }
    
    // 若切换了 CMG 或首次加载，联动刷新规则下拉，保证规则ID列表与模型一致
    await loadRules();
    
    // 同时加载统计信息
    await loadStatistics();
  } catch (error) {
    console.error('加载规则检测结果失败:', error);
    results.value = [];
    totalCount.value = 0;
  } finally {
    loading.value = false;
  }
}

function refresh() {
  loadResults();
}

function getFaultLevelType(level) {
  if (level >= 4) return 'danger';
  if (level >= 3) return 'warning';
  if (level >= 2) return 'info';
  return 'success';
}

function getDetailsArray(details) {
  if (!details || typeof details !== 'object') return [];
  return Object.entries(details).map(([key, value]) => ({
    key,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value)
  }));
}

function getDataArray(data) {
  if (!data || typeof data !== 'object') return [];
  return Object.entries(data).map(([parameter, value]) => ({
    parameter,
    value: typeof value === 'number' ? value.toFixed(3) : String(value)
  }));
}

function handleSizeChange(newSize) {
  pageSize.value = newSize;
  currentPage.value = 1;
  loadResults(); // 重新加载数据
}

function handleCurrentChange(newPage) {
  currentPage.value = newPage;
  loadResults(); // 重新加载数据
}

onMounted(async () => {
  await Promise.all([loadCmgs(), loadRules()]);
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
.rule-results-page {
  padding: 12px;
}

.toolbar {
  margin-bottom: 12px;
}

code {
  background: #f5f5f5;
  padding: 2px 4px;
  border-radius: 2px;
  font-family: 'Courier New', monospace;
}

h4 {
  margin: 0 0 8px 0;
  color: #409EFF;
}

p {
  margin: 0 0 16px 0;
}
</style>
