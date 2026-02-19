# OpenClaw Expenses 部署指南（pnpm + app.main）

本文档为当前生效版本，覆盖本地验证与阿里云部署流程。

## 1. 约定与路径

- 本地源码目录（开发）：`/Users/iter_1024/repository_common/openclaw-expenses`
- 本地验证目录（对齐生产相对结构）：`/Users/iter_1024/apps/openclaw-expenses`
- 阿里云应用目录：`/home/openclaw-expenses/apps/openclaw-expenses`
- 阿里云临时同步目录：`/home/lujie/openclaw-expenses-staging`

## 2. 运行基线

- 后端入口固定为：`app.main:app`
- 前端构建固定为：`pnpm`（不使用 npm）
- 后端健康检查：`/api/health`
- 前端构建兜底：`pnpm build || pnpm exec vite build`

## 3. 本地验证流程

### 3.1 同步到本地验证目录

```bash
rsync -az --delete \
  --exclude '.git' --exclude '.DS_Store' \
  --exclude 'backend/.venv' --exclude 'frontend/node_modules' \
  /Users/iter_1024/repository_common/openclaw-expenses/ \
  /Users/iter_1024/apps/openclaw-expenses/
```

### 3.2 后端验证

```bash
cd /Users/iter_1024/apps/openclaw-expenses/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements-jwt.txt

cp .env.development.example .env.development
APP_ENV=development uvicorn app.main:app --host 127.0.0.1 --port 18000

# 新开终端验证
curl -sS http://127.0.0.1:18000/api/health
```

### 3.3 前端验证

```bash
cd /Users/iter_1024/apps/openclaw-expenses/frontend
pnpm install --registry=https://registry.npmmirror.com
pnpm build || pnpm exec vite build
```

## 4. 阿里云部署流程（手工）

### 4.1 本地同步到云端 staging

```bash
rsync -az --delete \
  --exclude '.git' --exclude '.DS_Store' \
  --exclude 'backend/.venv' --exclude 'backend/venv' \
  --exclude 'frontend/node_modules' \
  /Users/iter_1024/apps/openclaw-expenses/ \
  lujie@120.27.250.73:/home/lujie/openclaw-expenses-staging/
```

### 4.2 服务器部署（SSH 后执行）

```bash
APP_DIR=/home/openclaw-expenses/apps/openclaw-expenses
STAGING_DIR=/home/lujie/openclaw-expenses-staging

# 备份
TS=$(date +%Y%m%d-%H%M%S)
sudo mkdir -p /home/openclaw-expenses/backups/$TS
sudo rsync -a --exclude 'backend/venv/' --exclude 'frontend/node_modules/' \
  "$APP_DIR/" "/home/openclaw-expenses/backups/$TS/openclaw-expenses/"

# 覆盖代码
sudo rsync -az --delete \
  --exclude 'backend/.env' --exclude 'backend/.env.*' \
  --exclude 'backend/venv/' --exclude 'backend/backend.log' \
  --exclude 'frontend/node_modules/' \
  "$STAGING_DIR/" "$APP_DIR/"
sudo chown -R openclaw-expenses:openclaw-expenses "$APP_DIR"
```

### 4.3 后端重启

```bash
sudo pkill -f '/home/openclaw-expenses/apps/openclaw-expenses/backend/venv/bin/uvicorn' || true

sudo -u openclaw-expenses -H bash -lc '
cd /home/openclaw-expenses/apps/openclaw-expenses/backend && \
source venv/bin/activate && \
pip install -r requirements-jwt.txt && \
nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
'
```

### 4.4 前端构建（pnpm）

```bash
sudo -u openclaw-expenses -H bash -lc '
export PATH=$HOME/node-v18.19.0-linux-x64/bin:$PATH
cd /home/openclaw-expenses/apps/openclaw-expenses/frontend
corepack enable || true
corepack prepare pnpm@10.28.2 --activate || true
pnpm install --registry=https://registry.npmmirror.com
pnpm build || pnpm exec vite build
'
```

### 4.5 Nginx 重载与验证

```bash
sudo systemctl reload nginx

curl -sS http://127.0.0.1:8000/api/health
curl -sS -I http://120.27.250.73/ | head -n 1
curl -sS http://120.27.250.73/api/health
```

## 5. deploy.sh 使用

项目根目录执行：

```bash
APP_ENV=production BACKEND_HOST=127.0.0.1 BACKEND_PORT=8000 bash deploy.sh
```

常用变量：
- `APP_ENV`：`development` / `production`
- `BACKEND_REQUIREMENTS`：默认 `requirements-jwt.txt`
- `PNPM_VERSION`：默认 `10.28.2`
- `RELOAD_NGINX`：`true/false`
- `HEALTH_CHECK_URL`：默认 `http://<host>:<port>/api/health`

## 6. 常见问题

### Q1: `pnpm build` 失败并报 `vue-tsc` 相关错误
- 现象：`Search string not found: "/supportedTSExtensions = .*(?=;)/"`
- 处理：使用 `pnpm exec vite build` 作为构建兜底（当前生产流程已纳入）。

### Q2: 后端启动后 8000 端口被占用
- 处理：先 `pkill` 旧 `uvicorn` 进程，再重新启动。

### Q3: 健康检查失败
- 排查顺序：
  1. `backend.log`
  2. `.env.production` / `.env.development` 配置
  3. 数据库连通性
