"""
Pet model for PostgreSQL - HelpPet MVP
"""

import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Text, UUID, ForeignKey, Date, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base


class Pet(Base):
    """Pet model - linked to pet owners"""
    
    __tablename__ = "pets"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to pet owner
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("pet_owners.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic pet information
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    species: Mapped[str] = mapped_column(String(50), nullable=False)  # Dog, Cat, Bird, etc.
    breed: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Physical characteristics
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # Male, Female, Unknown
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in pounds or kg
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Medical information
    microchip_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    spayed_neutered: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    medications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    medical_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Emergency information
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emergency_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    owner: Mapped["PetOwner"] = relationship("PetOwner", foreign_keys=[owner_id])
    medical_records: Mapped[List["MedicalRecord"]] = relationship(
        "MedicalRecord", 
        foreign_keys="MedicalRecord.pet_id",
        cascade="all, delete-orphan",
        order_by="MedicalRecord.visit_date.desc()"
    )
    
    def __repr__(self) -> str:
        return f"<Pet(id={self.id}, name='{self.name}', species='{self.species}')>"
    
    @property
    def age_years(self) -> Optional[int]:
        """Calculate age in years from date of birth"""
        if not self.date_of_birth:
            return None
        
        today = date.today()
        age = today.year - self.date_of_birth.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < self.date_of_birth.month or \
           (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1
            
        return max(0, age)
    
    @property
    def display_name(self) -> str:
        """Display name with species for UI"""
        return f"{self.name} ({self.species})"
    
    # Relationships
    visits: Mapped[List["Visit"]] = relationship("Visit", back_populates="pet", cascade="all, delete-orphan")
    appointment_pets: Mapped[List["AppointmentPet"]] = relationship("AppointmentPet", back_populates="pet", cascade="all, delete-orphan")