<template>
  <div>
    <el-card>
      <div style="margin-bottom: 10px;">
        <el-button type="primary" @click="openAddDialog">新增型号</el-button>
      </div>
      <el-table :data="modelList" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="model_name" label="型号名称" />
        <el-table-column label="类型">
          <template #default="{ row }">
            {{ typeMap[row.cmg_type] || row.cmg_type }}
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column label="启用">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="toggleActive(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="removeModel(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增型号对话框 -->
    <el-dialog v-model="addDialogVisible" title="新增型号">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="addForm.model_name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="addForm.cmg_type" placeholder="请选择类型">
            <el-option
              v-for="tp in typeList"
              :key="tp.id"
              :label="tp.name"
              :value="tp.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input type="textarea" v-model="addForm.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAdd">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑型号对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑型号">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="editForm.model_name" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="editForm.cmg_type">
            <el-option
              v-for="tp in typeList"
              :key="tp.id"
              :label="tp.name"
              :value="tp.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input type="textarea" v-model="editForm.description" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="editForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api';

// List of CMG models and types
const modelList = ref([]);
const typeList = ref([]);
const typeMap = {};

// Dialog visibility flags
const addDialogVisible = ref(false);
const editDialogVisible = ref(false);

// Forms for add/edit
const addForm = ref({
  model_name: '',
  cmg_type: null,
  description: '',
  is_active: true
});

const editForm = ref({
  id: null,
  model_name: '',
  cmg_type: null,
  description: '',
  is_active: true
});

// Fetch model and type data from the backend
async function loadData() {
  const [modelsRes, typesRes] = await Promise.all([
    api.get('/data/cmg-models/'),
    api.get('/data/cmg-types/')
  ]);
  modelList.value = modelsRes.data;
  typeList.value = typesRes.data;
  typeList.value.forEach(tp => {
    typeMap[tp.id] = tp.name;
  });
}

// Open add dialog
function openAddDialog() {
  addForm.value = { model_name: '', cmg_type: null, description: '', is_active: true };
  addDialogVisible.value = true;
}

// Save new model
async function saveAdd() {
  if (!addForm.value.model_name || !addForm.value.cmg_type) {
    alert('请填写名称并选择类型');
    return;
  }
  await api.post('/data/cmg-models/', addForm.value);
  addDialogVisible.value = false;
  await loadData();
}

// Open edit dialog
function openEditDialog(row) {
  editForm.value = { ...row };
  editDialogVisible.value = true;
}

// Save edited model
async function saveEdit() {
  const id = editForm.value.id;
  const data = { ...editForm.value };
  delete data.id;
  await api.put(`/data/cmg-models/${id}/`, data);
  editDialogVisible.value = false;
  await loadData();
}

// Delete model
async function removeModel(row) {
  if (confirm(`确认删除型号 ${row.model_name}？`)) {
    await api.delete(`/data/cmg-models/${row.id}/`);
    await loadData();
  }
}

// Toggle active flag
async function toggleActive(row) {
  await api.patch(`/data/cmg-models/${row.id}/`, { is_active: row.is_active });
}

onMounted(loadData);
</script>

<style scoped>
/* Optional styling can be placed here to adjust spacing or colors. */
</style>