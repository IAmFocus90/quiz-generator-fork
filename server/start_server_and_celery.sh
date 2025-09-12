#!/bin/bash

# Enable job control
set -m

echo "[STARTUP] Launching Celery worker..."
celery -A server.celery_config.celery_app worker --loglevel=info --concurrency=1 &

echo "[STARTUP] Starting FastAPI with Uvicorn..."
exec uvicorn server.main:app --host 0.0.0.0 --port 10000
