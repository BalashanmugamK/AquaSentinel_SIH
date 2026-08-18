# n8n Orchestration Guide for AquaSentinel

This guide details how **n8n** is used as the event orchestration and trigger layer for AquaSentinel.

---

## 1. Architectural Role of n8n

> **Architecture Principle**:
> n8n acts as the **orchestration/trigger layer**, NOT the repository of business logic or prompt engineering. All investigation tools and reasoning live in `backend/app/agent/`. n8n triggers the investigation and relays the grounded response.

```
┌─────────────────────────────────────────────────────────────┐
│                     Event / Frontend / User                 │
└──────────────────────────────┬──────────────────────────────┘
                               │ POST /webhook/aquasentinel-investigate
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       n8n Workflow                          │
│                                                             │
│  [ Webhook Trigger ]                                        │
│          ↓                                                  │
│  [ HTTP Request Node ] ──► POST http://localhost:8000/api/agent/ask
│          ↓                                                  │
│  [ Respond to Webhook ] ◄─ Returns Grounded JSON Payload    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Agent                          │
│   • Executes 6 Backend Read-Only Tools                      │
│   • Sarvam AI / Deterministic Fallback Reasoner             │
│   • Grounded Evidence & Scientific Disclaimer               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Importing & Activating the Workflow

### Step 1: Start n8n
If you have n8n installed:
```bash
n8n start
```
Or via Docker:
```bash
docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n
```
Open [http://localhost:5678](http://localhost:5678) in your browser.

### Step 2: Import Workflow File
1. In the n8n UI, navigate to **Workflows**.
2. Click **Import from File...** (or press `Ctrl + O` / `Cmd + O`).
3. Select `n8n/aquasentinel-investigation.workflow.json`.

### Step 3: Activate Workflow
Click the **Active** toggle in the top-right corner of the workflow editor.

---

## 3. Testing the n8n Workflow

### Automated Verification Script
With FastAPI running, run:
```bash
python scripts/test_n8n_flow.py
```

### Manual Trigger with curl
```bash
curl -X POST http://localhost:5678/webhook/aquasentinel-investigate \
  -H "Content-Type: application/json" \
  -d '{"message": "Why is this an anomaly?"}'
```

**Expected JSON Response:**
```json
{
  "response": "### 🔴 Alert: Water Quality Disturbance Pattern Detected\n\n...",
  "tools_called": [
    { "tool_name": "get_current_readings" },
    { "tool_name": "get_baseline" },
    { "tool_name": "get_anomaly_result" },
    { "tool_name": "get_sensor_health" },
    { "tool_name": "get_active_events" },
    { "tool_name": "get_recent_history" }
  ],
  "provider_used": "Deterministic Rule-Based Engine (Fallback)",
  "disclaimer": "The system detects anomalous water-quality patterns and generates evidence-based early warnings. It does not claim to identify a specific contaminant without validated labeled data."
}
```
