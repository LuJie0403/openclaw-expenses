import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import Categories from '@/views/Categories.vue'
import Timeline from '@/views/Timeline.vue'
import Payment from '@/views/Payment.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: Dashboard,
      meta: {
        title: '支出总览'
      }
    },
    {
      path: '/categories',
      name: 'categories',
      component: Categories,
      meta: {
        title: '分类分析'
      }
    },
    {
      path: '/timeline',
      name: 'timeline',
      component: Timeline,
      meta: {
        title: '时间线'
      }
    },
    {
      path: '/payment',
      name: 'payment',
      component: Payment,
      meta: {
        title: '支付方式'
      }
    }
  ]
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} - OpenClaw 支出一览`
  next()
})

export default router