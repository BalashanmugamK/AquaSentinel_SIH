"""
AquaSentinel Voice Interface - Should-Have (SRS Section 20).

Push-to-talk only: client records a short clip, uploads it here, gets an
audio reply back. No wake-word / always-listening / streaming - those are
explicitly Future Work per the SRS.

Flow:
  Microphone -> POST /voice-query (audio file)
      -> Sarvam Speech-to-Text (saaras:v3, mode=transcribe)
      -> agent /ask  (text question -> text answer)
      -> Sarvam Text-to-Speech (bulbul:v3)
      -> audio reply back to the client

Run standalone:
    uvicorn voice_service:app --port 8003 --reload
"""
import base64
import os

import requests
from fastapi import FastAPI, File, HTTPException, Response, UploadFile

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8001")
DEFAULT_NODE_ID = os.getenv("DEFAULT_NODE_ID", "node-01")

STT_URL = "https://api.sarvam.ai/speech-to-text"
TTS_URL = "https://api.sarvam.ai/text-to-speech"
TTS_LANGUAGE = os.getenv("SARVAM_TTS_LANGUAGE", "en-IN")
TTS_SPEAKER = os.getenv("SARVAM_TTS_SPEAKER", "aditya")

app = FastAPI(title="AquaSentinel Voice Interface", version="0.1.0")


def _require_key():
    if not SARVAM_API_KEY:
        raise HTTPException(status_code=500, detail="SARVAM_API_KEY is not set")


@app.post("/voice-query")
async def voice_query(audio: UploadFile = File(...), node_id: str = DEFAULT_NODE_ID):
    _require_key()

    # 1) Speech to text
    stt_resp = requests.post(
        STT_URL,
        headers={"api-subscription-key": SARVAM_API_KEY},
        files={"file": (audio.filename, await audio.read(), audio.content_type)},
        data={"model": "saaras:v3", "mode": "transcribe"},
        timeout=30,
    )
    if not stt_resp.ok:
        raise HTTPException(status_code=502, detail=f"STT failed: {stt_resp.text}")
    transcript = stt_resp.json().get("transcript", "").strip()
    if not transcript:
        raise HTTPException(status_code=422, detail="Could not transcribe any speech from the audio")

    # 2) Ask the agent
    ask_resp = requests.post(
        f"{AGENT_URL}/ask",
        json={"node_id": node_id, "question": transcript},
        timeout=30,
    )
    if not ask_resp.ok:
        raise HTTPException(status_code=502, detail=f"Agent failed: {ask_resp.text}")
    answer_text = ask_resp.json()["answer"]

    # 3) Text to speech
    tts_resp = requests.post(
        TTS_URL,
        headers={"api-subscription-key": SARVAM_API_KEY, "Content-Type": "application/json"},
        json={
            "text": answer_text,
            "target_language_code": TTS_LANGUAGE,
            "speaker": TTS_SPEAKER,
            "model": "bulbul:v3",
        },
        timeout=30,
    )
    if not tts_resp.ok:
        raise HTTPException(status_code=502, detail=f"TTS failed: {tts_resp.text}")

    audios = tts_resp.json().get("audios", [])
    if not audios:
        raise HTTPException(status_code=502, detail="TTS returned no audio")
    audio_bytes = base64.b64decode(audios[0])

    # Headers must be latin-1/ASCII-safe, and transcripts/answers may
    # contain non-Latin scripts (Hindi, Tamil, etc.) - base64-encode them
    # rather than risk an encoding error on the response.
    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={
            "X-Transcript-B64": base64.b64encode(transcript.encode("utf-8")).decode("ascii"),
            "X-Answer-Text-B64": base64.b64encode(answer_text.encode("utf-8")).decode("ascii"),
        },
    )


@app.get("/health")
def health():
    return {"status": "ok"}
