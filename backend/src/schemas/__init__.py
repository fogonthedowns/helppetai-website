"""
Schemas package for HelpPet API.
Contains all Pydantic models and validation schemas.
"""

from .pet_schemas import (
    PetSpecies,
    PetGender,
    PetBase,
    PetCreate,
    PetUpdate,
    PetOwnerSummary,
    PetResponse,
    PetWithOwnerResponse,
    PetListResponse,
    PetSearchRequest,
)

from .medical_record_schemas import (
    MedicalRecordType,
    MedicalRecordBase,
    MedicalRecordCreate,
    MedicalRecordUpdate,
    PetSummary,
    VeterinarianSummary,
    MedicalRecordResponse,
    MedicalRecordWithRelationsResponse,
    MedicalRecordListResponse,
    MedicalRecordSearchRequest,
    MedicalRecordTimelineResponse,
    MedicalRecordStatsResponse,
    MEDICAL_DATA_TEMPLATES,
)

from .base import (
    BaseResponse,
    ErrorResponse,
    HealthResponse,
    ItemBase,
    ItemCreate,
    ItemUpdate,
    ItemResponse,
    RAGQueryRequest,
    SourceReference,
    RAGResponse,
)

__all__ = [
    # Pet schemas
    "PetSpecies",
    "PetGender",
    "PetBase",
    "PetCreate",
    "PetUpdate",
    "PetOwnerSummary",
    "PetResponse",
    "PetWithOwnerResponse",
    "PetListResponse",
    "PetSearchRequest",
    
    # Medical record schemas
    "MedicalRecordType",
    "MedicalRecordBase",
    "MedicalRecordCreate",
    "MedicalRecordUpdate",
    "PetSummary",
    "VeterinarianSummary",
    "MedicalRecordResponse",
    "MedicalRecordWithRelationsResponse",
    "MedicalRecordListResponse",
    "MedicalRecordSearchRequest",
    "MedicalRecordTimelineResponse",
    "MedicalRecordStatsResponse",
    "MEDICAL_DATA_TEMPLATES",
    
    # Base schemas
    "BaseResponse",
    "ErrorResponse",
    "HealthResponse",
    "ItemBase",
    "ItemCreate",
    "ItemUpdate",
    "ItemResponse",
    "RAGQueryRequest",
    "SourceReference",
    "RAGResponse",
]
