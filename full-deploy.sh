#!/bin/bash
# One-command deploy script (backend + frontend build)

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

APP_ENV="${APP_ENV:-development}"
BACKEND_VENV_DIR="${BACKEND_VENV_DIR:-venv}"
BACKEND_REQUIREMENTS="${BACKEND_REQUIREMENTS:-requirements.txt}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_REGISTRY="${FRONTEND_REGISTRY:-https://registry.npmmirror.com}"
PNPM_VERSION="${PNPM_VERSION:-10.28.2}"
RELOAD_NGINX="${RELOAD_NGINX:-false}"
HEALTH_CHECK_URL="${HEALTH_CHECK_URL:-http://${BACKEND_HOST}:${BACKEND_PORT}/api/health}"
DIST_LINK_PATH="${DIST_LINK_PATH:-$ROOT_DIR/dist/frontend}"
LOGIN_PROBE_ENABLED="${LOGIN_PROBE_ENABLED:-true}"
LOGIN_PROBE_URL="${LOGIN_PROBE_URL:-http://${BACKEND_HOST}:${BACKEND_PORT}/api/auth/login}"
LOGIN_PROBE_TIMEOUT="${LOGIN_PROBE_TIMEOUT:-8}"

log() {
  echo "[deploy] $*"
}

die() {
  echo "[deploy][error] $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing command: $1"
}

resolve_pnpm_cmd() {
  if command -v pnpm >/dev/null 2>&1; then
    PNPM_CMD=(pnpm)
    return
  fi

  require_cmd corepack
  corepack enable >/dev/null 2>&1 || true
  corepack prepare "pnpm@${PNPM_VERSION}" --activate >/dev/null 2>&1 || true

  if command -v pnpm >/dev/null 2>&1; then
    PNPM_CMD=(pnpm)
    return
  fi

  # Fallback for environments where shim is not on PATH
  PNPM_CMD=(corepack pnpm)
}

wait_for_health() {
  local retries="${1:-20}"
  local sleep_seconds="${2:-1}"
  local i
  for i in $(seq 1 "$retries"); do
    if curl -fsS "$HEALTH_CHECK_URL" >/dev/null 2>&1; then
      log "Backend health check passed: $HEALTH_CHECK_URL"
      return 0
    fi
    sleep "$sleep_seconds"
  done
  return 1
}

find_listen_pid_by_port() {
  local port="$1"

  if command -v ss >/dev/null 2>&1; then
    ss -ltnp 2>/dev/null | awk -v port=":$port" '
      $4 ~ port"$" || $4 ~ port"[[:space:]]" {
        if (match($0, /pid=[0-9]+/)) {
          print substr($0, RSTART + 4, RLENGTH - 4)
          exit
        }
      }
    '
    return 0
  fi

  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | head -n 1
    return 0
  fi
}

cleanup_backend_port() {
  local pid
  pid="$(find_listen_pid_by_port "$BACKEND_PORT" || true)"
  if [ -n "$pid" ]; then
    log "Port ${BACKEND_PORT} is occupied by PID ${pid}, stopping it..."
    kill "$pid" >/dev/null 2>&1 || true
    sleep 1
  fi

  pid="$(find_listen_pid_by_port "$BACKEND_PORT" || true)"
  if [ -n "$pid" ]; then
    log "Port ${BACKEND_PORT} is still occupied by PID ${pid}, force killing..."
    kill -9 "$pid" >/dev/null 2>&1 || true
    sleep 1
  fi

  pid="$(find_listen_pid_by_port "$BACKEND_PORT" || true)"
  [ -z "$pid" ] || die "Port ${BACKEND_PORT} is still occupied by PID ${pid}"
}

probe_login_endpoint() {
  [ "$LOGIN_PROBE_ENABLED" = "true" ] || return 0

  local response_file status body_preview payload
  response_file="$(mktemp)"
  payload='{"username":"__deploy_probe__","password":"__deploy_probe__"}'
  status="$(curl -sS -o "$response_file" -w "%{http_code}" \
    -H "Content-Type: application/json" \
    --max-time "$LOGIN_PROBE_TIMEOUT" \
    --data "$payload" \
    "$LOGIN_PROBE_URL" || true)"

  case "$status" in
    200|401|422)
      log "Login probe passed (${status}): $LOGIN_PROBE_URL"
      ;;
    "")
      rm -f "$response_file"
      die "Login probe failed: no HTTP response from $LOGIN_PROBE_URL"
      ;;
    *)
      body_preview="$(head -c 200 "$response_file" | tr '\n' ' ')"
      rm -f "$response_file"
      die "Login probe failed (${status}): $LOGIN_PROBE_URL; response: ${body_preview}"
      ;;
  esac

  rm -f "$response_file"
}

log "Starting deployment from: $ROOT_DIR"
require_cmd python3
require_cmd node
require_cmd curl

if [ ! -d "$BACKEND_DIR" ] || [ ! -d "$FRONTEND_DIR" ]; then
  die "Project structure not found under $ROOT_DIR"
fi

resolve_pnpm_cmd
log "Using pnpm command: ${PNPM_CMD[*]}"
"${PNPM_CMD[@]}" -v

log "Deploying backend..."
cd "$BACKEND_DIR"

if [ ! -d "$BACKEND_VENV_DIR" ]; then
  log "Creating backend virtualenv: $BACKEND_VENV_DIR"
  python3.9 -m venv "$BACKEND_VENV_DIR"
fi

BACKEND_PYTHON="$BACKEND_DIR/$BACKEND_VENV_DIR/bin/python"
BACKEND_UVICORN="$BACKEND_DIR/$BACKEND_VENV_DIR/bin/uvicorn"

[ -x "$BACKEND_PYTHON" ] || die "Virtualenv python not found: $BACKEND_PYTHON"
[ -f "$BACKEND_REQUIREMENTS" ] || die "Requirements file not found: $BACKEND_REQUIREMENTS"

if [ ! -f ".env.${APP_ENV}" ]; then
  if [ -f ".env.${APP_ENV}.example" ]; then
    log "Creating backend env file: .env.${APP_ENV} (from example)"
    cp ".env.${APP_ENV}.example" ".env.${APP_ENV}"
  elif [ -f ".env.example" ]; then
    log "Creating backend env file: .env.${APP_ENV} (from .env.example)"
    cp ".env.example" ".env.${APP_ENV}"
  else
    die "Missing env template (.env.${APP_ENV}.example or .env.example)"
  fi
fi

log "Installing backend dependencies..."
"$BACKEND_PYTHON" -m pip install --upgrade pip setuptools wheel
"$BACKEND_PYTHON" -m pip install -r "$BACKEND_REQUIREMENTS"
[ -x "$BACKEND_UVICORN" ] || die "Virtualenv uvicorn not found after dependency install"

log "Stopping old backend process (if exists)..."
pkill -f "$BACKEND_UVICORN app.main:app" >/dev/null 2>&1 || true
pkill -f "uvicorn app.main:app --host $BACKEND_HOST --port $BACKEND_PORT" >/dev/null 2>&1 || true
cleanup_backend_port

log "Starting backend: app.main:app (${BACKEND_HOST}:${BACKEND_PORT})"
nohup "$BACKEND_UVICORN" app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" > backend.log 2>&1 &
BACKEND_PID=$!
log "Backend started with PID: $BACKEND_PID"

if ! wait_for_health 20 1; then
  tail -n 80 backend.log || true
  die "Backend health check failed: $HEALTH_CHECK_URL"
fi
probe_login_endpoint

log "Deploying frontend with pnpm..."
cd "$FRONTEND_DIR"
"${PNPM_CMD[@]}" install --registry "$FRONTEND_REGISTRY"

if ! "${PNPM_CMD[@]}" build; then
  log "pnpm build failed, fallback to: pnpm exec vite build"
  "${PNPM_CMD[@]}" exec vite build
fi

mkdir -p "$(dirname "$DIST_LINK_PATH")"
ln -sfn "$FRONTEND_DIR/dist" "$DIST_LINK_PATH"
log "Frontend dist symlink updated: $DIST_LINK_PATH -> $FRONTEND_DIR/dist"

if [ "$RELOAD_NGINX" = "true" ]; then
  if command -v systemctl >/dev/null 2>&1; then
    if sudo systemctl reload nginx; then
      log "Nginx reloaded."
    else
      die "Failed to reload nginx via systemctl."
    fi
  else
    die "RELOAD_NGINX=true but systemctl not found."
  fi
fi

log "Deployment completed successfully."
echo
echo "Backend health: $HEALTH_CHECK_URL"
echo "Backend docs:   http://${BACKEND_HOST}:${BACKEND_PORT}/docs"
echo "Frontend dist:  $FRONTEND_DIR/dist"
