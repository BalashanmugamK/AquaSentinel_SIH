"""
AquaSentinel — Wokwi ESP32 Simulation Test Harness
Simulates the exact firmware behavior of wokwi/src/main.ino.
Streams JSON telemetry to FastAPI directly or via an ngrok public forwarding URL.
"""

import os
import sys
import time
import argparse
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def map_pot_to_ph(adc_val: int) -> float:
    # Linear scaling: 0 -> 0.0 pH, 4095 -> 14.0 pH
    return round((adc_val * 14.0) / 4095.0, 2)


def map_pot_to_turbidity(adc_val: int) -> float:
    # Linear scaling: 0 -> 0.0 NTU, 4095 -> 100.0 NTU
    return round((adc_val * 100.0) / 4095.0, 2)


def map_pot_to_ec(adc_val: int) -> float:
    # Linear scaling: 0 -> 0.0 uS/cm, 4095 -> 2000.0 uS/cm
    return round((adc_val * 2000.0) / 4095.0, 1)


def run_simulator(target_url: str, mode: str = "normal", count: int = 5, interval: float = 3.0):
    print(f"\n{CYAN}{BOLD}{'=' * 70}{RESET}")
    print(f"{CYAN}{BOLD} [WOKWI ESP32 NODE EMULATOR] Target: {target_url}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * 70}{RESET}\n")
    print(f"Device ID: AQUA-01 | Mode: {mode.upper()} | Packets to send: {count}\n")

    # Set potentiometer ADC values (0 - 4095)
    if mode == "normal":
        pot_ph_adc = 2100       # ~7.18 pH
        pot_turb_adc = 50       # ~1.22 NTU
        pot_ec_adc = 635        # ~310.1 uS/cm
        temp_c = 27.0
    elif mode == "disturbance":
        pot_ph_adc = 2150       # ~7.35 pH
        pot_turb_adc = 1024     # ~25.00 NTU (Spike)
        pot_ec_adc = 1884       # ~920.1 uS/cm (Spike)
        temp_c = 27.4
    elif mode == "sensor_fault":
        pot_ph_adc = 600        # ~2.05 pH (Severe outlier)
        pot_turb_adc = 50       # ~1.22 NTU (Normal)
        pot_ec_adc = 635        # ~310.1 uS/cm (Normal)
        temp_c = 26.9
    else:
        raise ValueError(f"Unknown mode: {mode}")

    client = httpx.Client(timeout=10.0)

    for i in range(1, count + 1):
        ph = map_pot_to_ph(pot_ph_adc)
        turb = map_pot_to_turbidity(pot_turb_adc)
        ec = map_pot_to_ec(pot_ec_adc)

        payload = {
            "device_id": "AQUA-01",
            "ph": ph,
            "turbidity": turb,
            "ec": ec,
            "temperature": temp_c
        }

        print(f"[{i}/{count}] [SENSE] Analog Pins: pH={pot_ph_adc} (-> {ph}), Turb={pot_turb_adc} (-> {turb} NTU), EC={pot_ec_adc} (-> {ec} uS/cm), Temp={temp_c} C")

        try:
            start_t = time.time()
            res = client.post(target_url, json=payload)
            elapsed_ms = round((time.time() - start_t) * 1000, 1)

            if res.status_code in [200, 201]:
                data = res.json()
                is_anom = data.get("is_anomaly", False)
                score = data.get("anomaly_score", 0.0)
                health = data.get("sensor_health", "HEALTHY")
                color = RED if is_anom else (YELLOW if health != "HEALTHY" else GREEN)
                
                print(f"       -> [HTTPS POST {res.status_code} in {elapsed_ms}ms] Anomaly: {color}{is_anom} (Score: {score}){RESET} | Health: {color}{health}{RESET}")
            else:
                print(f"       -> [HTTP {res.status_code}] {res.text}")
        except Exception as e:
            print(f"       -> [ERROR] Failed to send packet to {target_url}: {e}")

        if i < count:
            time.sleep(interval)

    client.close()
    print(f"\n{GREEN}[DONE] Simulation batch completed.{RESET}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate Wokwi ESP32 telemetry transmission")
    parser.add_argument("--url", default="http://localhost:8000/api/telemetry", help="Target API URL (or ngrok forwarding URL)")
    parser.add_argument("--mode", default="normal", choices=["normal", "disturbance", "sensor_fault"], help="Telemetry pattern mode")
    parser.add_argument("--count", type=int, default=3, help="Number of packets to send")
    parser.add_argument("--interval", type=float, default=2.0, help="Delay in seconds between packets")

    args = parser.parse_args()
    run_simulator(target_url=args.url, mode=args.mode, count=args.count, interval=args.interval)
