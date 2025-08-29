"""
Pet Owner management routes for HelpPet
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.security import HTTPBearer

from ..models.pet_owner import (
    PetOwner,
    PetOwnerCreate, 
    PetOwnerUpdate,
    PetOwnerResponse
)
from ..models.user import User as UserDocument, UserRole
from ..repository.pet_owner_repository import PetOwnerRepository
from ..repository.pet_owner_practice_association_repository import PetOwnerPracticeAssociationRepository
from ..auth.jwt_auth import get_current_user
from beanie import PydanticObjectId

router = APIRouter(tags=["Pet Owners"])
security = HTTPBearer()


def get_pet_owner_repository() -> PetOwnerRepository:
    """Dependency to get pet owner repository instance."""
    return PetOwnerRepository()


def get_association_repository() -> PetOwnerPracticeAssociationRepository:
    """Dependency to get association repository instance."""
    return PetOwnerPracticeAssociationRepository()





def require_admin(current_user: UserDocument = Depends(get_current_user)) -> UserDocument:
    """Dependency that requires admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_accessible_pet_owner_uuids(
    current_user: UserDocument,
    association_repo: PetOwnerPracticeAssociationRepository
) -> List[str]:
    """
    Get pet owner UUIDs that the current user can access based on their role and practice.
    
    - Admin: Can access all pet owners
    - Vet Staff: Can only access pet owners associated with their practice
    """
    if current_user.role == UserRole.ADMIN:
        # Admin can access all pet owners - return None to indicate no filtering needed
        return None
    
    # For vet staff, get practice association
    # Note: For MVP, we'll need to link users to practices somehow
    # For now, assume practice_id is stored in user model
    if hasattr(current_user, 'practice_id') and current_user.practice_id:
        # Get pet owners associated with this practice
        practice_uuid = str(current_user.practice_id)  # Convert ObjectId to string if needed
        accessible_uuids = await association_repo.get_user_accessible_pet_owner_uuids(practice_uuid)
        return accessible_uuids
    
    # If no practice association, user can't access any pet owners
    return []


def require_admin_or_self(
    pet_owner_uuid: str,
    current_user: UserDocument = Depends(get_current_user),
    repository: PetOwnerRepository = Depends(get_pet_owner_repository)
) -> UserDocument:
    """Dependency that requires admin role OR the current user to be the pet owner."""
    # Admin can access anyone
    if current_user.role == UserRole.ADMIN:
        return current_user
    
    # Check if current user is the pet owner
    # We'll need to verify this in the route handler since it's async
    return current_user


@router.get(
    "/",
    response_model=List[PetOwnerResponse],
    status_code=status.HTTP_200_OK,
    summary="List pet owners",
    description="Get list of pet owners (Admin: all, Vet: only their practice's patients)"
)
async def get_pet_owners(
    repository: PetOwnerRepository = Depends(get_pet_owner_repository),
    association_repo: PetOwnerPracticeAssociationRepository = Depends(get_association_repository),
    current_user: UserDocument = Depends(get_current_user)
) -> List[PetOwnerResponse]:
    """List pet owners based on user permissions."""
    
    # Get accessible pet owner UUIDs based on user role
    accessible_uuids = await get_accessible_pet_owner_uuids(current_user, association_repo)
    
    if accessible_uuids is None:
        # Admin - get all pet owners
        pet_owners = await repository.get_all()
    elif len(accessible_uuids) == 0:
        # No accessible pet owners
        pet_owners = []
    else:
        # Filter by accessible UUIDs
        pet_owners = []
        for uuid in accessible_uuids:
            pet_owner = await repository.get_by_uuid(uuid)
            if pet_owner:
                pet_owners.append(pet_owner)
    
    return [
        PetOwnerResponse(
            uuid=pet_owner.uuid,
            user_id=str(pet_owner.user_id) if pet_owner.user_id else None,
            full_name=pet_owner.full_name,
            email=pet_owner.email,
            phone=pet_owner.phone,
            emergency_contact=pet_owner.emergency_contact,
            secondary_phone=pet_owner.secondary_phone,
            address=pet_owner.address,
            preferred_communication=pet_owner.preferred_communication,
            notifications_enabled=pet_owner.notifications_enabled,
            created_at=pet_owner.created_at,
            updated_at=pet_owner.updated_at
        )
        for pet_owner in pet_owners
    ]


@router.get(
    "/{pet_owner_uuid}",
    response_model=PetOwnerResponse,
    status_code=status.HTTP_200_OK,
    summary="View single pet owner",
    description="Get details of a specific pet owner (Admin | Vet with practice association)"
)
async def get_pet_owner(
    pet_owner_uuid: UUID = Path(..., description="Pet Owner UUID"),
    repository: PetOwnerRepository = Depends(get_pet_owner_repository),
    association_repo: PetOwnerPracticeAssociationRepository = Depends(get_association_repository),
    current_user: UserDocument = Depends(get_current_user)
) -> PetOwnerResponse:
    """Get a specific pet owner by UUID."""
    pet_owner = await repository.get_by_uuid(str(pet_owner_uuid))

    if not pet_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet owner with UUID {pet_owner_uuid} not found"
        )

    # Check access permissions
    accessible_uuids = await get_accessible_pet_owner_uuids(current_user, association_repo)
    
    if accessible_uuids is not None and str(pet_owner_uuid) not in accessible_uuids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this pet owner"
        )
    
    return PetOwnerResponse(
        uuid=pet_owner.uuid,
        user_id=str(pet_owner.user_id) if pet_owner.user_id else None,
        full_name=pet_owner.full_name,
        email=pet_owner.email,
        phone=pet_owner.phone,
        emergency_contact=pet_owner.emergency_contact,
        secondary_phone=pet_owner.secondary_phone,
        address=pet_owner.address,
        preferred_communication=pet_owner.preferred_communication,
        notifications_enabled=pet_owner.notifications_enabled,
        created_at=pet_owner.created_at,
        updated_at=pet_owner.updated_at
    )


@router.post(
    "/",
    response_model=PetOwnerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create pet owner",
    description="Create a new pet owner (Admin can create for any client)"
)
async def create_pet_owner(
    pet_owner_data: PetOwnerCreate,
    repository: PetOwnerRepository = Depends(get_pet_owner_repository),
    current_user: UserDocument = Depends(require_admin)
) -> PetOwnerResponse:
    """Create a new pet owner."""
    try:
        # Create pet owner document with provided data
        pet_owner = PetOwner(
            user_id=PydanticObjectId(pet_owner_data.user_id) if pet_owner_data.user_id else None,
            full_name=pet_owner_data.full_name,
            email=pet_owner_data.email,
            phone=pet_owner_data.phone,
            emergency_contact=pet_owner_data.emergency_contact,
            secondary_phone=pet_owner_data.secondary_phone,
            address=pet_owner_data.address,
            preferred_communication=pet_owner_data.preferred_communication,
            notifications_enabled=pet_owner_data.notifications_enabled
        )
        
        created_pet_owner = await repository.create(pet_owner)
        
        return PetOwnerResponse(
            uuid=created_pet_owner.uuid,
            user_id=str(created_pet_owner.user_id) if created_pet_owner.user_id else None,
            full_name=created_pet_owner.full_name,
            email=created_pet_owner.email,
            phone=created_pet_owner.phone,
            emergency_contact=created_pet_owner.emergency_contact,
            secondary_phone=created_pet_owner.secondary_phone,
            address=created_pet_owner.address,
            preferred_communication=created_pet_owner.preferred_communication,
            notifications_enabled=created_pet_owner.notifications_enabled,
            created_at=created_pet_owner.created_at,
            updated_at=created_pet_owner.updated_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating pet owner: {str(e)}"
        )


@router.put(
    "/{pet_owner_uuid}",
    response_model=PetOwnerResponse,
    status_code=status.HTTP_200_OK,
    summary="Update pet owner",
    description="Update an existing pet owner (Admin | Current User logged in must be that uuid)"
)
async def update_pet_owner(
    pet_owner_uuid: UUID = Path(..., description="Pet Owner UUID"),
    pet_owner_update: PetOwnerUpdate = ...,
    repository: PetOwnerRepository = Depends(get_pet_owner_repository),
    current_user: UserDocument = Depends(require_admin)
) -> PetOwnerResponse:
    """Update an existing pet owner."""
    # First check if pet owner exists
    pet_owner = await repository.get_by_uuid(str(pet_owner_uuid))
    if not pet_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet owner with UUID {pet_owner_uuid} not found"
        )
    
    # Convert update model to dict, excluding unset fields
    update_data = pet_owner_update.dict(exclude_unset=True)
    
    updated_pet_owner = await repository.update_by_uuid(str(pet_owner_uuid), update_data)
    
    if not updated_pet_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet owner with UUID {pet_owner_uuid} not found"
        )
    
    return PetOwnerResponse(
        uuid=updated_pet_owner.uuid,
        user_id=str(updated_pet_owner.user_id) if updated_pet_owner.user_id else None,
        full_name=updated_pet_owner.full_name,
        email=updated_pet_owner.email,
        phone=updated_pet_owner.phone,
        emergency_contact=updated_pet_owner.emergency_contact,
        secondary_phone=updated_pet_owner.secondary_phone,
        address=updated_pet_owner.address,
        preferred_communication=updated_pet_owner.preferred_communication,
        notifications_enabled=updated_pet_owner.notifications_enabled,
        created_at=updated_pet_owner.created_at,
        updated_at=updated_pet_owner.updated_at
    )


@router.delete(
    "/{pet_owner_uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete pet owner",
    description="Delete a pet owner (admin only)"
)
async def delete_pet_owner(
    pet_owner_uuid: UUID = Path(..., description="Pet Owner UUID"),
    repository: PetOwnerRepository = Depends(get_pet_owner_repository),
    current_user: UserDocument = Depends(require_admin)
) -> None:
    """Delete a pet owner (Admin only)."""
    deleted = await repository.delete_by_uuid(str(pet_owner_uuid))
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet owner with UUID {pet_owner_uuid} not found"
        )
