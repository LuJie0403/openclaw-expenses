# 认证系统设计方案 - 个人支出看板

## 🎯 认证框架选择

**选择**: **FastAPI-Users** + **SQLAlchemy** + **SQLite/MySQL
- ✅ 成熟稳定的认证框架
- ✅ 支持JWT Token认证  
- ✅ 内置用户管理、权限控制
- ✅ 支持OAuth2、Cookie认证
- ✅ 轻量级，易于集成

## 🗄️ 新增数据库表设计

### 1. 用户表 (users)
```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(320) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
```

### 2. 用户会话表 (user_sessions)
```sql
CREATE TABLE user_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_sessions_token (session_token),
    INDEX idx_sessions_user (user_id),
    INDEX idx_sessions_expires (expires_at)
);
```

### 3. 用户配置表 (user_preferences)
```sql
CREATE TABLE user_preferences (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_pref (user_id, preference_key)
);
```

## 🔧 后端集成方案

### 1. 安装依赖
```bash
pip install fastapi-users[sqlalchemy] 
pip install fastapi-users-db-sqlalchemy
pip install passlib[bcrypt]
pip install python-jose[cryptography]
```

### 2. 认证配置
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_users import FastAPIUsers, models
from fastapi_users.authentication import JWTAuthentication, CookieAuthentication
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
```

### 3. 用户模型
```python
from fastapi_users import models as user_models

class User(user_models.BaseUser):
    """用户基础模型"""
    pass

class UserCreate(user_models.BaseUserCreate):
    """用户创建模型"""
    pass

class UserUpdate(user_models.BaseUserUpdate):
    """用户更新模型"""
    pass

class UserDB(User, user_models.BaseUserDB):
    """用户数据库模型"""
    pass
```

### 4. 认证后端配置
```python
# JWT配置
SECRET_KEY = "your-secret-key-here"  # 生产环境使用环境变量
JWT_LIFETIME_SECONDS = 3600 * 24 * 7  # 7天有效期

# JWT认证
jwt_authentication = JWTAuthentication(
    secret=SECRET_KEY,
    lifetime_seconds=JWT_LIFETIME_SECONDS,
    tokenUrl="auth/jwt/login",
    name="jwt"
)

# Cookie认证
cookie_authentication = CookieAuthentication(
    secret=SECRET_KEY,
    lifetime_seconds=JWT_LIFETIME_SECONDS,
    name="cookie"
)
```

## 🌐 API接口设计

### 认证相关接口
```
POST /auth/register          # 用户注册
POST /auth/jwt/login         # JWT登录
POST /auth/jwt/logout        # JWT登出
GET  /auth/me               # 获取当前用户信息
PUT  /auth/me               # 更新当前用户信息
```

### 受保护的支出API (需要认证)
```
GET  /api/v1/expenses        # 获取支出列表 (需要认证)
GET  /api/v1/expenses/summary # 支出总览 (需要认证)
... 其他所有支出相关API都需要认证
```

## 🔒 前端认证集成

### 1. 登录页面
```vue
<!-- Login.vue -->
<template>
  <div class="login-container">
    <a-form :model="loginForm" @finish="handleLogin">
      <a-form-item name="username" :rules="[{ required: true, message: '请输入用户名' }]">
        <a-input v-model:value="loginForm.username" placeholder="用户名" />
      </a-form-item>
      <a-form-item name="password" :rules="[{ required: true, message: '请输入密码' }]">
        <a-input-password v-model:value="loginForm.password" placeholder="密码" />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" html-type="submit" :loading="loading" block>
          登录
        </a-button>
      </a-form-item>
    </a-form>
  </div>
</template>
```

### 2. 认证状态管理
```typescript
// stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)
  
  const isAuthenticated = computed(() => !!token.value)
  
  const login = async (username: string, password: string) => {
    try {
      const response = await axios.post('/auth/jwt/login', {
        username,
        password
      })
      
      token.value = response.data.access_token
      localStorage.setItem('token', token.value)
      
      // 设置axios默认认证头
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      
      // 获取用户信息
      await fetchUser()
      
      return true
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }
  
  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
  }
  
  const fetchUser = async () => {
    if (!token.value) return
    
    try {
      const response = await axios.get('/auth/me')
      user.value = response.data
    } catch (error) {
      console.error('获取用户信息失败:', error)
      logout()
    }
  }
  
  // 初始化时尝试获取用户信息
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    fetchUser()
  }
  
  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
    fetchUser
  }
})
```

### 3. 路由守卫
```typescript
// router/index.ts
import { useAuthStore } from '@/stores/auth'

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 需要认证的路由
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  
  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})
```

## 🛡️ 安全特性

### 1. 密码安全
- **加密算法**: bcrypt (12轮salt)
- **密码策略**: 最小8位，包含大小写字母和数字
- **密码过期**: 90天强制更新（可选）

### 2. JWT Token安全
- **密钥管理**: 环境变量存储
- **Token过期**: 7天有效期，支持刷新
- **HTTPS传输**: 生产环境强制HTTPS

### 3. 会话管理
- **并发限制**: 同一用户最多5个活跃会话
- **自动过期**: 30天无操作自动登出
- **异地登录**: 支持强制下线其他设备

## 📊 用户数据分析

### 用户行为统计
```sql
-- 用户登录统计
SELECT 
    DATE(login_time) as login_date,
    COUNT(*) as login_count,
    COUNT(DISTINCT user_id) as unique_users
FROM user_sessions 
WHERE login_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(login_time)
ORDER BY login_date DESC;
```

### 活跃用户分析
```sql
-- 最近7天活跃用户
SELECT 
    u.username,
    u.email,
    MAX(us.login_time) as last_login,
    COUNT(us.id) as session_count
FROM users u
LEFT JOIN user_sessions us ON u.id = us.user_id
WHERE us.login_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY u.id
ORDER BY last_login DESC;
```

## 🚀 部署配置

### 环境变量
```bash
# 认证配置
SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080  # 7天

# 数据库配置
DATABASE_URL=mysql://user:pass@host:3306/openclaw_expenses

# 安全配置
PASSWORD_MIN_LENGTH=8
MAX_LOGIN_ATTEMPTS=5
SESSION_TIMEOUT_MINUTES=43200  # 30天
```

### Docker配置
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV SECRET_KEY=${SECRET_KEY}

# 运行应用
CMD ["uvicorn", "main_auth:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**🎯 目标**: 建立安全、易用、可扩展的用户认证系统
**🔒 安全等级**: 生产级安全标准
**⚡ 性能要求**: 登录响应 < 200ms