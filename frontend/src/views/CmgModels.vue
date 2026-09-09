<template>
  <div>
    <el-card>
      <el-tabs v-model="activeTab">
        
        <el-tab-pane label="型号管理" name="models">
          <div class="toolbar">
            <el-button type="primary" @click="openModelDialog()">新增型号</el-button>
          </div>
          <el-table :data="cmgModels" style="width: 100%" size="small">
            <el-table-column type="index" label="#" width="60" />
            <el-table-column prop="model_name" label="型号名称" width="200" />
            
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="is_active" label="启用" width="80">
              <template #default="{ row }"><el-switch v-model="row.is_active" @change="saveModel(row)" /></template>
            </el-table-column>
            <el-table-column label="操作" width="220">
              <template #default="{ row }">
                <el-button size="small" @click="openModelDialog(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteModel(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="个体管理" name="cmgs">
          <div class="toolbar">
            <el-button type="primary" @click="openCmgDialog()">新增个体</el-button>
          </div>
          <el-table :data="cmgs" style="width: 100%" size="small">
            <el-table-column type="index" label="#" width="60" />
            
            <el-table-column label="型号" width="200">
              <template #default="{ row }">{{ modelName(row.cmg_model_detail?.id || row.cmg_model) }}</template>
            </el-table-column>
            <el-table-column prop="cmg_id" label="标识" width="200" />
            <el-table-column prop="name" label="名称" width="200" />
            <el-table-column prop="enabled" label="启用" width="100">
              <template #default="{ row }"><el-switch v-model="row.enabled" @change="saveCmg(row)" /></template>
            </el-table-column>
            <el-table-column label="操作" width="220">
              <template #default="{ row }">
                <el-button size="small" @click="openCmgDialog(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteCmg(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    

    <!-- 型号对话框 -->
    <el-dialog v-model="modelDialog.visible" :title="modelDialog.form.id ? '编辑型号' : '新增型号'" width="600px">
      <el-form :model="modelDialog.form" label-width="100px">
        <el-form-item label="型号名称" required>
          <el-input v-model="modelDialog.form.model_name" placeholder="例如：500NM、1000NM" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="modelDialog.form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="modelDialog.form.is_active" />
        </el-form-item>
        <el-form-item label="默认">
          <el-switch v-model="modelDialog.form.is_default" />
        </el-form-item>
        <el-form-item label="自定义">
          <el-switch v-model="modelDialog.form.is_custom" />
        </el-form-item>
        <el-form-item label="系统">
          <el-switch v-model="modelDialog.form.is_system" />
        </el-form-item>
        <el-form-item label="弃用">
          <el-switch v-model="modelDialog.form.is_deprecated" />
        </el-form-item>
        <el-form-item label="隐藏">
          <el-switch v-model="modelDialog.form.is_hidden" />
        </el-form-item>
        <el-form-item label="公开">
          <el-switch v-model="modelDialog.form.is_public" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modelDialog.visible=false">取消</el-button>
        <el-button type="primary" @click="saveModel(modelDialog.form)">保存</el-button>
      </template>
    </el-dialog>

    <!-- 个体对话框 -->
    <el-dialog v-model="cmgDialog.visible" :title="cmgDialog.form.id ? '编辑个体' : '新增个体'" width="600px">
      <el-form :model="cmgDialog.form" label-width="100px">
        
        <el-form-item label="所属型号" required>
          <el-select v-model="cmgDialog.form.cmg_model" placeholder="选择型号" style="width: 100%">
            <el-option v-for="m in cmgModels" :key="m.id" :label="m.model_name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="个体标识">
          <el-input v-model="cmgDialog.form.cmg_id" placeholder="例如 CMG-001" />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="cmgDialog.form.name" placeholder="显示名称" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="cmgDialog.form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cmgDialog.visible=false">取消</el-button>
        <el-button type="primary" @click="saveCmg(cmgDialog.form)">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api';

// 为 keep-alive 添加组件名称
defineOptions({
  name: 'CmgModels'
});

const activeTab = ref('models');
const cmgModels = ref([]);
// satellites removed
const cmgs = ref([]);

//
const modelDialog = ref({ visible: false, form: { id: null, model_name: '', cmg_type: null, description: '', is_active: true, is_default: false, is_custom: false, is_system: false, is_deprecated: false, is_hidden: false, is_public: true } });
const cmgDialog = ref({ visible: false, form: { id: null, satellite: null, cmg_model: null, cmg_id: '', name: '', enabled: true } });

// removed typeName

function modelName(id) {
  const m = cmgModels.value.find(x => x.id === id);
  return m ? m.model_name : id;
}

//

// removed loadTypes

async function loadModels() {
  const res = await api.get('/data/cmg-models/');
  cmgModels.value = Array.isArray(res.data) ? res.data : [];
}

//

async function loadCmgs() {
  const res = await api.get('/data/cmgs/');
  cmgs.value = Array.isArray(res.data) ? res.data : [];
}

//

// removed saveType

// removed deleteType

function openModelDialog(row) {
  modelDialog.value.form = row ? { ...row } : { id: null, model_name: '', cmg_type: null, description: '', is_active: true, is_default: false, is_custom: false, is_system: false, is_deprecated: false, is_hidden: false, is_public: true };
  modelDialog.value.visible = true;
}

async function saveModel(row) {
  const data = row?.id ? row : modelDialog.value.form;
  
  // 验证必填字段
  if (!data.model_name || data.model_name.trim() === '') {
    ElMessage.error('请输入型号名称');
    return;
  }
  
  try {
    if (data.id) {
      await api.put(`/data/cmg-models/${data.id}/`, data);
    } else {
      await api.post('/data/cmg-models/', data);
    }
    ElMessage.success('保存成功');
    modelDialog.value.visible = false;
    await loadModels();
  } catch (e) {
    console.error('保存失败:', e);
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message || '未知错误'));
  }
}

async function deleteModel(row) {
  await ElMessageBox.confirm(`确认删除型号「${row.model_name}」?`, '提示', { type: 'warning' });
  try {
    await api.delete(`/data/cmg-models/${row.id}/`);
    ElMessage.success('删除成功');
    await loadModels();
  } catch (e) {
    ElMessage.error('删除失败');
  }
}

function openCmgDialog(row) {
  if (row) {
    // 编辑模式
    cmgDialog.value.form = { ...row };
  } else {
    // 新建模式 - 如果有可用的型号，选择第一个作为默认值
    const defaultModelId = cmgModels.value.length > 0 ? cmgModels.value[0].id : null;
    cmgDialog.value.form = { 
      id: null, 
      satellite: null, 
      cmg_model: defaultModelId, 
      cmg_id: '', 
      name: '', 
      enabled: true 
    };
  }
  cmgDialog.value.visible = true;
}

async function saveCmg(row) {
  const data = row?.id ? row : cmgDialog.value.form;
  
  // 验证必填字段
  if (!data.cmg_model) {
    ElMessage.error('请选择所属型号');
    return;
  }
  if (!data.cmg_id || data.cmg_id.trim() === '') {
    ElMessage.error('请输入个体标识');
    return;
  }
  if (!data.name || data.name.trim() === '') {
    ElMessage.error('请输入名称');
    return;
  }
  
  try {
    if (data.id) {
      await api.put(`/data/cmgs/${data.id}/`, data);
    } else {
      await api.post('/data/cmgs/', data);
    }
    ElMessage.success('保存成功');
    cmgDialog.value.visible = false;
    await loadCmgs();
  } catch (e) {
    console.error('保存失败:', e);
    ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message || '未知错误'));
  }
}

async function deleteCmg(row) {
  await ElMessageBox.confirm(`确认删除个体「${row.name}」?`, '提示', { type: 'warning' });
  try {
    await api.delete(`/data/cmgs/${row.id}/`);
    ElMessage.success('删除成功');
    await loadCmgs();
  } catch (e) {
    ElMessage.error('删除失败');
  }
}

onMounted(async () => {
  await Promise.all([loadModels(), loadCmgs()]);
});
</script>

<style scoped>
.toolbar { margin-bottom: 10px; }
</style>
