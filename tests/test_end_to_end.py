import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal, init_db
from backend.app.config import settings
from scripts.seed_data import seed_database

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    seed_database(count=30, device_id="AQUA-01")
    yield


def test_01_health_endpoint():
    """Verify system health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "AquaSentinel" in data["app"]
    assert settings.SCIENTIFIC_DISCLAIMER in data["disclaimer"]


def test_02_telemetry_ingestion_and_query():
    """Verify HTTP POST telemetry ingestion and retrieval."""
    payload = {
        "device_id": "AQUA-01",
        "ph": 7.25,
        "turbidity": 1.35,
        "ec": 315.0,
        "temperature": 27.1,
    }
    # 1. Post telemetry
    post_res = client.post("/api/telemetry", json=payload)
    assert post_res.status_code == 201
    post_data = post_res.json()
    assert post_data["status"] == "SUCCESS"
    assert post_data["is_anomaly"] is False
    assert post_data["sensor_health"] == "HEALTHY"

    # 2. Get latest reading
    latest_res = client.get("/api/readings/latest?device_id=AQUA-01")
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    assert latest_data["ph"] == 7.25
    assert latest_data["turbidity"] == 1.35
    assert latest_data["ec"] == 315.0
    assert latest_data["temperature"] == 27.1

    # 3. Get history
    hist_res = client.get("/api/readings/history?device_id=AQUA-01&limit=10")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["count"] >= 10
    assert len(hist_data["readings"]) >= 10


def test_03_disturbance_anomaly_detection_and_events():
    """Verify multi-parameter disturbance triggers WATER_QUALITY_ANOMALY."""
    payload = {
        "device_id": "AQUA-01",
        "ph": 7.3,
        "turbidity": 28.0,   # Spike
        "ec": 950.0,         # Spike
        "temperature": 27.4,
    }
    # 1. Ingest disturbance
    res = client.post("/api/telemetry", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["is_anomaly"] is True
    assert data["anomaly_score"] >= 0.70
    assert data["sensor_health"] == "HEALTHY"
    assert data["event_active"] is True

    # 2. Verify active event in event API
    events_res = client.get("/api/events?device_id=AQUA-01")
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) > 0
    active_event = events[0]
    assert active_event["event_type"] == "WATER_QUALITY_ANOMALY"
    assert active_event["status"] == "ACTIVE"
    assert active_event["severity"] in ["HIGH", "MEDIUM"]

    # 3. Verify latest anomaly
    anomaly_res = client.get("/api/anomalies/latest?device_id=AQUA-01")
    assert anomaly_res.status_code == 200
    anomaly_data = anomaly_res.json()
    assert anomaly_data["is_anomaly"] is True
    assert len(anomaly_data["reasons"]) >= 2


def test_04_sensor_fault_isolation():
    """Verify single-sensor outlier triggers SENSOR_FAULT_SUSPECTED."""
    payload = {
        "device_id": "AQUA-01",
        "ph": 2.1,           # Severe outlier
        "turbidity": 1.3,    # Normal
        "ec": 310.0,         # Normal
        "temperature": 26.9, # Normal
    }
    res = client.post("/api/telemetry", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["sensor_health"] == "FAULT_SUSPECTED"

    # Verify sensor health API
    health_res = client.get("/api/health?device_id=AQUA-01")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] == "FAULT_SUSPECTED"
    assert health_data["suspect_sensor"] == "pH"
    assert "probe failure" in health_data["details"].lower() or "sensor" in health_data["details"].lower()


def test_05_agent_investigation_and_grounded_disclaimer():
    """Verify Agent calls 6 tools and returns evidence-based explanation with disclaimer."""
    # First inject disturbance
    client.post("/api/demo/scenario/disturbance")

    # Ask the agent
    ask_payload = {"message": "Why is this an anomaly? Explain what happened."}
    res = client.post("/api/agent/ask", json=ask_payload)
    assert res.status_code == 200
    data = res.json()

    assert "response" in data
    assert len(data["tools_called"]) == 6
    assert data["disclaimer"] == settings.SCIENTIFIC_DISCLAIMER
    assert settings.SCIENTIFIC_DISCLAIMER in data["response"]
    assert "turbidity" in data["response"].lower()
    assert "conductivity" in data["response"].lower() or "ec" in data["response"].lower()


def test_06_demo_scenario_endpoints():
    """Verify all 3 demo scenario endpoints run cleanly."""
    res_norm = client.post("/api/demo/scenario/normal")
    assert res_norm.status_code == 200
    assert res_norm.json()["scenario"] == "NORMAL"

    res_dist = client.post("/api/demo/scenario/disturbance")
    assert res_dist.status_code == 200
    assert res_dist.json()["scenario"] == "DISTURBANCE"
    assert res_dist.json()["anomaly_result"]["is_anomaly"] is True

    res_fault = client.post("/api/demo/scenario/sensor_fault")
    assert res_fault.status_code == 200
    assert res_fault.json()["scenario"] == "SENSOR_FAULT"
    assert res_fault.json()["sensor_health"]["status"] == "FAULT_SUSPECTED"
