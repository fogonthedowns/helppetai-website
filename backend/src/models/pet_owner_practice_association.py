"""
Pet Owner - Practice Association model for HelpPet MVP
Join table to manage which pet owners are associated with which practices
"""

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid


class AssociationStatus(str, Enum):
    """Status of the association request"""
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    INACTIVE = "inactive"


class AssociationRequestType(str, Enum):
    """Type of association request"""
    NEW_CLIENT = "new_client"        # New pet owner requesting to join practice
    REFERRAL = "referral"            # Referred from another practice
    TRANSFER = "transfer"            # Transferring from another practice
    EMERGENCY = "emergency"          # Emergency visit


class PetOwnerPracticeAssociation(Document):
    """
    Association between pet owners and veterinary practices
    Acts as a join table with additional metadata
    """
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()), unique=True)
    
    # Foreign keys
    pet_owner_uuid: str = Field(..., description="Reference to PetOwner.uuid")
    practice_uuid: str = Field(..., description="Reference to VeterinaryPractice.uuid")
    
    # Association metadata
    status: AssociationStatus = Field(default=AssociationStatus.PENDING)
    request_type: AssociationRequestType = Field(default=AssociationRequestType.NEW_CLIENT)
    
    # Request details
    requested_by_user_id: Optional[PydanticObjectId] = Field(None, description="User who created the request")
    approved_by_user_id: Optional[PydanticObjectId] = Field(None, description="User who approved the request")
    
    # Timestamps
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    last_visit_date: Optional[datetime] = None
    
    # Additional info
    notes: Optional[str] = Field(None, max_length=500)
    primary_contact: bool = Field(default=True, description="Is this the primary practice for this pet owner")
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "petOwnerPracticeAssociations"
        indexes = [
            "uuid",
            "pet_owner_uuid",
            "practice_uuid", 
            "status",
            ("pet_owner_uuid", "practice_uuid"),  # Compound index for unique constraint
            "requested_by_user_id",
            "approved_by_user_id"
        ]


class AssociationRequest(BaseModel):
    """Schema for creating new association requests"""
    pet_owner_uuid: str = Field(..., description="Pet owner UUID")
    practice_uuid: str = Field(..., description="Practice UUID")
    request_type: AssociationRequestType = Field(default=AssociationRequestType.NEW_CLIENT)
    notes: Optional[str] = Field(None, max_length=500)
    primary_contact: bool = Field(default=True)


class AssociationUpdate(BaseModel):
    """Schema for updating association requests"""
    status: Optional[AssociationStatus] = None
    notes: Optional[str] = Field(None, max_length=500)
    primary_contact: Optional[bool] = None
    last_visit_date: Optional[datetime] = None


class AssociationResponse(BaseModel):
    """Schema for association responses"""
    uuid: str
    pet_owner_uuid: str
    practice_uuid: str
    status: AssociationStatus
    request_type: AssociationRequestType
    requested_by_user_id: Optional[str] = None
    approved_by_user_id: Optional[str] = None
    requested_at: datetime
    approved_at: Optional[datetime] = None
    last_visit_date: Optional[datetime] = None
    notes: Optional[str] = None
    primary_contact: bool
    created_at: datetime
    updated_at: datetime


class PetOwnerWithPractices(BaseModel):
    """Pet owner with associated practices (for detailed views)"""
    uuid: str
    user_id: Optional[str] = None
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
    
    # Associated practices
    practices: List[dict] = Field(default_factory=list, description="List of associated practices with metadata")
