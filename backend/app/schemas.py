from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------- Readings ----------

class ReadingIn(BaseModel):
    """Payload the ESP32 sends via HTTP POST (SRS Section 4)."""
    node_id: str = Field(default="node-01")
    timestamp: Optional[datetime] = None  # backend stamps server time if omitted
    ph: float
    tds: float
    turbidity: float
    temperature: float


class ReadingOut(BaseModel):
    id: int
    node_id: str
    timestamp: datetime
    ph: float
    tds: float
    turbidity: float
    temperature: float
    status_flags: Optional[Dict[str, str]] = None

    class Config:
        from_attributes = True


class IngestResponse(BaseModel):
    reading: ReadingOut
    anomaly_event: Optional["EventOut"] = None


# ---------- Events ----------

class EventOut(BaseModel):
    event_id: str
    node_id: str
    timestamp: datetime
    status: str
    severity: Optional[str] = None
    parameters_affected: Optional[Dict[str, Any]] = None
    anomaly_score: Optional[float] = None
    baseline_comparison: Optional[Dict[str, Any]] = None
    investigation_status: str
    investigation_result: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventUpdate(BaseModel):
    """Body n8n PATCHes back after the agent finishes investigating."""
    investigation_status: Optional[str] = None
    investigation_result: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    status: Optional[str] = None


# ---------- Agent tool responses ----------

class CurrentReadingsTool(BaseModel):
    node_id: str
    timestamp: datetime
    ph: float
    tds: float
    turbidity: float
    temperature: float


class HistoricalReadingsTool(BaseModel):
    node_id: str
    baseline: Dict[str, float]      # mean/std per parameter
    recent_readings: List[ReadingOut]


class SensorStatusTool(BaseModel):
    node_id: str
    ok: bool
    issues: List[str]
    last_reading_age_seconds: Optional[float] = None


IngestResponse.model_rebuild()
