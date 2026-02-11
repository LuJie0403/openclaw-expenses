import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def parse_cors_origins(origins_value: str):
    return [origin.strip() for origin in origins_value.split(",") if origin.strip()]


class Settings:
    # Database Settings
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "expense_db")
    
    # Runtime Settings
    APP_ENV = os.getenv("APP_ENV", "development").lower()
    CORS_ORIGINS = parse_cors_origins(
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    )

    # Auth Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    @property
    def DATABASE_URL(self):
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()

if settings.APP_ENV == "production" and not settings.SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set when APP_ENV=production")

if not settings.SECRET_KEY:
    # Keep local development runnable, but prevent accidental production usage.
    settings.SECRET_KEY = "dev-only-secret-key-change-before-production"
