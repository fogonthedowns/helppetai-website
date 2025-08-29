"""
Pet models for HelpPet MVP
"""

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
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


class Pet(Document):
    """
    Pet document for MongoDB storage
    """
    name: str = Field(..., min_length=1, max_length=100)
    species: PetSpecies
    breed: Optional[str] = Field(None, max_length=100)
    owner_id: PydanticObjectId  # Reference to User document (pet owner)
    
    # Physical characteristics
    gender: PetGender = PetGender.UNKNOWN
    age: Optional[int] = Field(None, ge=0, le=50)  # Age in years
    birth_date: Optional[date] = None
    weight: Optional[float] = Field(None, ge=0, le=1000)  # Weight in kg
    color: Optional[str] = Field(None, max_length=100)
    
    # Identification
    microchip_id: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=50)
    
    # Status
    is_spayed_neutered: Optional[bool] = None
    is_deceased: bool = False
    date_of_death: Optional[date] = None
    
    # Emergency information
    special_needs: Optional[str] = Field(None, max_length=1000)
    allergies: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "pets"
        indexes = [
            "name",
            "species",
            "owner_id",
            "microchip_id",
            "is_deceased",
            [("owner_id", 1), ("is_deceased", 1)]  # Compound index for owner's active pets
        ]

    def get_age_from_birth_date(self) -> Optional[int]:
        """Calculate age from birth date"""
        if not self.birth_date:
            return None
        
        today = date.today()
        age = today.year - self.birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < self.birth_date.month or (
            today.month == self.birth_date.month and today.day < self.birth_date.day
        ):
            age -= 1
            
        return max(0, age)

    def is_active(self) -> bool:
        """Check if pet is active (not deceased)"""
        return not self.is_deceased


class PetCreate(BaseModel):
    """Schema for creating new pets"""
    name: str = Field(..., min_length=1, max_length=100)
    species: PetSpecies
    breed: Optional[str] = Field(None, max_length=100)
    owner_id: str  # String representation of ObjectId
    gender: PetGender = PetGender.UNKNOWN
    age: Optional[int] = Field(None, ge=0, le=50)
    birth_date: Optional[date] = None
    weight: Optional[float] = Field(None, ge=0, le=1000)
    color: Optional[str] = Field(None, max_length=100)
    microchip_id: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=50)
    is_spayed_neutered: Optional[bool] = None
    special_needs: Optional[str] = Field(None, max_length=1000)
    allergies: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)


class PetUpdate(BaseModel):
    """Schema for updating pets"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    breed: Optional[str] = Field(None, max_length=100)
    gender: Optional[PetGender] = None
    age: Optional[int] = Field(None, ge=0, le=50)
    birth_date: Optional[date] = None
    weight: Optional[float] = Field(None, ge=0, le=1000)
    color: Optional[str] = Field(None, max_length=100)
    microchip_id: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=50)
    is_spayed_neutered: Optional[bool] = None
    is_deceased: Optional[bool] = None
    date_of_death: Optional[date] = None
    special_needs: Optional[str] = Field(None, max_length=1000)
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None


class PetResponse(BaseModel):
    """Schema for pet responses"""
    id: str
    name: str
    species: PetSpecies
    breed: Optional[str] = None
    owner_id: str
    gender: PetGender
    age: Optional[int] = None
    birth_date: Optional[date] = None
    weight: Optional[float] = None
    color: Optional[str] = None
    microchip_id: Optional[str] = None
    registration_number: Optional[str] = None
    is_spayed_neutered: Optional[bool] = None
    is_deceased: bool
    date_of_death: Optional[date] = None
    special_needs: Optional[str] = None
    allergies: List[str]
    current_medications: List[str]
    created_at: datetime
    updated_at: datetime
