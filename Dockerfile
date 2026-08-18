# ============================================================
# Stage 1: Build React frontend
# ============================================================
FROM node:22-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm ci

COPY frontend/ ./

RUN npm run build


# ============================================================
# Stage 2: Python backend + built frontend
# ============================================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*


# Backend dependencies
COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt


# Backend
COPY backend/ /app/backend/

# Scripts
COPY scripts/ /app/scripts/

# Built React frontend from Stage 1
COPY --from=frontend-build /app/frontend/dist/ /app/frontend/dist/

COPY .python-version /app/.python-version


EXPOSE 8000

CMD sh -c "python scripts/seed_data.py && uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"