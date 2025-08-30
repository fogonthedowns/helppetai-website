"""
Pet Repository for PostgreSQL - HelpPet MVP
"""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from ..models_pg.pet import Pet
from ..models_pg.pet_owner import PetOwner


class PetRepository(BaseRepository[Pet]):
    """Repository for Pet CRUD operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Pet, session)
    
    async def get_by_owner_id(self, owner_id: uuid.UUID, include_inactive: bool = False) -> List[Pet]:
        """Get all pets for a specific owner"""
        query = select(Pet).where(Pet.owner_id == owner_id)
        
        if not include_inactive:
            query = query.where(Pet.is_active == True)
            
        query = query.order_by(Pet.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_microchip_id(self, microchip_id: str) -> Optional[Pet]:
        """Get pet by microchip ID"""
        query = select(Pet).where(Pet.microchip_id == microchip_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_owner(self, pet_id: uuid.UUID) -> Optional[Pet]:
        """Get pet with owner information loaded"""
        query = select(Pet).options(
            selectinload(Pet.owner)
        ).where(Pet.id == pet_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all_with_owners(self, include_inactive: bool = False) -> List[Pet]:
        """Get all pets with owner information (Admin only)"""
        query = select(Pet).options(
            selectinload(Pet.owner)
        )
        
        if not include_inactive:
            query = query.where(Pet.is_active == True)
            
        query = query.order_by(Pet.owner_id, Pet.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search_by_name(self, name_pattern: str, owner_id: Optional[uuid.UUID] = None) -> List[Pet]:
        """Search pets by name pattern"""
        query = select(Pet).where(
            Pet.name.ilike(f"%{name_pattern}%"),
            Pet.is_active == True
        )
        
        if owner_id:
            query = query.where(Pet.owner_id == owner_id)
            
        query = query.order_by(Pet.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_pets_for_practice(self, practice_id: uuid.UUID) -> List[Pet]:
        """Get all pets associated with a veterinary practice"""
        from ..models_pg.pet_owner_practice_association import PetOwnerPracticeAssociation
        
        query = select(Pet).join(
            PetOwner, Pet.owner_id == PetOwner.id
        ).join(
            PetOwnerPracticeAssociation, 
            PetOwner.id == PetOwnerPracticeAssociation.pet_owner_id
        ).where(
            and_(
                PetOwnerPracticeAssociation.practice_id == practice_id,
                PetOwnerPracticeAssociation.status == "approved",
                Pet.is_active == True
            )
        ).options(
            selectinload(Pet.owner)
        ).order_by(Pet.owner_id, Pet.name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def deactivate(self, pet_id: uuid.UUID) -> Optional[Pet]:
        """Soft delete a pet by setting is_active to False"""
        pet = await self.get_by_id(pet_id)
        if pet:
            pet.is_active = False
            await self.session.commit()
            await self.session.refresh(pet)
        return pet
    
    async def reactivate(self, pet_id: uuid.UUID) -> Optional[Pet]:
        """Reactivate a pet by setting is_active to True"""
        pet = await self.get_by_id(pet_id)
        if pet:
            pet.is_active = True
            await self.session.commit()
            await self.session.refresh(pet)
        return pet
