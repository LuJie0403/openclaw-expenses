
<template>
  <a-config-provider :theme="{ token: { colorPrimary: '#667eea' } }">
    <!-- Login Layout -->
    <div v-if="route.meta.guest" style="min-height: 100vh; display: flex; flex-direction: column;">
       <router-view />
       <!-- 底部 -->
       <footer style="text-align: center; background: #f0f2f5; padding: 24px; margin-top: auto;">
         Expenses Dashboard ©2026 Created by AI Assistant for <a href="https://github.com/LuJie0403" target="_blank">@Iter-1024</a>
       </footer>
    </div>

    <!-- Main Layout -->
    <a-layout v-else style="min-height: 100vh">
      <!-- 头部导航 -->
      <a-layout-header class="header">
        <div class="logo">
          <h1 style="color: white; margin: 0;">💰 支出面板</h1>
        </div>
        <a-menu
          v-model:selectedKeys="selectedKeys"
          theme="dark"
          mode="horizontal"
          :items="menuItems"
          @click="handleMenuClick"
          style="flex: 1;"
        />
        <div class="user-actions">
           <a-space>
             <span style="color: white;">你好, {{ authStore.user?.full_name || authStore.user?.username }}</span>
             <a-button type="link" @click="handleLogout" style="color: white;">退出登录</a-button>
           </a-space>
        </div>
      </a-layout-header>

      <!-- 内容区域 -->
      <a-layout-content style="padding: 24px;">
        <div class="content-wrapper">
          <router-view />
        </div>
      </a-layout-content>

      <!-- 底部 -->
      <a-layout-footer style="text-align: center; background: #f0f2f5;">
        Expenses Dashboard ©2026 Created by AI Assistant for <a href="https://github.com/LuJie0403" target="_blank">@Iter-1024</a>
      </a-layout-footer>
    </a-layout>
  </a-config-provider>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const selectedKeys = ref<string[]>(['dashboard'])

// Fetch user info on component mount if authenticated
onMounted(() => {
  if (authStore.isAuthenticated) {
    authStore.fetchUser()
  }
})

const menuItems = computed(() => [
  {
    key: 'dashboard',
    label: '总览',
    title: '总览',
  },
  {
    key: 'categories',
    label: '分类分析',
    title: '分类分析',
  },
  {
    key: 'timeline',
    label: '时间线',
    title: '时间线',
  },
  {
    key: 'payment',
    label: '支付方式',
    title: '支付方式',
  },
])

const handleMenuClick = ({ key }: { key: string }) => {
  router.push(`/${key}`)
  selectedKeys.value = [key]
}

const handleLogout = () => {
  authStore.logout()
}

// Sync menu with route
watch(
  () => route.name,
  (name) => {
    if (name && typeof name === 'string') {
       selectedKeys.value = [name]
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  padding: 0 24px;
}

.logo {
  margin-right: 24px;
}

.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

@media (max-width: 768px) {
  .content-wrapper {
    padding: 0 10px;
  }
}
</style>
