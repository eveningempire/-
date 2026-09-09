<template>
  <div style="height: 100%; display: flex; flex-direction: column;">
    <div style="margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
      <h3>规则编辑器</h3>
    </div>
    <iframe :src="iframeSrc" style="flex: 1; width: 100%; border: 1px solid #e0e0e0;" />
  </div>
</template>

<script setup>
import { computed } from 'vue';

function getBackendOrigin() {
  const hint = window.__BACKEND_ORIGIN__;
  if (typeof hint === 'string' && hint.startsWith('http')) return hint;
  const { protocol, hostname } = window.location;
  // 统一指向后端 8000 端口
  return `${protocol}//${hostname}:8000`;
}

const backendOrigin = getBackendOrigin();
const iframeSrc = computed(() => `${backendOrigin}/api/v1/rules/editor/editor/`);
</script>
