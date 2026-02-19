<template>
  <a-config-provider
    :locale="zhCN"
    :theme="themeConfig"
  >
    <!-- Login Layout -->
    <div v-if="isGuest" :style="guestLayoutWrapperStyle">
       <router-view />
       <footer style="text-align: center; background: transparent; color: #666; padding: 24px; margin-top: auto;">
         钱呢 (MoneyWhere) ©2026 Created by AI Assistant for <a href="https://github.com/LuJie0403" target="_blank">@Iter-1024</a>
       </footer>
    </div>

    <!-- Main Layout -->
    <a-layout v-else style="min-height: 100vh; background: #000;">
      <!-- Header -->
      <a-layout-header class="header" style="background: #141414; border-bottom: 1px solid #333;">
        <div class="logo">
          <div style="display: flex; align-items: center; gap: 12px;">
            <img src="/logo.svg" alt="Logo" style="height: 44px;" />
            <h1 style="color: #fff; margin: 0; font-family: 'Orbitron', sans-serif;">钱呢</h1>
          </div>
        </div>
        <a-menu
          v-model:selectedKeys="selectedKeys"
          theme="dark"
          mode="horizontal"
          :items="menuItems"
          @click="handleMenuClick"
          style="flex: 1; background: transparent; border-bottom: none;"
        />
        <div class="user-actions">
           <a-space>
             <span style="color: #fff;">{{ authStore.user?.full_name || authStore.user?.username }}</span>
             <a-button type="link" @click="handleLogout" style="color: #667eea;">退出登录</a-button>
           </a-space>
        </div>
      </a-layout-header>

      <!-- Content -->
      <a-layout-content style="padding: 24px; background: #000; position: relative; overflow: hidden;">
        <div class="stars-bg"></div>
        <div class="content-wrapper">
          <router-view />
        </div>
      </a-layout-content>

      <!-- Footer -->
      <a-layout-footer style="text-align: center; background: #000; color: #444; border-top: 1px solid #111;">
        钱呢 (MoneyWhere) ©2026 Created by AI Assistant for <a href="https://github.com/LuJie0403" target="_blank" style="color: #666">@Iter-1024</a>
      </a-layout-footer>
    </a-layout>
  </a-config-provider>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { theme } from 'ant-design-vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN';

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const selectedKeys = ref<string[]>(['dashboard'])

const isGuest = computed(() => route.meta.guest)

const themeConfig = computed(() => ({
  algorithm: isGuest.value ? theme.defaultAlgorithm : theme.darkAlgorithm,
  token: {
    colorPrimary: '#667eea',
    colorBgBase: isGuest.value ? '#f0f2f5' : '#000000',
  }
}))

const guestLayoutWrapperStyle = {
  minHeight: '100vh',
  display: 'flex',
  flexDirection: 'column',
  background: '#f0f2f5'
}

onMounted(() => {
  if (authStore.isAuthenticated) authStore.fetchUser()
})

const menuItems = computed(() => [
  { key: 'dashboard', label: '总览', title: '总览' },
  { key: 'stardust', label: '消费星辰', title: '消费星辰' },
  { key: 'categories', label: '分类分析', title: '分类分析' },
  { key: 'timeline', label: '时间洞察', title: '时间洞察' },
  { key: 'payment', label: '支付方式', title: '支付方式' },
])

const handleMenuClick = ({ key }: { key: string }) => router.push(`/${key}`)
const handleLogout = () => authStore.logout()

watch(() => route.name, (name) => {
  if (name && typeof name === 'string') selectedKeys.value = [name]
}, { immediate: true })
</script>

<style>
/* Global Styles */
body { background-color: #000 !important; color: #fff; }
.stars-bg { /* ... styles from before ... */ }
.ant-card { /* ... styles from before ... */ }
</style>

<style scoped>
.header { display: flex; align-items: center; padding: 0 24px; }
.logo { margin-right: 24px; }
.content-wrapper { max-width: 1400px; margin: 0 auto; padding: 0 20px; position: relative; z-index: 1; }
</style>
