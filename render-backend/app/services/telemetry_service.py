from datetime import datetime, timezone
import json
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from app.config import settings
from app.models import TelemetryRecord, AnomalyRecord, SensorHealthRecord, EventRecord
from app.schemas import TelemetryIngestRequest
from app.services.anomaly_service import AnomalyService
from app.services.sensor_health_service import SensorHealthService
from app.services.event_service import EventService


class TelemetryService:
    @classmethod
    def ingest_reading(
        cls, db: Session, payload: TelemetryIngestRequest
    ) -> Tuple[TelemetryRecord, AnomalyRecord, SensorHealthRecord, Optional[EventRecord]]:
        ts = payload.timestamp or datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        telemetry_rec = TelemetryRecord(
            device_id=payload.device_id,
            timestamp=ts,
            ph=round(payload.ph, 2),
            turbidity=round(payload.turbidity, 2),
            ec=round(payload.ec, 2),
            temperature=round(payload.temperature, 2),
            raw_payload=payload.model_dump_json(),
            created_at=datetime.now(timezone.utc),
        )
        db.add(telemetry_rec)
        db.commit()
        db.refresh(telemetry_rec)

        is_anomaly, anomaly_score, reasons, z_scores = AnomalyService.evaluate(db, telemetry_rec)
        anomaly_rec = AnomalyService.get_latest_anomaly(db, payload.device_id)

        health_status, suspect_sensor, health_details, metrics_status = SensorHealthService.evaluate_sensor_health(
            db, telemetry_rec, z_scores
        )
        health_rec = SensorHealthService.get_latest_health(db, payload.device_id)

        is_sensor_fault = (health_status == "FAULT_SUSPECTED")
        event_reasons = reasons if reasons else ([health_details] if is_sensor_fault else [])
        event_rec = EventService.process_telemetry_event(
            db=db,
            device_id=payload.device_id,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            is_sensor_fault=is_sensor_fault,
            reasons=event_reasons,
            timestamp=ts,
        )

        return telemetry_rec, anomaly_rec, health_rec, event_rec

    @classmethod
    def get_latest_reading(cls, db: Session, device_id: str = "AQUA-01") -> Optional[TelemetryRecord]:
        return (
            db.query(TelemetryRecord)
            .filter(TelemetryRecord.device_id == device_id)
            .order_by(TelemetryRecord.timestamp.desc())
            .first()
        )

    @classmethod
    def get_history(cls, db: Session, device_id: str = "AQUA-01", limit: int = 50) -> List[TelemetryRecord]:
        records = (
            db.query(TelemetryRecord)
            .filter(TelemetryRecord.device_id == device_id)
            .order_by(TelemetryRecord.timestamp.desc())
            .limit(limit)
            .all()
        )
        records.reverse()
        return records
