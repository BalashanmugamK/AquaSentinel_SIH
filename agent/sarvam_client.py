"""
Minimal Sarvam AI chat-completions client.

Sarvam's /v1/chat/completions endpoint is OpenAI-compatible, including
native tool calling (see https://docs.sarvam.ai). We call it directly with
`requests` rather than pulling in the full SDK, to keep the prototype's
dependency footprint small - swap this for `sarvamai` the official SDK
later if useful.
"""
import os
from typing import Any, Dict, List, Optional

import requests

SARVAM_API_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_MODEL = os.getenv("SARVAM_MODEL", "sarvam-105b")


class SarvamError(RuntimeError):
    pass


def chat_completion(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    temperature: float = 0.2,
    max_tokens: int = 1000,
) -> Dict[str, Any]:
    """Calls Sarvam's chat completions endpoint and returns the raw
    response['choices'][0]['message'] dict (OpenAI-shaped: may contain
    `content` and/or `tool_calls`)."""
    if not SARVAM_API_KEY:
        raise SarvamError("SARVAM_API_KEY is not set")

    payload: Dict[str, Any] = {
        "model": SARVAM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice

    resp = requests.post(
        SARVAM_API_URL,
        headers={
            "Authorization": f"Bearer {SARVAM_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    if resp.status_code != 200:
        raise SarvamError(f"Sarvam API error {resp.status_code}: {resp.text}")

    data = resp.json()
    return data["choices"][0]["message"]
