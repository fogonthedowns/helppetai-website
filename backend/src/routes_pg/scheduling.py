"""
Scheduling API routes for PostgreSQL - HelpPet MVP
Practice hours, vet availability, and appointment conflict management
"""

import uuid
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database_pg import get_db_session
from ..models_pg.user import User
from ..models_pg.scheduling import (
    PracticeHours, VetAvailability, RecurringAvailability, AppointmentConflict,
    AvailabilityType, ConflictType, ConflictSeverity
)
from ..repositories_pg.scheduling_repository import (
    PracticeHoursRepository,
    VetAvailabilityRepository,
    RecurringAvailabilityRepository,
    AppointmentConflictRepository
)
from ..schemas.scheduling_schemas import (
    PracticeHoursCreate, PracticeHoursUpdate, PracticeHoursResponse,
    VetAvailabilityCreate, VetAvailabilityUpdate, VetAvailabilityResponse,
    RecurringAvailabilityCreate, RecurringAvailabilityUpdate, RecurringAvailabilityResponse,
    AppointmentConflictCreate, AppointmentConflictUpdate, AppointmentConflictResolve, AppointmentConflictResponse,
    AvailableSlotRequest, AvailableSlotsResponse,
    ConflictCheckRequest, ConflictCheckResponse,
    BulkPracticeHoursCreate, BulkRecurringAvailabilityCreate,
    ConflictStatistics, SchedulingStatistics
)
from ..schemas.base import BaseResponse
from ..auth.jwt_auth_pg import get_current_user

router = APIRouter(prefix="/api/v1/scheduling", tags=["scheduling"])


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

async def get_practice_hours_repository(session: AsyncSession = Depends(get_db_session)) -> PracticeHoursRepository:
    """Dependency to get practice hours repository"""
    return PracticeHoursRepository(session)


async def get_vet_availability_repository(session: AsyncSession = Depends(get_db_session)) -> VetAvailabilityRepository:
    """Dependency to get vet availability repository"""
    return VetAvailabilityRepository(session)


async def get_recurring_availability_repository(session: AsyncSession = Depends(get_db_session)) -> RecurringAvailabilityRepository:
    """Dependency to get recurring availability repository"""
    return RecurringAvailabilityRepository(session)


async def get_conflict_repository(session: AsyncSession = Depends(get_db_session)) -> AppointmentConflictRepository:
    """Dependency to get appointment conflict repository"""
    return AppointmentConflictRepository(session)


# ============================================================================
# PRACTICE HOURS ENDPOINTS
# ============================================================================

@router.get("/practice-hours/{practice_id}", response_model=List[PracticeHoursResponse])
async def get_practice_hours(
    practice_id: uuid.UUID,
    include_inactive: bool = Query(False, description="Include inactive hours"),
    current_user: User = Depends(get_current_user),
    repo: PracticeHoursRepository = Depends(get_practice_hours_repository)
):
    """Get practice hours for a specific practice"""
    # TODO: Add proper authorization - check if user has access to this practice
    
    hours = await repo.get_by_practice_id(practice_id, include_inactive)
    return [PracticeHoursResponse.from_orm(hour) for hour in hours]


@router.post("/practice-hours", response_model=PracticeHoursResponse, status_code=status.HTTP_201_CREATED)
async def create_practice_hours(
    hours_data: PracticeHoursCreate,
    current_user: User = Depends(get_current_user),
    repo: PracticeHoursRepository = Depends(get_practice_hours_repository)
):
    """Create new practice hours"""
    # TODO: Add proper authorization - only practice admins should be able to create hours
    
    hours = PracticeHours(**hours_data.dict())
    created_hours = await repo.create(hours)
    return PracticeHoursResponse.from_orm(created_hours)


@router.put("/practice-hours/{hours_id}", response_model=PracticeHoursResponse)
async def update_practice_hours(
    hours_id: uuid.UUID,
    hours_data: PracticeHoursUpdate,
    current_user: User = Depends(get_current_user),
    repo: PracticeHoursRepository = Depends(get_practice_hours_repository)
):
    """Update practice hours"""
    # TODO: Add proper authorization
    
    update_data = {k: v for k, v in hours_data.dict().items() if v is not None}
    updated_hours = await repo.update_by_id(hours_id, update_data)
    
    if not updated_hours:
        raise HTTPException(status_code=404, detail="Practice hours not found")
    
    return PracticeHoursResponse.from_orm(updated_hours)


@router.delete("/practice-hours/{hours_id}", response_model=BaseResponse)
async def delete_practice_hours(
    hours_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repo: PracticeHoursRepository = Depends(get_practice_hours_repository)
):
    """Delete practice hours"""
    # TODO: Add proper authorization
    
    success = await repo.delete_by_id(hours_id)
    if not success:
        raise HTTPException(status_code=404, detail="Practice hours not found")
    
    return BaseResponse(message="Practice hours deleted successfully")


@router.post("/practice-hours/bulk", response_model=List[PracticeHoursResponse], status_code=status.HTTP_201_CREATED)
async def create_bulk_practice_hours(
    bulk_data: BulkPracticeHoursCreate,
    current_user: User = Depends(get_current_user),
    repo: PracticeHoursRepository = Depends(get_practice_hours_repository)
):
    """Create multiple practice hours at once"""
    # TODO: Add proper authorization
    
    created_hours = []
    for hours_data in bulk_data.hours:
        hours = PracticeHours(practice_id=bulk_data.practice_id, **hours_data.dict())
        created = await repo.create(hours)
        created_hours.append(created)
    
    return [PracticeHoursResponse.from_orm(hours) for hours in created_hours]


# ============================================================================
# VET AVAILABILITY ENDPOINTS
# ============================================================================

@router.get("/vet-availability/{vet_user_id}", response_model=List[VetAvailabilityResponse])
async def get_vet_availability(
    vet_user_id: uuid.UUID,
    date: date = Query(..., description="Date to get availability for"),
    include_inactive: bool = Query(False, description="Include inactive availability"),
    current_user: User = Depends(get_current_user),
    repo: VetAvailabilityRepository = Depends(get_vet_availability_repository)
):
    """Get vet availability for a specific date"""
    # TODO: Add proper authorization
    
    availability = await repo.get_by_vet_and_date(vet_user_id, date, include_inactive)
    return [VetAvailabilityResponse.from_orm(avail) for avail in availability]


@router.post("/vet-availability", response_model=VetAvailabilityResponse, status_code=status.HTTP_201_CREATED)
async def create_vet_availability(
    availability_data: VetAvailabilityCreate,
    current_user: User = Depends(get_current_user),
    repo: VetAvailabilityRepository = Depends(get_vet_availability_repository)
):
    """Create new vet availability"""
    # TODO: Add proper authorization - only the vet or practice admin should be able to create
    
    availability = VetAvailability(**availability_data.dict())
    created_availability = await repo.create(availability)
    return VetAvailabilityResponse.from_orm(created_availability)


@router.put("/vet-availability/{availability_id}", response_model=VetAvailabilityResponse)
async def update_vet_availability(
    availability_id: uuid.UUID,
    availability_data: VetAvailabilityUpdate,
    current_user: User = Depends(get_current_user),
    repo: VetAvailabilityRepository = Depends(get_vet_availability_repository)
):
    """Update vet availability"""
    # TODO: Add proper authorization
    
    update_data = {k: v for k, v in availability_data.dict().items() if v is not None}
    updated_availability = await repo.update_by_id(availability_id, update_data)
    
    if not updated_availability:
        raise HTTPException(status_code=404, detail="Vet availability not found")
    
    return VetAvailabilityResponse.from_orm(updated_availability)


@router.delete("/vet-availability/{availability_id}", response_model=BaseResponse)
async def delete_vet_availability(
    availability_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repo: VetAvailabilityRepository = Depends(get_vet_availability_repository)
):
    """Delete vet availability"""
    # TODO: Add proper authorization
    
    success = await repo.delete_by_id(availability_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vet availability not found")
    
    return BaseResponse(message="Vet availability deleted successfully")


# ============================================================================
# RECURRING AVAILABILITY ENDPOINTS
# ============================================================================

@router.get("/recurring-availability/{vet_user_id}", response_model=List[RecurringAvailabilityResponse])
async def get_recurring_availability(
    vet_user_id: uuid.UUID,
    include_inactive: bool = Query(False, description="Include inactive schedules"),
    current_user: User = Depends(get_current_user),
    repo: RecurringAvailabilityRepository = Depends(get_recurring_availability_repository)
):
    """Get recurring availability for a vet"""
    # TODO: Add proper authorization
    
    schedules = await repo.get_by_vet_id(vet_user_id, include_inactive)
    return [RecurringAvailabilityResponse.from_orm(schedule) for schedule in schedules]


@router.post("/recurring-availability", response_model=RecurringAvailabilityResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring_availability(
    schedule_data: RecurringAvailabilityCreate,
    current_user: User = Depends(get_current_user),
    repo: RecurringAvailabilityRepository = Depends(get_recurring_availability_repository)
):
    """Create new recurring availability"""
    # TODO: Add proper authorization
    
    schedule = RecurringAvailability(**schedule_data.dict())
    created_schedule = await repo.create(schedule)
    return RecurringAvailabilityResponse.from_orm(created_schedule)


@router.put("/recurring-availability/{schedule_id}", response_model=RecurringAvailabilityResponse)
async def update_recurring_availability(
    schedule_id: uuid.UUID,
    schedule_data: RecurringAvailabilityUpdate,
    current_user: User = Depends(get_current_user),
    repo: RecurringAvailabilityRepository = Depends(get_recurring_availability_repository)
):
    """Update recurring availability"""
    # TODO: Add proper authorization
    
    update_data = {k: v for k, v in schedule_data.dict().items() if v is not None}
    updated_schedule = await repo.update_by_id(schedule_id, update_data)
    
    if not updated_schedule:
        raise HTTPException(status_code=404, detail="Recurring availability not found")
    
    return RecurringAvailabilityResponse.from_orm(updated_schedule)


@router.delete("/recurring-availability/{schedule_id}", response_model=BaseResponse)
async def delete_recurring_availability(
    schedule_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repo: RecurringAvailabilityRepository = Depends(get_recurring_availability_repository)
):
    """Delete recurring availability"""
    # TODO: Add proper authorization
    
    success = await repo.delete_by_id(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Recurring availability not found")
    
    return BaseResponse(message="Recurring availability deleted successfully")


@router.post("/recurring-availability/bulk", response_model=List[RecurringAvailabilityResponse], status_code=status.HTTP_201_CREATED)
async def create_bulk_recurring_availability(
    bulk_data: BulkRecurringAvailabilityCreate,
    current_user: User = Depends(get_current_user),
    repo: RecurringAvailabilityRepository = Depends(get_recurring_availability_repository)
):
    """Create multiple recurring availability schedules at once"""
    # TODO: Add proper authorization
    
    created_schedules = []
    for schedule_data in bulk_data.schedules:
        schedule = RecurringAvailability(
            vet_user_id=bulk_data.vet_user_id,
            practice_id=bulk_data.practice_id,
            **schedule_data.dict()
        )
        created = await repo.create(schedule)
        created_schedules.append(created)
    
    return [RecurringAvailabilityResponse.from_orm(schedule) for schedule in created_schedules]


# ============================================================================
# APPOINTMENT CONFLICT ENDPOINTS
# ============================================================================

@router.get("/conflicts/{appointment_id}", response_model=List[AppointmentConflictResponse])
async def get_appointment_conflicts(
    appointment_id: uuid.UUID,
    include_resolved: bool = Query(False, description="Include resolved conflicts"),
    current_user: User = Depends(get_current_user),
    repo: AppointmentConflictRepository = Depends(get_conflict_repository)
):
    """Get conflicts for a specific appointment"""
    # TODO: Add proper authorization
    
    conflicts = await repo.get_by_appointment_id(appointment_id, include_resolved)
    return [AppointmentConflictResponse.from_orm(conflict) for conflict in conflicts]


@router.get("/conflicts", response_model=List[AppointmentConflictResponse])
async def get_unresolved_conflicts(
    practice_id: Optional[uuid.UUID] = Query(None, description="Filter by practice"),
    current_user: User = Depends(get_current_user),
    repo: AppointmentConflictRepository = Depends(get_conflict_repository)
):
    """Get all unresolved conflicts"""
    # TODO: Add proper authorization
    
    conflicts = await repo.get_unresolved_conflicts(practice_id)
    return [AppointmentConflictResponse.from_orm(conflict) for conflict in conflicts]


@router.post("/conflicts", response_model=AppointmentConflictResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment_conflict(
    conflict_data: AppointmentConflictCreate,
    current_user: User = Depends(get_current_user),
    repo: AppointmentConflictRepository = Depends(get_conflict_repository)
):
    """Create new appointment conflict"""
    # TODO: Add proper authorization
    
    conflict = AppointmentConflict(**conflict_data.dict())
    created_conflict = await repo.create(conflict)
    return AppointmentConflictResponse.from_orm(created_conflict)


@router.put("/conflicts/{conflict_id}/resolve", response_model=AppointmentConflictResponse)
async def resolve_appointment_conflict(
    conflict_id: uuid.UUID,
    resolve_data: AppointmentConflictResolve,
    current_user: User = Depends(get_current_user),
    repo: AppointmentConflictRepository = Depends(get_conflict_repository)
):
    """Resolve an appointment conflict"""
    # TODO: Add proper authorization
    
    resolved_conflict = await repo.resolve_conflict(conflict_id, resolve_data.resolved_by_user_id)
    
    if not resolved_conflict:
        raise HTTPException(status_code=404, detail="Appointment conflict not found")
    
    return AppointmentConflictResponse.from_orm(resolved_conflict)


@router.get("/conflicts/statistics", response_model=ConflictStatistics)
async def get_conflict_statistics(
    practice_id: Optional[uuid.UUID] = Query(None, description="Filter by practice"),
    current_user: User = Depends(get_current_user),
    repo: AppointmentConflictRepository = Depends(get_conflict_repository)
):
    """Get conflict statistics"""
    # TODO: Add proper authorization
    
    stats = await repo.get_conflict_statistics(practice_id)
    return ConflictStatistics(**stats)


# ============================================================================
# SCHEDULING UTILITY ENDPOINTS
# ============================================================================

@router.get("/practice/{practice_id}/is-open")
async def check_practice_open(
    practice_id: uuid.UUID,
    check_datetime: datetime = Query(..., description="DateTime to check"),
    current_user: User = Depends(get_current_user),
    repo: PracticeHoursRepository = Depends(get_practice_hours_repository)
):
    """Check if practice is open at a specific datetime"""
    # TODO: Add proper authorization
    
    is_open = await repo.is_practice_open(practice_id, check_datetime)
    return {"practice_id": practice_id, "datetime": check_datetime, "is_open": is_open}


# TODO: Implement these advanced scheduling endpoints
# @router.post("/available-slots", response_model=AvailableSlotsResponse)
# async def get_available_slots(
#     request: AvailableSlotRequest,
#     current_user: User = Depends(get_current_user)
# ):
#     """Get available appointment slots for a practice/vet on a specific date"""
#     # This would require complex logic to:
#     # 1. Check practice hours
#     # 2. Check vet availability
#     # 3. Check existing appointments
#     # 4. Generate available slots
#     pass

# @router.post("/check-conflicts", response_model=ConflictCheckResponse)
# async def check_appointment_conflicts(
#     request: ConflictCheckRequest,
#     current_user: User = Depends(get_current_user)
# ):
#     """Check for conflicts when scheduling an appointment"""
#     # This would check for:
#     # 1. Double booking
#     # 2. Outside practice hours
#     # 3. Outside vet availability
#     # 4. Overlapping appointments
#     pass
