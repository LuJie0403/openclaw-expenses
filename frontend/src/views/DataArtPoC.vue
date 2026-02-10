<template>
  <div v-if="loading" class="loading-container">
    <a-spin size="large" tip="正在召唤消费星尘..." />
  </div>
  <div v-else-if="error" class="error-container">
    <a-alert
      message="数据加载失败"
      :description="error"
      type="error"
      show-icon
    />
  </div>
  <div v-else ref="chartContainer" style="width: 100%; height: 80vh;"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import api from '../services/api'; // Import your api service
import { useAuthStore } from '@/stores/auth';

const chartContainer = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;
const loading = ref(true);
const error = ref<string | null>(null);
const authStore = useAuthStore();

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    error.value = "用户未认证，无法加载数据。";
    loading.value = false;
    return;
  }

  try {
    const response = await api.get('/expenses/stardust');
    const data = response.data;
    
    if (chartContainer.value) {
      chartInstance = echarts.init(chartContainer.value);

      const option = {
        backgroundColor: '#000',
        tooltip: {
          formatter: (params: any) => {
             if (params.dataType === 'node') {
               return `${params.name}: ${params.value.toFixed(2)}`;
             }
             return '';
          }
        },
        legend: [{
          data: data.categories.map((c: any) => c.trans_type_name),
          textStyle: { color: '#fff' }
        }],
        series: [
          {
            type: 'graph',
            layout: 'force',
            nodes: data.nodes,
            links: data.links,
            categories: data.categories.map((c: any) => ({ name: c.trans_type_name })),
            roam: true,
            label: {
              position: 'right',
              color: '#fff',
              show: false, // Initially hide labels for performance
            },
            force: {
              repulsion: 120,
              gravity: 0.05,
              edgeLength: [80, 200],
            },
            lineStyle: {
              color: 'source',
              curveness: 0.3,
              opacity: 0.2,
            },
            emphasis: {
              focus: 'adjacency',
              label: {
                show: true
              },
              lineStyle: {
                width: 10,
              },
            },
          },
        ],
      };
      
      chartInstance.setOption(option);
      loading.value = false;
    }
  } catch (err: any) {
    console.error("Failed to fetch stardust data:", err);
    error.value = err.message || "无法连接到服务器或处理数据时发生未知错误。";
    loading.value = false;
  }
});

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose();
  }
});
</script>

<style scoped>
.loading-container, .error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
}
</style>
