import os
import re

from dotenv import load_dotenv

# Load environment variables with environment-specific overrides.
# 1) .env (shared defaults)
# 2) .env.<APP_ENV> (environment-specific values)
load_dotenv(".env", override=False)
_APP_ENV = os.getenv("APP_ENV", "development").lower()
load_dotenv(f".env.{_APP_ENV}", override=False)


def parse_cors_origins(origins_value: str):
    return [origin.strip() for origin in origins_value.split(",") if origin.strip()]


def parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_sql_identifier(value: str, default: str) -> str:
    candidate = (value or default).strip()
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", candidate):
        return candidate
    raise ValueError(f"Invalid SQL identifier: {candidate}")


class Settings:
    # Database Settings
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "iterlife_reunion")
    AUTH_USER_TABLE = parse_sql_identifier(
        os.getenv("AUTH_USER_TABLE", "iterlife_user"),
        "iterlife_user",
    )

    # Runtime Settings
    APP_ENV = os.getenv("APP_ENV", "development").lower()
    CORS_ORIGINS = parse_cors_origins(
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    )

    # Auth Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    # Initial Admin User Settings (used by init_auth_db.py)
    ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
    ADMIN_FULL_NAME = os.getenv("ADMIN_FULL_NAME", "Administrator")
    INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    RESET_ADMIN_PASSWORD = parse_bool(os.getenv("RESET_ADMIN_PASSWORD"), default=False)

    @property
    def DATABASE_URL(self):
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()

if settings.APP_ENV == "production" and not settings.SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set when APP_ENV=production")

if not settings.SECRET_KEY:
    # Keep local development runnable, but prevent accidental production usage.
    settings.SECRET_KEY = "dev-only-secret-key-change-before-production"
