from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.schemas import (
    EventResponse,
    AnomalyResultResponse,
    SensorHealthResponse,
)
from backend.app.services.event_service import EventService
from backend.app.services.anomaly_service import AnomalyService
from backend.app.services.sensor_health_service import SensorHealthService

router = APIRouter(prefix="/api", tags=["Events & Diagnostics"])


@router.get(
    "/events",
    response_model=List[EventResponse],
    summary="Get recent and active system events",
)
def get_events(
    device_id: str = "AQUA-01", limit: int = 20, db: Session = Depends(get_db)
):
    records = EventService.get_recent_events(db, device_id=device_id, limit=limit)
    return [EventResponse.model_validate(r) for r in records]


@router.get(
    "/anomalies/latest",
    response_model=AnomalyResultResponse,
    summary="Get latest anomaly evaluation result",
)
def get_latest_anomaly(device_id: str = "AQUA-01", db: Session = Depends(get_db)):
    rec = AnomalyService.get_latest_anomaly(db, device_id=device_id)
    return AnomalyResultResponse(
        is_anomaly=rec.is_anomaly,
        anomaly_score=rec.anomaly_score,
        reasons=rec.reasons,
        z_scores=rec.z_scores,
        timestamp=rec.timestamp,
        disclaimer=settings.SCIENTIFIC_DISCLAIMER,
    )


@router.get(
    "/health",
    response_model=SensorHealthResponse,
    summary="Get current sensor network health status and fault isolation check",
)
def get_sensor_health(device_id: str = "AQUA-01", db: Session = Depends(get_db)):
    rec = SensorHealthService.get_latest_health(db, device_id=device_id)
    return SensorHealthResponse(
        status=rec.status,
        suspect_sensor=rec.suspect_sensor,
        details=rec.details,
        metrics_status=rec.metrics_status,
        timestamp=rec.timestamp,
    )
