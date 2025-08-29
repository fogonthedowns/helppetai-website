"""
Pet Owner repository for PostgreSQL - HelpPet MVP
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

try:
    from .base_repository import BaseRepository
    from ..models_pg.pet_owner import PetOwner, PreferredCommunication
except ImportError:
    from base_repository import BaseRepository
    from models_pg.pet_owner import PetOwner, PreferredCommunication


class PetOwnerRepository(BaseRepository[PetOwner]):
    """Repository for PetOwner operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(PetOwner, session)
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[PetOwner]:
        """Get pet owner by user ID (optional reference)"""
        result = await self.session.execute(
            select(PetOwner).where(PetOwner.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[PetOwner]:
        """Get pet owner by email"""
        result = await self.session.execute(
            select(PetOwner).where(PetOwner.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_phone(self, phone: str) -> Optional[PetOwner]:
        """Get pet owner by phone"""
        result = await self.session.execute(
            select(PetOwner).where(PetOwner.phone == phone)
        )
        return result.scalar_one_or_none()
    
    async def search_by_name(self, search_term: str) -> List[PetOwner]:
        """Search pet owners by name"""
        result = await self.session.execute(
            select(PetOwner).where(
                PetOwner.full_name.ilike(f"%{search_term}%")
            )
        )
        return list(result.scalars().all())
    
    async def email_exists(self, email: str, exclude_id: UUID = None) -> bool:
        """Check if email already exists"""
        query = select(PetOwner.id).where(PetOwner.email == email)
        
        if exclude_id:
            query = query.where(PetOwner.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def phone_exists(self, phone: str, exclude_id: UUID = None) -> bool:
        """Check if phone already exists"""
        query = select(PetOwner.id).where(PetOwner.phone == phone)
        
        if exclude_id:
            query = query.where(PetOwner.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def get_by_communication_preference(self, preference: PreferredCommunication) -> List[PetOwner]:
        """Get pet owners by communication preference"""
        result = await self.session.execute(
            select(PetOwner).where(PetOwner.preferred_communication == preference)
        )
        return list(result.scalars().all())
    
    async def email_exists(self, email: str, exclude_id: UUID = None) -> bool:
        """Check if email already exists"""
        query = select(PetOwner.id).where(PetOwner.email == email)
        
        if exclude_id:
            query = query.where(PetOwner.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def phone_exists(self, phone: str, exclude_id: UUID = None) -> bool:
        """Check if phone already exists"""
        query = select(PetOwner.id).where(PetOwner.phone == phone)
        
        if exclude_id:
            query = query.where(PetOwner.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def get_with_notifications_enabled(self) -> List[PetOwner]:
        """Get pet owners with notifications enabled"""
        result = await self.session.execute(
            select(PetOwner).where(PetOwner.notifications_enabled == True)
        )
        return list(result.scalars().all())
    
    async def email_exists(self, email: str, exclude_id: UUID = None) -> bool:
        """Check if email already exists"""
        query = select(PetOwner.id).where(PetOwner.email == email)
        
        if exclude_id:
            query = query.where(PetOwner.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def phone_exists(self, phone: str, exclude_id: UUID = None) -> bool:
        """Check if phone already exists"""
        query = select(PetOwner.id).where(PetOwner.phone == phone)
        
        if exclude_id:
            query = query.where(PetOwner.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def email_exists(self, email: str, exclude_id: UUID = None) -> bool:
        """Check if email already exists"""
        query = select(PetOwner.id).where(PetOwner.email == email)
        
        if exclude_id:
            query = query.where(PetOwner.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def phone_exists(self, phone: str, exclude_id: UUID = None) -> bool:
        """Check if phone already exists"""
        query = select(PetOwner.id).where(PetOwner.phone == phone)
        
        if exclude_id:
            query = query.where(PetOwner.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def get_by_practice_association(self, practice_id: UUID) -> List[PetOwner]:
        """Get pet owners associated with a specific practice"""
        try:
            from ..models_pg.pet_owner_practice_association import PetOwnerPracticeAssociation, AssociationStatus
        except ImportError:
            from models_pg.pet_owner_practice_association import PetOwnerPracticeAssociation, AssociationStatus
        
        result = await self.session.execute(
            select(PetOwner)
            .join(PetOwnerPracticeAssociation)
            .where(
                PetOwnerPracticeAssociation.practice_id == practice_id,
                PetOwnerPracticeAssociation.status == AssociationStatus.APPROVED
            )
        )
        return list(result.scalars().all())
    
    async def email_exists(self, email: str, exclude_id: UUID = None) -> bool:
        """Check if email already exists"""
        query = select(PetOwner.id).where(PetOwner.email == email)
        
        if exclude_id:
            query = query.where(PetOwner.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def phone_exists(self, phone: str, exclude_id: UUID = None) -> bool:
        """Check if phone already exists"""
        query = select(PetOwner.id).where(PetOwner.phone == phone)
        
        if exclude_id:
            query = query.where(PetOwner.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
