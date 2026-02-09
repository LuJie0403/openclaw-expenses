
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "openclaw_expenses"
    
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    PROJECT_NAME: str = "OpenClaw Expenses API"
    PROJECT_VERSION: str = "2.1.0-refactored"

    class Config:
        env_file = ".env"
        # Handle case where .env is in parent directory
        env_file_encoding = 'utf-8'

settings = Settings()
