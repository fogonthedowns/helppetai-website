"""
User model for MongoDB with Beanie ODM - HelpPet MVP
"""

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles in the HelpPet system"""
    PET_OWNER = "PetOwner"
    VET_STAFF = "VetStaff"
    ADMIN = "Admin"


class User(Document):
    """
    User document for MongoDB storage - supports pet owners and veterinary staff
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password_hash: str = Field(..., alias="hashed_password")  # Keep backward compatibility
    role: UserRole
    full_name: str = Field(..., min_length=1, max_length=100)
    practice_id: Optional[PydanticObjectId] = None  # ObjectId for staff, null for owners
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Settings:
        name = "users"
        # Remove indexes temporarily to avoid conflicts with existing database
        # In production, these should be managed via migrations
        indexes = []

    def is_pet_owner(self) -> bool:
        """Check if user is a pet owner"""
        return self.role == UserRole.PET_OWNER

    def is_vet_staff(self) -> bool:
        """Check if user is veterinary staff"""
        return self.role in [UserRole.VET_STAFF, UserRole.ADMIN]

    def is_admin(self) -> bool:
        """Check if user is an administrator"""
        return self.role == UserRole.ADMIN


class UserCreate(BaseModel):
    """Schema for creating new users"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=6)
    role: UserRole
    full_name: str = Field(..., min_length=1, max_length=100)
    practice_id: Optional[str] = None  # String representation of ObjectId


class UserUpdate(BaseModel):
    """Schema for updating users"""
    email: Optional[str] = Field(None, pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user responses (no password)"""
    id: str
    username: str
    email: str
    role: UserRole
    full_name: str
    practice_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
