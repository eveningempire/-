import Vue from 'vue'
// ...existing code...
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
// 导入自定义的 Element UI 样式覆盖
import '@/styles/element-ui-override.scss'
// ...existing code...

Vue.use(ElementUI)
// ...existing code...

new Vue({
  // ...existing code...
}).$mount('#app')
