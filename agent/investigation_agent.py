"""
AquaSentinel Investigation Agent - Workstream D.

Exposes POST /investigate {"event_id": "..."}. n8n calls this after an
anomaly event is created; this service runs a Sarvam-powered tool-calling
loop against the backend's four agent tools (SRS Section 14), then returns
a structured result. n8n is responsible for PATCHing the result back onto
the event (SRS Section 13: "Store Investigation Result"), matching the WBS
split of responsibilities between D (agent) and B (backend write-back).

Run standalone for local testing:
    uvicorn investigation_agent:app --port 8001 --reload
"""
import json
import os
from typing import Any, Dict, List

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sarvam_client import SarvamError, chat_completion

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BACKEND_API_KEY = os.getenv("AQUASENTINEL_API_KEY", "changeme-dev-key")

app = FastAPI(title="AquaSentinel Investigation Agent", version="0.1.0")


# ---------- Tool schema (OpenAI/Sarvam tool-calling format) ----------
# Each tool name maps 1:1 to a GET route in backend/app/routers/tools.py

TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_readings",
            "description": "Get the most recent sensor reading (pH, TDS, turbidity, temperature) for a node.",
            "parameters": {
                "type": "object",
                "properties": {"node_id": {"type": "string"}},
                "required": ["node_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_historical_readings",
            "description": "Get recent historical readings and the current baseline (mean/std per parameter) for a node.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {"type": "string"},
                    "limit": {"type": "integer", "description": "how many recent readings to fetch"},
                },
                "required": ["node_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_anomaly_event",
            "description": "Get full details of a specific anomaly event by ID, including which parameters triggered it.",
            "parameters": {
                "type": "object",
                "properties": {"event_id": {"type": "string"}},
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sensor_status",
            "description": "Check whether the node's sensors are reporting plausible, fresh data (basic sensor-fault check).",
            "parameters": {
                "type": "object",
                "properties": {"node_id": {"type": "string"}},
                "required": ["node_id"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are the AquaSentinel water-quality investigation agent.

You are given a detected anomaly event. Use the available tools to gather
evidence, then produce a concise, evidence-based assessment.

Rules (do not break these):
- Never claim laboratory-certain contamination (e.g. "the water is contaminated
  with X"). Only claim an anomalous pattern was detected, e.g. "an anomalous
  water-quality pattern was detected" or "a potential water-quality disturbance".
- Always cite specific evidence: parameter deltas vs. baseline, magnitude of
  deviation, and whether the sensors themselves look healthy.
- Always end with a concrete, practical recommendation for a human operator
  (e.g. inspect the sample, collect a physical sample for lab confirmation,
  check sensor calibration).
- Keep the explanation short: 3-6 sentences plus one recommendation line.

When you are done gathering evidence, respond with a final JSON object
(no other text) with exactly these keys:
{
  "investigation_result": "<evidence-based explanation>",
  "recommendation": "<concrete next step>",
  "confidence": <float between 0 and 1>
}
"""


def _call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    headers = {"X-API-Key": BACKEND_API_KEY}
    try:
        if name == "get_current_readings":
            r = requests.get(f"{BACKEND_URL}/api/tools/current_readings",
                              params={"node_id": args["node_id"]}, headers=headers, timeout=10)
        elif name == "get_historical_readings":
            params = {"node_id": args["node_id"]}
            if "limit" in args:
                params["limit"] = args["limit"]
            r = requests.get(f"{BACKEND_URL}/api/tools/historical_readings",
                              params=params, headers=headers, timeout=10)
        elif name == "get_anomaly_event":
            r = requests.get(f"{BACKEND_URL}/api/tools/anomaly_event/{args['event_id']}",
                              headers=headers, timeout=10)
        elif name == "get_sensor_status":
            r = requests.get(f"{BACKEND_URL}/api/tools/sensor_status",
                              params={"node_id": args["node_id"]}, headers=headers, timeout=10)
        else:
            return {"error": f"unknown tool '{name}'"}
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        return {"error": str(e), "status_code": e.response.status_code if e.response else None}
    except requests.RequestException as e:
        return {"error": str(e)}


class InvestigateRequest(BaseModel):
    event_id: str


class InvestigateResponse(BaseModel):
    event_id: str
    investigation_result: str
    recommendation: str
    confidence: float


@app.post("/investigate", response_model=InvestigateResponse)
def investigate(req: InvestigateRequest):
    event = _call_tool("get_anomaly_event", {"event_id": req.event_id})
    if "error" in event:
        raise HTTPException(status_code=404, detail=f"Could not load event: {event['error']}")

    node_id = event.get("node_id", "node-01")

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Investigate anomaly event {req.event_id} on node {node_id}. "
                f"Event summary: {json.dumps(event)}"
            ),
        },
    ]

    # Tool-calling loop (max 6 rounds - plenty for 4 tools + final answer)
    for _ in range(6):
        try:
            message = chat_completion(messages, tools=TOOLS, tool_choice="auto")
        except SarvamError as e:
            raise HTTPException(status_code=502, detail=str(e))

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            content = (message.get("content") or "").strip()
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Model didn't return clean JSON - wrap what it said instead
                # of failing the whole investigation.
                result = {
                    "investigation_result": content or "Investigation completed but no structured result was returned.",
                    "recommendation": "Inspect the sample manually and verify sensor calibration.",
                    "confidence": 0.4,
                }
            return InvestigateResponse(
                event_id=req.event_id,
                investigation_result=result.get("investigation_result", ""),
                recommendation=result.get("recommendation", ""),
                confidence=float(result.get("confidence", 0.5)),
            )

        # Model wants to call tools - append its message, run each tool,
        # append tool results, then loop back for the next model turn.
        messages.append(message)
        for call in tool_calls:
            fn_name = call["function"]["name"]
            try:
                fn_args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                fn_args = {}
            fn_args.setdefault("node_id", node_id)
            tool_result = _call_tool(fn_name, fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": json.dumps(tool_result),
            })

    raise HTTPException(status_code=504, detail="Agent did not converge within the tool-call budget")


QA_SYSTEM_PROMPT = """You are the AquaSentinel assistant. A user is asking a
question about their water-quality monitoring node - e.g. "why is my water
abnormal?" or "is everything okay?".

Use the available tools to check current readings, recent history, and any
active anomaly before answering. Answer in plain, non-technical language,
in 2-4 sentences.

Rules (do not break these):
- Never claim laboratory-certain contamination. Only describe detected
  anomalous patterns, e.g. "an anomalous pattern was detected" or
  "readings look normal right now".
- If there is no active anomaly, say so plainly and briefly - don't invent one.
- If there is an active anomaly, summarize what changed and the current
  recommendation.
- Respond with plain text only (no JSON, no markdown), since this may be
  read aloud or sent as a WhatsApp message.
"""


class AskRequest(BaseModel):
    node_id: str = "node-01"
    question: str


class AskResponse(BaseModel):
    node_id: str
    question: str
    answer: str


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """
    Ad-hoc Q&A entry point for the Should-Have WhatsApp / voice interfaces
    (SRS Sections 20-21). Same tool-calling loop as /investigate, but
    driven by a free-text user question instead of a fixed event_id, and
    returns plain text instead of a structured investigation result.
    """
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": QA_SYSTEM_PROMPT},
        {"role": "user", "content": f"[node_id={req.node_id}] {req.question}"},
    ]

    for _ in range(6):
        try:
            message = chat_completion(messages, tools=TOOLS, tool_choice="auto", max_tokens=400)
        except SarvamError as e:
            raise HTTPException(status_code=502, detail=str(e))

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            answer = (message.get("content") or "").strip()
            if not answer:
                answer = "I couldn't find an answer right now - please check the dashboard."
            return AskResponse(node_id=req.node_id, question=req.question, answer=answer)

        messages.append(message)
        for call in tool_calls:
            fn_name = call["function"]["name"]
            try:
                fn_args = json.loads(call["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                fn_args = {}
            fn_args.setdefault("node_id", req.node_id)
            # get_anomaly_event needs an event_id, not a node_id - if the
            # model calls it without one, look up the latest event instead.
            if fn_name == "get_anomaly_event" and "event_id" not in fn_args:
                latest = requests.get(
                    f"{BACKEND_URL}/api/events",
                    params={"node_id": req.node_id, "limit": 1},
                    headers={"X-API-Key": BACKEND_API_KEY}, timeout=10,
                )
                events = latest.json() if latest.ok else []
                tool_result = events[0] if events else {"error": "no events found for this node"}
            else:
                tool_result = _call_tool(fn_name, fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": json.dumps(tool_result),
            })

    raise HTTPException(status_code=504, detail="Agent did not converge within the tool-call budget")


@app.get("/health")
def health():
    return {"status": "ok"}
