import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import random
from datetime import datetime, timezone, timedelta
from backend.app.database import SessionLocal, init_db
from backend.app.models import TelemetryRecord, AnomalyRecord, SensorHealthRecord, EventRecord
from backend.app.schemas import TelemetryIngestRequest
from backend.app.services.telemetry_service import TelemetryService


def seed_database(count: int = 100, device_id: str = "AQUA-01"):
    """
    Populate the SQLite database with normal historical telemetry to train the rolling baseline.
    """
    init_db()
    db = SessionLocal()
    
    print(f"[SEED] Seeding database with {count} normal historical water telemetry records for {device_id}...")
    
    # Clean previous records for a fresh clean demo baseline
    db.query(EventRecord).filter(EventRecord.device_id == device_id).delete()
    db.query(SensorHealthRecord).filter(SensorHealthRecord.device_id == device_id).delete()
    db.query(AnomalyRecord).filter(AnomalyRecord.device_id == device_id).delete()
    db.query(TelemetryRecord).filter(TelemetryRecord.device_id == device_id).delete()
    db.commit()

    now = datetime.now(timezone.utc)
    interval_seconds = 60  # 1 reading per minute

    for i in range(count, 0, -1):
        timestamp = now - timedelta(seconds=i * interval_seconds)
        
        # Realistic small normal gaussian fluctuations
        ph = round(7.20 + random.gauss(0, 0.08), 2)
        turbidity = round(max(0.5, 1.40 + random.gauss(0, 0.25)), 2)
        ec = round(max(200.0, 310.0 + random.gauss(0, 12.0)), 1)
        temperature = round(26.8 + random.gauss(0, 0.6), 1)

        payload = TelemetryIngestRequest(
            device_id=device_id,
            timestamp=timestamp,
            ph=ph,
            turbidity=turbidity,
            ec=ec,
            temperature=temperature,
        )
        TelemetryService.ingest_reading(db, payload)

    db.close()
    print(f"[OK] Successfully seeded {count} records. Normal baseline established.")


if __name__ == "__main__":
    seed_database(count=100)
