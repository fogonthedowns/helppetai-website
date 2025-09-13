"""
Scheduling models for PostgreSQL - HelpPet MVP
Practice hours, vet availability, and appointment conflict tracking
"""

import uuid
from datetime import datetime, date, time
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, Text, UUID, ForeignKey, Date, Time, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base

if TYPE_CHECKING:
    from .practice import VeterinaryPractice
    from .user import User
    from .appointment import Appointment


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


class PracticeHours(Base):
    """Practice operating hours - hard constraint for scheduling"""
    
    __tablename__ = "practice_hours"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to practice
    practice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("veterinary_practices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Day of week (0=Sunday, 6=Saturday)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Operating hours (NULL means closed all day)
    open_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    close_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    
    # Effective date range
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    effective_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Additional info
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    practice: Mapped["VeterinaryPractice"] = relationship("VeterinaryPractice")
    
    def __repr__(self) -> str:
        return f"<PracticeHours(id={self.id}, practice_id={self.practice_id}, day={self.day_of_week}, {self.open_time}-{self.close_time})>"
    
    @property
    def is_closed(self) -> bool:
        """Check if practice is closed this day"""
        return self.open_time is None or self.close_time is None
    
    @property
    def day_name(self) -> str:
        """Get day name from day_of_week"""
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        return days[self.day_of_week]
    
    def is_time_within_hours(self, check_time: time) -> bool:
        """Check if a time falls within operating hours"""
        if self.is_closed:
            return False
        return self.open_time <= check_time <= self.close_time


class VetAvailability(Base):
    """Individual vet availability for specific dates"""
    
    __tablename__ = "vet_availability"
    
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
    
    # Availability details
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
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
        return f"<VetAvailability(id={self.id}, vet_id={self.vet_user_id}, date={self.date}, {self.start_time}-{self.end_time}, type={self.availability_type})>"
    
    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes"""
        start_datetime = datetime.combine(date.today(), self.start_time)
        end_datetime = datetime.combine(date.today(), self.end_time)
        return int((end_datetime - start_datetime).total_seconds() / 60)
    
    def is_available_for_appointment(self) -> bool:
        """Check if this availability allows regular appointments"""
        return self.availability_type in [AvailabilityType.AVAILABLE, AvailabilityType.EMERGENCY_ONLY]
    
    def overlaps_with_time(self, start: time, end: time) -> bool:
        """Check if this availability overlaps with given time range"""
        return not (end <= self.start_time or start >= self.end_time)


class RecurringAvailability(Base):
    """Templates for generating regular vet schedules"""
    
    __tablename__ = "recurring_availability"
    
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
    
    # Recurring schedule details
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 0=Sunday, 6=Saturday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    availability_type: Mapped[AvailabilityType] = mapped_column(
        SQLEnum(AvailabilityType), 
        nullable=False, 
        default=AvailabilityType.AVAILABLE
    )
    
    # Effective date range
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    effective_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    vet: Mapped["User"] = relationship("User")
    practice: Mapped["VeterinaryPractice"] = relationship("VeterinaryPractice")
    
    def __repr__(self) -> str:
        return f"<RecurringAvailability(id={self.id}, vet_id={self.vet_user_id}, day={self.day_of_week}, {self.start_time}-{self.end_time})>"
    
    @property
    def day_name(self) -> str:
        """Get day name from day_of_week"""
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        return days[self.day_of_week]
    
    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes"""
        start_datetime = datetime.combine(date.today(), self.start_time)
        end_datetime = datetime.combine(date.today(), self.end_time)
        return int((end_datetime - start_datetime).total_seconds() / 60)
    
    def is_effective_on_date(self, check_date: date) -> bool:
        """Check if this recurring schedule is effective on a given date"""
        if check_date < self.effective_from:
            return False
        if self.effective_until and check_date > self.effective_until:
            return False
        return True


class AppointmentConflict(Base):
    """Tracks scheduling conflicts for staff review"""
    
    __tablename__ = "appointment_conflict"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    conflicting_appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Conflict details
    conflict_type: Mapped[ConflictType] = mapped_column(SQLEnum(ConflictType), nullable=False)
    severity: Mapped[ConflictSeverity] = mapped_column(
        SQLEnum(ConflictSeverity), 
        nullable=False, 
        default=ConflictSeverity.WARNING
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Resolution tracking
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id"),
        nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    appointment: Mapped["Appointment"] = relationship("Appointment", foreign_keys=[appointment_id])
    conflicting_appointment: Mapped[Optional["Appointment"]] = relationship(
        "Appointment", 
        foreign_keys=[conflicting_appointment_id]
    )
    resolved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[resolved_by_user_id])
    
    def __repr__(self) -> str:
        return f"<AppointmentConflict(id={self.id}, appointment_id={self.appointment_id}, type={self.conflict_type}, severity={self.severity}, resolved={self.resolved})>"
    
    def resolve(self, resolved_by_user_id: uuid.UUID) -> None:
        """Mark conflict as resolved"""
        self.resolved = True
        self.resolved_by_user_id = resolved_by_user_id
        self.resolved_at = datetime.utcnow()
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error-level conflict"""
        return self.severity == ConflictSeverity.ERROR
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning-level conflict"""
        return self.severity == ConflictSeverity.WARNING
