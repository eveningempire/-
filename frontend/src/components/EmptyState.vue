<template>
  <div class="cmg-empty-state" :class="[sizeClass, typeClass]">
    <div class="cmg-empty-state__icon">
      <el-icon v-if="!customIcon">
        <component :is="iconComponent" />
      </el-icon>
      <div v-else class="cmg-empty-state__custom-icon">
        <slot name="icon">
          <component :is="customIcon" />
        </slot>
      </div>
    </div>
    
    <div class="cmg-empty-state__content">
      <h3 v-if="title" class="cmg-empty-state__title">{{ title }}</h3>
      <p v-if="description" class="cmg-empty-state__description">{{ description }}</p>
      
      <div v-if="$slots.content" class="cmg-empty-state__extra-content">
        <slot name="content"></slot>
      </div>
    </div>
    
    <div v-if="$slots.actions || showRetry" class="cmg-empty-state__actions">
      <slot name="actions">
        <el-button v-if="showRetry" type="primary" @click="handleRetry" :loading="retrying">
          <el-icon><Refresh /></el-icon>
          {{ retryText }}
        </el-button>
      </slot>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { 
  Document, 
  Search, 
  Connection, 
  Warning, 
  Lock, 
  Refresh,
  QuestionFilled
} from '@element-plus/icons-vue';

const props = defineProps({
  // 空状态类型
  type: {
    type: String,
    default: 'empty',
    validator: (value) => [
      'empty', 'search', 'error', 'network', 
      'permission', 'loading', 'maintenance'
    ].includes(value)
  },
  
  // 尺寸
  size: {
    type: String,
    default: 'default',
    validator: (value) => ['small', 'default', 'large'].includes(value)
  },
  
  // 标题
  title: {
    type: String,
    default: ''
  },
  
  // 描述
  description: {
    type: String,
    default: ''
  },
  
  // 自定义图标
  customIcon: {
    type: [String, Object],
    default: null
  },
  
  // 是否显示重试按钮
  showRetry: {
    type: Boolean,
    default: false
  },
  
  // 重试按钮文本
  retryText: {
    type: String,
    default: '重试'
  }
});

const emit = defineEmits(['retry']);

const retrying = ref(false);

// 预设配置
const presetConfigs = {
  empty: {
    icon: Document,
    title: '暂无数据',
    description: '当前没有可显示的内容'
  },
  search: {
    icon: Search,
    title: '无搜索结果',
    description: '请尝试调整搜索条件或关键词'
  },
  error: {
    icon: Warning,
    title: '加载失败',
    description: '数据加载时出现错误，请稍后重试'
  },
  network: {
    icon: Connection,
    title: '网络异常',
    description: '请检查网络连接后重试'
  },
  permission: {
    icon: Lock,
    title: '无访问权限',
    description: '您没有权限访问此内容，请联系管理员'
  },
  loading: {
    icon: Connection,
    title: '正在加载',
    description: '请稍候...'
  },
  maintenance: {
    icon: QuestionFilled,
    title: '系统维护中',
    description: '系统正在维护，请稍后再试'
  }
};

// 计算属性
const sizeClass = computed(() => `cmg-empty-state--${props.size}`);
const typeClass = computed(() => `cmg-empty-state--${props.type}`);

const currentConfig = computed(() => presetConfigs[props.type] || presetConfigs.empty);

const iconComponent = computed(() => {
  return props.customIcon || currentConfig.value.icon;
});

const finalTitle = computed(() => {
  return props.title || currentConfig.value.title;
});

const finalDescription = computed(() => {
  return props.description || currentConfig.value.description;
});

// 重试处理
async function handleRetry() {
  retrying.value = true;
  try {
    await emit('retry');
  } finally {
    retrying.value = false;
  }
}
</script>

<style scoped>
.cmg-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--cmg-space-12);
  color: var(--cmg-text-tertiary);
  min-height: 200px;
}

/* 尺寸变体 */
.cmg-empty-state--small {
  padding: var(--cmg-space-8);
  min-height: 120px;
}

.cmg-empty-state--large {
  padding: var(--cmg-space-16);
  min-height: 300px;
}

/* 图标区域 */
.cmg-empty-state__icon {
  margin-bottom: var(--cmg-space-6);
  opacity: 0.6;
}

.cmg-empty-state__icon .el-icon {
  font-size: 64px;
  color: var(--cmg-text-disabled);
}

.cmg-empty-state--small .cmg-empty-state__icon .el-icon {
  font-size: 48px;
}

.cmg-empty-state--large .cmg-empty-state__icon .el-icon {
  font-size: 80px;
}

.cmg-empty-state__custom-icon {
  font-size: 64px;
  color: var(--cmg-text-disabled);
}

/* 类型特定的图标颜色 */
.cmg-empty-state--error .cmg-empty-state__icon .el-icon,
.cmg-empty-state--error .cmg-empty-state__custom-icon {
  color: var(--cmg-aerospace-danger);
}

.cmg-empty-state--network .cmg-empty-state__icon .el-icon,
.cmg-empty-state--network .cmg-empty-state__custom-icon {
  color: var(--cmg-aerospace-warning);
}

.cmg-empty-state--permission .cmg-empty-state__icon .el-icon,
.cmg-empty-state--permission .cmg-empty-state__custom-icon {
  color: var(--cmg-aerospace-warning);
}

.cmg-empty-state--loading .cmg-empty-state__icon .el-icon,
.cmg-empty-state--loading .cmg-empty-state__custom-icon {
  color: var(--cmg-aerospace-primary);
  animation: spin 2s linear infinite;
}

.cmg-empty-state--search .cmg-empty-state__icon .el-icon,
.cmg-empty-state--search .cmg-empty-state__custom-icon {
  color: var(--cmg-aerospace-accent);
}

/* 内容区域 */
.cmg-empty-state__content {
  margin-bottom: var(--cmg-space-6);
}

.cmg-empty-state__title {
  margin: 0 0 var(--cmg-space-3) 0;
  font-size: var(--cmg-text-xl);
  font-weight: 600;
  color: var(--cmg-text-secondary);
  line-height: 1.4;
}

.cmg-empty-state--small .cmg-empty-state__title {
  font-size: var(--cmg-text-lg);
}

.cmg-empty-state--large .cmg-empty-state__title {
  font-size: var(--cmg-text-2xl);
}

.cmg-empty-state__description {
  margin: 0;
  font-size: var(--cmg-text-base);
  color: var(--cmg-text-tertiary);
  line-height: 1.6;
  max-width: 400px;
}

.cmg-empty-state--small .cmg-empty-state__description {
  font-size: var(--cmg-text-sm);
  max-width: 300px;
}

.cmg-empty-state--large .cmg-empty-state__description {
  font-size: var(--cmg-text-lg);
  max-width: 500px;
}

.cmg-empty-state__extra-content {
  margin-top: var(--cmg-space-4);
}

/* 操作区域 */
.cmg-empty-state__actions {
  display: flex;
  gap: var(--cmg-space-3);
  flex-wrap: wrap;
  justify-content: center;
}

/* 动画 */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 类型特定样式 */
.cmg-empty-state--error {
  background: linear-gradient(135deg, rgba(255, 77, 79, 0.02), rgba(255, 77, 79, 0.05));
  border: 1px solid rgba(255, 77, 79, 0.1);
  border-radius: var(--cmg-radius-lg);
}

.cmg-empty-state--network {
  background: linear-gradient(135deg, rgba(250, 173, 20, 0.02), rgba(250, 173, 20, 0.05));
  border: 1px solid rgba(250, 173, 20, 0.1);
  border-radius: var(--cmg-radius-lg);
}

.cmg-empty-state--permission {
  background: linear-gradient(135deg, rgba(250, 173, 20, 0.02), rgba(250, 173, 20, 0.05));
  border: 1px solid rgba(250, 173, 20, 0.1);
  border-radius: var(--cmg-radius-lg);
}

.cmg-empty-state--loading {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.02), rgba(24, 144, 255, 0.05));
  border: 1px solid rgba(24, 144, 255, 0.1);
  border-radius: var(--cmg-radius-lg);
}

/* 响应式设计 */
@media (max-width: 640px) {
  .cmg-empty-state {
    padding: var(--cmg-space-8);
    min-height: 160px;
  }
  
  .cmg-empty-state__icon .el-icon,
  .cmg-empty-state__custom-icon {
    font-size: 48px;
  }
  
  .cmg-empty-state__title {
    font-size: var(--cmg-text-lg);
  }
  
  .cmg-empty-state__description {
    font-size: var(--cmg-text-sm);
    max-width: 280px;
  }
  
  .cmg-empty-state__actions {
    flex-direction: column;
    align-items: center;
    width: 100%;
  }
  
  .cmg-empty-state__actions .el-button {
    width: 100%;
    max-width: 200px;
  }
}

/* 暗色主题适配 */
[data-theme="dark"] .cmg-empty-state--error {
  background: linear-gradient(135deg, rgba(255, 77, 79, 0.05), rgba(255, 77, 79, 0.1));
  border-color: rgba(255, 77, 79, 0.2);
}

[data-theme="dark"] .cmg-empty-state--network {
  background: linear-gradient(135deg, rgba(250, 173, 20, 0.05), rgba(250, 173, 20, 0.1));
  border-color: rgba(250, 173, 20, 0.2);
}

[data-theme="dark"] .cmg-empty-state--permission {
  background: linear-gradient(135deg, rgba(250, 173, 20, 0.05), rgba(250, 173, 20, 0.1));
  border-color: rgba(250, 173, 20, 0.2);
}

[data-theme="dark"] .cmg-empty-state--loading {
  background: linear-gradient(135deg, rgba(64, 169, 255, 0.05), rgba(64, 169, 255, 0.1));
  border-color: rgba(64, 169, 255, 0.2);
}
</style>
