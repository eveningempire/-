<template>
  <el-container class="cmg-layout">
    <!-- Sidebar -->
    <el-aside :width="sidebarCollapsed ? '64px' : '280px'" class="cmg-sidebar">
      <div class="cmg-sidebar__header">
        <div class="cmg-logo" :class="{ 'is-collapsed': sidebarCollapsed }">
          <el-icon class="cmg-logo__icon"><Compass /></el-icon>
          <span v-show="!sidebarCollapsed" class="cmg-logo__text">CMG</span>
        </div>
        <el-button 
          text 
          class="cmg-sidebar__collapse-btn"
          @click="toggleSidebar"
        >
          <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
        </el-button>
      </div>
      
      <el-menu
        :default-active="activePath"
        :collapse="sidebarCollapsed"
        class="cmg-sidebar__menu"
        @select="handleSelect"
        router
      >
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <template #title>总览</template>
        </el-menu-item>
        
        <el-sub-menu index="health-assessment">
          <template #title>
            <el-icon><DataAnalysis /></el-icon>
            <span>健康评估</span>
          </template>
          <el-menu-item index="/detection-overview">
            <el-icon><TrendCharts /></el-icon>
            <template #title>检测结果总览</template>
          </el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="lifetime">
          <template #title>
            <el-icon><Timer /></el-icon>
            <span>寿命预测</span>
          </template>
          <el-menu-item index="/lifetime-prediction">
            <el-icon><TrendCharts /></el-icon>
            <template #title>CMG寿命预测系统</template>
          </el-menu-item>
          <el-menu-item index="/model-finetune">
            <el-icon><Refresh /></el-icon>
            <template #title>CMG自扩展动态更新</template>
          </el-menu-item>
          <el-menu-item index="/modeling-overview">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>CMG寿命预测建模</template>
          </el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="data">
          <template #title>
            <el-icon><FolderOpened /></el-icon>
            <span>数据管理</span>
          </template>
          <el-menu-item index="/data-import">
            <el-icon><Upload /></el-icon>
            <template #title>数据文件导入</template>
          </el-menu-item>
          <el-menu-item index="/data-records">
            <el-icon><Search /></el-icon>
            <template #title>数据查询分析</template>
          </el-menu-item>
          <el-menu-item index="/model-management">
            <el-icon><Setting /></el-icon>
            <template #title>型号/个体管理</template>
          </el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="detection-config">
          <template #title>
            <el-icon><Tools /></el-icon>
            <span>检测配置</span>
          </template>
          <el-menu-item index="/ims-management">
            <el-icon><Warning /></el-icon>
            <template #title>CMG异常检测模型配置</template>
          </el-menu-item>
          <el-menu-item index="/rule-editor">
            <el-icon><List /></el-icon>
            <template #title>CMG专家规则配置</template>
          </el-menu-item>
          <el-menu-item index="/msfg-editor">
            <el-icon><Share /></el-icon>
            <template #title>CMG故障信号流图建模</template>
          </el-menu-item>
          <el-menu-item index="/msfg-testpoint-rules">
            <el-icon><EditPen /></el-icon>
            <template #title>CMG流图测点规则配置</template>
          </el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="detection-results">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>检测结果</span>
          </template>
          <el-menu-item index="/ims-results">
            <el-icon><Warning /></el-icon>
            <template #title>异常检测结果</template>
          </el-menu-item>
          <el-menu-item index="/rule-results">
            <el-icon><List /></el-icon>
            <template #title>专家规则检测结果</template>
          </el-menu-item>
          <el-menu-item index="/msfg-results">
            <el-icon><Share /></el-icon>
            <template #title>信号流图推理结果</template>
          </el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="realtime-assessment">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>实时评估</span>
          </template>
          <el-menu-item index="/cmg-detail">
            <el-icon><TrendCharts /></el-icon>
            <template #title>实时评估展示</template>
          </el-menu-item>
          <el-menu-item index="/network-settings">
            <el-icon><Connection /></el-icon>
            <template #title>网络传输设置</template>
          </el-menu-item>
        </el-sub-menu>
        
        <!-- 3D模型测试页面已隐藏，但路由保留 -->
        <!-- 
        <el-menu-item index="/model-3d-test">
          <el-icon><View /></el-icon>
          <template #title>3D模型测试</template>
        </el-menu-item>
        -->
        
        <el-sub-menu index="fund-presentation">
          <template #title>
            <el-icon><Promotion /></el-icon>
            <span>预研内容</span>
          </template>
          <el-menu-item index="/degradation-simulation">
            <el-icon><TrendCharts /></el-icon>
            <template #title>CMG健康演化模型</template>
          </el-menu-item>
          <el-menu-item index="/health-assessment">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>CMG特征提取与智能评估</template>
          </el-menu-item>
          <el-menu-item index="/smart-sensing">
            <el-icon><TrendCharts /></el-icon>
            <template #title>CMG智能感知方法</template>
          </el-menu-item>
          <el-menu-item index="/undersampling">
            <el-icon><DataLine /></el-icon>
            <template #title>CMG欠采样与有限传感</template>
          </el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="users">
          <template #title>
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </template>
          <el-menu-item index="/user-management">
            <el-icon><UserFilled /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="system">
          <template #title>
            <el-icon><Management /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/system-status">
            <el-icon><CircleCheck /></el-icon>
            <template #title>系统状态</template>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <!-- Main Content -->
    <el-container class="cmg-main-container">
      <el-header class="cmg-header">
        <div class="cmg-header__left">
          <h1 class="cmg-header__title">基于模型的寿命预测系统</h1>
          <div class="cmg-header__subtitle">Model-Based Life Prediction System</div>
        </div>
        <div class="cmg-header__right">
          <div class="cmg-header__actions">
            <ThemeToggle />
            <el-divider direction="vertical" />
            <el-dropdown @command="handleUserCommand" class="user-dropdown">
              <el-button text>
                <el-icon><User /></el-icon>
                {{ currentUser?.username || '用户' }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu class="user-dropdown-menu">
                  <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>
      
      <el-main class="cmg-main">
        <router-view v-slot="{ Component, route }">
          <keep-alive :include="['DetectionOverview', 'Dashboard', 'DataRecords', 'CmgDetail', 'DataImport', 'CmgModels', 'TcpIngest', 'IMSManagement', 'IMSResults', 'RuleEditor', 'RuleResults', 'MSFGEditor', 'MSFGResults', 'MSFGComponentMappings', 'SystemStatus', 'LifetimePrediction', 'ModelFinetune', 'Model3DTest', 'OrbitTwinDashboard', 'ModelingOverview', 'SmartSensing', 'Undersampling']">
            <component :is="Component" :key="route.fullPath" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router';
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { 
  Compass, Fold, Expand, Monitor, FolderOpened, Upload, Search, Setting,
  TrendCharts, Connection, Warning, Tools, Document, List, EditPen, 
  Share, User, UserFilled, Management, CircleCheck, Bell, QuestionFilled, Timer, ArrowDown, DataAnalysis, View, Refresh, Promotion, DataLine
} from '@element-plus/icons-vue';
import api from '../api';

const router = useRouter();
const route = useRoute();

// 侧边栏折叠状态
const sidebarCollapsed = ref(false);

// 当前用户信息
const currentUser = ref(null);

// Compute the active menu path based on the current route. This ensures
// that the correct menu item is highlighted when navigating directly via
// the browser address bar.
const activePath = computed(() => route.path);

function handleSelect(index) {
  router.push(index);
}

// 切换侧边栏折叠状态
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value;
  localStorage.setItem('cmg-sidebar-collapsed', sidebarCollapsed.value);
}

// 初始化侧边栏状态
function initSidebarState() {
  const saved = localStorage.getItem('cmg-sidebar-collapsed');
  if (saved !== null) {
    sidebarCollapsed.value = saved === 'true';
  }
}

// 初始化
initSidebarState();

// 加载当前用户信息
function loadCurrentUser() {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  currentUser.value = user;
}

// 处理用户命令
async function handleUserCommand(command) {
  if (command === 'logout') {
    try {
      await api.post('/users/logout/', {}, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      localStorage.removeItem('user');
      currentUser.value = null;
      router.push('/login');
    } catch (error) {
      console.error('登出失败:', error);
      // 即使API调用失败，也清除本地存储并跳转
      localStorage.removeItem('user');
      currentUser.value = null;
      router.push('/login');
    }
  }
}

// 初始化时加载用户信息
loadCurrentUser();
</script>

<style scoped>
/* 布局容器 */
.cmg-layout {
  height: 100vh;
  background: var(--cmg-bg-secondary);
}

/* 侧边栏 */
.cmg-sidebar {
  background: linear-gradient(180deg, var(--cmg-aerospace-primary), var(--cmg-primary-800));
  color: var(--cmg-text-inverse);
  transition: width var(--cmg-duration-base);
  box-shadow: var(--cmg-shadow-lg);
  border-right: 1px solid var(--cmg-border-base);
}

.cmg-sidebar__header {
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--cmg-space-4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.cmg-logo {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-3);
  transition: var(--cmg-transition-all);
}

.cmg-logo.is-collapsed {
  justify-content: center;
}

.cmg-logo__icon {
  font-size: 32px;
  color: var(--cmg-text-inverse);
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.cmg-logo__text {
  font-size: var(--cmg-text-2xl);
  font-weight: 700;
  color: var(--cmg-text-inverse);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  letter-spacing: 2px;
}

.cmg-sidebar__collapse-btn {
  color: var(--cmg-text-inverse);
  padding: var(--cmg-space-2);
  border-radius: var(--cmg-radius-base);
  transition: var(--cmg-transition-colors);
}

.cmg-sidebar__collapse-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.cmg-sidebar__menu {
  border: none;
  background: transparent;
  flex: 1;
  overflow-y: auto;
}

/* 菜单项样式覆盖 */
.cmg-sidebar__menu :deep(.el-menu-item),
.cmg-sidebar__menu :deep(.el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.85);
  border-radius: 0 var(--cmg-radius-lg) var(--cmg-radius-lg) 0;
  margin: var(--cmg-space-1) var(--cmg-space-2) var(--cmg-space-1) 0;
  transition: var(--cmg-transition-all);
}

.cmg-sidebar__menu :deep(.el-menu-item:hover),
.cmg-sidebar__menu :deep(.el-sub-menu__title:hover) {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--cmg-text-inverse);
}

.cmg-sidebar__menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  color: var(--cmg-text-inverse);
  font-weight: 600;
  box-shadow: var(--cmg-shadow-sm);
}

.cmg-sidebar__menu :deep(.el-sub-menu .el-menu-item) {
  background-color: rgba(255, 255, 255, 0.85); /* 浅蓝背景 + 深色字更清晰 */
  color: #243b53;
  margin: var(--cmg-space-1);
  border-radius: var(--cmg-radius-base);
}

.cmg-sidebar__menu :deep(.el-sub-menu .el-menu-item:hover) {
  background-color: #e6f4ff;
  color: #1d3a5f;
}

.cmg-sidebar__menu :deep(.el-sub-menu .el-menu-item.is-active) {
  background: linear-gradient(90deg, #d6ecff, #bfe3ff);
  color: #0f2d4d;
  font-weight: 600;
}

/* 主容器 */
.cmg-main-container {
  background: var(--cmg-bg-secondary);
}

/* 头部 */
.cmg-header {
  background: var(--cmg-bg-primary);
  border-bottom: 1px solid var(--cmg-border-light);
  box-shadow: var(--cmg-shadow-sm);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--cmg-space-6);
  height: 80px;
}

.cmg-header__left {
  flex: 1;
}

.cmg-header__title {
  margin: 0;
  font-size: var(--cmg-text-2xl);
  font-weight: 700;
  color: var(--cmg-aerospace-primary);
  line-height: 1.2;
  background: linear-gradient(135deg, var(--cmg-aerospace-primary), var(--cmg-aerospace-accent));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.cmg-header__subtitle {
  font-size: var(--cmg-text-sm);
  color: var(--cmg-text-tertiary);
  font-weight: 400;
  margin-top: var(--cmg-space-1);
  font-style: italic;
}

.cmg-header__right {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-4);
}

.cmg-header__actions {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-3);
}

.cmg-header__actions .el-button {
  color: var(--cmg-text-secondary);
  padding: var(--cmg-space-2);
  border-radius: var(--cmg-radius-base);
  transition: var(--cmg-transition-colors);
}

.cmg-header__actions .el-button:hover {
  background-color: var(--cmg-gray-100);
  color: var(--cmg-text-primary);
}

[data-theme="dark"] .cmg-header__actions .el-button:hover {
  background-color: var(--cmg-gray-800);
}

/* 主内容区域 */
.cmg-main {
  background: var(--cmg-bg-secondary);
  padding: var(--cmg-space-6);
  overflow: auto;
  height: calc(100vh - 80px);
}

/* 暗色主题适配 */
[data-theme="dark"] .cmg-sidebar {
  background: linear-gradient(180deg, var(--cmg-gray-900), var(--cmg-gray-800));
  border-right-color: var(--cmg-border-base);
}

[data-theme="dark"] .cmg-header {
  background: var(--cmg-bg-primary);
  border-bottom-color: var(--cmg-border-base);
}

[data-theme="dark"] .cmg-header__title {
  background: linear-gradient(135deg, var(--cmg-aerospace-primary), var(--cmg-aerospace-accent));
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .cmg-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: var(--cmg-z-fixed);
    height: 100vh;
  }
  
  .cmg-main-container {
    margin-left: 0;
  }
  
  .cmg-header {
    padding: 0 var(--cmg-space-4);
  }
  
  .cmg-header__title {
    font-size: var(--cmg-text-xl);
  }
  
  .cmg-header__subtitle {
    display: none;
  }
  
  .cmg-main {
    padding: var(--cmg-space-4);
  }
}

@media (max-width: 640px) {
  .cmg-header__actions {
    gap: var(--cmg-space-2);
  }
  
  .cmg-header__actions .el-divider {
    display: none;
  }
}

/* 滚动条样式 */
.cmg-sidebar__menu::-webkit-scrollbar {
  width: 4px;
}

.cmg-sidebar__menu::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.cmg-sidebar__menu::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: var(--cmg-radius-base);
}

.cmg-sidebar__menu::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* 用户下拉框样式 */
.user-dropdown :deep(.el-dropdown-menu) {
  background: white !important;
  border: 1px solid #e4e7ed !important;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1) !important;
}

.user-dropdown :deep(.el-dropdown-menu__item) {
  color: #303133 !important;
  background: white !important;
}

.user-dropdown :deep(.el-dropdown-menu__item:hover) {
  background: #f5f7fa !important;
  color: #303133 !important;
}

.user-dropdown :deep(.el-dropdown-menu__item:focus) {
  background: #f5f7fa !important;
  color: #303133 !important;
}
</style>
