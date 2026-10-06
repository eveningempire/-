<template>
  <div class="cmg-section-card" :class="[sizeClass, { 'is-loading': loading }]">
    <!-- 卡片头部 -->
    <div v-if="$slots.header || title || $slots.actions" class="cmg-section-card__header">
      <div class="cmg-section-card__title-area">
        <slot name="header">
          <h3 v-if="title" class="cmg-section-card__title">
            <el-icon v-if="icon" class="cmg-section-card__icon">
              <component :is="icon" />
            </el-icon>
            {{ title }}
          </h3>
        </slot>
      </div>
      <div v-if="$slots.actions" class="cmg-section-card__actions">
        <slot name="actions"></slot>
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="cmg-section-card__body" :class="{ 'no-padding': noPadding }">
      <!-- 加载状态 -->
      <div v-if="loading" class="cmg-section-card__loading">
        <el-skeleton :rows="skeletonRows" animated />
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="isEmpty && !$slots.default" class="cmg-section-card__empty">
        <div class="cmg-empty-state">
          <div class="cmg-empty-state-icon">
            <el-icon><component :is="emptyIcon" /></el-icon>
          </div>
          <div class="cmg-empty-state-title">{{ emptyTitle }}</div>
          <div class="cmg-empty-state-description">{{ emptyDescription }}</div>
          <div v-if="$slots.emptyActions" class="cmg-empty-state-actions">
            <slot name="emptyActions"></slot>
          </div>
        </div>
      </div>
      
      <!-- 正常内容 -->
      <div v-else class="cmg-section-card__content">
        <slot></slot>
      </div>
    </div>

    <!-- 卡片底部 -->
    <div v-if="$slots.footer" class="cmg-section-card__footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Document, Warning, InfoFilled } from '@element-plus/icons-vue';

const props = defineProps({
  // 标题
  title: {
    type: String,
    default: ''
  },
  
  // 图标
  icon: {
    type: [String, Object],
    default: null
  },
  
  // 尺寸
  size: {
    type: String,
    default: 'default', // small, default, large
    validator: (value) => ['small', 'default', 'large'].includes(value)
  },
  
  // 加载状态
  loading: {
    type: Boolean,
    default: false
  },
  
  // 骨架屏行数
  skeletonRows: {
    type: Number,
    default: 3
  },
  
  // 是否为空
  isEmpty: {
    type: Boolean,
    default: false
  },
  
  // 空状态配置
  emptyTitle: {
    type: String,
    default: '暂无数据'
  },
  
  emptyDescription: {
    type: String,
    default: '当前没有可显示的内容'
  },
  
  emptyIcon: {
    type: [String, Object],
    default: () => Document
  },
  
  // 是否移除内容区域的内边距
  noPadding: {
    type: Boolean,
    default: false
  },
  
  // 是否显示阴影
  shadow: {
    type: String,
    default: 'base', // none, sm, base, md, lg
    validator: (value) => ['none', 'sm', 'base', 'md', 'lg'].includes(value)
  }
});

const sizeClass = computed(() => `cmg-section-card--${props.size}`);
</script>

<style scoped>
.cmg-section-card {
  background: var(--cmg-bg-primary);
  border: 1px solid var(--cmg-border-light);
  border-radius: var(--cmg-radius-lg);
  box-shadow: var(--cmg-shadow-sm);
  transition: var(--cmg-transition-all);
  overflow: hidden;
}

.cmg-section-card:hover {
  border-color: var(--cmg-border-base);
  box-shadow: var(--cmg-shadow-md);
}

/* 尺寸变体 */
.cmg-section-card--small {
  font-size: var(--cmg-text-sm);
}

.cmg-section-card--large {
  font-size: var(--cmg-text-lg);
}

/* 头部区域 */
.cmg-section-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--cmg-space-4) var(--cmg-space-6);
  border-bottom: 1px solid var(--cmg-border-light);
  background: var(--cmg-bg-tertiary);
  min-height: 60px;
}

.cmg-section-card--small .cmg-section-card__header {
  padding: var(--cmg-space-3) var(--cmg-space-4);
  min-height: 48px;
}

.cmg-section-card--large .cmg-section-card__header {
  padding: var(--cmg-space-5) var(--cmg-space-8);
  min-height: 72px;
}

.cmg-section-card__title-area {
  flex: 1;
  min-width: 0;
}

.cmg-section-card__title {
  margin: 0;
  font-size: var(--cmg-text-lg);
  font-weight: 600;
  color: var(--cmg-text-primary);
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
}

.cmg-section-card--small .cmg-section-card__title {
  font-size: var(--cmg-text-base);
}

.cmg-section-card--large .cmg-section-card__title {
  font-size: var(--cmg-text-xl);
}

.cmg-section-card__icon {
  color: var(--cmg-aerospace-primary);
  font-size: 1.2em;
}

.cmg-section-card__actions {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
  flex-shrink: 0;
}

/* 内容区域 */
.cmg-section-card__body {
  position: relative;
  min-height: 120px;
}

.cmg-section-card__content {
  padding: var(--cmg-space-6);
}

.cmg-section-card__content.no-padding {
  padding: 0;
}

.cmg-section-card--small .cmg-section-card__content {
  padding: var(--cmg-space-4);
}

.cmg-section-card--large .cmg-section-card__content {
  padding: var(--cmg-space-8);
}

/* 加载状态 */
.cmg-section-card__loading {
  padding: var(--cmg-space-6);
}

.cmg-section-card--small .cmg-section-card__loading {
  padding: var(--cmg-space-4);
}

.cmg-section-card--large .cmg-section-card__loading {
  padding: var(--cmg-space-8);
}

.cmg-section-card.is-loading {
  pointer-events: none;
}

/* 空状态 */
.cmg-section-card__empty {
  padding: var(--cmg-space-8) var(--cmg-space-6);
}

.cmg-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--cmg-text-tertiary);
}

.cmg-empty-state-icon {
  font-size: 48px;
  margin-bottom: var(--cmg-space-4);
  opacity: 0.5;
  color: var(--cmg-text-disabled);
}

.cmg-empty-state-title {
  font-size: var(--cmg-text-lg);
  font-weight: 500;
  color: var(--cmg-text-secondary);
  margin-bottom: var(--cmg-space-2);
}

.cmg-empty-state-description {
  font-size: var(--cmg-text-sm);
  margin-bottom: var(--cmg-space-4);
  max-width: 300px;
  line-height: 1.5;
}

.cmg-empty-state-actions {
  display: flex;
  gap: var(--cmg-space-2);
  flex-wrap: wrap;
  justify-content: center;
}

/* 底部区域 */
.cmg-section-card__footer {
  padding: var(--cmg-space-4) var(--cmg-space-6);
  border-top: 1px solid var(--cmg-border-light);
  background: var(--cmg-bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--cmg-space-4);
}

.cmg-section-card--small .cmg-section-card__footer {
  padding: var(--cmg-space-3) var(--cmg-space-4);
}

.cmg-section-card--large .cmg-section-card__footer {
  padding: var(--cmg-space-5) var(--cmg-space-8);
}

/* 阴影变体 */
.cmg-section-card[data-shadow="none"] {
  box-shadow: none;
}

.cmg-section-card[data-shadow="sm"] {
  box-shadow: var(--cmg-shadow-sm);
}

.cmg-section-card[data-shadow="base"] {
  box-shadow: var(--cmg-shadow-base);
}

.cmg-section-card[data-shadow="md"] {
  box-shadow: var(--cmg-shadow-md);
}

.cmg-section-card[data-shadow="lg"] {
  box-shadow: var(--cmg-shadow-lg);
}

/* 响应式设计 */
@media (max-width: 640px) {
  .cmg-section-card__header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--cmg-space-3);
    min-height: auto;
  }
  
  .cmg-section-card__actions {
    justify-content: flex-end;
  }
  
  .cmg-section-card__content {
    padding: var(--cmg-space-4);
  }
  
  .cmg-section-card__footer {
    flex-direction: column;
    align-items: stretch;
    gap: var(--cmg-space-2);
  }
}

/* 暗色主题适配 */
[data-theme="dark"] .cmg-section-card {
  background: var(--cmg-bg-primary);
  border-color: var(--cmg-border-base);
}

[data-theme="dark"] .cmg-section-card__header,
[data-theme="dark"] .cmg-section-card__footer {
  background: var(--cmg-bg-secondary);
  border-color: var(--cmg-border-base);
}
</style>
