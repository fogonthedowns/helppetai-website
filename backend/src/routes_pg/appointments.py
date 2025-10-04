"""
Appointments REST API Routes
Based on spec in docs/0010_appointments.md
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field

from ..auth.jwt_auth_pg import get_current_user
from ..models_pg.user import User
from ..models_pg.appointment import Appointment, AppointmentPet, AppointmentType, AppointmentStatus
from ..models_pg.pet import Pet
from ..models_pg.practice import VeterinaryPractice
from ..models_pg.pet_owner import PetOwner
from ..database_pg import get_db_session


router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])


# Pydantic models for appointments
class AppointmentCreate(BaseModel):
    practice_id: str
    pet_owner_id: str
    assigned_vet_user_id: Optional[str] = None
    appointment_date: datetime
    duration_minutes: int = 30
    appointment_type: AppointmentType = AppointmentType.CHECKUP
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    notes: Optional[str] = None
    pet_ids: List[str] = Field(..., min_items=1)  # At least one pet required


class AppointmentUpdate(BaseModel):
    assigned_vet_user_id: Optional[str] = None
    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    appointment_type: Optional[AppointmentType] = None
    status: Optional[AppointmentStatus] = None
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    notes: Optional[str] = None
    pet_ids: Optional[List[str]] = None


class PetSummary(BaseModel):
    id: str
    name: str
    species: str
    breed: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: str
    practice_id: str
    pet_owner_id: str
    assigned_vet_user_id: Optional[str] = None
    created_by_user_id: str
    appointment_date: datetime
    duration_minutes: int
    appointment_type: AppointmentType
    status: AppointmentStatus
    title: str
    description: Optional[str] = None
    notes: Optional[str] = None
    pets: List[PetSummary]
    created_at: datetime
    updated_at: datetime


# Helper functions
async def check_practice_access(practice_id: str, user: User, db: AsyncSession) -> VeterinaryPractice:
    """Check if user has access to the practice"""
    try:
        practice_uuid = uuid.UUID(practice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid practice ID format")
    
    result = await db.execute(select(VeterinaryPractice).where(VeterinaryPractice.id == practice_uuid))
    practice = result.scalar_one_or_none()
    
    if not practice:
        raise HTTPException(status_code=404, detail="Practice not found")
    
    # Admin can access all practices
    if user.role in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"]:
        return practice
    
    # Vet staff can access their practice
    if user.role in ["VET_STAFF", "VET", "PRACTICE_ADMIN"] and hasattr(user, 'practice_id') and user.practice_id == practice_uuid:
        return practice
    
    raise HTTPException(status_code=403, detail="Access denied to this practice")


async def check_pet_owner_access(pet_owner_id: str, user: User, db: AsyncSession) -> PetOwner:
    """Check if user has access to the pet owner"""
    try:
        owner_uuid = uuid.UUID(pet_owner_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pet owner ID format")
    
    result = await db.execute(select(PetOwner).where(PetOwner.id == owner_uuid))
    pet_owner = result.scalar_one_or_none()
    
    if not pet_owner:
        raise HTTPException(status_code=404, detail="Pet owner not found")
    
    # Admin can access all pet owners
    if user.role in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"]:
        return pet_owner
    
    # Pet owner can access their own data
    if user.role == "PET_OWNER" and hasattr(user, 'pet_owner_id') and user.pet_owner_id == owner_uuid:
        return pet_owner
    
    # Vet staff can access pet owners associated with their practice
    if user.role in ["VET_STAFF", "VET", "PRACTICE_ADMIN"]:
        # TODO: Check if pet owner is associated with user's practice
        return pet_owner
    
    raise HTTPException(status_code=403, detail="Access denied to this pet owner")


def appointment_to_response(appointment: Appointment) -> AppointmentResponse:
    """Convert Appointment model to AppointmentResponse"""
    pets = [
        PetSummary(
            id=str(ap.pet.id),
            name=ap.pet.name,
            species=ap.pet.species,
            breed=ap.pet.breed
        )
        for ap in appointment.appointment_pets
    ]
    
    return AppointmentResponse(
        id=str(appointment.id),
        practice_id=str(appointment.practice_id),
        pet_owner_id=str(appointment.pet_owner_id),
        assigned_vet_user_id=str(appointment.assigned_vet_user_id) if appointment.assigned_vet_user_id else None,
        created_by_user_id=str(appointment.created_by_user_id),
        appointment_date=appointment.appointment_date,
        duration_minutes=appointment.duration_minutes,
        appointment_type=AppointmentType(appointment.appointment_type),
        status=AppointmentStatus(appointment.status),
        title=appointment.title,
        description=appointment.description,
        notes=appointment.notes,
        pets=pets,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at
    )


@router.get("/practice/{practice_uuid}")
async def list_practice_appointments(
    practice_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> List[AppointmentResponse]:
    """
    List appointments by practice
    Access: Admin | Practice Vets
    """
    practice = await check_practice_access(practice_uuid, current_user, db)
    
    # Get appointments with pets loaded
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.appointment_pets).selectinload(AppointmentPet.pet))
        .where(Appointment.practice_id == practice.id)
        .order_by(Appointment.appointment_date.desc())
    )
    appointments = result.scalars().all()
    
    return [appointment_to_response(appointment) for appointment in appointments]


@router.get("/pet-owner/{owner_uuid}")
async def list_pet_owner_appointments(
    owner_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> List[AppointmentResponse]:
    """
    List appointments by pet owner
    Access: Admin | Pet Owner | Associated Vets
    """
    pet_owner = await check_pet_owner_access(owner_uuid, current_user, db)
    
    # Get appointments with pets loaded
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.appointment_pets).selectinload(AppointmentPet.pet))
        .where(Appointment.pet_owner_id == pet_owner.id)
        .order_by(Appointment.appointment_date.desc())
    )
    appointments = result.scalars().all()
    
    return [appointment_to_response(appointment) for appointment in appointments]


@router.get("/{appointment_uuid}")
async def get_appointment(
    appointment_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> AppointmentResponse:
    """
    View single appointment
    Access: Admin | Pet Owner | Practice Vets
    """
    try:
        appointment_id = uuid.UUID(appointment_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid appointment ID format")
    
    # Get appointment with pets loaded
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.appointment_pets).selectinload(AppointmentPet.pet))
        .where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check access permissions
    if current_user.role in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"]:
        pass  # Admin can access all
    elif current_user.role in ["VET_STAFF", "VET", "PRACTICE_ADMIN"]:
        # Check if user's practice matches appointment practice
        if hasattr(current_user, 'practice_id') and current_user.practice_id != appointment.practice_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "PET_OWNER":
        # Check if user owns this appointment
        if hasattr(current_user, 'pet_owner_id') and current_user.pet_owner_id != appointment.pet_owner_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return appointment_to_response(appointment)


@router.post("")
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> AppointmentResponse:
    """
    Create appointment
    Access: Vet or Admin only
    """
    if current_user.role not in ["VET_STAFF", "VET", "PRACTICE_ADMIN", "SYSTEM_ADMIN"]:
        raise HTTPException(
            status_code=403, 
            detail="Only veterinarians and admins can create appointments"
        )
    
    # Verify practice and pet owner exist and user has access
    practice = await check_practice_access(appointment_data.practice_id, current_user, db)
    pet_owner = await check_pet_owner_access(appointment_data.pet_owner_id, current_user, db)
    
    # Verify pets exist and belong to the pet owner
    pet_uuids = []
    for pet_id in appointment_data.pet_ids:
        try:
            pet_uuid = uuid.UUID(pet_id)
            pet_uuids.append(pet_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid pet ID format: {pet_id}")
    
    result = await db.execute(
        select(Pet).where(
            and_(
                Pet.id.in_(pet_uuids),
                Pet.owner_id == pet_owner.id
            )
        )
    )
    pets = result.scalars().all()
    
    if len(pets) != len(pet_uuids):
        raise HTTPException(status_code=400, detail="One or more pets not found or don't belong to this owner")
    
    # Create appointment
    appointment = Appointment(
        practice_id=practice.id,
        pet_owner_id=pet_owner.id,
        assigned_vet_user_id=uuid.UUID(appointment_data.assigned_vet_user_id) if appointment_data.assigned_vet_user_id else None,
        created_by_user_id=current_user.id,
        appointment_date=appointment_data.appointment_date,
        duration_minutes=appointment_data.duration_minutes,
        appointment_type=appointment_data.appointment_type.value,
        title=appointment_data.title,
        description=appointment_data.description,
        notes=appointment_data.notes
    )
    
    db.add(appointment)
    await db.flush()  # Get the appointment ID
    
    # Create appointment-pet associations
    for pet in pets:
        appointment_pet = AppointmentPet(
            appointment_id=appointment.id,
            pet_id=pet.id
        )
        db.add(appointment_pet)
    
    await db.commit()
    
    # Reload with pets
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.appointment_pets).selectinload(AppointmentPet.pet))
        .where(Appointment.id == appointment.id)
    )
    appointment = result.scalar_one()
    
    # Send appointment confirmation email to pet owner
    if pet_owner.email:
        try:
            import logging
            from ..utils.email_service import send_appointment_confirmation_email
            
            logger = logging.getLogger(__name__)
            
            # Prepare pet data for email
            pets_data = [
                {
                    'name': ap.pet.name,
                    'species': ap.pet.species
                }
                for ap in appointment.appointment_pets
            ]
            
            # Get practice address
            practice_address = practice.full_address or "Address not available"
            practice_phone = practice.phone or "Phone not available"
            
            # Send email (don't block appointment creation if email fails)
            email_sent = send_appointment_confirmation_email(
                recipient_email=pet_owner.email,
                recipient_name=pet_owner.full_name,
                practice_name=practice.name,
                practice_address=practice_address,
                practice_phone=practice_phone,
                appointment_date=appointment.appointment_date,
                appointment_duration_minutes=appointment.duration_minutes,
                appointment_type=appointment.appointment_type,
                appointment_title=appointment.title,
                pets=pets_data,
                appointment_id=str(appointment.id),
                practice_timezone=practice.timezone
            )
            
            if email_sent:
                logger.info(f"Appointment confirmation email sent to {pet_owner.email} for appointment {appointment.id}")
            else:
                logger.warning(f"Failed to send appointment confirmation email to {pet_owner.email} for appointment {appointment.id}")
                
        except Exception as e:
            # Log but don't fail appointment creation
            logger.error(f"Error sending appointment confirmation email: {str(e)}")
    
    return appointment_to_response(appointment)


@router.put("/{appointment_uuid}")
async def update_appointment(
    appointment_uuid: str,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> AppointmentResponse:
    """
    Update appointment
    Access: Admin | Practice Vets | Pet Owner for limited fields
    """
    try:
        appointment_id = uuid.UUID(appointment_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid appointment ID format")
    
    # Get appointment
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.appointment_pets).selectinload(AppointmentPet.pet))
        .where(Appointment.id == appointment_id)
    )
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check permissions and determine allowed fields
    allowed_fields = set()
    if current_user.role in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"]:
        allowed_fields = {"assigned_vet_user_id", "appointment_date", "duration_minutes", "appointment_type", "status", "title", "description", "notes", "pet_ids"}
    elif current_user.role in ["VET_STAFF", "VET", "PRACTICE_ADMIN"]:
        if hasattr(current_user, 'practice_id') and current_user.practice_id == appointment.practice_id:
            allowed_fields = {"assigned_vet_user_id", "appointment_date", "duration_minutes", "appointment_type", "status", "title", "description", "notes", "pet_ids"}
        else:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "PET_OWNER":
        if hasattr(current_user, 'pet_owner_id') and current_user.pet_owner_id == appointment.pet_owner_id:
            allowed_fields = {"notes"}  # Pet owners can only update notes
        else:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Track if date/time changed for email notification
    date_changed = False
    old_appointment_date = appointment.appointment_date
    old_duration = appointment.duration_minutes
    
    # Update allowed fields
    if appointment_data.assigned_vet_user_id is not None and "assigned_vet_user_id" in allowed_fields:
        appointment.assigned_vet_user_id = uuid.UUID(appointment_data.assigned_vet_user_id) if appointment_data.assigned_vet_user_id else None
    if appointment_data.appointment_date is not None and "appointment_date" in allowed_fields:
        if appointment.appointment_date != appointment_data.appointment_date:
            date_changed = True
        appointment.appointment_date = appointment_data.appointment_date
    if appointment_data.duration_minutes is not None and "duration_minutes" in allowed_fields:
        if appointment.duration_minutes != appointment_data.duration_minutes:
            date_changed = True
        appointment.duration_minutes = appointment_data.duration_minutes
    if appointment_data.appointment_type is not None and "appointment_type" in allowed_fields:
        appointment.appointment_type = appointment_data.appointment_type.value
    if appointment_data.status is not None and "status" in allowed_fields:
        appointment.status = appointment_data.status.value
    if appointment_data.title is not None and "title" in allowed_fields:
        appointment.title = appointment_data.title
    if appointment_data.description is not None and "description" in allowed_fields:
        appointment.description = appointment_data.description
    if appointment_data.notes is not None and "notes" in allowed_fields:
        appointment.notes = appointment_data.notes
    
    # Update pets if provided and allowed
    if appointment_data.pet_ids is not None and "pet_ids" in allowed_fields:
        # Remove existing pet associations
        await db.execute(
            select(AppointmentPet).where(AppointmentPet.appointment_id == appointment.id)
        )
        existing_associations = (await db.execute(
            select(AppointmentPet).where(AppointmentPet.appointment_id == appointment.id)
        )).scalars().all()
        
        for assoc in existing_associations:
            await db.delete(assoc)
        
        # Add new pet associations
        pet_uuids = []
        for pet_id in appointment_data.pet_ids:
            try:
                pet_uuid = uuid.UUID(pet_id)
                pet_uuids.append(pet_uuid)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid pet ID format: {pet_id}")
        
        result = await db.execute(
            select(Pet).where(
                and_(
                    Pet.id.in_(pet_uuids),
                    Pet.owner_id == appointment.pet_owner_id
                )
            )
        )
        pets = result.scalars().all()
        
        if len(pets) != len(pet_uuids):
            raise HTTPException(status_code=400, detail="One or more pets not found or don't belong to this owner")
        
        for pet in pets:
            appointment_pet = AppointmentPet(
                appointment_id=appointment.id,
                pet_id=pet.id
            )
            db.add(appointment_pet)
    
    appointment.updated_at = datetime.utcnow()
    await db.commit()
    
    # Reload with pets and related data
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.appointment_pets).selectinload(AppointmentPet.pet))
        .where(Appointment.id == appointment.id)
    )
    appointment = result.scalar_one()
    
    # Send reschedule notification email if date/time changed
    if date_changed:
        try:
            # Get pet owner
            result = await db.execute(
                select(PetOwner).where(PetOwner.id == appointment.pet_owner_id)
            )
            pet_owner = result.scalar_one_or_none()
            
            # Get practice
            result = await db.execute(
                select(VeterinaryPractice).where(VeterinaryPractice.id == appointment.practice_id)
            )
            practice = result.scalar_one_or_none()
            
            if pet_owner and pet_owner.email and practice:
                import logging
                from ..utils.email_service import send_appointment_reschedule_email
                
                logger = logging.getLogger(__name__)
                
                # Prepare pet data for email
                pets_data = [
                    {
                        'name': ap.pet.name,
                        'species': ap.pet.species
                    }
                    for ap in appointment.appointment_pets
                ]
                
                # Get practice details
                practice_address = practice.full_address or "Address not available"
                practice_phone = practice.phone or "Phone not available"
                
                # Send reschedule email (don't block if email fails)
                email_sent = send_appointment_reschedule_email(
                    recipient_email=pet_owner.email,
                    recipient_name=pet_owner.full_name,
                    practice_name=practice.name,
                    practice_address=practice_address,
                    practice_phone=practice_phone,
                    old_appointment_date=old_appointment_date,
                    new_appointment_date=appointment.appointment_date,
                    appointment_duration_minutes=appointment.duration_minutes,
                    appointment_type=appointment.appointment_type,
                    appointment_title=appointment.title,
                    pets=pets_data,
                    appointment_id=str(appointment.id),
                    practice_timezone=practice.timezone
                )
                
                if email_sent:
                    logger.info(f"Appointment reschedule email sent to {pet_owner.email} for appointment {appointment.id}")
                else:
                    logger.warning(f"Failed to send appointment reschedule email to {pet_owner.email} for appointment {appointment.id}")
                    
        except Exception as e:
            # Log but don't fail appointment update
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending appointment reschedule email: {str(e)}")
    
    return appointment_to_response(appointment)


@router.delete("/{appointment_uuid}")
async def cancel_appointment(
    appointment_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Cancel appointment (sets status to cancelled)
    Access: Admin | Practice Vets | Pet Owner
    """
    try:
        appointment_id = uuid.UUID(appointment_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid appointment ID format")
    
    # Get appointment
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appointment = result.scalar_one_or_none()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Check permissions
    if current_user.role in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"]:
        pass  # Admin can cancel all
    elif current_user.role in ["VET_STAFF", "VET", "PRACTICE_ADMIN"]:
        if hasattr(current_user, 'practice_id') and current_user.practice_id != appointment.practice_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == "PET_OWNER":
        if hasattr(current_user, 'pet_owner_id') and current_user.pet_owner_id != appointment.pet_owner_id:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Set status to cancelled instead of deleting
    appointment.status = AppointmentStatus.CANCELLED.value
    appointment.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Appointment cancelled successfully"}
