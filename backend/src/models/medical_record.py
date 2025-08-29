"""
Medical Record models for HelpPet MVP - Versioned medical history
"""

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class MedicalRecord(Document):
    """
    Medical record document with versioning for pet health history
    Each update creates a new version, maintaining complete audit trail
    """
    pet_id: PydanticObjectId  # Reference to Pet document
    version: int = Field(..., ge=1)  # Version number for this record
    
    # Medical content - flexible JSON structure
    content: Dict[str, Any] = Field(default_factory=dict)
    # Example structure:
    # {
    #   "vaccinations": ["rabies", "dhpp", "bordetella"],
    #   "conditions": ["hip dysplasia", "allergies"],
    #   "current_medications": ["rimadyl", "fish oil"],
    #   "weight_history": [{"date": "2023-01-01", "weight": 25.5}],
    #   "vital_signs": {"temperature": 101.2, "heart_rate": 120},
    #   "notes": "Patient doing well, recommend follow-up in 6 months"
    # }
    
    # Change metadata
    change_summary: Optional[str] = Field(None, max_length=500)  # Summary of what changed
    change_type: str = Field(default="update", pattern="^(create|update|emergency|routine)$")
    
    # Audit fields
    updated_by: PydanticObjectId  # User who made this update
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Source information
    source_visit_id: Optional[PydanticObjectId] = None  # Related visit if applicable
    source_practice_id: Optional[PydanticObjectId] = None  # Practice that made the update
    
    class Settings:
        name = "medicalRecords"
        indexes = [
            "pet_id",
            [("pet_id", 1), ("version", -1)],  # Latest version first
            "updated_by",
            "updated_at",
            "source_practice_id",
            [("pet_id", 1), ("updated_at", -1)]  # Chronological order
        ]

    @classmethod
    async def get_latest_version(cls, pet_id: PydanticObjectId) -> Optional["MedicalRecord"]:
        """Get the latest version of medical records for a pet"""
        return await cls.find_one(
            {"pet_id": pet_id},
            sort=[("version", -1)]
        )

    @classmethod
    async def get_version_history(cls, pet_id: PydanticObjectId, limit: int = 50) -> List["MedicalRecord"]:
        """Get version history for a pet's medical records"""
        return await cls.find(
            {"pet_id": pet_id},
            sort=[("version", -1)],
            limit=limit
        ).to_list()


class MedicalRecordCreate(BaseModel):
    """Schema for creating new medical records"""
    pet_id: str  # String representation of ObjectId
    content: Dict[str, Any] = Field(default_factory=dict)
    change_summary: Optional[str] = Field(None, max_length=500)
    change_type: str = Field(default="update", pattern="^(create|update|emergency|routine)$")
    updated_by: str  # String representation of ObjectId
    source_visit_id: Optional[str] = None  # String representation of ObjectId
    source_practice_id: Optional[str] = None  # String representation of ObjectId


class MedicalRecordUpdate(BaseModel):
    """Schema for updating medical records (creates new version)"""
    content: Dict[str, Any]
    change_summary: Optional[str] = Field(None, max_length=500)
    change_type: str = Field(default="update", pattern="^(create|update|emergency|routine)$")
    updated_by: str  # String representation of ObjectId
    source_visit_id: Optional[str] = None  # String representation of ObjectId
    source_practice_id: Optional[str] = None  # String representation of ObjectId


class MedicalRecordResponse(BaseModel):
    """Schema for medical record responses"""
    id: str
    pet_id: str
    version: int
    content: Dict[str, Any]
    change_summary: Optional[str] = None
    change_type: str
    updated_by: str
    updated_at: datetime
    source_visit_id: Optional[str] = None
    source_practice_id: Optional[str] = None


class MedicalRecordSummary(BaseModel):
    """Lightweight summary of medical records for listing"""
    id: str
    pet_id: str
    version: int
    change_summary: Optional[str] = None
    change_type: str
    updated_by: str
    updated_at: datetime
    source_practice_id: Optional[str] = None
