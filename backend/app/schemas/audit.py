import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
