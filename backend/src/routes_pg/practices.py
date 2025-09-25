"""
Veterinary Practice routes for PostgreSQL - HelpPet MVP
"""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..database_pg import get_db_session
from ..models_pg.practice import VeterinaryPractice
from ..models_pg.user import User, UserRole
from ..repositories_pg.practice_repository import PracticeRepository
from ..auth.jwt_auth_pg import get_current_user, require_admin

router = APIRouter()


class PracticeCreate(BaseModel):
    name: str
    admin_user_id: Optional[str] = None  # Frontend sends this
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None  # Frontend sends single address field
    license_number: Optional[str] = None
    specialties: List[str] = []  # Frontend sends specialties array
    description: Optional[str] = None
    website: Optional[str] = None
    accepts_new_patients: bool = True


class PracticeUpdate(BaseModel):
    name: Optional[str] = None
    admin_user_id: Optional[str] = None  # Frontend sends this
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None  # Frontend sends single address field
    license_number: Optional[str] = None
    specialties: Optional[List[str]] = None  # Frontend sends specialties array
    description: Optional[str] = None
    website: Optional[str] = None
    is_active: Optional[bool] = None
    accepts_new_patients: Optional[bool] = None


class PracticeResponse(BaseModel):
    uuid: str  # Frontend expects 'uuid', not 'id'
    name: str
    description: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None  # Frontend expects 'address'
    license_number: Optional[str] = None
    specialties: List[str] = []  # Frontend expects 'specialties' array
    admin_user_id: Optional[str] = None  # Frontend expects 'admin_user_id'
    is_active: bool
    accepts_new_patients: bool
    created_at: str
    updated_at: str


@router.get("/", response_model=List[PracticeResponse])
async def get_practices(
    active_only: bool = Query(True, description="Filter to active practices only"),
    accepting_patients: bool = Query(False, description="Filter to practices accepting new patients"),
    city: Optional[str] = Query(None, description="Filter by city"),
    state: Optional[str] = Query(None, description="Filter by state"),
    session: AsyncSession = Depends(get_db_session)
) -> List[PracticeResponse]:
    """Get list of veterinary practices (public endpoint)"""
    
    practice_repo = PracticeRepository(session)
    
    if city or state:
        practices = await practice_repo.search_by_location(city=city, state=state)
    elif accepting_patients:
        practices = await practice_repo.get_accepting_new_patients()
    elif active_only:
        practices = await practice_repo.get_active_practices()
    else:
        practices = await practice_repo.get_all()
    
    return [
        PracticeResponse(
            uuid=str(practice.id),
            name=practice.name,
            description=practice.description,
            phone=practice.phone,
            email=practice.email,
            website=practice.website,
            address=practice.full_address,
            license_number=practice.license_number,
            specialties=practice.specialties or [],
            admin_user_id=None,  # TODO: Add admin_user_id relationship
            is_active=practice.is_active,
            accepts_new_patients=practice.accepts_new_patients,
            created_at=practice.created_at.isoformat(),
            updated_at=practice.updated_at.isoformat()
        )
        for practice in practices
    ]


@router.get("/{practice_id}", response_model=PracticeResponse)
async def get_practice(
    practice_id: UUID = Path(..., description="Practice ID"),
    session: AsyncSession = Depends(get_db_session)
) -> PracticeResponse:
    """Get a specific practice by ID (public endpoint)"""
    
    practice_repo = PracticeRepository(session)
    practice = await practice_repo.get_by_id(practice_id)
    
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with ID {practice_id} not found"
        )
    
    return PracticeResponse(
        uuid=str(practice.id),
        name=practice.name,
        description=practice.description,
        phone=practice.phone,
        email=practice.email,
        website=practice.website,
        address=practice.full_address,
        license_number=practice.license_number,
        specialties=[],  # TODO: Add specialties field to database model
        admin_user_id=None,  # TODO: Add admin_user_id relationship
        is_active=practice.is_active,
        accepts_new_patients=practice.accepts_new_patients,
        created_at=practice.created_at.isoformat(),
        updated_at=practice.updated_at.isoformat()
    )


@router.post("/", response_model=PracticeResponse, status_code=status.HTTP_201_CREATED)
async def create_practice(
    practice_data: PracticeCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> PracticeResponse:
    """Create a new practice (authenticated users only)"""
    
    practice_repo = PracticeRepository(session)
    
    # Handle empty license number - convert to None for database
    license_number = practice_data.license_number.strip() if practice_data.license_number else None
    if not license_number:  # Empty string becomes None
        license_number = None
    
    # Check if license number already exists (only if not None)
    if license_number:
        if await practice_repo.license_number_exists(license_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License number already exists"
            )
    
    # Create new practice
    new_practice = VeterinaryPractice(
        name=practice_data.name,
        description=practice_data.description,
        phone=practice_data.phone,
        email=practice_data.email,
        website=practice_data.website,
        address_line1=practice_data.address,  # Store single address in address_line1
        license_number=license_number,  # Use processed license_number
        specialties=practice_data.specialties,
        accepts_new_patients=practice_data.accepts_new_patients
    )
    
    created_practice = await practice_repo.create(new_practice)
    
    return PracticeResponse(
        uuid=str(created_practice.id),
        name=created_practice.name,
        description=created_practice.description,
        phone=created_practice.phone,
        email=created_practice.email,
        website=created_practice.website,
        address=created_practice.full_address,
        license_number=created_practice.license_number,
        specialties=[],  # TODO: Add specialties field to database model
        admin_user_id=None,  # TODO: Add admin_user_id relationship
        is_active=created_practice.is_active,
        accepts_new_patients=created_practice.accepts_new_patients,
        created_at=created_practice.created_at.isoformat(),
        updated_at=created_practice.updated_at.isoformat()
    )


@router.put("/{practice_id}", response_model=PracticeResponse)
async def update_practice(
    practice_id: UUID = Path(..., description="Practice ID"),
    practice_update: PracticeUpdate = ...,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
) -> PracticeResponse:
    """Update an existing practice (admin only)"""
    
    practice_repo = PracticeRepository(session)
    
    # Check if practice exists
    practice = await practice_repo.get_by_id(practice_id)
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with ID {practice_id} not found"
        )
    
    # Handle empty license number - convert to None for database
    license_number = None
    if hasattr(practice_update, 'license_number') and practice_update.license_number is not None:
        license_number = practice_update.license_number.strip() if practice_update.license_number else None
        if not license_number:  # Empty string becomes None
            license_number = None
    
    # Check license number uniqueness if being updated (only if not None)
    if license_number and license_number != practice.license_number:
        if await practice_repo.license_number_exists(license_number, exclude_id=practice_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License number already exists"
            )
    
    # Update practice
    update_data = practice_update.dict(exclude_unset=True)
    
    # Handle license number conversion
    if 'license_number' in update_data:
        update_data['license_number'] = license_number
    
    # Handle address mapping: frontend sends 'address', we store in 'address_line1'
    if 'address' in update_data:
        update_data['address_line1'] = update_data.pop('address')
    
    # Remove admin_user_id as it's not a field in our model
    update_data.pop('admin_user_id', None)
    
    updated_practice = await practice_repo.update_by_id(practice_id, update_data)
    
    return PracticeResponse(
        uuid=str(updated_practice.id),
        name=updated_practice.name,
        description=updated_practice.description,
        phone=updated_practice.phone,
        email=updated_practice.email,
        website=updated_practice.website,
        address=updated_practice.full_address,
        license_number=updated_practice.license_number,
        specialties=[],  # TODO: Add specialties field to database model
        admin_user_id=None,  # TODO: Add admin_user_id relationship
        is_active=updated_practice.is_active,
        accepts_new_patients=updated_practice.accepts_new_patients,
        created_at=updated_practice.created_at.isoformat(),
        updated_at=updated_practice.updated_at.isoformat()
    )


@router.delete("/{practice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_practice(
    practice_id: UUID = Path(..., description="Practice ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
) -> None:
    """Delete a practice (admin only)"""
    
    practice_repo = PracticeRepository(session)
    
    deleted = await practice_repo.delete_by_id(practice_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with ID {practice_id} not found"
        )
