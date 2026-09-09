<template>
  <div class="user-management">
    <div class="page-header">
      <h1>用户管理</h1>
      <p class="page-description">
        管理系统用户账户，创建、编辑和删除用户
      </p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button 
        type="primary" 
        @click="showCreateDialog = true"
        v-if="hasPermission('create_user')"
      >
        <el-icon><Plus /></el-icon>
        创建用户
      </el-button>
      <el-button @click="refreshUsers" :loading="loading">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <el-button @click="refreshUserInfo" type="info">
        <el-icon><Refresh /></el-icon>
        刷新用户信息
      </el-button>
    </div>

    <!-- 用户列表 -->
    <el-card class="user-list-card">
      <el-table 
        :data="users" 
        v-loading="loading"
        style="width: 100%"
        :empty-text="loading ? '加载中...' : '暂无用户数据'"
      >
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="first_name" label="姓名" width="120" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date_joined" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.date_joined) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login ? formatDateTime(row.last_login) : '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              size="small" 
              @click="editUser(row)"
              v-if="hasPermission('edit_user')"
            >
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteUser(row)"
              v-if="hasPermission('delete_user')"
              :disabled="row.role === 'admin'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingUser ? '编辑用户' : '创建用户'"
      width="500px"
      @close="resetForm"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="userForm.username" 
            placeholder="请输入用户名"
            :disabled="editingUser"
          />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input 
            v-model="userForm.email" 
            placeholder="请输入邮箱"
          />
        </el-form-item>
        
        <el-form-item label="姓名" prop="first_name">
          <el-input 
            v-model="userForm.first_name" 
            placeholder="请输入姓名"
          />
        </el-form-item>
        
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!editingUser">
          <el-input 
            v-model="userForm.password" 
            type="password" 
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirm_password" v-if="!editingUser">
          <el-input 
            v-model="userForm.confirm_password" 
            type="password" 
            placeholder="请确认密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="userForm.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser" :loading="saving">
          {{ saving ? '保存中...' : '保存' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Refresh } from '@element-plus/icons-vue';
import api from '../api';

defineOptions({
  name: 'UserManagement'
});

// 响应式数据
const users = ref([]);
const loading = ref(false);
const saving = ref(false);
const showCreateDialog = ref(false);
const editingUser = ref(null);
const userFormRef = ref();

// 当前用户信息
const currentUser = ref(null);

// 用户表单
const userForm = reactive({
  username: '',
  email: '',
  first_name: '',
  role: 'user',
  password: '',
  confirm_password: '',
  is_active: true
});

// 表单验证规则
const userRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  first_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== userForm.password) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
};

// 获取角色标签类型
function getRoleTagType(role) {
  const types = {
    admin: 'danger',
    user: 'info'
  };
  return types[role] || 'info';
}

// 获取角色标签文本
function getRoleLabel(role) {
  const labels = {
    admin: '管理员',
    user: '普通用户'
  };
  return labels[role] || role;
}

// 格式化日期时间
function formatDateTime(dateTime) {
  if (!dateTime) return '';
  
  try {
    // 创建Date对象，JavaScript会自动处理UTC到本地时间的转换
    const date = new Date(dateTime);
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.warn('无效的日期时间:', dateTime);
      return '无效时间';
    }
    
    // 使用中文本地化格式
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  } catch (error) {
    console.error('格式化日期时间失败:', error, dateTime);
    return '时间格式错误';
  }
}

// 加载用户列表
async function loadUsers() {
  loading.value = true;
  try {
    const response = await api.get('/users/users/');
    users.value = response.data;
  } catch (error) {
    console.error('加载用户列表失败:', error);
    ElMessage.error('加载用户列表失败');
  } finally {
    loading.value = false;
  }
}

// 刷新用户列表
function refreshUsers() {
  loadUsers();
}

// 编辑用户
function editUser(user) {
  editingUser.value = user;
  Object.assign(userForm, {
    username: user.username,
    email: user.email,
    first_name: user.first_name,
    role: user.role,
    is_active: user.is_active
  });
  showCreateDialog.value = true;
}

// 删除用户
async function deleteUser(user) {
  console.log('开始删除用户操作');
  console.log('当前用户信息:', currentUser.value);
  console.log('要删除的用户:', user);
  
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    console.log('用户确认删除，开始发送删除请求');
    console.log('删除URL:', `/users/users/${user.id}/`);
    
    const response = await api.delete(`/users/users/${user.id}/`);
    console.log('删除请求成功:', response);
    
    ElMessage.success('用户删除成功');
    loadUsers();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error);
      console.error('错误详情:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        headers: error.response?.headers
      });
      
      if (error.response?.status === 403) {
        ElMessage.error(`删除用户失败: 权限被拒绝 (403)。请检查您是否有管理员权限。`);
      } else {
        ElMessage.error('删除用户失败');
      }
    }
  }
}

// 保存用户
async function saveUser() {
  if (!userFormRef.value) return;
  
  try {
    await userFormRef.value.validate();
    saving.value = true;
    
    if (editingUser.value) {
      // 编辑用户
      await api.put(`/users/users/${editingUser.value.id}/`, {
        email: userForm.email,
        first_name: userForm.first_name,
        role: userForm.role,
        is_active: userForm.is_active
      });
      ElMessage.success('用户更新成功');
    } else {
      // 创建用户
      await api.post('/users/register/', userForm);
      ElMessage.success('用户创建成功');
    }
    
    showCreateDialog.value = false;
    loadUsers();
  } catch (error) {
    console.error('保存用户失败:', error);
    
    if (error.response?.status === 400) {
      const errors = error.response.data;
      if (typeof errors === 'object') {
        const errorMessages = Object.values(errors).flat();
        ElMessage.error(errorMessages.join(', '));
      } else {
        ElMessage.error(errors.detail || '保存失败');
      }
    } else {
      ElMessage.error('保存用户失败');
    }
  } finally {
    saving.value = false;
  }
}

// 重置表单
function resetForm() {
  editingUser.value = null;
  Object.assign(userForm, {
    username: '',
    email: '',
    first_name: '',
    role: 'user',
    password: '',
    confirm_password: '',
    is_active: true
  });
  if (userFormRef.value) {
    userFormRef.value.resetFields();
  }
}

// 加载当前用户信息
async function loadCurrentUser() {
  console.log('开始加载当前用户信息');
  try {
    // 尝试从API获取最新的用户信息
    const response = await api.get('/users/users/me/');
    currentUser.value = response.data;
    console.log('从API获取的用户信息:', response.data);
    console.log('用户角色:', response.data.role);
    
    // 同时更新localStorage
    localStorage.setItem('user', JSON.stringify(response.data));
    console.log('用户信息已更新到localStorage');
  } catch (error) {
    console.error('从API获取用户信息失败，使用localStorage:', error);
    // 如果API失败，使用localStorage中的信息
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    currentUser.value = user;
    console.log('localStorage中的用户信息:', user);
    console.log('localStorage中的用户角色:', user.role);
  }
}

// 刷新用户信息
async function refreshUserInfo() {
  try {
    const response = await api.get('/users/users/me/');
    currentUser.value = response.data;
    
    // 同时更新localStorage
    localStorage.setItem('user', JSON.stringify(response.data));
    
    ElMessage.success('用户信息刷新成功');
    console.log('刷新后的用户信息:', response.data);
  } catch (error) {
    console.error('刷新用户信息失败:', error);
    ElMessage.error('刷新用户信息失败');
  }
}

// 检查权限
function hasPermission(action) {
  if (!currentUser.value) {
    console.log('权限检查失败: 没有当前用户信息');
    return false;
  }
  
  const userRole = currentUser.value.role;
  console.log(`权限检查 - 操作: ${action}, 用户角色: ${userRole}, 用户信息:`, currentUser.value);
  
  switch (action) {
    case 'create_user':
    case 'edit_user':
    case 'delete_user':
      const hasAdminPermission = userRole === 'admin';
      console.log(`管理员权限检查: ${hasAdminPermission}`);
      return hasAdminPermission;
    case 'view_users':
      return ['admin', 'user'].includes(userRole);
    default:
      return false;
  }
}

// 组件挂载时加载数据
onMounted(async () => {
  await loadCurrentUser();
  loadUsers();
});
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--cmg-text-primary);
}

.page-description {
  margin: 0;
  color: var(--cmg-text-tertiary);
  font-size: 14px;
}

.action-bar {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
}

.user-list-card {
  margin-bottom: 20px;
}

.user-list-card :deep(.el-table) {
  border-radius: 8px;
}

.user-list-card :deep(.el-table th) {
  background-color: var(--cmg-bg-tertiary);
  color: var(--cmg-text-primary);
  font-weight: 600;
}

.user-list-card :deep(.el-table td) {
  padding: 12px 0;
}

.user-list-card :deep(.el-table--border) {
  border: 1px solid var(--cmg-border-light);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-management {
    padding: 16px;
  }
  
  .action-bar {
    flex-direction: column;
  }
  
  .action-bar .el-button {
    width: 100%;
  }
}
</style>
