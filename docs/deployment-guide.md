# OpenClaw Expenses 部署指南（当前脚本版）

本文档以仓库当前脚本为准，覆盖本地验证、脚本化部署和常见故障排查。

## 1. 版本基线

- 后端入口：`app.main:app`
- 前端构建命令：`pnpm build || pnpm exec vite build`
- 健康检查：`/api/health`（同时保留 `/health`）
- 部署脚本：
  - `full-deploy.sh`：完整部署（后端 + 前端）
  - `update-deploy.sh`：拉取并强制同步到 `origin/master` 后调用 `full-deploy.sh`

## 2. 先决条件

- Python 3.9+（`full-deploy.sh` 默认用 `python3.9 -m venv`）
- Node.js 18+
- pnpm 10+（脚本会尝试通过 corepack 激活）
- MySQL 5.7+/8.0+
- Nginx（可选，若需要 `RELOAD_NGINX=true`）

## 3. 本地验证流程

### 3.1 后端验证

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

cp .env.development.example .env.development
# 按实际环境修改 DB 与 SECRET_KEY
```

可选初始化管理员账号：

```bash
cd backend
source venv/bin/activate
APP_ENV=development python init_auth_db.py
```

启动并检查：

```bash
cd backend
source venv/bin/activate
APP_ENV=development uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

```bash
curl -sS http://127.0.0.1:8000/api/health
curl -sS http://127.0.0.1:8000/health
```

### 3.2 前端验证

```bash
cd frontend
pnpm install --registry=https://registry.npmmirror.com
pnpm build || pnpm exec vite build
```

## 4. 使用 `full-deploy.sh` 一键部署

在项目根目录执行：

```bash
APP_ENV=production BACKEND_HOST=127.0.0.1 BACKEND_PORT=8000 bash full-deploy.sh
```

脚本主要动作：

1. 检查 `python3`、`node`、`curl`。
2. 自动解析 `pnpm`（必要时通过 `corepack`）。
3. 创建/复用后端虚拟环境并安装依赖（默认 `requirements.txt`）。
4. 启动前先清理后端端口占用（`BACKEND_PORT`），防止旧进程残留。
5. 启动 `uvicorn app.main:app`，执行健康检查。
6. 执行登录接口探针（默认 `/api/auth/login`，接受 `200/401/422`，拦截 `500`）。
7. 安装前端依赖并构建，失败时回退到 `pnpm exec vite build`。
8. 更新符号链接：`dist/frontend -> frontend/dist`。
9. 可选重载 Nginx（`RELOAD_NGINX=true`）。

### 4.1 常用环境变量

- `APP_ENV`：默认 `development`
- `BACKEND_VENV_DIR`：默认 `venv`
- `BACKEND_REQUIREMENTS`：默认 `requirements.txt`
- `BACKEND_HOST`：默认 `127.0.0.1`
- `BACKEND_PORT`：默认 `8000`
- `FRONTEND_REGISTRY`：默认 `https://registry.npmmirror.com`
- `PNPM_VERSION`：默认 `10.28.2`
- `HEALTH_CHECK_URL`：默认 `http://<host>:<port>/api/health`
- `LOGIN_PROBE_ENABLED`：默认 `true`
- `LOGIN_PROBE_URL`：默认 `http://<host>:<port>/api/auth/login`
- `LOGIN_PROBE_TIMEOUT`：默认 `8`
- `DIST_LINK_PATH`：默认 `<repo>/dist/frontend`
- `RELOAD_NGINX`：默认 `false`

## 5. 使用 `update-deploy.sh` 更新部署

```bash
bash update-deploy.sh
```

注意事项：

- 该脚本会执行 `git reset --hard origin/master`。
- 只建议在部署机使用，不要在有未提交改动的开发环境执行。

## 6. Nginx 对齐建议

仓库内 `nginx.conf` 的关键行为：

- `location /`：回退到 `index.html`
- `location /api/`：反向代理到 `127.0.0.1:8000/api/`
- 兼容保留 `location /auth/`、`location /expenses/`

若使用自定义域名或目录，请同步修改 `root` 与 `server_name`。

## 7. 常见问题

### Q1: `pnpm build` 失败

- 现象：`vue-tsc` 或 TS 相关编译错误。
- 处理：使用 `pnpm exec vite build`（脚本已内置回退）。

### Q2: 后端健康检查失败

按顺序排查：

1. `backend/backend.log`（或脚本运行目录下 `backend.log`）
2. `.env.production` / `.env.development` 配置是否完整
3. 数据库连通性与账号权限
4. 端口占用（`8000`）

### Q3: 部署脚本创建 venv 失败

- 可能原因：机器没有 `python3.9`。
- 处理：安装 `python3.9`，或调整 `full-deploy.sh` 中创建虚拟环境的命令。
