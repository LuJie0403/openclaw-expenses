<template>
  <a-table
    :columns="tableColumns"
    :data-source="dataSource"
    :pagination="paginationConfig"
    :row-key="rowKey"
    @change="handleTableChange"
  >
    <template #bodyCell="{ column, record, index }">
      <template v-if="column.key === INDEX_COLUMN_KEY">
        {{ index + 1 }}
      </template>

      <template v-else-if="column.key === RATIO_COLUMN_KEY">
        <div class="percentage-cell">
          <span class="percentage-text">{{ getRatioPercent(record) }}%</span>
          <a-progress
            :percent="getRatioPercent(record)"
            :show-info="false"
            size="small"
            :stroke-color="ratioColor"
          />
        </div>
      </template>

      <template v-else>
        <span :class="getCellClass(column.key)">
          {{ resolveCellText(column.key, record) }}
        </span>
      </template>
    </template>
  </a-table>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import { formatAmount } from '@/utils/format'

type Primitive = string | number | boolean | null | undefined
type RowRecord = Record<string, Primitive>

type RowKey = string | ((record: RowRecord) => string)

interface DetailColumn {
  title: string
  key: string
  dataIndex: string
  width?: number
  align?: 'left' | 'center' | 'right'
  valueType?: 'text' | 'number' | 'currency'
  tone?: 'default' | 'danger' | 'info'
  sortable?: boolean
}

interface RatioConfig {
  title?: string
  valueKey: string
  color?: string
}

interface PaginationInfo {
  current?: number
  pageSize?: number
}

const INDEX_COLUMN_KEY = '__row_index__'
const RATIO_COLUMN_KEY = '__usage_ratio__'

const props = defineProps<{
  columns: DetailColumn[]
  dataSource: RowRecord[]
  rowKey: RowKey
  ratio?: RatioConfig
}>()

const paginationState = reactive({
  current: 1,
  pageSize: 10,
  showSizeChanger: true,
  pageSizeOptions: ['10', '20', '50', '100'],
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) =>
    `第 ${range[0]}-${range[1]} 条 / 共 ${total} 条`,
})

const ratioColor = computed(() => props.ratio?.color || '#667eea')

const ratioTotal = computed(() => {
  if (!props.ratio) return 0
  return props.dataSource.reduce((sum, row) => sum + toNumber(row[props.ratio!.valueKey]), 0)
})

const tableColumns = computed(() => {
  const indexColumn = {
    title: '#',
    key: INDEX_COLUMN_KEY,
    width: 70,
    align: 'center' as const,
  }

  const sortableBusinessColumns = props.columns.map((column) => ({
    ...column,
    sorter:
      column.sortable === false
        ? false
        : (left: RowRecord, right: RowRecord) =>
            compareValues(left[column.dataIndex], right[column.dataIndex]),
    sortDirections: ['descend', 'ascend'],
  }))

  const columns = [indexColumn, ...sortableBusinessColumns]

  if (props.ratio) {
    columns.push({
      title: props.ratio.title || '使用占比',
      key: RATIO_COLUMN_KEY,
      width: 180,
      align: 'center' as const,
      sorter: (left: RowRecord, right: RowRecord) =>
        getRatioPercent(left) - getRatioPercent(right),
      sortDirections: ['descend', 'ascend'],
    })
  }

  return columns
})

const paginationConfig = computed(() => ({
  ...paginationState,
  total: props.dataSource.length,
}))

const handleTableChange = (pagination: PaginationInfo): void => {
  paginationState.current = pagination.current || 1
  paginationState.pageSize = pagination.pageSize || paginationState.pageSize
}

const getColumnByKey = (key: string): DetailColumn | undefined =>
  props.columns.find((column) => column.key === key)

const toNumber = (value: Primitive): number => {
  const parsed = Number(value ?? 0)
  return Number.isFinite(parsed) ? parsed : 0
}

const compareValues = (left: Primitive, right: Primitive): number => {
  const leftNumber = Number(left)
  const rightNumber = Number(right)
  const bothNumeric = Number.isFinite(leftNumber) && Number.isFinite(rightNumber)
  if (bothNumeric) return leftNumber - rightNumber
  return String(left ?? '').localeCompare(String(right ?? ''), 'zh-Hans-CN')
}

const getRatioPercent = (record: RowRecord): number => {
  if (!props.ratio) return 0
  const total = ratioTotal.value
  if (total <= 0) return 0
  return Math.round((toNumber(record[props.ratio.valueKey]) / total) * 100)
}

const resolveCellText = (columnKey: string, record: RowRecord): string => {
  const column = getColumnByKey(columnKey)
  if (!column) return '-'

  const rawValue = record[column.dataIndex]
  if (column.valueType === 'currency') return `¥${formatAmount(toNumber(rawValue))}`
  if (column.valueType === 'number') return `${toNumber(rawValue)}`
  return String(rawValue ?? '-')
}

const getCellClass = (columnKey: string): string => {
  const column = getColumnByKey(columnKey)
  if (!column || column.valueType !== 'currency') return ''
  if (column.tone === 'info') return 'avg-text'
  if (column.tone === 'danger') return 'amount-text'
  return ''
}
</script>

<style scoped>
.amount-text {
  font-weight: 600;
  color: #ff4d4f;
}

.avg-text {
  color: #40a9ff;
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
</style>
