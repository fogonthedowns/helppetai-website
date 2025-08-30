"""
Pet management routes for PostgreSQL - HelpPet MVP
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database_pg import get_db_session
from ..models_pg.user import User
from ..models_pg.pet import Pet
from ..models.pet_schemas import (
    PetCreate, PetUpdate, PetResponse, PetWithOwnerResponse, 
    PetListResponse, PetSearchRequest
)
from ..repositories_pg.pet_repository import PetRepository
from ..repositories_pg.pet_owner_repository import PetOwnerRepository
from ..repositories_pg.association_repository import AssociationRepository
from ..models_pg.pet_owner_practice_association import AssociationStatus
from ..auth.jwt_auth_pg import get_current_user

router = APIRouter(prefix="/api/v1/pets", tags=["pets"])


async def get_pet_repository(session: AsyncSession = Depends(get_db_session)) -> PetRepository:
    """Dependency to get pet repository"""
    return PetRepository(session)


async def get_pet_owner_repository(session: AsyncSession = Depends(get_db_session)) -> PetOwnerRepository:
    """Dependency to get pet owner repository"""
    return PetOwnerRepository(session)


async def get_association_repository(session: AsyncSession = Depends(get_db_session)) -> AssociationRepository:
    """Dependency to get association repository"""
    return AssociationRepository(session)


async def check_pet_access(
    pet_id: uuid.UUID,
    current_user: User,
    pet_repo: PetRepository,
    pet_owner_repo: PetOwnerRepository,
    association_repo: AssociationRepository
) -> Pet:
    """Check if user has access to a specific pet"""
    pet = await pet_repo.get_with_owner(pet_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found"
        )
    
    # Admin can access all pets
    if current_user.role == "ADMIN":
        return pet
    
    # VET_STAFF can access pets from their practice
    if current_user.role == "VET_STAFF" and current_user.practice_id:
        association = await association_repo.check_association_exists(
            pet.owner_id, current_user.practice_id
        )
        if association and association.status == AssociationStatus.APPROVED:
            return pet
    
    # Pet owners can access their own pets (if they have a user account)
    if pet.owner.user_id == current_user.id:
        return pet
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied to this pet"
    )


@router.get("/", response_model=PetListResponse)
async def list_pets(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_user),
    pet_repo: PetRepository = Depends(get_pet_repository)
):
    """
    List all pets (Admin only)
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can list all pets"
        )
    
    pets = await pet_repo.get_all_with_owners(include_inactive=include_inactive)
    
    # Simple pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_pets = pets[start_idx:end_idx]
    
    return PetListResponse(
        pets=[PetResponse.model_validate(pet) for pet in paginated_pets],
        total=len(pets),
        page=page,
        per_page=per_page
    )


@router.get("/owner/{owner_uuid}", response_model=List[PetResponse])
async def list_pets_by_owner(
    owner_uuid: uuid.UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_user),
    pet_repo: PetRepository = Depends(get_pet_repository),
    pet_owner_repo: PetOwnerRepository = Depends(get_pet_owner_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    List pets by owner (Admin | Owner | Associated Vet)
    """
    # Check if pet owner exists
    pet_owner = await pet_owner_repo.get_by_id(owner_uuid)
    if not pet_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet owner not found"
        )
    
    # Check access permissions
    has_access = False
    
    if current_user.role == "ADMIN":
        has_access = True
    elif current_user.role == "VET_STAFF" and current_user.practice_id:
        # Check if vet's practice is associated with this pet owner
        association = await association_repo.check_association_exists(
            owner_uuid, current_user.practice_id
        )
        has_access = association and association.status == AssociationStatus.APPROVED
    elif pet_owner.user_id == current_user.id:
        # Pet owner accessing their own pets
        has_access = True
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this pet owner's pets"
        )
    
    pets = await pet_repo.get_by_owner_id(owner_uuid, include_inactive=include_inactive)
    return [PetResponse.model_validate(pet) for pet in pets]


@router.get("/{uuid}", response_model=PetWithOwnerResponse)
async def get_pet(
    uuid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    pet_repo: PetRepository = Depends(get_pet_repository),
    pet_owner_repo: PetOwnerRepository = Depends(get_pet_owner_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    View single pet (Admin | Owner | Associated Vet)
    """
    pet = await check_pet_access(
        uuid, current_user, pet_repo, pet_owner_repo, association_repo
    )
    
    return PetWithOwnerResponse.model_validate(pet)


@router.post("/", response_model=PetResponse)
async def create_pet(
    pet_data: PetCreate,
    current_user: User = Depends(get_current_user),
    pet_repo: PetRepository = Depends(get_pet_repository),
    pet_owner_repo: PetOwnerRepository = Depends(get_pet_owner_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    Create pet (Must be logged in)
    """
    # Check if pet owner exists
    pet_owner = await pet_owner_repo.get_by_id(pet_data.owner_id)
    if not pet_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet owner not found"
        )
    
    # Check access permissions for creating pets for this owner
    has_access = False
    
    if current_user.role == "ADMIN":
        has_access = True
    elif current_user.role == "VET_STAFF" and current_user.practice_id:
        # Check if vet's practice is associated with this pet owner
        association = await association_repo.check_association_exists(
            pet_data.owner_id, current_user.practice_id
        )
        has_access = association and association.status == AssociationStatus.APPROVED
    elif pet_owner.user_id == current_user.id:
        # Pet owner creating their own pet
        has_access = True
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to create pets for this owner"
        )
    
    # Check for duplicate microchip ID if provided
    if pet_data.microchip_id:
        existing_pet = await pet_repo.get_by_microchip_id(pet_data.microchip_id)
        if existing_pet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A pet with this microchip ID already exists"
            )
    
    # Create the pet
    pet_dict = pet_data.model_dump()
    pet = Pet(**pet_dict)
    
    created_pet = await pet_repo.create(pet)
    return PetResponse.model_validate(created_pet)


@router.put("/{uuid}", response_model=PetResponse)
async def update_pet(
    uuid: uuid.UUID,
    pet_data: PetUpdate,
    current_user: User = Depends(get_current_user),
    pet_repo: PetRepository = Depends(get_pet_repository),
    pet_owner_repo: PetOwnerRepository = Depends(get_pet_owner_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    Update pet (Admin | VET_STAFF | Pet Owner)
    """
    pet = await check_pet_access(
        uuid, current_user, pet_repo, pet_owner_repo, association_repo
    )
    
    # Admin, VET_STAFF (for their practice), and Pet Owner can update pets
    can_update = False
    
    if current_user.role == "ADMIN":
        can_update = True
    elif current_user.role == "VET_STAFF" and current_user.practice_id:
        # VET_STAFF can update pets from their practice
        association = await association_repo.check_association_exists(
            pet.owner_id, current_user.practice_id
        )
        can_update = association and association.status == AssociationStatus.APPROVED
    elif pet.owner.user_id == current_user.id:
        # Pet owner can update their own pets
        can_update = True
    
    if not can_update:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to update this pet"
        )
    
    # Check for duplicate microchip ID if being updated
    if pet_data.microchip_id and pet_data.microchip_id != pet.microchip_id:
        existing_pet = await pet_repo.get_by_microchip_id(pet_data.microchip_id)
        if existing_pet and existing_pet.id != uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A pet with this microchip ID already exists"
            )
    
    # Update the pet
    update_data = pet_data.model_dump(exclude_unset=True)
    updated_pet = await pet_repo.update_by_id(uuid, update_data)
    
    if not updated_pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found"
        )
    
    return PetResponse.model_validate(updated_pet)


@router.delete("/{uuid}")
async def delete_pet(
    uuid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    pet_repo: PetRepository = Depends(get_pet_repository),
    pet_owner_repo: PetOwnerRepository = Depends(get_pet_owner_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    Delete pet (Admin | VET_STAFF | Pet Owner)
    """
    pet = await check_pet_access(
        uuid, current_user, pet_repo, pet_owner_repo, association_repo
    )
    
    # Admin, VET_STAFF (for their practice), and Pet Owner can delete pets
    can_delete = False
    
    if current_user.role == "ADMIN":
        can_delete = True
    elif current_user.role == "VET_STAFF" and current_user.practice_id:
        # VET_STAFF can delete pets from their practice
        association = await association_repo.check_association_exists(
            pet.owner_id, current_user.practice_id
        )
        can_delete = association and association.status == AssociationStatus.APPROVED
    elif pet.owner.user_id == current_user.id:
        # Pet owner can delete their own pets
        can_delete = True
    
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to delete this pet"
        )
    
    # Soft delete by deactivating
    await pet_repo.deactivate(uuid)
    
    return {"message": "Pet deleted successfully"}


@router.post("/{uuid}/reactivate", response_model=PetResponse)
async def reactivate_pet(
    uuid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    pet_repo: PetRepository = Depends(get_pet_repository),
    pet_owner_repo: PetOwnerRepository = Depends(get_pet_owner_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    Reactivate a deactivated pet (Admin | VET_STAFF | Pet Owner)
    """
    pet = await pet_repo.get_by_id(uuid)  # Get even if inactive
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found"
        )
    
    # Admin, VET_STAFF (for their practice), and Pet Owner can reactivate pets
    can_reactivate = False
    
    if current_user.role == "ADMIN":
        can_reactivate = True
    elif current_user.role == "VET_STAFF" and current_user.practice_id:
        # VET_STAFF can reactivate pets from their practice
        association = await association_repo.check_association_exists(
            pet.owner_id, current_user.practice_id
        )
        can_reactivate = association and association.status == AssociationStatus.APPROVED
    elif pet.owner.user_id == current_user.id:
        # Pet owner can reactivate their own pets
        can_reactivate = True
    
    if not can_reactivate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to reactivate this pet"
        )
    
    reactivated_pet = await pet_repo.reactivate(uuid)
    return PetResponse.model_validate(reactivated_pet)
