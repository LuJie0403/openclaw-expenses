<!-- Categories.vue -->
<template>
  <div class="categories-container">
    <a-card title="支出分类分析" class="main-card">
      <!-- Chart Section -->
      <div ref="categoryChartRef" style="height: 400px; width: 100%;"></div>
      <a-divider />
      <!-- Table Section -->
      <h3>分类详情</h3>
      <a-table :columns="categoryColumns" :data-source="expenseStore.categories" :pagination="{ pageSize: 10, showSizeChanger: true, pageSizeOptions: ['10', '20', '50'], showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items` }" row-key="trans_sub_type_name" size="middle">
        <template #bodyCell="{ column, record, index }">
          <template v-if="column.key === 'rowIndex'">{{ index + 1 }}</template>
          <template v-if="column.key === 'total_amount'"><span style="color: #ff4d4f;">¥{{ formatNumber(record.total_amount) }}</span></template>
          <template v-if="column.key === 'avg_amount'"><span style="color: #40a9ff;">¥{{ formatNumber(record.avg_amount) }}</span></template>
          <template v-if="column.key === 'percentage'"><span>{{ record.percentage.toFixed(2) }}%</span></template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>
<script setup lang="ts">
// ... (imports)
import { ref, onMounted, onUnmounted } from 'vue';
import { useExpenseStore } from '@/stores/expense';
import { Chart } from '@antv/g2';
import { formatNumber } from '@/utils/format';

const expenseStore = useExpenseStore();
const categoryChartRef = ref<HTMLElement>();

const categoryColumns = [
  { title: '#', key: 'rowIndex', width: 60, align: 'center' },
  { title: '主分类', dataIndex: 'trans_type_name', sorter: (a, b) => a.trans_type_name.localeCompare(b.trans_type_name) },
  { title: '子分类', dataIndex: 'trans_sub_type_name', sorter: (a, b) => a.trans_sub_type_name.localeCompare(b.trans_sub_type_name) },
  { title: '交易笔数', dataIndex: 'count', sorter: (a, b) => a.count - b.count, align: 'right' },
  { title: '总金额', dataIndex: 'total_amount', key: 'total_amount', sorter: (a, b) => a.total_amount - b.total_amount, defaultSortOrder: 'descend', align: 'right' },
  { title: '平均金额', dataIndex: 'avg_amount', key: 'avg_amount', sorter: (a, b) => a.avg_amount - b.avg_amount, align: 'right' },
  { title: '金额占比', dataIndex: 'percentage', key: 'percentage', sorter: (a, b) => a.percentage - b.percentage, align: 'right' },
];

let chart: Chart | null = null;
const initChart = () => {
  if (!categoryChartRef.value || !expenseStore.categories.length) return;
  chart = new Chart({ container: categoryChartRef.value, autoFit: true, height: 400 });
  chart.theme({ type: 'classicDark' });
  chart.data(expenseStore.categories.slice(0, 20));
  chart.interval().encode('x', 'trans_sub_type_name').encode('y', 'total_amount').encode('color', 'trans_type_name').axis('x', { label: { autoRotate: true } }).tooltip({ items: [{ name: '金额', channel: 'y', valueFormatter: (d) => `¥${formatNumber(d)}` }] });
  chart.render();
};

onMounted(async () => {
  if (!expenseStore.categories.length) await expenseStore.fetchCategories();
  initChart();
});

onUnmounted(() => chart?.destroy());
</script>
<style scoped>
.categories-container { padding: 20px; }
.main-card { background: rgba(25, 25, 25, 0.6); border: 1px solid #333; }
h3 { color: #fff; }
</style>
