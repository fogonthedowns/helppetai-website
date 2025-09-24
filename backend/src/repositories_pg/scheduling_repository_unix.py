"""
CLEAN Unix Timestamp Scheduling Repositories

NO OLD DATA - NO MIGRATION - NO ROT
Only works with vet_availability_unix and appointments_unix tables
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
import pytz

from .base_repository import BaseRepository
from ..models_pg.scheduling_unix import VetAvailability
# AppointmentUnix is deprecated - use regular AppointmentRepository instead
from ..models_pg.practice import VeterinaryPractice

import logging
logger = logging.getLogger(__name__)


class VetAvailabilityUnixRepository(BaseRepository[VetAvailability]):
    """Unix timestamp vet availability repository - CLEAN IMPLEMENTATION"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(VetAvailability, session)
    
    async def get_by_vet_and_date_range(
        self, 
        vet_user_id: uuid.UUID, 
        utc_start: datetime, 
        utc_end: datetime
    ) -> List[VetAvailability]:
        """
        Get availability for a vet in UTC time range - SIMPLE!
        
        Args:
            vet_user_id: The vet UUID
            utc_start: UTC start time
            utc_end: UTC end time
            
        Returns:
            Availability records that overlap with the time range
        """
        query = select(VetAvailability).where(
            and_(
                VetAvailability.vet_user_id == vet_user_id,
                VetAvailability.start_at < utc_end,
                VetAvailability.end_at > utc_start,
                VetAvailability.is_active == True
            )
        ).order_by(VetAvailability.start_at)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_practice_and_date_range(
        self,
        practice_id: uuid.UUID,
        utc_start: datetime,
        utc_end: datetime,
        availability_types: Optional[List[str]] = None
    ) -> List[VetAvailability]:
        """Get availability for all vets in practice within UTC range"""
        query = select(VetAvailability).where(
            and_(
                VetAvailability.practice_id == practice_id,
                VetAvailability.start_at < utc_end,
                VetAvailability.end_at > utc_start,
                VetAvailability.is_active == True
            )
        )
        
        if availability_types:
            query = query.where(VetAvailability.availability_type.in_(availability_types))
        
        query = query.order_by(VetAvailability.start_at, VetAvailability.vet_user_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def find_overlapping_availability(
        self,
        vet_user_id: uuid.UUID,
        utc_start: datetime,
        utc_end: datetime,
        exclude_id: Optional[uuid.UUID] = None
    ) -> List[VetAvailability]:
        """Find availability records that overlap with UTC time range"""
        query = select(VetAvailability).where(
            and_(
                VetAvailability.vet_user_id == vet_user_id,
                VetAvailability.start_at < utc_end,
                VetAvailability.end_at > utc_start,
                VetAvailability.is_active == True
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
        utc_start: datetime,
        utc_end: datetime,
        slot_duration_minutes: int = 30,
        timezone_str: str = "America/Los_Angeles"
    ) -> List[Dict[str, Any]]:
        """
        Get available time slots within UTC range - CLEAN LOGIC
        
        This replaces the complex old logic with simple UTC queries
        """
        # Get availability records in range
        availability_records = await self.get_by_vet_and_date_range(
            vet_user_id, utc_start, utc_end
        )
        
        if not availability_records:
            return []
        
        # DEPRECATED: AppointmentUnixRepository not available
        # appointment_repo = AppointmentUnixRepository(self.session)
        # appointments = await appointment_repo.get_by_vet_and_time_range(
        #     vet_user_id, practice_id, utc_start, utc_end
        # )
        appointments = []  # Empty list since AppointmentUnix is deprecated
        
        # Generate slots
        slots = []
        slot_duration = timedelta(minutes=slot_duration_minutes)
        
        for availability in availability_records:
            current_time = availability.start_at
            
            while current_time + slot_duration <= availability.end_at:
                slot_end = current_time + slot_duration
                
                # Check for conflicts
                is_available = True
                conflicting_appointment = None
                
                for appointment in appointments:
                    appt_end = appointment.appointment_at + timedelta(minutes=appointment.duration_minutes)
                    if current_time < appt_end and slot_end > appointment.appointment_at:
                        is_available = False
                        conflicting_appointment = appointment.title
                        break
                
                # Convert to local time for display
                tz = pytz.timezone(timezone_str)
                local_start = current_time.astimezone(tz)
                local_end = slot_end.astimezone(tz)
                
                slots.append({
                    'utc_start': current_time,
                    'utc_end': slot_end,
                    'local_start': local_start,
                    'local_end': local_end,
                    'start_time': local_start.time(),
                    'end_time': local_end.time(),
                    'available': is_available,
                    'availability_type': availability.availability_type.value,
                    'conflicting_appointment': conflicting_appointment,
                    'vet_user_id': availability.vet_user_id
                })
                
                current_time += slot_duration
        
        # Sort by UTC start time
        slots.sort(key=lambda x: x['utc_start'])
        return slots
    
    async def create_from_voice_input(
        self,
        vet_user_id: uuid.UUID,
        practice_id: uuid.UUID,
        local_date_str: str,
        local_start_time_str: str,
        local_end_time_str: str,
        timezone_str: str,
        availability_type: str = "AVAILABLE",
        notes: Optional[str] = None
    ) -> VetAvailability:
        """
        Create availability from voice input - CLEAN TIMEZONE CONVERSION
        
        Args:
            local_date_str: "Oct 3, 2025" or "tomorrow"
            local_start_time_str: "9am" or "09:00"
            local_end_time_str: "5pm" or "17:00"
            timezone_str: "America/Los_Angeles"
        """
        from dateutil import parser
        
        # Parse voice input with timezone context
        tz = pytz.timezone(timezone_str)
        
        # Handle relative dates
        if local_date_str.lower() == 'today':
            local_date = datetime.now(tz).date()
        elif local_date_str.lower() == 'tomorrow':
            local_date = (datetime.now(tz) + timedelta(days=1)).date()
        else:
            parsed_date = parser.parse(local_date_str)
            local_date = parsed_date.date()
        
        # Parse times
        start_time = parser.parse(local_start_time_str).time()
        end_time = parser.parse(local_end_time_str).time()
        
        # Create timezone-aware local datetimes
        local_start_dt = tz.localize(datetime.combine(local_date, start_time))
        local_end_dt = tz.localize(datetime.combine(local_date, end_time))
        
        # Convert to UTC for storage
        utc_start = local_start_dt.astimezone(pytz.UTC)
        utc_end = local_end_dt.astimezone(pytz.UTC)
        
        # Create and save record
        availability = VetAvailability(
            vet_user_id=vet_user_id,
            practice_id=practice_id,
            start_at=utc_start,
            end_at=utc_end,
            availability_type=availability_type,
            notes=notes
        )
        
        self.session.add(availability)
        await self.session.commit()
        await self.session.refresh(availability)
        
        logger.info(f"✅ Created availability: {local_start_dt} - {local_end_dt} ({timezone_str})")
        logger.info(f"   Stored as UTC: {utc_start} - {utc_end}")
        
        return availability


# ============================================================================
# DEPRECATED: AppointmentUnixRepository
# ============================================================================
# 
# This repository was created but is NOT used by any production systems.
# The voice system uses regular AppointmentRepository instead.
# 
# Status: DEPRECATED (2025-09-24)
# Reason: No services use this repository
# Active Repository: AppointmentRepository (src/repositories_pg/appointment_repository.py)
# 
# ORIGINAL IMPLEMENTATION (COMMENTED FOR REFERENCE):
# ============================================================================

# class AppointmentUnixRepository(BaseRepository[AppointmentUnix]):
#     """DEPRECATED: Unix timestamp appointment repository"""
#     
#     def __init__(self, session: AsyncSession):
#         super().__init__(AppointmentUnix, session)
#     
#     async def get_by_vet_and_time_range(
#         self,
#         vet_user_id: uuid.UUID,
#         practice_id: uuid.UUID,
#         utc_start: datetime,
#         utc_end: datetime,
#         exclude_statuses: List[str] = None
#     ) -> List[AppointmentUnix]:
#         """Get appointments for vet within UTC time range"""
#         if exclude_statuses is None:
#             exclude_statuses = ['CANCELLED', 'NO_SHOW', 'COMPLETED']
#         
#         query = select(AppointmentUnix).where(
#             and_(
#                 AppointmentUnix.assigned_vet_user_id == vet_user_id,
#                 AppointmentUnix.practice_id == practice_id,
#                 AppointmentUnix.appointment_at >= utc_start,
#                 AppointmentUnix.appointment_at < utc_end,
#                 ~AppointmentUnix.status.in_(exclude_statuses)
#             )
#         ).order_by(AppointmentUnix.appointment_at)
#         
#         result = await self.session.execute(query)
#         return list(result.scalars().all())
#     
#     async def get_by_practice_and_time_range(
#         self,
#         practice_id: uuid.UUID,
#         utc_start: datetime,
#         utc_end: datetime,
#         exclude_statuses: List[str] = None
#     ) -> List[AppointmentUnix]:
#         """Get all appointments for practice within UTC time range"""
#         if exclude_statuses is None:
#             exclude_statuses = ['CANCELLED', 'NO_SHOW', 'COMPLETED']
#         
#         query = select(AppointmentUnix).where(
#             and_(
#                 AppointmentUnix.practice_id == practice_id,
#                 AppointmentUnix.appointment_at >= utc_start,
#                 AppointmentUnix.appointment_at < utc_end,
#                 ~AppointmentUnix.status.in_(exclude_statuses)
#             )
#         ).order_by(AppointmentUnix.appointment_at)
#         
#         result = await self.session.execute(query)
#         return list(result.scalars().all())
#     
#     async def find_conflicts(
#         self,
#         vet_user_id: uuid.UUID,
#         utc_appointment_time: datetime,
#         duration_minutes: int,
#         exclude_id: Optional[uuid.UUID] = None
#     ) -> List[AppointmentUnix]:
#         """Find conflicting appointments for a time slot"""
#         appointment_end = utc_appointment_time + timedelta(minutes=duration_minutes)
#         
#         query = select(AppointmentUnix).where(
#             and_(
#                 AppointmentUnix.assigned_vet_user_id == vet_user_id,
#                 AppointmentUnix.appointment_at < appointment_end,
#                 func.date_add(AppointmentUnix.appointment_at, text(f"INTERVAL {AppointmentUnix.duration_minutes} MINUTE")) > utc_appointment_time,
#                 ~AppointmentUnix.status.in_(['CANCELLED', 'NO_SHOW', 'COMPLETED'])
#             )
#         )
#         
#         if exclude_id:
#             query = query.where(AppointmentUnix.id != exclude_id)
#         
#         result = await self.session.execute(query)
#         return list(result.scalars().all())
#     
#     async def create_from_voice_booking(
#         self,
#         practice_id: uuid.UUID,
#         pet_owner_id: uuid.UUID,
#         assigned_vet_user_id: uuid.UUID,
#         created_by_user_id: uuid.UUID,
#         local_date_str: str,
#         local_time_str: str,
#         timezone_str: str,
#         duration_minutes: int = 30,
#         title: str = "Veterinary Appointment",
#         appointment_type: str = "CHECKUP",
#         notes: Optional[str] = None
#     ) -> AppointmentUnix:
#         """
#         Create appointment from voice booking - CLEAN TIMEZONE CONVERSION
#         """
#         from dateutil import parser
#         
#         # Parse with timezone context
#         tz = pytz.timezone(timezone_str)
#         
#         # Parse date and time
#         if local_date_str.lower() == 'today':
#             local_date = datetime.now(tz).date()
#         elif local_date_str.lower() == 'tomorrow':
#             local_date = (datetime.now(tz) + timedelta(days=1)).date()
#         else:
#             parsed_date = parser.parse(local_date_str)
#             local_date = parsed_date.date()
#         
#         parsed_time = parser.parse(local_time_str).time()
#         
#         # Create timezone-aware local datetime
#         local_dt = tz.localize(datetime.combine(local_date, parsed_time))
#         
#         # Convert to UTC for storage
#         utc_dt = local_dt.astimezone(pytz.UTC)
#         
#         # Create and save appointment
#         appointment = AppointmentUnix(
#             practice_id=practice_id,
#             pet_owner_id=pet_owner_id,
#             assigned_vet_user_id=assigned_vet_user_id,
#             created_by_user_id=created_by_user_id,
#             appointment_at=utc_dt,
#             duration_minutes=duration_minutes,
#             title=title,
#             appointment_type=appointment_type,
#             notes=notes
#         )
#         
#         self.session.add(appointment)
#         await self.session.commit()
#         await self.session.refresh(appointment)
#         
#         logger.info(f"✅ Created appointment: {local_dt} ({timezone_str})")
#         logger.info(f"   Stored as UTC: {utc_dt}")
#         
#         return appointment
#     
#     async def get_statistics(
#         self,
#         practice_id: Optional[uuid.UUID] = None,
#         utc_start: Optional[datetime] = None,
#         utc_end: Optional[datetime] = None
#     ) -> Dict[str, Any]:
#         """Get appointment statistics for UTC time range"""
#         base_query = select(AppointmentUnix)
#         
#         conditions = []
#         if practice_id:
#             conditions.append(AppointmentUnix.practice_id == practice_id)
#         if utc_start:
#             conditions.append(AppointmentUnix.appointment_at >= utc_start)
#         if utc_end:
#             conditions.append(AppointmentUnix.appointment_at < utc_end)
#         
#         if conditions:
#             base_query = base_query.where(and_(*conditions))
#         
#         # Total appointments
#         total_result = await self.session.execute(
#             select(func.count()).select_from(base_query.subquery())
#         )
#         total_appointments = total_result.scalar()
#         
#         # By status
#         status_result = await self.session.execute(
#             select(
#                 AppointmentUnix.status,
#                 func.count().label('count')
#             ).select_from(
#                 base_query.subquery()
#             ).group_by(AppointmentUnix.status)
#         )
#         appointments_by_status = {row.status: row.count for row in status_result}
#         
#         return {
#             'total_appointments': total_appointments,
#             'appointments_by_status': appointments_by_status,
#             'time_range': {
#                 'utc_start': utc_start.isoformat() if utc_start else None,
#                 'utc_end': utc_end.isoformat() if utc_end else None
#             }
#         }
