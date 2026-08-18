from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), index=True, nullable=False, default="AQUA-01")
    timestamp = Column(DateTime, index=True, nullable=False, default=utc_now)
    ph = Column(Float, nullable=False)
    turbidity = Column(Float, nullable=False)
    ec = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    raw_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), index=True, nullable=False, default="AQUA-01")
    timestamp = Column(DateTime, index=True, nullable=False, default=utc_now)
    is_anomaly = Column(Boolean, nullable=False, default=False)
    anomaly_score = Column(Float, nullable=False, default=0.0)
    reasons_json = Column(Text, nullable=False, default="[]")
    z_scores_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=utc_now)

    @property
    def reasons(self):
        try:
            return json.loads(self.reasons_json)
        except Exception:
            return []

    @reasons.setter
    def reasons(self, val):
        self.reasons_json = json.dumps(val)

    @property
    def z_scores(self):
        try:
            return json.loads(self.z_scores_json)
        except Exception:
            return {}

    @z_scores.setter
    def z_scores(self, val):
        self.z_scores_json = json.dumps(val)


class EventRecord(Base):
    __tablename__ = "event_records"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(64), nullable=False)
    severity = Column(String(32), nullable=False, default="MEDIUM")
    device_id = Column(String(64), index=True, nullable=False, default="AQUA-01")
    timestamp = Column(DateTime, index=True, nullable=False, default=utc_now)
    anomaly_score = Column(Float, nullable=False, default=0.0)
    status = Column(String(32), nullable=False, default="ACTIVE")
    details = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class SensorHealthRecord(Base):
    __tablename__ = "sensor_health_records"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), index=True, nullable=False, default="AQUA-01")
    timestamp = Column(DateTime, index=True, nullable=False, default=utc_now)
    status = Column(String(32), nullable=False, default="HEALTHY")
    suspect_sensor = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)
    metrics_status_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=utc_now)

    @property
    def metrics_status(self):
        try:
            return json.loads(self.metrics_status_json)
        except Exception:
            return {}

    @metrics_status.setter
    def metrics_status(self, val):
        self.metrics_status_json = json.dumps(val)
