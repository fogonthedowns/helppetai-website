"""
Appointment schemas for API validation and documentation
"""

from datetime import datetime, date, time
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator
from enum import Enum

from ..models_pg.appointment import AppointmentType, AppointmentStatus


class TimePreference(str, Enum):
    """Time preference options for appointment booking"""
    MORNING = "morning"
    AFTERNOON = "afternoon" 
    EVENING = "evening"
    ANY_TIME = "any time"


class BookAppointmentRequest(BaseModel):
    """Schema for booking an appointment via phone integration"""
    
    # Required fields
    practice_id: str = Field(
        ..., 
        description="Practice UUID - use the practice_id variable exactly as provided"
    )
    pet_owner_id: str = Field(
        ...,
        description="Pet owner UUID from user lookup"
    )
    date: str = Field(
        ..., 
        description="Local date for the appointment (e.g., '2025-09-15', '9-15', 'September 15', 'tomorrow')"
    )
    start_time: str = Field(
        ...,
        description="Local start time selected by user (e.g., '2:30 PM', '14:30', '7:30 PM')"
    )
    
    # Optional fields with defaults
    timezone: str = Field(
        default="America/Los_Angeles",
        description="Practice timezone (e.g., 'America/New_York', 'US/Pacific', 'US/Mountain', 'America/Chicago')"
    )
    service: str = Field(
        default="General Checkup",
        description="Type of service/appointment (e.g., 'General Checkup', 'Vaccination', 'Surgery Consultation')"
    )
    pet_names: Optional[List[str]] = Field(
        default=None,
        description="List of pet names for this appointment (e.g., ['Amira'], ['Winston'], ['Amira', 'Winston']). If not provided, all pets will be included"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes or special requests"
    )
    assigned_vet_user_id: Optional[str] = Field(
        default=None,
        description="Specific vet UUID if requested (optional - system will assign if not provided)"
    )

    @validator('practice_id', 'pet_owner_id')
    def validate_uuid_fields(cls, v):
        """Validate UUID format"""
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")

    @validator('pet_names')
    def validate_pet_names(cls, v):
        """Validate pet names list"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("Pet names must be a list")
            validated_names = []
            for name in v:
                if not isinstance(name, str):
                    raise ValueError("Each pet name must be a string")
                name = name.strip()
                if len(name) == 0:
                    raise ValueError("Pet name cannot be empty")
                if len(name) > 50:
                    raise ValueError("Pet name too long (max 50 characters)")
                validated_names.append(name)
            return validated_names
        return v

    @validator('assigned_vet_user_id')
    def validate_vet_uuid(cls, v):
        """Validate vet UUID format"""
        if v is not None:
            try:
                UUID(v)
            except ValueError:
                raise ValueError(f"Invalid vet UUID format: {v}")
        return v


class BookAppointmentResponse(BaseModel):
    """Response schema for appointment booking"""
    
    success: bool = Field(..., description="Whether the booking was successful")
    appointment_id: Optional[str] = Field(None, description="Created appointment UUID if successful")
    message: str = Field(..., description="Human-readable message for the caller")
    
    # Additional details for successful bookings
    details: Optional[dict] = Field(None, description="Appointment details if successful")
    
    # Error information for failed bookings
    error_code: Optional[str] = Field(None, description="Error code for failed bookings")
    conflicts: Optional[List[dict]] = Field(None, description="Time conflicts if any")


class ConfirmAppointmentRequest(BaseModel):
    """Schema for confirming an appointment"""
    
    appointment_id: str = Field(..., description="Appointment UUID to confirm")
    
    @validator('appointment_id')
    def validate_appointment_uuid(cls, v):
        """Validate appointment UUID format"""
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid appointment UUID format: {v}")


class ConfirmAppointmentResponse(BaseModel):
    """Response schema for appointment confirmation"""
    
    success: bool = Field(..., description="Whether the confirmation was successful")
    message: str = Field(..., description="Human-readable confirmation message")
    appointment_details: Optional[dict] = Field(None, description="Confirmed appointment details")


class GetAvailableTimesRequest(BaseModel):
    """Schema for getting available appointment times (from SchedulingService)"""
    
    date: str = Field(
        ..., 
        description="The date for availability check (e.g., '9-14', 'September 14', 'tomorrow')"
    )
    practice_id: str = Field(
        ...,
        description="Practice UUID - use the practice_id variable exactly as provided"
    )
    time_preference: str = Field(
        default="any time",
        description="Time of day preference (e.g., 'morning', 'afternoon', 'evening', 'any time')"
    )
    timezone: str = Field(
        default="America/Los_Angeles",
        description="Practice timezone (e.g., 'America/New_York', 'US/Pacific', 'US/Mountain')"
    )

    @validator('practice_id')
    def validate_practice_uuid(cls, v):
        """Validate practice UUID format"""
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid practice UUID format: {v}")


class GetAvailableTimesResponse(BaseModel):
    """Response schema for available times"""
    
    success: bool = Field(..., description="Whether the request was successful")
    available_times: Optional[List[str]] = Field(None, description="List of available times in local format")
    message: str = Field(..., description="Human-readable message")
    date: Optional[str] = Field(None, description="Requested date in YYYY-MM-DD format")
    time_preference: Optional[str] = Field(None, description="Time preference used")
    timezone_used: Optional[str] = Field(None, description="Timezone used for conversion")


# JSON Schema for external integrations (like Retell AI)
BOOK_APPOINTMENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "practice_id": {
            "type": "string",
            "description": "Practice UUID - use the practice_id variable exactly as provided"
        },
        "pet_owner_id": {
            "type": "string", 
            "description": "Pet owner UUID from user lookup"
        },
        "date": {
            "type": "string",
            "description": "Local date for the appointment (e.g., '2025-09-15', '9-15', 'September 15', 'tomorrow')"
        },
        "start_time": {
            "type": "string",
            "description": "Local start time selected by user (e.g., '2:30 PM', '14:30', '7:30 PM')"
        },
        "timezone": {
            "type": "string",
            "description": "Practice timezone (e.g., 'America/New_York', 'US/Pacific', 'US/Mountain')",
            "default": "America/Los_Angeles"
        },
        "service": {
            "type": "string", 
            "description": "Type of service/appointment (e.g., 'General Checkup', 'Vaccination')",
            "default": "General Checkup"
        },
        "pet_names": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of pet names for this appointment (e.g., ['Amira'], ['Winston'], ['Amira', 'Winston']). Optional - all pets included if not specified"
        },
        "notes": {
            "type": "string",
            "description": "Additional notes or special requests"
        },
        "assigned_vet_user_id": {
            "type": "string",
            "description": "Specific vet UUID if requested (optional)"
        }
    },
    "required": ["practice_id", "pet_owner_id", "date", "start_time"]
}

GET_AVAILABLE_TIMES_JSON_SCHEMA = {
    "type": "object", 
    "properties": {
        "date": {
            "type": "string",
            "description": "The date for availability check (e.g., '9-14', 'September 14', 'tomorrow')"
        },
        "practice_id": {
            "type": "string",
            "description": "Practice UUID - use the practice_id variable exactly as provided"
        },
        "time_preference": {
            "type": "string",
            "description": "Time of day preference (e.g., 'morning', 'afternoon', 'evening', 'any time')",
            "default": "any time"
        },
        "timezone": {
            "type": "string", 
            "description": "Practice timezone (e.g., 'America/New_York', 'US/Pacific', 'US/Mountain')",
            "default": "America/Los_Angeles"
        }
    },
    "required": ["date", "practice_id"]
}
