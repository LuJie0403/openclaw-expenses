#!/usr/bin/env python3
"""
OpenClaw Expenses 简化JWT认证系统 - 修复bcrypt密码长度限制
使用python-jose + passlib 实现轻量级用户认证
修复密码长度限制和bcrypt兼容性问题
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pymysql
import os
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings

# 加载环境变量
load_dotenv()

# 创建FastAPI应用实例
app = FastAPI(
    title="OpenClaw Expenses API with JWT Auth",
    version="2.0.0",
    description="个人支出数据管理RESTful API - 带JWT认证系统",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# JWT配置
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# 密码加密上下文 - 使用bcrypt但处理长度限制
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2配置
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# 数据库配置 - 已移除硬编码
# DB_CONFIG 现已通过 settings 动态获取

def get_db_connection():
    """获取数据库连接"""
    try:
        return pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"数据库连接错误: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")
# ... (rest of the file content from read output, but I will construct the full file content to write)
