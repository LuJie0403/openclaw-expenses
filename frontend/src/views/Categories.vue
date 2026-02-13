<template>
  <div class="categories-container">
    <a-card title="支出分类分析" class="main-card">
      <div class="chart-section">
        <div ref="categoryChartRef" class="chart-container"></div>
      </div>
      
      <a-divider />
      
      <div class="category-list">
        <h3>分类详情</h3>
        <a-table
          :columns="columns"
          :data-source="expenseStore.categories"
          :pagination="{ pageSize: 10 }"
          row-key="trans_sub_type_name"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'total_amount'">
              <span class="amount-text">¥{{ formatNumber(record.total_amount) }}</span>
            </template>
            <template v-if="column.key === 'avg_amount'">
              <span class="avg-text">¥{{ formatNumber(record.avg_amount) }}</span>
            </template>
          </template>
        </a-table>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useExpenseStore } from '@/stores/expense'
import { Chart } from '@antv/g2'
import { formatNumber } from '@/utils/format'

const expenseStore = useExpenseStore()
const categoryChartRef = ref<HTMLElement>()

const columns = [
  {
    title: '主分类',
    dataIndex: 'trans_type_name',
    key: 'trans_type_name',
    width: 120,
  },
  {
    title: '子分类',
    dataIndex: 'trans_sub_type_name',
    key: 'trans_sub_type_name',
  },
  {
    title: '交易笔数',
    dataIndex: 'count',
    key: 'count',
    align: 'center',
    width: 100,
  },
  {
    title: '总金额',
    dataIndex: 'total_amount',
    key: 'total_amount',
    align: 'right',
    width: 120,
  },
  {
    title: '平均金额',
    dataIndex: 'avg_amount',
    key: 'avg_amount',
    align: 'right',
    width: 120,
  },
]

let categoryChart: Chart | null = null

const initChart = () => {
  if (!categoryChartRef.value || !expenseStore.categories.length) return

  categoryChart = new Chart({
    container: categoryChartRef.value,
    autoFit: true,
    height: 400,
  })
  
  categoryChart.theme({ type: 'classicDark' });

  const data = expenseStore.categories.slice(0, 15)

  categoryChart
    .interval()
    .data(data)
    .encode('x', 'trans_sub_type_name')
    .encode('y', 'total_amount')
    .encode('color', 'trans_type_name')
    .scale('y', { nice: true })
    .axis('x', { 
      title: '消费类别',
      label: { autoRotate: true, autoHide: true }
    })
    .axis('y', { 
      title: '支出金额 (¥)',
      labelFormatter: (value: number) => `¥${(value / 1000).toFixed(0)}K`
    })
    .tooltip({
      items: [
        { name: '类别', field: 'trans_sub_type_name' },
        { name: '金额', field: 'total_amount', valueFormatter: (value: number) => `¥${formatNumber(value)}` },
        { name: '笔数', field: 'count' }
      ]
    })
    .legend({ position: 'top' })
    .animate({ enter: { type: 'scaleInY' } })

  categoryChart.render()
}

onMounted(async () => {
  if (!expenseStore.categories.length) {
    await expenseStore.fetchCategories()
  }
  
  setTimeout(initChart, 100)
})

onUnmounted(() => {
  categoryChart?.destroy()
})
</script>

<style scoped>
.categories-container {
  padding: 20px;
  min-height: calc(100vh - 64px);
  /* background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); REMOVED */
}

.main-card {
  background: rgba(25, 25, 25, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid #333;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.chart-section {
  margin-bottom: 24px;
}

.chart-container {
  height: 400px;
  width: 100%;
}

.category-list {
  margin-top: 24px;
}

.category-list h3 {
  color: #fff;
}

.amount-text {
  font-weight: 600;
  color: #ff4d4f; /* Brighter red for dark mode */
}

.avg-text {
  color: #40a9ff; /* Brighter blue for dark mode */
}

@media (max-width: 768px) {
  .categories-container {
    padding: 12px;
  }
  
  .chart-container {
    height: 300px;
  }
}
</style>