import { createRouter, createWebHistory } from 'vue-router'

// 引入页面组件
import Index from '../views/index.vue'
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',            // 默认路由,进入项目就跳转到登录页
    name: 'Login',
    component: Index
  },
  {
    path: '/home',        // 主页面
    name: 'Home',
    component: Home
  }
]

const router = createRouter({
  history: createWebHistory(), // history 模式
  routes
})

export default router
