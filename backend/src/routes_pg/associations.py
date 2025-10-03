"""
Pet Owner Practice Association routes for PostgreSQL - HelpPet MVP
"""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..database_pg import get_db_session
from ..models_pg.pet_owner_practice_association import (
    PetOwnerPracticeAssociation, 
    AssociationStatus, 
    AssociationRequestType
)
from ..models_pg.user import User, UserRole
from ..repositories_pg.association_repository import AssociationRepository
from ..repositories_pg.pet_owner_repository import PetOwnerRepository
from ..repositories_pg.practice_repository import PracticeRepository
from ..auth.jwt_auth_pg import get_current_user, require_admin

router = APIRouter()


class AssociationCreate(BaseModel):
    pet_owner_id: str
    practice_id: str
    request_type: AssociationRequestType = AssociationRequestType.NEW_CLIENT
    notes: Optional[str] = None
    primary_contact: bool = True


class AssociationUpdate(BaseModel):
    request_type: Optional[AssociationRequestType] = None
    status: Optional[AssociationStatus] = None
    notes: Optional[str] = None
    primary_contact: Optional[bool] = None


class AssociationResponse(BaseModel):
    id: str
    pet_owner_id: str
    practice_id: str
    status: AssociationStatus
    request_type: AssociationRequestType
    requested_by_user_id: Optional[str] = None
    approved_by_user_id: Optional[str] = None
    requested_at: str
    approved_at: Optional[str] = None
    last_visit_date: Optional[str] = None
    notes: Optional[str] = None
    primary_contact: bool
    created_at: str
    updated_at: str


@router.post("/", response_model=AssociationResponse, status_code=status.HTTP_201_CREATED)
async def create_association(
    association_data: AssociationCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> AssociationResponse:
    """Create a new association between pet owner and practice"""
    
    association_repo = AssociationRepository(session)
    pet_owner_repo = PetOwnerRepository(session)
    practice_repo = PracticeRepository(session)
    
    # Verify pet owner exists
    pet_owner_id = UUID(association_data.pet_owner_id)
    pet_owner = await pet_owner_repo.get_by_id(pet_owner_id)
    if not pet_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet owner with ID {association_data.pet_owner_id} not found"
        )
    
    # Verify practice exists
    practice_id = UUID(association_data.practice_id)
    practice = await practice_repo.get_by_id(practice_id)
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with ID {association_data.practice_id} not found"
        )
    
    # Check if association already exists
    existing = await association_repo.check_association_exists(pet_owner_id, practice_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Association already exists between this pet owner and practice"
        )
    
    # Create association
    new_association = PetOwnerPracticeAssociation(
        pet_owner_id=pet_owner_id,
        practice_id=practice_id,
        request_type=association_data.request_type,
        notes=association_data.notes,
        primary_contact=association_data.primary_contact,
        requested_by_user_id=current_user.id,
        status=AssociationStatus.APPROVED if current_user.role in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN] else AssociationStatus.PENDING
    )
    
    created_association = await association_repo.create(new_association)
    
    return AssociationResponse(
        id=str(created_association.id),
        pet_owner_id=str(created_association.pet_owner_id),
        practice_id=str(created_association.practice_id),
        status=created_association.status,
        request_type=created_association.request_type,
        requested_by_user_id=str(created_association.requested_by_user_id) if created_association.requested_by_user_id else None,
        approved_by_user_id=str(created_association.approved_by_user_id) if created_association.approved_by_user_id else None,
        requested_at=created_association.requested_at.isoformat(),
        approved_at=created_association.approved_at.isoformat() if created_association.approved_at else None,
        last_visit_date=created_association.last_visit_date.isoformat() if created_association.last_visit_date else None,
        notes=created_association.notes,
        primary_contact=created_association.primary_contact,
        created_at=created_association.created_at.isoformat(),
        updated_at=created_association.updated_at.isoformat()
    )


@router.get("/practice/{practice_id}", response_model=List[AssociationResponse])
async def get_associations_for_practice(
    practice_id: UUID = Path(..., description="Practice ID"),
    status_filter: Optional[AssociationStatus] = Query(None, description="Filter by association status"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> List[AssociationResponse]:
    """Get associations for a practice"""
    
    association_repo = AssociationRepository(session)
    
    # Get associations based on status filter
    if status_filter:
        associations = await association_repo.get_by_practice_and_status(practice_id, status_filter)
    else:
        associations = await association_repo.get_by_practice_id(practice_id)
    
    return [
        AssociationResponse(
            id=str(assoc.id),
            pet_owner_id=str(assoc.pet_owner_id),
            practice_id=str(assoc.practice_id),
            status=assoc.status,
            request_type=assoc.request_type,
            requested_by_user_id=str(assoc.requested_by_user_id) if assoc.requested_by_user_id else None,
            approved_by_user_id=str(assoc.approved_by_user_id) if assoc.approved_by_user_id else None,
            requested_at=assoc.requested_at.isoformat(),
            approved_at=assoc.approved_at.isoformat() if assoc.approved_at else None,
            last_visit_date=assoc.last_visit_date.isoformat() if assoc.last_visit_date else None,
            notes=assoc.notes,
            primary_contact=assoc.primary_contact,
            created_at=assoc.created_at.isoformat(),
            updated_at=assoc.updated_at.isoformat()
        )
        for assoc in associations
    ]


@router.get("/pet-owner/{pet_owner_id}", response_model=List[AssociationResponse])
async def get_associations_for_pet_owner(
    pet_owner_id: UUID = Path(..., description="Pet Owner ID"),
    status_filter: Optional[AssociationStatus] = Query(None, description="Filter by association status"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> List[AssociationResponse]:
    """Get associations for a pet owner"""
    
    association_repo = AssociationRepository(session)
    
    # Get all associations for the pet owner
    associations = await association_repo.get_by_pet_owner_id(pet_owner_id)
    
    # Filter by status if provided
    if status_filter:
        associations = [assoc for assoc in associations if assoc.status == status_filter]
    
    return [
        AssociationResponse(
            id=str(assoc.id),
            pet_owner_id=str(assoc.pet_owner_id),
            practice_id=str(assoc.practice_id),
            status=assoc.status,
            request_type=assoc.request_type,
            requested_by_user_id=str(assoc.requested_by_user_id) if assoc.requested_by_user_id else None,
            approved_by_user_id=str(assoc.approved_by_user_id) if assoc.approved_by_user_id else None,
            requested_at=assoc.requested_at.isoformat(),
            approved_at=assoc.approved_at.isoformat() if assoc.approved_at else None,
            last_visit_date=assoc.last_visit_date.isoformat() if assoc.last_visit_date else None,
            notes=assoc.notes,
            primary_contact=assoc.primary_contact,
            created_at=assoc.created_at.isoformat(),
            updated_at=assoc.updated_at.isoformat()
        )
        for assoc in associations
    ]


@router.put("/{association_id}", response_model=AssociationResponse)
async def update_association(
    association_id: UUID = Path(..., description="Association ID"),
    association_update: AssociationUpdate = ...,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> AssociationResponse:
    """Update an association (Admin can update any, VET_STAFF/PRACTICE_ADMIN can update their practice's associations)"""
    
    association_repo = AssociationRepository(session)
    
    # Get the association
    association = await association_repo.get_by_id(association_id)
    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association with ID {association_id} not found"
        )
    
    # Check access permissions
    if current_user.role in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]:
        # Admin can update any association
        pass
    elif current_user.role in [UserRole.VET_STAFF, UserRole.PRACTICE_ADMIN]:
        # VET_STAFF and PRACTICE_ADMIN can only update associations for their practice
        if not current_user.practice_id or current_user.practice_id != association.practice_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update associations for your own practice"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Vet Staff access required to update associations"
        )
    
    # Update the association
    update_data = association_update.dict(exclude_unset=True)
    updated_association = await association_repo.update_by_id(association_id, update_data)
    
    if not updated_association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association with ID {association_id} not found"
        )
    
    return AssociationResponse(
        id=str(updated_association.id),
        pet_owner_id=str(updated_association.pet_owner_id),
        practice_id=str(updated_association.practice_id),
        status=updated_association.status,
        request_type=updated_association.request_type,
        requested_by_user_id=str(updated_association.requested_by_user_id) if updated_association.requested_by_user_id else None,
        approved_by_user_id=str(updated_association.approved_by_user_id) if updated_association.approved_by_user_id else None,
        requested_at=updated_association.requested_at.isoformat(),
        approved_at=updated_association.approved_at.isoformat() if updated_association.approved_at else None,
        last_visit_date=updated_association.last_visit_date.isoformat() if updated_association.last_visit_date else None,
        notes=updated_association.notes,
        primary_contact=updated_association.primary_contact,
        created_at=updated_association.created_at.isoformat(),
        updated_at=updated_association.updated_at.isoformat()
    )


@router.put("/{association_id}/approve", response_model=AssociationResponse)
async def approve_association(
    association_id: UUID = Path(..., description="Association ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> AssociationResponse:
    """Approve an association request (Admin or Practice staff only)"""
    
    # For now, require admin. Later we can add practice-specific permissions
    if current_user.role not in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to approve associations"
        )
    
    association_repo = AssociationRepository(session)
    association = await association_repo.approve_association(association_id, current_user.id)
    
    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association with ID {association_id} not found"
        )
    
    return AssociationResponse(
        id=str(association.id),
        pet_owner_id=str(association.pet_owner_id),
        practice_id=str(association.practice_id),
        status=association.status,
        request_type=association.request_type,
        requested_by_user_id=str(association.requested_by_user_id) if association.requested_by_user_id else None,
        approved_by_user_id=str(association.approved_by_user_id) if association.approved_by_user_id else None,
        requested_at=association.requested_at.isoformat(),
        approved_at=association.approved_at.isoformat() if association.approved_at else None,
        last_visit_date=association.last_visit_date.isoformat() if association.last_visit_date else None,
        notes=association.notes,
        primary_contact=association.primary_contact,
        created_at=association.created_at.isoformat(),
        updated_at=association.updated_at.isoformat()
    )


@router.put("/{association_id}/reject", response_model=AssociationResponse)
async def reject_association(
    association_id: UUID = Path(..., description="Association ID"),
    rejection_notes: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
) -> AssociationResponse:
    """Reject an association request (Admin only)"""
    
    association_repo = AssociationRepository(session)
    association = await association_repo.reject_association(association_id, current_user.id, rejection_notes)
    
    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association with ID {association_id} not found"
        )
    
    return AssociationResponse(
        id=str(association.id),
        pet_owner_id=str(association.pet_owner_id),
        practice_id=str(association.practice_id),
        status=association.status,
        request_type=association.request_type,
        requested_by_user_id=str(association.requested_by_user_id) if association.requested_by_user_id else None,
        approved_by_user_id=str(association.approved_by_user_id) if association.approved_by_user_id else None,
        requested_at=association.requested_at.isoformat(),
        approved_at=association.approved_at.isoformat() if association.approved_at else None,
        last_visit_date=association.last_visit_date.isoformat() if association.last_visit_date else None,
        notes=association.notes,
        primary_contact=association.primary_contact,
        created_at=association.created_at.isoformat(),
        updated_at=association.updated_at.isoformat()
    )


@router.delete("/{association_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_association(
    association_id: UUID = Path(..., description="Association ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> None:
    """Delete an association (Admin can delete any, VET_STAFF/PRACTICE_ADMIN can delete their practice's associations)"""
    
    association_repo = AssociationRepository(session)
    
    # Get the association first to check permissions
    association = await association_repo.get_by_id(association_id)
    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association with ID {association_id} not found"
        )
    
    # Check access permissions
    if current_user.role in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]:
        # Admin can delete any association
        pass
    elif current_user.role in [UserRole.VET_STAFF, UserRole.PRACTICE_ADMIN]:
        # VET_STAFF and PRACTICE_ADMIN can only delete associations for their practice
        if not current_user.practice_id or current_user.practice_id != association.practice_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete associations for your own practice"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Vet Staff access required to delete associations"
        )
    
    # Delete the association
    deleted = await association_repo.delete_by_id(association_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association with ID {association_id} not found"
        )
