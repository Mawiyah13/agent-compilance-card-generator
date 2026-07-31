import json
import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_active_user, RoleChecker
from app.models.user import User
from app.models.card import ComplianceCard, CardVersion
from app.models.regulation import RegulationMapping
from app.models.audit import AuditLog
from app.schemas.card import CardResponse, CardCreate, CardVersionResponse, CardDiffResponse, CardData
from app.services.compliance import ComplianceEngine, parse_input_to_dict
from app.services.diff import DiffEngine
from app.services.pdf_generator import generate_compliance_pdf

router = APIRouter()

# Helper to log audits
async def log_audit(db: AsyncSession, user_id: uuid.UUID, action: str, details: dict):
    audit = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address="127.0.0.1"  # Simplified
    )
    db.add(audit)


@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_compliance_card(
    name: str = Form(...),
    config_text: Optional[str] = Form(None),
    tool_manifest_text: Optional[str] = Form(None),
    runtime_trace_text: Optional[str] = Form(None),
    config_file: Optional[UploadFile] = File(None),
    tool_manifest_file: Optional[UploadFile] = File(None),
    runtime_trace_file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    # 1. Read files if uploaded
    config_content = config_text or ""
    if config_file:
        config_content = (await config_file.read()).decode("utf-8")
        
    tool_manifest_content = tool_manifest_text or ""
    if tool_manifest_file:
        tool_manifest_content = (await tool_manifest_file.read()).decode("utf-8")
        
    runtime_trace_content = runtime_trace_text or ""
    if runtime_trace_file:
        runtime_trace_content = (await runtime_trace_file.read()).decode("utf-8")

    # 2. Parse and generate card data
    card_data = ComplianceEngine.generate_card(
        config_content,
        tool_manifest_content,
        runtime_trace_content
    )
    
    # 3. Calculate completeness and regulation mappings
    completeness_score, missing_fields = ComplianceEngine.calculate_completeness(card_data)
    regulation_data = ComplianceEngine.map_regulations(card_data)

    # 4. Save Card
    new_card = ComplianceCard(
        name=name,
        created_by_id=current_user.id
    )
    db.add(new_card)
    await db.flush()  # Populates ID

    # 5. Save CardVersion
    new_version = CardVersion(
        card_id=new_card.id,
        version="1.0.0",
        config_input=parse_input_to_dict(config_content),
        tool_manifest_input=parse_input_to_dict(tool_manifest_content),
        runtime_trace_input=runtime_trace_content,
        card_data=card_data.model_dump(mode="json"),
        completeness_score=completeness_score,
        risk_classification=card_data.risk_classification,
        confidence_score=card_data.confidence_score,
        created_by_id=current_user.id
    )
    db.add(new_version)
    await db.flush()  # Populates version ID

    # Set as current version
    new_card.current_version_id = new_version.id

    # 6. Save Regulation Mappings
    for fw, data in regulation_data.items():
        mapping = RegulationMapping(
            version_id=new_version.id,
            framework=fw,
            status=data["status"],
            details=data
        )
        db.add(mapping)

    await log_audit(db, current_user.id, "create_compliance_card", {
        "card_id": str(new_card.id),
        "card_name": name,
        "completeness_score": completeness_score,
        "risk_classification": card_data.risk_classification
    })
    
    await db.commit()
    
    # Load relationships for response
    stmt = (
        select(ComplianceCard)
        .options(selectinload(ComplianceCard.current_version).selectinload(CardVersion.regulation_mappings))
        .where(ComplianceCard.id == new_card.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("", response_model=List[CardResponse])
async def list_compliance_cards(
    search: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    stmt = (
        select(ComplianceCard)
        .options(selectinload(ComplianceCard.current_version).selectinload(CardVersion.regulation_mappings))
    )
    
    filters = []
    if search:
        filters.append(ComplianceCard.name.ilike(f"%{search}%"))
        
    if filters:
        stmt = stmt.where(and_(*filters))
        
    stmt = stmt.offset(skip).limit(limit).order_by(ComplianceCard.created_at.desc())
    result = await db.execute(stmt)
    cards = result.scalars().all()
    
    # Optional in-memory filter for risk
    if risk:
        cards = [c for c in cards if c.current_version and c.current_version.risk_classification == risk.lower()]
        
    return cards


@router.get("/{card_id}", response_model=CardResponse)
async def get_compliance_card(
    card_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    stmt = (
        select(ComplianceCard)
        .options(selectinload(ComplianceCard.current_version).selectinload(CardVersion.regulation_mappings))
        .where(ComplianceCard.id == card_id)
    )
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance card not found"
        )
    return card


@router.put("/{card_id}", response_model=CardResponse)
async def update_compliance_card(
    card_id: uuid.UUID,
    name: Optional[str] = Form(None),
    config_text: Optional[str] = Form(None),
    tool_manifest_text: Optional[str] = Form(None),
    runtime_trace_text: Optional[str] = Form(None),
    config_file: Optional[UploadFile] = File(None),
    tool_manifest_file: Optional[UploadFile] = File(None),
    runtime_trace_file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    # 1. Fetch card and latest version
    stmt = (
        select(ComplianceCard)
        .options(selectinload(ComplianceCard.current_version))
        .where(ComplianceCard.id == card_id)
    )
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance card not found"
        )

    # Update name if provided
    if name:
        card.name = name

    # Parse and generate card data
    config_content = config_text or ""
    if config_file:
        config_content = (await config_file.read()).decode("utf-8")
        
    tool_manifest_content = tool_manifest_text or ""
    if tool_manifest_file:
        tool_manifest_content = (await tool_manifest_file.read()).decode("utf-8")
        
    runtime_trace_content = runtime_trace_text or ""
    if runtime_trace_file:
        runtime_trace_content = (await runtime_trace_file.read()).decode("utf-8")

    # If no inputs provided, just commit updated fields (like name)
    if not config_content and not tool_manifest_content and not runtime_trace_content and not config_file and not tool_manifest_file and not runtime_trace_file:
        await db.commit()
        # Refetch and return
        stmt = (
            select(ComplianceCard)
            .options(selectinload(ComplianceCard.current_version).selectinload(CardVersion.regulation_mappings))
            .where(ComplianceCard.id == card_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one()

    # Generate new card data
    new_card_data = ComplianceEngine.generate_card(
        config_content,
        tool_manifest_content,
        runtime_trace_content
    )
    
    # 2. Get old card data to diff
    old_version = card.current_version
    if not old_version:
        # Fallback if somehow there is no version
        old_card_data = new_card_data
        old_version_str = "0.0.0"
    else:
        old_card_data = CardData.model_validate(old_version.card_data)
        old_version_str = old_version.version

    # 3. Diff and Semver bump
    diff_res = DiffEngine.diff_cards(old_card_data, new_card_data)
    
    v_parts = [int(x) for x in old_version_str.split(".")]
    if diff_res["reassessment_required"]:
        # Bump Major
        new_version_str = f"{v_parts[0] + 1}.0.0"
    elif diff_res["has_changes"]:
        # Bump Minor
        new_version_str = f"{v_parts[0]}.{v_parts[1] + 1}.0"
    else:
        # Bump Patch
        new_version_str = f"{v_parts[0]}.{v_parts[1]}.{v_parts[2] + 1}"

    # Update version in card_data
    new_card_data.version = new_version_str

    # Recalculate completeness & mappings
    completeness_score, missing_fields = ComplianceEngine.calculate_completeness(new_card_data)
    regulation_data = ComplianceEngine.map_regulations(new_card_data)

    # 4. Save new CardVersion
    new_version = CardVersion(
        card_id=card.id,
        version=new_version_str,
        config_input=parse_input_to_dict(config_content) if config_content else (old_version.config_input if old_version else {}),
        tool_manifest_input=parse_input_to_dict(tool_manifest_content) if tool_manifest_content else (old_version.tool_manifest_input if old_version else {}),
        runtime_trace_input=runtime_trace_content if runtime_trace_content else (old_version.runtime_trace_input if old_version else ""),
        card_data=new_card_data.model_dump(mode="json"),
        completeness_score=completeness_score,
        risk_classification=new_card_data.risk_classification,
        confidence_score=new_card_data.confidence_score,
        created_by_id=current_user.id
    )
    db.add(new_version)
    await db.flush()

    card.current_version_id = new_version.id

    # 5. Save Regulation Mappings for new version
    for fw, data in regulation_data.items():
        mapping = RegulationMapping(
            version_id=new_version.id,
            framework=fw,
            status=data["status"],
            details=data
        )
        db.add(mapping)

    await log_audit(db, current_user.id, "update_compliance_card", {
        "card_id": str(card.id),
        "card_name": card.name,
        "old_version": old_version_str,
        "new_version": new_version_str,
        "reassessment_required": diff_res["reassessment_required"],
        "reassessment_reasons": diff_res["reassessment_reasons"]
    })

    await db.commit()
    await db.refresh(card, ["current_version"])

    # Load relationships for response
    stmt = (
        select(ComplianceCard)
        .options(selectinload(ComplianceCard.current_version).selectinload(CardVersion.regulation_mappings))
        .where(ComplianceCard.id == card_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


@router.get("/{card_id}/versions", response_model=List[CardVersionResponse])
async def list_card_versions(
    card_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    stmt = (
        select(CardVersion)
        .where(CardVersion.card_id == card_id)
        .order_by(CardVersion.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{card_id}/diff", response_model=CardDiffResponse)
async def diff_card_versions(
    card_id: uuid.UUID,
    v1: str = Query(..., description="E.g., 1.0.0"),
    v2: str = Query(..., description="E.g., 2.0.0"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    # Query version 1
    stmt_v1 = select(CardVersion).where(and_(CardVersion.card_id == card_id, CardVersion.version == v1))
    res_v1 = await db.execute(stmt_v1)
    version_1 = res_v1.scalar_one_or_none()

    # Query version 2
    stmt_v2 = select(CardVersion).where(and_(CardVersion.card_id == card_id, CardVersion.version == v2))
    res_v2 = await db.execute(stmt_v2)
    version_2 = res_v2.scalar_one_or_none()

    if not version_1 or not version_2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both card versions not found"
        )

    c1_data = CardData.model_validate(version_1.card_data)
    c2_data = CardData.model_validate(version_2.card_data)
    
    diff_res = DiffEngine.diff_cards(c1_data, c2_data)

    return {
        "v1": v1,
        "v2": v2,
        "diff": diff_res
    }


@router.get("/{card_id}/export/pdf")
async def export_card_pdf(
    card_id: uuid.UUID,
    version: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    stmt = (
        select(ComplianceCard)
        .options(selectinload(ComplianceCard.versions).selectinload(CardVersion.regulation_mappings))
        .where(ComplianceCard.id == card_id)
    )
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    # Get target version
    target_version = None
    if version:
        for v in card.versions:
            if v.version == version:
                target_version = v
                break
    else:
        # fetch current version
        stmt_curr = (
            select(CardVersion)
            .options(selectinload(CardVersion.regulation_mappings))
            .where(CardVersion.id == card.current_version_id)
        )
        res_curr = await db.execute(stmt_curr)
        target_version = res_curr.scalar_one_or_none()

    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card version not found"
        )

    c_data = CardData.model_validate(target_version.card_data)
    
    # Map checklist objects
    mappings = {m.framework: m.details for m in target_version.regulation_mappings}
    
    pdf_bytes = generate_compliance_pdf(
        card.name,
        c_data,
        target_version.completeness_score,
        mappings
    )
    
    await log_audit(db, current_user.id, "export_compliance_card_pdf", {
        "card_id": str(card.id),
        "version": target_version.version
    })
    await db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=compliance_card_{card.name.replace(' ', '_')}_{target_version.version}.pdf"
        }
    )


@router.get("/{card_id}/export/json")
async def export_card_json(
    card_id: uuid.UUID,
    version: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    stmt = select(ComplianceCard).options(selectinload(ComplianceCard.versions)).where(ComplianceCard.id == card_id)
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    target_version = None
    if version:
        for v in card.versions:
            if v.version == version:
                target_version = v
                break
    else:
        stmt_curr = select(CardVersion).where(CardVersion.id == card.current_version_id)
        res_curr = await db.execute(stmt_curr)
        target_version = res_curr.scalar_one_or_none()

    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )

    await log_audit(db, current_user.id, "export_compliance_card_json", {
        "card_id": str(card.id),
        "version": target_version.version
    })
    await db.commit()

    return {
        "card_name": card.name,
        "version": target_version.version,
        "completeness_score": target_version.completeness_score,
        "risk_classification": target_version.risk_classification,
        "confidence_score": target_version.confidence_score,
        "card_data": target_version.card_data,
        "created_at": target_version.created_at.isoformat()
    }
