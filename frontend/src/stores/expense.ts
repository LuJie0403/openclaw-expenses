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

  // 方法
  const fetchSummary = async () => {
    try {
      summary.value = await expenseAPI.getSummary()
    } catch (err) {
      error.value = '获取支出总览失败'
      console.error(err)
    }
  }

  const fetchMonthlyData = async () => {
    try {
      monthlyExpenses.value = await expenseAPI.getMonthly()
    } catch (err) {
      error.value = '获取月度数据失败'
      console.error(err)
    }
  }

  const fetchCategories = async () => {
    try {
      categories.value = await expenseAPI.getCategories()
    } catch (err) {
      error.value = '获取分类数据失败'
      console.error(err)
    }
  }

  const fetchPaymentMethods = async () => {
    try {
      paymentMethods.value = await expenseAPI.getPaymentMethods()
    } catch (err) {
      error.value = '获取支付方式失败'
      console.error(err)
    }
  }

  const fetchTimeline = async () => {
    try {
      timeline.value = await expenseAPI.getTimeline()
    } catch (err) {
      error.value = '获取时间线数据失败'
      console.error(err)
    }
  }

  const fetchAllData = async () => {
    loading.value = true
    error.value = null
    try {
      await Promise.all([
        fetchSummary(),
        fetchMonthlyData(),
        fetchCategories(),
        fetchPaymentMethods(),
        fetchTimeline()
      ])
    } catch (err) {
      error.value = '数据加载失败'
      console.error(err)
    } finally {
      loading.value = false
    }
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