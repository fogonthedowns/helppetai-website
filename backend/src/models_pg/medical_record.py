"""
Medical Record model for PostgreSQL - HelpPet MVP
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import String, Boolean, DateTime, Text, UUID, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base


class MedicalRecord(Base):
    """Medical record model - linked to pets with versioning support"""
    
    __tablename__ = "medical_records"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to pet
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Versioning - each update creates a new record with incremented version
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    
    # Record metadata
    record_type: Mapped[str] = mapped_column(String(50), nullable=False)  # checkup, vaccination, surgery, etc.
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Medical data stored as JSON for flexibility
    medical_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Visit information
    visit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    veterinarian_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    clinic_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Treatment details
    diagnosis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    treatment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    medications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    follow_up_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Vital signs and measurements (stored in medical_data JSON, but common ones as columns)
    weight: Mapped[Optional[float]] = mapped_column(nullable=True)  # Weight at time of visit
    temperature: Mapped[Optional[float]] = mapped_column(nullable=True)  # Body temperature
    
    # Cost and billing
    cost: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Record management
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True
    )
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    pet: Mapped["Pet"] = relationship("Pet", foreign_keys=[pet_id])
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    
    def __repr__(self) -> str:
        return f"<MedicalRecord(id={self.id}, pet_id={self.pet_id}, title='{self.title}', version={self.version})>"
    
    @property
    def is_follow_up_due(self) -> bool:
        """Check if follow-up is due"""
        if not self.follow_up_required or not self.follow_up_date:
            return False
        return datetime.now(timezone.utc) >= self.follow_up_date
    
    @property
    def days_since_visit(self) -> int:
        """Calculate days since the visit"""
        return (datetime.now(timezone.utc) - self.visit_date).days
    
    def get_medical_data_field(self, field_name: str, default=None):
        """Safely get a field from medical_data JSON"""
        if not self.medical_data:
            return default
        return self.medical_data.get(field_name, default)
