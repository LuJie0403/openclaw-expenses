<template>
  <div class="timeline-container">
    <a-card title="支出时间线分析" class="main-card">
      <div class="chart-controls">
        <a-space>
          <span>时间范围：</span>
          <a-range-picker
            v-model:value="dateRange"
            :placeholder="['开始日期', '结束日期']"
            format="YYYY-MM-DD"
            @change="handleDateChange"
          />
          <a-button type="primary" @click="refreshData">刷新数据</a-button>
        </a-space>
      </div>
      
      <div class="chart-section">
        <div ref="timelineChartRef" class="chart-container"></div>
      </div>
      
      <a-divider />
      
      <div class="stats-grid">
        <a-row :gutter="16">
          <a-col :xs="24" :sm="12" :lg="6">
            <div class="stat-item">
              <div class="stat-value">{{ maxDailyExpense }}</div>
              <div class="stat-label">最高日支出</div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <div class="stat-item">
              <div class="stat-value">{{ avgDailyExpense }}</div>
              <div class="stat-label">平均日支出</div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <div class="stat-item">
              <div class="stat-value">{{ maxTransactionDay }}</div>
              <div class="stat-label">最多交易天数</div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :lg="6">
            <div class="stat-item">
              <div class="stat-value">{{ totalDays }}</div>
              <div class="stat-label">统计天数</div>
            </div>
          </a-col>
        </a-row>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useExpenseStore } from '@/stores/expense'
import { Chart } from '@antv/g2'
import { formatAmount, formatDate } from '@/utils/format'
import dayjs from 'dayjs'

const expenseStore = useExpenseStore()
const timelineChartRef = ref<HTMLElement>()
const dateRange = ref<[dayjs.Dayjs, dayjs.Dayjs]>()

let timelineChart: Chart | null = null

// 计算属性
const maxDailyExpense = computed(() => {
  if (!expenseStore.timeline.length) return '¥0.00'
  const max = Math.max(...expenseStore.timeline.map(item => item.daily_total))
  return `¥${formatAmount(max)}`
})

const avgDailyExpense = computed(() => {
  if (!expenseStore.timeline.length) return '¥0.00'
  const avg = expenseStore.timeline.reduce((sum, item) => sum + item.daily_total, 0) / expenseStore.timeline.length
  return `¥${formatAmount(avg)}`
})

const maxTransactionDay = computed(() => {
  if (!expenseStore.timeline.length) return '0'
  const max = Math.max(...expenseStore.timeline.map(item => item.transaction_count))
  return `${max}笔`
})

const totalDays = computed(() => {
  return `${expenseStore.timeline.length}天`
})

// 初始化日期范围
const initDateRange = () => {
  const end = dayjs()
  const start = end.subtract(90, 'day')
  dateRange.value = [start, end]
}

// 初始化时间线图表
const initTimelineChart = () => {
  if (!timelineChartRef.value || !expenseStore.timeline.length) return

  const data = expenseStore.timeline

  timelineChart = new Chart({
    container: timelineChartRef.value,
    autoFit: true,
    height: 400,
  })
  
  timelineChart.theme({ type: 'classicDark' });

  timelineChart
    .line()
    .data(data)
    .encode('x', 'date')
    .encode('y', 'daily_total')
    .encode('color', '#667eea')
    .scale('x', { type: 'time' })
    .scale('y', { nice: true })
    .axis('x', { 
      title: '日期',
      labelFormatter: (value: string) => dayjs(value).format('MM-DD')
    })
    .axis('y', { 
      title: '日支出金额（元）',
      labelFormatter: (value: number) => `¥${formatAmount(value)}`
    })
    .tooltip({
      items: [
        { name: '日期', field: 'date', valueFormatter: (value: string) => formatDate(value) },
        { name: '支出金额', field: 'daily_total', valueFormatter: (value: number) => `¥${formatAmount(value)}` },
        { name: '交易笔数', field: 'transaction_count' }
      ]
    })
    .animate({ enter: { type: 'fadeIn' } })

  timelineChart.render()
}

const handleDateChange = () => {
  if (dateRange.value) {
    // 这里可以添加根据日期范围过滤数据的逻辑
    console.log('日期范围变更:', dateRange.value)
  }
}

const refreshData = async () => {
  await expenseStore.fetchTimeline()
  if (timelineChart) {
    timelineChart.destroy()
    initTimelineChart()
  }
}

onMounted(async () => {
  initDateRange()
  if (!expenseStore.timeline.length) {
    await expenseStore.fetchTimeline()
  }
  
  setTimeout(initTimelineChart, 100)
})

onUnmounted(() => {
  if (timelineChart) {
    timelineChart.destroy()
    timelineChart = null
  }
})
</script>

<style scoped>
.timeline-container {
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

.chart-controls {
  margin-bottom: 24px;
  padding: 16px;
  background: rgba(40, 40, 40, 0.6);
  border-radius: 8px;
  border: 1px solid #444;
}

.chart-controls span {
  color: #ccc;
}

.chart-section {
  margin-bottom: 24px;
}

.chart-container {
  height: 400px;
  width: 100%;
}

.stats-grid {
  padding: 20px;
  background: transparent;
  border-radius: 8px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: rgba(40, 40, 40, 0.6);
  border: 1px solid #444;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #a0d911; /* Lime Green for stats */
  margin-bottom: 4px;
  text-shadow: 0 0 5px rgba(160, 217, 17, 0.3);
}

.stat-label {
  font-size: 14px;
  color: #aaa;
}

@media (max-width: 768px) {
  .timeline-container {
    padding: 12px;
  }
  
  .chart-container {
    height: 300px;
  }
  
  .chart-controls {
    padding: 12px;
  }
}
</style>
