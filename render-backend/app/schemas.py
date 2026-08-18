from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TelemetryIngestRequest(BaseModel):
    device_id: str = Field(default="AQUA-01", description="Identifier of the sensing node")
    timestamp: Optional[datetime] = Field(default=None, description="ISO-8601 UTC timestamp")
    ph: float = Field(..., ge=0.0, le=14.0, description="pH level (0.0 - 14.0)")
    turbidity: float = Field(..., ge=0.0, description="Turbidity in NTU")
    ec: float = Field(..., ge=0.0, description="Electrical Conductivity in µS/cm")
    temperature: float = Field(..., ge=-20.0, le=100.0, description="Water temperature in °C")


class TelemetryRecordSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    timestamp: datetime
    ph: float
    turbidity: float
    ec: float
    temperature: float


class TelemetryHistoryResponse(BaseModel):
    device_id: str
    count: int
    readings: List[TelemetryRecordSchema]


class AnomalyResultResponse(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    reasons: List[str]
    z_scores: Dict[str, float] = {}
    timestamp: datetime
    disclaimer: str


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    severity: str
    device_id: str
    timestamp: datetime
    anomaly_score: float
    status: str
    details: Optional[str] = None


class SensorHealthResponse(BaseModel):
    status: str
    suspect_sensor: Optional[str] = None
    details: Optional[str] = None
    metrics_status: Dict[str, str] = {}
    timestamp: datetime


class AgentAskRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User question or n8n trigger query")
    session_id: Optional[str] = Field(default="default", description="Conversation session id")


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}
    output_summary: Any = None


class AgentAskResponse(BaseModel):
    response: str
    tools_called: List[ToolCallRecord] = []
    provider_used: str
    grounded_facts: Dict[str, Any] = {}
    disclaimer: str


class DemoScenarioResponse(BaseModel):
    scenario: str
    status: str
    message: str
    telemetry_injected: TelemetryRecordSchema
    anomaly_result: AnomalyResultResponse
    event_created: Optional[EventResponse] = None
    sensor_health: SensorHealthResponse
