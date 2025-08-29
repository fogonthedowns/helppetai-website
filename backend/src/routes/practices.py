"""
Veterinary Practice REST API endpoints
"""

from typing import List
from fastapi import APIRouter, HTTPException, status, Path, Depends
from uuid import UUID, uuid4

from ..models.practice import (
    VeterinaryPractice, 
    VeterinaryPracticeCreate, 
    VeterinaryPracticeUpdate, 
    VeterinaryPracticeResponse
)
from ..repository.practice_repository import PracticeRepository
from ..auth.jwt_auth import get_current_user
from ..models.user import User, UserRole


router = APIRouter()


def get_practice_repository() -> PracticeRepository:
    """Dependency to get practice repository."""
    return PracticeRepository()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role for protected operations."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get(
    "/",
    response_model=List[VeterinaryPracticeResponse],
    status_code=status.HTTP_200_OK,
    summary="List all practices",
    description="Get list of all veterinary practices (public access)"
)
async def get_practices(
    repository: PracticeRepository = Depends(get_practice_repository)
) -> List[VeterinaryPracticeResponse]:
    """List all veterinary practices."""
    practices = await repository.get_all(is_active=True)
    
    return [
        VeterinaryPracticeResponse(
            uuid=practice.uuid,
            name=practice.name,
            admin_user_id=str(practice.admin_user_id),
            phone=practice.phone,
            email=practice.email,
            address=practice.address,
            license_number=practice.license_number,
            specialties=practice.specialties,
            created_at=practice.created_at,
            updated_at=practice.updated_at,
            is_active=practice.is_active
        )
        for practice in practices
    ]


@router.get(
    "/{practice_id}",
    response_model=VeterinaryPracticeResponse,
    status_code=status.HTTP_200_OK,
    summary="View single practice",
    description="Get details of a specific veterinary practice (public access)"
)
async def get_practice(
    practice_id: UUID = Path(..., description="Practice UUID"),
    repository: PracticeRepository = Depends(get_practice_repository)
) -> VeterinaryPracticeResponse:
    """Get a specific veterinary practice by UUID."""
    practice = await repository.get_by_uuid(str(practice_id))
    
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with UUID {practice_id} not found"
        )
    
    return VeterinaryPracticeResponse(
        uuid=practice.uuid,
        name=practice.name,
        admin_user_id=str(practice.admin_user_id),
        phone=practice.phone,
        email=practice.email,
        address=practice.address,
        license_number=practice.license_number,
        specialties=practice.specialties,
        created_at=practice.created_at,
        updated_at=practice.updated_at,
        is_active=practice.is_active
    )


@router.post(
    "/",
    response_model=VeterinaryPracticeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create practice",
    description="Create a new veterinary practice (admin only)"
)
async def create_practice(
    practice_data: VeterinaryPracticeCreate,
    repository: PracticeRepository = Depends(get_practice_repository),
    current_user: User = Depends(require_admin)
) -> VeterinaryPracticeResponse:
    """Create a new veterinary practice."""
    try:
        from beanie import PydanticObjectId
        
        # Create practice document
        practice = VeterinaryPractice(
            name=practice_data.name,
            admin_user_id=PydanticObjectId(practice_data.admin_user_id),
            phone=practice_data.phone,
            email=practice_data.email,
            address=practice_data.address,
            license_number=practice_data.license_number,
            specialties=practice_data.specialties
        )
        
        created_practice = await repository.create(practice)
        
        return VeterinaryPracticeResponse(
            uuid=created_practice.uuid,
            name=created_practice.name,
            admin_user_id=str(created_practice.admin_user_id),
            phone=created_practice.phone,
            email=created_practice.email,
            address=created_practice.address,
            license_number=created_practice.license_number,
            specialties=created_practice.specialties,
            created_at=created_practice.created_at,
            updated_at=created_practice.updated_at,
            is_active=created_practice.is_active
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating practice: {str(e)}"
        )


@router.put(
    "/{practice_id}",
    response_model=VeterinaryPracticeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update practice",
    description="Update an existing veterinary practice (admin only)"
)
async def update_practice(
    practice_id: UUID = Path(..., description="Practice UUID"),
    practice_update: VeterinaryPracticeUpdate = ...,
    repository: PracticeRepository = Depends(get_practice_repository),
    current_user: User = Depends(require_admin)
) -> VeterinaryPracticeResponse:
    """Update an existing veterinary practice."""
    # Convert update model to dict, excluding unset fields
    update_data = practice_update.dict(exclude_unset=True)
    
    updated_practice = await repository.update_by_uuid(str(practice_id), update_data)
    
    if not updated_practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with UUID {practice_id} not found"
        )
    
    return VeterinaryPracticeResponse(
        uuid=updated_practice.uuid,
        name=updated_practice.name,
        admin_user_id=str(updated_practice.admin_user_id),
        phone=updated_practice.phone,
        email=updated_practice.email,
        address=updated_practice.address,
        license_number=updated_practice.license_number,
        specialties=updated_practice.specialties,
        created_at=updated_practice.created_at,
        updated_at=updated_practice.updated_at,
        is_active=updated_practice.is_active
    )


@router.delete(
    "/{practice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete practice",
    description="Delete a veterinary practice (admin only)"
)
async def delete_practice(
    practice_id: UUID = Path(..., description="Practice UUID"),
    repository: PracticeRepository = Depends(get_practice_repository),
    current_user: User = Depends(require_admin)
) -> None:
    """Delete a veterinary practice."""
    deleted = await repository.delete_by_uuid(str(practice_id))
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with UUID {practice_id} not found"
        )
