"""
Association models for linking pets with veterinary practices - HelpPet MVP
"""

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PetPracticeAssociation(Document):
    """
    Association between pets and veterinary practices
    Enables pets to be treated at multiple practices while maintaining shared records
    """
    pet_id: PydanticObjectId  # Reference to Pet document
    practice_id: PydanticObjectId  # Reference to VeterinaryPractice document
    
    # Association metadata
    relationship_type: str = Field(default="patient", pattern="^(patient|emergency|referral|specialist)$")
    is_primary_practice: bool = False  # Indicates if this is the pet's primary vet
    notes: Optional[str] = Field(None, max_length=500)  # Notes about this relationship
    
    # Status
    is_active: bool = True
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PydanticObjectId] = None  # User who created this association
    
    class Settings:
        name = "petPracticeAssociations"
        indexes = [
            "pet_id",
            "practice_id",
            [("pet_id", 1), ("practice_id", 1)],  # Compound unique index
            [("pet_id", 1), ("is_active", 1)],    # Active associations for a pet
            [("practice_id", 1), ("is_active", 1)], # Active pets for a practice
            [("pet_id", 1), ("is_primary_practice", 1)] # Primary practice for a pet
        ]


class PetPracticeAssociationCreate(BaseModel):
    """Schema for creating new pet-practice associations"""
    pet_id: str  # String representation of ObjectId
    practice_id: str  # String representation of ObjectId
    relationship_type: str = Field(default="patient", pattern="^(patient|emergency|referral|specialist)$")
    is_primary_practice: bool = False
    notes: Optional[str] = Field(None, max_length=500)
    created_by: Optional[str] = None  # String representation of ObjectId


class PetPracticeAssociationUpdate(BaseModel):
    """Schema for updating pet-practice associations"""
    relationship_type: Optional[str] = Field(None, pattern="^(patient|emergency|referral|specialist)$")
    is_primary_practice: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class PetPracticeAssociationResponse(BaseModel):
    """Schema for pet-practice association responses"""
    id: str
    pet_id: str
    practice_id: str
    relationship_type: str
    is_primary_practice: bool
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
