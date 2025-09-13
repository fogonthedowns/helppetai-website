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


from .base_repository import BaseRepository
from ..models_pg.scheduling import (
    PracticeHours, VetAvailability, RecurringAvailability, AppointmentConflict,
    AvailabilityType, ConflictType, ConflictSeverity
)


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
    
    async def get_by_vet_and_date(self, vet_user_id: uuid.UUID, date: date, include_inactive: bool = False) -> List[VetAvailability]:
        """Get all availability records for a vet on a specific date"""
        query = select(VetAvailability).where(
            and_(
                VetAvailability.vet_user_id == vet_user_id,
                VetAvailability.date == date
            )
        )
        
        if not include_inactive:
            query = query.where(VetAvailability.is_active == True)
        
        query = query.order_by(VetAvailability.start_time)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
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
        
        # First, get the vet's availability for this date
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
        
        
        # Process ALL availability records and merge overlapping time windows
        all_slots = []
        slot_duration = timedelta(minutes=slot_duration_minutes)
        
        for availability in availability_records:
            # Generate slots for each availability window
            current_time = datetime.combine(date, availability.start_time)
            end_time = datetime.combine(date, availability.end_time)
            
            while current_time + slot_duration <= end_time:
                slot_end = current_time + slot_duration
                
                all_slots.append({
                    'start_time': current_time.time(),
                    'end_time': slot_end.time(),
                    'availability_type': availability.availability_type.value,
                    'available': True,  # Simplified - not checking appointments yet
                    'conflicting_appointment': None,
                    'conflicting_type': None,
                    'notes': 'Available'
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
