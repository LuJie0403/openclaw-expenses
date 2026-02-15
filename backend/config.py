
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def _to_bool(value: str, default: bool = False) -> bool:
    # Parse bool-like env values consistently.
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")

def _to_int(value: str, default: int) -> int:
    # Parse int env values with safe fallback.
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _to_csv_set(value: str) -> set:
    # Parse comma-separated host allowlist.
    if not value:
        return set()
    return {item.strip().lower() for item in value.split(",") if item.strip()}

class Settings:
    # Database Settings
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "expense_db")
    
    # Auth Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-it-in-production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

    @property
    def DATABASE_URL(self):
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

class WechatAuthSettings:
    # Keep WeChat config isolated from generic auth/database settings.
    # This makes it easier to:
    # - disable/enable feature in one place
    # - avoid hardcoded credentials in business code
    # - validate required fields before first request
    # - map all WeChat knobs via WECHAT_* environment variables
    WECHAT_OPEN_ENABLED = _to_bool(os.getenv("WECHAT_OPEN_ENABLED"), False)
    WECHAT_OPEN_APP_ID = os.getenv("WECHAT_OPEN_APP_ID", "").strip()
    WECHAT_OPEN_APP_SECRET = os.getenv("WECHAT_OPEN_APP_SECRET", "").strip()
    WECHAT_OPEN_REDIRECT_URI = os.getenv("WECHAT_OPEN_REDIRECT_URI", "").strip()
    WECHAT_OPEN_SCOPE = os.getenv("WECHAT_OPEN_SCOPE", "snsapi_login").strip() or "snsapi_login"
    WECHAT_QR_SESSION_TTL_SECONDS = _to_int(os.getenv("WECHAT_QR_SESSION_TTL_SECONDS"), 300)
    WECHAT_LOGIN_TICKET_TTL_SECONDS = _to_int(os.getenv("WECHAT_LOGIN_TICKET_TTL_SECONDS"), 60)
    WECHAT_HTTP_TIMEOUT_SECONDS = _to_int(os.getenv("WECHAT_HTTP_TIMEOUT_SECONDS"), 5)
    WECHAT_STATE_SIGN_SECRET = os.getenv(
        "WECHAT_STATE_SIGN_SECRET", os.getenv("SECRET_KEY", "change_me")
    ).strip()
    WECHAT_ALLOWED_REDIRECT_HOSTS = _to_csv_set(os.getenv("WECHAT_ALLOWED_REDIRECT_HOSTS", ""))

    def validate_enabled_config(self):
        # Validate only when feature is enabled to keep local dev friction low.
        if not self.WECHAT_OPEN_ENABLED:
            return

        missing = []
        if not self.WECHAT_OPEN_APP_ID:
            missing.append("WECHAT_OPEN_APP_ID")
        if not self.WECHAT_OPEN_APP_SECRET:
            missing.append("WECHAT_OPEN_APP_SECRET")
        if not self.WECHAT_OPEN_REDIRECT_URI:
            missing.append("WECHAT_OPEN_REDIRECT_URI")
        if not self.WECHAT_STATE_SIGN_SECRET:
            missing.append("WECHAT_STATE_SIGN_SECRET")
        if missing:
            raise RuntimeError(f"WeChat auth enabled but missing required config: {', '.join(missing)}")

        redirect_host = (urlparse(self.WECHAT_OPEN_REDIRECT_URI).hostname or "").lower()
        if not redirect_host:
            raise RuntimeError("WECHAT_OPEN_REDIRECT_URI is invalid")
        if self.WECHAT_ALLOWED_REDIRECT_HOSTS and redirect_host not in self.WECHAT_ALLOWED_REDIRECT_HOSTS:
            raise RuntimeError(
                f"WECHAT_OPEN_REDIRECT_URI host '{redirect_host}' is not in WECHAT_ALLOWED_REDIRECT_HOSTS"
            )

        if self.WECHAT_QR_SESSION_TTL_SECONDS <= 0:
            raise RuntimeError("WECHAT_QR_SESSION_TTL_SECONDS must be > 0")
        if self.WECHAT_LOGIN_TICKET_TTL_SECONDS <= 0:
            raise RuntimeError("WECHAT_LOGIN_TICKET_TTL_SECONDS must be > 0")
        if self.WECHAT_HTTP_TIMEOUT_SECONDS <= 0:
            raise RuntimeError("WECHAT_HTTP_TIMEOUT_SECONDS must be > 0")

settings = Settings()
wechat_settings = WechatAuthSettings()
