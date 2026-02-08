#!/usr/bin/env python3
import os
import pymysql
from dotenv import load_dotenv
from config import settings
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    # Ensure password is not too long for bcrypt
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def init_db():
    try:
        connection = pymysql.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            port=settings.DB_PORT,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Database connection successful")
        
        with connection.cursor() as cursor:
            # Create expenses_user table if not exists (previously 'users')
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses_user (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Check if admin user exists in expenses_user table
            cursor.execute("SELECT * FROM expenses_user WHERE username='admin'")
            admin = cursor.fetchone()
            
            admin_password = "Af3f@!@Mn5g"
            hashed_pwd = get_password_hash(admin_password)
            
            if not admin:
                print(f"Creating admin user with password: {admin_password}")
                cursor.execute("""
                INSERT INTO expenses_user (username, email, hashed_password, full_name, is_active)
                VALUES (%s, %s, %s, %s, %s)
                """, ('admin', 'admin@example.com', hashed_pwd, 'Administrator', True))
            else:
                print(f"Updating admin password to: {admin_password}")
                cursor.execute("""
                UPDATE expenses_user SET hashed_password=%s WHERE username='admin'
                """, (hashed_pwd,))
            
            connection.commit()
            print("Database initialized successfully (expenses_user table handled).")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    init_db()
