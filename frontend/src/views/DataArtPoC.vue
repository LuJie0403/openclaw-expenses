<template>
  <div ref="chartContainer" style="width: 100%; height: 80vh;"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import * as echarts from 'echarts';

const chartContainer = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

// --- Mock Data Generation ---
const categories = [
  { name: '餐饮美食', value: 3500 },
  { name: '购物消费', value: 2800 },
  { name: '交通出行', value: 1200 },
  { name: '生活服务', value: 1500 },
  { name: '娱乐活动', value: 800 },
];

const generateStardust = (category: { name: string, value: number }, count: number) => {
  const stardusts = [];
  for (let i = 0; i < count; i++) {
    stardusts.push({
      name: `消费${i + 1}`,
      value: Math.random() * (category.value / (count / 2)),
      category: category.name,
    });
  }
  return stardusts;
};

const mockData = categories.flatMap(cat => generateStardust(cat, Math.floor(Math.random() * 20) + 10));
// --- End Mock Data ---


onMounted(() => {
  if (chartContainer.value) {
    chartInstance = echarts.init(chartContainer.value);

    const nodes = [
      ...categories.map(c => ({
        id: c.name,
        name: c.name,
        symbolSize: Math.log(c.value) * 10,
        value: c.value,
        category: c.name,
        itemStyle: {
          opacity: 0.9,
        },
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold',
        },
      })),
      ...mockData.map((d, i) => ({
        id: `stardust-${i}`,
        name: d.name,
        symbolSize: Math.log(d.value + 1) * 3,
        value: d.value,
        category: d.category,
        itemStyle: {
          opacity: 0.7,
        },
      })),
    ];

    const links = mockData.map((d, i) => ({
      source: `stardust-${i}`,
      target: d.category,
    }));

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
        data: categories.map(c => c.name),
        textStyle: { color: '#fff' }
      }],
      series: [
        {
          type: 'graph',
          layout: 'force',
          nodes: nodes,
          links: links,
          categories: categories.map(c => ({ name: c.name })),
          roam: true,
          label: {
            position: 'right',
            color: '#fff',
          },
          force: {
            repulsion: 100,
            gravity: 0.03,
            edgeLength: [50, 150],
          },
          lineStyle: {
            color: 'source',
            curveness: 0.3,
            opacity: 0.2,
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 10,
            },
          },
        },
      ],
    };
    
    chartInstance.setOption(option);
  }
});

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose();
  }
});
</script>
