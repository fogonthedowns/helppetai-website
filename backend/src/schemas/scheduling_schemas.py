"""
Pydantic schemas for scheduling system - HelpPet MVP
Request/response models for practice hours, vet availability, and conflicts
"""

import uuid
import re
import pytz
from datetime import datetime, date, time, timedelta
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

    @validator('start_time', pre=True)
    def parse_start_time(cls, v):
        """Parse start_time from string if needed (iOS compatibility)"""
        if isinstance(v, str):
            return cls._parse_time_string(v)
        return v

    @validator('end_time', pre=True)
    def parse_end_time(cls, v):
        """Parse end_time from string if needed (iOS compatibility)"""
        if isinstance(v, str):
            return cls._parse_time_string(v)
        return v

    @validator('end_time')
    def validate_times(cls, v, values):
        """Validate that end_time is after start_time, handling overnight and boundary cases"""
        start_time = values.get('start_time')
        if start_time and v:
            # Case 1: Normal same-day times (9am-5pm)
            if start_time < v:
                return v
            
            # Case 2: Overnight times (11pm-3am) - end_time < start_time indicates next day
            # This is valid for overnight shifts, 24-hour operations, etc.
            if v < start_time:
                # End time is earlier in the day = next day
                # Examples: 23:00-03:00 (11pm-3am), 22:00-01:00 (10pm-1am)
                return v
            
            # Case 3: Same time (start_time == end_time)
            if start_time == v:
                # Only allow if it's midnight (represents 24-hour period)
                if v == dt.time(0, 0):
                    return v  # 00:00-00:00 = 24 hours
                else:
                    raise ValueError('start_time must be before end_time (same times only allowed for midnight 24-hour periods)')
        
        return v

    @staticmethod
    def _parse_time_string(time_str: str) -> dt.time:
        """
        Parse time string from various formats (iOS compatibility)
        Supports: HH:MM:SS, HH:MM, H:MM AM/PM, HH:MM AM/PM
        """
        if not time_str:
            raise ValueError("Time string cannot be empty")
        
        time_str = time_str.strip().upper()
        
        try:
            # Handle ISO time format: HH:MM:SS or HH:MM:SS.ffffff
            iso_match = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.(\d+))?$', time_str)
            if iso_match:
                hour = int(iso_match.group(1))
                minute = int(iso_match.group(2))
                second = int(iso_match.group(3) or 0)
                
                if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                    return dt.time(hour=hour, minute=minute, second=second)
            
            # Handle 12-hour format with AM/PM: "9:00 AM", "2:30 PM"
            twelve_hour_match = re.match(r'^(\d{1,2}):(\d{2})\s*(AM|PM)$', time_str)
            if twelve_hour_match:
                hour = int(twelve_hour_match.group(1))
                minute = int(twelve_hour_match.group(2))
                period = twelve_hour_match.group(3)
                
                # Convert to 24-hour format
                if period == 'AM':
                    if hour == 12:
                        hour = 0
                else:  # PM
                    if hour != 12:
                        hour += 12
                
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return dt.time(hour=hour, minute=minute)
            
            # Handle hour-only format: "9 AM", "2 PM"
            hour_only_match = re.match(r'^(\d{1,2})\s*(AM|PM)$', time_str)
            if hour_only_match:
                hour = int(hour_only_match.group(1))
                period = hour_only_match.group(2)
                
                # Convert to 24-hour format
                if period == 'AM':
                    if hour == 12:
                        hour = 0
                else:  # PM
                    if hour != 12:
                        hour += 12
                
                if 0 <= hour <= 23:
                    return dt.time(hour=hour, minute=0)
            
            raise ValueError(f"Unable to parse time format: {time_str}")
            
        except Exception as e:
            raise ValueError(f"Invalid time format '{time_str}': {str(e)}")


class VetAvailabilityCreate(VetAvailabilityBase):
    """Schema for creating vet availability with timezone support"""
    vet_user_id: uuid.UUID = Field(..., description="Vet user ID")
    practice_id: uuid.UUID = Field(..., description="Practice ID")
    timezone: Optional[str] = Field(
        default="America/Los_Angeles", 
        description="Timezone for the availability (e.g., 'America/Los_Angeles', 'America/New_York')"
    )
    
    @validator('date', pre=True)
    def parse_date(cls, v):
        """Parse date from string if needed (iOS compatibility)"""
        if isinstance(v, str):
            return cls._parse_date_string(v)
        return v
    
    @staticmethod
    def _parse_date_string(date_str: str) -> dt.date:
        """
        Parse date string from various formats (iOS compatibility)
        Supports: YYYY-MM-DD, MM-DD-YYYY, MM/DD/YYYY
        """
        if not date_str:
            raise ValueError("Date string cannot be empty")
        
        date_str = date_str.strip()
        
        try:
            # Handle ISO date format: YYYY-MM-DD
            iso_match = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})$', date_str)
            if iso_match:
                year = int(iso_match.group(1))
                month = int(iso_match.group(2))
                day = int(iso_match.group(3))
                return dt.date(year, month, day)
            
            # Handle US date formats: MM/DD/YYYY or MM-DD-YYYY
            us_match = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', date_str)
            if us_match:
                month = int(us_match.group(1))
                day = int(us_match.group(2))
                year = int(us_match.group(3))
                return dt.date(year, month, day)
            
            # Handle short date formats: MM/DD or MM-DD (assume current year)
            short_match = re.match(r'^(\d{1,2})[/-](\d{1,2})$', date_str)
            if short_match:
                month = int(short_match.group(1))
                day = int(short_match.group(2))
                year = datetime.now().year
                return dt.date(year, month, day)
            
            raise ValueError(f"Unable to parse date format: {date_str}")
            
        except ValueError as e:
            if "Unable to parse" in str(e):
                raise e
            raise ValueError(f"Invalid date format '{date_str}': {str(e)}")
    
    def to_utc_datetime_range(self) -> tuple[datetime, datetime]:
        """
        Convert local date/time to UTC datetime range, handling date boundary shifts
        
        Returns:
            tuple[datetime, datetime]: (start_datetime_utc, end_datetime_utc)
        """
        try:
            # Get the timezone
            tz = pytz.timezone(self.timezone)
            
            # Create local datetime objects
            local_start = tz.localize(datetime.combine(self.date, self.start_time))
            
            # Handle overnight times correctly
            # If end_time <= start_time, it represents next day (overnight shift)
            if self.end_time <= self.start_time:
                # End time is next day (midnight, or overnight like 11pm-3am)
                next_day = self.date + timedelta(days=1)
                local_end = tz.localize(datetime.combine(next_day, self.end_time))
            else:
                # Normal case - same day (9am-5pm)
                local_end = tz.localize(datetime.combine(self.date, self.end_time))
            
            # Convert to UTC
            utc_start = local_start.astimezone(pytz.UTC)
            utc_end = local_end.astimezone(pytz.UTC)
            
            return utc_start, utc_end
            
        except pytz.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {self.timezone}")
        except Exception as e:
            raise ValueError(f"Error converting to UTC: {str(e)}")
    
    def get_local_datetime_range(self) -> tuple[datetime, datetime]:
        """
        Get the local datetime range (for logging/debugging)
        
        Returns:
            tuple[datetime, datetime]: (start_datetime_local, end_datetime_local)
        """
        try:
            tz = pytz.timezone(self.timezone)
            local_start = tz.localize(datetime.combine(self.date, self.start_time))
            
            # Handle overnight times correctly
            # If end_time <= start_time, it represents next day (overnight shift)
            if self.end_time <= self.start_time:
                # End time is next day (midnight, or overnight like 11pm-3am)
                next_day = self.date + timedelta(days=1)
                local_end = tz.localize(datetime.combine(next_day, self.end_time))
            else:
                # Normal case - same day (9am-5pm)
                local_end = tz.localize(datetime.combine(self.date, self.end_time))
            
            return local_start, local_end
        except Exception as e:
            raise ValueError(f"Error getting local datetime: {str(e)}")
    
    def detect_date_boundary_shift(self) -> Dict[str, Any]:
        """
        Detect if timezone conversion causes date boundary shifts
        
        Returns:
            Dict with shift information for logging/debugging
        """
        try:
            utc_start, utc_end = self.to_utc_datetime_range()
            local_start, local_end = self.get_local_datetime_range()
            
            start_date_shifted = utc_start.date() != local_start.date()
            end_date_shifted = utc_end.date() != local_end.date()
            
            return {
                "original_date": self.date.isoformat(),
                "local_start": local_start.isoformat(),
                "local_end": local_end.isoformat(),
                "utc_start": utc_start.isoformat(),
                "utc_end": utc_end.isoformat(),
                "start_date_shifted": start_date_shifted,
                "end_date_shifted": end_date_shifted,
                "timezone": self.timezone,
                "utc_start_date": utc_start.date().isoformat(),
                "utc_end_date": utc_end.date().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    class Config:
        # Allow extra fields for timezone handling
        extra = "forbid"
        schema_extra = {
            "example": {
                "vet_user_id": "123e4567-e89b-12d3-a456-426614174000",
                "practice_id": "123e4567-e89b-12d3-a456-426614174001", 
                "date": "2025-09-23",
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "timezone": "America/Los_Angeles",
                "availability_type": "AVAILABLE",
                "notes": "Regular office hours",
                "is_active": True
            }
        }


class VetAvailabilityUpdate(BaseModel):
    """Schema for updating vet availability"""
    start_time: Optional[dt.time] = None
    end_time: Optional[dt.time] = None
    availability_type: Optional[AvailabilityType] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class VetAvailabilityResponse(BaseModel):
    """Schema for vet availability response - inherits from BaseModel to avoid time validation"""
    id: uuid.UUID
    vet_user_id: uuid.UUID
    practice_id: uuid.UUID
    date: dt.date = Field(..., description="Date of availability")
    start_time: dt.time = Field(..., description="Start time")
    end_time: dt.time = Field(..., description="End time")
    availability_type: AvailabilityType = Field(AvailabilityType.AVAILABLE, description="Type of availability")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    is_active: bool = Field(True, description="Whether this availability is active")
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


class TimeSlot(BaseModel):
    """Schema for individual time slot with availability status"""
    start_time: dt.time = Field(..., description="Slot start time")
    end_time: dt.time = Field(..., description="Slot end time")
    available: bool = Field(..., description="Whether this slot is available for booking")
    availability_type: AvailabilityType = Field(..., description="Type of availability")
    conflicting_appointment: Optional[str] = Field(None, description="Title of conflicting appointment if any")
    notes: Optional[str] = Field(None, description="Additional notes about availability")


class VetAvailabilitySlots(BaseModel):
    """Schema for vet availability broken down into bookable slots"""
    vet_user_id: uuid.UUID = Field(..., description="Vet user ID")
    date: dt.date = Field(..., description="Date of availability")
    practice_id: uuid.UUID = Field(..., description="Practice ID")
    slots: List[TimeSlot] = Field(..., description="Available time slots")
    total_slots: int = Field(..., description="Total number of slots")
    available_slots: int = Field(..., description="Number of available slots")


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
