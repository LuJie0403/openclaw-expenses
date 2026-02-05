import axios from 'axios'

const API_BASE_URL = import.meta.env.PROD 
  ? '/api' 
  : 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export interface ExpenseSummary {
  total_amount: number
  total_count: number
  avg_amount: number
  earliest_date: string
  latest_date: string
}

export interface MonthlyExpense {
  year: string
  month: string
  transaction_count: number
  monthly_total: number
  avg_transaction: number
}

export interface CategoryExpense {
  trans_type_name: string
  trans_sub_type_name: string
  count: number
  total_amount: number
  avg_amount: number
}

export interface PaymentMethod {
  pay_account: string
  usage_count: number
  total_spent: number
  avg_per_transaction: number
}

export interface TimelineData {
  date: string
  daily_total: number
  transaction_count: number
}

// API接口
export const expenseAPI = {
  // 获取支出总览
  getSummary: async (): Promise<ExpenseSummary> => {
    const response = await api.get('/expenses/summary')
    return response.data
  },

  // 获取月度支出
  getMonthly: async (): Promise<MonthlyExpense[]> => {
    const response = await api.get('/expenses/monthly')
    return response.data
  },

  // 获取分类支出
  getCategories: async (): Promise<CategoryExpense[]> => {
    const response = await api.get('/expenses/categories')
    return response.data
  },

  // 获取支付方式
  getPaymentMethods: async (): Promise<PaymentMethod[]> => {
    const response = await api.get('/expenses/payment-methods')
    return response.data
  },

  // 获取时间线数据
  getTimeline: async (): Promise<TimelineData[]> => {
    const response = await api.get('/expenses/timeline')
    return response.data
  },

  // 健康检查
  healthCheck: async (): Promise<any> => {
    const response = await api.get('/health')
    return response.data
  }
}