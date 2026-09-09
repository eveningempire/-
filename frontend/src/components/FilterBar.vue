<template>
  <div class="cmg-filter-bar" :class="[sizeClass, layoutClass]">
    <div class="cmg-filter-bar__content">
      <el-form 
        :model="filters" 
        :inline="layout === 'inline'"
        :label-width="labelWidth"
        class="cmg-filter-form"
      >
        <el-form-item
          v-for="field in fields"
          :key="field.key"
          :label="field.label"
          :prop="field.key"
          :class="field.className"
        >
          <!-- 文本输入 -->
          <el-input
            v-if="field.type === 'input'"
            v-model="filters[field.key]"
            :placeholder="field.placeholder"
            :clearable="field.clearable !== false"
            :disabled="field.disabled"
            :style="{ width: field.width || '200px' }"
            @change="handleChange(field.key, $event)"
          >
            <template v-if="field.prefix" #prefix>
              <el-icon><component :is="field.prefix" /></el-icon>
            </template>
            <template v-if="field.suffix" #suffix>
              <el-icon><component :is="field.suffix" /></el-icon>
            </template>
          </el-input>

          <!-- 选择器 -->
          <el-select
            v-else-if="field.type === 'select'"
            v-model="filters[field.key]"
            :placeholder="field.placeholder"
            :clearable="field.clearable !== false"
            :filterable="field.filterable"
            :multiple="field.multiple"
            :disabled="field.disabled"
            :style="{ width: field.width || '200px' }"
            @change="handleChange(field.key, $event)"
          >
            <el-option
              v-for="option in field.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
              :disabled="option.disabled"
            >
              <div v-if="field.optionRender" class="cmg-option-custom">
                <component 
                  :is="field.optionRender" 
                  :option="option"
                />
              </div>
            </el-option>
          </el-select>

          <!-- 日期选择器 -->
          <el-date-picker
            v-else-if="field.type === 'date'"
            v-model="filters[field.key]"
            :type="field.dateType || 'date'"
            :placeholder="field.placeholder"
            :start-placeholder="field.startPlaceholder"
            :end-placeholder="field.endPlaceholder"
            :range-separator="field.rangeSeparator || '-'"
            :shortcuts="field.shortcuts || defaultTimeShortcuts"
            :disabled="field.disabled"
            :style="{ width: field.width || '300px' }"
            @change="handleChange(field.key, $event)"
          />

          <!-- 数字输入 -->
          <el-input-number
            v-else-if="field.type === 'number'"
            v-model="filters[field.key]"
            :placeholder="field.placeholder"
            :min="field.min"
            :max="field.max"
            :step="field.step"
            :precision="field.precision"
            :disabled="field.disabled"
            :style="{ width: field.width || '150px' }"
            @change="handleChange(field.key, $event)"
          />

          <!-- 开关 -->
          <el-switch
            v-else-if="field.type === 'switch'"
            v-model="filters[field.key]"
            :active-text="field.activeText"
            :inactive-text="field.inactiveText"
            :disabled="field.disabled"
            @change="handleChange(field.key, $event)"
          />

          <!-- 标签选择 -->
          <div v-else-if="field.type === 'tags'" class="cmg-tag-selector">
            <el-tag
              v-for="tag in field.options"
              :key="tag.value"
              :type="isTagSelected(field.key, tag.value) ? 'primary' : ''"
              :effect="isTagSelected(field.key, tag.value) ? 'dark' : 'plain'"
              class="cmg-tag-option"
              @click="toggleTag(field.key, tag.value)"
            >
              <el-icon v-if="tag.icon"><component :is="tag.icon" /></el-icon>
              {{ tag.label }}
            </el-tag>
          </div>

          <!-- 自定义插槽 -->
          <div v-else-if="field.type === 'slot'" class="cmg-custom-field">
            <slot :name="field.key" :field="field" :value="filters[field.key]"></slot>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 操作按钮区域 -->
    <div class="cmg-filter-bar__actions">
      <el-button-group v-if="showActions">
        <el-button 
          type="primary" 
          @click="handleSearch"
          :loading="searching"
        >
          <el-icon><Search /></el-icon>
          {{ searchText }}
        </el-button>
        <el-button 
          @click="handleReset"
          :disabled="searching"
        >
          <el-icon><RefreshLeft /></el-icon>
          {{ resetText }}
        </el-button>
      </el-button-group>

      <!-- 额外操作 -->
      <div v-if="$slots.actions" class="cmg-filter-bar__extra-actions">
        <slot name="actions" :filters="filters" :search="handleSearch" :reset="handleReset"></slot>
      </div>

      <!-- 筛选方案管理 -->
      <el-dropdown v-if="showPresets" @command="handlePresetCommand">
        <el-button text>
          <el-icon><Setting /></el-icon>
          筛选方案
          <el-icon class="el-icon--right"><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item 
              v-for="preset in presets" 
              :key="preset.key"
              :command="`load:${preset.key}`"
            >
              <el-icon><Folder /></el-icon>
              {{ preset.name }}
            </el-dropdown-item>
            <el-dropdown-item divided command="save">
              <el-icon><Plus /></el-icon>
              保存当前方案
            </el-dropdown-item>
            <el-dropdown-item command="manage">
              <el-icon><Setting /></el-icon>
              管理方案
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { 
  Search, RefreshLeft, Setting, ArrowDown, Folder, Plus 
} from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';

const props = defineProps({
  // 筛选字段配置
  fields: {
    type: Array,
    required: true
  },
  
  // 初始值
  modelValue: {
    type: Object,
    default: () => ({})
  },
  
  // 布局方式
  layout: {
    type: String,
    default: 'inline',
    validator: (value) => ['inline', 'vertical', 'grid'].includes(value)
  },
  
  // 尺寸
  size: {
    type: String,
    default: 'default',
    validator: (value) => ['small', 'default', 'large'].includes(value)
  },
  
  // 标签宽度
  labelWidth: {
    type: String,
    default: 'auto'
  },
  
  // 是否显示操作按钮
  showActions: {
    type: Boolean,
    default: true
  },
  
  // 是否显示预设方案
  showPresets: {
    type: Boolean,
    default: false
  },
  
  // 搜索按钮文本
  searchText: {
    type: String,
    default: '搜索'
  },
  
  // 重置按钮文本
  resetText: {
    type: String,
    default: '重置'
  },
  
  // 预设方案
  presets: {
    type: Array,
    default: () => []
  },
  
  // 是否自动搜索
  autoSearch: {
    type: Boolean,
    default: false
  },
  
  // 自动搜索延迟（毫秒）
  autoSearchDelay: {
    type: Number,
    default: 500
  }
});

const emit = defineEmits(['update:modelValue', 'search', 'reset', 'change', 'preset-save', 'preset-load']);

const filters = ref({ ...props.modelValue });
const searching = ref(false);
let autoSearchTimer = null;

// 默认时间快捷选项
const defaultTimeShortcuts = [
  {
    text: '近1小时',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setHours(start.getHours() - 1);
      return [start, end];
    }
  },
  {
    text: '近6小时',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setHours(start.getHours() - 6);
      return [start, end];
    }
  },
  {
    text: '近24小时',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setHours(start.getHours() - 24);
      return [start, end];
    }
  },
  {
    text: '近7天',
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - 7);
      return [start, end];
    }
  }
];

// 计算属性
const sizeClass = computed(() => `cmg-filter-bar--${props.size}`);
const layoutClass = computed(() => `cmg-filter-bar--${props.layout}`);

// 监听外部值变化
watch(() => props.modelValue, (newVal) => {
  filters.value = { ...newVal };
}, { deep: true });

// 监听内部值变化
watch(filters, (newVal) => {
  emit('update:modelValue', { ...newVal });
  
  if (props.autoSearch) {
    clearTimeout(autoSearchTimer);
    autoSearchTimer = setTimeout(() => {
      handleSearch();
    }, props.autoSearchDelay);
  }
}, { deep: true });

// 字段值变化处理
function handleChange(key, value) {
  filters.value[key] = value;
  emit('change', key, value, filters.value);
}

// 标签选择处理
function isTagSelected(fieldKey, tagValue) {
  const value = filters.value[fieldKey];
  if (Array.isArray(value)) {
    return value.includes(tagValue);
  }
  return value === tagValue;
}

function toggleTag(fieldKey, tagValue) {
  const field = props.fields.find(f => f.key === fieldKey);
  if (!field) return;
  
  if (field.multiple) {
    const currentValue = filters.value[fieldKey] || [];
    const index = currentValue.indexOf(tagValue);
    if (index > -1) {
      currentValue.splice(index, 1);
    } else {
      currentValue.push(tagValue);
    }
    filters.value[fieldKey] = [...currentValue];
  } else {
    filters.value[fieldKey] = filters.value[fieldKey] === tagValue ? null : tagValue;
  }
}

// 搜索处理
async function handleSearch() {
  searching.value = true;
  try {
    await emit('search', { ...filters.value });
  } finally {
    searching.value = false;
  }
}

// 重置处理
function handleReset() {
  const resetValues = {};
  props.fields.forEach(field => {
    if (field.defaultValue !== undefined) {
      resetValues[field.key] = field.defaultValue;
    } else if (field.multiple || field.type === 'tags') {
      resetValues[field.key] = [];
    } else {
      resetValues[field.key] = null;
    }
  });
  
  filters.value = resetValues;
  emit('reset', resetValues);
  
  if (props.autoSearch) {
    nextTick(() => {
      handleSearch();
    });
  }
}

// 预设方案处理
async function handlePresetCommand(command) {
  if (command.startsWith('load:')) {
    const presetKey = command.replace('load:', '');
    const preset = props.presets.find(p => p.key === presetKey);
    if (preset) {
      filters.value = { ...preset.filters };
      emit('preset-load', preset);
      ElMessage.success(`已应用筛选方案：${preset.name}`);
    }
  } else if (command === 'save') {
    try {
      const { value: name } = await ElMessageBox.prompt('请输入方案名称', '保存筛选方案', {
        confirmButtonText: '保存',
        cancelButtonText: '取消',
        inputPattern: /\S+/,
        inputErrorMessage: '方案名称不能为空'
      });
      
      if (name) {
        const preset = {
          key: `preset_${Date.now()}`,
          name: name.trim(),
          filters: { ...filters.value },
          createTime: new Date().toISOString()
        };
        emit('preset-save', preset);
        ElMessage.success('筛选方案保存成功');
      }
    } catch {
      // 用户取消
    }
  } else if (command === 'manage') {
    // 触发管理事件，由父组件处理
    emit('preset-manage');
  }
}

// 暴露方法给父组件
defineExpose({
  search: handleSearch,
  reset: handleReset,
  getFilters: () => ({ ...filters.value }),
  setFilters: (newFilters) => {
    filters.value = { ...newFilters };
  }
});
</script>

<style scoped>
.cmg-filter-bar {
  background: var(--cmg-bg-primary);
  border: 1px solid var(--cmg-border-light);
  border-radius: var(--cmg-radius-lg);
  padding: var(--cmg-space-4);
  display: flex;
  align-items: flex-start;
  gap: var(--cmg-space-4);
  transition: var(--cmg-transition-all);
}

.cmg-filter-bar:hover {
  border-color: var(--cmg-border-base);
  box-shadow: var(--cmg-shadow-sm);
}

/* 尺寸变体 */
.cmg-filter-bar--small {
  padding: var(--cmg-space-3);
  gap: var(--cmg-space-3);
}

.cmg-filter-bar--large {
  padding: var(--cmg-space-6);
  gap: var(--cmg-space-6);
}

/* 布局变体 */
.cmg-filter-bar--vertical {
  flex-direction: column;
  align-items: stretch;
}

.cmg-filter-bar--grid .cmg-filter-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--cmg-space-3);
}

/* 内容区域 */
.cmg-filter-bar__content {
  flex: 1;
  min-width: 0;
}

.cmg-filter-form :deep(.el-form-item) {
  margin-right: var(--cmg-space-4);
  margin-bottom: var(--cmg-space-3);
}

.cmg-filter-bar--small .cmg-filter-form :deep(.el-form-item) {
  margin-right: var(--cmg-space-3);
  margin-bottom: var(--cmg-space-2);
}

.cmg-filter-bar--large .cmg-filter-form :deep(.el-form-item) {
  margin-right: var(--cmg-space-6);
  margin-bottom: var(--cmg-space-4);
}

.cmg-filter-bar--vertical .cmg-filter-form :deep(.el-form-item) {
  margin-right: 0;
}

/* 标签选择器 */
.cmg-tag-selector {
  display: flex;
  flex-wrap: wrap;
  gap: var(--cmg-space-2);
}

.cmg-tag-option {
  cursor: pointer;
  transition: var(--cmg-transition-all);
  display: flex;
  align-items: center;
  gap: var(--cmg-space-1);
}

.cmg-tag-option:hover {
  transform: translateY(-1px);
  box-shadow: var(--cmg-shadow-sm);
}

/* 自定义字段 */
.cmg-custom-field {
  display: flex;
  align-items: center;
}

/* 操作区域 */
.cmg-filter-bar__actions {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-3);
  flex-shrink: 0;
}

.cmg-filter-bar--vertical .cmg-filter-bar__actions {
  justify-content: flex-end;
  border-top: 1px solid var(--cmg-border-light);
  padding-top: var(--cmg-space-3);
  margin-top: var(--cmg-space-3);
}

.cmg-filter-bar__extra-actions {
  display: flex;
  align-items: center;
  gap: var(--cmg-space-2);
}

/* 选项自定义渲染 */
.cmg-option-custom {
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .cmg-filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .cmg-filter-form {
    flex-direction: column;
  }
  
  .cmg-filter-form :deep(.el-form-item) {
    margin-right: 0;
    width: 100%;
  }
  
  .cmg-filter-bar__actions {
    flex-direction: column;
    align-items: stretch;
    gap: var(--cmg-space-2);
  }
  
  .cmg-filter-bar__actions .el-button-group {
    width: 100%;
  }
  
  .cmg-filter-bar__actions .el-button {
    flex: 1;
  }
}

@media (max-width: 640px) {
  .cmg-filter-bar {
    padding: var(--cmg-space-3);
  }
  
  .cmg-tag-selector {
    gap: var(--cmg-space-1);
  }
  
  .cmg-tag-option {
    font-size: var(--cmg-text-xs);
  }
}

/* 暗色主题适配 */
[data-theme="dark"] .cmg-filter-bar {
  background: var(--cmg-bg-primary);
  border-color: var(--cmg-border-base);
}

[data-theme="dark"] .cmg-filter-bar:hover {
  border-color: var(--cmg-border-strong);
}

[data-theme="dark"] .cmg-filter-bar--vertical .cmg-filter-bar__actions {
  border-top-color: var(--cmg-border-base);
}
</style>