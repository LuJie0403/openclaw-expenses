<template>
  <div class="payment-container">
    <a-row :gutter="24" style="display: flex; align-items: stretch;">
      <!-- 支付方式总览 -->
      <a-col :xs="24" :lg="16">
        <a-card title="支付方式分析" class="chart-card" style="height: 100%;">
          <div ref="paymentChartRef" class="chart-container"></div>
        </a-card>
      </a-col>
      
      <!-- 支付统计 -->
      <a-col :xs="24" :lg="8">
        <a-card title="支付统计" class="stats-card" style="height: 100%;">
          <template #extra>
            <a-button v-if="expenseStore.paymentMethods.length > 4" type="link" @click="toggleShowAll">
              {{ showAll ? '收起' : '展开更多' }}
            </a-button>
          </template>
          <div class="stats-list">
            <div v-for="method in displayedMethods" :key="method.pay_account" class="stat-item">
              <div class="stat-header">
                <span class="account-name">{{ formatAccountName(method.pay_account) }}</span>
                <span class="total-amount">¥{{ formatAmount(method.total_spent) }}</span>
              </div>
              <div class="stat-detail">
                <span class="usage-count">{{ method.usage_count }}笔 / 平均¥{{ formatAmount(method.avg_per_transaction) }}</span>
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
          <DetailDataTable
            :columns="paymentDetailColumns"
            :data-source="expenseStore.paymentMethods"
            :row-key="'pay_account'"
            :ratio="{ title: '使用占比', valueKey: 'usage_count', color: '#667eea' }"
          />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useExpenseStore } from '@/stores/expense'
import { Chart } from '@antv/g2'
import { formatAmount } from '@/utils/format'
import DetailDataTable from '@/components/DetailDataTable.vue'

type DetailColumn = {
  title: string
  key: string
  dataIndex: string
  width?: number
  align?: 'left' | 'center' | 'right'
  valueType?: 'text' | 'number' | 'currency'
  tone?: 'default' | 'danger' | 'info'
}

const expenseStore = useExpenseStore()
const paymentChartRef = ref<HTMLElement>()
const showAll = ref(false)

let paymentChart: Chart | null = null

const displayedMethods = computed(() => 
  showAll.value ? expenseStore.paymentMethods : expenseStore.paymentMethods.slice(0, 4)
)

const toggleShowAll = () => {
  showAll.value = !showAll.value
}

const totalUsageCount = computed(() => 
  expenseStore.paymentMethods.reduce((sum, method) => sum + method.usage_count, 0)
)

const paymentDetailColumns: DetailColumn[] = [
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
    valueType: 'number',
    align: 'center',
    width: 100,
  },
  {
    title: '总消费（元）',
    dataIndex: 'total_spent',
    key: 'total_spent',
    valueType: 'currency',
    tone: 'danger',
    align: 'right',
    width: 120,
  },
  {
    title: '平均消费（元）',
    dataIndex: 'avg_per_transaction',
    key: 'avg_per_transaction',
    valueType: 'currency',
    tone: 'info',
    align: 'right',
    width: 120,
  },
]

const formatAccountName = (account: string): string => {
  if (account.length > 15) return account.substring(0, 12) + '...';
  return account;
}

const getUsagePercentage = (usageCount: number): number => {
  if (totalUsageCount.value === 0) return 0;
  return Math.round((usageCount / totalUsageCount.value) * 100);
}

const initChart = () => {
  if (!paymentChartRef.value || !expenseStore.paymentMethods.length) return

  const data = expenseStore.paymentMethods.slice(0, 10)

  paymentChart = new Chart({
    container: paymentChartRef.value,
    autoFit: true,
    height: 400,
  })
  
  paymentChart.theme({ type: 'classicDark' });

  paymentChart
    .interval()
    .data(data)
    .encode('x', 'pay_account')
    .encode('y', 'total_spent')
    .encode('color', '#667eea')
    .scale('y', { nice: true })
    .axis('x', { title: '支付账户', label: { autoRotate: true, autoHide: true } })
    .axis('y', { title: '消费金额（元）', labelFormatter: (value: number) => `¥${formatAmount(value)}` })
    .tooltip({
      items: [
        { name: '支付账户', field: 'pay_account' },
        { name: '总消费', field: 'total_spent', valueFormatter: (value: number) => `¥${formatAmount(value)}` },
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

onUnmounted(() => {
  if (paymentChart) {
    paymentChart.destroy()
    paymentChart = null
  }
})
</script>

<style scoped>
.payment-container {
  padding: 20px;
  min-height: calc(100vh - 64px);
}

.chart-card, .stats-card, .table-card {
  background: rgba(25, 25, 25, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid #333;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  margin-bottom: 24px;
}

.chart-container {
  height: 400px;
  width: 100%;
}

.stats-list {
  padding: 8px 0;
}

.stat-item {
  padding: 12px 0;
  border-bottom: 1px solid #333;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.account-name {
  font-weight: 500;
  color: #fff;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.total-amount {
  font-size: 14px;
  font-weight: 600;
  color: #ff4d4f;
}

.stat-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #aaa;
}

.table-section {
  margin-top: 24px;
}

@media (max-width: 768px) {
  .payment-container {
    padding: 12px;
  }
  
  .chart-container {
    height: 300px;
  }
}
</style>
