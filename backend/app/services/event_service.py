from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models import EventRecord


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
        """
        Create or update events based on anomaly and sensor health analysis with cooldown dedup.
        """
        now = timestamp or datetime.now(timezone.utc)
        cooldown_threshold = now - timedelta(seconds=settings.EVENT_COOLDOWN_SECONDS)

        # Determine target event type
        if is_sensor_fault:
            target_event_type = "SENSOR_FAULT_SUSPECTED"
            severity = "MEDIUM" if anomaly_score < 0.8 else "HIGH"
        elif is_anomaly:
            target_event_type = "WATER_QUALITY_ANOMALY"
            severity = "HIGH" if anomaly_score >= 0.75 else "MEDIUM"
        else:
            # Water is normal. Auto-resolve active events older than cooldown
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

        # Check for existing ACTIVE event within cooldown
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
            # Update score if higher, refresh timestamp
            recent_event.timestamp = now
            if anomaly_score > recent_event.anomaly_score:
                recent_event.anomaly_score = anomaly_score
                recent_event.severity = severity
            if reasons:
                recent_event.details = " | ".join(reasons)
            db.commit()
            db.refresh(recent_event)
            return recent_event

        # Otherwise, create new event
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
        """Fetch all currently ACTIVE events."""
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
        """Fetch recent events including historical resolved ones."""
        return (
            db.query(EventRecord)
            .filter(EventRecord.device_id == device_id)
            .order_by(EventRecord.timestamp.desc())
            .limit(limit)
            .all()
        )
