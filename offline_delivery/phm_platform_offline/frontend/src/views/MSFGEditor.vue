<template>
  <div style="height: 100%; display: flex; flex-direction: column;">
    <div style="margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
      <h3>多信号流图配置界面</h3>
      <div style="display: flex; gap: 10px;">
        <el-button type="primary" size="small" @click="refreshIframe">刷新</el-button>
        <el-button type="info" size="small" @click="openInNewTab">新窗口打开</el-button>
      </div>
    </div>
    <iframe 
      ref="iframeRef"
      :src="iframeSrc" 
      style="flex: 1; width: 100%; border: 1px solid #e0e0e0; border-radius: 4px;" 
      frameborder="0"
      @load="onIframeLoad" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';

const iframeRef = ref(null);

function getBackendOrigin() {
  const hint = window.__BACKEND_ORIGIN__;
  if (typeof hint === 'string' && hint.startsWith('http')) return hint;
  const { protocol, hostname } = window.location;
  return `${protocol}//${hostname}:8000`;
}

const backendOrigin = getBackendOrigin();
const iframeSrc = computed(() => `${backendOrigin}/api/v1/msfg/editor/editor/`);

function refreshIframe() {
  if (iframeRef.value) {
    iframeRef.value.src = iframeRef.value.src;
    ElMessage.success('正在刷新编辑器...');
  }
}

function openInNewTab() {
  window.open(iframeSrc.value, '_blank');
}

function onIframeLoad() {
  console.log('MSFG编辑器加载完成');
}
</script>
