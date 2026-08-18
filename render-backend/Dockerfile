# Standalone Production Dockerfile for AquaSentinel Backend on Render
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/

EXPOSE 8000

CMD sh -c "python scripts/seed_data.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
