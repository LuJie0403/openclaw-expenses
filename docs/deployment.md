# 个人支出看板部署手册 (Deployment Manual)

> **最后更新**: 2026-02-08
> **环境**: Alibaba Cloud Linux 3 (CentOS 8 兼容)

## 1. 核心架构
- **前端**: Vue 3 + Vite (部署于 Nginx)
- **后端**: FastAPI + Python 3.9 (部署于 Systemd/Uvicorn)
- **数据库**: MySQL (RDS 或 本地)

## 2. 基础环境准备 (The Hard Way)
由于系统默认源缺失 Python 3.9，需手动编译。

### 2.1 安装 Python 3.9
```bash
# 安装编译依赖
sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel make wget

# 下载并编译 (耗时约 5-10 分钟)
cd /tmp
wget https://registry.npmmirror.com/-/binary/python/3.9.18/Python-3.9.18.tgz
tar xzf Python-3.9.18.tgz
cd Python-3.9.18
./configure --enable-optimizations --prefix=/usr/local
sudo make altinstall

# 验证
/usr/local/bin/python3.9 --version
```

### 2.2 安装 Node.js (via NVM)
由于 yum 源缺失 nodejs:18，推荐使用 NVM。
```bash
# 1. 安装 NVM
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc

# 2. 安装 Node 18
nvm install 18
nvm use 18
```

### 2.3 安装 Nginx
```bash
sudo yum install -y nginx
sudo systemctl enable nginx
```

## 3. 后端部署

### 3.1 代码与虚拟环境
```bash
cd ~/apps/openclaw-expenses/backend
# 创建虚拟环境
/usr/local/bin/python3.9 -m venv venv
source venv/bin/activate

# 安装依赖 (注意：必须包含 cryptography 以支持 MySQL 8)
pip install -r requirements.txt
pip install cryptography passlib
```

### 3.2 配置文件 (.env)
```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=openclaw_aws
DB_PASSWORD=YOUR_PASSWORD
DB_NAME=iterlife4openclaw
SECRET_KEY=YOUR_SECRET
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3.3 Systemd 服务 (推荐)
文件: `/etc/systemd/system/openclaw-expenses-backend.service`
```ini
[Unit]
Description=OpenClaw Expenses Backend
After=network.target

[Service]
User=openclaw-expenses
WorkingDirectory=/home/openclaw-expenses/apps/openclaw-expenses/backend
# 注意使用 venv 中的 uvicorn
ExecStart=/home/openclaw-expenses/apps/openclaw-expenses/backend/venv/bin/uvicorn main_v2:app --host 0.0.0.0 --port 8000
Restart=always
EnvironmentFile=/home/openclaw-expenses/apps/openclaw-expenses/backend/.env

[Install]
WantedBy=multi-user.target
```

## 4. 前端部署

### 4.1 构建
```bash
cd ~/apps/openclaw-expenses/frontend
npm install
# 跳过 TS 检查进行构建 (如果有类型错误)
npx vite build
```
产物位于: `dist/`

### 4.2 Nginx 配置
文件: `/etc/nginx/conf.d/openclaw-expenses.conf`
**关键点**: `location /api/` 不要带尾部斜杠，原样转发。

```nginx
server {
    listen 80;
    server_name _;

    root /home/openclaw-expenses/apps/openclaw-expenses/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 反向代理后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 5. 常见问题
- **404 Not Found**: 检查 Nginx 是否剥离了 `/api` 前缀，后端路由是否包含 `/api`。
- **KeyError: 0**: 检查 `pymysql` 是否使用了 `DictCursor`，如果是，必须用 `['key']` 访问。
- **500 Internal Error**: 查看日志 `sudo journalctl -u openclaw-expenses-backend -f`。
