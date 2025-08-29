"""
Pet Owner models for HelpPet MVP
"""

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class PetOwner(Document):
    """
    Pet owner document for MongoDB storage - standalone entity with optional user reference
    """
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    
    # Optional user reference for future extensibility
    user_id: Optional[PydanticObjectId] = Field(None, description="Optional reference to User document")
    
    # Owner personal information
    full_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    # Additional contact information
    emergency_contact: Optional[str] = Field(None, max_length=20)
    secondary_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    
    # Preferences
    preferred_communication: str = Field(default="email", pattern="^(email|sms|phone)$")
    notifications_enabled: bool = True
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "petOwners"
        indexes = [
            "uuid",
            "user_id",  # Optional but indexed for future queries
            "full_name",
            "email",
            "phone"
        ]


class PetOwnerCreate(BaseModel):
    """Schema for creating new pet owners"""
    user_id: Optional[str] = Field(None, description="Optional user ID to link to account")
    full_name: str = Field(..., min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    emergency_contact: Optional[str] = Field(None, max_length=20)
    secondary_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    preferred_communication: str = Field(default="email", pattern="^(email|sms|phone)$")
    notifications_enabled: bool = True


class PetOwnerUpdate(BaseModel):
    """Schema for updating pet owners"""
    user_id: Optional[str] = Field(None, description="Optional user ID to link to account")
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    emergency_contact: Optional[str] = Field(None, max_length=20)
    secondary_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    preferred_communication: Optional[str] = Field(None, pattern="^(email|sms|phone)$")
    notifications_enabled: Optional[bool] = None


class PetOwnerResponse(BaseModel):
    """Schema for pet owner responses"""
    uuid: str
    user_id: Optional[str] = None  # Optional user reference
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    secondary_phone: Optional[str] = None
    address: Optional[str] = None
    preferred_communication: str
    notifications_enabled: bool
    created_at: datetime
    updated_at: datetime
