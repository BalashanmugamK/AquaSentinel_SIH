import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas import (
    TelemetryIngestRequest,
    TelemetryRecordSchema,
    TelemetryHistoryResponse,
)
from backend.app.services.telemetry_service import TelemetryService

logger = logging.getLogger("aquasentinel.api.telemetry")
router = APIRouter(prefix="/api", tags=["Telemetry"])


@router.post(
    "/telemetry",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest raw telemetry from ESP32 / Wokwi simulator",
)
def ingest_telemetry(payload: TelemetryIngestRequest, db: Session = Depends(get_db)):
    try:
        telemetry_rec, anomaly_rec, health_rec, event_rec = TelemetryService.ingest_reading(
            db, payload
        )
        return {
            "status": "SUCCESS",
            "message": "Telemetry reading ingested successfully",
            "reading_id": telemetry_rec.id,
            "device_id": telemetry_rec.device_id,
            "is_anomaly": anomaly_rec.is_anomaly,
            "anomaly_score": anomaly_rec.anomaly_score,
            "sensor_health": health_rec.status,
            "event_active": bool(event_rec and event_rec.status == "ACTIVE"),
        }
    except Exception as e:
        logger.error(f"Error ingesting telemetry payload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to ingest telemetry reading: {str(e)}",
        )


@router.get(
    "/readings/latest",
    response_model=Optional[TelemetryRecordSchema],
    summary="Get the most recent telemetry reading",
)
def get_latest_reading(device_id: str = "AQUA-01", db: Session = Depends(get_db)):
    rec = TelemetryService.get_latest_reading(db, device_id=device_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry readings found for device {device_id}",
        )
    return rec


@router.get(
    "/readings/history",
    response_model=TelemetryHistoryResponse,
    summary="Get historical telemetry time-series for trend charts",
)
def get_reading_history(
    device_id: str = "AQUA-01", limit: int = 50, db: Session = Depends(get_db)
):
    records = TelemetryService.get_history(db, device_id=device_id, limit=limit)
    return TelemetryHistoryResponse(
        device_id=device_id,
        count=len(records),
        readings=[TelemetryRecordSchema.model_validate(r) for r in records],
    )
