#!/usr/bin/env python3
"""
数据库迁移脚本 - 创建用户认证相关表
执行此脚本将创建用户认证系统所需的数据库表
"""

import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库连接配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '120.27.250.73'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'openclaw_aws'),
    'password': os.getenv('DB_PASSWORD', '9!wQSw@12sq'),
    'database': os.getenv('DB_NAME', 'iterlife4openclaw'),
    'charset': 'utf8mb4'
}

def create_auth_tables():
    """创建用户认证相关表"""
    conn = None
    cursor = None
    
    try:
        # 连接数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🚀 开始创建用户认证系统数据库表...")
        
        # 1. 创建用户表
        print("📊 创建用户表 (users)...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            email VARCHAR(320) UNIQUE NOT NULL,
            username VARCHAR(50) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            is_superuser BOOLEAN DEFAULT FALSE NOT NULL,
            is_verified BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
            INDEX idx_users_email (email),
            INDEX idx_users_username (username)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        # 2. 创建用户会话表
        print("📊 创建用户会话表 (user_sessions)...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            INDEX idx_sessions_token (session_token),
            INDEX idx_sessions_user (user_id),
            INDEX idx_sessions_expires (expires_at),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        # 3. 创建用户偏好设置表
        print("📊 创建用户偏好设置表 (user_preferences)...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            user_id BIGINT NOT NULL,
            preference_key VARCHAR(100) NOT NULL,
            preference_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY uk_user_pref (user_id, preference_key),
            INDEX idx_preferences_user (user_id),
            INDEX idx_preferences_key (preference_key)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        # 4. 创建默认管理员用户 (可选)
        print("👤 创建默认管理员用户...")
        cursor.execute("""
        INSERT IGNORE INTO users (email, username, hashed_password, is_active, is_superuser, is_verified)
        VALUES (
            'admin@openclaw.com',
            'admin',
            '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',  -- 密码: admin123
            TRUE,
            TRUE,
            TRUE
        );
        """)
        
        # 5. 创建测试用户 (可选)
        print("👤 创建测试用户...")
        cursor.execute("""
        INSERT IGNORE INTO users (email, username, hashed_password, is_active, is_superuser, is_verified)
        VALUES (
            'test@openclaw.com',
            'testuser',
            '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',  -- 密码: test123
            TRUE,
            FALSE,
            TRUE
        );
        """)
        
        # 提交所有更改
        conn.commit()
        
        print("✅ 所有数据库表创建成功！")
        
        # 显示创建的表
        print("\n📋 已创建的表:")
        cursor.execute("SHOW TABLES LIKE 'users' OR SHOW TABLES LIKE 'user_sessions' OR SHOW TABLES LIKE 'user_preferences'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # 显示用户数量
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\n👥 当前用户数量: {user_count}")
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def verify_tables():
    """验证表是否正确创建"""
    conn = None
    cursor = None
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n🔍 验证表结构...")
        
        # 检查表是否存在
        tables_to_check = ['users', 'user_sessions', 'user_preferences']
        
        for table_name in tables_to_check:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor.fetchone()
            if result:
                print(f"✅ {table_name} 表存在")
                
                # 显示表结构
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                print(f"   字段数量: {len(columns)}")
                for col in columns[:3]:  # 只显示前3个字段
                    print(f"   - {col[0]}: {col[1]}")
            else:
                print(f"❌ {table_name} 表不存在")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 OpenClaw Expenses 认证系统 - 数据库初始化")
    print("=" * 50)
    
    try:
        # 创建认证表
        create_auth_tables()
        
        # 验证表结构
        verify_tables()
        
        print("\n🎉 认证系统数据库初始化完成！")
        print("\n📋 下一步操作:")
        print("1. 启动认证系统: python auth_system.py")
        print("2. 测试登录: 用户名: admin, 密码: admin123")
        print("3. 测试登录: 用户名: testuser, 密码: test123")
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        exit(1)