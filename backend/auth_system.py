#!/usr/bin/env python3
"""
OpenClaw Expenses 认证系统 - 用户管理和JWT认证
集成FastAPI-Users提供完整的用户认证解决方案
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_users import FastAPIUsers, models as user_models
from fastapi_users.authentication import JWTAuthentication, AuthenticationBackend
from fastapi_users.db import SQLAlchemyUserDatabase
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pymysql
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext

# 加载环境变量
load_dotenv()

# 创建FastAPI应用实例
app = FastAPI(
    title="OpenClaw Expenses API with Authentication",
    version="2.0.0",
    description="个人支出数据管理RESTful API - 带用户认证系统",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS配置 - 支持前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 生产环境需要具体配置
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 数据库配置
DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER', 'openclaw_aws')}:{os.getenv('DB_PASSWORD', '9!wQSw@12sq')}@{os.getenv('DB_HOST', '120.27.250.73')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'iterlife4openclaw')}"

# SQLAlchemy配置
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天有效期

# 依赖函数 - 获取数据库会话
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 用户模型定义
class User(Base):
    """用户数据库模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")

class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="sessions")

class UserPreference(Base):
    """用户偏好设置模型"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    preference_key = Column(String(100), nullable=False)
    preference_value = Column(Text)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="preferences")
    
    __table_args__ = (UniqueConstraint('user_id', 'preference_key', name='uk_user_pref'),)

# Pydantic模型定义
class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False

class UserCreate(UserBase):
    """用户创建模型"""  
    password: str = Field(..., min_length=8, max_length=128)

class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class UserPreferenceCreate(BaseModel):
    """用户偏好创建模型"""
    preference_key: str = Field(..., min_length=1, max_length=100)
    preference_value: Optional[str] = None

class UserPreferenceUpdate(BaseModel):
    """用户偏好更新模型"""
    preference_value: Optional[str] = None

class UserPreferenceResponse(BaseModel):
    """用户偏好响应模型"""
    id: int
    preference_key: str
    preference_value: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 工具函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

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

# 数据库操作函数
def create_user(db: Session, user_create: UserCreate) -> User:
    """创建新用户"""
    # 检查用户名和邮箱是否已存在
    if db.query(User).filter(User.email == user_create.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    if db.query(User).filter(User.username == user_create.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建用户
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        username=user_create.username,
        hashed_password=hashed_password,
        is_active=user_create.is_active,
        is_superuser=user_create.is_superuser,
        is_verified=user_create.is_verified
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户身份"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user

# API路由定义

@app.post("/auth/register", response_model=UserResponse)
async def register_user(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册接口
    
    创建新用户账户，需要邮箱和用户名唯一
    """
    try:
        user = create_user(db, user_create)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"用户创建失败: {str(e)}")

@app.post("/auth/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    用户登录接口
    
    使用用户名和密码登录，返回JWT访问令牌
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已被禁用"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "email": user.email},
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息
    
    需要有效的JWT令牌
    """
    return current_user

# 认证依赖函数
def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="auth/login"))):
    """获取当前用户依赖函数"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    # 获取数据库会话
    db = next(get_db())
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise credentials_exception
        return user
    finally:
        db.close()

# 数据库初始化函数
def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
    print("✅ 认证系统数据库表创建完成")

# 创建数据库表
if __name__ == "__main__":
    init_db()
    print("🚀 OpenClaw Expenses 认证系统初始化完成")