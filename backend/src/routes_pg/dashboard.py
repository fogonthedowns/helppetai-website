"""
Vet Dashboard REST API endpoints
Based on spec in docs/0011_my_appointments_dashboard.md
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, HTTPException, status, Path, Depends
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from ..auth.jwt_auth_pg import get_current_user, User
from ..models_pg.appointment import Appointment, AppointmentPet
from ..database_pg import get_db_session

router = APIRouter()


# Pydantic models for dashboard responses
class DashboardStats(BaseModel):
    appointments_today: int
    completed_visits: int


class PetSummary(BaseModel):
    id: str
    name: str
    species: str
    breed: Optional[str] = None


class AppointmentSummary(BaseModel):
    id: str
    practice_id: str
    pet_owner_id: str
    assigned_vet_user_id: Optional[str] = None
    created_by_user_id: str
    appointment_date: datetime
    duration_minutes: int
    appointment_type: str
    status: str
    title: str
    description: Optional[str] = None
    notes: Optional[str] = None
    pets: List[PetSummary]
    created_at: datetime
    updated_at: datetime


class VetDashboardResponse(BaseModel):
    today_appointments: List[AppointmentSummary]
    stats: DashboardStats


class TodayWorkSummaryResponse(BaseModel):
    appointments_today: List[AppointmentSummary]
    next_appointment: Optional[AppointmentSummary] = None
    current_appointment: Optional[AppointmentSummary] = None
    completed_count: int
    remaining_count: int


def require_vet_access(current_user: User = Depends(get_current_user)) -> User:
    """Require VET or VET_STAFF role for dashboard access."""
    if current_user.role not in ["VET", "VET_STAFF"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Veterinary staff only."
        )
    return current_user


@router.get(
    "/vet/{vet_user_uuid}",
    response_model=VetDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Vet Dashboard",
    description="Get vet's appointments for specified date from database"
)
async def get_vet_dashboard(
    vet_user_uuid: str = Path(..., description="Veterinarian user UUID"),
    date: Optional[str] = None,
    current_user: User = Depends(require_vet_access),
    db: AsyncSession = Depends(get_db_session)
) -> VetDashboardResponse:
    """
    Get vet's appointments for specified date from the database.
    """
    try:
        vet_uuid = UUID(vet_user_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vet user UUID format")
    
    # Verify user can access this dashboard (admin or self)
    if current_user.role != "ADMIN" and str(current_user.id) != vet_user_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only view your own dashboard."
        )
    
    # Parse date parameter or use today
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Use UTC today to avoid timezone issues
        from datetime import timezone
        target_date = datetime.now(timezone.utc).date()
    
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    
    # Query today's appointments for this vet from database
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.appointment_pets).selectinload(AppointmentPet.pet))
        .where(
            and_(
                Appointment.assigned_vet_user_id == vet_uuid,
                Appointment.appointment_date >= start_of_day,
                Appointment.appointment_date <= end_of_day
            )
        )
        .order_by(Appointment.appointment_date)
    )
    appointments = result.scalars().all()
    
    # Convert to response format
    today_appointments = []
    for appointment in appointments:
        pets = [
            PetSummary(
                id=str(ap.pet.id),
                name=ap.pet.name,
                species=ap.pet.species,
                breed=ap.pet.breed
            )
            for ap in appointment.appointment_pets
        ]
        
        today_appointments.append(AppointmentSummary(
            id=str(appointment.id),
            practice_id=str(appointment.practice_id),
            pet_owner_id=str(appointment.pet_owner_id),
            assigned_vet_user_id=str(appointment.assigned_vet_user_id) if appointment.assigned_vet_user_id else None,
            created_by_user_id=str(appointment.created_by_user_id),
            appointment_date=appointment.appointment_date,
            duration_minutes=appointment.duration_minutes,
            appointment_type=appointment.appointment_type,
            status=appointment.status,
            title=appointment.title,
            description=appointment.description,
            notes=appointment.notes,
            pets=pets,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at
        ))
    
    # Calculate stats
    completed_count = len([apt for apt in today_appointments if apt.status in ["completed", "complete"]])
    stats = DashboardStats(
        appointments_today=len(today_appointments),
        completed_visits=completed_count
    )
    
    return VetDashboardResponse(
        today_appointments=today_appointments,
        stats=stats
    )


@router.get(
    "/vet/{vet_user_uuid}/today",
    response_model=TodayWorkSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Day's Work Summary",
    description="Get vet's work summary for specified date with next/current appointments from database"
)
async def get_vet_today_summary(
    vet_user_uuid: str = Path(..., description="Veterinarian user UUID"),
    date: Optional[str] = None,
    current_user: User = Depends(require_vet_access),
    db: AsyncSession = Depends(get_db_session)
) -> TodayWorkSummaryResponse:
    """
    Get vet's work summary for specified date from database.
    Returns appointments with next/current appointment highlighting.
    """
    try:
        vet_uuid = UUID(vet_user_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid vet user UUID format")
    
    # Verify user can access this dashboard (admin or self)
    if current_user.role != "ADMIN" and str(current_user.id) != vet_user_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only view your own dashboard."
        )
    
    # Parse date parameter or use today
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        # Use UTC today to avoid timezone issues
        from datetime import timezone
        target_date = datetime.now(timezone.utc).date()
    
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())
    now = datetime.now().replace(tzinfo=None)  # Make timezone-naive to match database datetimes
    
    # Query today's appointments for this vet from database
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.appointment_pets).selectinload(AppointmentPet.pet))
        .where(
            and_(
                Appointment.assigned_vet_user_id == vet_uuid,
                Appointment.appointment_date >= start_of_day,
                Appointment.appointment_date <= end_of_day
            )
        )
        .order_by(Appointment.appointment_date)
    )
    appointments = result.scalars().all()
    
    # Convert to response format
    today_appointments = []
    for appointment in appointments:
        pets = [
            PetSummary(
                id=str(ap.pet.id),
                name=ap.pet.name,
                species=ap.pet.species,
                breed=ap.pet.breed
            )
            for ap in appointment.appointment_pets
        ]
        
        today_appointments.append(AppointmentSummary(
            id=str(appointment.id),
            practice_id=str(appointment.practice_id),
            pet_owner_id=str(appointment.pet_owner_id),
            assigned_vet_user_id=str(appointment.assigned_vet_user_id) if appointment.assigned_vet_user_id else None,
            created_by_user_id=str(appointment.created_by_user_id),
            appointment_date=appointment.appointment_date,
            duration_minutes=appointment.duration_minutes,
            appointment_type=appointment.appointment_type,
            status=appointment.status,
            title=appointment.title,
            description=appointment.description,
            notes=appointment.notes,
            pets=pets,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at
        ))
    
    # Determine next appointment (next scheduled appointment after now)
    next_appointment = None
    current_appointment = None
    
    for apt in today_appointments:
        if apt.status in ["scheduled", "confirmed"]:
            # Ensure appointment_date is timezone-naive for comparison
            apt_date = apt.appointment_date.replace(tzinfo=None) if apt.appointment_date.tzinfo else apt.appointment_date
            
            if apt_date > now:
                if next_appointment is None or apt_date < (next_appointment.appointment_date.replace(tzinfo=None) if next_appointment.appointment_date.tzinfo else next_appointment.appointment_date):
                    next_appointment = apt
            elif (apt_date <= now and 
                  apt_date + timedelta(minutes=apt.duration_minutes) > now):
                current_appointment = apt
    
    completed_count = len([apt for apt in today_appointments if apt.status in ["completed", "complete"]])
    remaining_count = len(today_appointments) - completed_count
    
    return TodayWorkSummaryResponse(
        appointments_today=today_appointments,
        next_appointment=next_appointment,
        current_appointment=current_appointment,
        completed_count=completed_count,
        remaining_count=remaining_count
    )



