<template>
  <div>
    <el-card>
      <div class="toolbar">
        <el-button type="primary" @click="openDialog()">新增卫星</el-button>
      </div>
      <el-table :data="satellites" style="width: 100%" size="small">
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="name" label="名称" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="openDialog(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialog.visible" :title="dialog.form.id ? '编辑卫星' : '新增卫星'" width="480px">
      <el-form :model="dialog.form" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="dialog.form.name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible=false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import api from '../api';

const satellites = ref([]);
const dialog = ref({ visible: false, form: { id: null, name: '' } });

function openDialog(row) {
  dialog.value.form = row ? { ...row } : { id: null, name: '' };
  dialog.value.visible = true;
}

async function load() {
  const res = await api.get('/data/satellites/');
  satellites.value = Array.isArray(res.data) ? res.data : [];
}

async function save() {
  const f = dialog.value.form;
  try {
    if (!f.name) {
      ElMessage.warning('请输入名称');
      return;
    }
    if (f.id) {
      await api.put(`/data/satellites/${f.id}/`, f);
    } else {
      await api.post('/data/satellites/', f);
    }
    ElMessage.success('保存成功');
    dialog.value.visible = false;
    await load();
  } catch (e) {
    ElMessage.error('保存失败');
  }
}

async function remove(row) {
  await ElMessageBox.confirm(`确认删除卫星「${row.name}」?`, '提示', { type: 'warning' });
  try {
    await api.delete(`/data/satellites/${row.id}/`);
    ElMessage.success('删除成功');
    await load();
  } catch (e) {
    ElMessage.error('删除失败');
  }
}

onMounted(load);
</script>

<style scoped>
.toolbar { margin-bottom: 10px; }
</style>
