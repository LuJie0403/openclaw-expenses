#!/bin/bash
# 启动后端服务
source venv/bin/activate

APP_ENV=${APP_ENV:-development}
ENV_FILE=".env.${APP_ENV}"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ 环境配置文件不存在: $ENV_FILE"
  echo "请基于 .env.${APP_ENV}.example 或 .env.example 创建对应文件。"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
