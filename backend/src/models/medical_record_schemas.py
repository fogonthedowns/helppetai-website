"""
Medical Record Pydantic schemas for PostgreSQL - HelpPet MVP
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class MedicalRecordType(str, Enum):
    """Common medical record types"""
    CHECKUP = "checkup"
    VACCINATION = "vaccination"
    SURGERY = "surgery"
    EMERGENCY = "emergency"
    DENTAL = "dental"
    GROOMING = "grooming"
    DIAGNOSTIC = "diagnostic"
    TREATMENT = "treatment"
    FOLLOW_UP = "follow_up"
    OTHER = "other"


class MedicalRecordBase(BaseModel):
    """Base medical record schema with common fields"""
    record_type: str = Field(..., max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    medical_data: Optional[Dict[str, Any]] = None
    visit_date: datetime
    veterinarian_name: Optional[str] = Field(None, max_length=100)
    clinic_name: Optional[str] = Field(None, max_length=100)
    diagnosis: Optional[str] = Field(None, max_length=2000)
    treatment: Optional[str] = Field(None, max_length=2000)
    medications: Optional[str] = Field(None, max_length=2000)
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    weight: Optional[float] = Field(None, ge=0, le=1000)
    temperature: Optional[float] = Field(None, ge=90, le=110)  # Fahrenheit
    cost: Optional[float] = Field(None, ge=0)


class MedicalRecordCreate(MedicalRecordBase):
    """Schema for creating new medical records"""
    pet_id: uuid.UUID


class MedicalRecordUpdate(BaseModel):
    """Schema for updating medical records - creates new version"""
    record_type: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    medical_data: Optional[Dict[str, Any]] = None
    visit_date: Optional[datetime] = None
    veterinarian_name: Optional[str] = Field(None, max_length=100)
    clinic_name: Optional[str] = Field(None, max_length=100)
    diagnosis: Optional[str] = Field(None, max_length=2000)
    treatment: Optional[str] = Field(None, max_length=2000)
    medications: Optional[str] = Field(None, max_length=2000)
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    weight: Optional[float] = Field(None, ge=0, le=1000)
    temperature: Optional[float] = Field(None, ge=90, le=110)
    cost: Optional[float] = Field(None, ge=0)


class PetSummary(BaseModel):
    """Summary of pet for medical record responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    name: str
    species: str
    breed: Optional[str] = None


class VeterinarianSummary(BaseModel):
    """Summary of veterinarian for medical record responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    full_name: Optional[str] = None
    email: Optional[str] = None


class MedicalRecordResponse(MedicalRecordBase):
    """Schema for medical record responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    pet_id: uuid.UUID
    version: int
    is_current: bool
    created_by_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_follow_up_due: bool
    days_since_visit: int


class MedicalRecordWithRelationsResponse(MedicalRecordResponse):
    """Medical record response with pet and veterinarian information"""
    pet: PetSummary
    created_by: VeterinarianSummary


class MedicalRecordListResponse(BaseModel):
    """Response for medical record list endpoints"""
    records: List[MedicalRecordResponse]
    total: int
    current_records_count: int
    historical_records_count: int


class MedicalRecordSearchRequest(BaseModel):
    """Request schema for medical record search"""
    search_term: Optional[str] = Field(None, max_length=200)
    record_type: Optional[str] = Field(None, max_length=50)
    veterinarian_name: Optional[str] = Field(None, max_length=100)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_historical: bool = True


class MedicalRecordTimelineResponse(BaseModel):
    """Response for medical record timeline view"""
    pet_id: uuid.UUID
    pet_name: str
    records_by_date: List[MedicalRecordResponse]
    follow_up_due: List[MedicalRecordResponse]
    recent_weight: Optional[float] = None
    weight_trend: Optional[str] = None  # "increasing", "decreasing", "stable"


class MedicalRecordStatsResponse(BaseModel):
    """Response for medical record statistics"""
    total_records: int
    records_by_type: Dict[str, int]
    recent_visits: int  # Last 30 days
    follow_ups_due: int
    average_cost: Optional[float] = None
    last_visit_date: Optional[datetime] = None


# Common medical data templates for different record types
MEDICAL_DATA_TEMPLATES = {
    "vaccination": {
        "vaccine_name": "",
        "vaccine_type": "",
        "batch_number": "",
        "expiration_date": "",
        "next_due_date": "",
        "adverse_reactions": ""
    },
    "surgery": {
        "procedure_name": "",
        "anesthesia_type": "",
        "complications": "",
        "recovery_notes": "",
        "suture_removal_date": "",
        "activity_restrictions": ""
    },
    "checkup": {
        "heart_rate": "",
        "respiratory_rate": "",
        "blood_pressure": "",
        "body_condition_score": "",
        "dental_condition": "",
        "skin_condition": "",
        "eye_condition": "",
        "ear_condition": ""
    },
    "diagnostic": {
        "test_type": "",
        "test_results": "",
        "reference_ranges": "",
        "abnormal_findings": "",
        "recommendations": ""
    }
}
