# OpenClaw Expenses

OpenClaw Expenses（钱呢）是一个前后端分离的消费数据分析系统，支持登录鉴权、消费总览、分类分析、支付方式分析、时间洞察与消费星辰可视化。

本文档基于当前仓库代码（`backend/app/**` + `frontend/src/**`）整理。

## 当前代码主链路

- 后端真实入口：`backend/app/main.py`（`FastAPI` + `/api/*` 路由）
- 前端真实入口：`frontend/src/main.ts`（`Vue 3 + Pinia + Router`）
- 部署脚本：`full-deploy.sh`（全量部署）、`update-deploy.sh`（更新并重部署）
- 健康检查：`GET /health`、`GET /api/health`

> 说明：已清理历史 `auth_*.py` 与冗余 `requirements-*.txt`。`backend/` 根目录仍保留 `main.py`、`config.py` 等过渡文件；当前生产主路径以 `backend/app` 为准。

## 核心能力

- JWT 认证：登录获取 token，接口通过 `Bearer Token` 鉴权。
- 数据总览：总支出、交易笔数、平均消费、最早/最晚日期。
- 多维分析：月度趋势、分类占比（饼图/矩形树图）、支付方式、时间线洞察。
- 可视化：Dashboard、Timeline、Stardust 页面分别采用 G2/ECharts。
- 明细表复用：`DetailDataTable` 统一排序、分页、占比进度条与金额格式。

## 技术栈

- 后端：FastAPI、PyMySQL、python-jose、passlib、bcrypt（固定 `4.0.1`）、python-dotenv
- 前端：Vue 3、TypeScript、Pinia、Vue Router、Ant Design Vue、Axios
- 图表：AntV G2、ECharts
- 部署：pnpm、Nginx、Shell 脚本

## 目录结构（关键部分）

```text
backend/
  app/
    auth/       # 认证路由、schema、服务
    core/       # 配置、数据库连接、安全能力
    expenses/   # 业务查询路由与服务
    main.py     # FastAPI 入口（当前主入口）
  init_auth_db.py
  start.sh
  requirements.txt

frontend/
  src/
    components/DetailDataTable.vue
    router/index.ts
    services/api.ts
    stores/{auth,expense}.ts
    views/{Login,Dashboard,Categories,Payment,Timeline,Stardust}.vue
    main.ts

docs/
  codebase-analysis.md
  deployment-guide.md
```

## 环境要求

- Python 3.9+（`full-deploy.sh` 创建虚拟环境时使用 `python3.9`）
- Node.js 18+
- pnpm 10+
- MySQL 5.7+/8.0+

## 本地开发

### 1. 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

cp .env.development.example .env.development
# 修改 DB_HOST / DB_USER / DB_PASSWORD / DB_NAME / SECRET_KEY 等配置
```

首次初始化管理员账号（可选但推荐）：

```bash
cd backend
source venv/bin/activate
APP_ENV=development python init_auth_db.py
```

启动服务：

```bash
cd backend
source venv/bin/activate
APP_ENV=development uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. 前端

```bash
cd frontend
pnpm install --registry=https://registry.npmmirror.com
pnpm dev
```

默认访问：

- 前端：`http://127.0.0.1:3000`
- 后端：`http://127.0.0.1:8000`
- OpenAPI：`http://127.0.0.1:8000/docs`

## 构建与部署

### 前端构建

```bash
cd frontend
pnpm build || pnpm exec vite build
```

### 一键部署（仓库根目录）

```bash
APP_ENV=production BACKEND_HOST=127.0.0.1 BACKEND_PORT=8000 bash full-deploy.sh
```

`full-deploy.sh` 现在会在启动后端前自动检测并清理端口占用（`BACKEND_PORT`），并在健康检查后执行一次登录接口探针（默认检查 `/api/auth/login`，预期返回 `200/401/422`，用于拦截 `500` 类异常）。

常用变量：

- `APP_ENV`：`development` / `production`
- `BACKEND_REQUIREMENTS`：默认 `requirements.txt`
- `BACKEND_HOST` / `BACKEND_PORT`：后端监听地址
- `HEALTH_CHECK_URL`：默认 `http://<host>:<port>/api/health`
- `LOGIN_PROBE_ENABLED`：是否启用登录探针（默认 `true`）
- `LOGIN_PROBE_URL`：登录探针地址（默认 `http://<host>:<port>/api/auth/login`）
- `LOGIN_PROBE_TIMEOUT`：登录探针超时秒数（默认 `8`）
- `RELOAD_NGINX`：`true` 时尝试 `sudo systemctl reload nginx`

### 更新部署

```bash
bash update-deploy.sh
```

`update-deploy.sh` 在更新代码前会自动创建代码快照备份，统一写入 `/home/openclaw-expenses/backups`，命名规则为：

- `openclaw-expenses_backup_YYYYMMDD-HHMMSS`

随后脚本会执行 `git reset --hard origin/master` 并调用 `full-deploy.sh`。仅建议在部署机上使用。

常用变量（`update-deploy.sh`）：

- `BACKUP_ROOT`：备份根目录，默认 `/home/openclaw-expenses/backups`
- `BACKUP_PREFIX`：备份名前缀，默认 `openclaw-expenses_backup`
- `SKIP_CODE_BACKUP`：是否跳过代码备份（默认 `false`）

## API 概览

- `POST /api/auth/login`：登录
- `GET /api/auth/me`：当前用户
- `GET /api/expenses/summary`
- `GET /api/expenses/monthly`
- `GET /api/expenses/categories`
- `GET /api/expenses/payment-methods`
- `GET /api/expenses/timeline`
- `GET /api/expenses/stardust`
- `GET /health`
- `GET /api/health`

## 文档

- 统一代码解读与评审（主文档）：`docs/codebase-analysis.md`
- 部署指南：`docs/deployment-guide.md`
