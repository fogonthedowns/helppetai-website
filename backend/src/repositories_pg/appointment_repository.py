"""
Appointment repository for PostgreSQL - HelpPet MVP
Repository for appointment CRUD operations
"""

import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from ..models_pg.appointment import Appointment, AppointmentPet, AppointmentStatus, AppointmentType


class AppointmentRepository(BaseRepository[Appointment]):
    """Repository for Appointment operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Appointment, session)
    
    async def create_appointment(
        self,
        practice_id: uuid.UUID,
        pet_owner_id: uuid.UUID,
        created_by_user_id: uuid.UUID,
        appointment_date: datetime,
        title: str,
        description: str = None,
        appointment_type: AppointmentType = AppointmentType.CHECKUP,
        duration_minutes: int = 30,
        assigned_vet_user_id: uuid.UUID = None,
        pet_ids: List[uuid.UUID] = None
    ) -> Appointment:
        """Create a new appointment with optional pet associations"""
        
        # Create the appointment
        appointment = Appointment(
            practice_id=practice_id,
            pet_owner_id=pet_owner_id,
            created_by_user_id=created_by_user_id,
            assigned_vet_user_id=assigned_vet_user_id,
            appointment_date=appointment_date,
            duration_minutes=duration_minutes,
            appointment_type=appointment_type.value,
            status=AppointmentStatus.SCHEDULED.value,
            title=title,
            description=description
        )
        
        self.session.add(appointment)
        await self.session.flush()  # Get the ID
        
        # Associate pets if provided
        if pet_ids:
            for pet_id in pet_ids:
                appointment_pet = AppointmentPet(
                    appointment_id=appointment.id,
                    pet_id=pet_id
                )
                self.session.add(appointment_pet)
        
        await self.session.commit()
        await self.session.refresh(appointment)
        
        return appointment
    
    async def get_by_practice_id(
        self,
        practice_id: uuid.UUID,
        start_date: date = None,
        end_date: date = None,
        status_filter: List[AppointmentStatus] = None,
        include_relationships: bool = True
    ) -> List[Appointment]:
        """Get appointments for a practice with optional filters"""
        
        query = select(Appointment).where(Appointment.practice_id == practice_id)
        
        # Add relationships if requested
        if include_relationships:
            query = query.options(
                selectinload(Appointment.pet_owner),
                selectinload(Appointment.assigned_vet),
                selectinload(Appointment.appointment_pets).selectinload(AppointmentPet.pet)
            )
        
        # Date range filter
        if start_date:
            query = query.where(func.date(Appointment.appointment_date) >= start_date)
        if end_date:
            query = query.where(func.date(Appointment.appointment_date) <= end_date)
        
        # Status filter
        if status_filter:
            status_values = [status.value for status in status_filter]
            query = query.where(Appointment.status.in_(status_values))
        
        query = query.order_by(Appointment.appointment_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_pet_owner_id(
        self,
        pet_owner_id: uuid.UUID,
        include_past: bool = False,
        include_relationships: bool = True
    ) -> List[Appointment]:
        """Get appointments for a pet owner"""
        
        query = select(Appointment).where(Appointment.pet_owner_id == pet_owner_id)
        
        # Add relationships if requested
        if include_relationships:
            query = query.options(
                selectinload(Appointment.practice),
                selectinload(Appointment.assigned_vet),
                selectinload(Appointment.appointment_pets).selectinload(AppointmentPet.pet)
            )
        
        # Filter out past appointments unless requested
        if not include_past:
            query = query.where(Appointment.appointment_date >= datetime.utcnow())
        
        # Exclude cancelled/no-show appointments
        query = query.where(
            Appointment.status.notin_([
                AppointmentStatus.CANCELLED.value,
                AppointmentStatus.NO_SHOW.value
            ])
        )
        
        query = query.order_by(Appointment.appointment_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_vet_id(
        self,
        vet_user_id: uuid.UUID,
        start_date: date = None,
        end_date: date = None,
        include_relationships: bool = True
    ) -> List[Appointment]:
        """Get appointments assigned to a specific vet"""
        
        query = select(Appointment).where(Appointment.assigned_vet_user_id == vet_user_id)
        
        # Add relationships if requested
        if include_relationships:
            query = query.options(
                selectinload(Appointment.pet_owner),
                selectinload(Appointment.practice),
                selectinload(Appointment.appointment_pets).selectinload(AppointmentPet.pet)
            )
        
        # Date range filter
        if start_date:
            query = query.where(func.date(Appointment.appointment_date) >= start_date)
        if end_date:
            query = query.where(func.date(Appointment.appointment_date) <= end_date)
        
        query = query.order_by(Appointment.appointment_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_status(self, appointment_id: uuid.UUID, status: AppointmentStatus) -> Optional[Appointment]:
        """Update appointment status"""
        appointment = await self.get_by_id(appointment_id)
        if appointment:
            appointment.status = status.value
            appointment.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(appointment)
        return appointment
    
    async def check_time_conflict(
        self,
        vet_user_id: uuid.UUID,
        appointment_date: datetime,
        duration_minutes: int,
        exclude_appointment_id: uuid.UUID = None
    ) -> List[Appointment]:
        """Check for time conflicts with existing appointments"""
        
        # Calculate time range
        start_time = appointment_date
        end_time = appointment_date + timedelta(minutes=duration_minutes)
        
        # Build query for overlapping appointments
        query = select(Appointment).where(
            and_(
                Appointment.assigned_vet_user_id == vet_user_id,
                Appointment.status.notin_([
                    AppointmentStatus.CANCELLED.value,
                    AppointmentStatus.NO_SHOW.value,
                    AppointmentStatus.COMPLETED.value
                ]),
                # Check for overlap: appointment starts before our end AND ends after our start
                Appointment.appointment_date < end_time,
                (Appointment.appointment_date + func.make_interval(0, 0, 0, 0, 0, Appointment.duration_minutes, 0)) > start_time
            )
        )
        
        # Exclude specific appointment if provided (for updates)
        if exclude_appointment_id:
            query = query.where(Appointment.id != exclude_appointment_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_appointments_for_date_range(
        self,
        practice_id: uuid.UUID,
        start_datetime: datetime,
        end_datetime: datetime,
        vet_user_id: uuid.UUID = None
    ) -> List[Appointment]:
        """Get appointments within a specific datetime range"""
        
        query = select(Appointment).where(
            and_(
                Appointment.practice_id == practice_id,
                Appointment.appointment_date >= start_datetime,
                Appointment.appointment_date <= end_datetime,
                Appointment.status.notin_([
                    AppointmentStatus.CANCELLED.value,
                    AppointmentStatus.NO_SHOW.value
                ])
            )
        )
        
        # Filter by vet if specified
        if vet_user_id:
            query = query.where(Appointment.assigned_vet_user_id == vet_user_id)
        
        query = query.order_by(Appointment.appointment_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
