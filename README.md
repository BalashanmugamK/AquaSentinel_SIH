# AquaSentinel — Prototype Vertical Slice

One ESP32 → 4 sensors → Wi-Fi/HTTP → FastAPI backend → database → anomaly
detection → n8n → single Sarvam-powered investigation agent →
evidence-based explanation → dashboard.

This repo is the software headstart for the 5-day prototype build
(see `AquaSentinel_Prototype_WBS.docx` and the SRS scope-correction doc for
full context — this code follows that scoping exactly: one node, HTTP not
MQTT, z-score anomaly detection, single agent, no CV/digital
twin/forecasting).

```
firmware/   Workstream A — ESP32 firmware skeleton (Sudhish)
backend/    Workstream B — FastAPI + DB + anomaly detection + agent tools (Bala)
n8n/        Workstream D — orchestration workflow (Tharun)
agent/      Workstream D — Sarvam-powered investigation + Q&A agent (Monisha + Bala)
dashboard/  Workstream E — status dashboard (Durga)
whatsapp/   Workstream E, Should-Have — WhatsApp Q&A interface (Tharun)
voice/      Workstream E, Should-Have — push-to-talk voice interface (Tharun)
```

The Must-Have vertical slice is `firmware → backend → n8n → agent → dashboard`.
`whatsapp/` and `voice/` are Should-Have per SRS §20-21 — build and demo
them only after that core loop is solid; neither can block the core demo.

## Quick start (local, no hardware needed)

### 1. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for interactive API docs.

Simulate a few normal readings, then an anomalous one, to see an event get
created automatically:

```bash
API=http://localhost:8000/api/readings
KEY="changeme-dev-key"   # must match AQUASENTINEL_API_KEY in backend/.env

# 12 "normal" readings so the baseline has enough history
for i in $(seq 1 12); do
  curl -s -X POST $API -H "Content-Type: application/json" -H "X-API-Key: $KEY" \
    -d '{"node_id":"node-01","ph":7.1,"tds":280,"turbidity":1.2,"temperature":27.1}' > /dev/null
done

# one anomalous reading (spike in turbidity + TDS)
curl -X POST $API -H "Content-Type: application/json" -H "X-API-Key: $KEY" \
  -d '{"node_id":"node-01","ph":6.2,"tds":650,"turbidity":7.8,"temperature":30.0}'
```

The response includes `anomaly_event` if one was created. Check it:

```bash
curl http://localhost:8000/api/events?node_id=node-01
```

### 2. Investigation agent

```bash
cd agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in SARVAM_API_KEY
uvicorn investigation_agent:app --reload --port 8001
```

Test it directly against an event_id from step 1:

```bash
curl -X POST http://localhost:8001/investigate \
  -H "Content-Type: application/json" \
  -d '{"event_id": "<event_id from above>"}'
```

### 3. n8n

1. Run n8n (`npx n8n` or Docker).
2. Import `n8n/aquasentinel_workflow.json` (Workflows → Import from File).
3. Set environment variables n8n needs: `AGENT_URL` (e.g.
   `http://localhost:8001`), `BACKEND_URL` (e.g. `http://localhost:8000`),
   `AQUASENTINEL_API_KEY` (matches backend `.env`).
4. Activate the workflow, copy its webhook URL, and set that as
   `N8N_WEBHOOK_URL` in `backend/.env`. Restart the backend.

Now every anomalous reading posted to the backend will automatically
trigger n8n → agent → write-back, with no manual step.

### 4. Dashboard

Just open `dashboard/index.html` in a browser (or serve it with any static
file server). Set the backend URL/node ID in the two inputs at the bottom
if not using the defaults.

### 5. WhatsApp Q&A (Should-Have)

```bash
cd whatsapp
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in Meta WhatsApp Cloud API credentials
uvicorn whatsapp_bot:app --reload --port 8002
```

Without real WhatsApp credentials set, inbound-message replies just print
to the console (`[dev mode]`) so you can still test the agent-question
flow locally. To go live: create a Meta WhatsApp Business app, point its
webhook at `https://<your-host>/webhook` with the same verify token as
`WHATSAPP_VERIFY_TOKEN`, and fill in `WHATSAPP_ACCESS_TOKEN` /
`WHATSAPP_PHONE_NUMBER_ID`.

### 6. Voice — push-to-talk (Should-Have)

```bash
cd voice
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in SARVAM_API_KEY
uvicorn voice_service:app --reload --port 8003
```

Test with any short WAV/MP3 clip asking a question like "why is my water abnormal?":

```bash
curl -X POST http://localhost:8003/voice-query \
  -F "audio=@question.wav" \
  --output reply.wav
```

`reply.wav` is the spoken answer (Sarvam Bulbul TTS). The transcript and
answer text are also returned as base64 in the `X-Transcript-B64` /
`X-Answer-Text-B64` response headers, for debugging.

Both `agent/` services (`/investigate` and `/ask`) must be running first —
WhatsApp and voice are thin front-ends over the same agent.

### 7. Firmware

`firmware/esp32_node/esp32_node.ino` is configured for physical hardware sensors with 30-sample median filtering, ADC1-safe pins, temperature compensation, and configurable calibration constants:

- **Sensors & Wiring (ESP32 DevKit V1)**:
  - **DS18B20 Temp (Digital 1-Wire)**: GPIO 4 (with 4.7kΩ pull-up resistor to 3.3V)
  - **pH Sensor (Analog)**: GPIO 34 (ADC1_CH6)
  - **TDS Sensor (Analog)**: GPIO 35 (ADC1_CH7)
  - **Turbidity Sensor (Analog)**: GPIO 32 (ADC1_CH4)
  - *All analog sensors use ADC1 to prevent conflict with active Wi-Fi.*

- **Required Arduino Libraries**:
  1. `ArduinoJson` (v6 or v7)
  2. `OneWire`
  3. `DallasTemperature`

- **Sensor Pipeline & Calibration**:
  - **Temperature**: Digital OneWire reading with 25.0°C fallback if disconnected.
  - **TDS (ppm)**: $V_{comp} = \frac{V}{1.0 + 0.02 \times (T - 25.0)}$, followed by polynomial conversion and `TDS_K_VALUE` scaling.
  - **pH**: $pH = 7.0 + \frac{V_{neutral} - V}{pH_{slope}}$ (configurable `PH_NEUTRAL_VOLTAGE` and `PH_SLOPE_VOLTAGE_PER_PH`).
  - **Turbidity (NTU)**: Configurable polynomial coefficients `TURBIDITY_A`, `TURBIDITY_B`, `TURBIDITY_C` with clean-water thresholding.


## Design notes

- **Database**: SQLite by default (zero setup) via `DATABASE_URL`; point it
  at Postgres later with no code changes (`backend/app/config.py`).
- **Anomaly detection**: rolling mean/std + z-score per parameter
  (`backend/app/anomaly.py`). Swap-in point for a better model later —
  only `score_reading()` needs to change.
- **Auth**: a single shared `X-API-Key` header on write endpoints
  (ingest + event patch). Prototype-level only, per SRS Section 26 — not
  full RBAC.
- **Agent tools**: `get_current_readings`, `get_historical_readings`,
  `get_anomaly_event`, `get_sensor_status` — all backed by the same
  backend used by the dashboard, so there's one source of truth
  (`backend/app/routers/tools.py`, called from `agent/investigation_agent.py`).
- **Reliability**: if n8n/agent/Sarvam is unavailable, ingestion and
  storage keep working — the webhook notify is fire-and-forget
  (SRS Section 27).
- **Q&A vs. investigation**: `agent/investigation_agent.py` exposes two
  endpoints on the same Sarvam tool-calling loop — `/investigate` (fixed
  event_id, structured JSON output, called by n8n) and `/ask` (free-text
  question, plain-text answer, called by WhatsApp/voice). Both share the
  same four tools and the same "no lab-certainty claims" system-prompt rule.

## What's intentionally NOT here

Per the SRS scope-correction doc: second ESP32, MQTT, camera/CV,
forecasting, digital twin, weather/satellite integration, multi-agent
orchestration, full RBAC, large RAG. All future work, not prototype-blocking.
