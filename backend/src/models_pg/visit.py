"""
Visit model for PostgreSQL - HelpPet MVP
Visit transcripts for veterinary appointments
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, UUID, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base

if TYPE_CHECKING:
    from .pet import Pet
    from .practice import VeterinaryPractice
    from .user import User


class VisitState(str, Enum):
    """Visit transcript processing states"""
    NEW = "new"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Visit(Base):
    """Visit model - appointment transcripts linked to pets"""
    
    __tablename__ = "visits"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    practice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("veterinary_practices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    vet_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Visit details
    visit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Transcript content
    full_text: Mapped[str] = mapped_column(Text, nullable=False)
    audio_transcript_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Processing state
    state: Mapped[str] = mapped_column(String(20), nullable=False, default=VisitState.NEW.value, index=True)
    
    # Additional metadata as JSON
    additional_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    pet: Mapped["Pet"] = relationship("Pet", back_populates="visits")
    practice: Mapped["VeterinaryPractice"] = relationship("VeterinaryPractice", back_populates="visits")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by], back_populates="created_visits")
    veterinarian: Mapped[Optional["User"]] = relationship("User", foreign_keys=[vet_user_id], back_populates="vet_visits")
    
    def __repr__(self) -> str:
        return f"<Visit(id={self.id}, pet_id={self.pet_id}, visit_date={self.visit_date}, state={self.state})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "uuid": str(self.id),
            "pet_id": str(self.pet_id),
            "visit_date": int(self.visit_date.timestamp()),
            "full_text": self.full_text,
            "audio_transcript_url": self.audio_transcript_url,
            "summary": self.summary,
            "state": self.state,
            "metadata": self.additional_data or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
        }
