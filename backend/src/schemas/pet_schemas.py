"""
Pet Pydantic schemas for PostgreSQL - HelpPet MVP
"""

import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class PetSpecies(str, Enum):
    """Common pet species"""
    DOG = "Dog"
    CAT = "Cat"
    BIRD = "Bird"
    RABBIT = "Rabbit"
    HORSE = "Horse"
    REPTILE = "Reptile"
    FISH = "Fish"
    OTHER = "Other"


class PetGender(str, Enum):
    """Pet gender options"""
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown"


class PetBase(BaseModel):
    """Base pet schema with common fields"""
    name: str = Field(..., min_length=1, max_length=100)
    species: str = Field(..., max_length=50)
    breed: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=10)
    weight: Optional[float] = Field(None, ge=0, le=1000)
    date_of_birth: Optional[date] = None
    microchip_id: Optional[str] = Field(None, max_length=50)
    spayed_neutered: Optional[bool] = None
    allergies: Optional[str] = Field(None, max_length=1000)
    medications: Optional[str] = Field(None, max_length=1000)
    medical_notes: Optional[str] = Field(None, max_length=1000)
    emergency_contact: Optional[str] = Field(None, max_length=100)
    emergency_phone: Optional[str] = Field(None, max_length=20)


class PetCreate(PetBase):
    """Schema for creating new pets"""
    owner_id: uuid.UUID


class PetUpdate(BaseModel):
    """Schema for updating pets - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    species: Optional[str] = Field(None, max_length=50)
    breed: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, max_length=50)
    gender: Optional[str] = Field(None, max_length=10)
    weight: Optional[float] = Field(None, ge=0, le=1000)
    date_of_birth: Optional[date] = None
    microchip_id: Optional[str] = Field(None, max_length=50)
    spayed_neutered: Optional[bool] = None
    allergies: Optional[str] = Field(None, max_length=1000)
    medications: Optional[str] = Field(None, max_length=1000)
    medical_notes: Optional[str] = Field(None, max_length=1000)
    emergency_contact: Optional[str] = Field(None, max_length=100)
    emergency_phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class PetOwnerSummary(BaseModel):
    """Summary of pet owner for pet responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class PetResponse(PetBase):
    """Schema for pet responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    owner_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    age_years: Optional[int] = None
    display_name: str


class PetWithOwnerResponse(PetResponse):
    """Pet response with owner information included"""
    owner: PetOwnerSummary


class PetListResponse(BaseModel):
    """Response for pet list endpoints"""
    pets: List[PetResponse]
    total: int
    page: int = 1
    per_page: int = 50


class PetSearchRequest(BaseModel):
    """Request schema for pet search"""
    name: Optional[str] = Field(None, max_length=100)
    species: Optional[str] = Field(None, max_length=50)
    owner_id: Optional[uuid.UUID] = None
    include_inactive: bool = False
    page: int = Field(1, ge=1)
    per_page: int = Field(50, ge=1, le=100)
