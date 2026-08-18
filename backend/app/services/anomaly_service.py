from datetime import datetime, timezone
import math
from typing import Dict, Any, List, Tuple
import numpy as np
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models import TelemetryRecord, AnomalyRecord


class AnomalyService:
    # Default reference baseline if database has minimal historical records
    DEFAULT_BASELINE = {
        "ph": {"mean": 7.2, "std": 0.25, "min": 6.8, "max": 7.6},
        "turbidity": {"mean": 1.5, "std": 0.5, "min": 0.5, "max": 3.0},
        "ec": {"mean": 320.0, "std": 30.0, "min": 250.0, "max": 400.0},
        "temperature": {"mean": 26.5, "std": 1.2, "min": 24.0, "max": 29.0},
    }

    @classmethod
    def calculate_baseline(cls, db: Session, device_id: str = "AQUA-01", limit: int = 50) -> Dict[str, Dict[str, float]]:
        """Calculate statistical baseline from recent normal telemetry records."""
        records = (
            db.query(TelemetryRecord)
            .filter(TelemetryRecord.device_id == device_id)
            .order_by(TelemetryRecord.timestamp.desc())
            .limit(limit)
            .all()
        )

        if len(records) < 5:
            return cls.DEFAULT_BASELINE

        ph_vals = [r.ph for r in records]
        turb_vals = [r.turbidity for r in records]
        ec_vals = [r.ec for r in records]
        temp_vals = [r.temperature for r in records]

        def get_stats(vals: List[float], default_std: float = 0.1) -> Dict[str, float]:
            mean_val = float(np.mean(vals))
            std_val = float(np.std(vals))
            if std_val < 0.001:  # avoid divide-by-zero on completely flat signals
                std_val = default_std
            return {
                "mean": round(mean_val, 2),
                "std": round(std_val, 2),
                "min": round(float(np.min(vals)), 2),
                "max": round(float(np.max(vals)), 2),
            }

        return {
            "ph": get_stats(ph_vals, default_std=0.2),
            "turbidity": get_stats(turb_vals, default_std=0.4),
            "ec": get_stats(ec_vals, default_std=20.0),
            "temperature": get_stats(temp_vals, default_std=1.0),
        }

    @classmethod
    def evaluate(
        cls, db: Session, telemetry: TelemetryRecord
    ) -> Tuple[bool, float, List[str], Dict[str, float]]:
        """
        Evaluate single telemetry point against baseline and engineering thresholds.
        Returns: (is_anomaly, anomaly_score, reasons, z_scores)
        """
        baseline = cls.calculate_baseline(db, telemetry.device_id, limit=settings.BASELINE_WINDOW_SIZE)

        z_scores: Dict[str, float] = {}
        reasons: List[str] = []
        abnormal_count = 0
        total_deviation_score = 0.0

        metrics_map = {
            "ph": (telemetry.ph, "pH"),
            "turbidity": (telemetry.turbidity, "Turbidity"),
            "ec": (telemetry.ec, "Electrical Conductivity (EC)"),
            "temperature": (telemetry.temperature, "Temperature"),
        }

        for key, (val, label) in metrics_map.items():
            base = baseline.get(key, cls.DEFAULT_BASELINE[key])
            mean = base["mean"]
            std = base["std"]
            z = (val - mean) / std if std > 0 else 0.0
            z_scores[key] = round(z, 2)

            is_metric_anomaly = False
            reason_detail = ""

            # Check Z-Score deviation
            if abs(z) >= settings.Z_SCORE_THRESHOLD:
                is_metric_anomaly = True
                direction = "above" if z > 0 else "below"
                reason_detail = (
                    f"{label} ({val}) is significantly {direction} baseline "
                    f"(learned mean: {mean}, z-score: {z:+.2f})"
                )

            # Check absolute scientific bounds
            if key == "turbidity" and val > settings.TURBIDITY_THRESHOLD_NTU:
                is_metric_anomaly = True
                if not reason_detail:
                    reason_detail = f"{label} ({val} NTU) breached environmental threshold (> {settings.TURBIDITY_THRESHOLD_NTU} NTU)"
            elif key == "ec" and val > settings.EC_THRESHOLD_US_CM:
                is_metric_anomaly = True
                if not reason_detail:
                    reason_detail = f"{label} ({val} µS/cm) breached safe conductivity limit (> {settings.EC_THRESHOLD_US_CM} µS/cm)"
            elif key == "ph" and (val < settings.PH_MIN_NORMAL or val > settings.PH_MAX_NORMAL):
                is_metric_anomaly = True
                if not reason_detail:
                    reason_detail = f"{label} ({val}) is outside normal range [{settings.PH_MIN_NORMAL} - {settings.PH_MAX_NORMAL}]"

            if is_metric_anomaly:
                abnormal_count += 1
                if reason_detail and reason_detail not in reasons:
                    reasons.append(reason_detail)
                # Sigmoid scaling for deviation contribution
                total_deviation_score += 1.0 / (1.0 + math.exp(-0.8 * (abs(z) - 2.0)))

        # Composite anomaly score [0.0 - 1.0]
        if abnormal_count == 0:
            anomaly_score = 0.05
            is_anomaly = False
        else:
            # Scale score between 0.50 and 0.98 depending on severity and multi-variable concurrence
            base_score = 0.5 + min(0.48, total_deviation_score * 0.25)
            anomaly_score = round(min(1.0, base_score), 2)
            is_anomaly = anomaly_score >= 0.60

        # Persist Anomaly Record
        anomaly_rec = AnomalyRecord(
            device_id=telemetry.device_id,
            timestamp=telemetry.timestamp,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            created_at=datetime.now(timezone.utc),
        )
        anomaly_rec.reasons = reasons
        anomaly_rec.z_scores = z_scores

        db.add(anomaly_rec)
        db.commit()
        db.refresh(anomaly_rec)

        return is_anomaly, anomaly_score, reasons, z_scores

    @classmethod
    def get_latest_anomaly(cls, db: Session, device_id: str = "AQUA-01") -> AnomalyRecord:
        """Fetch the most recent anomaly evaluation record."""
        rec = (
            db.query(AnomalyRecord)
            .filter(AnomalyRecord.device_id == device_id)
            .order_by(AnomalyRecord.timestamp.desc())
            .first()
        )
        if not rec:
            rec = AnomalyRecord(
                device_id=device_id,
                timestamp=datetime.now(timezone.utc),
                is_anomaly=False,
                anomaly_score=0.0,
            )
            rec.reasons = []
            rec.z_scores = {}
        return rec
