// 格式化工具函数
export function formatNumber(num: number, decimals: number = 0): string {
  const safeNum = Number.isFinite(num) ? num : 0
  return safeNum.toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

export function formatAmount(num: number): string {
  return formatNumber(num, 2)
}

export function formatCurrency(num: number): string {
  return '¥' + formatAmount(num)
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

export function formatMonth(monthStr: string): string {
  const [year, month] = monthStr.split('-')
  return `${year}年${parseInt(month)}月`
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      func(...args)
    }
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}
