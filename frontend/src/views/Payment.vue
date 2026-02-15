<template>
  <!-- (Template remains largely the same, only columns and pagination in script are changed) -->
  <div class="payment-container">
    <!-- ... chart ... -->
    <a-card title="支付方式详情" class="table-card">
      <a-table :columns="paymentColumns" :data-source="expenseStore.paymentMethods" :pagination="paginationConfig" @change="handleTableChange">
        <!-- ... cell templates ... -->
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useExpenseStore } from '@/stores/expense';
// ... other imports

const expenseStore = useExpenseStore();

// Pagination and Sorting state
const paginationConfig = ref({
  pageSize: 10,
  current: 1,
  pageSizeOptions: ['5', '10', '15', '20', '50', '100'],
  showSizeChanger: true,
  showQuickJumper: true,
  total: computed(() => expenseStore.paymentMethods.length),
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条 / 共 ${total} 条`,
});

const paymentColumns = [
  { title: '#', key: 'rowIndex', customRender: ({ index }) => `${(paginationConfig.value.current - 1) * paginationConfig.value.pageSize + index + 1}` },
  { title: '支付账户', dataIndex: 'pay_account', sorter: (a, b) => a.pay_account.localeCompare(b.pay_account) },
  { title: '使用次数', dataIndex: 'usage_count', sorter: (a, b) => a.usage_count - b.usage_count, defaultSortOrder: 'descend' },
  { title: '总消费', dataIndex: 'total_spent', sorter: (a, b) => a.total_spent - b.total_spent },
  { title: '平均消费', dataIndex: 'avg_per_transaction', sorter: (a, b) => a.avg_per_transaction - b.avg_per_transaction },
  // ... other columns
];

const handleTableChange = (pagination, filters, sorter) => {
  paginationConfig.value = pagination;
  // Logic to handle server-side sorting if needed in future
};


onMounted(async () => {
  if (!expenseStore.paymentMethods.length) {
    await expenseStore.fetchPaymentMethods();
  }
  // ... init chart
});

</script>

<style scoped>
/* ... styles ... */
</style>
