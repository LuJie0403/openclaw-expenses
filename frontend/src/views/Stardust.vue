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
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import * as echarts from 'echarts';
import api from '../services/api'; 
import { useAuthStore } from '@/stores/auth';
import { formatAmount } from '@/utils/format';

type StardustNode = {
  id: string
  name: string
  value: number
  symbolSize: number
  category: number
  label?: unknown
  itemStyle?: unknown
}

type StardustLink = {
  source: string
  target: string
}

type StardustCategory = {
  name: string
}

type StardustGraphData = {
  nodes: StardustNode[]
  links: StardustLink[]
  categories: StardustCategory[]
}

const chartContainer = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;
const loading = ref(true);
const error = ref<string | null>(null);
const debugInfo = ref<string>('');
const stardustData = ref<StardustGraphData | null>(null)
const authStore = useAuthStore();
const onResize = () => {
  if (chartInstance && stardustData.value) {
    renderChart();
  } else if (chartInstance) {
    chartInstance.resize();
  }
};

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);
const splitEvenly = (items: string[], groups: number) => {
  if (!items.length) return [] as string[][];
  const normalizedGroups = Math.max(1, Math.min(groups, items.length));
  const base = Math.floor(items.length / normalizedGroups);
  const remainder = items.length % normalizedGroups;
  const chunks: string[][] = [];
  let cursor = 0;
  for (let i = 0; i < normalizedGroups; i++) {
    const size = base + (i < remainder ? 1 : 0);
    chunks.push(items.slice(cursor, cursor + size));
    cursor += size;
  }
  return chunks;
};

const normalizeStardustPayload = (payload: any): StardustGraphData => {
  const rawNodes = Array.isArray(payload?.nodes) ? payload.nodes : [];
  const rawLinks = Array.isArray(payload?.links) ? payload.links : [];
  const rawCategories = Array.isArray(payload?.categories) ? payload.categories : [];

  const normalizedNodes: StardustNode[] = rawNodes.map((node: any, index: number) => {
    const id = String(node?.id ?? node?.name ?? `node_${index}`);
    const value = Number(node?.value ?? 0);
    const symbolSize = clamp(Number(node?.symbolSize ?? 18), 8, 90);
    return {
      id,
      name: String(node?.name ?? id),
      value: Number.isFinite(value) ? value : 0,
      symbolSize: Number.isFinite(symbolSize) ? symbolSize : 18,
      category: Number.isFinite(Number(node?.category)) ? Number(node.category) : 0,
      label: node?.label,
      itemStyle: node?.itemStyle,
    };
  });

  const nodeById = new Map<string, StardustNode>();
  const nodeByName = new Map<string, StardustNode>();
  normalizedNodes.forEach((node) => {
    nodeById.set(node.id, node);
    nodeByName.set(node.name, node);
  });

  const normalizedLinks = rawLinks
    .map((link: any) => {
      const rawSource = String(link?.source ?? '');
      const rawTarget = String(link?.target ?? '');
      const sourceNode = nodeById.get(rawSource) ?? nodeByName.get(rawSource);
      const targetNode = nodeById.get(rawTarget) ?? nodeByName.get(rawTarget);
      if (!sourceNode || !targetNode) {
        return null;
      }
      return { source: sourceNode.id, target: targetNode.id };
    })
    .filter(Boolean) as Array<{ source: string; target: string }>;

  if (!normalizedLinks.length && normalizedNodes.length > 1) {
    const rootNode = normalizedNodes[0]
    normalizedNodes.slice(1).forEach((node) => {
      normalizedLinks.push({ source: rootNode.id, target: node.id });
    });
  }

  const maxCategoryIndex = normalizedNodes.reduce((max: number, node: StardustNode) => Math.max(max, Number(node.category || 0)), 0)
  const normalizedCategories: StardustCategory[] = rawCategories.map((item: any, index: number) => ({
    name: String(item?.name ?? `分组${index + 1}`),
  }));
  while (normalizedCategories.length <= maxCategoryIndex) {
    normalizedCategories.push({ name: `分组${normalizedCategories.length + 1}` });
  }

  return {
    nodes: normalizedNodes,
    links: normalizedLinks,
    categories: normalizedCategories,
  };
};

const renderChart = () => {
  if (!chartContainer.value || !stardustData.value) return

  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  chartInstance = echarts.init(chartContainer.value)
  const data = stardustData.value
  const categoryNames = data.categories.map((c) => String(c.name ?? '未分类'));
  const containerWidth = chartContainer.value.clientWidth || window.innerWidth || 1200;
  const maxItemsPerRow = containerWidth >= 1400 ? 7 : containerWidth >= 1200 ? 6 : containerWidth >= 900 ? 5 : containerWidth >= 700 ? 4 : 3;
  const rowCount = Math.max(1, Math.ceil(categoryNames.length / maxItemsPerRow));
  const legendRows = splitEvenly(categoryNames, rowCount);
  const legendRowHeight = 28;
  const legendBottomPadding = 8;
  const legendBlockHeight = legendRows.length * legendRowHeight;
  const graphBottomPadding = legendBottomPadding + legendBlockHeight + 8;

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      formatter: (params: any) =>
        params.dataType === 'node' ? `${params.name}: ¥${formatAmount(Number(params.value || 0))}` : '',
    },
    legend: legendRows.map((row, index) => ({
      type: 'plain',
      orient: 'horizontal',
      bottom: legendBottomPadding + (legendRows.length - 1 - index) * legendRowHeight,
      left: 'center',
      icon: 'circle',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 14,
      selectedMode: true,
      data: row,
      textStyle: { color: '#fff' },
    })),
    series: [{
        type: 'graph',
        layout: 'force',
        data: data.nodes,
        links: data.links,
        categories: data.categories,
        top: 8,
        bottom: graphBottomPadding,
        roam: true,
        label: { position: 'right', color: '#fff', show: false },
        force: { repulsion: 150, gravity: 0.1, edgeLength: [100, 250], layoutAnimation: false },
        lineStyle: { color: 'source', curveness: 0.3, opacity: 0.2 },
        emphasis: { focus: 'adjacency', label: { show: true }, lineStyle: { width: 10 } },
    }],
  }

  chartInstance.setOption(option)
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    error.value = "用户未认证，无法加载数据。";
    loading.value = false;
    return;
  }

  let data: any = null;
  try {
    const response = await api.get('/expenses/stardust');
    data = normalizeStardustPayload(response.data);
    debugInfo.value = JSON.stringify({
      nodeCount: data.nodes.length,
      linkCount: data.links.length,
      categoryCount: data.categories.length,
      previewNode: data.nodes[0] ?? null,
    }, null, 2);

    if (!data || !data.nodes || !data.links || !data.categories) {
        throw new Error("返回数据格式错误: 缺少 nodes/links/categories");
    }
    if (data.nodes.length === 0) {
        throw new Error("返回数据为空 (nodes length is 0)");
    }

    stardustData.value = data
  } catch (err: any) {
    console.error("Stardust Error:", err);
    error.value = `渲染失败: ${err.message}`;
  } finally {
    loading.value = false;
  }

  if (!error.value && stardustData.value) {
    await nextTick()
    renderChart()
    window.addEventListener('resize', onResize)
  }
});

onUnmounted(() => {
  window.removeEventListener('resize', onResize);
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
