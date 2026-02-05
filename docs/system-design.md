# 📊 OpenClaw Expenses - 个人支出可视化看板

## 🎯 项目概述

OpenClaw Expenses 是一个现代化的个人支出数据可视化看板，基于3年完整财务数据（3,913笔交易，总金额589,443元），提供多维度、交互式的支出分析体验。

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端 (Vue3 + TypeScript)                 │
├─────────────────────────────────────────────────────────────┤
│  • 响应式H5设计              • AntV G2图表可视化           │
│  • Pinia状态管理             • 移动端优化                  │
│  • TypeScript类型安全        • 多主题适配                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              API网关 (RESTful + JSON)                      │
├─────────────────────────────────────────────────────────────┤
│  • /api/v1/expenses          • 统一响应格式               │
│  • /api/v1/expenses/summary  • 分页、过滤、排序           │
│  • /api/v1/expenses/categories• HATEOAS支持               │
│  • /api/v1/health            • 标准化错误处理            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              后端 (Python3 + FastAPI)                      │
├─────────────────────────────────────────────────────────────┤
│  • RESTful API设计           • 异步数据库操作             │
│  • 连接池管理                • 数据验证和清洗             │
│  • 环境配置隔离              • 错误处理和日志             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                MySQL数据库 (阿里云)                         │
├─────────────────────────────────────────────────────────────┤
│  • personal_expenses_final   • 3,913笔交易记录             │
│  • personal_expenses_type    • 2023-2025完整数据           │
│  • 索引优化                  • 事务完整性保证              │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 技术栈

### 后端技术栈
- **框架**: FastAPI (Python 3.x)
- **数据库**: PyMySQL + MySQL 8.0
- **配置**: python-dotenv
- **部署**: Uvicorn + Gunicorn

### 前端技术栈
- **框架**: Vue 3 + TypeScript + Vite
- **UI组件**: Ant Design Vue 4.x
- **图表库**: AntV G2 / G2Plot (蚂蚁集团开源)
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios

### 部署架构
- **服务器**: 阿里云ECS
- **反向代理**: Nginx
- **进程管理**: PM2
- **域名**: 待配置
- **HTTPS**: SSL证书

## 📋 RESTful API设计

### 统一响应格式
```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "timestamp": "2024-01-01T12:00:00"
}
```

### 核心端点

#### 1. 健康检查
```
GET /api/v1/health
Response: {
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-01T12:00:00"
}
```

#### 2. 获取支出列表（支持过滤、分页、排序）
```
GET /api/v1/expenses
Query Parameters:
  - page: 页码 (默认1)
  - page_size: 每页条数 (默认20, 最大100)
  - start_date: 开始日期 (YYYY-MM-DD)
  - end_date: 结束日期 (YYYY-MM-DD)
  - category: 消费类别
  - sub_category: 消费子类别
  - pay_account: 支付账户
  - min_amount: 最小金额
  - max_amount: 最大金额
  - sort_by: 排序字段 (默认trans_datetime)
  - sort_order: 排序方向 (asc/desc, 默认desc)

Response: {
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### 3. 支出总览统计
```
GET /api/v1/expenses/summary
Response: {
  "total_amount": 589443.66,
  "total_count": 3913,
  "avg_amount": 150.89,
  "earliest_date": "2023-01-02",
  "latest_date": "2025-12-31"
}
```

#### 4. 分类支出统计
```
GET /api/v1/expenses/categories
Response: [{
  "trans_type_name": "住",
  "trans_sub_type_name": "房租",
  "count": 12,
  "total_amount": 252000.0,
  "avg_amount": 21000.0
}]
```

#### 5. 月度支出统计
```
GET /api/v1/expenses/monthly
Response: [{
  "year": "2025",
  "month": "2025-12",
  "transaction_count": 94,
  "monthly_total": 10028.64,
  "avg_transaction": 106.69
}]
```

#### 6. 支付方式统计
```
GET /api/v1/expenses/payment-methods
Response: [{
  "pay_account": "招商银行信用卡(4933)",
  "usage_count": 1094,
  "total_spent": 98665.01,
  "avg_per_transaction": 90.19
}]
```

#### 7. 支出时间线
```
GET /api/v1/expenses/timeline
Response: [{
  "date": "2025-12-31",
  "daily_total": 500.0,
  "transaction_count": 5
}]
```

## 📊 数据可视化设计

### 核心图表组件

#### 1. 支出总览卡片
- **总支出金额**: 大字体突出显示
- **交易笔数**: 累计交易统计
- **平均金额**: 单笔消费均值
- **时间跨度**: 数据覆盖范围

#### 2. 月度趋势图 (Line Chart)
- **X轴**: 时间（年月）
- **Y轴**: 支出金额
- **数据点**: 每月总支出、平均支出
- **交互**: 悬停显示详情，点击切换年份

#### 3. 分类占比图 (Pie Chart + TreeMap)
- **主分类**: 住、食、金融服务、家庭、出行等
- **子分类**: 房租、餐饮、社保、孝敬父母等
- **双重展示**: 饼图显示占比，树图显示金额层次

#### 4. 支付方式分析 (Bar Chart + Radar)
- **使用频次**: 各信用卡/储蓄卡使用次数
- **消费金额**: 各支付方式总支出
- **平均消费**: 单笔交易均值分析

#### 5. 时间线热力图 (Heatmap + Calendar)
- **日消费热力图**: 颜色深浅表示消费金额
- **周模式分析**: 工作日vs周末消费模式
- **节假日标注**: 特殊日期消费高峰

### 移动端H5优化
- **触摸手势**: 滑动切换图表，捏合缩放
- **响应式布局**: 自适应不同屏幕尺寸
- **性能优化**: 懒加载，虚拟滚动
- **离线缓存**: PWA支持，弱网环境可用

## 🔐 安全与隐私

### 环境配置隔离
```bash
# 开发环境
.env.development
DB_HOST=120.27.250.73
DB_PASSWORD=9!wQSw@12sq

# 生产环境
.env.production
DB_HOST=${DB_HOST}
DB_PASSWORD=${DB_PASSWORD}
```

### GitHub安全策略
- `.env*` 文件加入`.gitignore`
- 提供`.env.example`模板文件
- GitHub Actions部署时注入密钥
- 敏感信息绝不提交到代码仓库

## 🚀 部署方案

### 开发环境
```bash
# 后端启动
cd backend
source venv/bin/activate
./start.sh

# 前端启动  
cd frontend
npm install
npm run dev
```

### 生产环境
```bash
# Docker容器化
docker-compose up -d

# 或者手动部署
# 1. 构建前端
npm run build

# 2. 配置Nginx
# 3. 启动后端服务
# 4. 配置SSL证书
```

## 📈 性能优化

### 后端优化
- **数据库连接池**: 减少连接开销
- **查询优化**: 索引优化，避免N+1查询
- **缓存策略**: Redis缓存热点数据
- **异步处理**: 非阻塞IO操作

### 前端优化
- **代码分割**: 路由懒加载
- **图片优化**: WebP格式，懒加载
- **CDN加速**: 静态资源全球分发
- **压缩传输**: Gzip/Brotli压缩

## 🎯 数据洞察亮点

基于3913笔交易数据的深度分析：

### 核心发现
- **总支出**: 589,443元 (2023-2025)
- **最大支出**: 住房成本 252,000元 (42.8%)
- **最活跃**: 餐饮支出 1,353笔交易
- **支付偏好**: 招商银行信用卡主力使用

### 消费模式
- **住房**: 21,000元/月平均房租
- **餐饮**: 30.4元/笔平均消费
- **金融**: 49,151元社保和税款
- **家庭**: 35,358元孝敬和红包

### 财务健康度
- ✅ 支出多元化，结构合理
- ✅ 支付工具管理得当
- ✅ 有稳定储蓄投资行为
- ⚠️ 住房成本占比略高但可控

## 🔮 后续迭代计划

### Phase 2: 数据导入功能
- CSV文件上传导入
- 数据清洗和验证
- 批量数据管理

### Phase 3: 智能分析
- AI消费趋势预测
- 异常消费检测
- 理财建议生成

### Phase 4: 移动端App
- React Native跨平台
- 离线数据支持
- 推送通知提醒

---

**📝 设计完成时间**: 2026-02-05
**👨‍💻 设计者**: AI Assistant for 路杰
**🎯 目标**: 打造专业级个人财务管理工具