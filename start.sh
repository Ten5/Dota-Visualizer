#!/bin/bash
set -e

# Support dynamic PORT assignment from cloud host or fallback to 8050
PORT="${PORT:-8050}"

# Launch Celery render worker in background if REDIS_URL is configured
if [ -n "$REDIS_URL" ]; then
    echo "Starting background Celery render worker..."
    celery -A src.backend.worker.celery_app worker --loglevel=info -c 1 &
fi

# Launch FastAPI Uvicorn Server in foreground
echo "Starting FastAPI gateway server on port $PORT..."
exec uvicorn src.backend.main:app --host 0.0.0.0 --port "$PORT"
