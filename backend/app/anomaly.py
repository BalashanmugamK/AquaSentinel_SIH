"""
Anomaly detection - Prototype SRS Section 8.

This is intentionally a lightweight rolling-baseline + z-score detector,
not a trained ML model. It is the Workstream C interface (owner: Ananya);
Workstream B (backend) calls it synchronously on ingest so a new reading
can immediately produce an anomaly event.

Swap-in point: if Workstream C wants to plug in Isolation Forest or another
model later, only `score_reading()` needs to change - its inputs/outputs
(a dict of per-parameter z-scores + an overall score) stay the same, so
nothing else in the backend has to be touched.
"""
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .config import get_settings
from .models import Reading, Severity

settings = get_settings()

PARAMS = ("ph", "tds", "turbidity", "temperature")

PLAUSIBLE_RANGES = {
    "ph": (settings.PH_MIN, settings.PH_MAX),
    "tds": (settings.TDS_MIN, settings.TDS_MAX),
    "turbidity": (settings.TURBIDITY_MIN, settings.TURBIDITY_MAX),
    "temperature": (settings.TEMP_MIN, settings.TEMP_MAX),
}


@dataclass
class AnomalyResult:
    is_anomalous: bool
    anomaly_score: float
    severity: Optional[Severity]
    parameters_affected: Dict[str, Dict[str, float]] = field(default_factory=dict)
    baseline_comparison: Dict[str, Dict[str, float]] = field(default_factory=dict)


def check_plausibility(reading: Reading) -> Dict[str, str]:
    """Basic sensor-sanity check (SRS Section 11 / FR-EDGE-04)."""
    flags = {}
    for param in PARAMS:
        value = getattr(reading, param)
        lo, hi = PLAUSIBLE_RANGES[param]
        flags[param] = "ok" if lo <= value <= hi else "out_of_range"
    return flags


def build_baseline(history: List[Reading]) -> Dict[str, Dict[str, float]]:
    """Rolling mean/std per parameter from recent historical readings."""
    baseline: Dict[str, Dict[str, float]] = {}
    for param in PARAMS:
        values = [getattr(r, param) for r in history]
        if len(values) >= 2:
            mean = statistics.mean(values)
            std = statistics.pstdev(values)
        elif values:
            mean, std = values[0], 0.0
        else:
            mean, std = 0.0, 0.0
        # Floor std with a parameter-scale-aware epsilon (applied AFTER
        # rounding is avoided here) so perfectly flat historical data
        # doesn't cause a division-by-zero z-score later, while still
        # letting a genuinely tiny real deviation register as anomalous.
        std = max(std, 0.01)
        baseline[param] = {"mean": round(mean, 4), "std": round(std, 4)}
    return baseline


def score_reading(reading: Reading, history: List[Reading]) -> AnomalyResult:
    """
    Compare `reading` against a baseline built from `history`
    (most recent settings.BASELINE_WINDOW readings, excluding `reading` itself).

    Returns z-scores per parameter and an overall anomaly decision.
    """
    if len(history) < settings.MIN_READINGS_FOR_BASELINE:
        # Not enough data yet to say anything is abnormal - stay quiet
        # rather than false-alarming on the first few readings.
        return AnomalyResult(is_anomalous=False, anomaly_score=0.0, severity=None)

    baseline = build_baseline(history)
    affected: Dict[str, Dict[str, float]] = {}
    z_scores: List[float] = []

    for param in PARAMS:
        value = getattr(reading, param)
        mean = baseline[param]["mean"]
        std = baseline[param]["std"]
        z = (value - mean) / std
        z_scores.append(abs(z))

        if abs(z) >= settings.ZSCORE_THRESHOLD:
            affected[param] = {
                "value": value,
                "baseline_mean": mean,
                "baseline_std": std,
                "z_score": round(z, 3),
            }

    overall_score = max(z_scores) if z_scores else 0.0
    is_anomalous = len(affected) > 0

    severity = None
    if is_anomalous:
        if overall_score >= settings.ZSCORE_THRESHOLD * 2:
            severity = Severity.HIGH
        elif overall_score >= settings.ZSCORE_THRESHOLD * 1.3:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

    return AnomalyResult(
        is_anomalous=is_anomalous,
        anomaly_score=round(overall_score, 3),
        severity=severity,
        parameters_affected=affected,
        baseline_comparison=baseline,
    )
