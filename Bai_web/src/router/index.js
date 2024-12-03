import Vue from 'vue';
import VueRouter from 'vue-router';
import RegisterView from '../views/RegisterView.vue';
import LoginView from '../views/LoginView.vue';
import HomeView from "../views/HomeView.vue";

Vue.use(VueRouter);

const routes = [
  { path: '/', redirect: '/register' },
  { path: '/register', component: RegisterView },
  { path: '/login', name: 'Login', component: LoginView },
  { path: '/home', name: 'Home', component: HomeView }
];

const router = new VueRouter({
  mode: 'history',
  routes
});

export default router;
