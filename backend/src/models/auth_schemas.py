"""
Authentication schemas for PostgreSQL - HelpPet MVP
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from ..models_pg.user import UserRole


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    """User creation schema"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.PET_OWNER


class UserResponse(BaseModel):
    """User response schema"""
    id: UUID
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserTestCredentials(BaseModel):
    """Test credentials for development"""
    username: str
    password: str
    role: UserRole
