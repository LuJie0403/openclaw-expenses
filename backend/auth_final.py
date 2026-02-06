#!/usr/bin/env python3
"""
OpenClaw Expenses 简化JWT认证系统
修复FastAPI和Pydantic v2兼容性问题
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pymysql
import os
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

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
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天有效期

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '120.27.250.73'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'openclaw_aws'),
    'password': os.getenv('DB_PASSWORD', '9!wQSw@12sq'),
    'database': os.getenv('DB_NAME', 'iterlife4openclaw'),
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"数据库连接错误: {e}")
        raise HTTPException(status_code=500, detail="数据库连接失败")

# Pydantic模型定义
class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(max_length=320)
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(min_length=6, max_length=128)

class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)

class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }

class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# OAuth2配置 - 修复缺失的定义
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except JWTError:
        return None

# 密码工具函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

# 数据库操作函数
def get_user_by_username(username: str):
    """根据用户名获取用户信息"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT id, email, username, hashed_password, full_name, is_active, created_at
            FROM users 
            WHERE username = %s AND is_active = TRUE
            """
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "email": result[1],
                    "username": result[2],
                    "hashed_password": result[3],
                    "full_name": result[4],
                    "is_active": result[5],
                    "created_at": result[6]
                }
            return None
    finally:
        conn.close()

def create_user(user_create: UserCreate):
    """创建新用户"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 检查用户名和邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = %s", (user_create.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="邮箱已存在")
            
            cursor.execute("SELECT id FROM users WHERE username = %s", (user_create.username,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="用户名已存在")
            
            # 创建用户
            hashed_password = get_password_hash(user_create.password)
            sql = """
            INSERT INTO users (email, username, hashed_password, full_name, is_active)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                user_create.email,
                user_create.username,
                hashed_password,
                user_create.full_name,
                user_create.is_active
            ))
            
            conn.commit()
            
            # 获取新创建的用户
            cursor.execute("SELECT id, email, username, full_name, is_active, created_at FROM users WHERE username = %s", (user_create.username,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "id": result[0],
                    "email": result[1],
                    "username": result[2],
                    "full_name": result[3],
                    "is_active": result[4],
                    "created_at": result[5]
                }
            return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"用户创建失败: {str(e)}")
    finally:
        conn.close()

def authenticate_user(username: str, password: str):
    """验证用户身份"""
    user = get_user_by_username(username)
    if not user:
        return None
    
    if not verify_password(password, user["hashed_password"]):
        return None
    
    return user

# 简化的认证依赖函数
def get_current_user_from_token(token: str = Depends(oauth2_scheme)):
    """从Token获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    
    return user

# API路由定义

@app.post("/auth/register", response_model=UserResponse)
async def register_user(user_create: UserCreate):
    """
    用户注册接口
    
    创建新用户账户，需要邮箱和用户名唯一
    """
    try:
        user = create_user(user_create)
        return UserResponse(**user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"用户创建失败: {str(e)}")

@app.post("/auth/login", response_model=Token)
async def login_user(login_data: UserLogin):
    """
    用户登录接口
    
    使用用户名和密码登录，返回JWT访问令牌
    """
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "user_id": user["id"], "email": user["email"]},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user_from_token)):
    """
    获取当前登录用户信息
    
    需要有效的JWT令牌
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        username=current_user["username"],
        full_name=current_user.get("full_name"),
        is_active=current_user["is_active"],
        created_at=current_user["created_at"]
    )

# 数据库初始化函数
def init_auth_database():
    """初始化用户认证数据库表"""
    conn = None
    cursor = None
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🚀 开始创建用户认证数据库表...")
        
        # 创建用户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            email VARCHAR(320) NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            is_superuser BOOLEAN DEFAULT FALSE NOT NULL,
            is_verified BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
            INDEX idx_users_email (email),
            INDEX idx_users_username (username)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        # 创建默认管理员用户
        cursor.execute("""
        INSERT IGNORE INTO users (email, username, hashed_password, full_name, is_active, is_superuser, is_verified)
        VALUES (
            'admin@openclaw.com',
            'admin',
            '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
            '系统管理员',
            TRUE,
            TRUE,
            TRUE
        );
        """)
        
        # 创建测试用户
        cursor.execute("""
        INSERT IGNORE INTO users (email, username, hashed_password, full_name, is_active, is_superuser, is_verified)
        VALUES (
            'test@openclaw.com',
            'testuser',
            '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
            '测试用户',
            TRUE,
            FALSE,
            TRUE
        );
        """)
        
        conn.commit()
        print("✅ 用户认证数据库表创建完成！")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# 数据库初始化
if __name__ == "__main__":
    init_auth_database()
    print("🎉 JWT认证系统初始化完成！")
    print("\n📋 测试账户:")
    print("管理员 - 用户名: admin, 密码: admin123")
    print("测试用户 - 用户名: testuser, 密码: test123")