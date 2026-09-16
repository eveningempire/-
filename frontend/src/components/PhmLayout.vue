<template>
  <el-container class="shell">
    <el-aside width="250px" class="side">
      <div class="brand"><b>PHM</b><span>重复使用运载器健康管理平台</span></div>
      <el-menu router :default-active="$route.path" class="nav">
        <el-menu-item index="/"><el-icon><Monitor /></el-icon>综合态势</el-menu-item>
        <el-sub-menu index="monitor"><template #title><el-icon><DataLine /></el-icon>状态监测</template><el-menu-item index="/telemetry">遥测数据监测</el-menu-item><el-menu-item index="/alarms">异常告警中心</el-menu-item></el-sub-menu>
        <el-sub-menu index="simulation"><template #title><el-icon><DataLine /></el-icon>仿真及故障注入</template><el-menu-item index="/simulation-demo">离线故障数据集</el-menu-item><el-menu-item index="/realtime-fault-injection">实时故障注入</el-menu-item><el-menu-item index="/fault-replay">故障事件重演</el-menu-item></el-sub-menu><el-sub-menu index="diagnosis"><template #title><el-icon><Aim /></el-icon>故障诊断</template><el-menu-item index="/fault-diagnosis">诊断分析</el-menu-item></el-sub-menu>
        <el-sub-menu index="assessment"><template #title><el-icon><TrendCharts /></el-icon>健康与放行评估</template><el-menu-item index="/platform-health">部件/系统健康评估</el-menu-item><el-menu-item index="/lifetime-prediction">寿命预测</el-menu-item><el-menu-item index="/release-assessment">再飞与放行评估</el-menu-item></el-sub-menu>
        <el-sub-menu index="assets"><template #title><el-icon><Box /></el-icon>模型与可视化</template><el-menu-item index="/model-registry">模型管理</el-menu-item><el-menu-item index="/model-3d">三维部件定位</el-menu-item></el-sub-menu>
        <el-sub-menu index="structure-knowledge"><template #title><el-icon><Share /></el-icon>结构与知识</template><el-menu-item index="/vehicle-structure">运载器PBS结构树</el-menu-item><el-menu-item index="/fta">FTA故障树</el-menu-item><el-menu-item index="/fmeca">FMECA</el-menu-item></el-sub-menu>
        <el-menu-item index="/data-management"><el-icon><FolderOpened /></el-icon>数据管理</el-menu-item><el-menu-item index="/users"><el-icon><User /></el-icon>用户与权限</el-menu-item>
      </el-menu>
      <div class="online">● 平台服务正常</div>
    </el-aside>
    <el-container>
      <el-header class="header"><div><h1>重复使用运载器健康管理平台</h1><p>状态监测 · 故障诊断 · 健康评估 · 寿命预测</p></div><div class="actions"><el-tag type="success">演示环境</el-tag><span>{{ now }}</span><el-button size="small" type="danger" plain @click="logout">退出登录</el-button></div></el-header>
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>
<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Monitor, DataLine, Aim, TrendCharts, Timer, FolderOpened, Share, User, Box } from '@element-plus/icons-vue'
const router = useRouter(), now = ref(''); let timer
const tick = () => { now.value = new Date().toLocaleString('zh-CN', { hour12: false }) }
onMounted(() => { tick(); timer = setInterval(tick, 1000) }); onUnmounted(() => clearInterval(timer))
async function logout() { await fetch('/api/v1/auth/logout/', { method: 'POST', credentials: 'include' }); sessionStorage.removeItem('user'); router.replace('/login') }
</script>
<style scoped>.shell{height:100vh;background:#f3f6fa}.side{background:#102945;color:#fff;display:flex;flex-direction:column}.brand{height:76px;display:flex;align-items:center;gap:12px;padding:0 20px;border-bottom:1px solid #ffffff20}.brand b{background:#2189e8;padding:13px;border-radius:8px}.brand span{flex:1;font-size:14px;line-height:1.35}.nav{border:0;flex:1;background:transparent}.nav :deep(.el-menu-item),.nav :deep(.el-sub-menu__title){color:#c5d4e8}.nav :deep(.el-menu-item.is-active){background:#2189e8;color:white}.online{margin:16px;padding:12px;color:#9fe4c5;border:1px solid #ffffff25;border-radius:6px}.header{height:78px;background:white;border-bottom:1px solid #e1e7ef;display:flex;justify-content:space-between;align-items:center;padding:0 26px}.header h1{font-size:20px;margin:0;color:#162b45}.header p{margin:6px 0 0;color:#718198;font-size:12px}.actions{display:flex;align-items:center;gap:16px;color:#60728a;font-size:13px}.main{overflow:auto;padding:24px}</style>


