<template>
  <div class="timeline-lab">
    <div class="hero-panel">
      <div>
        <h2>时间洞察中心</h2>
        <p>从日、周、月三个尺度观察消费节奏，定位高峰与结构变化。</p>
      </div>
      <div class="hero-actions">
        <a-radio-group v-model:value="selectedRange" size="small" button-style="solid">
          <a-radio-button value="30">近30天</a-radio-button>
          <a-radio-button value="90">近90天</a-radio-button>
          <a-radio-button value="180">近180天</a-radio-button>
          <a-radio-button value="all">全部</a-radio-button>
        </a-radio-group>
        <a-button type="primary" :loading="isLoading" @click="refreshData">刷新</a-button>
      </div>
    </div>

    <a-alert
      v-if="expenseStore.error"
      :message="expenseStore.error"
      type="error"
      show-icon
      class="error-banner"
    />

    <a-row :gutter="16" class="stats-row">
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-title">最高日支出</div>
          <div class="stat-value">¥{{ formatAmount(highestDay.amount) }}</div>
          <div class="stat-sub">发生于 {{ highestDay.date }}</div>
        </div>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-title">平均日支出</div>
          <div class="stat-value">¥{{ formatAmount(avgDayExpense) }}</div>
          <div class="stat-sub">{{ rangeSummary }}</div>
        </div>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-title">最多交易天数</div>
          <div class="stat-value">{{ maxTradeDay.count }}笔</div>
          <div class="stat-sub">发生于 {{ maxTradeDay.date }}</div>
        </div>
      </a-col>
      <a-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-title">统计天数</div>
          <div class="stat-value">{{ filteredTimeline.length }}天</div>
          <div class="stat-sub">有消费记录的自然日</div>
        </div>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="panel-row">
      <a-col :xs="24" :lg="14">
        <a-card title="日度消费脉冲（含7日均线）" class="panel-card">
          <div ref="dailyPulseRef" class="chart-box" />
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="10">
        <a-card title="周内消费分布（周一至周日）" class="panel-card">
          <div ref="weekdayRef" class="chart-box" />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="panel-row">
      <a-col :xs="24" :lg="14">
        <a-card title="周度热力矩阵" class="panel-card">
          <div ref="heatmapRef" class="chart-box" />
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="10">
        <a-card title="月度消费结构" class="panel-card">
          <div ref="monthlyRef" class="chart-box" />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useExpenseStore } from '@/stores/expense'
import * as echarts from 'echarts'
import dayjs from 'dayjs'
import { formatAmount } from '@/utils/format'

type RangeValue = '30' | '90' | '180' | 'all'

type TimelinePoint = {
  date: string
  daily_total: number
  transaction_count: number
}

type MonthPoint = {
  month: string
  monthly_total: number
  transaction_count: number
}

const expenseStore = useExpenseStore()
const selectedRange = ref<RangeValue>('90')
const isLoading = ref(false)

const dailyPulseRef = ref<HTMLElement>()
const weekdayRef = ref<HTMLElement>()
const heatmapRef = ref<HTMLElement>()
const monthlyRef = ref<HTMLElement>()

const chartInstances: Record<string, echarts.ECharts | null> = {
  dailyPulse: null,
  weekday: null,
  heatmap: null,
  monthly: null,
}

const fullTimeline = computed<TimelinePoint[]>(() =>
  expenseStore.timeline
    .map((item) => ({
      date: item.date,
      daily_total: Number(item.daily_total || 0),
      transaction_count: Number(item.transaction_count || 0),
    }))
    .sort((left, right) => dayjs(left.date).valueOf() - dayjs(right.date).valueOf()),
)

const monthlyTimeline = computed<MonthPoint[]>(() =>
  expenseStore.monthlyExpenses
    .map((item) => ({
      month: `${item.year}-${String(item.month).padStart(2, '0')}`,
      monthly_total: Number(item.monthly_total || 0),
      transaction_count: Number(item.transaction_count || 0),
    }))
    .sort((left, right) => dayjs(`${left.month}-01`).valueOf() - dayjs(`${right.month}-01`).valueOf()),
)

const filteredTimeline = computed<TimelinePoint[]>(() => {
  if (!fullTimeline.value.length) return []
  if (selectedRange.value === 'all') return fullTimeline.value

  const days = Number(selectedRange.value)
  const end = dayjs(fullTimeline.value[fullTimeline.value.length - 1].date)
  const start = end.subtract(days - 1, 'day')

  return fullTimeline.value.filter((item) => {
    const current = dayjs(item.date)
    return current.isAfter(start.subtract(1, 'day')) && current.isBefore(end.add(1, 'day'))
  })
})

const filteredMonthly = computed<MonthPoint[]>(() => {
  if (!monthlyTimeline.value.length) return []
  if (selectedRange.value === 'all') return monthlyTimeline.value
  if (!filteredTimeline.value.length) return []

  const start = dayjs(filteredTimeline.value[0].date).startOf('month')
  const end = dayjs(filteredTimeline.value[filteredTimeline.value.length - 1].date).endOf('month')

  return monthlyTimeline.value.filter((item) => {
    const current = dayjs(`${item.month}-01`)
    return current.isAfter(start.subtract(1, 'day')) && current.isBefore(end.add(1, 'day'))
  })
})

const highestDay = computed(() => {
  if (!filteredTimeline.value.length) return { amount: 0, date: '--' }
  const target = filteredTimeline.value.reduce((max, item) =>
    item.daily_total > max.daily_total ? item : max,
  )
  return {
    amount: target.daily_total,
    date: dayjs(target.date).format('YYYY-MM-DD'),
  }
})

const avgDayExpense = computed(() => {
  if (!filteredTimeline.value.length) return 0
  const sum = filteredTimeline.value.reduce((acc, item) => acc + item.daily_total, 0)
  return sum / filteredTimeline.value.length
})

const maxTradeDay = computed(() => {
  if (!filteredTimeline.value.length) return { count: 0, date: '--' }
  const target = filteredTimeline.value.reduce((max, item) =>
    item.transaction_count > max.transaction_count ? item : max,
  )
  return {
    count: target.transaction_count,
    date: dayjs(target.date).format('YYYY-MM-DD'),
  }
})

const rangeSummary = computed(() => {
  if (!filteredTimeline.value.length) return '暂无数据'
  const start = dayjs(filteredTimeline.value[0].date).format('YYYY-MM-DD')
  const end = dayjs(filteredTimeline.value[filteredTimeline.value.length - 1].date).format('YYYY-MM-DD')
  return `${start} 至 ${end}`
})

const setEmptyOption = (chart: echarts.ECharts, title: string) => {
  chart.setOption({
    title: {
      text: title,
      left: 'center',
      top: 'middle',
      textStyle: { color: '#8c8c8c', fontSize: 14, fontWeight: 400 },
    },
    xAxis: { show: false },
    yAxis: { show: false },
    series: [],
  })
}

const createChart = (container: HTMLElement | undefined): echarts.ECharts | null => {
  if (!container) return null
  return echarts.init(container)
}

const renderDailyPulseChart = () => {
  const chart = createChart(dailyPulseRef.value)
  if (!chart) return

  if (!filteredTimeline.value.length) {
    setEmptyOption(chart, '暂无日度数据')
    chartInstances.dailyPulse = chart
    return
  }

  const labels = filteredTimeline.value.map((item) => dayjs(item.date).format('MM-DD'))
  const amounts = filteredTimeline.value.map((item) => item.daily_total)
  const trades = filteredTimeline.value.map((item) => item.transaction_count)
  const movingAvg = amounts.map((_, index) => {
    const start = Math.max(0, index - 6)
    const slice = amounts.slice(start, index + 1)
    const avg = slice.reduce((sum, value) => sum + value, 0) / slice.length
    return Number(avg.toFixed(2))
  })

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params: any[]) => {
        const i = Number(params?.[0]?.dataIndex || 0)
        return [
          `${dayjs(filteredTimeline.value[i].date).format('YYYY-MM-DD')}`,
          `日支出: ¥${formatAmount(amounts[i])}`,
          `交易笔数: ${trades[i]}笔`,
          `7日均线: ¥${formatAmount(movingAvg[i])}`,
        ].join('<br/>')
      },
    },
    legend: {
      data: ['日支出', '7日均线'],
      textStyle: { color: '#d9d9d9' },
      top: 4,
    },
    grid: { left: 56, right: 20, top: 50, bottom: 40 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#8c8c8c', interval: Math.max(Math.floor(labels.length / 10), 0) },
      axisLine: { lineStyle: { color: '#434343' } },
    },
    yAxis: {
      type: 'value',
      name: '金额（元）',
      nameTextStyle: { color: '#8c8c8c' },
      axisLabel: { color: '#8c8c8c', formatter: (value: number) => `¥${formatAmount(value)}` },
      splitLine: { lineStyle: { color: '#262626' } },
    },
    series: [
      {
        name: '日支出',
        type: 'bar',
        data: amounts,
        itemStyle: { color: '#4e79ff' },
        barWidth: '65%',
      },
      {
        name: '7日均线',
        type: 'line',
        data: movingAvg,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#ff9f43' },
      },
    ],
  })

  chartInstances.dailyPulse = chart
}

const renderWeekdayChart = () => {
  const chart = createChart(weekdayRef.value)
  if (!chart) return

  if (!filteredTimeline.value.length) {
    setEmptyOption(chart, '暂无周内分布数据')
    chartInstances.weekday = chart
    return
  }

  const weekdayOrder = [1, 2, 3, 4, 5, 6, 0]
  const weekdayLabelMap: Record<number, string> = {
    1: '周一',
    2: '周二',
    3: '周三',
    4: '周四',
    5: '周五',
    6: '周六',
    0: '周日',
  }

  const buckets = new Map<number, { amount: number; trades: number }>()
  weekdayOrder.forEach((weekday) => buckets.set(weekday, { amount: 0, trades: 0 }))

  filteredTimeline.value.forEach((item) => {
    const weekday = dayjs(item.date).day()
    const current = buckets.get(weekday)
    if (!current) return
    current.amount += item.daily_total
    current.trades += item.transaction_count
  })

  const labels = weekdayOrder.map((weekday) => weekdayLabelMap[weekday])
  const amounts = weekdayOrder.map((weekday) => Number((buckets.get(weekday)?.amount || 0).toFixed(2)))
  const trades = weekdayOrder.map((weekday) => buckets.get(weekday)?.trades || 0)

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any[]) => {
        const i = Number(params?.[0]?.dataIndex || 0)
        return [
          labels[i],
          `总支出: ¥${formatAmount(amounts[i])}`,
          `交易总笔数: ${trades[i]}笔`,
        ].join('<br/>')
      },
    },
    grid: { left: 52, right: 16, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#8c8c8c' },
      axisLine: { lineStyle: { color: '#434343' } },
    },
    yAxis: {
      type: 'value',
      name: '金额（元）',
      nameTextStyle: { color: '#8c8c8c' },
      axisLabel: { color: '#8c8c8c', formatter: (value: number) => `¥${formatAmount(value)}` },
      splitLine: { lineStyle: { color: '#262626' } },
    },
    series: [
      {
        type: 'bar',
        data: amounts,
        barWidth: '50%',
        itemStyle: { color: '#00bcd4' },
      },
    ],
  })

  chartInstances.weekday = chart
}

const renderHeatmapChart = () => {
  const chart = createChart(heatmapRef.value)
  if (!chart) return

  if (!filteredTimeline.value.length) {
    setEmptyOption(chart, '暂无热力矩阵数据')
    chartInstances.heatmap = chart
    return
  }

  const start = dayjs(filteredTimeline.value[0].date).startOf('week')
  const end = dayjs(filteredTimeline.value[filteredTimeline.value.length - 1].date).endOf('week')
  const weekCount = Math.max(end.diff(start, 'week') + 1, 1)

  const xLabels = Array.from({ length: weekCount }, (_, i) =>
    dayjs(start).add(i, 'week').format('MM-DD'),
  )

  const yLabels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const weekdayIndexMap: Record<number, number> = { 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 0: 6 }

  const heatData = filteredTimeline.value.map((item) => {
    const current = dayjs(item.date)
    const weekIndex = current.startOf('week').diff(start, 'week')
    const dayIndex = weekdayIndexMap[current.day()]
    return [weekIndex, dayIndex, Number(item.daily_total.toFixed(2)), item.transaction_count, item.date]
  })

  const maxAmount = Math.max(...filteredTimeline.value.map((item) => item.daily_total), 0)

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      formatter: (params: any) => {
        const [weekIndex, dayIndex, amount, trades, date] = params.data
        return [
          `${date}`,
          `周序: ${xLabels[Number(weekIndex)]}`,
          `星期: ${yLabels[Number(dayIndex)]}`,
          `日支出: ¥${formatAmount(Number(amount))}`,
          `交易笔数: ${trades}笔`,
        ].join('<br/>')
      },
    },
    grid: { left: 64, right: 24, top: 18, bottom: 62 },
    xAxis: {
      type: 'category',
      data: xLabels,
      axisLabel: { color: '#8c8c8c', interval: Math.max(Math.floor(xLabels.length / 8), 0) },
      axisLine: { lineStyle: { color: '#434343' } },
    },
    yAxis: {
      type: 'category',
      data: yLabels,
      axisLabel: { color: '#8c8c8c' },
      axisLine: { lineStyle: { color: '#434343' } },
    },
    visualMap: {
      min: 0,
      max: Math.max(maxAmount, 1),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 8,
      text: ['高', '低'],
      textStyle: { color: '#8c8c8c' },
      inRange: {
        color: ['#1b1f3a', '#225ea8', '#41b6c4', '#7fcdbb', '#fed976', '#ff6b6b'],
      },
    },
    series: [
      {
        type: 'heatmap',
        data: heatData,
        label: { show: false },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  })

  chartInstances.heatmap = chart
}

const renderMonthlyChart = () => {
  const chart = createChart(monthlyRef.value)
  if (!chart) return

  if (!filteredMonthly.value.length) {
    setEmptyOption(chart, '暂无月度结构数据')
    chartInstances.monthly = chart
    return
  }

  const labels = filteredMonthly.value.map((item) => item.month)
  const amountSeries = filteredMonthly.value.map((item) => item.monthly_total)
  const countSeries = filteredMonthly.value.map((item) => item.transaction_count)

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params: any[]) => {
        const i = Number(params?.[0]?.dataIndex || 0)
        return [
          labels[i],
          `月消费: ¥${formatAmount(amountSeries[i])}`,
          `交易笔数: ${countSeries[i]}笔`,
        ].join('<br/>')
      },
    },
    legend: {
      data: ['月消费', '交易笔数'],
      textStyle: { color: '#d9d9d9' },
      top: 4,
    },
    grid: { left: 52, right: 54, top: 50, bottom: 40 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#8c8c8c', interval: Math.max(Math.floor(labels.length / 8), 0) },
      axisLine: { lineStyle: { color: '#434343' } },
    },
    yAxis: [
      {
        type: 'value',
        name: '金额（元）',
        nameTextStyle: { color: '#8c8c8c' },
        axisLabel: { color: '#8c8c8c', formatter: (value: number) => `¥${formatAmount(value)}` },
        splitLine: { lineStyle: { color: '#262626' } },
      },
      {
        type: 'value',
        name: '笔数',
        nameTextStyle: { color: '#8c8c8c' },
        axisLabel: { color: '#8c8c8c' },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '月消费',
        type: 'bar',
        data: amountSeries,
        itemStyle: { color: '#7f5af0' },
        barWidth: '48%',
      },
      {
        name: '交易笔数',
        type: 'line',
        yAxisIndex: 1,
        data: countSeries,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#2dd4bf', width: 2 },
      },
    ],
  })

  chartInstances.monthly = chart
}

const disposeCharts = () => {
  Object.keys(chartInstances).forEach((key) => {
    const chart = chartInstances[key]
    if (chart) {
      chart.dispose()
      chartInstances[key] = null
    }
  })
}

const renderAllCharts = async () => {
  await nextTick()
  disposeCharts()
  renderDailyPulseChart()
  renderWeekdayChart()
  renderHeatmapChart()
  renderMonthlyChart()
}

const refreshData = async () => {
  isLoading.value = true
  try {
    await Promise.allSettled([expenseStore.fetchTimeline(), expenseStore.fetchMonthlyData()])
    await renderAllCharts()
  } finally {
    isLoading.value = false
  }
}

const handleResize = () => {
  Object.values(chartInstances).forEach((chart) => chart?.resize())
}

watch([filteredTimeline, filteredMonthly], () => {
  renderAllCharts()
})

onMounted(async () => {
  if (!expenseStore.timeline.length || !expenseStore.monthlyExpenses.length) {
    await refreshData()
  } else {
    await renderAllCharts()
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  disposeCharts()
})
</script>

<style scoped>
.timeline-lab {
  padding: 20px;
  min-height: calc(100vh - 64px);
}

.hero-panel {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  background: linear-gradient(135deg, rgba(20, 24, 51, 0.9), rgba(33, 44, 91, 0.75));
  border: 1px solid rgba(95, 114, 189, 0.5);
  border-radius: 14px;
  padding: 18px 20px;
  margin-bottom: 16px;
}

.hero-panel h2 {
  margin: 0;
  color: #f5f7ff;
  font-size: 22px;
}

.hero-panel p {
  margin: 6px 0 0;
  color: #a9b4df;
  font-size: 13px;
}

.hero-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.error-banner {
  margin-bottom: 16px;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-card {
  height: 100%;
  background: rgba(18, 20, 35, 0.85);
  border: 1px solid #2e355f;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 10px 24px rgba(6, 10, 32, 0.35);
}

.stat-title {
  color: #9aa7d8;
  font-size: 13px;
  margin-bottom: 8px;
}

.stat-value {
  color: #ffffff;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-sub {
  margin-top: 6px;
  color: #7f8cc5;
  font-size: 12px;
}

.panel-row {
  margin-bottom: 16px;
}

.panel-card {
  height: 100%;
  background: rgba(25, 25, 25, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid #333;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.chart-box {
  height: 360px;
  width: 100%;
}

@media (max-width: 992px) {
  .timeline-lab {
    padding: 12px;
  }

  .hero-panel {
    flex-direction: column;
  }

  .hero-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .chart-box {
    height: 300px;
  }
}
</style>
