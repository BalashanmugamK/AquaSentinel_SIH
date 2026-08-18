# AquaSentinel 🌊
### Agentic AI Water Intelligence & Early-Warning System

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-cyan.svg)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AquaSentinel is an end-to-end, runnable proof-of-concept for real-time water quality intelligence. It continuously monitors physicochemical telemetry, isolates sensor hardware faults from real environmental anomalies, and triggers an agentic investigation agent to produce evidence-grounded early warnings.

---

## 🎯 The Scientific Core

> **Scientifically Defensible Claim**:  
> *"The system detects anomalous water-quality patterns and generates evidence-based early warnings. It does not claim to identify a specific contaminant without validated labeled data."*

The system never hallucinates chemical pollutants without certified spectrometry assays.

---

## 🔄 The 8-Stage Intelligence Cycle

```
  [ SENSE ]   ESP32 + DS18B20 + 3 Potentiometers (pH, Turbidity, EC)
      │
  [  SEND ]   HTTPS POST over Wokwi Outbound Gateway → ngrok Tunnel
      │
  [ STORE ]   SQLite Ingestion & Time-Series History
      │
 [ ANALYZE ]  Rolling Baseline Estimation (Mean, Std Dev, Min, Max)
      │
  [ DETECT ]  Z-Score Statistical Scoring & Environmental Thresholds
      │
[ INVESTIGATE ] 6 Read-Only Tools + Sensor Fault Isolation
      │
  [ EXPLAIN ] Sarvam AI / Deterministic Fallback Reasoner
      │
  [  ALERT ]  Deduplicated Warning Events & Real-Time React Dashboard
```

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Wokwi Hardware Simulation                   │
│   • DS18B20 Digital Temp Sensor (GPIO 4)                    │
│   • pH Potentiometer (GPIO 34)                              │
│   • Turbidity Potentiometer (GPIO 35)                       │
│   • TDS/EC Potentiometer (GPIO 32)                          │
│   • Outbound Wi-Fi ("Wokwi-GUEST") → HTTPS POST             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      Public ngrok Tunnel                    │
│        https://<id>.ngrok-free.app/api/telemetry            │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI Backend (localhost:8000)              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Ingestion & Persistent SQLite Database                  │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ Statistical Anomaly Engine (Z-Score + Thresholds)       │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ Sensor Health Engine (Single vs Multi-Parameter Check)  │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ Event Engine (Dedup & Cooldown Alerts)                  │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ 6 Read-Only Backend Tools (app/agent/tools.py)          │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ Sarvam AI LLM Agent + Deterministic Fallback Reasoner   │ │
│ └─────────────────────────────────────────────────────────┘ │
└───────────────▲─────────────────────────────▲───────────────┘
                │                             │
    HTTP Webhook/Trigger (Ask)            Live Polling & Chat
                │                             │
┌───────────────┴─────────────┐ ┌─────────────┴───────────────┐
│        n8n Workflow         │ │       React Dashboard       │
│ Single Trigger → Backend    │ │  • Real-Time Metric Cards   │
│ HTTP Request → Response     │ │  • Multi-Series Trend Chart │
│ Relay (No business logic)   │ │  • Anomaly & Health Badges  │
│                             │ │  • AI Investigation Chat    │
└─────────────────────────────┘ └─────────────────────────────┘
```

---

## 📁 Repository Structure

```
aquasentinel/
├── README.md                                  # Complete documentation
├── render.yaml                                # Render Blueprint 1-click cloud deployment
├── Dockerfile                                 # Production container image
├── .python-version                            # Python runtime pin (3.12.2)
├── .env.example                               # Environment template
├── pytest.ini                                 # Pytest configuration
├── deploy/
│   └── render/
│       ├── Dockerfile                         # Standalone Docker deployment
│       ├── render.yaml                        # Blueprint configuration
│       └── start.sh                           # Boot script with auto-baseline seed
├── wokwi/
│   ├── diagram.json                           # ESP32 + DS18B20 + 3 Potentiometers
│   ├── wokwi.toml                             # Wokwi simulation config
│   └── src/
│       └── main.ino                           # ESP32 Arduino C++ firmware
├── backend/
│   ├── requirements.txt                       # Pinned Python dependencies
│   └── app/
│       ├── main.py                            # FastAPI app entry point
│       ├── config.py                          # Settings & scientific disclaimer
│       ├── database.py                        # SQLAlchemy SQLite session engine
│       ├── models.py                          # Database ORM models
│       ├── schemas.py                         # Pydantic validation schemas
│       ├── services/
│       │   ├── telemetry_service.py           # Ingestion & storage pipeline
│       │   ├── anomaly_service.py             # Z-score & baseline calculation
│       │   ├── sensor_health_service.py       # Single vs multi-sensor fault isolation
│       │   └── event_service.py               # Cooldown & deduplication event engine
│       ├── agent/
│       │   ├── agent.py                       # Sarvam AI client + fallback reasoner
│       │   └── tools.py                       # 6 read-only backend tools
│       └── api/
│           ├── telemetry.py                   # Ingestion & query endpoints
│           ├── events.py                      # Events, anomaly & health endpoints
│           ├── agent.py                       # AI question-answering route
│           └── demo.py                        # Fast demo scenario endpoints
├── n8n/
│   └── aquasentinel-investigation.workflow.json # n8n orchestration workflow
├── frontend/
│   ├── package.json                           # React + Vite configuration
│   ├── vite.config.js                         # Dev proxy configuration
│   ├── index.html                             # Web app shell
│   ├── dist/                                  # Compiled production static bundle
│   └── src/
│       ├── main.jsx                           # React entry point
│       ├── index.css                          # Oceanic glassmorphism design system
│       ├── App.jsx                            # Dashboard root component
│       └── components/
│           ├── Header.jsx                     # Branding & connection monitor
│           ├── DemoControls.jsx               # Quick scenario trigger pills
│           ├── StatusBanner.jsx               # Dynamic NORMAL / ANOMALY / FAULT banner
│           ├── MetricCards.jsx                # Telemetry values with baseline comparisons
│           ├── TrendChart.jsx                 # Multi-series SVG time-series chart
│           ├── EventsFeed.jsx                 # Active alert event log
│           └── AgentChat.jsx                  # AI investigation chat with tool inspection
├── scripts/
│   ├── seed_data.py                           # Historical baseline generator
│   ├── demo.py                                # Colorized CLI live demo runner
│   ├── simulate_wokwi_esp32.py                # Standalone edge node telemetry simulator
│   └── test_n8n_flow.py                       # n8n payload contract integration test
├── tests/
│   └── test_end_to_end.py                     # Pytest automated test suite
└── docs/
    ├── architecture.md                        # Deep architectural design
    ├── demo.md                                # 5-minute live presentation script
    ├── render_deployment.md                   # Complete Render cloud deployment guide
    ├── n8n_guide.md                           # n8n workflow setup & execution guide
    ├── ngrok_setup.md                         # ngrok tunnel setup & troubleshooting
    └── api.md                                 # REST API specification
```

---

## ☁️ 1-Click Cloud Deployment on Render

You can deploy the full AquaSentinel backend and live React dashboard to Render with a single click:

1. Push this repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com), click **New + → Blueprint**.
3. Select this repository — Render will automatically read [`render.yaml`](file:///c:/Users/brill/Downloads/aquasentinel/render.yaml) and configure the build/start commands and health checks.
4. **Permanent Public URL**: Once deployed, you get a public HTTPS address (e.g. `https://aquasentinel-backend.onrender.com`). You can paste this directly into `wokwi/src/main.ino` to stream Wokwi telemetry without requiring ngrok!

*(See [docs/render_deployment.md](file:///c:/Users/brill/Downloads/aquasentinel/docs/render_deployment.md) for step-by-step screenshots and manual setup).*

---

## 🛠️ Prerequisites & Installation

### 1. Prerequisites
- **Python 3.11 or 3.12+**
- **Node.js 18+ & npm** (optional for dev server; production bundle is already pre-built)
- **ngrok** (optional for local Wokwi simulation; not needed if deployed on Render)

### 2. Setup Python Virtual Environment
```bash
# Clone or navigate to the repository
cd aquasentinel

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
To enable Sarvam AI, set:
```env
LLM_PROVIDER=sarvam
SARVAM_API_KEY=your_actual_sarvam_api_key
SARVAM_MODEL_NAME=sarvam-2b
```
> *Note: If no API key is provided, the backend automatically uses its deterministic rule-based reasoning engine. All features, tools, and demo scenarios run 100% locally with zero external dependencies.*

---

## 🚀 Running AquaSentinel

### Step 1: Initialize Database Baseline
Populate the SQLite database with 100 historical readings to establish the normal water baseline:
```bash
python scripts/seed_data.py
```

### Step 2: Start the FastAPI Backend
```bash
uvicorn backend.app.main:app --port 8000 --reload
```
- Web Dashboard: [http://localhost:8000](http://localhost:8000)
- Interactive API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)

### Step 3: (Optional) Start Frontend in Vite Dev Mode
```bash
cd frontend
npm install
npm run dev
```
- Vite Dev Dashboard: [http://localhost:3000](http://localhost:3000)

---

## 🌐 Wokwi Simulation & ngrok Ingestion

Wokwi's free tier only permits outbound internet connections (`Wokwi-GUEST`). An ngrok tunnel routes the ESP32's HTTPS POSTs to your local machine:

1. **Start ngrok**:
   ```bash
   ngrok http 8000
   ```
2. **Copy Forwarding URL** (e.g. `https://xyz-123.ngrok-free.app`).
3. **Update Firmware**:
   In `wokwi/src/main.ino`, set:
   ```cpp
   const char* BACKEND_TELEMETRY_URL = "https://xyz-123.ngrok-free.app/api/telemetry";
   ```
4. **Import to Wokwi**:
   Open [wokwi.com](https://wokwi.com), upload `wokwi/diagram.json` and `wokwi/src/main.ino`, and click **Start Simulation**.

### Hardware Potentiometer Mapping:
- **DS18B20 (Native Wokwi component)**: Water Temperature (°C) on Pin 4.
- **Potentiometer 1 (Left, labeled "pH (simulated)")**: Maps to 0.00 – 14.00 pH on Pin 34.
- **Potentiometer 2 (Middle, labeled "Turbidity (simulated)")**: Maps to 0.0 – 100.0 NTU on Pin 35.
- **Potentiometer 3 (Right, labeled "TDS / EC (simulated)")**: Maps to 0 – 2000 µS/cm on Pin 32.

---

## 🎬 The 5-Minute Live Demo Walkthrough

### 🟢 Scenario 1: NORMAL Operation
- **Action**: Keep all 3 potentiometers at normal values (pH ~7.2, Turbidity ~1.2 NTU, EC ~310 µS/cm).
- **Dashboard**: Displays 🟢 **NORMAL (NOMINAL)**. Anomaly score: `0.05`.
- **Ask Agent**: *"How is my water?"*
- **Agent Response**: Cites exact tool-retrieved readings and confirms all parameters are within learned nominal boundaries.

### 🔴 Scenario 2: DISTURBANCE (Environmental Anomaly)
- **Action**: Turn Potentiometer 2 (Turbidity) to ~25 NTU and Potentiometer 3 (EC) to ~900 µS/cm.
- **Dashboard**: Flips to 🔴 **WATER QUALITY ANOMALY DETECTED (Score: 0.87)**. Event `WATER_QUALITY_ANOMALY` created. Sensor health stays `HEALTHY`.
- **Ask Agent**: *"Why is this an anomaly? What happened?"*
- **Agent Response**: Explains that Turbidity and EC rose in synchronization relative to baseline. Emphasizes evidence-based early warning and advises certified field sampling without hallucinating a specific chemical contaminant.

### 🟡 Scenario 3: SENSOR_FAULT (Isolated Hardware Drift)
- **Action**: Turn only Potentiometer 1 (pH) down to ~2.0 pH while Turbidity and EC remain normal.
- **Dashboard**: Changes to 🟡 **SENSOR FAULT SUSPECTED (ISOLATED PROBE DRIFT)**. Suspect sensor: `pH`.
- **Ask Agent**: *"Is this likely a sensor problem?"*
- **Agent Response**: Reasons that single-parameter deviation with all 3 other channels stable is characteristic of probe failure or electrical drift rather than water contamination.

---

## ⚡ Standalone CLI Demo Runner
To run all 3 scenarios in an automated terminal script without touching Wokwi:
```bash
python scripts/demo.py
```

---

## 🤖 n8n Workflow Integration

1. Start n8n (`n8n start` or open your n8n workspace).
2. Go to **Workflows → Import from File** and select `n8n/aquasentinel-investigation.workflow.json`.
3. The workflow provides a streamlined trigger → HTTP Request (`http://localhost:8000/api/agent/ask`) → Webhook Response relay.

---

## 🧪 Automated Testing

Execute the comprehensive pytest test suite verifying the complete 10-step intelligence loop:
```bash
python -m pytest tests/test_end_to_end.py -v
```

---

## ⚠️ Limitations & Known Friction Points

1. **Wokwi Potentiometer Analog Stand-ins**: Wokwi does not simulate electrochemical fluid dynamics; potentiometers are controllable analog voltage stand-ins.
2. **ngrok Ephemeral URLs**: On ngrok's free tier, restarting ngrok creates a new URL that must be copied to `wokwi/src/main.ino`. Use `/api/demo/scenario/*` or `scripts/demo.py` for reliable local demos without ngrok.
3. **Single Monitored Node**: This MVP focuses on a single simulated node (`AQUA-01`).

---

## 🔮 Future Extensions (Out of Scope for MVP)

- Multi-node spatial mesh & digital twin mapping
- LoRaWAN, cellular (NB-IoT), and satellite telemetry transports
- Dissolved oxygen (DO), oxidation-reduction potential (ORP), and heavy-metal optical sensors
- Computer vision surface camera monitoring
- Deep learning sequence modeling (LSTM / GRU / Transformers)
- Multi-agent swarm orchestration for dispatch and automated physical valve actuation
