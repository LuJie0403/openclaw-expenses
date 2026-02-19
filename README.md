# OpenClaw Expenses

OpenClaw Expenses 是一个面向个人/团队的消费数据分析系统，提供总览、分类、支付方式、时间线与消费星辰可视化能力。

## 核心能力
- 统一认证：基于 JWT 的登录态与接口鉴权。
- 数据总览：总额、笔数、均值、时间跨度（含最早/最晚时间）。
- 多维分析：月度趋势（近 12/24/36 月）、分类占比（饼图/矩形树图）、支付方式、时间线。
- 明细一致性：支付方式详情与分类详情复用公共表格组件，支持页内序号、占比进度、分页统计、全字段排序。
- 金额规范：全站金额字段统一千分位、保留两位小数，并在表头标注单位。

## 技术栈
- 后端：FastAPI、Uvicorn、PyMySQL、Pydantic、python-jose、passlib
- 前端：Vue 3、TypeScript、Pinia、Vue Router、Ant Design Vue
- 图表：AntV G2、ECharts
- 构建与部署：pnpm、Nginx

## 目录结构

```text
backend/
  app/
    auth/
    core/
    expenses/
    main.py
  start.sh
  requirements-*.txt

frontend/
  src/
    components/
      DetailDataTable.vue
    services/
    stores/
    utils/
    views/

docs/
  deployment-guide.md
  code-review.md
```

## 运行要求
- Python 3.8+
- Node.js 18+
- pnpm 10+
- MySQL 5.7+/8.0+

## 本地开发（推荐）

### 1) 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements-jwt.txt

# 配置环境
cp .env.development.example .env.development
# 按需修改 DB / SECRET_KEY / CORS_ORIGINS

APP_ENV=development uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2) 前端

```bash
cd frontend
pnpm install --registry=https://registry.npmmirror.com
pnpm dev
```

## 本地构建验证（与生产相对路径对齐）

建议在以下目录进行构建验证：
- `/Users/iter_1024/apps/openclaw-expenses`

```bash
cd /Users/iter_1024/apps/openclaw-expenses/frontend
pnpm install --registry=https://registry.npmmirror.com
pnpm build || pnpm exec vite build
```

> 说明：当前存在 `vue-tsc` 兼容问题时，使用 `pnpm exec vite build` 作为构建兜底。

## 部署

已提供统一部署脚本：`deploy.sh`

关键特性：
- 固定后端入口：`app.main:app`
- 固定前端包管理：`pnpm`（含 corepack 引导）
- 后端健康检查：`/api/health`
- 前端构建兜底：`pnpm build || pnpm exec vite build`

示例：

```bash
# 在项目根目录
APP_ENV=production BACKEND_HOST=127.0.0.1 BACKEND_PORT=8000 bash deploy.sh

# 若需要自动重载 nginx（需 sudo 权限）
RELOAD_NGINX=true bash deploy.sh
```

## API 健康检查
- `GET /health`
- `GET /api/health`

## 文档
- 部署指南：`docs/deployment-guide.md`
- 走查与整改记录：`docs/code-review.md`
