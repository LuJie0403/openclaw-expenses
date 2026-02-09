# OpenClaw Expenses 统一设计文档

## 1. 目标与范围
本设计文档以当前仓库实现为准，整合后端、前端、数据模型、部署配置与已知差异，确保描述与代码一致，便于维护与交接。

## 2. 系统概览
系统由三部分组成：
- **前端**：Vue 3 + Vite + TypeScript + Ant Design Vue，可视化展示支出数据与登录状态管理。
- **后端**：FastAPI + PyMySQL，提供认证与支出统计接口，使用 JWT 作为访问凭证。
- **部署层**：Nginx 托管前端静态文件并反向代理后端 API（仓库提供参考配置）。

## 3. 运行入口与工程结构
### 3.1 后端入口
当前仓库存在两套后端入口：
- **默认启动脚本使用** `backend/main_v2.py`（见 `backend/start.sh`），此入口包含认证与支出统计 API 的实现，并启用了 CORS 中间件。
- **模块化重构版** 位于 `backend/app/main.py`，将认证与支出模块拆分在 `backend/app/auth` 与 `backend/app/expenses` 中，但尚未在启动脚本中启用。

### 3.2 前端入口
前端入口为 `frontend/src/main.ts`，路由与页面在 `frontend/src/router` 与 `frontend/src/views`。

## 4. 后端设计

### 4.1 API 前缀与路由
后端 API 统一使用 `/api` 前缀（`backend/main_v2.py` 和 `backend/app/main.py` 均如此）。当前已实现的接口如下：

**认证接口**
- `POST /api/auth/login`：验证用户名与密码，返回 JWT。
- `GET /api/auth/me`：解析 JWT 并返回当前用户信息。

**支出统计接口**
- `GET /api/expenses/summary`：总金额、总笔数、平均金额、时间范围。
- `GET /api/expenses/monthly`：按月汇总。
- `GET /api/expenses/categories`：按类别/子类别聚合。
- `GET /api/expenses/payment-methods`：支付方式汇总。
- `GET /api/expenses/timeline`：按日期聚合的时间线数据。

### 4.2 认证与安全
- **JWT**：使用 `SECRET_KEY`、`ALGORITHM`、`ACCESS_TOKEN_EXPIRE_MINUTES` 配置生成与校验。
- **密码哈希**：`bcrypt`，并对明文密码进行 72 字符截断以规避算法限制。
- **Token 传递方式**：前端通过 `Authorization: Bearer <token>` 传递。

### 4.3 配置与依赖
当前有两套配置读取方式：
- `backend/main_v2.py` 使用 `backend/config.py`（`dotenv` + `os.getenv`）。
- `backend/app/main.py` 使用 `backend/app/core/config.py`（`pydantic_settings`）。

两套配置均提供数据库连接与 JWT 配置，但字段默认值不同，使用时需确保与实际入口一致。

### 4.4 数据访问层
后端通过 `pymysql` 创建数据库连接，并统一使用 `DictCursor` 返回字典数据。

### 4.5 数据表与字段（基于 SQL 实际使用字段）
**expenses_user**
- `id`, `username`, `email`, `hashed_password`, `full_name`, `is_active`, `created_at`

**personal_expenses_final**
- `id`, `created_by`, `trans_amount`, `trans_datetime`, `trans_date`, `trans_year`, `trans_month`, `pay_account`, `trans_code`, `trans_sub_code`

**personal_expenses_type**
- `trans_code`, `trans_sub_code`, `trans_type_name`, `trans_sub_type_name`

所有支出统计均基于 `created_by` 进行用户级过滤。

## 5. 前端设计

### 5.1 技术栈
- Vue 3 + Vite + TypeScript
- Ant Design Vue
- Pinia（状态管理）
- Axios（HTTP）

### 5.2 路由与鉴权
路由配置在 `frontend/src/router/index.ts`：
- `/login`：登录页（访客可访问）。
- `/dashboard`、`/categories`、`/timeline`、`/payment`：需要认证。

路由守卫会在未登录时跳转至登录页，并阻止已登录用户再次访问 `/login`。

### 5.3 认证状态
`frontend/src/stores/auth.ts` 负责：
- 登录后保存 token 到 `localStorage`。
- 调用 `/auth/me` 获取用户信息。
- 401 时清理 token 并跳转登录页。

### 5.4 API 访问
`frontend/src/services/api.ts`：
- 生产环境 baseURL 为 `/api`。
- 开发环境 baseURL 为 `http://localhost:8000`。
- 统一请求拦截器附加 `Authorization`。
- 统一响应拦截器处理 401 重定向。

## 6. 部署与反向代理
仓库内提供 `nginx.conf` 示例，用于静态资源与 API 反向代理。需要注意：
- `nginx.conf` 目前将 `/auth/` 与 `/expenses/` 直接反向代理到后端，但后端实际路由前缀是 `/api`。
- 若按示例部署，需调整 Nginx 路由或后端前缀以保持一致。

## 7. 已知差异与待完善项
- 前端定义了 `healthCheck` API 方法，但后端未实现 `/health` 路由。
- 旧文档中提到的 `/api/v1` 前缀与“支出列表分页/过滤”接口在当前代码中不存在。
- 统一响应包装（如 `{ code, message, data, timestamp }`）未在当前后端实现，返回内容为原始数据结构。
