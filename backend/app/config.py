import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "AquaSentinel Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Storage
    DATABASE_URL: str = "sqlite:///./aquasentinel.db"
    
    # Device Identification
    DEFAULT_DEVICE_ID: str = "AQUA-01"
    WATER_BODY_NAME: str = "Simulated Reservoir 01"
    
    # Anomaly Engine Config
    BASELINE_WINDOW_SIZE: int = 50          # Number of telemetry records for rolling baseline
    Z_SCORE_THRESHOLD: float = 2.5          # Z-score cutoff for statistical anomaly
    TURBIDITY_THRESHOLD_NTU: float = 15.0   # Absolute threshold for drinking/ambient water
    EC_THRESHOLD_US_CM: float = 800.0       # Absolute threshold for electrical conductivity
    PH_MIN_NORMAL: float = 6.5
    PH_MAX_NORMAL: float = 8.5
    
    # Event Engine Config
    EVENT_COOLDOWN_SECONDS: int = 30        # Prevent duplicate alerts within this window
    
    # LLM & Agent Config
    LLM_PROVIDER: str = "sarvam"            # "sarvam" or "fallback"
    SARVAM_API_KEY: Optional[str] = None
    SARVAM_MODEL_NAME: str = "sarvam-2b"
    SARVAM_API_URL: str = "https://api.sarvam.ai/v1/chat/completions"
    
    # Scientific Claim enforced across all system outputs
    SCIENTIFIC_DISCLAIMER: str = (
        "The system detects anomalous water-quality patterns and generates "
        "evidence-based early warnings. It does not claim to identify a specific "
        "contaminant without validated labeled data."
    )


settings = Settings()
