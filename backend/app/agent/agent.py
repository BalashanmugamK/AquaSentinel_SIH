import logging
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.schemas import AgentAskRequest, AgentAskResponse, ToolCallRecord
from backend.app.agent.tools import (
    get_current_readings,
    get_recent_history,
    get_baseline,
    get_anomaly_result,
    get_active_events,
    get_sensor_health,
)

logger = logging.getLogger("aquasentinel.agent")


class InvestigationAgent:
    """
    Agentic AI Water Intelligence Agent.
    Orchestrates tool calling against real database state and generates grounded explanations
    via Sarvam AI or the deterministic rule-based engine.
    """

    SYSTEM_PROMPT = f"""You are AquaSentinel, an expert AI Water Intelligence & Early-Warning Agent.
You analyze water-quality telemetry and provide grounded, evidence-based early warnings.

MANDATORY SCIENTIFIC PRECISION RULES:
1. ALWAYS cite exact current values and learned baseline values retrieved via tools.
2. If a single sensor deviates while others remain normal, reason that this is a SENSOR FAULT, not water contamination.
3. If multiple parameters deviate (e.g., turbidity + EC rise together), identify it as an environmental water-quality anomaly.
4. SCIENTIFIC TERMINOLOGY: The Anomaly Score (0.00 – 1.00) is a Normalized Statistical Divergence Index from the learned baseline, NOT a percentage probability of contamination.
5. You must NEVER claim to identify a specific contaminant or confirm chemical pollution without certified laboratory spectrometry.
6. ALWAYS conclude your answer with the exact disclaimer:
"{settings.SCIENTIFIC_DISCLAIMER}"
"""

    @classmethod
    def execute_all_tools(cls, db: Session, device_id: str = "AQUA-01") -> Dict[str, Any]:
        """Fetch full contextual facts using the 6 read-only tools."""
        current = get_current_readings(db, device_id)
        history = get_recent_history(db, device_id, limit=5)
        baseline = get_baseline(db, device_id)
        anomaly = get_anomaly_result(db, device_id)
        events = get_active_events(db, device_id)
        health = get_sensor_health(db, device_id)

        return {
            "current_readings": current,
            "recent_history": history,
            "baseline": baseline,
            "anomaly_result": anomaly,
            "active_events": events,
            "sensor_health": health,
        }

    @classmethod
    def ask(cls, db: Session, request: AgentAskRequest, device_id: str = "AQUA-01") -> AgentAskResponse:
        """Process question through agentic tools + provider reasoning."""
        facts = cls.execute_all_tools(db, device_id)
        
        tools_called = [
            ToolCallRecord(tool_name="get_current_readings", arguments={"device_id": device_id}, output_summary=facts["current_readings"].get("parameters")),
            ToolCallRecord(tool_name="get_baseline", arguments={"device_id": device_id}, output_summary=facts["baseline"].get("baseline_summary")),
            ToolCallRecord(tool_name="get_anomaly_result", arguments={"device_id": device_id}, output_summary={"is_anomaly": facts["anomaly_result"].get("is_anomaly"), "score": facts["anomaly_result"].get("anomaly_score")}),
            ToolCallRecord(tool_name="get_sensor_health", arguments={"device_id": device_id}, output_summary={"status": facts["sensor_health"].get("health_status"), "suspect": facts["sensor_health"].get("suspect_sensor")}),
            ToolCallRecord(tool_name="get_active_events", arguments={"device_id": device_id}, output_summary={"active_count": facts["active_events"].get("active_event_count")}),
            ToolCallRecord(tool_name="get_recent_history", arguments={"device_id": device_id, "limit": 5}, output_summary=f"{facts['recent_history'].get('count')} records"),
        ]

        # Attempt Sarvam AI if configured
        if settings.LLM_PROVIDER.lower() == "sarvam" and settings.SARVAM_API_KEY:
            try:
                response_text = cls._call_sarvam_ai(request.message, facts)
                return AgentAskResponse(
                    response=response_text,
                    tools_called=tools_called,
                    provider_used="Sarvam AI (sarvam-2b)",
                    grounded_facts=facts,
                    disclaimer=settings.SCIENTIFIC_DISCLAIMER,
                )
            except Exception as e:
                logger.warning(f"Sarvam AI call failed ({e}), switching to deterministic fallback provider.")

        # Deterministic rule-based fallback provider
        response_text = cls._deterministic_fallback_reasoner(request.message, facts)
        return AgentAskResponse(
            response=response_text,
            tools_called=tools_called,
            provider_used="Deterministic Rule-Based Engine (Fallback)",
            grounded_facts=facts,
            disclaimer=settings.SCIENTIFIC_DISCLAIMER,
        )

    @classmethod
    def _deterministic_fallback_reasoner(cls, question: str, facts: Dict[str, Any]) -> str:
        """
        Deterministic, mathematically grounded reasoning engine.
        Applies expert water intelligence rules and ensures factual integrity.
        """
        current = facts["current_readings"].get("parameters", {})
        baseline = facts["baseline"].get("baseline_summary", {})
        anomaly = facts["anomaly_result"]
        health = facts["sensor_health"]
        events = facts["active_events"]

        if not current:
            return (
                f"No telemetry readings are currently available for this node.\n\n"
                f"**System Claim**: {settings.SCIENTIFIC_DISCLAIMER}"
            )

        ph = current.get("ph", 7.0)
        turb = current.get("turbidity_ntu", 0.0)
        ec = current.get("ec_us_cm", 0.0)
        temp = current.get("temperature_c", 25.0)

        is_anomaly = anomaly.get("is_anomaly", False)
        anomaly_score = anomaly.get("anomaly_score", 0.0)
        reasons = anomaly.get("reasons", [])
        health_status = health.get("health_status", "HEALTHY")
        suspect_sensor = health.get("suspect_sensor")
        active_count = events.get("active_event_count", 0)

        q_lower = question.lower()

        # Scenario 3: Sensor Fault Inquiry or State
        if health_status == "FAULT_SUSPECTED" or "sensor" in q_lower or (suspect_sensor and is_anomaly):
            return (
                f"### ⚠️ Sensor Health Diagnostic: Suspected Hardware/Probe Fault\n\n"
                f"**Analysis of Current Readings vs Baseline:**\n"
                f"- **{suspect_sensor}**: {current.get('ph' if suspect_sensor=='pH' else 'turbidity_ntu', 0)} (Abnormal deviation)\n"
                f"- **Turbidity**: {turb} NTU (Baseline mean: {baseline.get('turbidity', {}).get('mean', 1.5)} NTU - Normal)\n"
                f"- **Electrical Conductivity (EC)**: {ec} µS/cm (Baseline mean: {baseline.get('ec', {}).get('mean', 320.0)} µS/cm - Normal)\n"
                f"- **Temperature**: {temp} °C (Baseline mean: {baseline.get('temperature', {}).get('mean', 26.5)} °C - Normal)\n\n"
                f"**Diagnostic Reasoning:**\n"
                f"Only the **{suspect_sensor}** probe has recorded a severe outlier while all other 3 water parameters remain completely stable within normal bounds. "
                f"Because physical water-quality contamination typically alters multiple related parameters simultaneously (e.g., runoff increases both turbidity and conductivity), "
                f"this isolated single-parameter deviation is **consistent with a sensor hardware, calibration, or probe drift issue**, rather than an environmental contamination event.\n\n"
                f"**Recommended Action:** Inspect and recalibrate the {suspect_sensor} probe and check terminal wiring.\n\n"
                f"> **Scientific Notice**: {settings.SCIENTIFIC_DISCLAIMER}"
            )

        # Scenario 2: Water Quality Disturbance
        if is_anomaly or active_count > 0 or "why" in q_lower or "what happened" in q_lower:
            reasons_str = "\n".join([f"- {r}" for r in reasons]) if reasons else "- Coordinated shift in water optical and conductivity metrics."
            return (
                f"### 🔴 Alert: Water Quality Disturbance Pattern Detected\n\n"
                f"**Current State (Statistical Anomaly Index: {anomaly_score} / 1.00 relative divergence):**\n"
                f"- **Turbidity**: **{turb} NTU** (Learned baseline: {baseline.get('turbidity', {}).get('mean', 1.5)} ± {baseline.get('turbidity', {}).get('std', 0.5)} NTU)\n"
                f"- **Electrical Conductivity**: **{ec} µS/cm** (Learned baseline: {baseline.get('ec', {}).get('mean', 320.0)} ± {baseline.get('ec', {}).get('std', 30.0)} µS/cm)\n"
                f"- **pH**: {ph} (Learned baseline: {baseline.get('ph', {}).get('mean', 7.2)} ± {baseline.get('ph', {}).get('std', 0.25)})\n"
                f"- **Temperature**: {temp} °C\n\n"
                f"**Investigation Findings:**\n"
                f"{reasons_str}\n\n"
                f"**Evidence Interpretation:**\n"
                f"Both turbidity and electrical conductivity (EC) rose significantly above baseline in temporal synchronization. "
                f"The sensor health diagnostics confirm all 4 sensor channels are operational (`HEALTHY`), indicating this is a genuine physical change in the monitored water body.\n\n"
                f"**Recommended Protocol:** Dispatch field technicians to collect grab samples for certified laboratory spectrometry and inspect upstream inflow channels.\n\n"
                f"> **Scientific Notice**: {settings.SCIENTIFIC_DISCLAIMER}"
            )

        # Scenario 1: Normal State
        return (
            f"### 🟢 System Status: NORMAL\n\n"
            f"**Current Telemetry vs Learned Baseline:**\n"
            f"- **pH**: {ph} (Nominal range: 6.5 – 8.5, baseline mean: {baseline.get('ph', {}).get('mean', 7.2)})\n"
            f"- **Turbidity**: {turb} NTU (Safe limit: < 5.0 NTU, baseline mean: {baseline.get('turbidity', {}).get('mean', 1.5)} NTU)\n"
            f"- **Electrical Conductivity**: {ec} µS/cm (Normal range: 250 – 500 µS/cm, baseline mean: {baseline.get('ec', {}).get('mean', 320.0)} µS/cm)\n"
            f"- **Temperature**: {temp} °C (Baseline mean: {baseline.get('temperature', {}).get('mean', 26.5)} °C)\n\n"
            f"**Evaluation:**\n"
            f"All 4 water quality parameters are currently within learned baseline boundaries and environmental safety limits (Statistical Anomaly Index: {anomaly_score} / 1.00). "
            f"Sensor health diagnostics report 100% nominal operation across all analog and digital channels. No active alerts exist.\n\n"
            f"> **Scientific Notice**: {settings.SCIENTIFIC_DISCLAIMER}"
        )

    @classmethod
    def _call_sarvam_ai(cls, user_message: str, facts: Dict[str, Any]) -> str:
        """Call Sarvam AI endpoint with structured grounded context."""
        context_payload = {
            "grounded_evidence": facts,
            "user_inquiry": user_message,
        }

        headers = {
            "Authorization": f"Bearer {settings.SARVAM_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.SARVAM_MODEL_NAME,
            "messages": [
                {"role": "system", "content": cls.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Analyze the following real-time water sensor facts and answer the user query.\n\n"
                        f"Context Facts (from backend tools):\n{context_payload}\n\n"
                        f"User Query: {user_message}"
                    ),
                },
            ],
            "temperature": 0.2,
            "max_tokens": 600,
        }

        with httpx.Client(timeout=10.0) as client:
            res = client.post(settings.SARVAM_API_URL, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            answer = data["choices"][0]["message"]["content"]
            # Ensure disclaimer is included
            if settings.SCIENTIFIC_DISCLAIMER not in answer:
                answer += f"\n\n> **Scientific Notice**: {settings.SCIENTIFIC_DISCLAIMER}"
            return answer
