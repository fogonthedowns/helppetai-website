"""
Veterinary Practice models for HelpPet MVP
"""

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class VeterinaryPractice(Document):
    """
    Veterinary practice document for MongoDB storage
    """
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    name: str = Field(..., min_length=1, max_length=200)
    admin_user_id: PydanticObjectId  # Reference to User document
    
    # Contact information
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    
    # Practice details
    license_number: Optional[str] = Field(None, max_length=50)
    specialties: List[str] = Field(default_factory=list)  # e.g., ["Emergency", "Dermatology"]
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Settings:
        name = "veterinaryPractices"
        indexes = [
            "uuid",
            "name",
            "admin_user_id",
            "license_number",
            "is_active"
        ]


class VeterinaryPracticeCreate(BaseModel):
    """Schema for creating new veterinary practices"""
    name: str = Field(..., min_length=1, max_length=200)
    admin_user_id: str  # String representation of ObjectId
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    license_number: Optional[str] = Field(None, max_length=50)
    specialties: List[str] = Field(default_factory=list)


class VeterinaryPracticeUpdate(BaseModel):
    """Schema for updating veterinary practices"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    license_number: Optional[str] = Field(None, max_length=50)
    specialties: Optional[List[str]] = None
    is_active: Optional[bool] = None


class VeterinaryPracticeResponse(BaseModel):
    """Schema for veterinary practice responses"""
    uuid: str
    name: str
    admin_user_id: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    license_number: Optional[str] = None
    specialties: List[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
