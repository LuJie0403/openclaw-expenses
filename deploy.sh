#!/bin/bash
# 一键部署脚本

set -e

echo "🚀 开始部署 OpenClaw Expenses..."

# 检查环境
echo "📋 检查环境..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 未安装"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js 未安装"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm 未安装"; exit 1; }

# 后端部署
echo "🔧 部署后端服务..."
cd backend

if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ ! -f ".env.development" ]; then
    echo "⚙️  创建配置文件..."
    cp .env.example .env.development
    echo "📝 请编辑 .env.development 文件，填入数据库配置"
fi

echo "📥 安装Python依赖..."
pip install -r requirements.txt

echo "🚀 启动后端服务..."
# 杀死旧进程以防端口占用
pkill -f "uvicorn app.main:app" || true
sleep 2
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 后端服务已启动，PID: $BACKEND_PID"

cd ..

# 前端部署
echo "🎨 部署前端应用..."
cd frontend

echo "📥 安装Node.js依赖..."
npm install

echo "🔨 构建前端应用..."
npm run build

echo "📁 创建dist目录链接..."
mkdir -p ../dist
ln -sf $(pwd)/dist ../dist/frontend

cd ..

# Nginx配置 (可选)
if command -v nginx >/dev/null 2>&1; then
    echo "🌐 配置Nginx..."
    cat > nginx.conf << EOF
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /home/lujie/app/openclaw-expenses/dist/frontend;
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF
    echo "📝 Nginx配置已生成，请手动配置到nginx.conf"
fi

echo ""
echo "✅ 部署完成！"
echo ""
echo "📊 应用信息："
echo "   • 后端API: http://localhost:8000/api/v1/health"
echo "   • 前端应用: http://localhost:3000"
echo "   • API文档: http://localhost:8000/api/docs"
echo ""
echo "📝 下一步操作："
echo "   1. 配置数据库连接 (.env.development)"
echo "   2. 配置Nginx (可选)"
echo "   3. 配置SSL证书 (生产环境)"
echo "   4. 推送到GitHub仓库"
echo ""
echo "🎯 项目已准备就绪！"