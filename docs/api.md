# AquaSentinel REST API Reference

Base URL: `http://localhost:8000` (or your ngrok forwarding URL)

Interactive OpenAPI / Swagger UI: `http://localhost:8000/docs`

---

## 1. Telemetry Ingestion

### `POST /api/telemetry`
Receives and stores raw sensor telemetry packet from ESP32 / Wokwi simulator, evaluates statistical baseline & z-scores, checks sensor health, and manages alert events.

**Request Body:**
```json
{
  "device_id": "AQUA-01",
  "timestamp": "2026-08-18T10:00:00Z",
  "ph": 7.20,
  "turbidity": 1.35,
  "ec": 315.0,
  "temperature": 27.1
}
```

**Response (201 Created):**
```json
{
  "status": "SUCCESS",
  "message": "Telemetry reading ingested successfully",
  "reading_id": 42,
  "device_id": "AQUA-01",
  "is_anomaly": false,
  "anomaly_score": 0.05,
  "sensor_health": "HEALTHY",
  "event_active": false
}
```

---

## 2. Telemetry Queries

### `GET /api/readings/latest?device_id=AQUA-01`
Retrieves the most recent telemetry record.

**Response (200 OK):**
```json
{
  "id": 42,
  "device_id": "AQUA-01",
  "timestamp": "2026-08-18T10:00:00Z",
  "ph": 7.2,
  "turbidity": 1.35,
  "ec": 315.0,
  "temperature": 27.1
}
```

### `GET /api/readings/history?device_id=AQUA-01&limit=50`
Retrieves chronologically sorted historical records for multi-series trend visualization.

---

## 3. Anomaly & Diagnostics

### `GET /api/anomalies/latest?device_id=AQUA-01`
Retrieves the latest anomaly evaluation result with z-scores, composite score, and explainable reasons.

**Response (200 OK):**
```json
{
  "is_anomaly": true,
  "anomaly_score": 0.87,
  "reasons": [
    "Turbidity (25.0 NTU) breached environmental threshold (> 15.0 NTU)",
    "Electrical Conductivity (EC) (920.0 µS/cm) breached safe conductivity limit (> 800.0 µS/cm)"
  ],
  "z_scores": {
    "ph": 0.42,
    "turbidity": 47.1,
    "ec": 19.3,
    "temperature": 0.58
  },
  "timestamp": "2026-08-18T10:02:15Z",
  "disclaimer": "The system detects anomalous water-quality patterns and generates evidence-based early warnings. It does not claim to identify a specific contaminant without validated labeled data."
}
```

### `GET /api/health?device_id=AQUA-01`
Retrieves sensor hardware health status and fault isolation analysis.

**Response (200 OK):**
```json
{
  "status": "HEALTHY",
  "suspect_sensor": null,
  "details": "Sensors operating normally. Multiple co-varying parameters indicate an actual physical disturbance.",
  "metrics_status": {
    "ph": "NORMAL",
    "turbidity": "DEVIATING",
    "ec": "DEVIATING",
    "temperature": "NORMAL"
  },
  "timestamp": "2026-08-18T10:02:15Z"
}
```

---

## 4. Events & Alerts

### `GET /api/events?device_id=AQUA-01&limit=20`
Retrieves active and historical events with severity and deduplicated timestamps.

---

## 5. AI Investigation Agent

### `POST /api/agent/ask`
Invokes the Investigation Agent via 6 read-only tools and Sarvam AI / deterministic fallback engine.

**Request Body:**
```json
{
  "message": "Why is this an anomaly?",
  "session_id": "web-dashboard"
}
```

**Response (200 OK):**
```json
{
  "response": "### 🔴 Alert: Water Quality Disturbance Pattern Detected\n\n**Current State (Anomaly Score: 0.87):**\n- **Turbidity**: **25.0 NTU** (Learned baseline: 1.5 ± 0.5 NTU)\n- **Electrical Conductivity**: **920.0 µS/cm** (Learned baseline: 320.0 ± 30.0 µS/cm)\n\n**Evidence Interpretation:**\nBoth turbidity and EC rose together. Sensor health confirms all 4 channels are functional (`HEALTHY`), indicating an environmental event.\n\n> **Scientific Notice**: The system detects anomalous water-quality patterns and generates evidence-based early warnings. It does not claim to identify a specific contaminant without validated labeled data.",
  "tools_called": [
    { "tool_name": "get_current_readings", "arguments": { "device_id": "AQUA-01" }, "output_summary": { "ph": 7.3, "turbidity_ntu": 25.0, "ec_us_cm": 920.0, "temperature_c": 27.5 } },
    { "tool_name": "get_baseline", "arguments": { "device_id": "AQUA-01" }, "output_summary": { ... } },
    { "tool_name": "get_anomaly_result", "arguments": { "device_id": "AQUA-01" }, "output_summary": { "is_anomaly": true, "score": 0.87 } },
    { "tool_name": "get_sensor_health", "arguments": { "device_id": "AQUA-01" }, "output_summary": { "status": "HEALTHY", "suspect": null } },
    { "tool_name": "get_active_events", "arguments": { "device_id": "AQUA-01" }, "output_summary": { "active_count": 1 } },
    { "tool_name": "get_recent_history", "arguments": { "device_id": "AQUA-01", "limit": 5 }, "output_summary": "5 records" }
  ],
  "provider_used": "Deterministic Rule-Based Engine (Fallback)",
  "grounded_facts": { ... },
  "disclaimer": "The system detects anomalous water-quality patterns and generates evidence-based early warnings. It does not claim to identify a specific contaminant without validated labeled data."
}
```

---

## 6. Demo Control Endpoints

- `POST /api/demo/scenario/normal`
- `POST /api/demo/scenario/disturbance`
- `POST /api/demo/scenario/sensor_fault`
