# AquaSentinel Architecture & Technical Design

AquaSentinel implements an automated real-time water quality intelligence cycle:
**Sense → Send → Store → Analyze → Detect → Investigate → Explain → Alert.**

---

## 1. System Philosophy & Scientific Defensibility

Water contamination events in open water bodies, reservoirs, and aquaculture tanks are often high-consequence yet sparse in ground-truth labeled analytical chemistry assays. Claiming to identify specific chemical toxins (e.g., arsenic, benzene) purely from low-cost physicochemical surrogate probes without laboratory spectrometry is scientifically unsound.

AquaSentinel strictly bakes the following **Scientifically Defensible Claim** into every alert, explanation, and agent output:

> *"The system detects anomalous water-quality patterns and generates evidence-based early warnings. It does not claim to identify a specific contaminant without validated labeled data."*

---

## 2. End-to-End Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Wokwi Hardware Simulator                        │
│                                                                        │
│  [DS18B20 Temp (GPIO 4)]        [Pot 1: pH (GPIO 34)]                  │
│  [Pot 2: Turbidity (GPIO 35)]   [Pot 3: TDS/EC (GPIO 32)]              │
│                                 │                                      │
│                                 ▼                                      │
│           ESP32 Microcontroller: JSON Packaging & HTTPS POST           │
│                                 │                                      │
│                      "Wokwi-GUEST" Outbound Gateway                    │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Public Ingress Transport                        │
│             https://<ngrok-id>.ngrok-free.app/api/telemetry            │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │ (ngrok tunnel)
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (localhost:8000)                    │
│                                                                        │
│  1. Ingestion Endpoint (`/api/telemetry`)                              │
│     - Pydantic schema validation & bounds checking                     │
│     - SQLite persistence (`TelemetryRecord`)                           │
│                                                                        │
│  2. Anomaly Engine (`AnomalyService`)                                  │
│     - Rolling historical baseline calculation (mean, std, min, max)    │
│     - Statistical z-score computation per channel                      │
│     - Composite anomaly scoring [0.0 - 1.0]                            │
│                                                                        │
│  3. Sensor Health & Fault Isolation (`SensorHealthService`)            │
│     - Single vs Multi-parameter deviation isolation                    │
│     - Single outlier → `FAULT_SUSPECTED` (Hardware/Probe failure)      │
│     - Co-varying outliers → `HEALTHY` (True water body disturbance)    │
│                                                                        │
│  4. Event Engine (`EventService`)                                      │
│     - Dedup & Cooldown tracking (`EVENT_COOLDOWN_SECONDS = 30`)        │
│     - Creates `WATER_QUALITY_ANOMALY` or `SENSOR_FAULT_SUSPECTED`      │
│                                                                        │
│  5. 6 Read-Only Tools (`backend/app/agent/tools.py`)                   │
│     • `get_current_readings()`   • `get_recent_history()`              │
│     • `get_baseline()`           • `get_anomaly_result()`              │
│     • `get_active_events()`      • `get_sensor_health()`               │
│                                                                        │
│  6. Investigation Agent (`backend/app/agent/agent.py`)                 │
│     - Sarvam AI LLM provider (`sarvam-2b`)                             │
│     - Deterministic rule-based fallback provider                       │
└───────────────────────────▲─────────────────────────────▲──────────────┘
                            │                             │
                     Trigger Request (Ask)        Live Telemetry Polling
                            │                             │
┌───────────────────────────┴─────────────┐ ┌─────────────┴──────────────┐
│           Orchestration (n8n)           │ │       React Dashboard       │
│  Webhook Trigger                        │ │  - Real-time Metric Cards  │
│        ↓                                │ │  - SVG Multi-Series Trend  │
│  HTTP Request (POST /api/agent/ask)     │ │  - Status & Anomaly Banner │
│        ↓                                │ │  - Active Event Alert Feed │
│  Webhook Response                       │ │  - AI Investigation Chat   │
└─────────────────────────────────────────┘ └────────────────────────────┘
```

---

## 3. Simulated Hardware to Physical Sensor Mapping

Because Wokwi does not have native analog electrochemical simulation models for pH, TDS, and optical nephelometric turbidity, 3 standard 10k potentiometers are used as controllable analog voltage stand-ins.

| Simulated Input in Wokwi | Hardware Pin | Simulated Engineering Range | Normal Water Baseline | Disturbance Range |
| :--- | :--- | :--- | :--- | :--- |
| **DS18B20 (Native Wokwi part)** | GPIO 4 (Digital 1-Wire) | -55.0 °C to +125.0 °C | 26.5 °C ± 1.0 °C | 26.0 – 28.0 °C |
| **pH (Potentiometer 1)** | GPIO 34 (ADC1_CH6) | 0.00 – 14.00 pH | 7.00 – 7.40 pH | Normal or Acidic Fault (< 3.0) |
| **Turbidity (Potentiometer 2)** | GPIO 35 (ADC1_CH7) | 0.0 – 100.0 NTU | 1.0 – 2.0 NTU | 20.0 – 50.0 NTU (Spike) |
| **TDS / EC (Potentiometer 3)** | GPIO 32 (ADC1_CH4) | 0 – 2000 µS/cm | 280 – 350 µS/cm | 800 – 1500 µS/cm (Spike) |

---

## 4. Anomaly Detection & Sensor Health Mathematics

### Statistical Rolling Baseline
For each parameter $x \in \{\text{pH}, \text{turbidity}, \text{ec}, \text{temp}\}$, over a window of $N=50$ recent records:
$$\mu_x = \frac{1}{N} \sum_{i=1}^{N} x_i, \quad \sigma_x = \sqrt{\frac{1}{N}\sum_{i=1}^{N}(x_i - \mu_x)^2}$$

### Z-Score Metric
$$Z_x = \frac{x_{\text{current}} - \mu_x}{\sigma_x}$$
An individual metric breaches statistical normal bounds if $|Z_x| \ge 2.5$.

### Fault Isolation Decision Matrix

| Condition | Anomaly Evaluation | Sensor Health Status | Event Generated | Explanation Grounding |
| :--- | :--- | :--- | :--- | :--- |
| All $|Z_x| < 2.5$ and within safe limits | `is_anomaly = False` | `HEALTHY` | None / Resolved | All metrics nominal. |
| $\ge 2$ sensors deviate (e.g. Turbidity $\uparrow$ + EC $\uparrow$) | `is_anomaly = True` (Score $\approx 0.85$) | `HEALTHY` | `WATER_QUALITY_ANOMALY` | Co-varying optical & conductivity shift; true water disturbance. |
| Exactly 1 sensor deviates (e.g. pH = 2.0 while Turbidity, EC, Temp normal) | `is_anomaly = True` (Score $\approx 0.70$) | `FAULT_SUSPECTED` | `SENSOR_FAULT_SUSPECTED` | Isolated single probe outlier; consistent with hardware drift/failure. |
