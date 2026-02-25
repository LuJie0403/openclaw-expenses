#!/bin/bash
# Update and redeploy an existing installation.
# This script should be run on the server inside the project directory.

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="${BACKUP_ROOT:-/home/openclaw-expenses/backups}"
BACKUP_PREFIX="${BACKUP_PREFIX:-openclaw-expenses_backup}"
SKIP_CODE_BACKUP="${SKIP_CODE_BACKUP:-false}"
BACKUP_TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_PREFIX}_${BACKUP_TIMESTAMP}"

log() {
  echo "[update] $*"
}

die() {
  echo "[update][error] $*" >&2
  exit 1
}

create_code_backup() {
  [ "$SKIP_CODE_BACKUP" = "true" ] && {
    log "Skipping code backup (SKIP_CODE_BACKUP=true)."
    return 0
  }

  mkdir -p "$BACKUP_ROOT" || die "Failed to create backup root: $BACKUP_ROOT"
  [ -w "$BACKUP_ROOT" ] || die "Backup root is not writable: $BACKUP_ROOT"
  [ ! -e "$BACKUP_DIR" ] || die "Backup path already exists: $BACKUP_DIR"

  log "Creating backup snapshot: $BACKUP_DIR"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a \
      --exclude ".git" \
      --exclude "frontend/node_modules" \
      --exclude "backend/venv" \
      --exclude "dist/frontend" \
      --exclude "*.log" \
      "$ROOT_DIR/" "$BACKUP_DIR/" || die "Backup failed via rsync"
  else
    mkdir -p "$BACKUP_DIR" || die "Failed to create backup path: $BACKUP_DIR"
    tar -C "$ROOT_DIR" \
      --exclude ".git" \
      --exclude "frontend/node_modules" \
      --exclude "backend/venv" \
      --exclude "dist/frontend" \
      --exclude "*.log" \
      -cf - . | tar -C "$BACKUP_DIR" -xf - || die "Backup failed via tar"
  fi

  log "Backup completed: $BACKUP_DIR"
}

create_code_backup

log "Fetching latest code from origin..."
git fetch origin

log "Resetting local branch to match origin/master..."
git reset --hard origin/master

log "Code updated. Triggering full deployment script..."
# Run the full-deploy script to handle dependencies, build, and restart
# Use the same environment variables as the full deploy.
APP_ENV="${APP_ENV:-production}" \
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}" \
BACKEND_PORT="${BACKEND_PORT:-8000}" \
bash full-deploy.sh

log "Update deployment process finished."
