"""
Database schema - Workstream B (Backend & Database).

Two tables per the Prototype SRS (Section 6):
  - readings: raw + validated sensor readings from the ESP32 node(s).
  - events:   anomaly events created by the detector, later enriched by
              the investigation agent via n8n (FR-BACK-04).
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text,
)
from sqlalchemy.orm import relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EventStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    RESOLVED = "RESOLVED"


class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, index=True, nullable=False, default="node-01")
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False, default=_utcnow)

    ph = Column(Float, nullable=False)
    tds = Column(Float, nullable=False)          # ppm
    turbidity = Column(Float, nullable=False)     # NTU
    temperature = Column(Float, nullable=False)   # Celsius

    # Basic sensor-sanity flags set by the plausibility check, e.g.
    # {"ph": "ok", "tds": "out_of_range", "turbidity": "ok", "temperature": "ok"}
    status_flags = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)


class Event(Base):
    __tablename__ = "events"

    event_id = Column(String, primary_key=True, default=_uuid)
    node_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    status = Column(Enum(EventStatus), default=EventStatus.DETECTED, nullable=False)
    severity = Column(Enum(Severity), nullable=True)

    # Which parameters triggered the anomaly and by how much, e.g.
    # {"turbidity": {"value": 7.8, "baseline_mean": 1.2, "z_score": 5.1}, ...}
    parameters_affected = Column(JSON, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    baseline_comparison = Column(JSON, nullable=True)

    # Filled in later by the investigation agent (via n8n PATCH callback)
    investigation_status = Column(String, default="PENDING")  # PENDING | IN_PROGRESS | DONE | FAILED
    investigation_result = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
