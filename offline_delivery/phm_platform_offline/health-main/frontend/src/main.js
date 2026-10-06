import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import DataVVue3 from '@kjgl77/datav-vue3'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn' // Correct import path
import 'element-plus/dist/index.css'
import * as echarts from 'echarts'
//import './assets/style.css'

const app = createApp(App)
app.use(router)
app.config.globalProperties.$echarts = echarts;
app.use(DataVVue3)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')