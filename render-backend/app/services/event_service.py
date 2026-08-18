from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models import EventRecord


class EventService:
    @classmethod
    def process_telemetry_event(
        cls,
        db: Session,
        device_id: str,
        is_anomaly: bool,
        anomaly_score: float,
        is_sensor_fault: bool,
        reasons: List[str],
        timestamp: Optional[datetime] = None,
    ) -> Optional[EventRecord]:
        now = timestamp or datetime.now(timezone.utc)
        cooldown_threshold = now - timedelta(seconds=settings.EVENT_COOLDOWN_SECONDS)

        if is_sensor_fault:
            target_event_type = "SENSOR_FAULT_SUSPECTED"
            severity = "MEDIUM" if anomaly_score < 0.8 else "HIGH"
        elif is_anomaly:
            target_event_type = "WATER_QUALITY_ANOMALY"
            severity = "HIGH" if anomaly_score >= 0.75 else "MEDIUM"
        else:
            active_events = (
                db.query(EventRecord)
                .filter(
                    EventRecord.device_id == device_id,
                    EventRecord.status == "ACTIVE",
                )
                .all()
            )
            for ev in active_events:
                ev.status = "RESOLVED"
                ev.resolved_at = now
            if active_events:
                db.commit()
            return None

        recent_event = (
            db.query(EventRecord)
            .filter(
                EventRecord.device_id == device_id,
                EventRecord.event_type == target_event_type,
                EventRecord.status == "ACTIVE",
                EventRecord.timestamp >= cooldown_threshold,
            )
            .order_by(EventRecord.timestamp.desc())
            .first()
        )

        if recent_event:
            recent_event.timestamp = now
            if anomaly_score > recent_event.anomaly_score:
                recent_event.anomaly_score = anomaly_score
                recent_event.severity = severity
            if reasons:
                recent_event.details = " | ".join(reasons)
            db.commit()
            db.refresh(recent_event)
            return recent_event

        new_event = EventRecord(
            event_type=target_event_type,
            severity=severity,
            device_id=device_id,
            timestamp=now,
            anomaly_score=anomaly_score,
            status="ACTIVE",
            details=" | ".join(reasons) if reasons else f"{target_event_type} detected.",
            created_at=datetime.now(timezone.utc),
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return new_event

    @classmethod
    def get_active_events(cls, db: Session, device_id: str = "AQUA-01") -> List[EventRecord]:
        return (
            db.query(EventRecord)
            .filter(
                EventRecord.device_id == device_id,
                EventRecord.status == "ACTIVE"
            )
            .order_by(EventRecord.timestamp.desc())
            .all()
        )

    @classmethod
    def get_recent_events(cls, db: Session, device_id: str = "AQUA-01", limit: int = 20) -> List[EventRecord]:
        return (
            db.query(EventRecord)
            .filter(EventRecord.device_id == device_id)
            .order_by(EventRecord.timestamp.desc())
            .limit(limit)
            .all()
        )
