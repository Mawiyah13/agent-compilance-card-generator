import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class RequirementCheck(BaseModel):
    id: str
    title: str
    description: str
    status: str  # compliant, partially-compliant, non-compliant, not-applicable
    evidence: str
    remediation: Optional[str] = None

class RegulationMappingResponse(BaseModel):
    id: uuid.UUID
    version_id: uuid.UUID
    framework: str
    status: str
    details: Dict[str, Any]  # list of checks and mapping logs

    class Config:
        from_attributes = True
