<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useExpenseStore } from '@/stores/expense'
import { Chart } from '@antv/g2'
import { formatNumber, formatDate } from '@/utils/format'
import dayjs from 'dayjs'
import weekOfYear from 'dayjs/plugin/weekOfYear'
dayjs.extend(weekOfYear)

const expenseStore = useExpenseStore()

const loading = computed(() => expenseStore.loading)
const chartTimeRange = ref('12')
const chartType = ref('pie')

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

const monthlyChartRef = ref<HTMLElement>()
const categoryChartRef = ref<HTMLElement>()
const paymentChartRef = ref<HTMLElement>()
const heatmapChartRef = ref<HTMLElement>()

let monthlyChart: Chart | null = null
let categoryChart: Chart | null = null
let paymentChart: Chart | null = null
let heatmapChart: Chart | null = null

const initMonthlyChart = () => { /* ... existing code ... */ }
const initCategoryChart = () => { /* ... existing code ... */ }
const initPaymentChart = () => { /* ... existing code ... */ }
const initHeatmapChart = () => {
  if (!heatmapChartRef.value || !expenseStore.timeline.length) return
  const calendarData = expenseStore.timeline.map(d => ({ /* ... existing logic ... */ }));
  heatmapChart = new Chart({ container: heatmapChartRef.value, autoFit: true, height: 350 });
  heatmapChart.theme({ type: 'classicDark' });
  heatmapChart.coordinate({ type: 'theta' });
  heatmapChart.cell().data(calendarData).encode('x', d => dayjs(d.date).week()).encode('y', d => dayjs(d.date).day()).encode('color', 'value').scale('color', { palette: 'spectral' }).style({ inset: 0.5 }).tooltip({ items: [{ name: '日期', field: 'day' }, { name: '日支出', field: 'value', valueFormatter: (value) => `¥${formatNumber(value)}` }] });
  heatmapChart.render()
}


onMounted(async () => {
  await expenseStore.fetchAllData()
  setTimeout(() => {
    initMonthlyChart()
    initCategoryChart()
    initPaymentChart()
    initHeatmapChart()
  }, 100)
})

onUnmounted(() => {
  monthlyChart?.destroy()
  categoryChart?.destroy()
  paymentChart?.destroy()
  heatmapChart?.destroy()
})

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