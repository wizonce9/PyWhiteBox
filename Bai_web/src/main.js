import Vue from 'vue';
import App from './App.vue';
import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';
import router from './router'; // 引入路由

Vue.config.productionTip = false;
Vue.use(ElementUI);

new Vue({
  router, // 将路由注入到 Vue 实例中
  render: h => h(App),
}).$mount('#app');
