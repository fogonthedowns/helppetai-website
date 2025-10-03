"""
Medical Record management routes for PostgreSQL - HelpPet MVP
"""

import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database_pg import get_db_session
from ..models_pg.user import User
from ..models_pg.medical_record import MedicalRecord
from ..models_pg.pet import Pet
from ..schemas.medical_record_schemas import (
    MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordResponse, 
    MedicalRecordWithRelationsResponse, MedicalRecordListResponse,
    MedicalRecordSearchRequest, MedicalRecordTimelineResponse
)
from ..repositories_pg.medical_record_repository import MedicalRecordRepository
from ..repositories_pg.pet_repository import PetRepository
from ..repositories_pg.association_repository import AssociationRepository
from ..models_pg.pet_owner_practice_association import AssociationStatus
from ..auth.jwt_auth_pg import get_current_user

router = APIRouter(prefix="/api/v1/medical-records", tags=["medical-records"])


async def get_medical_record_repository(session: AsyncSession = Depends(get_db_session)) -> MedicalRecordRepository:
    """Dependency to get medical record repository"""
    return MedicalRecordRepository(session)


async def get_pet_repository(session: AsyncSession = Depends(get_db_session)) -> PetRepository:
    """Dependency to get pet repository"""
    return PetRepository(session)


async def get_association_repository(session: AsyncSession = Depends(get_db_session)) -> AssociationRepository:
    """Dependency to get association repository"""
    return AssociationRepository(session)


async def check_pet_access_for_medical_records(
    pet_id: uuid.UUID,
    current_user: User,
    pet_repo: PetRepository,
    association_repo: AssociationRepository
) -> Pet:
    """Check if user has access to view/manage medical records for a specific pet"""
    pet = await pet_repo.get_with_owner(pet_id)
    if not pet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pet not found"
        )
    
    # Admin can access all pets
    if current_user.role in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"]:
        return pet
    
    # VET_STAFF can access pets from their practice
    if current_user.role in ["VET_STAFF", "VET", "PRACTICE_ADMIN"] and current_user.practice_id:
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
        detail="Access denied to this pet's medical records"
    )


@router.get("/pet/{pet_uuid}", response_model=MedicalRecordListResponse)
async def list_medical_records_for_pet(
    pet_uuid: uuid.UUID,
    include_historical: bool = Query(True, description="Include historical versions"),
    latest_only: bool = Query(False, description="Return only the latest medical record"),
    current_user: User = Depends(get_current_user),
    medical_record_repo: MedicalRecordRepository = Depends(get_medical_record_repository),
    pet_repo: PetRepository = Depends(get_pet_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    List medical records for a pet (Admin | Pet Owner | Associated Vet)
    
    Query Parameters:
    - include_historical: Include historical versions (default: True)
    - latest_only: Return only the latest medical record for optimization (default: False)
    """
    # Check access to pet
    await check_pet_access_for_medical_records(
        pet_uuid, current_user, pet_repo, association_repo
    )
    
    # Get medical records
    records = await medical_record_repo.get_by_pet_id(pet_uuid, include_historical, latest_only)
    current_records = [r for r in records if r.is_current]
    historical_records = [r for r in records if not r.is_current]
    
    return MedicalRecordListResponse(
        records=[MedicalRecordResponse.model_validate(record) for record in records],
        total=len(records),
        current_records_count=len(current_records),
        historical_records_count=len(historical_records)
    )


@router.get("/{uuid}", response_model=MedicalRecordWithRelationsResponse)
async def get_medical_record(
    uuid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    medical_record_repo: MedicalRecordRepository = Depends(get_medical_record_repository),
    pet_repo: PetRepository = Depends(get_pet_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    View single medical record (Admin | Pet Owner | Associated Vet)
    """
    record = await medical_record_repo.get_with_relationships(uuid)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )
    
    # Check access to pet
    await check_pet_access_for_medical_records(
        record.pet_id, current_user, pet_repo, association_repo
    )
    
    return MedicalRecordWithRelationsResponse.model_validate(record)


@router.post("/", response_model=MedicalRecordResponse)
async def create_medical_record(
    record_data: MedicalRecordCreate,
    current_user: User = Depends(get_current_user),
    medical_record_repo: MedicalRecordRepository = Depends(get_medical_record_repository),
    pet_repo: PetRepository = Depends(get_pet_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    Create medical record (Vet or Admin only)
    """
    # Only VET_STAFF and ADMIN can create medical records
    if current_user.role not in ["VET_STAFF", "VET", "PRACTICE_ADMIN", "SYSTEM_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only veterinarians and administrators can create medical records"
        )
    
    # Check access to pet
    await check_pet_access_for_medical_records(
        record_data.pet_id, current_user, pet_repo, association_repo
    )
    
    # Create the medical record
    record_dict = record_data.model_dump()
    record_dict['created_by_user_id'] = current_user.id
    
    record = MedicalRecord(**record_dict)
    created_record = await medical_record_repo.create(record)
    
    return MedicalRecordResponse.model_validate(created_record)


@router.put("/{uuid}", response_model=MedicalRecordResponse)
async def update_medical_record(
    uuid: uuid.UUID,
    record_data: MedicalRecordUpdate,
    current_user: User = Depends(get_current_user),
    medical_record_repo: MedicalRecordRepository = Depends(get_medical_record_repository),
    pet_repo: PetRepository = Depends(get_pet_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    Update medical record (Admin | Creating Vet only) - Creates new version
    """
    existing_record = await medical_record_repo.get_by_id(uuid)
    if not existing_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )
    
    # Check access to pet
    await check_pet_access_for_medical_records(
        existing_record.pet_id, current_user, pet_repo, association_repo
    )
    
    # Only ADMIN or the creating veterinarian can update
    if current_user.role not in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"] and existing_record.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and the creating veterinarian can update medical records"
        )
    
    # Create new version with updates
    update_data = record_data.model_dump(exclude_unset=True)
    new_record = await medical_record_repo.create_new_version(
        existing_record, update_data, current_user.id
    )
    
    return MedicalRecordResponse.model_validate(new_record)


@router.delete("/{uuid}")
async def delete_medical_record(
    uuid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    medical_record_repo: MedicalRecordRepository = Depends(get_medical_record_repository),
    pet_repo: PetRepository = Depends(get_pet_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    Delete medical record (Admin only)
    """
    if current_user.role not in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete medical records"
        )
    
    record = await medical_record_repo.get_by_id(uuid)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )
    
    # Check access to pet
    await check_pet_access_for_medical_records(
        record.pet_id, current_user, pet_repo, association_repo
    )
    
    # Delete the record
    success = await medical_record_repo.delete_by_id(uuid)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical record not found"
        )
    
    return {"message": "Medical record deleted successfully"}


@router.get("/pet/{pet_uuid}/timeline", response_model=MedicalRecordTimelineResponse)
async def get_medical_record_timeline(
    pet_uuid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    medical_record_repo: MedicalRecordRepository = Depends(get_medical_record_repository),
    pet_repo: PetRepository = Depends(get_pet_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    Get medical record timeline for a pet (Admin | Pet Owner | Associated Vet)
    """
    # Check access to pet
    pet = await check_pet_access_for_medical_records(
        pet_uuid, current_user, pet_repo, association_repo
    )
    
    # Get current records only for timeline
    records = await medical_record_repo.get_current_records_by_pet_id(pet_uuid)
    
    # Get follow-up records
    follow_up_records = [r for r in records if r.follow_up_required and r.is_follow_up_due]
    
    # Get latest weight
    latest_weight_record = await medical_record_repo.get_latest_weight_record(pet_uuid)
    recent_weight = latest_weight_record.weight if latest_weight_record else None
    
    return MedicalRecordTimelineResponse(
        pet_id=pet_uuid,
        pet_name=pet.name,
        records_by_date=[MedicalRecordResponse.model_validate(r) for r in records],
        follow_up_due=[MedicalRecordResponse.model_validate(r) for r in follow_up_records],
        recent_weight=recent_weight,
        weight_trend=None  # Could implement weight trend analysis
    )


@router.get("/follow-ups/due")
async def get_follow_ups_due(
    current_user: User = Depends(get_current_user),
    medical_record_repo: MedicalRecordRepository = Depends(get_medical_record_repository)
):
    """
    Get all follow-ups due (Vet Staff and Admin only)
    """
    if current_user.role not in ["VET_STAFF", "VET", "PRACTICE_ADMIN", "SYSTEM_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only veterinarians and administrators can view follow-ups"
        )
    
    records = await medical_record_repo.get_records_requiring_follow_up()
    
    # For VET_STAFF, filter to only their practice's pets
    if current_user.role in ["VET_STAFF", "VET", "PRACTICE_ADMIN"] and current_user.practice_id:
        # This would require additional filtering logic based on practice associations
        pass
    
    return {
        "follow_ups_due": [MedicalRecordResponse.model_validate(r) for r in records],
        "total": len(records)
    }


@router.get("/pet/{pet_uuid}/history", response_model=MedicalRecordListResponse)
async def get_medical_record_history(
    pet_uuid: uuid.UUID,
    current_user: User = Depends(get_current_user),
    medical_record_repo: MedicalRecordRepository = Depends(get_medical_record_repository),
    pet_repo: PetRepository = Depends(get_pet_repository),
    association_repo: AssociationRepository = Depends(get_association_repository)
):
    """
    Get complete medical record history for a pet (Admin | Pet Owner | Associated Vet)
    """
    # Check access to pet
    await check_pet_access_for_medical_records(
        pet_uuid, current_user, pet_repo, association_repo
    )
    
    # Get all versions
    records = await medical_record_repo.get_record_history(pet_uuid)
    current_records = [r for r in records if r.is_current]
    historical_records = [r for r in records if not r.is_current]
    
    return MedicalRecordListResponse(
        records=[MedicalRecordResponse.model_validate(record) for record in records],
        total=len(records),
        current_records_count=len(current_records),
        historical_records_count=len(historical_records)
    )
