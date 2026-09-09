<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo">
          <el-icon class="logo-icon"><Compass /></el-icon>
          <h1 class="platform-title">基于模型的寿命预测系统</h1>
        </div>
        <p class="platform-subtitle">Model-Based Life Prediction System</p>
      </div>
      
      <el-form 
        ref="loginFormRef" 
        :model="loginForm" 
        :rules="loginRules" 
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username" label="用户名">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            size="large"
            prefix-icon="User"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password" label="密码">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            prefix-icon="Lock"
            show-password
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p class="help-text">
          首次使用请联系管理员创建账户
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Compass, User, Lock } from '@element-plus/icons-vue';
import api from '../api';

defineOptions({
  name: 'Login'
});

const router = useRouter();
const loginFormRef = ref();
const loading = ref(false);

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: ''
});

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ]
};

// 处理登录
async function handleLogin() {
  if (!loginFormRef.value) return;
  
  try {
    await loginFormRef.value.validate();
    loading.value = true;
    
    console.log('开始登录请求...');
    console.log('用户名:', loginForm.username);
    
    // 使用JSON格式发送登录请求
    const loginData = {
      username: loginForm.username,
      password: loginForm.password
    };
    
    console.log('发送登录请求到:', '/users/login/');
    console.log('请求数据:', loginData);
    
    const response = await api.post('/users/login/', loginData, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('登录响应:', response.data);
    
    if (response.data.detail === '登录成功') {
      ElMessage.success('登录成功');
      
      // 存储用户信息
      localStorage.setItem('user', JSON.stringify({
        username: response.data.username,
        role: response.data.role,
        isLoggedIn: true
      }));
      
      console.log('用户信息已存储:', {
        username: response.data.username,
        role: response.data.role
      });
      
      // 跳转到首页
      router.push('/');
    }
  } catch (error) {
    console.error('登录失败:', error);
    console.error('错误详情:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      headers: error.response?.headers
    });
    
    if (error.response?.status === 401) {
      ElMessage.error('用户名或密码错误');
    } else if (error.response?.status === 400) {
      ElMessage.error(error.response.data.detail || '登录参数错误');
    } else if (error.response?.status === 403) {
      ElMessage.error('登录被拒绝，请检查网络连接或联系管理员');
    } else {
      ElMessage.error('登录失败，请检查网络连接');
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-image: url('/images/pingtaibackground.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  position: relative;
  padding: 20px;
}

.login-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1;
}

.login-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
  padding: 50px;
  width: 100%;
  max-width: 500px;
  position: relative;
  z-index: 2;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  margin-bottom: 20px;
}

.logo-icon {
  font-size: 36px;
  color: var(--cmg-aerospace-primary);
}

.platform-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--cmg-text-primary);
  margin: 0;
  line-height: 1.2;
}

.platform-subtitle {
  font-size: 16px;
  color: var(--cmg-text-tertiary);
  margin: 0;
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.login-form {
  margin-bottom: 30px;
}

.login-form .el-form-item {
  margin-bottom: 24px;
}

.login-form .el-form-item__label {
  font-size: 16px;
  font-weight: 600;
  color: var(--cmg-text-primary);
  margin-bottom: 8px;
  display: block;
}

.login-form .el-input {
  height: 50px;
}

.login-form .el-input__wrapper {
  border-radius: 10px;
  border: 2px solid #e4e7ed;
  transition: all 0.3s ease;
}

.login-form .el-input__wrapper:hover {
  border-color: var(--cmg-aerospace-primary);
}

.login-form .el-input__wrapper.is-focus {
  border-color: var(--cmg-aerospace-primary);
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.login-button {
  width: 100%;
  height: 52px;
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(135deg, var(--cmg-aerospace-primary), var(--cmg-primary-600));
  border: none;
  border-radius: 10px;
  transition: all 0.3s ease;
  color: white;
}

.login-button:hover {
  background: linear-gradient(135deg, var(--cmg-primary-800), var(--cmg-aerospace-primary));
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
}

.login-button:active {
  transform: translateY(0);
}

.login-footer {
  text-align: center;
}

.help-text {
  font-size: 14px;
  color: var(--cmg-text-tertiary);
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-card {
    padding: 40px 30px;
    max-width: 450px;
  }
  
  .platform-title {
    font-size: 22px;
  }
  
  .platform-subtitle {
    font-size: 15px;
  }
  
  .logo-icon {
    font-size: 32px;
  }
}

@media (max-width: 480px) {
  .login-card {
    padding: 30px 20px;
    max-width: 400px;
  }
  
  .platform-title {
    font-size: 20px;
  }
  
  .platform-subtitle {
    font-size: 14px;
  }
  
  .logo-icon {
    font-size: 28px;
  }
  
  .login-form .el-input {
    height: 45px;
  }
  
  .login-button {
    height: 48px;
    font-size: 16px;
  }
}
</style>