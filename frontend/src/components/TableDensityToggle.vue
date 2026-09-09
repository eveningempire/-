<template>
  <div class="cmg-table-density-toggle">
    <el-dropdown @command="handleDensityChange" placement="bottom-end">
      <el-button text size="small" class="cmg-table-density-toggle__button">
        <el-icon class="cmg-table-density-toggle__icon">
          <component :is="currentDensityIcon" />
        </el-icon>
        <span class="cmg-table-density-toggle__text">{{ currentDensityLabel }}</span>
        <el-icon class="cmg-table-density-toggle__arrow"><ArrowDown /></el-icon>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item 
            v-for="density in densities" 
            :key="density.key"
            :command="density.key"
            :class="{ 'is-active': currentDensity === density.key }"
          >
            <div class="cmg-density-option">
              <el-icon class="cmg-density-option__icon">
                <component :is="density.icon" />
              </el-icon>
              <div class="cmg-density-option__content">
                <div class="cmg-density-option__name">{{ density.name }}</div>
                <div class="cmg-density-option__description">{{ density.description }}</div>
              </div>
              <div v-if="currentDensity === density.key" class="cmg-density-option__check">
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
import { ref, computed, onMounted } from 'vue';
import { 
  Grid, 
  Menu, 
  List,
  ArrowDown, 
  Check 
} from '@element-plus/icons-vue';

const props = defineProps({
  // 默认密度
  defaultDensity: {
    type: String,
    default: 'default',
    validator: (value) => ['compact', 'default', 'comfortable'].includes(value)
  },
  
  // 存储键名
  storageKey: {
    type: String,
    default: 'cmg-table-density'
  }
});

const emit = defineEmits(['change']);

const currentDensity = ref('default');

const densities = [
  {
    key: 'compact',
    name: '紧凑',
    description: '更多数据，节省空间',
    icon: List,
    size: 'small',
    cellPadding: '4px 8px',
    rowHeight: '32px'
  },
  {
    key: 'default',
    name: '标准',
    description: '平衡的显示密度',
    icon: Menu,
    size: 'default',
    cellPadding: '8px 12px',
    rowHeight: '40px'
  },
  {
    key: 'comfortable',
    name: '舒适',
    description: '更大间距，易于阅读',
    icon: Grid,
    size: 'large',
    cellPadding: '12px 16px',
    rowHeight: '48px'
  }
];

const currentDensityData = computed(() => {
  return densities.find(density => density.key === currentDensity.value) || densities[1];
});

const currentDensityIcon = computed(() => currentDensityData.value.icon);
const currentDensityLabel = computed(() => currentDensityData.value.name);

// 处理密度切换
function handleDensityChange(density) {
  currentDensity.value = density;
  
  // 保存到 localStorage
  localStorage.setItem(props.storageKey, density);
  
  // 应用样式
  applyDensityStyles(density);
  
  // 触发事件
  const densityData = densities.find(d => d.key === density);
  emit('change', {
    density,
    size: densityData.size,
    data: densityData
  });
}

// 应用密度样式
function applyDensityStyles(density) {
  const densityData = densities.find(d => d.key === density);
  if (!densityData) return;
  
  const root = document.documentElement;
  
  // 设置 CSS 变量
  root.style.setProperty('--cmg-table-cell-padding', densityData.cellPadding);
  root.style.setProperty('--cmg-table-row-height', densityData.rowHeight);
  root.style.setProperty('--cmg-table-density', density);
  
  // 添加全局类
  document.body.classList.remove('cmg-table-compact', 'cmg-table-default', 'cmg-table-comfortable');
  document.body.classList.add(`cmg-table-${density}`);
}

// 初始化密度设置
function initDensity() {
  const savedDensity = localStorage.getItem(props.storageKey);
  
  if (savedDensity && densities.some(d => d.key === savedDensity)) {
    currentDensity.value = savedDensity;
  } else {
    currentDensity.value = props.defaultDensity;
  }
  
  applyDensityStyles(currentDensity.value);
  
  // 初始化时也触发事件
  const densityData = densities.find(d => d.key === currentDensity.value);
  emit('change', {
    density: currentDensity.value,
    size: densityData.size,
    data: densityData
  });
}

onMounted(() => {
  initDensity();
});

// 暴露给父组件的方法
defineExpose({
  getCurrentDensity: () => currentDensity.value,
  setDensity: handleDensityChange,
  getDensityData: () => currentDensityData.value
});
</script>

<style scoped>
.cmg-table-density-toggle {
  display: inline-block;
}

.cmg-table-density-toggle__button {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
  padding: var(--cmg-space-2) var(--cmg-space-3);
  border-radius: var(--cmg-radius-base);
  transition: var(--cmg-transition-colors);
  color: var(--cmg-text-secondary);
  font-size: var(--cmg-text-sm);
}

.cmg-table-density-toggle__button:hover {
  background-color: var(--cmg-gray-100);
  color: var(--cmg-text-primary);
}

[data-theme="dark"] .cmg-table-density-toggle__button:hover {
  background-color: var(--cmg-gray-800);
}

.cmg-table-density-toggle__icon {
  font-size: 14px;
}

.cmg-table-density-toggle__text {
  font-weight: 500;
}

.cmg-table-density-toggle__arrow {
  font-size: 12px;
  transition: var(--cmg-transition-transform);
}

.cmg-table-density-toggle__button:hover .cmg-table-density-toggle__arrow {
  transform: rotate(180deg);
}

/* 密度选项样式 */
.cmg-density-option {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-3);
  padding: var(--cmg-space-2) 0;
  min-width: 180px;
}

.cmg-density-option__icon {
  font-size: 16px;
  color: var(--cmg-aerospace-primary);
  flex-shrink: 0;
}

.cmg-density-option__content {
  flex: 1;
  min-width: 0;
}

.cmg-density-option__name {
  font-weight: 500;
  color: var(--cmg-text-primary);
  font-size: var(--cmg-text-sm);
  line-height: 1.2;
}

.cmg-density-option__description {
  color: var(--cmg-text-tertiary);
  font-size: var(--cmg-text-xs);
  line-height: 1.2;
  margin-top: 2px;
}

.cmg-density-option__check {
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
  .cmg-table-density-toggle__text {
    display: none;
  }
  
  .cmg-density-option {
    min-width: 160px;
  }
}
</style>

<!-- 全局样式 - 表格密度 -->
<style>
/* 紧凑密度 */
.cmg-table-compact .el-table .el-table__cell {
  padding: 4px 8px;
  font-size: 12px;
}

.cmg-table-compact .el-table .el-table__row {
  height: 32px;
}

.cmg-table-compact .el-table .el-table__header .el-table__cell {
  padding: 6px 8px;
}

/* 标准密度 */
.cmg-table-default .el-table .el-table__cell {
  padding: 8px 12px;
  font-size: 13px;
}

.cmg-table-default .el-table .el-table__row {
  height: 40px;
}

.cmg-table-default .el-table .el-table__header .el-table__cell {
  padding: 10px 12px;
}

/* 舒适密度 */
.cmg-table-comfortable .el-table .el-table__cell {
  padding: 12px 16px;
  font-size: 14px;
}

.cmg-table-comfortable .el-table .el-table__row {
  height: 48px;
}

.cmg-table-comfortable .el-table .el-table__header .el-table__cell {
  padding: 14px 16px;
}

/* 表格样式增强 */
.el-table {
  --el-table-border-color: var(--cmg-border-light);
  --el-table-bg-color: var(--cmg-bg-primary);
  --el-table-tr-bg-color: var(--cmg-bg-primary);
  --el-table-expanded-cell-bg-color: var(--cmg-bg-secondary);
}

.el-table .el-table__header {
  background-color: var(--cmg-bg-tertiary);
}

.el-table .el-table__row:nth-child(even) {
  background-color: var(--cmg-gray-50);
}

.el-table .el-table__row:hover {
  background-color: var(--cmg-primary-50) !important;
}

[data-theme="dark"] .el-table .el-table__row:nth-child(even) {
  background-color: var(--cmg-gray-800);
}

[data-theme="dark"] .el-table .el-table__row:hover {
  background-color: var(--cmg-primary-900) !important;
}

/* 数值列样式 */
.cmg-numeric-column {
  text-align: right;
  font-family: var(--cmg-font-mono);
  font-variant-numeric: tabular-nums;
}

/* 状态列样式 */
.cmg-status-column .el-tag {
  font-weight: 500;
}

/* 粘性表头 */
.cmg-sticky-header .el-table__header-wrapper {
  position: sticky;
  top: 0;
  z-index: var(--cmg-z-sticky);
  box-shadow: var(--cmg-shadow-sm);
}
</style>
