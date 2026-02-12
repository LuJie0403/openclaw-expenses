# 💸 钱呢 (MoneyWhere) - 个人消费分析系统

“钱呢”是一个现代化的个人消费/支出信息分析处理系统。它旨在帮助用户轻松收集、分类和挖掘消费数据，通过丰富的可视化面板提供洞察，并最终给出支出优化建议。

## ✨ 功能亮点

-   **全景数据面板**: 提供总览、月度趋势、分类占比、支付方式等多维度统计。
-   **消费星辰**: 通过 ECharts 力导向图展示消费数据关联，提供独特的“数据艺术”体验。
-   **科幻感 UI**: 采用全站深色主题，配合数据可视化，营造沉浸式的数据探索体验。
-   **安全认证**: 基于 JWT 的现代化用户认证系统。

## 🛠️ 技术栈 (Tech Stack)

| 领域     | 技术                                                                 |
| :------- | :------------------------------------------------------------------- |
| **后端** | FastAPI, Uvicorn, Python 3.9+, Pydantic (Settings), JWT, MySQL        |
| **前端** | Vue 3 (Composition API), Vite, TypeScript, Pinia, Vue Router         |
| **UI/图表** | Ant Design Vue 4.x, AntV G2, ECharts                               |
| **部署** | Nginx, Systemd                                                       |

## 📂 项目结构

项目采用前后端分离架构。

### 后端 (`/backend`)

重构后的后端遵循标准的模块化、分层设计：

```
backend/
└── app/
    ├── auth/         # 认证模块 (用户、登录、Token)
    │   ├── router.py
    │   ├── schemas.py
    │   └── service.py
    ├── core/         # 核心组件 (配置、数据库连接、安全)
    │   ├── config.py
    │   ├── database.py
    │   └── security.py
    ├── expenses/     # 核心业务模块 (消费数据接口)
    │   ├── router.py
    │   ├── schemas.py
    │   └── service.py
    └── main.py       # FastAPI 应用主入口
```

-   **`main.py`**: 组装应用，挂载路由和中间件。
-   **`core/`**: 提供应用级别的单例和配置。
-   **`auth/`, `expenses/`**: 按业务领域划分模块，每个模块内实现 `Router` (API接口), `Service` (业务逻辑), `Schemas` (数据模型) 的分离。

### 前端 (`/frontend`)

```
frontend/
└── src/
    ├── assets/       # 静态资源
    ├── components/   # 可复用 Vue 组件
    ├── router/       # Vue Router 配置
    ├── services/     # API 请求服务
    ├── stores/       # Pinia 状态管理
    ├── utils/        # 工具函数
    └── views/        # 页面级组件
```

-   **`stores/`**: 使用 Pinia 统一管理用户认证 (`auth.ts`) 和消费数据 (`expense.ts`) 状态。
-   **`services/api.ts`**: 封装 Axios 实例，提供统一的 API 请求和拦截器。

## 🚀 本地开发指南 (Local Development)

### 1. 后端

```bash
# 1. 进入后端目录
cd backend

# 2. 创建并激活 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
# 复制 .env.example (如果存在) 或手动创建 .env 文件
cp .env.example .env 
# 编辑 .env 文件，填入你的数据库连接信息和密钥
# --- .env ---
# DB_HOST=127.0.0.1
# DB_PORT=3306
# DB_USER=your_user
# DB_PASSWORD=your_password
# DB_NAME=your_db
# SECRET_KEY=a_very_secret_key
# ------------

# 5. 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装 Node.js 依赖 (推荐使用 Node.js v18+)
npm install

# 3. 配置 API 代理 (可选, 用于开发)
# 在 vite.config.ts 中可以配置 proxy 以避免 CORS 问题
# server: {
#   proxy: {
#     '/api': {
#       target: 'http://127.0.0.1:8000',
#       changeOrigin: true,
#     },
#   },
# },

# 4. 启动开发服务器
npm run dev
```

## 部署 (Deployment)

生产环境推荐使用 Nginx + Systemd 进行部署。

1.  **后端**: 使用 Systemd (用户或系统服务) 守护 `uvicorn app.main:app` 进程。
2.  **前端**: 执行 `npm run build` 生成静态文件，并使用 Nginx 托管 `dist` 目录。
3.  **Nginx 配置**: 配置反向代理，将 `/api` 请求转发到后端 Uvicorn 服务。

详细步骤可参考 `docs/DEPLOYMENT_GUIDE.md` (注意：该文件可能需要根据最新重构进行更新)。
