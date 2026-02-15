
import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'

// Determine API base URL
const API_BASE_URL = import.meta.env.PROD 
  ? '/api' // In production (Nginx proxy), use relative path
  : '/api' // In development, also use proxy


// Create Axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Increased timeout
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request Interceptor: Attach Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response Interceptor: Handle 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      // Redirect to login page if not already there
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api

// Define interfaces for API responses
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

// API methods wrapper
export const expenseAPI = {
  // Get expense summary
  getSummary: async (): Promise<ExpenseSummary> => {
    const response = await api.get('/expenses/summary')
    return response.data
  },

  // Get monthly expenses
  getMonthly: async (): Promise<MonthlyExpense[]> => {
    const response = await api.get('/expenses/monthly')
    return response.data
  },

  // Get category breakdown
  getCategories: async (): Promise<CategoryExpense[]> => {
    const response = await api.get('/expenses/categories')
    return response.data
  },

  // Get payment methods usage
  getPaymentMethods: async (): Promise<PaymentMethod[]> => {
    const response = await api.get('/expenses/payment-methods')
    return response.data
  },

  // Get timeline data
  getTimeline: async (): Promise<TimelineData[]> => {
    const response = await api.get('/expenses/timeline')
    return response.data
  },

  // Health check
  healthCheck: async (): Promise<any> => {
    const response = await api.get('/health')
    return response.data
  }
}
