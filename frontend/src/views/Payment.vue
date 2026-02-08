<template>
  <div class="payment-container">
    <a-row :gutter="24">
      <!-- 支付方式总览 -->
      <a-col :xs="24" :lg="16">
        <a-card title="支付方式分析" class="chart-card">
          <div ref="paymentChartRef" class="chart-container"></div>
        </a-card>
      </a-col>
      
      <!-- 支付统计 -->
      <a-col :xs="24" :lg="8">
        <a-card title="支付统计" class="stats-card">
          <div class="stats-list">
            <div v-for="method in topPaymentMethods" :key="method.pay_account" class="stat-item">
              <div class="stat-header">
                <span class="account-name">{{ formatAccountName(method.pay_account) }}</span>
                <span class="usage-count">{{ method.usage_count }}笔</span>
              </div>
              <div class="stat-detail">
                <span class="total-amount">¥{{ formatNumber(method.total_spent) }}</span>
                <span class="avg-amount">平均¥{{ formatNumber(method.avg_per_transaction) }}</span>
              </div>
              <a-progress 
                :percent="getUsagePercentage(method.usage_count)" 
                :show-info="false"
                stroke-color="#667eea"
              />
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 详细表格 -->
    <a-row :gutter="24" class="table-section">
      <a-col :span="24">
        <a-card title="支付方式详情" class="table-card">
          <a-table
            :columns="columns"
            :data-source="expenseStore.paymentMethods"
            :pagination="{ pageSize: 10 }"
            row-key="pay_account"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'total_spent'">
                <span class="amount-text">¥{{ formatNumber(record.total_spent) }}</span>
              </template>
              <template v-if="column.key === 'avg_per_transaction'">
                <span class="avg-text">¥{{ formatNumber(record.avg_per_transaction) }}</span>
              </template>
              <template v-if="column.key === 'usage_percentage'">
                <div class="percentage-cell">
                  <span class="percentage-text">{{ getUsagePercentage(record.usage_count) }}%</span>
                  <a-progress 
                    :percent="getUsagePercentage(record.usage_count)" 
                    :show-info="false"
                    size="small"
                    stroke-color="#667eea"
                  />
                </div>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useExpenseStore } from '@/stores/expense'
import { Chart } from '@antv/g2'
import { formatNumber } from '@/utils/format'

const expenseStore = useExpenseStore()
const paymentChartRef = ref<HTMLElement>()

let paymentChart: Chart | null = null

// 计算属性
const topPaymentMethods = computed(() => 
  expenseStore.paymentMethods.slice(0, 8)
)

const totalUsageCount = computed(() => 
  expenseStore.paymentMethods.reduce((sum, method) => sum + method.usage_count, 0)
)

const columns = [
  {
    title: '支付账户',
    dataIndex: 'pay_account',
    key: 'pay_account',
    width: 200,
  },
  {
    title: '使用次数',
    dataIndex: 'usage_count',
    key: 'usage_count',
    align: 'center',
    width: 100,
  },
  {
    title: '总消费',
    dataIndex: 'total_spent',
    key: 'total_spent',
    align: 'right',
    width: 120,
  },
  {
    title: '平均消费',
    dataIndex: 'avg_per_transaction',
    key: 'avg_per_transaction',
    align: 'right',
    width: 120,
  },
  {
    title: '使用占比',
    key: 'usage_percentage',
    align: 'center',
    width: 150,
  },
]

// 工具函数
const formatAccountName = (account: string): string => {
  if (account.length > 15) {
    return account.substring(0, 12) + '...'
  }
  return account
}

const getUsagePercentage = (usageCount: number): number => {
  if (totalUsageCount.value === 0) return 0
  return Math.round((usageCount / totalUsageCount.value) * 100)
}

// 初始化图表
const initChart = () => {
  if (!paymentChartRef.value || !expenseStore.paymentMethods.length) return

  const data = expenseStore.paymentMethods.slice(0, 10)

  paymentChart = new Chart({
    container: paymentChartRef.value,
    autoFit: true,
    height: 400,
  })

  paymentChart
    .interval()
    .data(data)
    .encode('x', 'pay_account')
    .encode('y', 'total_spent')
    .encode('color', '#667eea')
    .scale('y', { nice: true })
    .axis('x', { 
      title: '支付账户',
      label: { autoRotate: true, autoHide: true }
    })
    .axis('y', { 
      title: '消费金额 (¥)',
      labelFormatter: (value: number) => `¥${(value / 1000).toFixed(0)}k`
    })
    .tooltip({
      items: [
        { name: '支付账户', field: 'pay_account' },
        { name: '总消费', field: 'total_spent', valueFormatter: (value: number) => `¥${formatNumber(value)}` },
        { name: '使用次数', field: 'usage_count' }
      ]
    })
    .animate({ enter: { type: 'scaleInY' } })

  paymentChart.render()
}

onMounted(async () => {
  if (!expenseStore.paymentMethods.length) {
    await expenseStore.fetchPaymentMethods()
  }
  
  setTimeout(initChart, 100)
})
</script>

<style scoped>
.payment-container {
  padding: 20px;
  min-height: calc(100vh - 64px);
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.chart-card, .stats-card, .table-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.chart-container {
  height: 400px;
  width: 100%;
}

.stats-list {
  padding: 16px 0;
}

.stat-item {
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.account-name {
  font-weight: 500;
  color: #262626;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.usage-count {
  font-size: 12px;
  color: #8c8c8c;
}

.stat-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.total-amount {
  font-size: 16px;
  font-weight: 600;
  color: #cf1322;
}

.avg-amount {
  font-size: 12px;
  color: #8c8c8c;
}

.table-section {
  margin-top: 24px;
}

.amount-text {
  font-weight: 600;
  color: #cf1322;
}

.avg-text {
  color: #1890ff;
}

.percentage-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.percentage-text {
  font-size: 12px;
  font-weight: 500;
  color: #667eea;
}

@media (max-width: 768px) {
  .payment-container {
    padding: 12px;
  }
  
  .chart-container {
    height: 300px;
  }
  
  .account-name {
    max-width: 150px;
  }
}
</style>