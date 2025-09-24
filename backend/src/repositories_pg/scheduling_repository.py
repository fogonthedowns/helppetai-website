"""
Scheduling repositories for PostgreSQL - HelpPet MVP
Repositories for practice hours, vet availability, and appointment conflicts
"""

import uuid
from datetime import date, time, datetime
from datetime import timedelta

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, text, func
from sqlalchemy.orm import selectinload
import pytz
import logging

from .base_repository import BaseRepository
from ..models_pg.scheduling import (
    PracticeHours, VetAvailability, RecurringAvailability, AppointmentConflict,
    AvailabilityType, ConflictType, ConflictSeverity
)
from ..models_pg.practice import VeterinaryPractice
logger = logging.getLogger(__name__)


class PracticeHoursRepository(BaseRepository[PracticeHours]):
    """Repository for PracticeHours operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(PracticeHours, session)
    
    async def get_by_practice_id(self, practice_id: uuid.UUID, include_inactive: bool = False) -> List[PracticeHours]:
        """Get all practice hours for a practice"""
        query = select(PracticeHours).where(PracticeHours.practice_id == practice_id)
        
        if not include_inactive:
            query = query.where(PracticeHours.is_active == True)
        
        query = query.order_by(PracticeHours.day_of_week, PracticeHours.effective_from)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_current_hours_for_date(self, practice_id: uuid.UUID, check_date: date) -> Optional[PracticeHours]:
        """Get practice hours for a specific date"""
        day_of_week = check_date.weekday() + 1  # Convert to 1-7 (Monday=1, Sunday=7)
        if day_of_week == 7:  # Sunday
            day_of_week = 0
        
        query = select(PracticeHours).where(
            and_(
                PracticeHours.practice_id == practice_id,
                PracticeHours.day_of_week == day_of_week,
                PracticeHours.is_active == True,
                PracticeHours.effective_from <= check_date,
                or_(
                    PracticeHours.effective_until.is_(None),
                    PracticeHours.effective_until >= check_date
                )
            )
        ).order_by(PracticeHours.effective_from.desc())
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def is_practice_open(self, practice_id: uuid.UUID, check_datetime: datetime) -> bool:
        """Check if practice is open at a specific datetime"""
        check_date = check_datetime.date()
        check_time = check_datetime.time()
        
        hours = await self.get_current_hours_for_date(practice_id, check_date)
        if not hours or hours.is_closed:
            return False
        
        return hours.is_time_within_hours(check_time)


class VetAvailabilityRepository(BaseRepository[VetAvailability]):
    """Repository for VetAvailability operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(VetAvailability, session)
    
    async def get_by_vet_and_date(self, vet_user_id: uuid.UUID, date: date, include_inactive: bool = False, timezone_str: str = "America/Los_Angeles") -> List[VetAvailability]:
        """
        Get all availability records for a vet on a specific LOCAL date
        
        CRITICAL: This method now handles timezone boundaries correctly.
        When querying a local date, it checks multiple UTC dates because:
        - Morning times (9am PST) are stored on same UTC date
        - Evening times (5pm PST) are stored on next UTC date
        
        Args:
            vet_user_id: The vet to query for
            date: LOCAL date to query (e.g., Sept 26 in user's timezone)
            include_inactive: Whether to include inactive records
            timezone_str: Timezone for the query (e.g., "America/Los_Angeles")
        
        Returns:
            All availability records that represent the given local date
        """
        from ..utils.timezone_utils import TimezoneHandler
        from datetime import time as dt_time
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 TIMEZONE-AWARE QUERY: vet={vet_user_id}, local_date={date}, timezone={timezone_str}")
        
        # Calculate which UTC dates might contain records for this local date
        test_times = [
            dt_time(0, 0),   # Start of local day
            dt_time(12, 0),  # Middle of local day  
            dt_time(23, 59)  # End of local day
        ]
        
        utc_dates_to_check = set()
        for test_time in test_times:
            try:
                utc_dt = TimezoneHandler.convert_to_utc(date, test_time, timezone_str)
                utc_dates_to_check.add(utc_dt.date())
            except Exception as e:
                logger.warning(f"⚠️ Timezone conversion error for {test_time}: {e}")
                # Fallback to original date
                utc_dates_to_check.add(date)
        
        logger.info(f"🔍 Checking UTC dates: {sorted(utc_dates_to_check)}")
        
        # Query all relevant UTC dates
        query = select(VetAvailability).where(
            and_(
                VetAvailability.vet_user_id == vet_user_id,
                VetAvailability.date.in_(list(utc_dates_to_check))
            )
        )
        
        if not include_inactive:
            query = query.where(VetAvailability.is_active == True)
        
        query = query.order_by(VetAvailability.date, VetAvailability.start_time)
        
        result = await self.session.execute(query)
        all_records = list(result.scalars().all())
        
        logger.info(f"✅ Found {len(all_records)} total records across UTC dates")
        
        # CRITICAL: Filter to only include records that actually represent the target local date
        # Convert each record back to local time and verify it falls on the target date
        filtered_records = []
        
        for record in all_records:
            try:
                # Convert UTC record back to local time to check if it belongs to target date
                utc_start_dt = TimezoneHandler.create_local_datetime(record.date, record.start_time, "UTC")
                local_start_dt = utc_start_dt.astimezone(pytz.timezone(timezone_str))
                
                # Check if this record actually represents the target local date
                if local_start_dt.date() == date:
                    filtered_records.append(record)
                    logger.info(f"  ✅ Record {record.id[:8]} belongs to {date}: UTC {record.date} {record.start_time} → Local {local_start_dt.date()} {local_start_dt.time()}")
                else:
                    logger.info(f"  ❌ Record {record.id[:8]} does NOT belong to {date}: UTC {record.date} {record.start_time} → Local {local_start_dt.date()} {local_start_dt.time()}")
            except Exception as e:
                logger.warning(f"  ⚠️ Error filtering record {record.id[:8]}: {e}")
                # Include record if we can't verify (safer)
                filtered_records.append(record)
        
        logger.info(f"✅ After filtering: {len(filtered_records)} records actually belong to {date}")
        
        # CRITICAL: If no records belong to the target date, return empty immediately
        # This prevents generating artificial slots from records that represent other dates
        if len(filtered_records) == 0:
            logger.info(f"✅ NO AVAILABILITY RECORDS for local date {date} - this is normal if no slots are scheduled")
            return []
        
        return filtered_records
    
    async def get_by_practice_and_date_range(
        self, 
        practice_id: uuid.UUID, 
        start_date: date, 
        end_date: date,
        availability_types: Optional[List[AvailabilityType]] = None
    ) -> List[VetAvailability]:
        """Get availability for all vets in a practice within date range"""
        query = select(VetAvailability).where(
            and_(
                VetAvailability.practice_id == practice_id,
                VetAvailability.date >= start_date,
                VetAvailability.date <= end_date,
                VetAvailability.is_active == True
            )
        )
        
        if availability_types:
            query = query.where(VetAvailability.availability_type.in_(availability_types))
        
        query = query.order_by(VetAvailability.date, VetAvailability.vet_user_id, VetAvailability.start_time)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def find_overlapping_availability(
        self, 
        vet_user_id: uuid.UUID, 
        date: date, 
        start_time: time, 
        end_time: time,
        exclude_id: Optional[uuid.UUID] = None
    ) -> List[VetAvailability]:
        """Find availability records that overlap with given time range"""
        query = select(VetAvailability).where(
            and_(
                VetAvailability.vet_user_id == vet_user_id,
                VetAvailability.date == date,
                VetAvailability.is_active == True,
                # Overlap condition: not (end <= start_time or start >= end_time)
                ~(or_(
                    VetAvailability.end_time <= start_time,
                    VetAvailability.start_time >= end_time
                ))
            )
        )
        
        if exclude_id:
            query = query.where(VetAvailability.id != exclude_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_available_slots(
        self, 
        vet_user_id: uuid.UUID, 
        practice_id: uuid.UUID,
        date: date, 
        slot_duration_minutes: int = 30
    ) -> List[Dict]:
        """
        Get actual available time slots for a vet on a specific date.
        This implements the logic from service.md to return bookable slots instead of broad windows.
        """
        # Simplified approach - get vet availability and generate slots in Python
        # This avoids complex SQL parameter binding issues
        
        # First, get the practice to access its timezone
        practice_query = select(VeterinaryPractice).where(VeterinaryPractice.id == practice_id)
        practice_result = await self.session.execute(practice_query)
        practice = practice_result.scalar_one_or_none()
        logger.info("💩!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        if not practice:
            return []
        
        # Get current time in the practice's timezone
        practice_tz = pytz.timezone(practice.timezone)
        current_datetime_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)
        current_datetime_practice = current_datetime_utc.astimezone(practice_tz)
        current_date_practice = current_datetime_practice.date()
        current_time_practice = current_datetime_practice.time()
        
        
        # Get availability for the exact date
        availability_query = select(VetAvailability).where(
            and_(
                VetAvailability.vet_user_id == vet_user_id,
                VetAvailability.practice_id == practice_id,
                VetAvailability.date == date,
                VetAvailability.is_active == True,
                VetAvailability.availability_type.in_(['AVAILABLE', 'EMERGENCY_ONLY'])
            )
        )
        
        availability_result = await self.session.execute(availability_query)
        availability_records = list(availability_result.scalars().all())
        
        if not availability_records:
            return []
        
        # Get existing appointments for this vet on this date
        from ..models_pg.appointment import Appointment
        appointments_query = select(Appointment).where(
            and_(
                Appointment.assigned_vet_user_id == vet_user_id,
                Appointment.practice_id == practice_id,
                func.date(Appointment.appointment_date) == date,
                Appointment.status.notin_(['CANCELLED', 'NO_SHOW', 'COMPLETED'])
            )
        )
        
        appointments_result = await self.session.execute(appointments_query)
        existing_appointments = list(appointments_result.scalars().all())
        
        # Process availability records and generate slots
        all_slots = []
        slot_duration = timedelta(minutes=slot_duration_minutes)
        
        for availability in availability_records:
            # Generate slots for each availability window
            current_time = datetime.combine(date, availability.start_time)
            end_time = datetime.combine(date, availability.end_time)
            
            while current_time + slot_duration <= end_time:
                slot_end = current_time + slot_duration
                
                # Skip past time slots if the requested date is today in the practice's timezone
                if date == current_date_practice and current_time.time() <= current_time_practice:
                    current_time = slot_end
                    continue
                
                # Check if this slot conflicts with any existing appointments
                slot_available = True
                conflicting_appointment = None
                conflicting_type = None
                
                for appointment in existing_appointments:
                    appt_start = appointment.appointment_date
                    appt_end = appt_start + timedelta(minutes=appointment.duration_minutes)
                    
                    # Convert to naive datetimes for comparison (remove timezone info)
                    appt_start_naive = appt_start.replace(tzinfo=None) if appt_start.tzinfo else appt_start
                    appt_end_naive = appt_end.replace(tzinfo=None) if appt_end.tzinfo else appt_end
                    
                    # Check for overlap: slot overlaps if it starts before appointment ends 
                    # and ends after appointment starts
                    if (current_time < appt_end_naive and slot_end > appt_start_naive):
                        slot_available = False
                        conflicting_appointment = appointment.title
                        conflicting_type = appointment.appointment_type
                        break
                
                # Convert local slot times to UTC for storage consistency
                local_tz = pytz.timezone(practice.timezone)
                
                # Create local datetime objects for the slot
                local_start_dt = local_tz.localize(current_time)
                local_end_dt = local_tz.localize(slot_end)
                
                # Convert to UTC
                utc_start_dt = local_start_dt.astimezone(pytz.UTC)
                utc_end_dt = local_end_dt.astimezone(pytz.UTC)
                
                all_slots.append({
                    'start_time': utc_start_dt.time(),  # Store UTC time
                    'end_time': utc_end_dt.time(),      # Store UTC time
                    'availability_type': availability.availability_type.value,
                    'available': slot_available,
                    'conflicting_appointment': conflicting_appointment,
                    'conflicting_type': conflicting_type,
                    'notes': 'Slot already booked' if not slot_available else 'Available',
                    'local_datetime': local_start_dt.isoformat(),  # Include local time for reference
                    'utc_datetime': utc_start_dt.isoformat()       # Include UTC time for reference
                })
                
                current_time = slot_end
        
        # Remove duplicate slots (same start_time) and sort by start_time
        unique_slots = {}
        for slot in all_slots:
            start_time_key = slot['start_time']
            if start_time_key not in unique_slots:
                unique_slots[start_time_key] = slot
        
        # Sort slots by start time
        sorted_slots = sorted(unique_slots.values(), key=lambda x: x['start_time'])
        
        return sorted_slots


class RecurringAvailabilityRepository(BaseRepository[RecurringAvailability]):
    """Repository for RecurringAvailability operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(RecurringAvailability, session)
    
    async def get_by_vet_id(self, vet_user_id: uuid.UUID, include_inactive: bool = False) -> List[RecurringAvailability]:
        """Get all recurring availability for a vet"""
        query = select(RecurringAvailability).where(RecurringAvailability.vet_user_id == vet_user_id)
        
        if not include_inactive:
            query = query.where(RecurringAvailability.is_active == True)
        
        query = query.order_by(RecurringAvailability.day_of_week, RecurringAvailability.start_time)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_effective_for_date(self, vet_user_id: uuid.UUID, check_date: date) -> List[RecurringAvailability]:
        """Get recurring availability effective for a specific date"""
        day_of_week = check_date.weekday() + 1  # Convert to 1-7 (Monday=1, Sunday=7)
        if day_of_week == 7:  # Sunday
            day_of_week = 0
        
        query = select(RecurringAvailability).where(
            and_(
                RecurringAvailability.vet_user_id == vet_user_id,
                RecurringAvailability.day_of_week == day_of_week,
                RecurringAvailability.is_active == True,
                RecurringAvailability.effective_from <= check_date,
                or_(
                    RecurringAvailability.effective_until.is_(None),
                    RecurringAvailability.effective_until >= check_date
                )
            )
        ).order_by(RecurringAvailability.start_time)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_practice_id(self, practice_id: uuid.UUID, include_inactive: bool = False) -> List[RecurringAvailability]:
        """Get all recurring availability for a practice"""
        query = select(RecurringAvailability).where(RecurringAvailability.practice_id == practice_id)
        
        if not include_inactive:
            query = query.where(RecurringAvailability.is_active == True)
        
        query = query.order_by(
            RecurringAvailability.vet_user_id, 
            RecurringAvailability.day_of_week, 
            RecurringAvailability.start_time
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


class AppointmentConflictRepository(BaseRepository[AppointmentConflict]):
    """Repository for AppointmentConflict operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(AppointmentConflict, session)
    
    async def get_by_appointment_id(self, appointment_id: uuid.UUID, include_resolved: bool = False) -> List[AppointmentConflict]:
        """Get all conflicts for an appointment"""
        query = select(AppointmentConflict).where(AppointmentConflict.appointment_id == appointment_id)
        
        if not include_resolved:
            query = query.where(AppointmentConflict.resolved == False)
        
        query = query.order_by(AppointmentConflict.severity.desc(), AppointmentConflict.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_unresolved_conflicts(self, practice_id: Optional[uuid.UUID] = None) -> List[AppointmentConflict]:
        """Get all unresolved conflicts, optionally filtered by practice"""
        query = select(AppointmentConflict).join(
            AppointmentConflict.appointment
        ).where(AppointmentConflict.resolved == False)
        
        if practice_id:
            # Need to import Appointment model to filter by practice
            from ..models_pg.appointment import Appointment
            query = query.where(Appointment.practice_id == practice_id)
        
        query = query.order_by(AppointmentConflict.severity.desc(), AppointmentConflict.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_conflicts_by_type(self, conflict_type: ConflictType, include_resolved: bool = False) -> List[AppointmentConflict]:
        """Get conflicts by type"""
        query = select(AppointmentConflict).where(AppointmentConflict.conflict_type == conflict_type)
        
        if not include_resolved:
            query = query.where(AppointmentConflict.resolved == False)
        
        query = query.order_by(AppointmentConflict.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def resolve_conflict(self, conflict_id: uuid.UUID, resolved_by_user_id: uuid.UUID) -> Optional[AppointmentConflict]:
        """Mark a conflict as resolved"""
        conflict = await self.get_by_id(conflict_id)
        if conflict:
            conflict.resolve(resolved_by_user_id)
            await self.session.commit()
            await self.session.refresh(conflict)
        return conflict
    
    async def get_conflict_statistics(self, practice_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Get conflict statistics for reporting"""
        from ..models_pg.appointment import Appointment
        
        base_query = select(AppointmentConflict).join(AppointmentConflict.appointment)
        
        if practice_id:
            base_query = base_query.where(Appointment.practice_id == practice_id)
        
        # Total conflicts
        total_result = await self.session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total_conflicts = total_result.scalar()
        
        # Unresolved conflicts
        unresolved_result = await self.session.execute(
            select(func.count()).select_from(
                base_query.where(AppointmentConflict.resolved == False).subquery()
            )
        )
        unresolved_conflicts = unresolved_result.scalar()
        
        # Conflicts by type
        type_result = await self.session.execute(
            select(
                AppointmentConflict.conflict_type,
                func.count().label('count')
            ).select_from(
                base_query.subquery()
            ).group_by(AppointmentConflict.conflict_type)
        )
        conflicts_by_type = {row.conflict_type: row.count for row in type_result}
        
        # Conflicts by severity
        severity_result = await self.session.execute(
            select(
                AppointmentConflict.severity,
                func.count().label('count')
            ).select_from(
                base_query.subquery()
            ).group_by(AppointmentConflict.severity)
        )
        conflicts_by_severity = {row.severity: row.count for row in severity_result}
        
        return {
            'total_conflicts': total_conflicts,
            'unresolved_conflicts': unresolved_conflicts,
            'resolved_conflicts': total_conflicts - unresolved_conflicts,
            'conflicts_by_type': conflicts_by_type,
            'conflicts_by_severity': conflicts_by_severity
        }
