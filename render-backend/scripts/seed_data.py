import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure render-backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import random
from datetime import datetime, timezone, timedelta
from app.database import SessionLocal, init_db
from app.models import TelemetryRecord, AnomalyRecord, SensorHealthRecord, EventRecord
from app.schemas import TelemetryIngestRequest
from app.services.telemetry_service import TelemetryService


def seed_database(count: int = 50, device_id: str = "AQUA-01"):
    init_db()
    db = SessionLocal()
    
    # Check if records already exist
    existing = db.query(TelemetryRecord).filter(TelemetryRecord.device_id == device_id).count()
    if existing >= 20:
        print(f"✓ Database already contains {existing} records. Baseline is established.")
        db.close()
        return

    print(f"[SEED] Initializing database with {count} baseline telemetry records for {device_id}...")

    now = datetime.now(timezone.utc)
    interval_seconds = 60

    for i in range(count, 0, -1):
        timestamp = now - timedelta(seconds=i * interval_seconds)
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
    print(f"[OK] Seeded {count} baseline records successfully.")


if __name__ == "__main__":
    seed_database(count=50)
