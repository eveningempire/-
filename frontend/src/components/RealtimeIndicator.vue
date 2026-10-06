<template>
  <div class="cmg-realtime-indicator" :class="statusClass">
    <!-- 实时指示灯 -->
    <div class="cmg-realtime-indicator__status">
      <div class="cmg-realtime-indicator__dot" :class="dotClass"></div>
      <span class="cmg-realtime-indicator__label">{{ statusLabel }}</span>
    </div>
    
    <!-- 最后更新时间 -->
    <div v-if="showLastUpdate && lastUpdateTime" class="cmg-realtime-indicator__time">
      <el-icon class="cmg-realtime-indicator__time-icon"><Clock /></el-icon>
      <span class="cmg-realtime-indicator__time-text">{{ formattedLastUpdate }}</span>
    </div>
    
    <!-- 连接状态详情 -->
    <el-popover 
      v-if="showDetails"
      placement="bottom-start" 
      :width="280"
      trigger="hover"
    >
      <template #reference>
        <el-button 
          text 
          size="small" 
          class="cmg-realtime-indicator__details-btn"
        >
          <el-icon><InfoFilled /></el-icon>
        </el-button>
      </template>
      
      <div class="cmg-realtime-details">
        <div class="cmg-realtime-details__header">
          <h4>实时连接状态</h4>
        </div>
        
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="连接状态">
            <el-tag :type="statusTagType" size="small">{{ statusLabel }}</el-tag>
          </el-descriptions-item>
          
          <el-descriptions-item label="WebSocket URL" v-if="wsUrl">
            <code class="cmg-realtime-details__url">{{ wsUrl }}</code>
          </el-descriptions-item>
          
          <el-descriptions-item label="最后更新">
            {{ formattedLastUpdate || '从未更新' }}
          </el-descriptions-item>
          
          <el-descriptions-item label="重连次数" v-if="reconnectCount > 0">
            {{ reconnectCount }} 次
          </el-descriptions-item>
          
          <el-descriptions-item label="延迟" v-if="latency !== null">
            {{ latency }}ms
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="error" class="cmg-realtime-details__error">
          <el-alert 
            :title="error" 
            type="error" 
            size="small" 
            :closable="false"
            show-icon
          />
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { Clock, InfoFilled } from '@element-plus/icons-vue';

const props = defineProps({
  // 连接状态: 'connected', 'connecting', 'disconnected', 'error'
  status: {
    type: String,
    default: 'disconnected',
    validator: (value) => ['connected', 'connecting', 'disconnected', 'error'].includes(value)
  },
  
  // 最后更新时间
  lastUpdateTime: {
    type: [String, Date, Number],
    default: null
  },
  
  // 是否显示最后更新时间
  showLastUpdate: {
    type: Boolean,
    default: true
  },
  
  // 是否显示详情按钮
  showDetails: {
    type: Boolean,
    default: true
  },
  
  // WebSocket URL
  wsUrl: {
    type: String,
    default: ''
  },
  
  // 重连次数
  reconnectCount: {
    type: Number,
    default: 0
  },
  
  // 连接延迟 (ms)
  latency: {
    type: Number,
    default: null
  },
  
  // 错误信息
  error: {
    type: String,
    default: ''
  }
});

// 状态标签映射
const statusLabels = {
  connected: '实时连接',
  connecting: '连接中',
  disconnected: '已断开',
  error: '连接异常'
};

// 状态样式类
const statusClass = computed(() => `cmg-realtime-indicator--${props.status}`);

// 指示点样式类
const dotClass = computed(() => ({
  'cmg-realtime-indicator__dot--pulse': props.status === 'connected',
  'cmg-realtime-indicator__dot--spin': props.status === 'connecting'
}));

// 状态标签
const statusLabel = computed(() => statusLabels[props.status] || '未知状态');

// 标签类型
const statusTagType = computed(() => {
  const typeMap = {
    connected: 'success',
    connecting: 'warning',
    disconnected: 'info',
    error: 'danger'
  };
  return typeMap[props.status] || 'info';
});

// 格式化的最后更新时间
const formattedLastUpdate = computed(() => {
  if (!props.lastUpdateTime) return '';
  
  const date = new Date(props.lastUpdateTime);
  if (isNaN(date.getTime())) return '';
  
  const now = new Date();
  const diff = now - date;
  
  if (diff < 1000) {
    return '刚刚';
  } else if (diff < 60000) {
    return `${Math.floor(diff / 1000)}秒前`;
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`;
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`;
  } else {
    return date.toLocaleString();
  }
});

// 定时更新相对时间
const updateTimer = ref(null);

onMounted(() => {
  // 每秒更新一次相对时间
  updateTimer.value = setInterval(() => {
    // 触发响应式更新
    if (props.lastUpdateTime) {
      // 通过改变一个响应式属性来触发重新计算
    }
  }, 1000);
});

onUnmounted(() => {
  if (updateTimer.value) {
    clearInterval(updateTimer.value);
  }
});
</script>

<style scoped>
.cmg-realtime-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--cmg-space-3);
  padding: var(--cmg-space-2) var(--cmg-space-3);
  border-radius: var(--cmg-radius-base);
  background: var(--cmg-bg-primary);
  border: 1px solid var(--cmg-border-light);
  font-size: var(--cmg-text-sm);
}

.cmg-realtime-indicator__status {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
}

.cmg-realtime-indicator__dot {
  width: 8px;
  height: 8px;
  border-radius: var(--cmg-radius-full);
  transition: var(--cmg-transition-all);
}

/* 状态颜色 */
.cmg-realtime-indicator--connected .cmg-realtime-indicator__dot {
  background-color: var(--cmg-aerospace-success);
}

.cmg-realtime-indicator--connecting .cmg-realtime-indicator__dot {
  background-color: var(--cmg-aerospace-warning);
}

.cmg-realtime-indicator--disconnected .cmg-realtime-indicator__dot {
  background-color: var(--cmg-gray-400);
}

.cmg-realtime-indicator--error .cmg-realtime-indicator__dot {
  background-color: var(--cmg-aerospace-danger);
}

/* 脉冲动画 - 连接状态 */
.cmg-realtime-indicator__dot--pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
    box-shadow: 0 0 0 0 currentColor;
  }
  50% {
    opacity: 0.8;
    transform: scale(1.1);
    box-shadow: 0 0 0 4px transparent;
  }
}

/* 旋转动画 - 连接中状态 */
.cmg-realtime-indicator__dot--spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.cmg-realtime-indicator__label {
  font-weight: 500;
  color: var(--cmg-text-primary);
}

.cmg-realtime-indicator__time {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-1);
  color: var(--cmg-text-tertiary);
  font-size: var(--cmg-text-xs);
  padding-left: var(--cmg-space-2);
  border-left: 1px solid var(--cmg-border-light);
}

.cmg-realtime-indicator__time-icon {
  font-size: 12px;
}

.cmg-realtime-indicator__time-text {
  white-space: nowrap;
}

.cmg-realtime-indicator__details-btn {
  padding: var(--cmg-space-1);
  color: var(--cmg-text-tertiary);
}

.cmg-realtime-indicator__details-btn:hover {
  color: var(--cmg-aerospace-primary);
}

/* 详情弹窗样式 */
.cmg-realtime-details {
  padding: var(--cmg-space-2);
}

.cmg-realtime-details__header {
  margin-bottom: var(--cmg-space-3);
}

.cmg-realtime-details__header h4 {
  margin: 0;
  font-size: var(--cmg-text-base);
  color: var(--cmg-text-primary);
  font-weight: 600;
}

.cmg-realtime-details__url {
  font-family: var(--cmg-font-mono);
  font-size: var(--cmg-text-xs);
  color: var(--cmg-aerospace-primary);
  background: var(--cmg-bg-tertiary);
  padding: var(--cmg-space-1) var(--cmg-space-2);
  border-radius: var(--cmg-radius-sm);
  word-break: break-all;
}

.cmg-realtime-details__error {
  margin-top: var(--cmg-space-3);
}

/* 状态变体样式 */
.cmg-realtime-indicator--connected {
  border-color: var(--cmg-success-500);
  background: var(--cmg-success-50);
}

.cmg-realtime-indicator--connecting {
  border-color: var(--cmg-warning-500);
  background: var(--cmg-warning-50);
}

.cmg-realtime-indicator--error {
  border-color: var(--cmg-error-500);
  background: var(--cmg-error-50);
}

/* 暗色主题适配 */
[data-theme="dark"] .cmg-realtime-indicator {
  background: var(--cmg-bg-secondary);
  border-color: var(--cmg-border-base);
}

[data-theme="dark"] .cmg-realtime-indicator--connected {
  background: rgba(82, 196, 26, 0.1);
  border-color: var(--cmg-success-500);
}

[data-theme="dark"] .cmg-realtime-indicator--connecting {
  background: rgba(250, 173, 20, 0.1);
  border-color: var(--cmg-warning-500);
}

[data-theme="dark"] .cmg-realtime-indicator--error {
  background: rgba(255, 77, 79, 0.1);
  border-color: var(--cmg-error-500);
}

/* 响应式设计 */
@media (max-width: 640px) {
  .cmg-realtime-indicator {
    font-size: var(--cmg-text-xs);
    padding: var(--cmg-space-1) var(--cmg-space-2);
    gap: var(--cmg-space-2);
  }
  
  .cmg-realtime-indicator__time {
    display: none;
  }
  
  .cmg-realtime-indicator__dot {
    width: 6px;
    height: 6px;
  }
}
</style>
