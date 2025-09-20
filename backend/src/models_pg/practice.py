"""
Veterinary Practice model for PostgreSQL - HelpPet MVP
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Text, UUID, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base


class VeterinaryPractice(Base):
    """Veterinary practice model"""
    
    __tablename__ = "veterinary_practices"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Practice information
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Contact information
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Address information
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(50), nullable=False, default="US")
    
    # Business information
    license_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Operating information
    hours_of_operation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="America/Los_Angeles")
    
    # Capacity and limits
    max_appointments_per_day: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    accepts_new_patients: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Specialties (stored as JSON array)
    specialties: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True, default=list)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships (will be added when we create association models)
    # users: Mapped[List["User"]] = relationship("User", back_populates="practice")
    # pet_owner_associations: Mapped[List["PetOwnerPracticeAssociation"]] = relationship("PetOwnerPracticeAssociation", back_populates="practice")
    visits: Mapped[List["Visit"]] = relationship("Visit", back_populates="practice")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="practice")
    voice_config: Mapped[Optional["VoiceConfig"]] = relationship("VoiceConfig", back_populates="practice", uselist=False)
    
    def __repr__(self) -> str:
        return f"<VeterinaryPractice(id={self.id}, name='{self.name}')>"
    
    @property
    def full_address(self) -> Optional[str]:
        """Get formatted full address"""
        parts = []
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.zip_code)
        
        return ", ".join(parts) if parts else None
