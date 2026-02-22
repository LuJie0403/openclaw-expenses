#!/bin/bash
# Update and redeploy an existing installation.
# This script should be run on the server inside the project directory.

set -Eeuo pipefail

echo "[update] Fetching latest code from origin..."
git fetch origin

echo "[update] Resetting local branch to match origin/master..."
git reset --hard origin/master

echo "[update] Code updated. Triggering full deployment script..."
# Run the full-deploy script to handle dependencies, build, and restart
# Use the same environment variables as the full deploy.
APP_ENV="${APP_ENV:-production}" \
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}" \
BACKEND_PORT="${BACKEND_PORT:-8000}" \
bash full-deploy.sh

echo "[update] Update deployment process finished."
