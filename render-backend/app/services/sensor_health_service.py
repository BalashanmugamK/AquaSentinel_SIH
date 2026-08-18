from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.models import TelemetryRecord, SensorHealthRecord


class SensorHealthService:
    @classmethod
    def evaluate_sensor_health(
        cls, db: Session, telemetry: TelemetryRecord, z_scores: Dict[str, float]
    ) -> Tuple[str, Optional[str], str, Dict[str, str]]:
        metrics_status: Dict[str, str] = {}
        deviating_sensors = []

        if telemetry.ph < settings.PH_MIN_NORMAL or telemetry.ph > settings.PH_MAX_NORMAL or abs(z_scores.get("ph", 0)) >= settings.Z_SCORE_THRESHOLD:
            metrics_status["ph"] = "DEVIATING"
            deviating_sensors.append(("pH", telemetry.ph, z_scores.get("ph", 0)))
        else:
            metrics_status["ph"] = "NORMAL"

        if telemetry.turbidity > settings.TURBIDITY_THRESHOLD_NTU or abs(z_scores.get("turbidity", 0)) >= settings.Z_SCORE_THRESHOLD:
            metrics_status["turbidity"] = "DEVIATING"
            deviating_sensors.append(("Turbidity", telemetry.turbidity, z_scores.get("turbidity", 0)))
        else:
            metrics_status["turbidity"] = "NORMAL"

        if telemetry.ec > settings.EC_THRESHOLD_US_CM or abs(z_scores.get("ec", 0)) >= settings.Z_SCORE_THRESHOLD:
            metrics_status["ec"] = "DEVIATING"
            deviating_sensors.append(("EC", telemetry.ec, z_scores.get("ec", 0)))
        else:
            metrics_status["ec"] = "NORMAL"

        if telemetry.temperature < 5.0 or telemetry.temperature > 50.0 or abs(z_scores.get("temperature", 0)) >= settings.Z_SCORE_THRESHOLD:
            metrics_status["temperature"] = "DEVIATING"
            deviating_sensors.append(("Temperature", telemetry.temperature, z_scores.get("temperature", 0)))
        else:
            metrics_status["temperature"] = "NORMAL"

        if len(deviating_sensors) == 1:
            sensor_name, val, z = deviating_sensors[0]
            status = "FAULT_SUSPECTED"
            suspect_sensor = sensor_name
            details = (
                f"Isolated single-parameter anomaly on {sensor_name} (val: {val}, z: {z:+.2f}) "
                f"while all other 3 water parameters remain stable within normal baseline. "
                f"This pattern is characteristic of sensor probe failure, drift, or electrical fault, "
                f"not an environmental water-quality event."
            )
        elif len(deviating_sensors) > 1:
            status = "HEALTHY"
            suspect_sensor = None
            sensor_names = ", ".join([s[0] for s in deviating_sensors])
            details = (
                f"Sensors operating normally. Multiple co-varying parameters ({sensor_names}) "
                f"indicate an actual physical/chemical disturbance in the monitored water body."
            )
        else:
            status = "HEALTHY"
            suspect_sensor = None
            details = "All 4 sensor channels (pH, Turbidity, EC, Temperature) operating within nominal baseline."

        health_rec = SensorHealthRecord(
            device_id=telemetry.device_id,
            timestamp=telemetry.timestamp,
            status=status,
            suspect_sensor=suspect_sensor,
            details=details,
            created_at=datetime.now(timezone.utc),
        )
        health_rec.metrics_status = metrics_status

        db.add(health_rec)
        db.commit()
        db.refresh(health_rec)

        return status, suspect_sensor, details, metrics_status

    @classmethod
    def get_latest_health(cls, db: Session, device_id: str = "AQUA-01") -> SensorHealthRecord:
        rec = (
            db.query(SensorHealthRecord)
            .filter(SensorHealthRecord.device_id == device_id)
            .order_by(SensorHealthRecord.timestamp.desc())
            .first()
        )
        if not rec:
            rec = SensorHealthRecord(
                device_id=device_id,
                timestamp=datetime.now(timezone.utc),
                status="HEALTHY",
                suspect_sensor=None,
                details="Sensors nominal. Initial state.",
            )
            rec.metrics_status = {"ph": "NORMAL", "turbidity": "NORMAL", "ec": "NORMAL", "temperature": "NORMAL"}
        return rec
