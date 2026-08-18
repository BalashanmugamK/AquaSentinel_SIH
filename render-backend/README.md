# AquaSentinel — Standalone Render Deployment Package 🚀

This folder (`render-backend/`) is a **completely standalone, self-contained deployment package** designed to be pushed to a separate GitHub repository and deployed to [Render.com](https://render.com) with zero external dependencies.

---

## 📁 Package Contents

```
render-backend/
├── app/                        # FastAPI Application
│   ├── main.py                 # App entry point + static UI server
│   ├── config.py               # Settings & scientific disclaimer
│   ├── database.py             # SQLite persistence engine
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic v2 schemas
│   ├── services/               # Ingestion, Anomaly, Health & Events
│   ├── agent/                  # Sarvam AI + 6 Read-only tools
│   └── api/                    # REST API routes (/api/telemetry, /api/agent/ask, etc.)
├── frontend_dist/              # Pre-compiled React Dashboard (served on /)
├── scripts/
│   └── seed_data.py            # Baseline database seeder
├── .python-version             # Pins Python 3.12.2 on Render
├── requirements.txt            # Python dependencies
├── render.yaml                 # 1-Click Render Blueprint
├── Dockerfile                  # Standalone Docker container
├── start.sh                    # Startup boot script
└── README.md                   # This deployment guide
```

---

## ⚡ How to Deploy this Folder to Render (2 Minutes)

### Step 1: Create a Separate GitHub Repo
1. Create a new repository on GitHub (e.g., `aquasentinel-backend`).
2. Copy or initialize this `render-backend/` folder as the repository root:
   ```bash
   cd render-backend
   git init
   git add .
   git commit -m "Initial commit for AquaSentinel Render backend"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/aquasentinel-backend.git
   git push -u origin main
   ```

### Step 2: Deploy on Render

#### Option A: 1-Click Blueprint (Recommended)
1. In the [Render Dashboard](https://dashboard.render.com), click **New + → Blueprint**.
2. Connect your new `aquasentinel-backend` repository.
3. Render reads `render.yaml` and deploys automatically!

#### Option B: Manual Web Service
1. Click **New + → Web Service**.
2. Select your repository.
3. Set:
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     python scripts/seed_data.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
4. Click **Create Web Service**.

---

## 🌐 Connect Wokwi Directly (No ngrok needed!)

Once deployed, Render gives you a public HTTPS URL (e.g. `https://aquasentinel-backend.onrender.com`).

In your `wokwi/src/main.ino`:
```cpp
const char* BACKEND_TELEMETRY_URL = "https://aquasentinel-backend.onrender.com/api/telemetry";
```

Start the Wokwi simulation on [wokwi.com](https://wokwi.com), and the simulated ESP32 will send live telemetry straight to your cloud backend on Render!
