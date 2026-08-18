# Multi-stage / Production Dockerfile for AquaSentinel on Render
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy backend, scripts, and pre-built frontend
COPY backend/ /app/backend/
COPY scripts/ /app/scripts/
COPY frontend/dist/ /app/frontend/dist/
COPY .python-version /app/.python-version

# Expose port
EXPOSE 8000

# Seed database baseline on startup if empty, then run uvicorn
CMD sh -c "python scripts/seed_data.py && uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
