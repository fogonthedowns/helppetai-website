"""
User model for PostgreSQL - HelpPet MVP
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Boolean, DateTime, Text, Enum as SQLEnum, UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base


class UserRole(str, Enum):
    """User role enumeration"""
    PET_OWNER = "PET_OWNER"           # Pet owner - manages their pets
    VET_STAFF = "VET_STAFF"            # Regular staff - can view/edit within practice
    PRACTICE_ADMIN = "PRACTICE_ADMIN"  # Practice admin - can manage team, invite, remove
    SYSTEM_ADMIN = "SYSTEM_ADMIN"      # Platform admin - can manage all practices (future use)
    PENDING_INVITE = "PENDING_INVITE"  # Temporary - awaiting invite acceptance


class User(Base):
    """User model for authentication and authorization"""
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication fields
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile fields
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False, default=UserRole.VET_STAFF)
    
    # Practice association (for vet staff)
    practice_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Survey data (optional JSON field for onboarding survey responses)
    survey: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    # Note: We'll add foreign key relationships once we have the Practice model
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    @property
    def is_vet_staff(self) -> bool:
        """Check if user is veterinary staff (includes practice admin and system admin)"""
        return self.role in [UserRole.VET_STAFF, UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]
    
    @property
    def is_pet_owner(self) -> bool:
        """Check if user is a pet owner"""
        return self.role == UserRole.PET_OWNER
    
    @property
    def is_practice_admin(self) -> bool:
        """Check if user is a practice admin (can manage team within their practice)"""
        return self.role in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]
    
    @property
    def is_system_admin(self) -> bool:
        """Check if user is a system admin (can manage all practices)"""
        return self.role == UserRole.SYSTEM_ADMIN
    
    # Relationships
    created_visits: Mapped[List["Visit"]] = relationship("Visit", foreign_keys="Visit.created_by", back_populates="creator")
    vet_visits: Mapped[List["Visit"]] = relationship("Visit", foreign_keys="Visit.vet_user_id", back_populates="veterinarian")
    assigned_appointments: Mapped[List["Appointment"]] = relationship("Appointment", foreign_keys="Appointment.assigned_vet_user_id", back_populates="assigned_vet")
    created_appointments: Mapped[List["Appointment"]] = relationship("Appointment", foreign_keys="Appointment.created_by_user_id", back_populates="created_by")
    device_tokens: Mapped[List["DeviceToken"]] = relationship("DeviceToken", back_populates="user")
