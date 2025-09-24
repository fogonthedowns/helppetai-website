"""
Unix-timestamp based Scheduling API routes

Endpoints used by the iOS app under /api/v1/scheduling-unix
"""

import uuid
from datetime import datetime, timedelta, date, time
from typing import List, Optional

import pytz
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database_pg import get_db_session
from ..models_pg.scheduling_unix import VetAvailability, AvailabilityType
# AppointmentUnix is deprecated - use regular appointments table instead
from ..models_pg.user import User
from ..models_pg.practice import VeterinaryPractice


router = APIRouter(prefix="/api/v1/scheduling-unix", tags=["scheduling-unix"])


# =============================================================================
# Schemas
# =============================================================================

class VetAvailabilityUnixCreate(BaseModel):
    vet_user_id: uuid.UUID = Field(..., description="Vet user ID")
    practice_id: uuid.UUID = Field(..., description="Practice ID")
    start_at: datetime = Field(..., description="UTC start timestamp")
    end_at: datetime = Field(..., description="UTC end timestamp")
    availability_type: AvailabilityType = Field(AvailabilityType.AVAILABLE, description="Type of availability")
    notes: Optional[str] = Field(None, max_length=500)


class VetAvailabilityUnixUpdate(BaseModel):
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    availability_type: Optional[AvailabilityType] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class VetAvailabilityUnixResponse(BaseModel):
    id: uuid.UUID
    vet_user_id: uuid.UUID
    practice_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    availability_type: AvailabilityType
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/vet-availability/{vet_user_id}", response_model=List[VetAvailabilityUnixResponse])
async def get_vet_availability_unix(
    vet_user_id: uuid.UUID,
    date_str: str = Query(..., alias="date", description="Local date (YYYY-MM-DD) in the provided timezone"),
    timezone_str: Optional[str] = Query(None, alias="timezone", description="Timezone identifier (e.g., America/Los_Angeles)"),
    include_inactive: bool = Query(False, description="Include inactive records"),
    db: AsyncSession = Depends(get_db_session),
):
    """Return Unix-timestamp availability for a vet on a given local date.

    Interprets the date in the provided timezone, converts to UTC day range, and
    returns records that overlap that UTC window. This ensures 5–6pm local times
    on 2025-09-23 are included when querying for date=2025-09-23 with the local timezone.
    """
    try:
        year, month, day = [int(x) for x in date_str.split("-")]
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid date format. Expected YYYY-MM-DD")

    # Resolve timezone: use query param if provided, otherwise fall back to the vet's practice timezone
    if timezone_str:
        try:
            tz = pytz.timezone(timezone_str)
        except Exception:
            raise HTTPException(status_code=422, detail=f"Unknown timezone: {timezone_str}")
    else:
        # Look up the vet's practice timezone
        result = await db.execute(
            select(VeterinaryPractice.timezone)
            .join(User, User.practice_id == VeterinaryPractice.id)
            .where(User.id == vet_user_id)
        )
        practice_timezone = result.scalar_one_or_none()
        if not practice_timezone:
            # Final fallback: UTC
            tz = pytz.UTC
        else:
            try:
                tz = pytz.timezone(practice_timezone)
            except Exception:
                tz = pytz.UTC

    # Compute local day start/end, then convert to UTC
    local_day_start = tz.localize(datetime(year, month, day, 0, 0, 0))
    local_day_end = local_day_start + timedelta(days=1)
    day_start_utc = local_day_start.astimezone(pytz.UTC)
    day_end_utc = local_day_end.astimezone(pytz.UTC)

    conditions = [
        VetAvailability.vet_user_id == vet_user_id,
        VetAvailability.start_at < day_end_utc,
        VetAvailability.end_at > day_start_utc,
    ]
    if not include_inactive:
        conditions.append(VetAvailability.is_active == True)  # noqa: E712

    query = (
        select(VetAvailability)
        .where(and_(*conditions))
        .order_by(VetAvailability.start_at)
    )

    result = await db.execute(query)
    records = list(result.scalars().all())
    return [VetAvailabilityUnixResponse.from_orm(r) for r in records]


@router.post("/vet-availability", response_model=VetAvailabilityUnixResponse, status_code=status.HTTP_201_CREATED)
async def create_vet_availability_unix(
    payload: VetAvailabilityUnixCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new Unix-timestamp availability window."""
    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=422, detail="end_at must be after start_at")

    availability = VetAvailability(
        vet_user_id=payload.vet_user_id,
        practice_id=payload.practice_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        availability_type=payload.availability_type,
        notes=payload.notes,
        is_active=True,
    )

    db.add(availability)
    await db.commit()
    await db.refresh(availability)
    return VetAvailabilityUnixResponse.from_orm(availability)


@router.put("/vet-availability/{availability_id}", response_model=VetAvailabilityUnixResponse)
async def update_vet_availability_unix(
    availability_id: uuid.UUID,
    payload: VetAvailabilityUnixUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    """Update an existing Unix-timestamp availability window."""
    result = await db.execute(
        select(VetAvailability).where(VetAvailability.id == availability_id)
    )
    availability = result.scalar_one_or_none()
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")

    if payload.start_at is not None:
        availability.start_at = payload.start_at
    if payload.end_at is not None:
        availability.end_at = payload.end_at
    if payload.availability_type is not None:
        availability.availability_type = payload.availability_type
    if payload.notes is not None:
        availability.notes = payload.notes
    if payload.is_active is not None:
        availability.is_active = payload.is_active

    if availability.end_at <= availability.start_at:
        raise HTTPException(status_code=422, detail="end_at must be after start_at")

    await db.commit()
    await db.refresh(availability)
    return VetAvailabilityUnixResponse.from_orm(availability)


@router.delete("/vet-availability/{availability_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vet_availability_unix(
    availability_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a Unix-timestamp availability window."""
    result = await db.execute(
        select(VetAvailability).where(VetAvailability.id == availability_id)
    )
    availability = result.scalar_one_or_none()
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")

    await db.delete(availability)
    await db.commit()
    return None


