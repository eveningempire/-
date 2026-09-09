<template>
  <div class="ims-management">
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>IMS异常检测模型管理</span>
          <div>
            <el-button type="success" @click="showTrainDialog = true">
              <el-icon><DataAnalysis /></el-icon>
              训练模型
            </el-button>
            <el-button type="primary" @click="showUploadDialog = true" style="margin-left: 8px;">
              <el-icon><Upload /></el-icon>
              上传模型
            </el-button>
          </div>
        </div>
      </template>

      <!-- IMS模型列表 -->
      <el-table :data="imsModels" v-loading="loading">
        <el-table-column prop="name" label="模型名称" />
        <el-table-column prop="cmg_model_name" label="CMG型号" />
        <el-table-column prop="parameters" label="监测参数">
          <template #default="scope">
            <div style="display:flex; flex-wrap: wrap; gap:4px;">
              <el-tag v-for="param in scope.row.parameters" :key="param" size="small">
                {{ param }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="threshold" label="异常阈值">
          <template #default="scope">
            {{ scope.row.threshold?.toFixed(3) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
              {{ scope.row.is_active ? '激活' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="scope">
            {{ new Date(scope.row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button 
              :type="scope.row.is_active ? 'warning' : 'success'" 
              size="small"
              @click="toggleModelStatus(scope.row)"
            >
              {{ scope.row.is_active ? '停用' : '激活' }}
            </el-button>
            <el-button type="danger" size="small" @click="deleteModel(scope.row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传模型对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传IMS模型" width="500px">
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="CMG型号" required>
          <el-select v-model="uploadForm.cmg_model_id" placeholder="选择CMG型号">
            <el-option 
              v-for="model in cmgModels" 
              :key="model.id" 
              :label="model.model_name" 
              :value="model.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="uploadForm.name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="模型文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            accept=".json"
            :on-change="handleFileChange"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div style="color: #999; font-size: 12px;">
                只能上传.json格式的模型文件
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="uploadModel" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>

    <!-- 训练模型对话框 -->
    <el-dialog v-model="showTrainDialog" title="训练IMS模型" width="720px" :close-on-click-modal="false">
      <el-form :model="trainForm" label-width="120px">
        <el-form-item label="算法类型">
          <el-radio-group v-model="trainForm.algorithmType">
            <el-radio label="isolation_forest">孤立森林</el-radio>
            <el-radio label="legacy_kmeans">K均值聚类</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="CMG型号" required>
          <el-select v-model="trainForm.cmg_model_id" placeholder="选择CMG型号" @change="loadAvailableParams">
            <el-option 
              v-for="model in cmgModels" 
              :key="model.id" 
              :label="model.model_name" 
              :value="model.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="trainForm.name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item v-if="trainForm.algorithmType==='isolation_forest' && availableParams.length > 0" label="监测参数">
          <el-select 
            v-model="trainForm.parameters" 
            multiple 
            filterable 
            collapse-tags 
            placeholder="选择要监测的参数（留空则自动选择）"
            style="width: 100%"
          >
            <el-option 
              v-for="param in availableParams" 
              :key="param" 
              :label="param" 
              :value="param"
            />
          </el-select>
          <div style="color: #666; font-size: 12px; margin-top: 5px;">
            如果不选择参数，系统将自动选择数值型参数进行训练
          </div>
        </el-form-item>
        <el-form-item v-if="trainForm.algorithmType==='isolation_forest'" label="异常比例">
          <el-input-number v-model="trainForm.contamination" :min="0.01" :max="0.3" :step="0.01" :precision="2" />
          <span style="margin-left: 10px; color: #666;">训练数据中异常样本的预期比例</span>
        </el-form-item>
        <el-form-item v-if="trainForm.algorithmType==='isolation_forest'" label="隔离树数量">
          <el-input-number v-model="trainForm.n_estimators" :min="50" :max="500" :step="10" />
          <span style="margin-left: 10px; color: #666;">更多的树可提高精度但增加计算时间</span>
        </el-form-item>
        <div v-if="trainForm.algorithmType==='isolation_forest' && availableParams.length > 0" style="color: #666; font-size: 12px; margin-bottom: 15px;">
          数据统计：共{{ dataCount }}条记录，{{ availableParams.length }}个可用参数
        </div>

        <!-- Legacy KMeans 配置 -->
        <template v-if="trainForm.algorithmType==='legacy_kmeans'">
          <el-form-item label="训练数据目录">
            <el-input v-model="trainForm.data_dir" placeholder="如：delete/IMS/Health" />
            <div style="color:#666;font-size:12px;margin-top:6px;">默认路径：delete/IMS/Health（可修改为你的训练数据目录）</div>
          </el-form-item>
          <el-form-item label="监测参数（可选）">
            <el-select
              v-model="trainForm.legacy_parameters"
              multiple
              filterable
              collapse-tags
              placeholder="选择要监测的参数（留空则由系统从CSV数值列自动筛选）"
              style="width: 100%"
            >
              <el-option
                v-for="param in availableParams"
                :key="param"
                :label="param"
                :value="param"
              />
            </el-select>
            <div style="color:#666;font-size:12px;margin-top:6px;">若不选择，系统会在CSV中自动筛选数值列用于训练。</div>
          </el-form-item>
          <el-form-item label="参数列（可选）">
            <el-input
              v-model="trainForm.columns"
              type="textarea"
              :rows="2"
              placeholder="逗号分隔列名；留空则自动使用CSV中的数值列"
            />
            <div style="color:#999;font-size:12px;margin-top:4px;">高级用法：也可以直接手动填写列名。若同时选择了上面的"监测参数"，以选择为准。</div>
          </el-form-item>
          <el-form-item label="聚类数（可选）">
            <el-input-number v-model="trainForm.n_clusters" :min="2" :max="128" :step="1" />
            <div class="param-hint">不设置则自动计算最优K值</div>
          </el-form-item>
          <el-form-item label="半径收缩比例">
            <el-input-number v-model="trainForm.shrink_ratio" :min="0.0" :max="0.5" :step="0.01" :precision="2" />
            <div class="param-hint">推荐0.15-0.25，值越大边界越紧，虚警率越低</div>
          </el-form-item>
          <el-form-item label="校准百分位数">
            <el-input-number v-model="trainForm.calib_percentile" :min="50" :max="100" :step="1" :precision="1" />
            <div class="param-hint">推荐99-99.9，值越高越保守，虚警率越低</div>
          </el-form-item>
          <el-form-item label="异常判定阈值">
            <el-input-number v-model="trainForm.threshold" :min="0.3" :max="0.9" :step="0.05" :precision="2" />
            <div class="param-hint">推荐0.6-0.7，值越高越保守，虚警率越低</div>
          </el-form-item>
          <el-form-item label="激活且停用其他">
            <el-switch v-model="trainForm.deactivate_others" />
          </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <el-button @click="showTrainDialog = false">取消</el-button>
        <el-button type="primary" @click="trainModel" :loading="training">开始训练</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Upload, DataAnalysis } from '@element-plus/icons-vue';
import api from '../api';

// 为 keep-alive 添加组件名称
defineOptions({
  name: 'IMSManagement'
});

const loading = ref(false);
const imsModels = ref([]);
const cmgModels = ref([]);
const showUploadDialog = ref(false);
const uploading = ref(false);
const showTrainDialog = ref(false);
const training = ref(false);
const availableParams = ref([]);
const dataCount = ref(0);

const uploadForm = ref({
  cmg_model_id: null,
  name: '',
  file: null
});

const trainForm = ref({
  algorithmType: 'isolation_forest',
  cmg_model_id: null,
  name: '',
  parameters: [],
  contamination: 0.05,
  n_estimators: 150,
  // legacy options - 优化默认参数以降低虚警率
  data_dir: 'delete/IMS/Health',
  columns: '',
  legacy_parameters: [],
  threshold: 0.65,        // 提高阈值：0.5 -> 0.65（更保守）
  n_clusters: null,
  shrink_ratio: 0.20,     // 增加收缩比例：0.05 -> 0.20（边界更紧）
  calib_percentile: 99,   // 提高百分位数：95 -> 99（更严格）
  deactivate_others: true
});

// 加载IMS模型列表
async function loadIMSModels() {
  loading.value = true;
  try {
    const res = await api.get('/health/ims-models/');
    imsModels.value = res.data || [];
  } catch (error) {
    ElMessage.error('加载IMS模型失败: ' + error.message);
  } finally {
    loading.value = false;
  }
}

// 加载CMG型号列表
async function loadCMGModels() {
  try {
    const res = await api.get('/data/cmg-models/');
    cmgModels.value = res.data || [];
  } catch (error) {
    ElMessage.error('加载CMG型号失败: ' + error.message);
  }
}

// 文件选择处理
function handleFileChange(file) {
  uploadForm.value.file = file.raw;
}

// 上传模型
async function uploadModel() {
  if (!uploadForm.value.cmg_model_id || !uploadForm.value.name || !uploadForm.value.file) {
    ElMessage.warning('请填写所有必填项');
    return;
  }

  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append('cmg_model_id', uploadForm.value.cmg_model_id);
    formData.append('name', uploadForm.value.name);
    formData.append('model_file', uploadForm.value.file);

    await api.post('/health/ims-models/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    ElMessage.success('模型上传成功');
    showUploadDialog.value = false;
    uploadForm.value = {
      cmg_model_id: null,
      name: '',
      file: null
    };
    await loadIMSModels();
  } catch (error) {
    ElMessage.error('模型上传失败: ' + error.message);
  } finally {
    uploading.value = false;
  }
}

// 切换模型状态
async function toggleModelStatus(model) {
  try {
    const action = model.is_active ? 'deactivate' : 'activate';
    const actionText = model.is_active ? '停用' : '激活';
    
    await ElMessageBox.confirm(
      `确定要${actionText}模型 "${model.name}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await api.post(`/health/ims-models/${model.id}/${action}/`);
    ElMessage.success(`模型${actionText}成功`);
    await loadIMSModels();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败: ' + error.message);
    }
  }
}

// 删除模型
async function deleteModel(model) {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${model.name}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    await api.delete(`/health/ims-models/${model.id}/`);
    ElMessage.success('模型删除成功');
    await loadIMSModels();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message);
    }
  }
}

// 获取可用参数
async function loadAvailableParams() {
  if (!trainForm.value.cmg_model_id) return;
  
  try {
    const res = await api.get('/health/ims-models/available-params/', {
      params: { cmg_model_id: trainForm.value.cmg_model_id }
    });
    availableParams.value = res.data.parameters || [];
    dataCount.value = res.data.data_count || 0;
  } catch (error) {
    ElMessage.error('获取可用参数失败: ' + error.message);
  }
}

// 训练模型
async function trainModel() {
  if (!trainForm.value.cmg_model_id || !trainForm.value.name) {
    ElMessage.warning('请填写所有必填项');
    return;
  }

  training.value = true;
  try {
    const url = trainForm.value.algorithmType === 'legacy_kmeans' ? '/health/ims-models/train-legacy/' : '/health/ims-models/train/';
    // 组装 payload：legacy_kmeans 若选择了“监测参数”，优先用其生成 columns
    const payload = { ...trainForm.value };
    if (payload.algorithmType === 'legacy_kmeans') {
      if (Array.isArray(payload.legacy_parameters) && payload.legacy_parameters.length > 0) {
        payload.columns = payload.legacy_parameters.join(',');
      }
    }
    const res = await api.post(url, payload, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    ElMessage.success('模型训练成功');
    showTrainDialog.value = false;
    
    // 重置表单（使用优化后的默认参数）
    trainForm.value = {
      algorithmType: 'isolation_forest',
      cmg_model_id: null,
      name: '',
      parameters: [],
      contamination: 0.05,
      n_estimators: 150,
      data_dir: 'delete/IMS/Health',
      columns: '',
      legacy_parameters: [],
      threshold: 0.65,        // 优化后的默认阈值
      n_clusters: null,
      shrink_ratio: 0.20,     // 优化后的默认收缩比例
      calib_percentile: 99,   // 优化后的默认百分位数
      deactivate_others: true
    };
    availableParams.value = [];
    dataCount.value = 0;
    
    await loadIMSModels();
    
    // 显示训练摘要
    if (res.data.training_summary) {
      const summary = res.data.training_summary;
      const parts = [];
      if (summary.training_samples) parts.push(`样本${summary.training_samples}`);
      parts.push(`参数${summary.parameters.length}`);
      if (summary.n_clusters) parts.push(`聚类数${summary.n_clusters}`);
      if (summary.shrink_ratio !== undefined) parts.push(`收缩${summary.shrink_ratio}`);
      if (summary.calib_percentile !== undefined) parts.push(`P${summary.calib_percentile}`);
      ElMessage({ message: `训练完成！${parts.join('，')}，阈值${Number(summary.threshold).toFixed(3)}`, type: 'success', duration: 5000 });
    }
  } catch (error) {
    ElMessage.error('模型训练失败: ' + (error.response?.data?.error || error.message));
  } finally {
    training.value = false;
  }
}

onMounted(async () => {
  await Promise.all([
    loadIMSModels(),
    loadCMGModels()
  ]);
});
</script>

<style scoped>
.ims-management {
  padding: 20px;
}

.param-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}
</style>
