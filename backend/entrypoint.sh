#!/bin/sh
set -e

python -m app.migrations.run_migrations

if [ "$SEED_ON_START" = "true" ]; then
    python -m app.seed
fi

if [ "$SEED_DEMO" = "true" ]; then
    python -m app.seed_demo || echo "[seed demo] omitido"
fi

RELOAD_FLAG=""
[ "$RELOAD" = "true" ] && RELOAD_FLAG="--reload"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" $RELOAD_FLAG
