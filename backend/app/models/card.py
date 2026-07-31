import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, ForeignKey, Float, JSON, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class ComplianceCard(Base):
    __tablename__ = "compliance_cards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("card_versions.id", use_alter=True, name="fk_current_version"), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    created_by: Mapped["User"] = relationship("User", back_populates="cards", foreign_keys=[created_by_id])
    versions: Mapped[List["CardVersion"]] = relationship("CardVersion", back_populates="card", foreign_keys="CardVersion.card_id", cascade="all, delete-orphan")
    current_version: Mapped[Optional["CardVersion"]] = relationship("CardVersion", foreign_keys=[current_version_id], post_update=True)


class CardVersion(Base):
    __tablename__ = "card_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("compliance_cards.id"), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "1.0.0"
    
    # Inputs
    config_input: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tool_manifest_input: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    runtime_trace_input: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Outputs
    card_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # holds all the compliance fields (purpose, scope, decision authority, etc.)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_classification: Mapped[str] = mapped_column(String(50), default="low", nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    card: Mapped[ComplianceCard] = relationship("ComplianceCard", back_populates="versions", foreign_keys=[card_id])
    created_by: Mapped["User"] = relationship("User", back_populates="versions", foreign_keys=[created_by_id])
    regulation_mappings: Mapped[List["RegulationMapping"]] = relationship("RegulationMapping", back_populates="version", cascade="all, delete-orphan")
