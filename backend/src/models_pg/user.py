"""
User model for PostgreSQL - HelpPet MVP
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, Text, Enum as SQLEnum, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base


class UserRole(str, Enum):
    """User role enumeration"""
    PET_OWNER = "PET_OWNER"
    VET_STAFF = "VET_STAFF"
    ADMIN = "ADMIN"


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
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    # Note: We'll add foreign key relationships once we have the Practice model
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    @property
    def is_vet_staff(self) -> bool:
        """Check if user is veterinary staff (includes admin)"""
        return self.role in [UserRole.VET_STAFF, UserRole.ADMIN]
    
    @property
    def is_pet_owner(self) -> bool:
        """Check if user is a pet owner"""
        return self.role == UserRole.PET_OWNER
    
    @property
    def is_vet_staff(self) -> bool:
        """Check if user is vet staff (includes admin)"""
        return self.role in [UserRole.VET_STAFF, UserRole.ADMIN]
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role == UserRole.ADMIN
    
    # Relationships
    created_visits: Mapped[List["Visit"]] = relationship("Visit", foreign_keys="Visit.created_by", back_populates="creator")
    vet_visits: Mapped[List["Visit"]] = relationship("Visit", foreign_keys="Visit.vet_user_id", back_populates="veterinarian")