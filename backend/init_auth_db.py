#!/usr/bin/env python3
import pymysql
from dotenv import load_dotenv
from config import settings
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
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
            # Create expenses_user table (with VARCHAR id)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses_user (
                id VARCHAR(50) PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Check if admin exists
            if not settings.ADMIN_USERNAME:
                raise ValueError("ADMIN_USERNAME is required in environment config.")
            if not settings.ADMIN_EMAIL:
                raise ValueError("ADMIN_EMAIL is required in environment config.")
            if not settings.ADMIN_USER_ID:
                raise ValueError("ADMIN_USER_ID is required in environment config.")

            cursor.execute("SELECT * FROM expenses_user WHERE username=%s", (settings.ADMIN_USERNAME,))
            admin = cursor.fetchone()

            admin_password = settings.INITIAL_ADMIN_PASSWORD.strip()
            force_reset_admin_password = settings.RESET_ADMIN_PASSWORD

            if not admin:
                if not admin_password:
                    raise ValueError(
                        "INITIAL_ADMIN_PASSWORD is required when creating admin user for the first time."
                    )
                hashed_pwd = get_password_hash(admin_password)
                print("Creating admin user...")
                cursor.execute("""
                INSERT INTO expenses_user (id, username, email, hashed_password, full_name, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    settings.ADMIN_USER_ID,
                    settings.ADMIN_USERNAME,
                    settings.ADMIN_EMAIL,
                    hashed_pwd,
                    settings.ADMIN_FULL_NAME,
                    True
                ))
            elif admin_password and force_reset_admin_password:
                hashed_pwd = get_password_hash(admin_password)
                print("Resetting admin password...")
                cursor.execute("""
                UPDATE expenses_user SET hashed_password=%s WHERE username=%s
                """, (hashed_pwd, settings.ADMIN_USERNAME))
            else:
                print("Admin user already exists. Skip password reset.")
            
            connection.commit()
            print("Database initialized successfully (expenses_user table updated).")
            
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    init_db()
