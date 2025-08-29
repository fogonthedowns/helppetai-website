"""
Pet Owner models for HelpPet MVP
"""

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PetOwner(Document):
    """
    Pet owner document for MongoDB storage - extends user information for pet owners
    """
    user_id: PydanticObjectId  # Reference to User document
    emergency_contact: Optional[str] = Field(None, max_length=20)
    
    # Additional contact information
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
            "user_id",
            "emergency_contact"
        ]


class PetOwnerCreate(BaseModel):
    """Schema for creating new pet owners"""
    user_id: str  # String representation of ObjectId
    emergency_contact: Optional[str] = Field(None, max_length=20)
    secondary_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    preferred_communication: str = Field(default="email", pattern="^(email|sms|phone)$")
    notifications_enabled: bool = True


class PetOwnerUpdate(BaseModel):
    """Schema for updating pet owners"""
    emergency_contact: Optional[str] = Field(None, max_length=20)
    secondary_phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    preferred_communication: Optional[str] = Field(None, pattern="^(email|sms|phone)$")
    notifications_enabled: Optional[bool] = None


class PetOwnerResponse(BaseModel):
    """Schema for pet owner responses"""
    id: str
    user_id: str
    emergency_contact: Optional[str] = None
    secondary_phone: Optional[str] = None
    address: Optional[str] = None
    preferred_communication: str
    notifications_enabled: bool
    created_at: datetime
    updated_at: datetime
