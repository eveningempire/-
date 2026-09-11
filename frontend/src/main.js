import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import App from './App.vue';
import router from './router';
import axios from 'axios';

// 每次重新打开前端都要求重新登录；登录成功后仅在当前页面会话中有效。
sessionStorage.removeItem('user');

// 引入统一设计系统样式
import './styles/design-tokens.css';
import './styles/global.css';

// 全局组件注册
import SectionCard from './components/SectionCard.vue';
import ThemeToggle from './components/ThemeToggle.vue';
import RealtimeIndicator from './components/RealtimeIndicator.vue';
import TableDensityToggle from './components/TableDensityToggle.vue';
import EmptyState from './components/EmptyState.vue';
import FilterBar from './components/FilterBar.vue';

// 图表主题初始化
import { initChartTheme } from './utils/chartTheme.js';

// Create the Vue application instance. Register the router and ElementPlus
// component library. Attach axios to the global properties so that it can
// easily be accessed in components via this.$axios.

const app = createApp(App);
app.use(ElementPlus);
app.use(router);

// 全局组件注册
app.component('SectionCard', SectionCard);
app.component('ThemeToggle', ThemeToggle);
app.component('RealtimeIndicator', RealtimeIndicator);
app.component('TableDensityToggle', TableDensityToggle);
app.component('EmptyState', EmptyState);
app.component('FilterBar', FilterBar);

// 初始化图表主题
initChartTheme();

app.config.globalProperties.$axios = axios;
app.mount('#app');
