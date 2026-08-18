# AquaSentinel — 5-Minute Live Presentation & Demo Guide

This script walks through the live demonstration of AquaSentinel in under 5 minutes.

---

## Preparation (2 minutes before presentation)

1. Start the FastAPI backend:
   ```bash
   uvicorn backend.app.main:app --port 8000 --reload
   ```
2. Open the web dashboard:
   Navigate to `http://localhost:8000` (or `http://localhost:3000` if running Vite).
3. Start ngrok (if using Wokwi simulation):
   ```bash
   ngrok http 8000
   ```
   Paste the forwarding URL into `wokwi/src/main.ino` and start the Wokwi simulation.
   *(Alternatively, use the dashboard's Fast Demo Controls or `python scripts/demo.py` for a 100% reliable local demo).*

---

## Step 1: Normal Water Baseline (🟢 NORMAL)

- **Action**:
  - In Wokwi: Keep Potentiometer 1 (pH) at middle (~514 / ~7.2 pH), Potentiometer 2 (Turbidity) low (~50 / ~1.2 NTU), Potentiometer 3 (EC) low (~614 / ~300 µS/cm).
  - *Or click*: `Scenario 1: Normal` on the dashboard.
- **Visuals on Dashboard**:
  - Top Status Banner turns 🟢 **NORMAL (NOMINAL)** with anomaly score ~0.05.
  - Telemetry cards show pH 7.2, Turbidity 1.2 NTU, EC 310 µS/cm, Temp 27.0 °C.
  - Trend chart shows flat, stable historical lines.
- **Ask the Agent**:
  Click prompt: *"How is my water?"*
- **Agent's Grounded Output**:
  > Cites exact current values (pH 7.2, Turbidity 1.2 NTU, EC 310 µS/cm) from tool calls.
  > Confirms all 4 channels are within the learned nominal baseline.
  > Includes the scientific disclaimer.

---

## Step 2: Environmental Disturbance (🔴 ANOMALY)

- **Action**:
  - In Wokwi: Turn Potentiometer 2 (Turbidity) up to ~1000 (~25.0 NTU) and Potentiometer 3 (EC) up to ~1800 (~900 µS/cm).
  - *Or click*: `Scenario 2: Disturbance` on the dashboard.
- **Visuals on Dashboard**:
  - Top Status Banner immediately flips to 🔴 **WATER QUALITY ANOMALY DETECTED (Score: 0.87)**.
  - Evidence list pops up:
    - *Turbidity (25.0 NTU) breached environmental threshold (> 15.0 NTU)*
    - *EC (900.0 µS/cm) breached safe conductivity limit (> 800.0 µS/cm)*
  - Active Alert appears in Event Log: `WATER_QUALITY_ANOMALY` [HIGH].
  - Sensor Health badge stays `HEALTHY` (verifying sensors are operational, the water body is what changed).
- **Ask the Agent**:
  Click prompt: *"Why is this an anomaly? What happened?"*
- **Agent's Grounded Output**:
  > Explains that Turbidity and EC rose in synchronization relative to the learned baseline.
  > Recommends dispatching field operators for certified grab samples.
  > Emphasizes early warning without claiming specific unverified contaminants.

---

## Step 3: Sensor Fault Isolation (🟡 SENSOR FAULT)

- **Action**:
  - In Wokwi: Turn only Potentiometer 1 (pH) all the way down to ~50 (~2.0 pH) while leaving Turbidity (1.2 NTU) and EC (315 µS/cm) at normal values.
  - *Or click*: `Scenario 3: Sensor Fault` on the dashboard.
- **Visuals on Dashboard**:
  - Top Status Banner changes to 🟡 **SENSOR FAULT SUSPECTED (ISOLATED PROBE DRIFT)**.
  - Suspect Sensor badge highlights `pH`.
  - Event Log creates `SENSOR_FAULT_SUSPECTED`.
- **Ask the Agent**:
  Click prompt: *"Is this likely a sensor problem?"*
- **Agent's Grounded Output**:
  > Identifies that only the pH channel recorded an extreme deviation while all other 3 water parameters remained stable.
  > Explains that physical water pollution alters multiple parameters simultaneously.
  > Confirms the pattern is consistent with probe failure or drift rather than water contamination.

---

## Step 4: Standalone Automated CLI Demo

For presentation backup or CI validation, run:
```bash
python scripts/demo.py
```
This executes the full 3-scenario loop with formatted terminal output and tool inspections in under 30 seconds.
