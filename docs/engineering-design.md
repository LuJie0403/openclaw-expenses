# OpenClaw Expenses 设计文档（代码分析版）

## 1. 目标与范围

本设计文档基于当前代码实现进行分析，覆盖系统的后端 API、前端界面、数据流、配置与部署方式。目标是为维护者提供架构与模块职责的整体认知，并明确关键接口与数据模型。

## 2. 总体架构概览

系统由三部分组成：

- **前端**：Vue 3 + Vite + Ant Design Vue，用于展示支出统计、分类、时间线等数据，并处理登录流程。
- **后端**：FastAPI 提供认证与支出数据 API，以 MySQL 作为数据存储。
- **部署层**：Nginx 托管前端静态资源，并反向代理后端 API。

## 3. 后端设计

### 3.1 入口与应用结构

- FastAPI 应用位于 `backend/app/main.py`，配置了项目名称与版本，并挂载认证和支出模块路由（统一 `/api` 前缀）。
- 配置与安全相关逻辑在 `backend/app/core` 目录下，包括数据库连接、JWT 与密码加密。

### 3.2 配置管理（core.config）

- 使用 `pydantic_settings.BaseSettings` 读取环境变量。
- 配置项包括数据库连接参数、JWT 密钥/算法/过期时间、项目元信息等。

### 3.3 数据库访问（core.database）

- 使用 `pymysql` 直接创建连接。
- 默认使用 `DictCursor` 返回字典型结果，便于路由层序列化。

### 3.4 安全与认证（core.security + auth 模块）

- **密码处理**：基于 `passlib` 的 bcrypt，且对明文密码做长度截断（bcrypt 72 字符限制）。
- **JWT**：`create_access_token` 生成带 `exp` 的 token；认证接口对 token 解码并验证。
- **认证流程**：
  1. `/auth/login` 接口验证用户名密码。
  2. 登录成功返回 access token。
  3. 业务接口依赖 `read_users_me` 解析 token 获取用户信息。

### 3.5 认证模块（auth）

- `auth/service.py` 负责用户查询与验证：
  - `get_user_by_username` 查询 `expenses_user` 表返回用户信息。
  - `authenticate_user` 校验密码。
- `auth/router.py` 提供 `login` 与 `me` 两个端点。

### 3.6 支出模块（expenses）

- `expenses/router.py` 提供 5 个 API：摘要、月度、分类、支付方式、时间线。
- `expenses/service.py` 通过 SQL 查询聚合数据，涉及表：
  - `personal_expenses_final`（交易明细）
  - `personal_expenses_type`（交易类型/子类型）

## 4. 前端设计

### 4.1 技术栈与工程结构

- 框架：Vue 3 + Vite + TypeScript
- 组件库：Ant Design Vue
- 图表：AntV G2
- 状态管理：Pinia
- 网络请求：Axios

### 4.2 路由与权限

- `frontend/src/router/index.ts` 定义路由和导航守卫。
- 路由元信息 `requiresAuth` 控制是否需要登录；`guest` 表示登录页。
- `beforeEach` 中若未登录则跳转 `/login`。

### 4.3 登录与认证状态

- `stores/auth.ts` 管理 token 与用户信息。
- 登录成功后保存 token，并调用 `/auth/me` 获取用户信息。
- Axios 拦截器会在请求头附加 `Authorization: Bearer <token>`，并在 401 时清除 token。 

### 4.4 主要页面与数据可视化

- `Dashboard.vue`：统计卡片 + 月度趋势 + 分类占比 + 支付方式 + 日支出热力图。
- `Categories.vue`、`Timeline.vue`、`Payment.vue`：分别聚焦分类、时间线、支付方式。

### 4.5 API 服务层

- `services/api.ts` 提供 `expenseAPI` 封装，统一调用后端接口。
- 在生产环境默认使用 `/api` 作为 baseURL。

## 5. 主要 API 与数据模型

### 5.1 认证接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/login` | 用户登录，返回 JWT |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 5.2 支出接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/expenses/summary` | 总支出/笔数/平均值/时间范围 |
| GET | `/api/expenses/monthly` | 月度趋势 |
| GET | `/api/expenses/categories` | 分类聚合 |
| GET | `/api/expenses/payment-methods` | 支付方式统计 |
| GET | `/api/expenses/timeline` | 日级时间线 |

### 5.3 数据字段（示例）

- `ExpenseSummary`：`total_amount`, `total_count`, `avg_amount`, `earliest_date`, `latest_date`
- `MonthlyExpense`：`year`, `month`, `transaction_count`, `monthly_total`, `avg_transaction`
- `CategoryExpense`：`trans_type_name`, `trans_sub_type_name`, `count`, `total_amount`, `avg_amount`
- `PaymentMethod`：`pay_account`, `usage_count`, `total_spent`, `avg_per_transaction`
- `TimelineData`：`date`, `daily_total`, `transaction_count`

## 6. 数据库设计（基于 SQL 访问推断）

- `expenses_user`：存储用户账号、密码哈希、邮箱、状态等。
- `personal_expenses_final`：存储交易记录、交易金额、交易日期、支付账户等。
- `personal_expenses_type`：存储交易类型与子类型。

> 说明：本节为根据服务层 SQL 推导出的数据表说明，字段以代码中使用到的为准。

## 7. 安全性与异常处理

- 密码加密采用 bcrypt，并处理过长密码截断。
- JWT 作为认证机制，`read_users_me` 中对 token 解析失败或 payload 不完整直接返回 401。
- API 端未统一异常处理器，当前错误由 FastAPI 默认异常返回。

## 8. 部署与运行

### 8.1 前端

- `npm run build` 生成 `dist/` 静态资源。
- Nginx 配置使用 `try_files` 支持前端路由。

### 8.2 后端

- 使用 Uvicorn 启动 FastAPI。
- 生产配置通过 `.env` 或环境变量覆盖。

### 8.3 Nginx 反向代理

- `/auth/` 与 `/expenses/` 代理至后端服务。
- `/docs` 与 `/openapi.json` 代理到 FastAPI 文档。

## 9. 可维护性建议

- 建议统一后端 API 前缀（当前后端路由 `/api/*`，Nginx 代理 `/auth`/`/expenses` 需保持一致）。
- 可在后端增加健康检查 `/health` 接口，便于部署与监控。
- 可增加统一日志与错误处理，提高排障效率。
