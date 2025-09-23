"""
REFACTORED Scheduling models using Unix timestamps - HelpPet MVP
Following the recommendations in suggestion.txt for timezone handling

Key changes:
- Replace date + start_time + end_time with start_at + end_at TIMESTAMPTZ
- Store everything in UTC using Unix timestamps 
- Convert at boundaries only (input/output)
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, UUID, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum
import pytz

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base

if TYPE_CHECKING:
    from .practice import VeterinaryPractice
    from .user import User


class AvailabilityType(str, Enum):
    """Types of vet availability"""
    AVAILABLE = "AVAILABLE"
    SURGERY_BLOCK = "SURGERY_BLOCK"
    UNAVAILABLE = "UNAVAILABLE"
    EMERGENCY_ONLY = "EMERGENCY_ONLY"


class VetAvailability(Base):
    """
    REFACTORED: Individual vet availability using Unix timestamps
    
    🔑 KEY DESIGN PRINCIPLES (from suggestion.txt):
    1. Store everything in UTC using TIMESTAMPTZ
    2. No more separate date/time fields = no more phantom shifts
    3. Parse voice input to timezone-aware datetime, convert to UTC, store as Unix timestamp
    4. For display: Unix timestamp -> UTC datetime -> local timezone -> human format
    """
    
    __tablename__ = "vet_availability_unix"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    vet_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    practice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("veterinary_practices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 🎯 UNIX TIMESTAMP FIELDS - The ultimate fix!
    # Store as UTC timestamps - no ambiguity, easy to compare/query
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        index=True,
        comment="UTC timestamp when availability starts"
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        index=True,
        comment="UTC timestamp when availability ends"
    )
    
    # Availability type
    availability_type: Mapped[AvailabilityType] = mapped_column(
        SQLEnum(AvailabilityType), 
        nullable=False, 
        default=AvailabilityType.AVAILABLE
    )
    
    # Additional info
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    vet: Mapped["User"] = relationship("User")
    practice: Mapped["VeterinaryPractice"] = relationship("VeterinaryPractice")
    
    def __repr__(self) -> str:
        return f"<VetAvailability(id={self.id}, vet_id={self.vet_user_id}, start_at={self.start_at}, end_at={self.end_at}, type={self.availability_type})>"
    
    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes"""
        return int((self.end_at - self.start_at).total_seconds() / 60)
    
    def is_available_for_appointment(self) -> bool:
        """Check if this availability allows regular appointments"""
        return self.availability_type in [AvailabilityType.AVAILABLE, AvailabilityType.EMERGENCY_ONLY]
    
    def to_local_timezone(self, timezone_str: str) -> tuple[datetime, datetime]:
        """
        Convert UTC timestamps to local timezone
        
        Args:
            timezone_str: Target timezone (e.g., 'America/Los_Angeles')
            
        Returns:
            tuple: (local_start, local_end) as timezone-aware datetimes
        """
        tz = pytz.timezone(timezone_str)
        local_start = self.start_at.astimezone(tz)
        local_end = self.end_at.astimezone(tz)
        return local_start, local_end
    
    def get_local_date(self, timezone_str: str) -> datetime.date:
        """
        Get the local date this availability represents
        
        Args:
            timezone_str: Target timezone (e.g., 'America/Los_Angeles')
            
        Returns:
            The local date in the specified timezone
        """
        local_start, _ = self.to_local_timezone(timezone_str)
        return local_start.date()
    
    def overlaps_with_utc_range(self, utc_start: datetime, utc_end: datetime) -> bool:
        """
        Check if this availability overlaps with a UTC time range
        
        Args:
            utc_start: UTC start time
            utc_end: UTC end time
            
        Returns:
            True if there's overlap
        """
        return not (utc_end <= self.start_at or utc_start >= self.end_at)
    
    @classmethod
    def from_voice_input(
        cls, 
        vet_user_id: uuid.UUID,
        practice_id: uuid.UUID,
        local_date_str: str,
        local_start_time_str: str, 
        local_end_time_str: str,
        timezone_str: str,
        availability_type: AvailabilityType = AvailabilityType.AVAILABLE,
        notes: Optional[str] = None
    ) -> 'VetAvailability':
        """
        🎯 CREATE FROM VOICE INPUT - The canonical way!
        
        This follows the exact flow from suggestion.txt:
        1. Parse natural language input with timezone
        2. Convert to UTC timestamp
        3. Store in DB
        
        Args:
            local_date_str: "Oct 3, 2025" or "2025-10-03"
            local_start_time_str: "9pm" or "21:00"
            local_end_time_str: "5pm" or "17:00"
            timezone_str: "America/Los_Angeles"
            
        Returns:
            VetAvailability instance ready for DB storage
        """
        from dateutil import parser
        from zoneinfo import ZoneInfo
        
        # Parse the input with timezone context
        tz = ZoneInfo(timezone_str)
        
        # Parse date and times
        if local_date_str.lower() in ['today', 'tomorrow']:
            # Handle relative dates
            today = datetime.now(tz).date()
            if local_date_str.lower() == 'today':
                local_date = today
            else:  # tomorrow
                local_date = today + timedelta(days=1)
        else:
            # Parse date string
            parsed_date = parser.parse(local_date_str)
            local_date = parsed_date.date()
        
        # Parse times
        start_time = parser.parse(local_start_time_str).time()
        end_time = parser.parse(local_end_time_str).time()
        
        # Create timezone-aware local datetimes
        local_start_dt = datetime.combine(local_date, start_time).replace(tzinfo=tz)
        local_end_dt = datetime.combine(local_date, end_time).replace(tzinfo=tz)
        
        # Convert to UTC for storage
        utc_start = local_start_dt.astimezone(pytz.UTC)
        utc_end = local_end_dt.astimezone(pytz.UTC)
        
        return cls(
            vet_user_id=vet_user_id,
            practice_id=practice_id,
            start_at=utc_start,
            end_at=utc_end,
            availability_type=availability_type,
            notes=notes
        )


class AppointmentUnix(Base):
    """
    REFACTORED: Appointment model using Unix timestamp
    
    🔑 Same principle: store appointment_at as UTC timestamp
    """
    
    __tablename__ = "appointments_unix"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    practice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("veterinary_practices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    pet_owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("pet_owners.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    assigned_vet_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )
    
    # 🎯 UNIX TIMESTAMP - Single source of truth for appointment time
    appointment_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        index=True,
        comment="UTC timestamp when appointment is scheduled"
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    
    # Appointment details
    appointment_type: Mapped[str] = mapped_column(String(50), nullable=False, default="CHECKUP")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="SCHEDULED", index=True)
    
    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, title='{self.title}', appointment_at={self.appointment_at}, status={self.status})>"
    
    @property
    def end_at(self) -> datetime:
        """Calculate when appointment ends"""
        return self.appointment_at + timedelta(minutes=self.duration_minutes)
    
    def to_local_timezone(self, timezone_str: str) -> datetime:
        """Convert UTC appointment time to local timezone"""
        tz = pytz.timezone(timezone_str)
        return self.appointment_at.astimezone(tz)
    
    def overlaps_with_utc_range(self, utc_start: datetime, utc_end: datetime) -> bool:
        """Check if appointment overlaps with a UTC time range"""
        appointment_end = self.end_at
        return not (utc_end <= self.appointment_at or utc_start >= appointment_end)
    
    @classmethod
    def from_voice_booking(
        cls,
        practice_id: uuid.UUID,
        pet_owner_id: uuid.UUID,
        assigned_vet_user_id: uuid.UUID,
        created_by_user_id: uuid.UUID,
        local_date_str: str,
        local_time_str: str,
        timezone_str: str,
        duration_minutes: int = 30,
        title: str = "Veterinary Appointment",
        appointment_type: str = "CHECKUP",
        notes: Optional[str] = None
    ) -> 'AppointmentUnix':
        """
        🎯 CREATE APPOINTMENT FROM VOICE INPUT
        
        Args:
            local_date_str: "Oct 3, 2025" 
            local_time_str: "9pm"
            timezone_str: "America/Los_Angeles"
            
        Returns:
            Appointment instance ready for DB storage
        """
        from dateutil import parser
        from zoneinfo import ZoneInfo
        
        # Parse with timezone context
        tz = ZoneInfo(timezone_str)
        
        # Parse date and time
        parsed_date = parser.parse(local_date_str).date()
        parsed_time = parser.parse(local_time_str).time()
        
        # Create timezone-aware local datetime
        local_dt = datetime.combine(parsed_date, parsed_time).replace(tzinfo=tz)
        
        # Convert to UTC for storage
        utc_dt = local_dt.astimezone(pytz.UTC)
        
        return cls(
            practice_id=practice_id,
            pet_owner_id=pet_owner_id,
            assigned_vet_user_id=assigned_vet_user_id,
            created_by_user_id=created_by_user_id,
            appointment_at=utc_dt,
            duration_minutes=duration_minutes,
            title=title,
            appointment_type=appointment_type,
            notes=notes
        )


# 🔄 MIGRATION HELPER FUNCTIONS

def migrate_old_availability_to_unix(
    old_availability,  # Old VetAvailability record with date/time fields
    practice_timezone: str
) -> VetAvailability:
    """
    Helper to migrate old date+time records to Unix timestamp format
    
    Args:
        old_availability: Old VetAvailability with date, start_time, end_time
        practice_timezone: Practice timezone string
        
    Returns:
        New VetAvailability with Unix timestamps
    """
    import pytz
    
    # Get practice timezone
    tz = pytz.timezone(practice_timezone)
    
    # Combine old date + time into local datetime
    local_start = tz.localize(
        datetime.combine(old_availability.date, old_availability.start_time)
    )
    local_end = tz.localize(
        datetime.combine(old_availability.date, old_availability.end_time)
    )
    
    # Convert to UTC
    utc_start = local_start.astimezone(pytz.UTC)
    utc_end = local_end.astimezone(pytz.UTC)
    
    return VetAvailability(
        id=old_availability.id,  # Keep same ID
        vet_user_id=old_availability.vet_user_id,
        practice_id=old_availability.practice_id,
        start_at=utc_start,
        end_at=utc_end,
        availability_type=old_availability.availability_type,
        notes=old_availability.notes,
        is_active=old_availability.is_active,
        created_at=old_availability.created_at,
        updated_at=old_availability.updated_at
    )


def migrate_old_appointment_to_unix(
    old_appointment,  # Old Appointment with appointment_date
    practice_timezone: str
) -> AppointmentUnix:
    """
    Helper to migrate old appointment_date to Unix timestamp format
    """
    import pytz
    
    # Old appointment_date should already be UTC, but let's be safe
    if old_appointment.appointment_date.tzinfo is None:
        # Assume it's in practice timezone if no timezone info
        tz = pytz.timezone(practice_timezone)
        local_dt = tz.localize(old_appointment.appointment_date)
        utc_dt = local_dt.astimezone(pytz.UTC)
    else:
        # Already has timezone info, convert to UTC
        utc_dt = old_appointment.appointment_date.astimezone(pytz.UTC)
    
    return AppointmentUnix(
        id=old_appointment.id,  # Keep same ID
        practice_id=old_appointment.practice_id,
        pet_owner_id=old_appointment.pet_owner_id,
        assigned_vet_user_id=old_appointment.assigned_vet_user_id,
        created_by_user_id=old_appointment.created_by_user_id,
        appointment_at=utc_dt,
        duration_minutes=old_appointment.duration_minutes,
        appointment_type=old_appointment.appointment_type,
        status=old_appointment.status,
        title=old_appointment.title,
        description=old_appointment.description,
        notes=old_appointment.notes,
        created_at=old_appointment.created_at,
        updated_at=old_appointment.updated_at
    )


# Backward compatibility for older imports expecting `Appointment`
# Some modules may still do: from .scheduling_unix import Appointment
# Provide alias to prevent ImportError during transition
Appointment = AppointmentUnix
