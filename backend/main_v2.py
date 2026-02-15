#!/usr/bin/env python3
import hashlib
import hmac
import json
import secrets
import uuid
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, HTTPException, Depends, status, APIRouter, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import pymysql
from threading import Lock
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import settings, wechat_settings

load_dotenv()

app = FastAPI(
    title="钱呢 API (Where Is My Money)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

api_router = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ---------------------------------------------------------------------------
# WeChat QR Login Backend Contract (maintenance notes)
# ---------------------------------------------------------------------------
# 1) Password login remains unchanged:
#    - POST /api/auth/login
#    - GET  /api/auth/me
#    Existing JWT auth for business APIs is intentionally reused.
#
# 2) WeChat QR login uses 4 endpoints:
#    - POST /api/auth/wechat/qr-session
#      Creates local login session, returns QR metadata.
#    - GET /api/auth/wechat/qr-session/{session_id}
#      Browser polls status: PENDING/CONFIRMED/EXPIRED/FAILED/CONSUMED.
#    - POST /api/auth/wechat/exchange-ticket
#      Browser exchanges one-time ticket for JWT.
#    - GET /api/auth/wechat/callback
#      WeChat redirects mobile browser here after scan confirmation.
#
# 3) Security model:
#    - state is signed with HMAC(secret, session_id + nonce).
#    - ticket is short-lived and one-time; consumed transactionally.
#    - JWT is never transported in callback querystring.
#    - app_secret is server-side only and never exposed to frontend.
#
# 4) Data model:
#    - auth_user_identity:
#      binds local user_id to provider identity.
#    - auth_login_session:
#      stores scan session lifecycle and temporary ticket.
#
# 5) System fields convention on new auth tables:
#    - created_at, updated_at
#    - created_by, updated_by
#    - deleted_at (0 means active, >0 means soft deleted timestamp)
#
# 6) Failure behavior:
#    - callback/API failures update auth_login_session error_code/error_message.
#    - browser receives safe error page in mobile callback context.
#    - polling endpoint exposes concise failure reason to desktop UI.
#
# 7) Concurrency/idempotency:
#    - exchange-ticket uses SELECT ... FOR UPDATE and marks CONSUMED atomically.
#    - callback checks status and exits early for CONFIRMED/CONSUMED.
#    - table creation guarded by process lock + IF NOT EXISTS DDL.
#
# 8) Time semantics:
#    - all expiry checks use UTC now() in server.
#    - expires_in returned as max(0, seconds_left).
#
# 9) Extension hooks:
#    - provider field reserved for future OAuth providers.
#    - identity snapshot fields can be expanded without breaking auth core.
#
# 10) Operational notes:
#    - feature toggle: WECHAT_OPEN_ENABLED.
#    - startup validation runs when toggle is enabled.
#    - if config is missing/invalid, endpoints fail fast with explicit errors.
# ---------------------------------------------------------------------------

# WeChat identity provider name persisted in auth_user_identity.provider.
WECHAT_PROVIDER = "wechat"
# Channel name persisted in auth_login_session.channel.
WECHAT_CHANNEL = "wechat_qr"
# Session just created, waiting for user scan + confirm.
WECHAT_STATUS_PENDING = "PENDING"
# Callback completed, waiting for browser to exchange ticket.
WECHAT_STATUS_CONFIRMED = "CONFIRMED"
# Session expired before callback/consumption.
WECHAT_STATUS_EXPIRED = "EXPIRED"
# Callback or downstream logic failed.
WECHAT_STATUS_FAILED = "FAILED"
# Ticket already consumed once; terminal status.
WECHAT_STATUS_CONSUMED = "CONSUMED"
# Actor name used by system-write rows.
SYSTEM_ACTOR = "SYSTEM"
# Browser polling interval guidance.
WECHAT_POLL_INTERVAL_MS = 2000

# Process-local optimization: avoid checking/creating tables repeatedly.
_wechat_tables_ready = False
_wechat_tables_lock = Lock()

def get_db_connection():
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def utc_now() -> datetime:
    # Keep one UTC time source to avoid local timezone ambiguity.
    return datetime.utcnow()

def ensure_wechat_enabled():
    # Feature switch guard: keep password login unaffected when disabled.
    if not wechat_settings.WECHAT_OPEN_ENABLED:
        raise HTTPException(status_code=404, detail="WeChat QR login is disabled")

def create_signed_state(session_id: str) -> str:
    # state = nonce + signature, signature binds state to server-side session_id.
    nonce = secrets.token_hex(8)
    payload = f"{session_id}:{nonce}"
    signature = hmac.new(
        wechat_settings.WECHAT_STATE_SIGN_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    return f"{nonce}{signature}"

def verify_signed_state(session_id: str, state_value: str) -> bool:
    # Expected format: 16 hex chars nonce + 32 hex chars signature.
    if not state_value or len(state_value) != 48:
        return False
    nonce = state_value[:16]
    signature = state_value[16:]
    payload = f"{session_id}:{nonce}"
    expected = hmac.new(
        wechat_settings.WECHAT_STATE_SIGN_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:32]
    return hmac.compare_digest(signature, expected)

def wechat_callback_page(title: str, description: str) -> HTMLResponse:
    # Return a standalone safe callback page for mobile browser context.
    escaped_title = title.replace("<", "&lt;").replace(">", "&gt;")
    escaped_description = description.replace("<", "&lt;").replace(">", "&gt;")
    html = f"""
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escaped_title}</title>
    <style>
      body {{
        margin: 0;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f3f4f6;
        color: #111827;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }}
      .card {{
        width: min(92vw, 420px);
        background: #fff;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
      }}
      h1 {{
        margin: 0 0 8px 0;
        font-size: 20px;
      }}
      p {{
        margin: 0;
        line-height: 1.6;
        color: #374151;
      }}
    </style>
  </head>
  <body>
    <div class="card">
      <h1>{escaped_title}</h1>
      <p>{escaped_description}</p>
    </div>
  </body>
</html>
"""
    return HTMLResponse(content=html)

def wechat_get_json(url: str) -> Dict[str, Any]:
    # Minimal HTTP client wrapper with unified error mapping to HTTPException.
    try:
        with urlopen(url, timeout=wechat_settings.WECHAT_HTTP_TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore") if hasattr(exc, "read") else str(exc)
        raise HTTPException(status_code=502, detail=f"WeChat HTTP error: {details}")
    except URLError as exc:
        raise HTTPException(status_code=502, detail=f"WeChat network error: {exc}")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Invalid WeChat response")

    if isinstance(data, dict):
        # WeChat API usually reports business errors via errcode/errmsg in JSON payload.
        errcode = data.get("errcode")
        if errcode not in (None, 0, "0"):
            errmsg = data.get("errmsg", "unknown")
            raise HTTPException(status_code=400, detail=f"WeChat API error: {errcode} {errmsg}")
    return data

def ensure_wechat_auth_tables():
    # Lazy-create tables on first WeChat request to reduce deployment coupling.
    global _wechat_tables_ready
    if _wechat_tables_ready:
        return

    with _wechat_tables_lock:
        # Double-check after acquiring lock to avoid duplicate DDL race.
        if _wechat_tables_ready:
            return

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS auth_user_identity (
                        id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        user_id VARCHAR(50) NOT NULL,
                        provider VARCHAR(32) NOT NULL,
                        provider_user_id VARCHAR(128) NOT NULL,
                        wechat_openid VARCHAR(128) NULL,
                        wechat_unionid VARCHAR(128) NULL,
                        nickname VARCHAR(128) NULL,
                        avatar_url VARCHAR(512) NULL,
                        raw_profile_json JSON NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        created_by VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
                        updated_by VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
                        deleted_at BIGINT NOT NULL DEFAULT 0,
                        last_login_at DATETIME NULL,
                        UNIQUE KEY uq_auth_user_identity_provider_user (provider, provider_user_id),
                        KEY idx_auth_user_identity_user_id (user_id),
                        KEY idx_auth_user_identity_deleted_at (deleted_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS auth_login_session (
                        session_id CHAR(36) PRIMARY KEY,
                        channel VARCHAR(32) NOT NULL,
                        state CHAR(64) NOT NULL,
                        status VARCHAR(32) NOT NULL,
                        user_id VARCHAR(50) NULL,
                        ticket CHAR(64) NULL,
                        ticket_expires_at DATETIME NULL,
                        error_code VARCHAR(64) NULL,
                        error_message VARCHAR(255) NULL,
                        expires_at DATETIME NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        consumed_at DATETIME NULL,
                        created_by VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
                        updated_by VARCHAR(50) NOT NULL DEFAULT 'SYSTEM',
                        deleted_at BIGINT NOT NULL DEFAULT 0,
                        UNIQUE KEY uq_auth_login_session_state (state),
                        UNIQUE KEY uq_auth_login_session_ticket (ticket),
                        KEY idx_auth_login_session_status_exp (status, expires_at),
                        KEY idx_auth_login_session_ticket_exp (ticket, ticket_expires_at),
                        KEY idx_auth_login_session_deleted_at (deleted_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                    """
                )
            conn.commit()
            _wechat_tables_ready = True
        finally:
            conn.close()

def expire_session_if_needed(cursor, session_row: Dict[str, Any]) -> Dict[str, Any]:
    # Translate timed-out pending sessions into EXPIRED deterministically.
    now = utc_now()
    if session_row["status"] == WECHAT_STATUS_PENDING and session_row["expires_at"] <= now:
        cursor.execute(
            """
            UPDATE auth_login_session
            SET status = %s, updated_at = %s, updated_by = %s
            WHERE session_id = %s AND deleted_at = 0
            """,
            (WECHAT_STATUS_EXPIRED, now, SYSTEM_ACTOR, session_row["session_id"]),
        )
        session_row["status"] = WECHAT_STATUS_EXPIRED
    return session_row

class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class WechatQrSessionResponse(BaseModel):
    session_id: str
    qr_url: str
    expires_in: int
    poll_interval_ms: int
    wechat_app_id: str
    wechat_redirect_uri: str
    wechat_scope: str
    state: str

class WechatQrSessionStatusResponse(BaseModel):
    status: str
    expires_in: int
    ticket: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

class WechatExchangeTicketRequest(BaseModel):
    session_id: str
    ticket: str

class UserResponse(UserBase):
    id: str
    created_at: datetime

class ExpenseSummary(BaseModel):
    total_amount: float
    total_count: int
    avg_amount: float
    earliest_date: Optional[str]
    latest_date: Optional[str]

class MonthlyExpense(BaseModel):
    year: str
    month: str
    transaction_count: int
    monthly_total: float
    avg_transaction: float

class CategoryExpense(BaseModel):
    trans_type_name: Optional[str] # From personal_expenses_type
    trans_sub_type_name: Optional[str] # From personal_expenses_type
    count: int
    total_amount: float
    avg_amount: float

class PaymentMethod(BaseModel):
    pay_account: str
    usage_count: int
    total_spent: float
    avg_per_transaction: float

class TimelineData(BaseModel):
    date: str
    daily_total: float
    transaction_count: int

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    # Ensure password is not too long for bcrypt
    if len(plain_password) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Ensure password is not too long for bcrypt
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def get_user_by_username(username: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, username, email, hashed_password, full_name, is_active, created_at FROM expenses_user WHERE username = %s"
            cursor.execute(sql, (username,))
            user_data = cursor.fetchone()
            if user_data:
                return {
                    "id": user_data['id'],
                    "username": user_data['username'],
                    "email": user_data['email'],
                    "hashed_password": user_data['hashed_password'],
                    "full_name": user_data['full_name'],
                    "is_active": user_data['is_active'],
                    "created_at": user_data['created_at'],
                }
            return None
    finally:
        conn.close()

def get_user_by_id(user_id: str):
    # Used by ticket exchange to reconstruct JWT claims from canonical user record.
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, username, email, hashed_password, full_name, is_active, created_at FROM expenses_user WHERE id = %s"
            cursor.execute(sql, (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return {
                    "id": user_data['id'],
                    "username": user_data['username'],
                    "email": user_data['email'],
                    "hashed_password": user_data['hashed_password'],
                    "full_name": user_data['full_name'],
                    "is_active": user_data['is_active'],
                    "created_at": user_data['created_at'],
                }
            return None
    finally:
        conn.close()

def mark_wechat_session_failed(
    session_id: str,
    error_code: str,
    error_message: str,
    status_value: str = WECHAT_STATUS_FAILED,
):
    # Centralized failure writer to keep callback error handling consistent.
    error_code_text = str(error_code) if error_code is not None else None
    error_message_text = str(error_message) if error_message is not None else None
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE auth_login_session
                SET status = %s,
                    error_code = %s,
                    error_message = %s,
                    updated_at = %s,
                    updated_by = %s
                WHERE session_id = %s AND deleted_at = 0
                """,
                (
                    status_value,
                    error_code_text[:64] if error_code_text else None,
                    error_message_text[:255] if error_message_text else None,
                    utc_now(),
                    SYSTEM_ACTOR,
                    session_id,
                ),
            )
        conn.commit()
    finally:
        conn.close()

def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user['hashed_password']):
        return False
    return user

def create_wechat_user(cursor, nickname: Optional[str]) -> str:
    # Create a local placeholder account for first-time WeChat users.
    # Password is random and not intended for direct credential login.
    user_id = str(uuid.uuid4())
    display_name = (nickname or "").strip()[:100]

    while True:
        # Ensure generated username/email do not conflict with existing local users.
        username = f"wx_{secrets.token_hex(4)}"
        email = f"{username}@wx.local"
        cursor.execute(
            "SELECT id FROM expenses_user WHERE username = %s OR email = %s LIMIT 1",
            (username, email),
        )
        if not cursor.fetchone():
            break

    random_password = secrets.token_urlsafe(24)
    hashed_password = get_password_hash(random_password)
    cursor.execute(
        """
        INSERT INTO expenses_user (id, username, email, hashed_password, full_name, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (user_id, username, email, hashed_password, display_name or username, True),
    )
    return user_id

def get_or_create_user_by_wechat_profile(cursor, profile: Dict[str, Any]) -> str:
    # Prefer unionid for cross-app stable identity; fallback to openid.
    openid = (profile.get("openid") or "").strip()
    unionid = (profile.get("unionid") or "").strip()
    provider_user_id = unionid or openid
    if not provider_user_id:
        raise HTTPException(status_code=400, detail="Missing WeChat user identifier")

    now = utc_now()
    profile_json = json.dumps(profile, ensure_ascii=False)
    nickname = (profile.get("nickname") or "").strip()[:128]
    avatar_url = (profile.get("headimgurl") or "").strip()[:512]

    cursor.execute(
        """
        SELECT id, user_id
        FROM auth_user_identity
        WHERE provider = %s AND provider_user_id = %s AND deleted_at = 0
        LIMIT 1
        """,
        (WECHAT_PROVIDER, provider_user_id),
    )
    identity = cursor.fetchone()
    if identity:
        # Existing binding: refresh snapshot fields and login audit timestamp.
        cursor.execute(
            """
            UPDATE auth_user_identity
            SET wechat_openid = %s,
                wechat_unionid = %s,
                nickname = %s,
                avatar_url = %s,
                raw_profile_json = %s,
                last_login_at = %s,
                updated_at = %s,
                updated_by = %s
            WHERE id = %s
            """,
            (
                openid or None,
                unionid or None,
                nickname or None,
                avatar_url or None,
                profile_json,
                now,
                now,
                SYSTEM_ACTOR,
                identity["id"],
            ),
        )
        return identity["user_id"]

    # First login through WeChat: create local user + identity binding.
    user_id = create_wechat_user(cursor, nickname)
    cursor.execute(
        """
        INSERT INTO auth_user_identity (
            user_id, provider, provider_user_id, wechat_openid, wechat_unionid,
            nickname, avatar_url, raw_profile_json, created_at, updated_at,
            created_by, updated_by, deleted_at, last_login_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, %s)
        """,
        (
            user_id,
            WECHAT_PROVIDER,
            provider_user_id,
            openid or None,
            unionid or None,
            nickname or None,
            avatar_url or None,
            profile_json,
            now,
            now,
            SYSTEM_ACTOR,
            SYSTEM_ACTOR,
            now,
        ),
    )
    return user_id

def build_wechat_qr_url(state: str) -> str:
    # Build QRConnect URL for desktop scan flow.
    params = {
        "appid": wechat_settings.WECHAT_OPEN_APP_ID,
        "redirect_uri": wechat_settings.WECHAT_OPEN_REDIRECT_URI,
        "response_type": "code",
        "scope": wechat_settings.WECHAT_OPEN_SCOPE,
        "state": state,
    }
    return f"https://open.weixin.qq.com/connect/qrconnect?{urlencode(params)}#wechat_redirect"

def fetch_wechat_profile(code: str) -> Dict[str, Any]:
    # Step 1: exchange callback code for access_token/openid.
    token_url = (
        "https://api.weixin.qq.com/sns/oauth2/access_token?"
        + urlencode(
            {
                "appid": wechat_settings.WECHAT_OPEN_APP_ID,
                "secret": wechat_settings.WECHAT_OPEN_APP_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            }
        )
    )
    token_data = wechat_get_json(token_url)
    access_token = token_data.get("access_token")
    openid = token_data.get("openid")
    if not access_token or not openid:
        raise HTTPException(status_code=400, detail="Failed to fetch WeChat access token")

    # Step 2: fetch user profile with access_token + openid.
    profile_url = (
        "https://api.weixin.qq.com/sns/userinfo?"
        + urlencode({"access_token": access_token, "openid": openid, "lang": "zh_CN"})
    )
    profile_data = wechat_get_json(profile_url)
    # Some responses include unionid only in token payload; normalize here.
    if "unionid" not in profile_data and token_data.get("unionid"):
        profile_data["unionid"] = token_data.get("unionid")
    return profile_data

def ensure_wechat_runtime():
    # Guard all preconditions in one place for each WeChat API entrypoint.
    ensure_wechat_enabled()
    wechat_settings.validate_enabled_config()
    ensure_wechat_auth_tables()

# --- Authentication Routes ---
@api_router.post("/auth/wechat/qr-session", response_model=WechatQrSessionResponse)
async def create_wechat_qr_session():
    # Entrypoint for browser to bootstrap QR login session.
    ensure_wechat_runtime()

    # Step 1: generate local session identity and signed state.
    session_id = str(uuid.uuid4())
    # state is signed locally to mitigate callback tampering/replay mixups.
    state = create_signed_state(session_id)
    now = utc_now()
    expires_at = now + timedelta(seconds=wechat_settings.WECHAT_QR_SESSION_TTL_SECONDS)
    qr_url = build_wechat_qr_url(state)

    # Step 2: persist session as PENDING.
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Persist only server-trusted state. JWT is never exposed at this stage.
            cursor.execute(
                """
                INSERT INTO auth_login_session (
                    session_id, channel, state, status, expires_at, created_at, updated_at,
                    created_by, updated_by, deleted_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
                """,
                (
                    session_id,
                    WECHAT_CHANNEL,
                    state,
                    WECHAT_STATUS_PENDING,
                    expires_at,
                    now,
                    now,
                    SYSTEM_ACTOR,
                    SYSTEM_ACTOR,
                ),
            )
        conn.commit()
    finally:
        conn.close()

    # Step 3: return QR metadata to frontend.
    # Client receives both direct qr_url and WxLogin constructor parameters.
    return {
        "session_id": session_id,
        "qr_url": qr_url,
        "expires_in": wechat_settings.WECHAT_QR_SESSION_TTL_SECONDS,
        "poll_interval_ms": WECHAT_POLL_INTERVAL_MS,
        "wechat_app_id": wechat_settings.WECHAT_OPEN_APP_ID,
        "wechat_redirect_uri": wechat_settings.WECHAT_OPEN_REDIRECT_URI,
        "wechat_scope": wechat_settings.WECHAT_OPEN_SCOPE,
        "state": state,
    }

@api_router.get("/auth/wechat/qr-session/{session_id}", response_model=WechatQrSessionStatusResponse)
async def get_wechat_qr_session_status(session_id: str):
    # Polled by browser until CONFIRMED/FAILED/EXPIRED.
    ensure_wechat_runtime()

    # Step 1: load session row by id.
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT session_id, status, expires_at, ticket, ticket_expires_at, error_code, error_message
                FROM auth_login_session
                WHERE session_id = %s AND deleted_at = 0
                LIMIT 1
                """,
                (session_id,),
            )
            session_row = cursor.fetchone()
            if not session_row:
                raise HTTPException(status_code=404, detail="QR session not found")

            # Keep state transition deterministic on read path.
            session_row = expire_session_if_needed(cursor, session_row)
        conn.commit()
    finally:
        conn.close()

    # Step 2: compute derived response fields.
    now = utc_now()
    expires_in = max(0, int((session_row["expires_at"] - now).total_seconds()))
    ticket = None
    if session_row["status"] == WECHAT_STATUS_CONFIRMED and session_row["ticket_expires_at"] and session_row["ticket_expires_at"] > now:
        # Ticket is only returned while still valid.
        ticket = session_row["ticket"]

    return {
        "status": session_row["status"],
        "expires_in": expires_in,
        "ticket": ticket,
        "error_code": session_row.get("error_code"),
        "error_message": session_row.get("error_message"),
    }

@api_router.post("/auth/wechat/exchange-ticket", response_model=Token)
async def exchange_wechat_ticket(payload: WechatExchangeTicketRequest):
    # One-time exchange: browser turns short-lived ticket into regular JWT.
    ensure_wechat_runtime()
    now = utc_now()

    # Step 1: lock session row and validate exchange preconditions.
    conn = get_db_connection()
    user_id = None
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT session_id, status, user_id, ticket, ticket_expires_at, expires_at
                FROM auth_login_session
                WHERE session_id = %s AND deleted_at = 0
                FOR UPDATE
                """,
                (payload.session_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="QR session not found")
            row = expire_session_if_needed(cursor, row)
            if row["status"] != WECHAT_STATUS_CONFIRMED:
                raise HTTPException(status_code=401, detail=f"QR session is not exchangeable: {row['status']}")
            if row["ticket"] != payload.ticket:
                raise HTTPException(status_code=401, detail="Invalid login ticket")
            if not row["ticket_expires_at"] or row["ticket_expires_at"] <= now:
                raise HTTPException(status_code=401, detail="Login ticket expired")
            user_id = row["user_id"]
            if not user_id:
                raise HTTPException(status_code=400, detail="Login session has no user")

            # Mark consumed atomically inside same transaction to block replay.
            cursor.execute(
                """
                UPDATE auth_login_session
                SET status = %s, consumed_at = %s, updated_at = %s, updated_by = %s
                WHERE session_id = %s AND deleted_at = 0
                """,
                (WECHAT_STATUS_CONSUMED, now, now, SYSTEM_ACTOR, payload.session_id),
            )
        conn.commit()
    finally:
        conn.close()

    # Step 2: mint JWT via existing auth model.
    # Reuse existing JWT issuance model to keep downstream auth unchanged.
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username'], "user_id": user['id']},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/wechat/callback")
async def wechat_callback(
    code: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
):
    # This endpoint is called by WeChat in mobile browser context.
    if not wechat_settings.WECHAT_OPEN_ENABLED:
        return wechat_callback_page("微信登录未启用", "该环境未启用微信扫码登录。")

    # Step 0: runtime validation and lazy DDL ensure.
    try:
        wechat_settings.validate_enabled_config()
        ensure_wechat_auth_tables()
    except Exception as exc:
        return wechat_callback_page("微信登录暂不可用", str(exc))

    if not state:
        return wechat_callback_page("登录失败", "缺少回调参数 state。")

    # Step 1: find session by callback state.
    conn = get_db_connection()
    session_row = None
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT session_id, state, status, expires_at
                FROM auth_login_session
                WHERE state = %s AND deleted_at = 0
                LIMIT 1
                """,
                (state,),
            )
            session_row = cursor.fetchone()
        conn.commit()
    finally:
        conn.close()

    # Validate callback against local session and signed state.
    if not session_row:
        return wechat_callback_page("登录失败", "登录会话不存在或已失效。")
    if not verify_signed_state(session_row["session_id"], state):
        mark_wechat_session_failed(session_row["session_id"], "INVALID_STATE", "Invalid callback state signature")
        return wechat_callback_page("登录失败", "state 校验失败，请重新扫码。")
    if session_row["status"] in (WECHAT_STATUS_CONSUMED, WECHAT_STATUS_CONFIRMED):
        return wechat_callback_page("登录已确认", "扫码信息已处理，请回到电脑端继续。")
    if session_row["expires_at"] <= utc_now():
        mark_wechat_session_failed(
            session_row["session_id"],
            "EXPIRED",
            "QR session expired before callback",
            status_value=WECHAT_STATUS_EXPIRED,
        )
        return wechat_callback_page("二维码已过期", "请在电脑端刷新二维码后重试。")
    if not code:
        mark_wechat_session_failed(session_row["session_id"], "MISSING_CODE", "Missing code in callback")
        return wechat_callback_page("登录失败", "未获取到微信授权 code。")

    # Step 2: exchange code and fetch profile from WeChat.
    # Call WeChat APIs to exchange code and fetch profile.
    try:
        profile = fetch_wechat_profile(code)
    except HTTPException as exc:
        mark_wechat_session_failed(session_row["session_id"], "WECHAT_API_ERROR", exc.detail)
        return wechat_callback_page("登录失败", f"微信授权失败：{exc.detail}")
    except Exception as exc:
        mark_wechat_session_failed(session_row["session_id"], "WECHAT_API_ERROR", str(exc))
        return wechat_callback_page("登录失败", "微信授权过程中发生异常，请稍后重试。")

    # Step 3: bind user and issue one-time ticket.
    conn = get_db_connection()
    try:
        now = utc_now()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT session_id, status
                FROM auth_login_session
                WHERE session_id = %s AND deleted_at = 0
                FOR UPDATE
                """,
                (session_row["session_id"],),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="QR session not found")
            if row["status"] in (WECHAT_STATUS_CONSUMED, WECHAT_STATUS_CONFIRMED):
                conn.commit()
                return wechat_callback_page("登录已确认", "扫码信息已处理，请回到电脑端继续。")

            # Resolve local user id by identity binding, creating on first login.
            user_id = get_or_create_user_by_wechat_profile(cursor, profile)
            # Ticket is short-lived and single-use; JWT will be minted on exchange.
            ticket = secrets.token_urlsafe(32)[:64]
            ticket_expires_at = now + timedelta(seconds=wechat_settings.WECHAT_LOGIN_TICKET_TTL_SECONDS)
            cursor.execute(
                """
                UPDATE auth_login_session
                SET status = %s,
                    user_id = %s,
                    ticket = %s,
                    ticket_expires_at = %s,
                    error_code = NULL,
                    error_message = NULL,
                    updated_at = %s,
                    updated_by = %s
                WHERE session_id = %s AND deleted_at = 0
                """,
                (
                    WECHAT_STATUS_CONFIRMED,
                    user_id,
                    ticket,
                    ticket_expires_at,
                    now,
                    SYSTEM_ACTOR,
                    session_row["session_id"],
                ),
            )
        conn.commit()
    except HTTPException as exc:
        conn.rollback()
        mark_wechat_session_failed(session_row["session_id"], "DB_ERROR", exc.detail)
        return wechat_callback_page("登录失败", "服务端处理失败，请重试。")
    except Exception as exc:
        conn.rollback()
        mark_wechat_session_failed(session_row["session_id"], "DB_ERROR", str(exc))
        return wechat_callback_page("登录失败", "服务端处理失败，请稍后再试。")
    finally:
        conn.close()

    # Step 4: return mobile-side callback page and let browser poller continue.
    return wechat_callback_page("登录成功", "微信扫码已确认，请回到电脑端继续登录。")

@api_router.post("/auth/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username'], "user_id": user['id']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=UserResponse)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Fetch user data from DB by username to ensure it's active
    user_data = get_user_by_username(username)
    if not user_data or user_data['id'] != user_id:
        raise HTTPException(status_code=404, detail="User not found or token mismatch")
    
    return user_data

# --- Expenses Data Routes ---
@api_router.get("/expenses/summary", response_model=ExpenseSummary)
async def get_expenses_summary(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                COALESCE(SUM(trans_amount), 0) AS total_amount,
                COALESCE(COUNT(id), 0) AS total_count,
                COALESCE(AVG(trans_amount), 0) AS avg_amount,
                MIN(trans_datetime) AS earliest_date,
                MAX(trans_datetime) AS latest_date
            FROM personal_expenses_final
            WHERE deleted_at = 0
            """
            
            if username != 'admin':
                sql += " AND user_id = %s"
                cursor.execute(sql, (str(user_id),))
            else:
                cursor.execute(sql)
                
            result = cursor.fetchone()
            if result and result['earliest_date']:
                result['earliest_date'] = result['earliest_date'].strftime("%Y-%m-%d")
            if result and result['latest_date']:
                result['latest_date'] = result['latest_date'].strftime("%Y-%m-%d")
            return result
    finally:
        conn.close()

@api_router.get("/expenses/monthly", response_model=List[MonthlyExpense])
async def get_monthly_expenses(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                trans_year AS year,
                trans_month AS month,
                COUNT(id) AS transaction_count,
                SUM(trans_amount) AS monthly_total,
                AVG(trans_amount) AS avg_transaction
            FROM personal_expenses_final
            WHERE deleted_at = 0
            """
            
            if username != 'admin':
                sql += " AND user_id = %s"
                params = (str(user_id),)
            else:
                params = ()
                
            sql += " GROUP BY trans_year, trans_month ORDER BY trans_year DESC, trans_month DESC"
            
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()

@api_router.get("/expenses/categories", response_model=List[CategoryExpense])
async def get_category_expenses(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                pet.trans_type_name,
                pet.trans_sub_type_name,
                COUNT(pef.id) AS count,
                SUM(pef.trans_amount) AS total_amount,
                AVG(pef.trans_amount) AS avg_amount
            FROM personal_expenses_final AS pef
            JOIN personal_expenses_type AS pet
                ON pef.trans_code = pet.trans_code AND pef.trans_sub_code = pet.trans_sub_code
            WHERE pef.deleted_at = 0
            """
            
            if username != 'admin':
                sql += " AND pef.user_id = %s"
                params = (str(user_id),)
            else:
                params = ()
                
            sql += " GROUP BY pet.trans_type_name, pet.trans_sub_type_name ORDER BY total_amount DESC"
            
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()

@api_router.get("/expenses/payment-methods", response_model=List[PaymentMethod])
async def get_payment_method_expenses(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                pay_account,
                COUNT(id) AS usage_count,
                SUM(trans_amount) AS total_spent,
                AVG(trans_amount) AS avg_per_transaction
            FROM personal_expenses_final
            WHERE deleted_at = 0
            """
            
            if username != 'admin':
                sql += " AND user_id = %s"
                params = (str(user_id),)
            else:
                params = ()
                
            sql += " GROUP BY pay_account ORDER BY total_spent DESC"
            
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()

@api_router.get("/expenses/timeline", response_model=List[TimelineData])
async def get_expenses_timeline(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            SELECT
                trans_date AS date,
                SUM(trans_amount) AS daily_total,
                COUNT(id) AS transaction_count
            FROM personal_expenses_final
            WHERE deleted_at = 0
            """
            
            if username != 'admin':
                sql += " AND user_id = %s"
                params = (str(user_id),)
            else:
                params = ()
                
            sql += " GROUP BY trans_date ORDER BY trans_date ASC"
            
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()

# --- Visualization Routes ---
@api_router.get("/expenses/stardust")
async def get_expenses_stardust(current_user: dict = Depends(read_users_me)):
    user_id = current_user['id']
    username = current_user['username']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch aggregated data for graph: Category -> SubCategory -> Amount
            sql = """
            SELECT
                pet.trans_type_name,
                pet.trans_sub_type_name,
                SUM(pef.trans_amount) AS total_amount
            FROM personal_expenses_final AS pef
            JOIN personal_expenses_type AS pet
                ON pef.trans_code = pet.trans_code AND pef.trans_sub_code = pet.trans_sub_code
            WHERE pef.deleted_at = 0
            """
            
            if username != 'admin':
                sql += " AND pef.user_id = %s"
                params = (str(user_id),)
            else:
                params = ()
                
            sql += " GROUP BY pet.trans_type_name, pet.trans_sub_type_name"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Transform to Graph Data
            nodes = []
            links = []
            categories = []
            
            # Root Node (User)
            root_name = "Total Expenses"
            total_sum = sum(row['total_amount'] for row in rows)
            nodes.append({
                "id": "root",
                "name": root_name,
                "symbolSize": 50,
                "value": total_sum,
                "category": 0,
                "label": {"show": True}
            })
            categories.append({"name": root_name})
            
            # Process Categories and SubCategories
            cat_map = {} # To track unique categories
            cat_set = set() # Use a set for unique check
            cat_index = 1 
            
            for row in rows:
                cat_name = row['trans_type_name']
                
                # Add Category Node if not exists
                if cat_name not in cat_set:
                    cat_id = f"cat_{cat_name}"
                    nodes.append({
                        "id": cat_id,
                        "name": cat_name,
                        "symbolSize": 30, # Base size, will adjust later if needed
                        "value": 0, # Accumulate
                        "category": cat_index,
                        "label": {"show": True}
                    })
                    links.append({"source": "root", "target": cat_id})
                    categories.append({"name": cat_name})
                    cat_map[cat_name] = len(nodes) - 1 # Index in nodes array
                    cat_set.add(cat_name)
                    cat_index += 1
            
            # Second pass to add sub-categories and accumulate values
            for row in rows:
                cat_name = row['trans_type_name']
                sub_cat_name = row['trans_sub_type_name']
                amount = float(row['total_amount'])

                # Update Category Node Value
                cat_node_idx = cat_map[cat_name]
                nodes[cat_node_idx]["value"] += amount
                
                # Add SubCategory Node
                sub_cat_id = f"sub_{cat_name}_{sub_cat_name}"
                nodes.append({
                    "id": sub_cat_id,
                    "name": sub_cat_name,
                    "symbolSize": 10 + (amount / total_sum) * 40, # Dynamic size
                    "value": amount,
                    "category": nodes[cat_node_idx]["category"], # Use parent's category index
                    "label": {"show": amount > (total_sum * 0.01)} # Only show label if > 1%
                })
                links.append({"source": f"cat_{cat_name}", "target": sub_cat_id})

            # Adjust category node sizes finally
            for node in nodes:
                if node["id"].startswith("cat_"):
                     node["symbolSize"] = 20 + (node["value"] / total_sum) * 60

            return {
                "nodes": nodes,
                "links": links,
                "categories": categories
            }

    finally:
        conn.close()

# Validate WeChat config early when feature is enabled.
if wechat_settings.WECHAT_OPEN_ENABLED:
    wechat_settings.validate_enabled_config()

# Include the router in the app
app.include_router(api_router)
