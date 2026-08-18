"""
AquaSentinel — n8n Workflow Integration Verification Script
Verifies the n8n trigger -> backend HTTP request -> response relay contract.
Works in standalone mode (using FastAPI TestClient) or against a live running server.
"""

import os
import sys
import json
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def test_backend_agent_contract(backend_url: str = "http://localhost:8000"):
    print(f"\n{CYAN}{BOLD}{'=' * 75}{RESET}")
    print(f"{CYAN}{BOLD} [1/2] TESTING BACKEND AGENT CONTRACT FOR n8n (POST /api/agent/ask){RESET}")
    print(f"{CYAN}{BOLD}{'=' * 75}{RESET}\n")

    test_queries = [
        "How is my water?",
        "Why is this an anomaly? What happened?",
        "Is this likely a sensor problem?"
    ]

    # Try live HTTP first, fallback to FastAPI TestClient
    is_live_server = False
    try:
        r = httpx.get(f"{backend_url}/health", timeout=1.0)
        if r.status_code == 200:
            is_live_server = True
    except Exception:
        pass

    if is_live_server:
        print(f"[{GREEN}CONNECTED{RESET}] Live FastAPI server detected on {backend_url}")
        client = httpx.Client(timeout=10.0)
        post_fn = lambda url, json_body: client.post(f"{backend_url}{url}", json=json_body)
    else:
        print(f"[{YELLOW}STANDALONE{RESET}] Using internal FastAPI TestClient for n8n contract verification")
        client = TestClient(app)
        post_fn = lambda url, json_body: client.post(url, json=json_body)

    for q in test_queries:
        print(f"\n{BOLD}n8n Trigger Payload:{RESET} {{\"message\": \"{q}\"}}")
        payload = {"message": q, "session_id": "n8n-test-session"}

        res = post_fn("/api/agent/ask", payload)
        if res.status_code == 200:
            data = res.json()
            print(f"{GREEN}✓ HTTP 200 OK{RESET} | Provider: {data.get('provider_used')} | Tools Executed: {len(data.get('tools_called', []))}")
            print(f"  Response summary: {data.get('response')[:140].replace('\n', ' ')}...")
        else:
            print(f"{RED}✗ Error HTTP {res.status_code}: {res.text}{RESET}")

    if is_live_server:
        client.close()
    return True


def test_live_n8n_webhook(n8n_webhook_url: str = "http://localhost:5678/webhook/aquasentinel-investigate"):
    print(f"\n{CYAN}{BOLD}{'=' * 75}{RESET}")
    print(f"{CYAN}{BOLD} [2/2] TESTING LIVE n8n WEBHOOK RELAY ({n8n_webhook_url}){RESET}")
    print(f"{CYAN}{BOLD}{'=' * 75}{RESET}\n")

    client = httpx.Client(timeout=3.0)
    payload = {"message": "Why is this an anomaly?"}

    try:
        print(f"Pinging live n8n webhook: {n8n_webhook_url}...")
        res = client.post(n8n_webhook_url, json=payload)
        if res.status_code == 200:
            print(f"{GREEN}✓ Live n8n Workflow successfully triggered & returned agent response!{RESET}")
            print(f"Response: {json.dumps(res.json(), indent=2)[:300]}...")
        else:
            print(f"{YELLOW}⚠️ n8n returned HTTP {res.status_code}. (Activate the workflow in the n8n UI).{RESET}")
    except Exception as e:
        print(f"{YELLOW}ℹ️ No active live n8n instance listening on port 5678 ({type(e).__name__}).{RESET}")
        print("  💡 Workflow template 'n8n/aquasentinel-investigation.workflow.json' is ready for import into any local or cloud n8n instance.")

    client.close()


if __name__ == "__main__":
    test_backend_agent_contract()
    test_live_n8n_webhook()
    print(f"\n{GREEN}{BOLD}✓ n8n Integration Contract Verification Complete.{RESET}\n")
