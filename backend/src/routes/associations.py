"""
Pet Owner Practice Association routes for HelpPet MVP
"""

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.security import HTTPBearer

from ..models.pet_owner_practice_association import (
    PetOwnerPracticeAssociation,
    AssociationRequest,
    AssociationUpdate,
    AssociationResponse,
    AssociationStatus
)
from ..models.user import User as UserDocument, UserRole
from ..repository.pet_owner_practice_association_repository import PetOwnerPracticeAssociationRepository
from ..repository.pet_owner_repository import PetOwnerRepository
from ..repository.practice_repository import PracticeRepository
from ..auth.jwt_auth import get_current_user
from beanie import PydanticObjectId

router = APIRouter(tags=["Pet Owner Practice Associations"])
security = HTTPBearer()


def get_association_repository() -> PetOwnerPracticeAssociationRepository:
    """Dependency to get association repository instance."""
    return PetOwnerPracticeAssociationRepository()


def get_pet_owner_repository() -> PetOwnerRepository:
    """Dependency to get pet owner repository instance."""
    return PetOwnerRepository()


def get_practice_repository() -> PracticeRepository:
    """Dependency to get practice repository instance."""
    return PracticeRepository()


def require_admin(current_user: UserDocument = Depends(get_current_user)) -> UserDocument:
    """Dependency that requires admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.post(
    "/",
    response_model=AssociationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create association request",
    description="Create a new association between pet owner and practice"
)
async def create_association(
    association_data: AssociationRequest,
    repository: PetOwnerPracticeAssociationRepository = Depends(get_association_repository),
    pet_owner_repo: PetOwnerRepository = Depends(get_pet_owner_repository),
    practice_repo: PracticeRepository = Depends(get_practice_repository),
    current_user: UserDocument = Depends(get_current_user)
) -> AssociationResponse:
    """Create a new pet owner-practice association."""
    
    # Verify pet owner exists
    pet_owner = await pet_owner_repo.get_by_uuid(association_data.pet_owner_uuid)
    if not pet_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet owner with UUID {association_data.pet_owner_uuid} not found"
        )
    
    # Verify practice exists
    practice = await practice_repo.get_by_uuid(association_data.practice_uuid)
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with UUID {association_data.practice_uuid} not found"
        )
    
    # Check if association already exists
    existing = await repository.check_association_exists(
        association_data.pet_owner_uuid,
        association_data.practice_uuid
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Association already exists between this pet owner and practice"
        )
    
    try:
        # Create association
        association = PetOwnerPracticeAssociation(
            pet_owner_uuid=association_data.pet_owner_uuid,
            practice_uuid=association_data.practice_uuid,
            request_type=association_data.request_type,
            notes=association_data.notes,
            primary_contact=association_data.primary_contact,
            requested_by_user_id=current_user.id,
            status=AssociationStatus.APPROVED if current_user.role == UserRole.ADMIN else AssociationStatus.PENDING
        )
        
        created_association = await repository.create(association)
        
        return AssociationResponse(
            uuid=created_association.uuid,
            pet_owner_uuid=created_association.pet_owner_uuid,
            practice_uuid=created_association.practice_uuid,
            status=created_association.status,
            request_type=created_association.request_type,
            requested_by_user_id=str(created_association.requested_by_user_id) if created_association.requested_by_user_id else None,
            approved_by_user_id=str(created_association.approved_by_user_id) if created_association.approved_by_user_id else None,
            requested_at=created_association.requested_at,
            approved_at=created_association.approved_at,
            last_visit_date=created_association.last_visit_date,
            notes=created_association.notes,
            primary_contact=created_association.primary_contact,
            created_at=created_association.created_at,
            updated_at=created_association.updated_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating association: {str(e)}"
        )


@router.get(
    "/practice/{practice_uuid}",
    response_model=List[AssociationResponse],
    summary="Get associations for practice",
    description="Get all associations for a specific practice"
)
async def get_associations_for_practice(
    practice_uuid: UUID = Path(..., description="Practice UUID"),
    status_filter: AssociationStatus = None,
    repository: PetOwnerPracticeAssociationRepository = Depends(get_association_repository),
    current_user: UserDocument = Depends(get_current_user)
) -> List[AssociationResponse]:
    """Get associations for a practice."""
    
    practice_uuid_str = str(practice_uuid)
    
    # Get associations based on status filter
    if status_filter:
        associations = await repository.get_by_practice_uuid_and_status(practice_uuid_str, status_filter)
    else:
        associations = await repository.get_by_practice_uuid(practice_uuid_str)
    
    return [
        AssociationResponse(
            uuid=assoc.uuid,
            pet_owner_uuid=assoc.pet_owner_uuid,
            practice_uuid=assoc.practice_uuid,
            status=assoc.status,
            request_type=assoc.request_type,
            requested_by_user_id=str(assoc.requested_by_user_id) if assoc.requested_by_user_id else None,
            approved_by_user_id=str(assoc.approved_by_user_id) if assoc.approved_by_user_id else None,
            requested_at=assoc.requested_at,
            approved_at=assoc.approved_at,
            last_visit_date=assoc.last_visit_date,
            notes=assoc.notes,
            primary_contact=assoc.primary_contact,
            created_at=assoc.created_at,
            updated_at=assoc.updated_at
        )
        for assoc in associations
    ]


@router.put(
    "/{association_uuid}/approve",
    response_model=AssociationResponse,
    summary="Approve association",
    description="Approve a pending association request (Admin or Practice staff only)"
)
async def approve_association(
    association_uuid: UUID = Path(..., description="Association UUID"),
    repository: PetOwnerPracticeAssociationRepository = Depends(get_association_repository),
    current_user: UserDocument = Depends(get_current_user)
) -> AssociationResponse:
    """Approve an association request."""
    
    # For now, require admin. Later we can add practice-specific permissions
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to approve associations"
        )
    
    association = await repository.approve_association(str(association_uuid), str(current_user.id))
    
    if not association:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association with UUID {association_uuid} not found"
        )
    
    return AssociationResponse(
        uuid=association.uuid,
        pet_owner_uuid=association.pet_owner_uuid,
        practice_uuid=association.practice_uuid,
        status=association.status,
        request_type=association.request_type,
        requested_by_user_id=str(association.requested_by_user_id) if association.requested_by_user_id else None,
        approved_by_user_id=str(association.approved_by_user_id) if association.approved_by_user_id else None,
        requested_at=association.requested_at,
        approved_at=association.approved_at,
        last_visit_date=association.last_visit_date,
        notes=association.notes,
        primary_contact=association.primary_contact,
        created_at=association.created_at,
        updated_at=association.updated_at
    )


@router.delete(
    "/{association_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete association",
    description="Delete an association (Admin only)"
)
async def delete_association(
    association_uuid: UUID = Path(..., description="Association UUID"),
    repository: PetOwnerPracticeAssociationRepository = Depends(get_association_repository),
    current_user: UserDocument = Depends(require_admin)
) -> None:
    """Delete an association."""
    
    deleted = await repository.delete_by_uuid(str(association_uuid))
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Association with UUID {association_uuid} not found"
        )
