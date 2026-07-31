import uuid
from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class RegulationMapping(Base):
    __tablename__ = "regulation_mappings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("card_versions.id"), nullable=False)
    framework: Mapped[str] = mapped_column(String(100), nullable=False)  # EU AI Act, NIST AI RMF, ISO 42001
    status: Mapped[str] = mapped_column(String(50), default="non-compliant", nullable=False)  # compliant, partially-compliant, non-compliant
    details: Mapped[dict] = mapped_column(JSON, nullable=False)  # stores list of clauses/requirements and their status

    # Relationships
    version: Mapped["CardVersion"] = relationship("CardVersion", back_populates="regulation_mappings")
