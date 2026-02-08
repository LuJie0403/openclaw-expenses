# 个人支出看板部署手册 (Deployment Manual)

## 1. 概览
本手册记录如何在阿里云 ECS (CentOS) 上部署 `openclaw-expenses` 应用。

- **服务器**: 120.27.250.73
- **用户**: `openclaw-expenses`
- **部署路径**: `~/apps/openclaw-expenses`
- **架构**: FastAPI (Backend) + Vue 3 (Frontend, 静态文件)

## 2. 环境准备
确保服务器已安装 Python 3.9+ 和 Node.js 18+ (如果需要构建前端)。

```bash
# SSH 登录
ssh openclaw-expenses@120.27.250.73

# 创建部署目录
mkdir -p ~/apps/openclaw-expenses
```

## 3. 代码同步
从本地或 GitHub 拉取代码。

**方式 A: 从本地推送 (推荐，含最新修改)**
```bash
# 在本地执行
scp -r expense_web_repo/* openclaw-expenses@120.27.250.73:~/apps/openclaw-expenses/
```

**方式 B: 从 GitHub 拉取 (需配置 SSH Key)**
```bash
# 在服务器执行
git clone git@github.com:LuJie0403/openclaw-expenses.git ~/apps/openclaw-expenses
```

## 4. 后端配置 (Backend)

### 4.1 创建虚拟环境
```bash
cd ~/apps/openclaw-expenses/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4.2 配置环境变量 (.env)
**安全警告**: 严禁将 .env 提交到 Git。请手动创建。

```bash
cp .env.example .env
nano .env
```

**填入真实配置**:
```ini
DB_HOST=127.0.0.1  # 或 120.27.250.73 (内网IP)
DB_PORT=3306
DB_USER=openclaw_aws
DB_PASSWORD=9!wQSw@12sq  # 真实密码
DB_NAME=iterlife4openclaw
SECRET_KEY=... (生成一个随机字符串)
```

### 4.3 启动服务 (测试)
```bash
uvicorn main_v2:app --host 0.0.0.0 --port 8000
```
访问 `http://120.27.250.73:8000/docs` 验证 API 文档。

### 4.4 后台运行 (Systemd / Nohup)
推荐使用 Systemd 管理服务。
(详见 systemd-config.md)

## 5. 前端部署 (Frontend)
如果服务器资源允许构建，或本地构建后上传 `dist` 目录。

```bash
cd ../frontend
npm install
npm run build
```
构建产物位于 `dist/`，配置 Nginx 指向该目录。

## 6. 维护与更新
```bash
# 更新代码
git pull origin master

# 重启服务
systemctl restart openclaw-expenses
```
