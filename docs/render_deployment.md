# Deploying AquaSentinel Backend on Render 🚀

This guide provides step-by-step instructions for deploying the **AquaSentinel** backend and web dashboard to [Render](https://render.com).

> 💡 **Major Demo Advantage**:  
> Once deployed on Render, your backend gets a permanent public HTTPS URL (e.g. `https://aquasentinel-backend.onrender.com`). You can plug this URL directly into `wokwi/src/main.ino` — **eliminating the need for ngrok tunnels during live presentations!**

---

## Deployment Options

| Method | Best For | Complexity |
| :--- | :--- | :--- |
| **Option A: Render Blueprint (`render.yaml`)** | 1-Click infrastructure deployment | 🟢 Simplest (Recommended) |
| **Option B: Manual Web Service (Python Native)** | Standard manual UI configuration | 🟡 Easy |
| **Option C: Docker Web Service** | Containerized reproducible builds | 🟡 Easy |

---

## Option A: 1-Click Blueprint Deployment (Recommended)

1. **Push your code to GitHub / GitLab**.
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New +** in the top right and select **Blueprint**.
4. Connect your `aquasentinel` repository.
5. Render will automatically detect the root [`render.yaml`](file:///c:/Users/brill/Downloads/aquasentinel/render.yaml) file:
   - Sets runtime to **Python 3.12**
   - Configures build command: `pip install --upgrade pip && pip install -r backend/requirements.txt`
   - Configures start command: `python scripts/seed_data.py && uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
   - Sets health check to `/health`
6. Click **Apply**. Render will build and deploy the web service in ~2 minutes.

---

## Option B: Manual Web Service Setup

If configuring manually from the Render web dashboard:

1. Click **New +** → **Web Service**.
2. Select your repository.
3. Configure the following fields:
   - **Name**: `aquasentinel-backend`
   - **Region**: Choose closest to you (e.g., *Oregon (US)*, *Frankfurt (EU)*, or *Singapore*)
   - **Branch**: `main`
   - **Root Directory**: *(Leave empty / root)*
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r backend/requirements.txt
     ```
   - **Start Command**:
     ```bash
     python scripts/seed_data.py && uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: `Free`

4. **Environment Variables**:
   Under the **Environment** tab, add:

   | Key | Value | Notes |
   | :--- | :--- | :--- |
   | `PYTHON_VERSION` | `3.12.2` | Forces Render to use Python 3.12 |
   | `LLM_PROVIDER` | `fallback` *(or `sarvam`)* | Use `fallback` for 100% offline rule-based reasoning |
   | `SARVAM_API_KEY` | *(your key if using Sarvam)* | Optional |
   | `SARVAM_MODEL_NAME` | `sarvam-2b` | Default model |
   | `DEFAULT_DEVICE_ID` | `AQUA-01` | Node ID |
   | `DATABASE_URL` | `sqlite:///./aquasentinel.db` | Storage path |

5. Click **Create Web Service**.

---

## Option C: Docker Deployment

If deploying with Docker on Render:

1. Click **New +** → **Web Service**.
2. Select **Docker** as runtime.
3. Render will automatically build the root [`Dockerfile`](file:///c:/Users/brill/Downloads/aquasentinel/Dockerfile).
4. Add the environment variables listed in Option B.
5. Click **Create Web Service**.

---

## 🌐 Connecting Wokwi Directly to your Render Backend

Once Render finishes deploying, copy your public service URL (e.g., `https://aquasentinel-backend.onrender.com`).

### 1. Update Wokwi Firmware
In `wokwi/src/main.ino`, update line 26:
```cpp
const char* BACKEND_TELEMETRY_URL = "https://aquasentinel-backend.onrender.com/api/telemetry";
```

### 2. Run Wokwi Simulation
Start the simulation on [wokwi.com](https://wokwi.com). The simulated ESP32 will now POST telemetry directly to your live cloud backend on Render!

### 3. Open the Cloud Dashboard
Open `https://aquasentinel-backend.onrender.com` in your browser. You will see:
- Live telemetry streaming in real time
- Trend charts updating
- Anomaly detection alerts firing when you adjust potentiometers in Wokwi
- AI chat panel ready to answer *"How is my water?"* and *"Why is this an anomaly?"*

---

## 🛠️ Verification & Troubleshooting

### Check Health Endpoint
```bash
curl https://your-service.onrender.com/health
```
**Expected Response:**
```json
{
  "status": "HEALTHY",
  "app": "AquaSentinel Backend",
  "version": "1.0.0",
  "disclaimer": "The system detects anomalous water-quality patterns and generates evidence-based early warnings. It does not claim to identify a specific contaminant without validated labeled data."
}
```

### Render Free Tier "Spin Down"
Render's free tier spins down inactive web services after 15 minutes of idle time. The first request after sleep may take ~30–50 seconds to spin up. For a live presentation, simply load `https://your-service.onrender.com` 1 minute before your presentation begins.
