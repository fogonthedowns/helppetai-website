"""
Appointment models for PostgreSQL - HelpPet MVP
Based on spec in docs/0010_appointments.md
"""

import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, UUID, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base

if TYPE_CHECKING:
    from .practice import VeterinaryPractice
    from .pet_owner import PetOwner
    from .user import User
    from .pet import Pet
    from .visit import Visit



class AppointmentType(str, Enum):
    """Types of veterinary appointments"""
    CHECKUP = "checkup"
    EMERGENCY = "emergency"
    SURGERY = "surgery"
    CONSULTATION = "consultation"


class AppointmentStatus(str, Enum):
    """Appointment status options"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    ERROR = "error"
    # Keep legacy values for backward compatibility
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Appointment(Base):
    """Appointment model - veterinary appointments"""
    
    __tablename__ = "appointments"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    practice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("veterinary_practices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    pet_owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("pet_owners.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    assigned_vet_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )
    
    # Appointment details
    appointment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    appointment_type: Mapped[str] = mapped_column(String(50), nullable=False, default=AppointmentType.CHECKUP.value)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=AppointmentStatus.SCHEDULED.value, index=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    practice: Mapped["VeterinaryPractice"] = relationship("VeterinaryPractice", back_populates="appointments")
    pet_owner: Mapped["PetOwner"] = relationship("PetOwner", back_populates="appointments")
    assigned_vet: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_vet_user_id], back_populates="assigned_appointments")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_appointments")
    appointment_pets: Mapped[List["AppointmentPet"]] = relationship("AppointmentPet", back_populates="appointment", cascade="all, delete-orphan")
    visits: Mapped[List["Visit"]] = relationship("Visit", back_populates="appointment", cascade="all, delete-orphan")

    
    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, title='{self.title}', date={self.appointment_date}, status={self.status})>"
    
    @property
    def pets(self) -> List["Pet"]:
        """Get all pets associated with this appointment"""
        return [ap.pet for ap in self.appointment_pets]


class AppointmentPet(Base):
    """Junction table for appointments and pets (many-to-many)"""
    
    __tablename__ = "appointment_pets"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    appointment: Mapped["Appointment"] = relationship("Appointment", back_populates="appointment_pets")
    pet: Mapped["Pet"] = relationship("Pet", back_populates="appointment_pets")
    
    def __repr__(self) -> str:
        return f"<AppointmentPet(appointment_id={self.appointment_id}, pet_id={self.pet_id})>"
    
    # Unique constraint to prevent duplicate pet-appointment pairs
    __table_args__ = (
        UniqueConstraint('appointment_id', 'pet_id', name='unique_appointment_pet'),
    )
