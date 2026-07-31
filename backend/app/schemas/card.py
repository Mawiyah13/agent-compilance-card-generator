import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class LLMInfo(BaseModel):
    provider: str = Field(..., description="e.g. OpenAI, Anthropic, Custom")
    model_name: str = Field(..., description="e.g. gpt-4o, claude-3-5-sonnet")
    version: Optional[str] = Field(None, description="Model version or release tag")
    temperature: Optional[float] = None

class ToolInfo(BaseModel):
    name: str
    description: str
    permissions: List[str] = Field(default_factory=list)
    impact_level: str = Field(default="low", description="low, medium, high")

class CardData(BaseModel):
    purpose: str = Field(..., description="General purpose and intent of the agent")
    scope: str = Field(..., description="Boundary and application scope")
    llm_info: LLMInfo = Field(..., description="LLM settings and version")
    prompt_info: str = Field(..., description="System instructions and prompt strategy")
    tool_inventory: List[ToolInfo] = Field(default_factory=list, description="List of tools the agent can execute")
    operations: str = Field(..., description="Operational bounds and triggers")
    data_access: str = Field(..., description="Scope of data access and permissions")
    data_sources: List[str] = Field(default_factory=list, description="Primary sources of data utilized")
    decision_authority: str = Field(..., description="Level of decision authority granted to the agent")
    human_oversight: str = Field(..., description="Details of human-in-the-loop controls")
    risk_classification: str = Field(default="low", description="Risk level: low, medium, high, critical")
    known_limitations: List[str] = Field(default_factory=list, description="Known failure modes or edge cases")
    incident_contact: str = Field(..., description="Point of contact for incidents")
    audit_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata for auditing compliance")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = Field(default="1.0.0", description="Semver version of this card")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)

class CardVersionBase(BaseModel):
    version: str
    config_input: Optional[Dict[str, Any]] = None
    tool_manifest_input: Optional[Dict[str, Any]] = None
    runtime_trace_input: Optional[str] = None

class CardVersionCreate(CardVersionBase):
    card_data: CardData
    completeness_score: float
    risk_classification: str
    confidence_score: float

class CardVersionResponse(CardVersionBase):
    id: uuid.UUID
    card_id: uuid.UUID
    card_data: CardData
    completeness_score: float
    risk_classification: str
    confidence_score: float
    created_by_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class CardResponse(BaseModel):
    id: uuid.UUID
    name: str
    current_version_id: Optional[uuid.UUID] = None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    current_version: Optional[CardVersionResponse] = None

    class Config:
        from_attributes = True

class CardCreate(BaseModel):
    name: str
    config_input: Optional[Dict[str, Any]] = None
    tool_manifest_input: Optional[Dict[str, Any]] = None
    runtime_trace_input: Optional[str] = None

class CardUpdate(BaseModel):
    name: Optional[str] = None
    config_input: Optional[Dict[str, Any]] = None
    tool_manifest_input: Optional[Dict[str, Any]] = None
    runtime_trace_input: Optional[str] = None

# For Diffing
class CardDiffResponse(BaseModel):
    v1: str
    v2: str
    diff: Dict[str, Any]  # Key-by-key changes between versions
