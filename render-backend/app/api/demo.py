from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    TelemetryIngestRequest,
    TelemetryRecordSchema,
    AnomalyResultResponse,
    EventResponse,
    SensorHealthResponse,
    DemoScenarioResponse,
)
from app.services.telemetry_service import TelemetryService
from app.config import settings

router = APIRouter(prefix="/api/demo", tags=["Demo Control Scenarios"])


@router.post(
    "/scenario/normal",
    response_model=DemoScenarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Scenario 1: Normal Water Quality Telemetry",
)
def trigger_scenario_normal(db: Session = Depends(get_db)):
    payload = TelemetryIngestRequest(
        device_id="AQUA-01",
        timestamp=datetime.now(timezone.utc),
        ph=7.2,
        turbidity=1.2,
        ec=310.0,
        temperature=27.0,
    )
    telemetry, anomaly, health, event = TelemetryService.ingest_reading(db, payload)

    return DemoScenarioResponse(
        scenario="NORMAL",
        status="SUCCESS",
        message="Injected normal baseline telemetry. System is 🟢 NORMAL.",
        telemetry_injected=TelemetryRecordSchema.model_validate(telemetry),
        anomaly_result=AnomalyResultResponse(
            is_anomaly=anomaly.is_anomaly,
            anomaly_score=anomaly.anomaly_score,
            reasons=anomaly.reasons,
            z_scores=anomaly.z_scores,
            timestamp=anomaly.timestamp,
            disclaimer=settings.SCIENTIFIC_DISCLAIMER,
        ),
        event_created=EventResponse.model_validate(event) if event else None,
        sensor_health=SensorHealthResponse(
            status=health.status,
            suspect_sensor=health.suspect_sensor,
            details=health.details,
            metrics_status=health.metrics_status,
            timestamp=health.timestamp,
        ),
    )


@router.post(
    "/scenario/disturbance",
    response_model=DemoScenarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Scenario 2: Multi-Parameter Water Disturbance Anomaly",
)
def trigger_scenario_disturbance(db: Session = Depends(get_db)):
    payload = TelemetryIngestRequest(
        device_id="AQUA-01",
        timestamp=datetime.now(timezone.utc),
        ph=7.3,
        turbidity=25.0,
        ec=920.0,
        temperature=27.5,
    )
    telemetry, anomaly, health, event = TelemetryService.ingest_reading(db, payload)

    return DemoScenarioResponse(
        scenario="DISTURBANCE",
        status="SUCCESS",
        message="Injected multi-parameter disturbance (Turbidity + EC spike). System is 🔴 ANOMALY.",
        telemetry_injected=TelemetryRecordSchema.model_validate(telemetry),
        anomaly_result=AnomalyResultResponse(
            is_anomaly=anomaly.is_anomaly,
            anomaly_score=anomaly.anomaly_score,
            reasons=anomaly.reasons,
            z_scores=anomaly.z_scores,
            timestamp=anomaly.timestamp,
            disclaimer=settings.SCIENTIFIC_DISCLAIMER,
        ),
        event_created=EventResponse.model_validate(event) if event else None,
        sensor_health=SensorHealthResponse(
            status=health.status,
            suspect_sensor=health.suspect_sensor,
            details=health.details,
            metrics_status=health.metrics_status,
            timestamp=health.timestamp,
        ),
    )


@router.post(
    "/scenario/sensor_fault",
    response_model=DemoScenarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Scenario 3: Single-Sensor Extreme Fault Isolation",
)
def trigger_scenario_sensor_fault(db: Session = Depends(get_db)):
    payload = TelemetryIngestRequest(
        device_id="AQUA-01",
        timestamp=datetime.now(timezone.utc),
        ph=2.0,
        turbidity=1.3,
        ec=315.0,
        temperature=26.8,
    )
    telemetry, anomaly, health, event = TelemetryService.ingest_reading(db, payload)

    return DemoScenarioResponse(
        scenario="SENSOR_FAULT",
        status="SUCCESS",
        message="Injected isolated pH probe fault. System is ⚠️ SENSOR_FAULT_SUSPECTED.",
        telemetry_injected=TelemetryRecordSchema.model_validate(telemetry),
        anomaly_result=AnomalyResultResponse(
            is_anomaly=anomaly.is_anomaly,
            anomaly_score=anomaly.anomaly_score,
            reasons=anomaly.reasons,
            z_scores=anomaly.z_scores,
            timestamp=anomaly.timestamp,
            disclaimer=settings.SCIENTIFIC_DISCLAIMER,
        ),
        event_created=EventResponse.model_validate(event) if event else None,
        sensor_health=SensorHealthResponse(
            status=health.status,
            suspect_sensor=health.suspect_sensor,
            details=health.details,
            metrics_status=health.metrics_status,
            timestamp=health.timestamp,
        ),
    )
