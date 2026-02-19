
import os

from dotenv import load_dotenv

# Load shared defaults first, then environment-specific overrides.
load_dotenv(".env", override=False)
_APP_ENV = os.getenv("APP_ENV", "development").lower()
load_dotenv(f".env.{_APP_ENV}", override=False)

def parse_cors_origins(origins_value: str):
    return [origin.strip() for origin in origins_value.split(",") if origin.strip()]


class Settings:
    APP_ENV = os.getenv("APP_ENV", "development").lower()

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "openclaw_expenses")

    SECRET_KEY = os.getenv("SECRET_KEY", "")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    CORS_ORIGINS = parse_cors_origins(
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    )

    PROJECT_NAME = "OpenClaw Expenses API"
    PROJECT_VERSION = "2.1.0"

settings = Settings()

if settings.APP_ENV == "production" and not settings.SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set when APP_ENV=production")

if not settings.SECRET_KEY:
    settings.SECRET_KEY = "dev-only-secret-key-change-before-production"
