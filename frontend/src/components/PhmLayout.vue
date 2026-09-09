<template>
  <el-container class="phm-shell">
    <el-aside width="272px" class="phm-sidebar">
      <div class="brand">
        <div class="brand-mark">PHM</div>
        <div><strong>航天器健康管理</strong><small>Spacecraft PHM Platform</small></div>
      </div>
      <el-menu :default-active="$route.path" router class="nav" background-color="transparent" text-color="#a9bad3" active-text-color="#fff">
        <el-menu-item index="/"><el-icon><Monitor /></el-icon><span>综合态势</span></el-menu-item>
        <el-sub-menu index="monitor">
          <template #title><el-icon><DataLine /></el-icon><span>状态监测</span></template>
          <el-menu-item index="/telemetry">遥测数据监测</el-menu-item>
          <el-menu-item index="/alarms">异常告警管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="diagnosis">
          <template #title><el-icon><Aim /></el-icon><span>故障诊断</span></template>
          <el-menu-item index="/fault-diagnosis">故障诊断分析</el-menu-item>
          <el-menu-item index="/msfg-editor">结构/MSFG模型</el-menu-item>
          <el-menu-item index="/fault-injection">故障注入配置</el-menu-item>
          <el-menu-item index="/simulation-dataset">仿真数据集</el-menu-item>
          <el-menu-item index="/fmeca">FMECA知识库</el-menu-item>
          <el-menu-item index="/fta">FTA故障树</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="assessment">
          <template #title><el-icon><TrendCharts /></el-icon><span>健康评估</span></template>
          <el-menu-item index="/health-assessment">部件健康指数</el-menu-item>
          <el-menu-item index="/system-health">系统健康状态</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="prediction">
          <template #title><el-icon><Timer /></el-icon><span>寿命预测</span></template>
          <el-menu-item index="/lifetime-prediction">剩余寿命预测</el-menu-item>
          <el-menu-item index="/model-management">预测模型管理</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/data-management"><el-icon><FolderOpened /></el-icon><span>数据管理</span></el-menu-item>
        <el-menu-item index="/vehicle-structure"><el-icon><Share /></el-icon><span>航天器结构管理</span></el-menu-item>
        <el-menu-item index="/maintenance-decision"><el-icon><Tools /></el-icon><span>维修辅助决策</span></el-menu-item>
        <el-menu-item index="/integration-assets"><el-icon><Box /></el-icon><span>整合资产中心</span></el-menu-item>
        <el-menu-item index="/users"><el-icon><User /></el-icon><span>用户与权限</span></el-menu-item>
      </el-menu>
      <div class="sidebar-status"><span class="pulse"></span><div>平台服务正常<small>骨架环境 · 数据未接入</small></div></div>
    </el-aside>
    <el-container>
      <el-header class="topbar">
        <div><h1>可重复使用航天器故障预测与健康管理平台</h1><p>状态监测 · 故障诊断 · 健康评估 · 寿命预测</p></div>
        <div class="top-actions"><el-tag type="warning" effect="plain">框架阶段</el-tag><span class="clock">{{ now }}</span><el-avatar :size="34">管</el-avatar></div>
      </el-header>
      <el-main class="content"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { Monitor, DataLine, Aim, TrendCharts, Timer, FolderOpened, Share, User, Tools, Box } from '@element-plus/icons-vue';
const now = ref(''); let timer;
const tick = () => { now.value = new Date().toLocaleString('zh-CN', { hour12: false }); };
onMounted(() => { tick(); timer = setInterval(tick, 1000); });
onUnmounted(() => clearInterval(timer));
</script>

<style scoped>
.phm-shell{height:100vh;background:#f2f5fa;color:#19283d}.phm-sidebar{background:linear-gradient(180deg,#0d203a,#102b4c);box-shadow:4px 0 18px #0a1d3324;display:flex;flex-direction:column}.brand{height:78px;display:flex;align-items:center;gap:12px;padding:0 20px;color:#fff;border-bottom:1px solid #ffffff16}.brand-mark{width:48px;height:48px;border-radius:12px;background:linear-gradient(135deg,#2e8cff,#20c7be);display:grid;place-items:center;font-weight:800;font-size:15px;box-shadow:0 8px 20px #168fd64d}.brand strong{display:block;font-size:16px}.brand small,.sidebar-status small{display:block;color:#8198b7;font-size:11px;margin-top:4px}.nav{border:0;flex:1;padding:12px 8px}.nav :deep(.el-menu-item),.nav :deep(.el-sub-menu__title){border-radius:7px;margin:3px 0}.nav :deep(.el-menu-item.is-active){background:linear-gradient(90deg,#237ee8,#1ba8b2);box-shadow:0 5px 14px #087bc34a}.sidebar-status{margin:16px;padding:13px;border:1px solid #ffffff18;background:#ffffff08;border-radius:9px;color:#dbe7f6;font-size:13px;display:flex;gap:10px;align-items:center}.pulse{width:9px;height:9px;background:#21d49b;border-radius:50%;box-shadow:0 0 0 5px #21d49b20}.topbar{height:78px;background:#fff;border-bottom:1px solid #e3e9f1;display:flex;align-items:center;justify-content:space-between;padding:0 28px}.topbar h1{font-size:20px;margin:0;color:#172a43}.topbar p{margin:6px 0 0;color:#8090a5;font-size:12px;letter-spacing:1px}.top-actions{display:flex;align-items:center;gap:18px}.clock{font-variant-numeric:tabular-nums;color:#5e7087;font-size:13px}.content{padding:24px;overflow:auto}
</style>
