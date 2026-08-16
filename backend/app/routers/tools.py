"""
Agent tools - Prototype SRS Section 14.

These four endpoints are the backend-backed tools the investigation agent
(Workstream D) calls: get_current_readings, get_historical_readings,
get_anomaly_event, get_sensor_status. They live in the backend (not the
agent service) because they're just reads over the same data the dashboard
uses - keeping one source of truth.

The agent's tool-calling loop (see agent/investigation_agent.py) maps each
Sarvam tool-call 1:1 onto one of these routes.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import anomaly, models, schemas
from ..config import get_settings
from ..database import get_db

router = APIRouter(prefix="/api/tools", tags=["agent-tools"])
settings = get_settings()


@router.get("/current_readings", response_model=schemas.CurrentReadingsTool)
def get_current_readings(node_id: str = Query(default="node-01"), db: Session = Depends(get_db)):
    reading = (
        db.query(models.Reading)
        .filter(models.Reading.node_id == node_id)
        .order_by(models.Reading.timestamp.desc())
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail=f"No readings for node '{node_id}'")
    return schemas.CurrentReadingsTool(
        node_id=reading.node_id,
        timestamp=reading.timestamp,
        ph=reading.ph,
        tds=reading.tds,
        turbidity=reading.turbidity,
        temperature=reading.temperature,
    )


@router.get("/historical_readings", response_model=schemas.HistoricalReadingsTool)
def get_historical_readings(
    node_id: str = Query(default="node-01"),
    limit: int = Query(default=30, le=200),
    db: Session = Depends(get_db),
):
    history = (
        db.query(models.Reading)
        .filter(models.Reading.node_id == node_id)
        .order_by(models.Reading.timestamp.desc())
        .limit(max(limit, settings.BASELINE_WINDOW))
        .all()
    )
    if not history:
        raise HTTPException(status_code=404, detail=f"No readings for node '{node_id}'")

    baseline_full = anomaly.build_baseline(history)
    baseline_flat = {f"{p}_mean": v["mean"] for p, v in baseline_full.items()}
    baseline_flat.update({f"{p}_std": v["std"] for p, v in baseline_full.items()})

    return schemas.HistoricalReadingsTool(
        node_id=node_id,
        baseline=baseline_flat,
        recent_readings=history[:limit],
    )


@router.get("/anomaly_event/{event_id}", response_model=schemas.EventOut)
def get_anomaly_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/sensor_status", response_model=schemas.SensorStatusTool)
def get_sensor_status(node_id: str = Query(default="node-01"), db: Session = Depends(get_db)):
    """Basic sensor-sanity summary (SRS Section 11) - not predictive
    maintenance, just: is the latest reading plausible and recent?"""
    reading = (
        db.query(models.Reading)
        .filter(models.Reading.node_id == node_id)
        .order_by(models.Reading.timestamp.desc())
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail=f"No readings for node '{node_id}'")

    issues = []
    flags = reading.status_flags or {}
    for param, flag in flags.items():
        if flag != "ok":
            issues.append(f"{param}_out_of_plausible_range")

    ts = reading.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - ts).total_seconds()
    if age_seconds > 300:  # stale if no reading in the last 5 minutes
        issues.append("stale_data")

    return schemas.SensorStatusTool(
        node_id=node_id,
        ok=len(issues) == 0,
        issues=issues,
        last_reading_age_seconds=round(age_seconds, 1),
    )
