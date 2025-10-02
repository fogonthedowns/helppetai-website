"""
Pet Owner routes for PostgreSQL - HelpPet MVP
"""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..database_pg import get_db_session
from ..models_pg.pet_owner import PetOwner, PreferredCommunication
from ..models_pg.user import User, UserRole
from ..repositories_pg.pet_owner_repository import PetOwnerRepository
from ..repositories_pg.association_repository import AssociationRepository
from ..auth.jwt_auth_pg import get_current_user, require_admin

router = APIRouter()


class PetOwnerCreate(BaseModel):
    user_id: Optional[str] = None
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    secondary_phone: Optional[str] = None
    address: Optional[str] = None
    preferred_communication: PreferredCommunication = PreferredCommunication.EMAIL
    notifications_enabled: bool = True


class PetOwnerUpdate(BaseModel):
    user_id: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    secondary_phone: Optional[str] = None
    address: Optional[str] = None
    preferred_communication: Optional[PreferredCommunication] = None
    notifications_enabled: Optional[bool] = None


class PetOwnerResponse(BaseModel):
    uuid: str  # Frontend expects 'uuid', not 'id'
    user_id: Optional[str] = None
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    secondary_phone: Optional[str] = None
    address: Optional[str] = None
    preferred_communication: PreferredCommunication
    notifications_enabled: bool
    created_at: str
    updated_at: str


async def get_accessible_pet_owner_ids(
    current_user: User,
    association_repo: AssociationRepository
) -> Optional[List[UUID]]:
    """
    Get pet owner IDs that the current user can access based on their role and practice.
    
    - Admin: Can access all pet owners (returns None to indicate no filtering)
    - Vet Staff: Can only access pet owners associated with their practice
    """
    if current_user.role in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]:
        return None  # Admin can access all
    
    # For vet staff, get pet owners associated with their practice
    if current_user.role == UserRole.VET_STAFF:
        if not current_user.practice_id:
            # VET_STAFF without practice_id can't access any pet owners
            return []
        
        # Get all approved pet owners associated with this practice
        pet_owner_ids = await association_repo.get_pet_owners_for_practice(
            current_user.practice_id
        )
        return pet_owner_ids
    
    # If no practice association or other role, user can't access any pet owners
    return []


@router.get("/", response_model=List[PetOwnerResponse])
async def get_pet_owners(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> List[PetOwnerResponse]:
    """List pet owners based on user permissions (Admin: all, Vet: only their practice's patients)"""
    
    pet_owner_repo = PetOwnerRepository(session)
    association_repo = AssociationRepository(session)
    
    # Get accessible pet owner IDs based on user role
    accessible_ids = await get_accessible_pet_owner_ids(current_user, association_repo)
    
    if accessible_ids is None:
        # Admin - get all pet owners
        pet_owners = await pet_owner_repo.get_all()
    elif len(accessible_ids) == 0:
        # No accessible pet owners
        pet_owners = []
    else:
        # Filter by accessible IDs
        pet_owners = []
        for pet_owner_id in accessible_ids:
            pet_owner = await pet_owner_repo.get_by_id(pet_owner_id)
            if pet_owner:
                pet_owners.append(pet_owner)
    
    return [
        PetOwnerResponse(
            uuid=str(pet_owner.id),
            user_id=str(pet_owner.user_id) if pet_owner.user_id else None,
            full_name=pet_owner.full_name,
            email=pet_owner.email,
            phone=pet_owner.phone,
            emergency_contact=pet_owner.emergency_contact,
            secondary_phone=pet_owner.secondary_phone,
            address=pet_owner.address,
            preferred_communication=pet_owner.preferred_communication,
            notifications_enabled=pet_owner.notifications_enabled,
            created_at=pet_owner.created_at.isoformat(),
            updated_at=pet_owner.updated_at.isoformat()
        )
        for pet_owner in pet_owners
    ]


@router.get("/{pet_owner_id}", response_model=PetOwnerResponse)
async def get_pet_owner(
    pet_owner_id: UUID = Path(..., description="Pet Owner ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> PetOwnerResponse:
    """Get details of a specific pet owner (Admin | Vet with practice association)"""
    
    pet_owner_repo = PetOwnerRepository(session)
    association_repo = AssociationRepository(session)
    
    pet_owner = await pet_owner_repo.get_by_id(pet_owner_id)
    if not pet_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet owner with ID {pet_owner_id} not found"
        )
    
    # Check access permissions
    accessible_ids = await get_accessible_pet_owner_ids(current_user, association_repo)
    
    if accessible_ids is not None and pet_owner_id not in accessible_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this pet owner"
        )
    
    return PetOwnerResponse(
        uuid=str(pet_owner.id),
        user_id=str(pet_owner.user_id) if pet_owner.user_id else None,
        full_name=pet_owner.full_name,
        email=pet_owner.email,
        phone=pet_owner.phone,
        emergency_contact=pet_owner.emergency_contact,
        secondary_phone=pet_owner.secondary_phone,
        address=pet_owner.address,
        preferred_communication=pet_owner.preferred_communication,
        notifications_enabled=pet_owner.notifications_enabled,
        created_at=pet_owner.created_at.isoformat(),
        updated_at=pet_owner.updated_at.isoformat()
    )


@router.post("/", response_model=PetOwnerResponse, status_code=status.HTTP_201_CREATED)
async def create_pet_owner(
    pet_owner_data: PetOwnerCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> PetOwnerResponse:
    """Create a new pet owner (Admin and Vet Staff can create pet owners)"""
    
    # Check if user can create pet owners
    if current_user.role not in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN, UserRole.VET_STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Vet Staff access required to create pet owners"
        )
    
    pet_owner_repo = PetOwnerRepository(session)
    
    # Check if email already exists
    if pet_owner_data.email:
        if await pet_owner_repo.email_exists(pet_owner_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Check if phone already exists
    if pet_owner_data.phone:
        if await pet_owner_repo.phone_exists(pet_owner_data.phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists"
            )
    
    # Create pet owner
    new_pet_owner = PetOwner(
        user_id=UUID(pet_owner_data.user_id) if pet_owner_data.user_id and pet_owner_data.user_id.strip() else None,
        full_name=pet_owner_data.full_name,
        email=pet_owner_data.email,
        phone=pet_owner_data.phone,
        emergency_contact=pet_owner_data.emergency_contact,
        secondary_phone=pet_owner_data.secondary_phone,
        address=pet_owner_data.address,
        preferred_communication=pet_owner_data.preferred_communication,
        notifications_enabled=pet_owner_data.notifications_enabled
    )
    
    created_pet_owner = await pet_owner_repo.create(new_pet_owner)
    
    # Auto-create practice association for VET_STAFF users
    if current_user.role == UserRole.VET_STAFF and current_user.practice_id:
        from ..models_pg.pet_owner_practice_association import PetOwnerPracticeAssociation, AssociationStatus, AssociationRequestType
        
        association_repo = AssociationRepository(session)
        
        # Check if association already exists (in case frontend created it)
        existing_association = await association_repo.check_association_exists(
            created_pet_owner.id, current_user.practice_id
        )
        
        if not existing_association:
            # Create automatic association for VET_STAFF
            auto_association = PetOwnerPracticeAssociation(
                pet_owner_id=created_pet_owner.id,
                practice_id=current_user.practice_id,
                request_type=AssociationRequestType.NEW_CLIENT,
                notes="Automatically created by vet staff",
                primary_contact=True,
                requested_by_user_id=current_user.id,
                status=AssociationStatus.APPROVED  # Auto-approve for VET_STAFF
            )
            
            await association_repo.create(auto_association)
    
    return PetOwnerResponse(
        uuid=str(created_pet_owner.id),
        user_id=str(created_pet_owner.user_id) if created_pet_owner.user_id else None,
        full_name=created_pet_owner.full_name,
        email=created_pet_owner.email,
        phone=created_pet_owner.phone,
        emergency_contact=created_pet_owner.emergency_contact,
        secondary_phone=created_pet_owner.secondary_phone,
        address=created_pet_owner.address,
        preferred_communication=created_pet_owner.preferred_communication,
        notifications_enabled=created_pet_owner.notifications_enabled,
        created_at=created_pet_owner.created_at.isoformat(),
        updated_at=created_pet_owner.updated_at.isoformat()
    )


@router.put("/{pet_owner_id}", response_model=PetOwnerResponse)
async def update_pet_owner(
    pet_owner_id: UUID = Path(..., description="Pet Owner ID"),
    pet_owner_update: PetOwnerUpdate = ...,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> PetOwnerResponse:
    """Update an existing pet owner (Admin can update any, VET_STAFF can update their practice's pet owners)"""
    
    pet_owner_repo = PetOwnerRepository(session)
    association_repo = AssociationRepository(session)
    
    # Check if pet owner exists
    pet_owner = await pet_owner_repo.get_by_id(pet_owner_id)
    if not pet_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet owner with ID {pet_owner_id} not found"
        )
    
    # Check access permissions
    if current_user.role in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]:
        # Admin can update any pet owner
        pass
    elif current_user.role == UserRole.VET_STAFF:
        # VET_STAFF can only update pet owners associated with their practice
        if not current_user.practice_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="VET_STAFF user must have a practice_id to update pet owners"
            )
        
        # Check if this pet owner is associated with the user's practice
        accessible_ids = await get_accessible_pet_owner_ids(current_user, association_repo)
        if accessible_ids is not None and pet_owner_id not in accessible_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update pet owners associated with your practice"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Vet Staff access required to update pet owners"
        )
    
    # Check email uniqueness if being updated
    if pet_owner_update.email and pet_owner_update.email != pet_owner.email:
        if await pet_owner_repo.email_exists(pet_owner_update.email, exclude_id=pet_owner_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Check phone uniqueness if being updated
    if pet_owner_update.phone and pet_owner_update.phone != pet_owner.phone:
        if await pet_owner_repo.phone_exists(pet_owner_update.phone, exclude_id=pet_owner_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists"
            )
    
    # Update pet owner
    update_data = pet_owner_update.dict(exclude_unset=True)
    if 'user_id' in update_data:
        if update_data['user_id']:
            update_data['user_id'] = UUID(update_data['user_id'])
        else:
            update_data['user_id'] = None
    
    updated_pet_owner = await pet_owner_repo.update_by_id(pet_owner_id, update_data)
    
    return PetOwnerResponse(
        uuid=str(updated_pet_owner.id),
        user_id=str(updated_pet_owner.user_id) if updated_pet_owner.user_id else None,
        full_name=updated_pet_owner.full_name,
        email=updated_pet_owner.email,
        phone=updated_pet_owner.phone,
        emergency_contact=updated_pet_owner.emergency_contact,
        secondary_phone=updated_pet_owner.secondary_phone,
        address=updated_pet_owner.address,
        preferred_communication=updated_pet_owner.preferred_communication,
        notifications_enabled=updated_pet_owner.notifications_enabled,
        created_at=updated_pet_owner.created_at.isoformat(),
        updated_at=updated_pet_owner.updated_at.isoformat()
    )


@router.delete("/{pet_owner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pet_owner(
    pet_owner_id: UUID = Path(..., description="Pet Owner ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin())
) -> None:
    """Delete a pet owner (admin only)"""
    
    pet_owner_repo = PetOwnerRepository(session)
    
    deleted = await pet_owner_repo.delete_by_id(pet_owner_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pet owner with ID {pet_owner_id} not found"
        )
