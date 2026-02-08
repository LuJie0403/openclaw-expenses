#!/bin/bash
# 启动后端服务
source venv/bin/activate
export $(cat .env.development | xargs)
uvicorn main_v2:app --host 0.0.0.0 --port 8000 --reload