<template>
  <div class="timeline-lab">
    <div class="hero-panel">
      <div>
        <h2>时间洞察中心</h2>
        <p>从日、周、月、年四个尺度观察消费节奏，定位高峰与结构变化。</p>
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
        <a-card title="By年走势对比（月度支出）" class="panel-card">
          <div ref="yearTrendRef" class="chart-box" />
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
  year: number
  monthNumber: number
  monthly_total: number
  transaction_count: number
}

const expenseStore = useExpenseStore()
const selectedRange = ref<RangeValue>('90')
const isLoading = ref(false)

const dailyPulseRef = ref<HTMLElement>()
const weekdayRef = ref<HTMLElement>()
const yearTrendRef = ref<HTMLElement>()
const monthlyRef = ref<HTMLElement>()

const chartInstances: Record<string, echarts.ECharts | null> = {
  dailyPulse: null,
  weekday: null,
  yearTrend: null,
  monthly: null,
}

const parseYearMonth = (yearRaw: unknown, monthRaw: unknown): { year: number; monthNumber: number } | null => {
  const directYear = Number(yearRaw)
  const directMonth = Number(monthRaw)
  if (Number.isFinite(directYear) && Number.isFinite(directMonth) && directMonth >= 1 && directMonth <= 12) {
    return { year: directYear, monthNumber: directMonth }
  }

  const monthText = String(monthRaw ?? '').trim()
  const fullMatch = monthText.match(/(\d{4})[-/.年](\d{1,2})/)
  if (fullMatch) {
    const year = Number(fullMatch[1])
    const monthNumber = Number(fullMatch[2])
    if (Number.isFinite(year) && monthNumber >= 1 && monthNumber <= 12) {
      return { year, monthNumber }
    }
  }

  const monthOnly = Number(monthText)
  if (Number.isFinite(directYear) && Number.isFinite(monthOnly) && monthOnly >= 1 && monthOnly <= 12) {
    return { year: directYear, monthNumber: monthOnly }
  }

  return null
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
    .map((item) => {
      const parsed = parseYearMonth(item.year, item.month)
      if (!parsed) return null
      return {
        month: `${parsed.year}-${String(parsed.monthNumber).padStart(2, '0')}`,
        year: parsed.year,
        monthNumber: parsed.monthNumber,
        monthly_total: Number(item.monthly_total || 0),
        transaction_count: Number(item.transaction_count || 0),
      }
    })
    .filter((item): item is MonthPoint => item !== null)
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
      left: 'center',
      bottom: 8,
    },
    grid: { left: 56, right: 20, top: 24, bottom: 78 },
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

const renderYearTrendChart = () => {
  const chart = createChart(yearTrendRef.value)
  if (!chart) return

  if (!filteredMonthly.value.length) {
    setEmptyOption(chart, '暂无年度走势数据')
    chartInstances.yearTrend = chart
    return
  }

  const monthLabels = Array.from({ length: 12 }, (_, i) => `${i + 1}月`)
  const yearBuckets = new Map<string, Array<number | null>>()

  filteredMonthly.value.forEach((item) => {
    const monthIndex = item.monthNumber - 1
    if (monthIndex < 0 || monthIndex > 11) return
    const year = String(item.year)
    if (!yearBuckets.has(year)) {
      yearBuckets.set(year, Array(12).fill(null))
    }
    const values = yearBuckets.get(year)
    if (!values) return
    values[monthIndex] = Number(item.monthly_total.toFixed(2))
  })

  const years = Array.from(yearBuckets.keys()).sort((a, b) => Number(a) - Number(b))
  const series = years.map((year) => ({
    name: year,
    type: 'line',
    data: yearBuckets.get(year),
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    connectNulls: false,
    lineStyle: { width: 2 },
  }))

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line' },
      formatter: (params: any[]) => {
        const title = params?.[0]?.axisValueLabel || ''
        const lines = (params || [])
          .filter((p) => p.value !== null && p.value !== undefined)
          .map((p) => `${p.marker}${p.seriesName}: ¥${formatAmount(Number(p.value))}`)
        return [title, ...lines].join('<br/>')
      },
    },
    legend: {
      data: years,
      textStyle: { color: '#d9d9d9' },
      left: 'center',
      bottom: 8,
    },
    grid: { left: 56, right: 24, top: 24, bottom: 78 },
    xAxis: {
      type: 'category',
      data: monthLabels,
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
    series,
  })

  chartInstances.yearTrend = chart
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
      left: 'center',
      bottom: 8,
    },
    grid: { left: 52, right: 54, top: 24, bottom: 82 },
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
  renderYearTrendChart()
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
