from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .readings import require_api_key

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("", response_model=list[schemas.EventOut])
def list_events(node_id: str | None = None, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(models.Event)
    if node_id:
        q = q.filter(models.Event.node_id == node_id)
    return q.order_by(models.Event.timestamp.desc()).limit(limit).all()


@router.patch("/{event_id}", response_model=schemas.EventOut, dependencies=[Depends(require_api_key)])
def update_event(event_id: str, patch: schemas.EventUpdate, db: Session = Depends(get_db)):
    """
    Called by n8n after the investigation agent finishes (SRS Section 13:
    'Store Investigation Result'). This is the write-back step in
    Workstream D's flow: Anomaly Event -> n8n -> Agent -> back here.
    """
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    data = patch.model_dump(exclude_unset=True)
    status_value = data.pop("status", None)
    if status_value:
        try:
            event.status = models.EventStatus(status_value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status '{status_value}'")

    for field, value in data.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return event
