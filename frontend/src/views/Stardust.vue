<template>
  <div v-if="loading" class="loading-container">
    <a-spin size="large" tip="正在召唤消费星尘..." />
  </div>
  <div v-else-if="error" class="error-container">
    <a-alert
      message="数据加载失败或图表渲染错误"
      :description="error"
      type="error"
      show-icon
    />
    <div style="margin-top: 20px; color: #fff; text-align: left; max-width: 800px; max-height: 400px; overflow: auto; background: #333; padding: 10px; border-radius: 8px;">
        <h4>原始数据 (前1000字符):</h4>
        <pre>{{ debugInfo }}</pre>
    </div>
  </div>
  <div v-else ref="chartContainer" style="width: 100%; height: 80vh;"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import api from '../services/api'; 
import { useAuthStore } from '@/stores/auth';

const chartContainer = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;
const loading = ref(true);
const error = ref<string | null>(null);
const debugInfo = ref<string>('');
const authStore = useAuthStore();

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    error.value = "用户未认证，无法加载数据。";
    loading.value = false;
    return;
  }

  let data: any = null;
  try {
    const response = await api.get('/expenses/stardust');
    data = response.data;
    debugInfo.value = JSON.stringify(data, null, 2).substring(0, 1000) + '...';

    if (!data || !data.nodes || !data.links || !data.categories) {
        throw new Error("返回数据格式错误: 缺少 nodes/links/categories");
    }
    if (data.nodes.length === 0) {
        throw new Error("返回数据为空 (nodes length is 0)");
    }

    if (chartContainer.value) {
      chartInstance = echarts.init(chartContainer.value);
      
      const option = {
        backgroundColor: 'transparent',
        tooltip: { formatter: (params: any) => (params.dataType === 'node' ? `${params.name}: ${params.value.toFixed(2)}` : '') },
        legend: [{ data: data.categories.map((c: any) => c.name), textStyle: { color: '#fff' } }],
        series: [{
            type: 'graph',
            layout: 'force',
            nodes: data.nodes,
            links: data.links,
            categories: data.categories,
            roam: true,
            label: { position: 'right', color: '#fff', show: false },
            force: { repulsion: 150, gravity: 0.1, edgeLength: [100, 250], layoutAnimation: false },
            lineStyle: { color: 'source', curveness: 0.3, opacity: 0.2 },
            emphasis: { focus: 'adjacency', label: { show: true }, lineStyle: { width: 10 } },
        }],
      };
      
      chartInstance.setOption(option);
    }
  } catch (err: any) {
    console.error("Stardust Error:", err);
    error.value = `渲染失败: ${err.message}`;
  } finally {
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
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 80vh;
  text-align: center;
}
</style>