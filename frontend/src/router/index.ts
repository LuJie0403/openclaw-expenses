
import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '@/views/Dashboard.vue';
import Categories from '@/views/Categories.vue';
import Timeline from '@/views/Timeline.vue';
import Payment from '@/views/Payment.vue';
import Login from '@/views/Login.vue';
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login,
      meta: {
        title: '登录',
        guest: true
      }
    },
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: Dashboard,
      meta: {
        title: '支出总览',
        requiresAuth: true
      }
    },
    {
      path: '/categories',
      name: 'categories',
      component: Categories,
      meta: {
        title: '分类分析',
        requiresAuth: true
      }
    },
    {
      path: '/timeline',
      name: 'timeline',
      component: Timeline,
      meta: {
        title: '时间线',
        requiresAuth: true
      }
    },
    {
      path: '/payment',
      name: 'payment',
      component: Payment,
      meta: {
        title: '支付方式',
        requiresAuth: true
      }
    }
  ]
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  if (to.meta.title) {
    document.title = `${to.meta.title} - OpenClaw 支出一览`;
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login');
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/');
  } else {
    next();
  }
});

export default router;
// POC Route Added by 1024
