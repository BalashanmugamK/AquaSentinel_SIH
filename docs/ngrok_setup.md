# ngrok Tunnel Setup for Wokwi ESP32 Ingestion

## 1. Why ngrok is required for Wokwi Simulation

Wokwi's free cloud simulation gateway (`WiFi.begin("Wokwi-GUEST", "", 6)`) allows the simulated ESP32 microcontroller to make **outbound internet requests** (HTTPS/HTTP). However, Wokwi's virtual machine cannot access `localhost` or private local area network (LAN) IP addresses on your host computer.

Therefore, an ngrok reverse proxy tunnel exposes your local FastAPI server running on `http://localhost:8000` to a secure public HTTPS address accessible by the simulated ESP32.

```
┌─────────────────┐      HTTPS POST       ┌───────────────────────────────┐
│   Wokwi ESP32   │ ───────────────────►  │  https://<id>.ngrok-free.app  │
└─────────────────┘                       └──────────────┬────────────────┘
                                                         │ (ngrok tunnel)
                                                         ▼
                                          ┌───────────────────────────────┐
                                          │   FastAPI (localhost:8000)    │
                                          └───────────────────────────────┘
```

---

## 2. Step-by-Step Setup

### Step 1: Install ngrok
- **Windows**: `winget install ngrok.ngrok` or download from [ngrok.com](https://ngrok.com)
- **macOS**: `brew install ngrok/ngrok/ngrok`
- **Linux**: `snap install ngrok` or `apt install ngrok`

### Step 2: Authenticate (Free tier)
Sign up for a free ngrok account and run:
```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
```

### Step 3: Start the Tunnel to Port 8000
With your FastAPI backend running on port 8000, open a separate terminal window and run:
```bash
ngrok http 8000
```

ngrok will display a status screen:
```
Forwarding   https://a1b2-c3d4-e5f6.ngrok-free.app -> http://localhost:8000
```

### Step 4: Update ESP32 Firmware
Copy the `https://...ngrok-free.app` URL and update the `BACKEND_TELEMETRY_URL` constant in `wokwi/src/main.ino`:
```cpp
const char* BACKEND_TELEMETRY_URL = "https://a1b2-c3d4-e5f6.ngrok-free.app/api/telemetry";
```

### Step 5: Test the Tunnel Manually
You can verify the tunnel is active using `curl`:
```bash
curl -X POST https://a1b2-c3d4-e5f6.ngrok-free.app/api/telemetry \
  -H "Content-Type: application/json" \
  -d '{"device_id":"AQUA-01","ph":7.2,"turbidity":1.3,"ec":310.0,"temperature":27.0}'
```
Expected response:
```json
{"status":"SUCCESS","reading_id":1,"is_anomaly":false,"sensor_health":"HEALTHY"}
```

---

## 3. Important Notes & Known Friction Points

> [!WARNING]
> **Free Tier Ephemeral URL**: On ngrok's free tier, a new random forwarding URL is generated each time the `ngrok http 8000` process restarts. If you stop and restart ngrok, remember to update `BACKEND_TELEMETRY_URL` in `wokwi/src/main.ino`.
>
> **Fallback Demonstration**: If ngrok is unavailable during a live demo or offline development, you can use the FastAPI backend's built-in demo trigger endpoints (`POST /api/demo/scenario/*`) or `python scripts/demo.py` to drive all three scenarios directly without requiring a public tunnel.
