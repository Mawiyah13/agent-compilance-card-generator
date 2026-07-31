from typing import Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import RoleChecker
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse

router = APIRouter()

# RBAC: Only admin or auditor can read audit logs
@router.get("/", response_model=List[AuditLogResponse])
async def list_audit_logs(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _ = Depends(RoleChecker(allowed_roles=["admin", "auditor"]))
) -> Any:
    stmt = (
        select(AuditLog)
        .offset(skip)
        .limit(limit)
        .order_by(AuditLog.timestamp.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
