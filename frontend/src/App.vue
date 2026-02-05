<template>
  <a-config-provider :theme="{ token: { colorPrimary: '#667eea' } }">
    <a-layout style="min-height: 100vh">
      <!-- 头部导航 -->
      <a-layout-header class="header">
        <div class="logo">
          <h1 style="color: white; margin: 0;">💰 OpenClaw 支出一览</h1>
        </div>
        <a-menu
          v-model:selectedKeys="selectedKeys"
          theme="dark"
          mode="horizontal"
          :items="menuItems"
          @click="handleMenuClick"
        />
      </a-layout-header>

      <!-- 内容区域 -->
      <a-layout-content style="padding: 24px;">
        <div class="content-wrapper">
          <router-view />
        </div>
      </a-layout-content>

      <!-- 底部 -->
      <a-layout-footer style="text-align: center; background: #f0f2f5;">
        OpenClaw Expenses Dashboard ©2024 Created by AI Assistant
      </a-layout-footer>
    </a-layout>
  </a-config-provider>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const selectedKeys = ref<string[]>(['dashboard'])

const menuItems = [
  {
    key: 'dashboard',
    label: '总览',
    icon: 'h',
  },
  {
    key: 'categories',
    label: '分类分析',
    icon: 'pie-chart',
  },
  {
    key: 'timeline',
    label: '时间线',
    icon: 'line-chart',
  },
  {
    key: 'payment',
    label: '支付方式',
    icon: 'credit-card',
  },
]

const handleMenuClick = ({ key }: { key: string }) => {
  router.push(`/${key}`)
  selectedKeys.value = [key]
}
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