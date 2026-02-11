<template>
  <div class="dashboard-container">
    <!-- 顶部统计卡片 -->
    <a-row :gutter="24" class="stat-cards">
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card primary">
          <div class="stat-icon">💰</div>
          <div class="stat-content">
            <div class="stat-number">¥{{ formatNumber(totalExpenses) }}</div>
            <div class="stat-label">总支出</div>
          </div>
        </div>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card success">
          <div class="stat-icon">📊</div>
          <div class="stat-content">
            <div class="stat-number">{{ formatNumber(totalTransactions) }}</div>
            <div class="stat-label">交易笔数</div>
          </div>
        </div>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card warning">
          <div class="stat-icon">📅</div>
          <div class="stat-content">
            <div class="stat-number">¥{{ formatNumber(avgExpense) }}</div>
            <div class="stat-label">平均消费</div>
          </div>
        </div>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card info">
          <div class="stat-icon">⏰</div>
          <div class="stat-content">
            <div class="stat-number">{{ dateRange }}</div>
            <div class="stat-label">数据跨度</div>
          </div>
        </div>
      </a-col>
    </a-row>

    <!-- 图表区域 -->
    <a-row :gutter="24" class="chart-section">
      <!-- 月度趋势图 -->
      <a-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3>📈 月度支出趋势</h3>
            <a-radio-group v-model:value="chartTimeRange" size="small">
              <a-radio-button value="12">近12月</a-radio-button>
              <a-radio-button value="24">近24月</a-radio-button>
            </a-radio-group>
          </div>
          <div ref="monthlyChartRef" class="chart-container"></div>
        </div>
      </a-col>

      <!-- 分类占比图 -->
      <a-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3>🥧 支出分类占比</h3>
            <a-radio-group v-model:value="chartType" size="small">
              <a-radio-button value="pie">饼图</a-radio-button>
              <a-radio-button value="treemap">矩形树图</a-radio-button>
            </a-radio-group>
          </div>
          <div ref="categoryChartRef" class="chart-container"></div>
        </div>
      </a-col>
    </a-row>

    <a-row :gutter="24" class="chart-section">
      <!-- 支付方式分析 -->
      <a-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3>💳 支付方式分析</h3>
            <span class="chart-subtitle">按使用频次排序</span>
          </div>
          <div ref="paymentChartRef" class="chart-container"></div>
        </div>
      </a-col>

      <!-- 支出热力图 -->
      <a-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3>🔥 日支出热力图</h3>
            <span class="chart-subtitle">最近90天消费热度</span>
          </div>
          <div ref="heatmapChartRef" class="chart-container"></div>
        </div>
      </a-col>
    </a-row>

    <!-- 数据加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <a-spin size="large" tip="正在加载数据..." />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useExpenseStore } from '@/stores/expense'
import { Chart } from '@antv/g2'
import { formatNumber } from '@/utils/format'

const expenseStore = useExpenseStore()

// 状态
const loading = computed(() => expenseStore.loading)
const chartTimeRange = ref('12')
const chartType = ref('pie')

// 计算属性
const totalExpenses = computed(() => expenseStore.totalExpenses)
const totalTransactions = computed(() => expenseStore.totalTransactions)
const avgExpense = computed(() => expenseStore.avgExpense)
const dateRange = computed(() => {
  if (!expenseStore.summary) return '0天'
  const start = new Date(expenseStore.summary.earliest_date)
  const end = new Date(expenseStore.summary.latest_date)
  const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
  return `${Math.floor(days / 365)}年${Math.floor((days % 365) / 30)}月`
})

// 图表引用
const monthlyChartRef = ref<HTMLElement>()
const categoryChartRef = ref<HTMLElement>()
const paymentChartRef = ref<HTMLElement>()
const heatmapChartRef = ref<HTMLElement>()

// 图表实例
let monthlyChart: Chart | null = null
let categoryChart: Chart | null = null
let paymentChart: Chart | null = null
let heatmapChart: Chart | null = null

// 初始化月度趋势图
const initMonthlyChart = () => {
  if (!monthlyChartRef.value || !expenseStore.monthlyExpenses.length) return

  monthlyChart = new Chart({
    container: monthlyChartRef.value,
    autoFit: true,
    height: 350,
  })

  const data = expenseStore.monthlyExpenses.slice(0, parseInt(chartTimeRange.value))

  monthlyChart.theme({ type: 'classicDark' }); // Enable Dark Theme

  monthlyChart
    .line()
    .data(data)
    .encode('x', 'month')
    .encode('y', 'monthly_total')
    .encode('color', '#667eea')
    .scale('y', { nice: true })
    .axis('x', { title: '月份' })
    .axis('y', { 
      title: '支出金额 (¥)',
      labelFormatter: (value: number) => `¥${(value / 1000).toFixed(0)}K`
    })
    .tooltip({
      items: [
        { name: '月份', channel: 'x' },
        { name: '支出金额', channel: 'y', valueFormatter: (value: number) => `¥${formatNumber(value)}` },
        { name: '交易笔数', field: 'transaction_count' }
      ]
    })
    .animate({ enter: { type: 'fadeIn' } })

  monthlyChart.render()
}

// 初始化分类占比图
const initCategoryChart = () => {
  if (!categoryChartRef.value || !expenseStore.topCategories.length) return

  const data = expenseStore.topCategories.slice(0, 10)

  if (chartType.value === 'pie') {
    categoryChart = new Chart({
      container: categoryChartRef.value,
      autoFit: true,
      height: 350,
    })
    
    categoryChart.theme({ type: 'classicDark' }); // Enable Dark Theme

    categoryChart
      .interval()
      .data(data)
      .coordinate({ type: 'theta' })
      .encode('y', 'total_amount')
      .encode('color', 'trans_sub_type_name')
      .scale('color', { 
        palette: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7']
      })
      .label({ 
        text: 'trans_sub_type_name',
        fontSize: 12,
        fontWeight: 'bold',
        fill: '#fff'
      })
      .tooltip({
        items: [
          { name: '类别', channel: 'color' },
          { name: '金额', channel: 'y', valueFormatter: (value: number) => `¥${formatNumber(value)}` },
          { name: '笔数', field: 'count' }
        ]
      })
      .legend({ position: 'right' })
  } else {
    categoryChart = new Chart({
      container: categoryChartRef.value,
      autoFit: true,
      height: 350,
    })
    
    categoryChart.theme({ type: 'classicDark' }); // Enable Dark Theme

    categoryChart
      .treemap()
      .data({
        type: 'hierarchical',
        value: data,
      })
      .encode('value', 'total_amount')
      .encode('color', 'trans_type_name')
      .tooltip({
        items: [
          { name: '类别', field: 'trans_sub_type_name' },
          { name: '金额', field: 'total_amount', valueFormatter: (value: number) => `¥${formatNumber(value)}` }
        ]
      })
  }

  categoryChart.render()
}

// 初始化支付方式分析图
const initPaymentChart = () => {
  if (!paymentChartRef.value || !expenseStore.mainPaymentMethods.length) return

  const data = expenseStore.mainPaymentMethods

  paymentChart = new Chart({
    container: paymentChartRef.value,
    autoFit: true,
    height: 350,
  })
  
  paymentChart.theme({ type: 'classicDark' }); // Enable Dark Theme

  paymentChart
    .interval()
    .data(data)
    .encode('x', 'pay_account')
    .encode('y', 'usage_count')
    .encode('color', '#764ba2')
    .axis('x', { 
      title: '支付账户',
      label: { autoRotate: true, autoHide: true }
    })
    .axis('y', { title: '使用次数' })
    .tooltip({
      items: [
        { name: '支付账户', channel: 'x' },
        { name: '使用次数', channel: 'y' },
        { name: '总消费', field: 'total_spent', valueFormatter: (value: number) => `¥${formatNumber(value)}` }
      ]
    })
    .animate({ enter: { type: 'scaleInY' } })

  paymentChart.render()
}

// 初始化热力图
const initHeatmapChart = () => {
  if (!heatmapChartRef.value || !expenseStore.timeline.length) return

  // 1. Process data for calendar heatmap
  const calendarData = expenseStore.timeline.map(d => ({
    date: d.date,
    value: d.daily_total,
    week: dayjs(d.date).day(), // 0 (Sun) - 6 (Sat)
    day: dayjs(d.date).format('YYYY-MM-DD'),
  }));

  heatmapChart = new Chart({
    container: heatmapChartRef.value,
    autoFit: true,
    height: 350,
  })
  
  heatmapChart.theme({ type: 'classicDark' }); 
  
  heatmapChart.coordinate({ type: 'theta' });

  heatmapChart
    .cell() // Use cell geometry for heatmaps
    .data(calendarData)
    .encode('x', d => dayjs(d.date).week()) // week number
    .encode('y', d => dayjs(d.date).day())  // day of week
    .encode('color', 'value')
    .scale('color', {
        palette: 'spectral', // Use a vibrant palette for dark mode
    })
    .style({
        inset: 0.5,
    })
    .tooltip({
      items: [
        { name: '日期', field: 'day' },
        { name: '日支出', field: 'value', valueFormatter: (value) => `¥${formatNumber(value)}` },
      ]
    });

  heatmapChart.render()
}

// 生命周期
onMounted(async () => {
  await expenseStore.fetchAllData()
  
  // 延迟渲染图表，确保DOM ready
  setTimeout(() => {
    initMonthlyChart()
    initCategoryChart()
    initPaymentChart()
    initHeatmapChart()
  }, 100)
})

// 监听图表配置变化
watch(chartTimeRange, () => {
  if (monthlyChart) {
    monthlyChart.destroy()
    initMonthlyChart()
  }
})

watch(chartType, () => {
  if (categoryChart) {
    categoryChart.destroy()
    initCategoryChart()
  }
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  min-height: calc(100vh - 64px);
  /* background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);  REMOVED */
}

.stat-cards {
  margin-bottom: 24px;
}

.stat-card {
  background: rgba(25, 25, 25, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  background: rgba(40, 40, 40, 0.8);
}

.stat-card.primary {
  border-left: 4px solid #667eea;
}

.stat-card.success {
  border-left: 4px solid #52c41a;
}

.stat-card.warning {
  border-left: 4px solid #faad14;
}

.stat-card.info {
  border-left: 4px solid #1890ff;
}

.stat-icon {
  font-size: 32px;
  margin-right: 16px;
  opacity: 0.8;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #fff; /* Changed from #262626 */
  margin-bottom: 4px;
  text-shadow: 0 0 10px rgba(255,255,255,0.2);
}

.stat-label {
  font-size: 14px;
  color: #aaa; /* Changed from #8c8c8c */
}

.chart-section {
  margin-bottom: 24px;
}

.chart-card {
  background: rgba(25, 25, 25, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  height: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #fff; /* Changed from #262626 */
}

.chart-subtitle {
  font-size: 12px;
  color: #888;
}

.chart-container {
  height: 350px;
  width: 100%;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8); /* Changed from white */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .dashboard-container {
    padding: 12px;
  }
  
  .stat-card {
    padding: 16px;
    margin-bottom: 12px;
  }
  
  .stat-icon {
    font-size: 24px;
    margin-right: 12px;
  }
  
  .stat-number {
    font-size: 18px;
  }
  
  .chart-card {
    padding: 16px;
  }
  
  .chart-container {
    height: 280px;
  }
  
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>