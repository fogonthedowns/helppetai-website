"""
Comprehensive schemas for HelpPet MVP - Request/Response models for API endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from .user import UserRole, UserResponse
from .pet import PetSpecies, PetGender, PetResponse
from .practice import VeterinaryPracticeResponse
from .pet_owner import PetOwnerResponse
from .associations import PetPracticeAssociationResponse
from .medical_record import MedicalRecordResponse, MedicalRecordSummary
from .visit import VisitType, VisitStatus, VisitResponse, VisitSummary


# Base response schemas
class BaseResponse(BaseModel):
    """Base response schema for simple operations"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None
    success: bool = False


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


# User-related schemas
class UserWithProfile(BaseModel):
    """User with associated profile information"""
    user: UserResponse
    pet_owner_profile: Optional[PetOwnerResponse] = None
    practice: Optional[VeterinaryPracticeResponse] = None


class UserStats(BaseModel):
    """User statistics"""
    total_pets: int = 0
    total_visits: int = 0
    recent_visits: int = 0
    practices_count: int = 0


# Pet-related schemas
class PetWithAssociations(BaseModel):
    """Pet with associated practices and summary stats"""
    pet: PetResponse
    associated_practices: List[VeterinaryPracticeResponse] = Field(default_factory=list)
    primary_practice: Optional[VeterinaryPracticeResponse] = None
    total_visits: int = 0
    last_visit_date: Optional[datetime] = None
    needs_follow_up: bool = False


class PetMedicalSummary(BaseModel):
    """Pet medical summary for quick overview"""
    pet: PetResponse
    latest_medical_record: Optional[MedicalRecordSummary] = None
    recent_visits: List[VisitSummary] = Field(default_factory=list)
    total_medical_versions: int = 0
    has_emergency_records: bool = False


# Practice-related schemas
class PracticeWithStats(BaseModel):
    """Practice with statistics"""
    practice: VeterinaryPracticeResponse
    total_pets: int = 0
    total_visits: int = 0
    active_associations: int = 0
    staff_count: int = 0
    upcoming_visits: int = 0


class PracticeOverview(BaseModel):
    """Practice overview for dashboard"""
    practice: VeterinaryPracticeResponse
    recent_visits: List[VisitSummary] = Field(default_factory=list)
    upcoming_visits: List[VisitSummary] = Field(default_factory=list)
    overdue_visits: List[VisitSummary] = Field(default_factory=list)
    follow_up_needed: List[VisitSummary] = Field(default_factory=list)


# Visit-related schemas
class VisitWithDetails(BaseModel):
    """Visit with related pet and practice information"""
    visit: VisitResponse
    pet: PetResponse
    practice: VeterinaryPracticeResponse
    veterinarian: UserResponse


class VisitHistory(BaseModel):
    """Complete visit history for a pet across all practices"""
    pet: PetResponse
    visits: List[VisitWithDetails] = Field(default_factory=list)
    total_visits: int = 0
    practices_visited: List[VeterinaryPracticeResponse] = Field(default_factory=list)
    has_transcripts: bool = False


# Medical record-related schemas
class MedicalHistoryOverview(BaseModel):
    """Complete medical history overview for a pet"""
    pet: PetResponse
    latest_record: Optional[MedicalRecordResponse] = None
    version_history: List[MedicalRecordSummary] = Field(default_factory=list)
    total_versions: int = 0
    last_updated: Optional[datetime] = None
    updated_by_practices: List[str] = Field(default_factory=list)


class MedicalRecordComparison(BaseModel):
    """Comparison between two medical record versions"""
    pet_id: str
    older_version: MedicalRecordResponse
    newer_version: MedicalRecordResponse
    changes_summary: List[str] = Field(default_factory=list)


# Search and filter schemas
class PetSearchFilters(BaseModel):
    """Filters for pet search"""
    owner_id: Optional[str] = None
    species: Optional[PetSpecies] = None
    age_min: Optional[int] = Field(None, ge=0)
    age_max: Optional[int] = Field(None, le=50)
    include_deceased: bool = False
    has_microchip: Optional[bool] = None
    breed: Optional[str] = None


class VisitSearchFilters(BaseModel):
    """Filters for visit search"""
    pet_id: Optional[str] = None
    practice_id: Optional[str] = None
    vet_user_id: Optional[str] = None
    visit_type: Optional[VisitType] = None
    status: Optional[VisitStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_transcript: Optional[bool] = None
    follow_up_required: Optional[bool] = None


class UserSearchFilters(BaseModel):
    """Filters for user search"""
    role: Optional[UserRole] = None
    practice_id: Optional[str] = None
    is_active: bool = True


# Dashboard schemas
class OwnerDashboard(BaseModel):
    """Pet owner dashboard data"""
    owner: UserResponse
    pets: List[PetWithAssociations] = Field(default_factory=list)
    recent_visits: List[VisitSummary] = Field(default_factory=list)
    upcoming_visits: List[VisitSummary] = Field(default_factory=list)
    follow_up_needed: List[VisitSummary] = Field(default_factory=list)
    stats: UserStats


class VetDashboard(BaseModel):
    """Veterinarian dashboard data"""
    veterinarian: UserResponse
    practice: Optional[VeterinaryPracticeResponse] = None
    todays_visits: List[VisitSummary] = Field(default_factory=list)
    upcoming_visits: List[VisitSummary] = Field(default_factory=list)
    recent_patients: List[PetResponse] = Field(default_factory=list)
    follow_up_needed: List[VisitSummary] = Field(default_factory=list)


class PracticeDashboard(BaseModel):
    """Practice administrator dashboard data"""
    practice_overview: PracticeOverview
    staff_list: List[UserResponse] = Field(default_factory=list)
    patient_stats: Dict[str, int] = Field(default_factory=dict)
    visit_stats: Dict[str, int] = Field(default_factory=dict)
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)


# Bulk operation schemas
class BulkCreateResponse(BaseModel):
    """Response for bulk create operations"""
    created_count: int
    failed_count: int
    errors: List[str] = Field(default_factory=list)
    created_ids: List[str] = Field(default_factory=list)


class BulkUpdateResponse(BaseModel):
    """Response for bulk update operations"""
    updated_count: int
    failed_count: int
    errors: List[str] = Field(default_factory=list)
    updated_ids: List[str] = Field(default_factory=list)


# Association management schemas
class AssociationRequest(BaseModel):
    """Request to create pet-practice association"""
    pet_id: str
    practice_id: str
    relationship_type: str = Field(default="patient", pattern="^(patient|emergency|referral|specialist)$")
    is_primary_practice: bool = False
    notes: Optional[str] = Field(None, max_length=500)


class AssociationUpdate(BaseModel):
    """Request to update pet-practice association"""
    relationship_type: Optional[str] = Field(None, pattern="^(patient|emergency|referral|specialist)$")
    is_primary_practice: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


# Health check and system schemas
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    database_connected: bool = True
    services: Dict[str, str] = Field(default_factory=dict)
