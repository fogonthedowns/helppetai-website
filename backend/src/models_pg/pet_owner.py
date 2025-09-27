"""
Pet Owner model for PostgreSQL - HelpPet MVP
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Text, UUID, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base
except ImportError:
    from database_pg import Base


class PreferredCommunication(str, Enum):
    """Preferred communication method"""
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"


class PetOwner(Base):
    """Pet owner model - standalone entity with optional user reference"""
    
    __tablename__ = "pet_owners"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Optional user reference for future extensibility
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Owner personal information
    full_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    
    # Additional contact information
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    secondary_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Communication preferences
    preferred_communication: Mapped[PreferredCommunication] = mapped_column(
        SQLEnum(PreferredCommunication), 
        nullable=False, 
        default=PreferredCommunication.EMAIL
    )
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])
    practice_associations: Mapped[List["PetOwnerPracticeAssociation"]] = relationship(
        "PetOwnerPracticeAssociation", 
        back_populates="pet_owner",
        cascade="all, delete-orphan"
    )
    pets: Mapped[List["Pet"]] = relationship(
        "Pet", 
        foreign_keys="Pet.owner_id",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<PetOwner(id={self.id}, full_name='{self.full_name}')>"
    
    # Relationships
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="pet_owner")
    
    @property
    def primary_practice_association(self) -> Optional["PetOwnerPracticeAssociation"]:
        """Get the primary practice association"""
        for assoc in self.practice_associations:
            if assoc.primary_contact and assoc.status == "approved":
                return assoc
        return None
