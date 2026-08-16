from datetime import datetime, timezone
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from .. import anomaly, models, schemas
from ..config import get_settings
from ..database import get_db

router = APIRouter(prefix="/api/readings", tags=["readings"])
settings = get_settings()


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    """Prototype-level auth (SRS Section 26) - not full RBAC, just keeps the
    ingest endpoint from being wide open on a public demo network."""
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


@router.post("", response_model=schemas.IngestResponse, dependencies=[Depends(require_api_key)])
def ingest_reading(payload: schemas.ReadingIn, db: Session = Depends(get_db)):
    """
    ESP32 -> here (FR-EDGE-05). Stores the reading, runs the plausibility
    check, then runs anomaly detection against recent history. If an
    anomaly is found, creates an Event and (if configured) fires the n8n
    webhook so the investigation agent picks it up automatically.
    """
    reading = models.Reading(
        node_id=payload.node_id,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
        ph=payload.ph,
        tds=payload.tds,
        turbidity=payload.turbidity,
        temperature=payload.temperature,
    )
    reading.status_flags = anomaly.check_plausibility(reading)

    db.add(reading)
    db.commit()
    db.refresh(reading)

    history = (
        db.query(models.Reading)
        .filter(models.Reading.node_id == payload.node_id, models.Reading.id != reading.id)
        .order_by(models.Reading.timestamp.desc())
        .limit(settings.BASELINE_WINDOW)
        .all()
    )

    result = anomaly.score_reading(reading, history)

    event_out = None
    if result.is_anomalous:
        event = models.Event(
            node_id=payload.node_id,
            timestamp=reading.timestamp,
            status=models.EventStatus.DETECTED,
            severity=result.severity,
            parameters_affected=result.parameters_affected,
            anomaly_score=result.anomaly_score,
            baseline_comparison=result.baseline_comparison,
            investigation_status="PENDING",
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        event_out = event
        _notify_n8n(event.event_id)

    return schemas.IngestResponse(
        reading=schemas.ReadingOut.model_validate(reading),
        anomaly_event=schemas.EventOut.model_validate(event_out) if event_out else None,
    )


def _notify_n8n(event_id: str) -> None:
    """Fire-and-forget POST to the n8n webhook (SRS Section 13).
    Failure here must never break sensor ingestion (SRS Section 27:
    reliability - the raw pipeline keeps working even if AI/orchestration
    is unavailable)."""
    if not settings.N8N_WEBHOOK_URL:
        return
    try:
        httpx.post(settings.N8N_WEBHOOK_URL, json={"event_id": event_id}, timeout=3.0)
    except httpx.HTTPError:
        # Prototype-level: log and move on. The event still exists in the DB
        # and can be picked up by re-running the workflow or a manual retry.
        print(f"[warn] failed to notify n8n for event {event_id}")


@router.get("/current", response_model=schemas.ReadingOut)
def get_current_reading(node_id: str = Query(default="node-01"), db: Session = Depends(get_db)):
    reading = (
        db.query(models.Reading)
        .filter(models.Reading.node_id == node_id)
        .order_by(models.Reading.timestamp.desc())
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail=f"No readings yet for node '{node_id}'")
    return reading


@router.get("/history", response_model=List[schemas.ReadingOut])
def get_history(
    node_id: str = Query(default="node-01"),
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Reading)
        .filter(models.Reading.node_id == node_id)
        .order_by(models.Reading.timestamp.desc())
        .limit(limit)
        .all()
    )


@router.get("/baseline")
def get_baseline(node_id: str = Query(default="node-01"), db: Session = Depends(get_db)):
    history = (
        db.query(models.Reading)
        .filter(models.Reading.node_id == node_id)
        .order_by(models.Reading.timestamp.desc())
        .limit(settings.BASELINE_WINDOW)
        .all()
    )
    if not history:
        raise HTTPException(status_code=404, detail=f"No readings yet for node '{node_id}'")
    return {"node_id": node_id, "sample_size": len(history), "baseline": anomaly.build_baseline(history)}
