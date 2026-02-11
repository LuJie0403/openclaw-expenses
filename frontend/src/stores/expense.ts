import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { expenseAPI, type ExpenseSummary, type MonthlyExpense, type CategoryExpense, type PaymentMethod, type TimelineData } from '@/services/api'

export const useExpenseStore = defineStore('expense', () => {
  // 状态
  const summary = ref<ExpenseSummary | null>(null)
  const monthlyExpenses = ref<MonthlyExpense[]>([])
  const categories = ref<CategoryExpense[]>([])
  const paymentMethods = ref<PaymentMethod[]>([])
  const timeline = ref<TimelineData[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 计算属性
  const totalExpenses = computed(() => summary.value?.total_amount || 0)
  const totalTransactions = computed(() => summary.value?.total_count || 0)
  const avgExpense = computed(() => summary.value?.avg_amount || 0)

  const topCategories = computed(() => 
    categories.value.slice(0, 10)
  )

  const mainPaymentMethods = computed(() =>
    paymentMethods.value.slice(0, 8)
  )

  const raiseStoreError = (message: string, err: unknown) => {
    error.value = message
    console.error(err)
    throw err
  }

  // 方法
  const fetchSummary = async () => {
    try {
      summary.value = await expenseAPI.getSummary()
    } catch (err) {
      raiseStoreError('获取支出总览失败', err)
    }
  }

  const fetchMonthlyData = async () => {
    try {
      monthlyExpenses.value = await expenseAPI.getMonthly()
    } catch (err) {
      raiseStoreError('获取月度数据失败', err)
    }
  }

  const fetchCategories = async () => {
    try {
      categories.value = await expenseAPI.getCategories()
    } catch (err) {
      raiseStoreError('获取分类数据失败', err)
    }
  }

  const fetchPaymentMethods = async () => {
    try {
      paymentMethods.value = await expenseAPI.getPaymentMethods()
    } catch (err) {
      raiseStoreError('获取支付方式失败', err)
    }
  }

  const fetchTimeline = async () => {
    try {
      timeline.value = await expenseAPI.getTimeline()
    } catch (err) {
      raiseStoreError('获取时间线数据失败', err)
    }
  }

  const fetchAllData = async () => {
    loading.value = true
    error.value = null
    const results = await Promise.allSettled([
      fetchSummary(),
      fetchMonthlyData(),
      fetchCategories(),
      fetchPaymentMethods(),
      fetchTimeline()
    ])
    const failedCount = results.filter(result => result.status === 'rejected').length
    if (failedCount > 0) {
      error.value = `部分数据加载失败（${failedCount}/${results.length}）`
    }
    loading.value = false
  }

  return {
    // 状态
    summary,
    monthlyExpenses,
    categories,
    paymentMethods,
    timeline,
    loading,
    error,
    
    // 计算属性
    totalExpenses,
    totalTransactions,
    avgExpense,
    topCategories,
    mainPaymentMethods,
    
    // 方法
    fetchAllData,
    fetchSummary,
    fetchMonthlyData,
    fetchCategories,
    fetchPaymentMethods,
    fetchTimeline
  }
})
