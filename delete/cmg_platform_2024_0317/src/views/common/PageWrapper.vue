<template>
  <div class="page-wrapper">
    <div class="page-header" v-if="title">
      <h2 class="page-title">{{ title }}</h2>
      <div class="page-toolbar">
        <slot name="toolbar"></slot>
      </div>
    </div>
    <div class="page-content">
      <slot></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PageWrapper',
  props: {
    title: {
      type: String,
      default: ''
    }
  }
}
</script>

<style lang="scss" scoped>
.page-wrapper {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  margin-bottom: 24px;
  padding: 0;
  
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    border-bottom: 1px solid #f0f0f0;
    
    .page-title {
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }
    
    .page-toolbar {
      display: flex;
      align-items: center;
    }
  }
  
  .page-content {
    padding: 24px;
  }
}
</style>
