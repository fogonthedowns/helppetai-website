"""
Visit models for HelpPet MVP - Veterinary visit records with transcripts
"""

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class VisitType(str, Enum):
    """Types of veterinary visits"""
    ROUTINE = "routine"
    EMERGENCY = "emergency"
    FOLLOW_UP = "follow_up"
    CONSULTATION = "consultation"
    SURGERY = "surgery"
    VACCINATION = "vaccination"
    DENTAL = "dental"
    SPECIALTY = "specialty"


class VisitStatus(str, Enum):
    """Visit status options"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Visit(Document):
    """
    Visit document for recording veterinary appointments and visits
    Includes audio transcripts shared across all associated practices
    """
    pet_id: PydanticObjectId  # Reference to Pet document
    practice_id: PydanticObjectId  # Reference to VeterinaryPractice document
    vet_user_id: PydanticObjectId  # Reference to User document (veterinarian)
    
    # Visit details
    visit_date: datetime
    visit_type: VisitType = VisitType.ROUTINE
    status: VisitStatus = VisitStatus.SCHEDULED
    
    # Duration and scheduling
    scheduled_duration: Optional[int] = Field(None, ge=1, le=480)  # Duration in minutes
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    
    # Visit content
    chief_complaint: Optional[str] = Field(None, max_length=1000)  # Reason for visit
    diagnosis: Optional[str] = Field(None, max_length=1000)
    treatment_plan: Optional[str] = Field(None, max_length=2000)
    notes: Optional[str] = Field(None, max_length=5000)
    
    # Audio transcript - shared across all practices for continuity of care
    audio_transcript: Optional[str] = Field(None, max_length=50000)
    transcript_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    transcript_processed_at: Optional[datetime] = None
    
    # Financial information
    total_cost: Optional[float] = Field(None, ge=0)
    payment_status: str = Field(default="pending", pattern="^(pending|partial|paid|insurance_pending)$")
    
    # Follow-up information
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = Field(None, max_length=1000)
    
    # Additional data (flexible for future needs)
    additional_data: Dict[str, Any] = Field(default_factory=dict)
    # Example: vital signs, lab results, imaging references, etc.
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[PydanticObjectId] = None  # User who created the visit
    
    class Settings:
        name = "visits"
        indexes = [
            "pet_id",
            "practice_id",
            "vet_user_id",
            "visit_date",
            "status",
            "visit_type",
            [("pet_id", 1), ("visit_date", -1)],  # Pet's visits chronologically
            [("practice_id", 1), ("visit_date", -1)],  # Practice's visits
            [("pet_id", 1), ("status", 1)],  # Pet's visits by status
            [("vet_user_id", 1), ("visit_date", -1)]  # Vet's visits
        ]

    def get_duration_minutes(self) -> Optional[int]:
        """Calculate actual visit duration in minutes"""
        if not self.actual_start_time or not self.actual_end_time:
            return None
        
        delta = self.actual_end_time - self.actual_start_time
        return int(delta.total_seconds() / 60)

    def is_completed(self) -> bool:
        """Check if visit is completed"""
        return self.status == VisitStatus.COMPLETED

    def has_transcript(self) -> bool:
        """Check if visit has an audio transcript"""
        return bool(self.audio_transcript)


class VisitCreate(BaseModel):
    """Schema for creating new visits"""
    pet_id: str  # String representation of ObjectId
    practice_id: str  # String representation of ObjectId
    vet_user_id: str  # String representation of ObjectId
    visit_date: datetime
    visit_type: VisitType = VisitType.ROUTINE
    scheduled_duration: Optional[int] = Field(None, ge=1, le=480)
    chief_complaint: Optional[str] = Field(None, max_length=1000)
    notes: Optional[str] = Field(None, max_length=5000)
    created_by: Optional[str] = None  # String representation of ObjectId


class VisitUpdate(BaseModel):
    """Schema for updating visits"""
    visit_date: Optional[datetime] = None
    visit_type: Optional[VisitType] = None
    status: Optional[VisitStatus] = None
    scheduled_duration: Optional[int] = Field(None, ge=1, le=480)
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    chief_complaint: Optional[str] = Field(None, max_length=1000)
    diagnosis: Optional[str] = Field(None, max_length=1000)
    treatment_plan: Optional[str] = Field(None, max_length=2000)
    notes: Optional[str] = Field(None, max_length=5000)
    audio_transcript: Optional[str] = Field(None, max_length=50000)
    transcript_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    total_cost: Optional[float] = Field(None, ge=0)
    payment_status: Optional[str] = Field(None, pattern="^(pending|partial|paid|insurance_pending)$")
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = Field(None, max_length=1000)
    additional_data: Optional[Dict[str, Any]] = None


class VisitResponse(BaseModel):
    """Schema for visit responses"""
    id: str
    pet_id: str
    practice_id: str
    vet_user_id: str
    visit_date: datetime
    visit_type: VisitType
    status: VisitStatus
    scheduled_duration: Optional[int] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_plan: Optional[str] = None
    notes: Optional[str] = None
    audio_transcript: Optional[str] = None
    transcript_confidence: Optional[float] = None
    transcript_processed_at: Optional[datetime] = None
    total_cost: Optional[float] = None
    payment_status: str
    follow_up_required: bool
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None
    additional_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None


class VisitSummary(BaseModel):
    """Lightweight summary of visits for listing"""
    id: str
    pet_id: str
    practice_id: str
    vet_user_id: str
    visit_date: datetime
    visit_type: VisitType
    status: VisitStatus
    chief_complaint: Optional[str] = None
    diagnosis: Optional[str] = None
    has_transcript: bool
    created_at: datetime
