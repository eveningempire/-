<template>
  <div class="cmg-theme-toggle">
    <el-dropdown @command="handleThemeChange" placement="bottom-end">
      <el-button text class="cmg-theme-toggle__button">
        <el-icon class="cmg-theme-toggle__icon">
          <component :is="currentThemeIcon" />
        </el-icon>
        <span class="cmg-theme-toggle__text">{{ currentThemeName }}</span>
        <el-icon class="cmg-theme-toggle__arrow"><ArrowDown /></el-icon>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item 
            v-for="theme in themes" 
            :key="theme.key"
            :command="theme.key"
            :class="{ 'is-active': currentTheme === theme.key }"
          >
            <div class="cmg-theme-option">
              <el-icon class="cmg-theme-option__icon">
                <component :is="theme.icon" />
              </el-icon>
              <div class="cmg-theme-option__content">
                <div class="cmg-theme-option__name">{{ theme.name }}</div>
                <div class="cmg-theme-option__description">{{ theme.description }}</div>
              </div>
              <div v-if="currentTheme === theme.key" class="cmg-theme-option__check">
                <el-icon><Check /></el-icon>
              </div>
            </div>
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { 
  Sunny, 
  Moon, 
  Monitor, 
  ArrowDown, 
  Check 
} from '@element-plus/icons-vue';

const currentTheme = ref('light');

const themes = [
  {
    key: 'light',
    name: '科研蓝',
    description: '专业科研风格浅色主题',
    icon: Sunny
  },
  {
    key: 'dark',
    name: '深空暗色',
    description: '航天风格深色主题',
    icon: Moon
  },
  {
    key: 'auto',
    name: '跟随系统',
    description: '根据系统设置自动切换',
    icon: Monitor
  }
];

const currentThemeData = computed(() => {
  return themes.find(theme => theme.key === currentTheme.value) || themes[0];
});

const currentThemeIcon = computed(() => currentThemeData.value.icon);
const currentThemeName = computed(() => currentThemeData.value.name);

// 应用主题
function applyTheme(theme) {
  const root = document.documentElement;
  
  if (theme === 'auto') {
    // 跟随系统主题
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
  } else {
    root.setAttribute('data-theme', theme);
  }
  
  // 保存到 localStorage
  localStorage.setItem('cmg-theme', theme);
}

// 处理主题切换
function handleThemeChange(theme) {
  currentTheme.value = theme;
  applyTheme(theme);
  
  // 触发主题变更事件
  window.dispatchEvent(new CustomEvent('theme-change', { 
    detail: { theme } 
  }));
}

// 监听系统主题变化
function setupSystemThemeListener() {
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  
  const handleSystemThemeChange = (e) => {
    if (currentTheme.value === 'auto') {
      applyTheme('auto');
    }
  };
  
  mediaQuery.addEventListener('change', handleSystemThemeChange);
  
  // 返回清理函数
  return () => {
    mediaQuery.removeEventListener('change', handleSystemThemeChange);
  };
}

// 初始化主题
function initTheme() {
  const savedTheme = localStorage.getItem('cmg-theme');
  
  if (savedTheme && themes.some(theme => theme.key === savedTheme)) {
    currentTheme.value = savedTheme;
  } else {
    // 默认跟随系统
    currentTheme.value = 'auto';
  }
  
  applyTheme(currentTheme.value);
}

onMounted(() => {
  initTheme();
  const cleanup = setupSystemThemeListener();
  
  // 组件卸载时清理监听器
  return cleanup;
});

// 暴露给父组件的方法
defineExpose({
  getCurrentTheme: () => currentTheme.value,
  setTheme: handleThemeChange
});
</script>

<style scoped>
.cmg-theme-toggle {
  display: inline-block;
}

.cmg-theme-toggle__button {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
  padding: var(--cmg-space-2) var(--cmg-space-3);
  border-radius: var(--cmg-radius-base);
  transition: var(--cmg-transition-colors);
  color: var(--cmg-text-secondary);
}

.cmg-theme-toggle__button:hover {
  background-color: var(--cmg-gray-100);
  color: var(--cmg-text-primary);
}

[data-theme="dark"] .cmg-theme-toggle__button:hover {
  background-color: var(--cmg-gray-800);
}

.cmg-theme-toggle__icon {
  font-size: 16px;
}

.cmg-theme-toggle__text {
  font-size: var(--cmg-text-sm);
  font-weight: 500;
}

.cmg-theme-toggle__arrow {
  font-size: 12px;
  transition: var(--cmg-transition-transform);
}

.cmg-theme-toggle__button:hover .cmg-theme-toggle__arrow {
  transform: rotate(180deg);
}

/* 主题选项样式 */
.cmg-theme-option {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-3);
  padding: var(--cmg-space-2) 0;
  min-width: 200px;
}

.cmg-theme-option__icon {
  font-size: 18px;
  color: var(--cmg-aerospace-primary);
  flex-shrink: 0;
}

.cmg-theme-option__content {
  flex: 1;
  min-width: 0;
}

.cmg-theme-option__name {
  font-weight: 500;
  color: var(--cmg-text-primary);
  font-size: var(--cmg-text-sm);
  line-height: 1.2;
}

.cmg-theme-option__description {
  color: var(--cmg-text-tertiary);
  font-size: var(--cmg-text-xs);
  line-height: 1.2;
  margin-top: 2px;
}

.cmg-theme-option__check {
  color: var(--cmg-aerospace-success);
  font-size: 14px;
  flex-shrink: 0;
}

/* 激活状态 */
:deep(.el-dropdown-menu__item.is-active) {
  background-color: var(--cmg-primary-50);
  color: var(--cmg-aerospace-primary);
}

[data-theme="dark"] :deep(.el-dropdown-menu__item.is-active) {
  background-color: var(--cmg-primary-900);
}

/* 响应式设计 */
@media (max-width: 640px) {
  .cmg-theme-toggle__text {
    display: none;
  }
  
  .cmg-theme-option {
    min-width: 180px;
  }
}
</style>
