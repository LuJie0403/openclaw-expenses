# OpenClaw Expenses API 文档

## 🔗 基础信息
- **Base URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json`
- **字符编码**: UTF-8

## 📋 统一响应格式

所有API响应都遵循统一格式：

```json
{
  "code": 0,        // 响应代码：0=成功，其他=错误
  "message": "success",  // 响应消息
  "data": {},       // 响应数据
  "timestamp": "2024-01-01T12:00:00"  // 时间戳
}
```

## 🏥 健康检查

### GET /health
检查服务健康状态

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "healthy",
    "database": "connected",
    "timestamp": "2024-01-01T12:00:00",
    "service": "openclaw-expenses-api",
    "version": "1.0.0"
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

## 💰 支出管理

### GET /expenses
获取支出列表，支持过滤、分页、排序

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页条数，默认20，最大100 |
| start_date | string | 否 | 开始日期 (YYYY-MM-DD) |
| end_date | string | 否 | 结束日期 (YYYY-MM-DD) |
| category | string | 否 | 消费类别 |
| sub_category | string | 否 | 消费子类别 |
| pay_account | string | 否 | 支付账户 |
| min_amount | float | 否 | 最小金额 |
| max_amount | float | 否 | 最大金额 |
| sort_by | string | 否 | 排序字段，默认trans_datetime |
| sort_order | string | 否 | 排序方向 (asc/desc)，默认desc |

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/expenses?page=1&page_size=10&start_date=2024-01-01&end_date=2024-12-31&category=住"
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "trans_datetime": "2024-01-15 14:30:00",
        "trans_year": "2024",
        "trans_month": "2024-01",
        "trans_date": "2024-01-15",
        "trans_time": "14:30:00",
        "trans_amount": 21000.0,
        "trans_event": "房租支付",
        "product_desc": "月度房租",
        "pay_type": "支出",
        "pay_account": "招商银行信用卡(4933)",
        "bill_remark": "1月份房租",
        "trans_type_name": "住",
        "trans_sub_type_name": "房租"
      }
    ],
    "total": 3913,
    "page": 1,
    "page_size": 10,
    "total_pages": 392
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

### GET /expenses/summary
获取支出总览统计

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/expenses/summary"
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_amount": 589443.66,
    "total_count": 3913,
    "avg_amount": 150.89,
    "earliest_date": "2023-01-02",
    "latest_date": "2025-12-31"
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

### GET /expenses/categories
获取支出分类统计

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/expenses/categories"
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "trans_type_name": "住",
      "trans_sub_type_name": "房租",
      "count": 12,
      "total_amount": 252000.0,
      "avg_amount": 21000.0
    },
    {
      "trans_type_name": "食",
      "trans_sub_type_name": "早午晚餐",
      "count": 1353,
      "total_amount": 41146.19,
      "avg_amount": 30.41
    }
  ],
  "timestamp": "2024-01-01T12:00:00"
}
```

### GET /expenses/monthly
获取月度支出统计

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/expenses/monthly"
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "year": "2025",
      "month": "2025-12",
      "transaction_count": 94,
      "monthly_total": 10028.64,
      "avg_transaction": 106.69
    },
    {
      "year": "2025",
      "month": "2025-11",
      "transaction_count": 81,
      "monthly_total": 5464.36,
      "avg_transaction": 67.46
    }
  ],
  "timestamp": "2024-01-01T12:00:00"
}
```

### GET /expenses/payment-methods
获取支付方式统计

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/expenses/payment-methods"
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "pay_account": "招商银行信用卡(4933)",
      "usage_count": 1094,
      "total_spent": 98665.01,
      "avg_per_transaction": 90.19
    },
    {
      "pay_account": "浦发银行信用卡(0187)",
      "usage_count": 666,
      "total_spent": 32898.23,
      "avg_per_transaction": 49.40
    }
  ],
  "timestamp": "2024-01-01T12:00:00"
}
```

### GET /expenses/timeline
获取支出时间线数据

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/expenses/timeline"
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "date": "2025-12-31",
      "daily_total": 500.0,
      "transaction_count": 5
    },
    {
      "date": "2025-12-30",
      "daily_total": 1234.56,
      "transaction_count": 8
    }
  ],
  "timestamp": "2024-01-01T12:00:00"
}
```

## ❗ 错误处理

### 标准错误响应
```json
{
  "code": 1,
  "message": "错误描述",
  "data": null,
  "timestamp": "2024-01-01T12:00:00"
}
```

### 常见错误码
| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1 | 通用错误 |
| 400 | 请求参数错误 |
| 404 | 资源未找到 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

## 🔒 安全认证

当前版本为公开API，无需认证。生产环境建议添加：
- API Key认证
- JWT Token认证
- 请求频率限制

## 📊 数据模型

### 支出记录 (Expense)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键ID |
| trans_datetime | datetime | 交易时间 |
| trans_year | varchar | 交易年份 |
| trans_month | varchar | 交易月份 |
| trans_date | varchar | 交易日期 |
| trans_time | varchar | 交易时间 |
| trans_amount | double | 交易金额 |
| trans_event | varchar | 交易事件 |
| product_desc | varchar | 商品描述 |
| pay_type | varchar | 支付类型 |
| pay_account | varchar | 支付账户 |
| bill_remark | varchar | 备注 |
| trans_type_name | varchar | 消费类别 |
| trans_sub_type_name | varchar | 消费子类别 |

## 🧪 测试示例

### 基础测试
```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 获取总览
curl http://localhost:8000/api/v1/expenses/summary

# 获取分类统计
curl http://localhost:8000/api/v1/expenses/categories
```

### 高级查询
```bash
# 查询2024年餐饮支出，按金额降序
curl "http://localhost:8000/api/v1/expenses?start_date=2024-01-01&end_date=2024-12-31&category=食&sort_by=trans_amount&sort_order=desc"

# 查询特定支付方式的使用情况
curl "http://localhost:8000/api/v1/expenses?pay_account=招商银行信用卡(4933)&page_size=50"
```

---

**📖 API版本**: v1.0.0  
**📝 文档更新**: 2026-02-05  
**👨‍💻 维护者**: AI Assistant for 路杰