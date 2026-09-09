<template>
  <div class="app-container">
    <el-container class="main-container">
      <el-aside class="sidebar-container" :width="isCollapse ? '64px' : '200px'">
        <div class="logo-container">
          <img src="@/assets/logo.png" alt="Logo" class="logo-image" v-if="!isCollapse">
          <img src="@/assets/logo-small.png" alt="Logo" class="logo-small" v-else>
        </div>
        <side-menu :is-collapse="isCollapse"></side-menu>
      </el-aside>
      <el-container>
        <el-header class="main-header">
          <div class="header-left">
            <i 
              :class="[isCollapse ? 'el-icon-s-unfold' : 'el-icon-s-fold', 'collapse-btn']" 
              @click="toggleCollapse"
            ></i>
            <breadcrumb />
          </div>
          <div class="header-right">
            <!-- ...existing code... -->
          </div>
        </el-header>
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
// ...existing code...

export default {
  // ...existing code...
  methods: {
    // ...existing code...
    toggleCollapse() {
      this.isCollapse = !this.isCollapse;
    },
    // ...existing code...
  }
}
</script>

<style lang="scss" scoped>
.app-container {
  height: 100vh;
  overflow: hidden;
}

.main-container {
  height: 100%;
}

.sidebar-container {
  transition: width 0.3s;
  background-color: #304156;
  overflow: hidden;
}

.logo-container {
  height: 60px;
  padding: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #2b3649;
}

.logo-image {
  height: 40px;
  max-width: 180px;
}

.logo-small {
  height: 32px;
  width: 32px;
}

.main-header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px !important;
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  margin-right: 20px;
  color: #606266;
  
  &:hover {
    color: #409EFF;
  }
}

.header-right {
  display: flex;
  align-items: center;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

/* 针对滚动条的样式美化 */
.main-content::-webkit-scrollbar {
  width: 8px;
}

.main-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.main-content::-webkit-scrollbar-track {
  background: #f1f1f1;
}
</style>
