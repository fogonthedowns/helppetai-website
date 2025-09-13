"""
Pydantic schemas for scheduling system - HelpPet MVP
Request/response models for practice hours, vet availability, and conflicts
"""

import uuid
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
import datetime as dt
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseResponse


class AvailabilityType(str, Enum):
    """Types of vet availability"""
    AVAILABLE = "AVAILABLE"
    SURGERY_BLOCK = "SURGERY_BLOCK"
    UNAVAILABLE = "UNAVAILABLE"
    EMERGENCY_ONLY = "EMERGENCY_ONLY"


class ConflictType(str, Enum):
    """Types of appointment conflicts"""
    DOUBLE_BOOKED = "DOUBLE_BOOKED"
    OVERLAPPING = "OVERLAPPING"
    OUTSIDE_AVAILABILITY = "OUTSIDE_AVAILABILITY"
    PRACTICE_CLOSED = "PRACTICE_CLOSED"


class ConflictSeverity(str, Enum):
    """Severity levels for appointment conflicts"""
    WARNING = "WARNING"
    ERROR = "ERROR"


# ============================================================================
# PRACTICE HOURS SCHEMAS
# ============================================================================

class PracticeHoursBase(BaseModel):
    """Base schema for practice hours"""
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Sunday, 6=Saturday)")
    open_time: Optional[dt.time] = Field(None, description="Opening time (null means closed)")
    close_time: Optional[dt.time] = Field(None, description="Closing time (null means closed)")
    effective_from: dt.date = Field(..., description="Date when these hours become effective")
    effective_until: Optional[dt.date] = Field(None, description="Date when these hours end (null = indefinite)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes about hours")
    is_active: bool = Field(True, description="Whether these hours are active")

    @validator('close_time')
    def validate_times(cls, v, values):
        """Validate that both times are provided or both are null"""
        open_time = values.get('open_time')
        if (open_time is None) != (v is None):
            raise ValueError('Both open_time and close_time must be provided or both must be null')
        if open_time and v and open_time >= v:
            raise ValueError('open_time must be before close_time')
        return v

    @validator('effective_until')
    def validate_effective_dates(cls, v, values):
        """Validate that effective_until is after effective_from"""
        effective_from = values.get('effective_from')
        if v and effective_from and v < effective_from:
            raise ValueError('effective_until must be after effective_from')
        return v


class PracticeHoursCreate(PracticeHoursBase):
    """Schema for creating practice hours"""
    practice_id: uuid.UUID = Field(..., description="Practice ID")


class PracticeHoursUpdate(BaseModel):
    """Schema for updating practice hours"""
    open_time: Optional[dt.time] = None
    close_time: Optional[dt.time] = None
    effective_until: Optional[dt.date] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class PracticeHoursResponse(PracticeHoursBase):
    """Schema for practice hours response"""
    id: uuid.UUID
    practice_id: uuid.UUID
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True

    @property
    def day_name(self) -> str:
        """Get day name from day_of_week"""
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        return days[self.day_of_week]

    @property
    def is_closed(self) -> bool:
        """Check if practice is closed this day"""
        return self.open_time is None or self.close_time is None


# ============================================================================
# VET AVAILABILITY SCHEMAS
# ============================================================================

class VetAvailabilityBase(BaseModel):
    """Base schema for vet availability"""
    date: dt.date = Field(..., description="Date of availability")
    start_time: dt.time = Field(..., description="Start time")
    end_time: dt.time = Field(..., description="End time")
    availability_type: AvailabilityType = Field(AvailabilityType.AVAILABLE, description="Type of availability")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    is_active: bool = Field(True, description="Whether this availability is active")

    @validator('end_time')
    def validate_times(cls, v, values):
        """Validate that end_time is after start_time"""
        start_time = values.get('start_time')
        if start_time and v and start_time >= v:
            raise ValueError('start_time must be before end_time')
        return v


class VetAvailabilityCreate(VetAvailabilityBase):
    """Schema for creating vet availability"""
    vet_user_id: uuid.UUID = Field(..., description="Vet user ID")
    practice_id: uuid.UUID = Field(..., description="Practice ID")


class VetAvailabilityUpdate(BaseModel):
    """Schema for updating vet availability"""
    start_time: Optional[dt.time] = None
    end_time: Optional[dt.time] = None
    availability_type: Optional[AvailabilityType] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class VetAvailabilityResponse(VetAvailabilityBase):
    """Schema for vet availability response"""
    id: uuid.UUID
    vet_user_id: uuid.UUID
    practice_id: uuid.UUID
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True

    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes"""
        start_datetime = datetime.combine(dt.date.today(), self.start_time)
        end_datetime = datetime.combine(dt.date.today(), self.end_time)
        return int((end_datetime - start_datetime).total_seconds() / 60)


# ============================================================================
# RECURRING AVAILABILITY SCHEMAS
# ============================================================================

class RecurringAvailabilityBase(BaseModel):
    """Base schema for recurring availability"""
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Sunday, 6=Saturday)")
    start_time: dt.time = Field(..., description="Start time")
    end_time: dt.time = Field(..., description="End time")
    availability_type: AvailabilityType = Field(AvailabilityType.AVAILABLE, description="Type of availability")
    effective_from: dt.date = Field(..., description="Date when this schedule becomes effective")
    effective_until: Optional[dt.date] = Field(None, description="Date when this schedule ends (null = indefinite)")
    is_active: bool = Field(True, description="Whether this schedule is active")

    @validator('end_time')
    def validate_times(cls, v, values):
        """Validate that end_time is after start_time"""
        start_time = values.get('start_time')
        if start_time and v and start_time >= v:
            raise ValueError('start_time must be before end_time')
        return v

    @validator('effective_until')
    def validate_effective_dates(cls, v, values):
        """Validate that effective_until is after effective_from"""
        effective_from = values.get('effective_from')
        if v and effective_from and v < effective_from:
            raise ValueError('effective_until must be after effective_from')
        return v


class RecurringAvailabilityCreate(RecurringAvailabilityBase):
    """Schema for creating recurring availability"""
    vet_user_id: uuid.UUID = Field(..., description="Vet user ID")
    practice_id: uuid.UUID = Field(..., description="Practice ID")


class RecurringAvailabilityUpdate(BaseModel):
    """Schema for updating recurring availability"""
    start_time: Optional[dt.time] = None
    end_time: Optional[dt.time] = None
    availability_type: Optional[AvailabilityType] = None
    effective_until: Optional[dt.date] = None
    is_active: Optional[bool] = None


class RecurringAvailabilityResponse(RecurringAvailabilityBase):
    """Schema for recurring availability response"""
    id: uuid.UUID
    vet_user_id: uuid.UUID
    practice_id: uuid.UUID
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True

    @property
    def day_name(self) -> str:
        """Get day name from day_of_week"""
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        return days[self.day_of_week]


# ============================================================================
# APPOINTMENT CONFLICT SCHEMAS
# ============================================================================

class AppointmentConflictBase(BaseModel):
    """Base schema for appointment conflicts"""
    conflict_type: ConflictType = Field(..., description="Type of conflict")
    severity: ConflictSeverity = Field(ConflictSeverity.WARNING, description="Severity of conflict")
    message: str = Field(..., max_length=1000, description="Conflict description")


class AppointmentConflictCreate(AppointmentConflictBase):
    """Schema for creating appointment conflicts"""
    appointment_id: uuid.UUID = Field(..., description="Appointment ID")
    conflicting_appointment_id: Optional[uuid.UUID] = Field(None, description="Conflicting appointment ID")


class AppointmentConflictUpdate(BaseModel):
    """Schema for updating appointment conflicts"""
    message: Optional[str] = Field(None, max_length=1000)
    severity: Optional[ConflictSeverity] = None


class AppointmentConflictResolve(BaseModel):
    """Schema for resolving conflicts"""
    resolved_by_user_id: uuid.UUID = Field(..., description="User who resolved the conflict")


class AppointmentConflictResponse(AppointmentConflictBase):
    """Schema for appointment conflict response"""
    id: uuid.UUID
    appointment_id: uuid.UUID
    conflicting_appointment_id: Optional[uuid.UUID]
    resolved: bool
    resolved_by_user_id: Optional[uuid.UUID]
    resolved_at: Optional[datetime]
    created_at: dt.datetime

    class Config:
        from_attributes = True


# ============================================================================
# SCHEDULING QUERY SCHEMAS
# ============================================================================

class AvailableSlotRequest(BaseModel):
    """Schema for requesting available appointment slots"""
    practice_id: uuid.UUID = Field(..., description="Practice ID")
    vet_user_id: Optional[uuid.UUID] = Field(None, description="Specific vet (optional)")
    date: dt.date = Field(..., description="Date to check availability")
    duration_minutes: int = Field(30, ge=15, le=480, description="Appointment duration in minutes")
    appointment_type: Optional[str] = Field(None, description="Type of appointment")


class AvailableSlot(BaseModel):
    """Schema for available appointment slot"""
    vet_user_id: uuid.UUID
    vet_name: str
    start_time: dt.time
    end_time: dt.time
    availability_type: AvailabilityType
    duration_minutes: int


class AvailableSlotsResponse(BaseResponse):
    """Schema for available slots response"""
    slots: List[AvailableSlot] = Field(..., description="Available appointment slots")
    date: dt.date = Field(..., description="Date of availability")
    practice_id: uuid.UUID = Field(..., description="Practice ID")


class ConflictCheckRequest(BaseModel):
    """Schema for checking appointment conflicts"""
    appointment_id: uuid.UUID = Field(..., description="Appointment to check")
    vet_user_id: uuid.UUID = Field(..., description="Assigned vet")
    appointment_date: dt.datetime = Field(..., description="Appointment date and time")
    duration_minutes: int = Field(..., description="Appointment duration")


class ConflictCheckResponse(BaseResponse):
    """Schema for conflict check response"""
    has_conflicts: bool = Field(..., description="Whether conflicts were found")
    conflicts: List[AppointmentConflictResponse] = Field(..., description="List of conflicts")


# ============================================================================
# BULK OPERATIONS SCHEMAS
# ============================================================================

class BulkPracticeHoursCreate(BaseModel):
    """Schema for creating multiple practice hours"""
    practice_id: uuid.UUID = Field(..., description="Practice ID")
    hours: List[PracticeHoursBase] = Field(..., description="List of practice hours")


class BulkRecurringAvailabilityCreate(BaseModel):
    """Schema for creating multiple recurring availability records"""
    vet_user_id: uuid.UUID = Field(..., description="Vet user ID")
    practice_id: uuid.UUID = Field(..., description="Practice ID")
    schedules: List[RecurringAvailabilityBase] = Field(..., description="List of recurring schedules")


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class ConflictStatistics(BaseModel):
    """Schema for conflict statistics"""
    total_conflicts: int
    unresolved_conflicts: int
    resolved_conflicts: int
    conflicts_by_type: Dict[str, int]
    conflicts_by_severity: Dict[str, int]


class SchedulingStatistics(BaseModel):
    """Schema for scheduling statistics"""
    practice_id: uuid.UUID
    date_range: str
    total_appointments: int
    available_slots: int
    utilization_rate: float
    conflicts: ConflictStatistics
