"""
Centralized configuration for the AquaSentinel backend.
All values are overridable via environment variables (.env file in dev).
"""
import os
from functools import lru_cache


class Settings:
    # Database - SQLite by default for zero-setup local dev.
    # Swap to Postgres by setting DATABASE_URL, e.g.:
    #   postgresql+psycopg2://user:pass@host:5432/aquasentinel
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./aquasentinel.db")

    # Anomaly detection tuning
    BASELINE_WINDOW: int = int(os.getenv("BASELINE_WINDOW", "60"))       # readings used to build baseline
    ZSCORE_THRESHOLD: float = float(os.getenv("ZSCORE_THRESHOLD", "3.0"))  # |z| above this = anomalous
    MIN_READINGS_FOR_BASELINE: int = int(os.getenv("MIN_READINGS_FOR_BASELINE", "10"))

    # Sensor plausibility bounds (used for basic sensor-sanity checks)
    PH_MIN, PH_MAX = 0.0, 14.0
    TDS_MIN, TDS_MAX = 0.0, 5000.0        # ppm
    TURBIDITY_MIN, TURBIDITY_MAX = 0.0, 3000.0  # NTU
    TEMP_MIN, TEMP_MAX = -5.0, 60.0       # Celsius

    # n8n integration: backend POSTs here when a new anomaly event is created.
    N8N_WEBHOOK_URL: str = os.getenv("N8N_WEBHOOK_URL", "")

    # Shared secret so the ingest endpoint and n8n callback aren't wide open.
    # Prototype-level auth only (per SRS Section 26) - not full RBAC.
    API_KEY: str = os.getenv("AQUASENTINEL_API_KEY", "changeme-dev-key")

    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")


@lru_cache
def get_settings() -> Settings:
    return Settings()
