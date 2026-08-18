#!/usr/bin/env bash
set -e

PORT=${PORT:-8000}
echo "🌊 AquaSentinel: Starting on Port $PORT"

# Seed baseline on initial boot if empty
python scripts/seed_data.py

# Launch FastAPI
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
