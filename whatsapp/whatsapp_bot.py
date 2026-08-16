"""
AquaSentinel WhatsApp Interface - Should-Have (SRS Section 21).

Uses the WhatsApp Cloud API (Meta). Receives inbound messages via webhook,
forwards the question to the agent's /ask endpoint, sends the reply back.

This must never block the core prototype (SRS Section 21): if this service
is down, the dashboard is still the primary interface.

Run standalone:
    uvicorn whatsapp_bot:app --port 8002 --reload

Meta setup (once you have a WhatsApp Business / Cloud API account):
1. Set the webhook URL (this service's public URL + /webhook) in the
   Meta App dashboard, with WHATSAPP_VERIFY_TOKEN as the verify token.
2. Set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID below.
"""
import os
from typing import Any, Dict

import requests
from fastapi import FastAPI, HTTPException, Query, Request

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8001")
DEFAULT_NODE_ID = os.getenv("DEFAULT_NODE_ID", "node-01")

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "changeme-verify-token")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
GRAPH_API_VERSION = os.getenv("WHATSAPP_GRAPH_API_VERSION", "v21.0")

app = FastAPI(title="AquaSentinel WhatsApp Bot", version="0.1.0")


@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
):
    """Meta calls this once, at setup time, to confirm the webhook is real."""
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_message(request: Request):
    """Handles inbound WhatsApp messages and replies with the agent's answer."""
    body = await request.json()
    message = _extract_message(body)
    if not message:
        return {"status": "ignored"}  # non-message events (delivery receipts, etc.)

    from_number, text = message
    answer = _ask_agent(text)
    _send_whatsapp_reply(from_number, answer)
    return {"status": "replied"}


def _extract_message(body: Dict[str, Any]):
    """Pulls the first text message out of a WhatsApp Cloud API webhook payload."""
    try:
        entry = body["entry"][0]["changes"][0]["value"]
        messages = entry.get("messages")
        if not messages:
            return None
        msg = messages[0]
        if msg.get("type") != "text":
            return None
        return msg["from"], msg["text"]["body"]
    except (KeyError, IndexError):
        return None


def _ask_agent(question: str) -> str:
    try:
        r = requests.post(
            f"{AGENT_URL}/ask",
            json={"node_id": DEFAULT_NODE_ID, "question": question},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["answer"]
    except requests.RequestException:
        return ("Sorry, the AquaSentinel assistant is unavailable right now. "
                "Please check the dashboard directly.")


def _send_whatsapp_reply(to: str, text: str) -> None:
    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        print(f"[dev mode - no WhatsApp credentials set] Would reply to {to}: {text}")
        return
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    try:
        requests.post(
            url,
            headers={"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": text},
            },
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"[warn] failed to send WhatsApp reply: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}
