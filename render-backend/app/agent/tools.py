from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.telemetry_service import TelemetryService
from app.services.anomaly_service import AnomalyService
from app.services.sensor_health_service import SensorHealthService
from app.services.event_service import EventService


def get_current_readings(db: Session, device_id: str = "AQUA-01") -> Dict[str, Any]:
    rec = TelemetryService.get_latest_reading(db, device_id=device_id)
    if not rec:
        return {
            "status": "NO_DATA",
            "message": "No telemetry readings have been recorded yet.",
            "device_id": device_id,
        }
    return {
        "status": "SUCCESS",
        "device_id": rec.device_id,
        "timestamp": rec.timestamp.isoformat() if rec.timestamp else None,
        "parameters": {
            "ph": rec.ph,
            "turbidity_ntu": rec.turbidity,
            "ec_us_cm": rec.ec,
            "temperature_c": rec.temperature,
        }
    }


def get_recent_history(db: Session, device_id: str = "AQUA-01", limit: int = 10) -> Dict[str, Any]:
    records = TelemetryService.get_history(db, device_id=device_id, limit=limit)
    return {
        "status": "SUCCESS",
        "device_id": device_id,
        "count": len(records),
        "history": [
            {
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "ph": r.ph,
                "turbidity": r.turbidity,
                "ec": r.ec,
                "temperature": r.temperature,
            }
            for r in records
        ]
    }


def get_baseline(db: Session, device_id: str = "AQUA-01", window_minutes: int = 60) -> Dict[str, Any]:
    baseline = AnomalyService.calculate_baseline(db, device_id=device_id, limit=50)
    return {
        "status": "SUCCESS",
        "device_id": device_id,
        "baseline_summary": baseline,
        "window_minutes": window_minutes,
    }


def get_anomaly_result(db: Session, device_id: str = "AQUA-01") -> Dict[str, Any]:
    rec = AnomalyService.get_latest_anomaly(db, device_id=device_id)
    return {
        "status": "SUCCESS",
        "device_id": rec.device_id,
        "timestamp": rec.timestamp.isoformat() if rec.timestamp else None,
        "is_anomaly": rec.is_anomaly,
        "anomaly_score": rec.anomaly_score,
        "reasons": rec.reasons,
        "z_scores": rec.z_scores,
    }


def get_active_events(db: Session, device_id: str = "AQUA-01") -> Dict[str, Any]:
    events = EventService.get_active_events(db, device_id=device_id)
    return {
        "status": "SUCCESS",
        "device_id": device_id,
        "active_event_count": len(events),
        "events": [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "severity": ev.severity,
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                "anomaly_score": ev.anomaly_score,
                "status": ev.status,
                "details": ev.details,
            }
            for ev in events
        ]
    }


def get_sensor_health(db: Session, device_id: str = "AQUA-01") -> Dict[str, Any]:
    rec = SensorHealthService.get_latest_health(db, device_id=device_id)
    return {
        "status": "SUCCESS",
        "device_id": rec.device_id,
        "timestamp": rec.timestamp.isoformat() if rec.timestamp else None,
        "health_status": rec.status,
        "suspect_sensor": rec.suspect_sensor,
        "details": rec.details,
        "metrics_status": rec.metrics_status,
    }
