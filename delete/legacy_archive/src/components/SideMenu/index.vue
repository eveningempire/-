<template>
  <div class="side-menu-wrapper">
    <el-menu
      :default-active="activeMenu"
      class="el-menu-vertical"
      :collapse="isCollapse"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409EFF"
      :unique-opened="true"
      :router="true"
    >
      <!-- ...existing code... -->
    </el-menu>
  </div>
</template>

<script>
// ...existing code...
</script>

<style lang="scss" scoped>
.side-menu-wrapper {
  height: 100%;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
  border-right: 1px solid #eaeaea;
}

.el-menu-vertical {
  height: 100%;
  border-right: none;
}

.el-menu-vertical:not(.el-menu--collapse) {
  width: 200px;
}

.el-menu-item {
  &:hover {
    background-color: #263445 !important;
  }
  
  &.is-active {
    border-left: 4px solid #409EFF;
    background-color: #1f2d3d !important;
  }
}

.el-submenu__title {
  &:hover {
    background-color: #263445 !important;
  }
}

.menu-item-icon {
  margin-right: 10px;
  font-size: 18px;
  vertical-align: middle;
}

.menu-item-title {
  vertical-align: middle;
}
</style>
