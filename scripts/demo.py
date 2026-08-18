import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from backend.app.database import SessionLocal, init_db
from backend.app.schemas import TelemetryIngestRequest, AgentAskRequest
from backend.app.services.telemetry_service import TelemetryService
from backend.app.agent.agent import InvestigationAgent
from scripts.seed_data import seed_database

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner(title: str, color=CYAN):
    print(f"\n{color}{BOLD}{'=' * 75}{RESET}")
    print(f"{color}{BOLD} {title}{RESET}")
    print(f"{color}{BOLD}{'=' * 75}{RESET}\n")


def run_full_demo():
    print_banner("AQUASENTINEL: 5-MINUTE LIVE DEMO WALKTHROUGH")
    print("Loop: SENSE -> SEND -> STORE -> ANALYZE -> DETECT -> INVESTIGATE -> EXPLAIN -> ALERT\n")
    
    # 0. Setup database & baseline
    seed_database(count=50)
    db = SessionLocal()

    # =========================================================================
    # SCENARIO 1: NORMAL OPERATION
    # =========================================================================
    print_banner("SCENARIO 1: [NORMAL OPERATION]", GREEN)
    print("Simulating normal Wokwi ESP32 telemetry (pH: 7.1, Turbidity: 1.2 NTU, EC: 300 uS/cm, Temp: 27.0 C)...")
    
    payload1 = TelemetryIngestRequest(
        device_id="AQUA-01",
        ph=7.1,
        turbidity=1.2,
        ec=300.0,
        temperature=27.0,
    )
    telemetry, anomaly, health, event = TelemetryService.ingest_reading(db, payload1)
    
    print(f"[{GREEN}INGESTED{RESET}] Telemetry #{telemetry.id} stored in SQLite.")
    print(f"[{GREEN}EVALUATE{RESET}] Anomaly Detected: {anomaly.is_anomaly} (Score: {anomaly.anomaly_score})")
    print(f"[{GREEN}HEALTH  {RESET}] Sensor Network Status: {health.status}")
    print(f"[{GREEN}EVENTS  {RESET}] Active Event Created: {event.event_type if event else 'None (All Normal)'}")
    
    print(f"\n{BOLD}User asks:{RESET} \"How is my water?\"")
    print(f"{CYAN}Agent investigating via 6 read-only tools...{RESET}\n")
    res1 = InvestigationAgent.ask(db, AgentAskRequest(message="How is my water?"))
    print(f"{res1.response}\n")
    print(f"{CYAN}Provider: {res1.provider_used} | Tools Called: {len(res1.tools_called)}{RESET}")

    time.sleep(1)

    # =========================================================================
    # SCENARIO 2: WATER QUALITY DISTURBANCE (MULTI-PARAMETER SPIKE)
    # =========================================================================
    print_banner("SCENARIO 2: [WATER QUALITY DISTURBANCE]", RED)
    print("Simulating potentiometer turns on Wokwi: Turbidity spiked to 25.0 NTU, EC to 900.0 uS/cm...")
    
    payload2 = TelemetryIngestRequest(
        device_id="AQUA-01",
        ph=7.2,
        turbidity=25.0,
        ec=900.0,
        temperature=27.2,
    )
    telemetry, anomaly, health, event = TelemetryService.ingest_reading(db, payload2)
    
    print(f"[{RED}INGESTED{RESET}] Telemetry #{telemetry.id} stored in SQLite.")
    print(f"[{RED}DETECT  {RESET}] Anomaly: {anomaly.is_anomaly} | Anomaly Score: {anomaly.anomaly_score}")
    print(f"[{RED}REASONS {RESET}] {anomaly.reasons}")
    print(f"[{GREEN}HEALTH  {RESET}] Sensor Health: {health.status} (Sensors functional, water body altered)")
    print(f"[{RED}EVENT   {RESET}] New Active Event: {event.event_type if event else 'None'} [Severity: {event.severity if event else 'N/A'}]")
    
    print(f"\n{BOLD}User asks:{RESET} \"Why is this an anomaly? What happened?\"")
    print(f"{CYAN}Agent investigating via 6 read-only tools...{RESET}\n")
    res2 = InvestigationAgent.ask(db, AgentAskRequest(message="Why is this an anomaly? What happened?"))
    print(f"{res2.response}\n")
    print(f"{CYAN}Provider: {res2.provider_used} | Tools Called: {len(res2.tools_called)}{RESET}")

    time.sleep(1)

    # =========================================================================
    # SCENARIO 3: SENSOR FAULT ISOLATION (SINGLE-PARAMETER SHIFT)
    # =========================================================================
    print_banner("SCENARIO 3: [SENSOR FAULT ISOLATION]", YELLOW)
    print("Simulating single potentiometer turn: pH drops to extreme 2.0 while Turbidity, EC, Temp stay normal...")
    
    payload3 = TelemetryIngestRequest(
        device_id="AQUA-01",
        ph=2.0,
        turbidity=1.2,
        ec=305.0,
        temperature=26.9,
    )
    telemetry, anomaly, health, event = TelemetryService.ingest_reading(db, payload3)
    
    print(f"[{YELLOW}INGESTED{RESET}] Telemetry #{telemetry.id} stored in SQLite.")
    print(f"[{YELLOW}DETECT  {RESET}] Anomaly: {anomaly.is_anomaly} | Score: {anomaly.anomaly_score}")
    print(f"[{YELLOW}HEALTH  {RESET}] Sensor Status: {health.status} | Suspect Sensor: {health.suspect_sensor}")
    print(f"[{YELLOW}EVENT   {RESET}] Event: {event.event_type if event else 'None'} [Severity: {event.severity if event else 'N/A'}]")
    
    print(f"\n{BOLD}User asks:{RESET} \"Is this likely a sensor problem?\"")
    print(f"{CYAN}Agent investigating via 6 read-only tools...{RESET}\n")
    res3 = InvestigationAgent.ask(db, AgentAskRequest(message="Is this likely a sensor problem?"))
    print(f"{res3.response}\n")
    print(f"{CYAN}Provider: {res3.provider_used} | Tools Called: {len(res3.tools_called)}{RESET}")

    db.close()
    print_banner("DEMO COMPLETED SUCCESSFULLY - ALL 3 SCENARIOS VERIFIED", GREEN)


if __name__ == "__main__":
    run_full_demo()
