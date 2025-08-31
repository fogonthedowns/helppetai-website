"""
Visit Transcripts REST API Routes
Based on spec in docs/0009_VisitTranscript.md
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field

from ..auth.jwt_auth_pg import get_current_user
from ..models_pg.user import User
from ..models_pg.visit import Visit, VisitState
from ..models_pg.pet import Pet
from ..database_pg import get_db_session


router = APIRouter(prefix="/api/v1/visit-transcripts", tags=["visit-transcripts"])


# Pydantic models for visit transcripts
class VisitTranscriptCreate(BaseModel):
    pet_id: str
    visit_date: int  # Unix timestamp
    full_text: str
    audio_transcript_url: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    summary: Optional[str] = None


class VisitTranscriptUpdate(BaseModel):
    visit_date: Optional[int] = None
    full_text: Optional[str] = None
    audio_transcript_url: Optional[str] = None
    metadata: Optional[dict] = None
    summary: Optional[str] = None
    state: Optional[VisitState] = None


class VisitTranscriptResponse(BaseModel):
    uuid: str
    pet_id: str
    visit_date: int
    full_text: str
    audio_transcript_url: Optional[str] = None
    metadata: dict
    summary: Optional[str] = None
    state: VisitState
    created_at: str
    updated_at: str
    created_by: Optional[str] = None


# Helper functions
async def check_pet_access(pet_id: str, user: User, db: AsyncSession) -> Pet:
    """Check if user has access to the pet"""
    try:
        pet_uuid = uuid.UUID(pet_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pet ID format")
    
    # Get pet from database
    result = await db.execute(select(Pet).where(Pet.id == pet_uuid))
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    # Admin can access all pets
    if user.role == "ADMIN":
        return pet
    
    # Vet can access pets from their associated practices
    if user.role in ["VET_STAFF", "VET"]:
        # TODO: Check if user's practice is associated with pet owner
        return pet
    
    # Pet owner can access their own pets
    if user.role == "PET_OWNER":
        # TODO: Check if user owns this pet
        return pet
    
    raise HTTPException(status_code=403, detail="Access denied")


def visit_to_transcript_response(visit: Visit) -> VisitTranscriptResponse:
    """Convert Visit model to VisitTranscriptResponse"""
    return VisitTranscriptResponse(
        uuid=str(visit.id),
        pet_id=str(visit.pet_id),
        visit_date=int(visit.visit_date.timestamp()),
        full_text=visit.full_text,
        audio_transcript_url=visit.audio_transcript_url,
        metadata=visit.additional_data or {},
        summary=visit.summary,
        state=VisitState(visit.state),
        created_at=visit.created_at.isoformat(),
        updated_at=visit.updated_at.isoformat(),
        created_by=str(visit.created_by) if visit.created_by else None
    )


@router.get("/pet/{pet_uuid}")
async def list_pet_visit_transcripts(
    pet_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> List[VisitTranscriptResponse]:
    """
    List all visit transcripts for a pet
    Access: Admin | Pet Owner | Associated Vet
    """
    pet = await check_pet_access(pet_uuid, current_user, db)
    
    # Find all visits for this pet, ordered by visit date descending
    result = await db.execute(
        select(Visit)
        .where(Visit.pet_id == pet.id)
        .order_by(Visit.visit_date.desc())
    )
    visits = result.scalars().all()
    
    return [visit_to_transcript_response(visit) for visit in visits]


@router.get("/{transcript_uuid}")
async def get_visit_transcript(
    transcript_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> VisitTranscriptResponse:
    """
    View single visit transcript
    Access: Admin | Pet Owner | Associated Vet
    """
    try:
        visit_uuid = uuid.UUID(transcript_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transcript ID format")
    
    # Get visit from database
    result = await db.execute(select(Visit).where(Visit.id == visit_uuid))
    visit = result.scalar_one_or_none()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit transcript not found")
    
    # Check access to the pet
    await check_pet_access(str(visit.pet_id), current_user, db)
    
    return visit_to_transcript_response(visit)


@router.post("")
async def create_visit_transcript(
    transcript_data: VisitTranscriptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> VisitTranscriptResponse:
    """
    Create visit transcript
    Access: Vet or Admin only
    """
    if current_user.role not in ["VET_STAFF", "VET", "ADMIN"]:
        raise HTTPException(
            status_code=403, 
            detail="Only veterinarians and admins can create visit transcripts"
        )
    
    # Verify pet exists and user has access
    pet = await check_pet_access(transcript_data.pet_id, current_user, db)
    
    # Convert unix timestamp to datetime
    visit_datetime = datetime.fromtimestamp(transcript_data.visit_date)
    
    # Create new visit
    visit = Visit(
        pet_id=pet.id,
        practice_id=current_user.practice_id if hasattr(current_user, 'practice_id') else None,
        vet_user_id=current_user.id,
        visit_date=visit_datetime,
        full_text=transcript_data.full_text,
        audio_transcript_url=transcript_data.audio_transcript_url,
        summary=transcript_data.summary,
        state=VisitState.PROCESSED.value,  # Transcripts are for completed visits
        additional_data=transcript_data.metadata,
        created_by=current_user.id
    )
    
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    
    return visit_to_transcript_response(visit)


@router.put("/{transcript_uuid}")
async def update_visit_transcript(
    transcript_uuid: str,
    transcript_data: VisitTranscriptUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> VisitTranscriptResponse:
    """
    Update visit transcript
    Access: Admin | Creating Vet only
    """
    try:
        visit_uuid = uuid.UUID(transcript_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transcript ID format")
    
    # Get visit from database
    result = await db.execute(select(Visit).where(Visit.id == visit_uuid))
    visit = result.scalar_one_or_none()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit transcript not found")
    
    # Check permissions
    if current_user.role != "ADMIN" and visit.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only admins or the creating veterinarian can update this transcript"
        )
    
    # Update fields
    if transcript_data.visit_date is not None:
        visit.visit_date = datetime.fromtimestamp(transcript_data.visit_date)
    if transcript_data.full_text is not None:
        visit.full_text = transcript_data.full_text
    if transcript_data.summary is not None:
        visit.summary = transcript_data.summary
    if transcript_data.audio_transcript_url is not None:
        visit.audio_transcript_url = transcript_data.audio_transcript_url
    if transcript_data.metadata is not None:
        visit.additional_data = transcript_data.metadata
    if transcript_data.state is not None:
        visit.state = transcript_data.state.value
    
    visit.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(visit)
    
    return visit_to_transcript_response(visit)


@router.delete("/{transcript_uuid}")
async def delete_visit_transcript(
    transcript_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Delete visit transcript
    Access: Admin only
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only admins can delete visit transcripts"
        )
    
    try:
        visit_uuid = uuid.UUID(transcript_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transcript ID format")
    
    # Get visit from database
    result = await db.execute(select(Visit).where(Visit.id == visit_uuid))
    visit = result.scalar_one_or_none()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit transcript not found")
    
    await db.delete(visit)
    await db.commit()
    
    return {"message": "Visit transcript deleted successfully"}
