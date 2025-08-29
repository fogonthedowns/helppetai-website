"""
Practice repository for PostgreSQL - HelpPet MVP
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

try:
    from .base_repository import BaseRepository
    from ..models_pg.practice import VeterinaryPractice
except ImportError:
    from base_repository import BaseRepository
    from models_pg.practice import VeterinaryPractice


class PracticeRepository(BaseRepository[VeterinaryPractice]):
    """Repository for VeterinaryPractice operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(VeterinaryPractice, session)
    
    async def get_by_name(self, name: str) -> Optional[VeterinaryPractice]:
        """Get practice by name"""
        result = await self.session.execute(
            select(VeterinaryPractice).where(VeterinaryPractice.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_by_license_number(self, license_number: str) -> Optional[VeterinaryPractice]:
        """Get practice by license number"""
        result = await self.session.execute(
            select(VeterinaryPractice).where(VeterinaryPractice.license_number == license_number)
        )
        return result.scalar_one_or_none()
    
    async def get_active_practices(self) -> List[VeterinaryPractice]:
        """Get all active practices"""
        result = await self.session.execute(
            select(VeterinaryPractice).where(VeterinaryPractice.is_active == True)
        )
        return list(result.scalars().all())
    
    async def get_accepting_new_patients(self) -> List[VeterinaryPractice]:
        """Get practices accepting new patients"""
        result = await self.session.execute(
            select(VeterinaryPractice).where(
                VeterinaryPractice.is_active == True,
                VeterinaryPractice.accepts_new_patients == True
            )
        )
        return list(result.scalars().all())
    
    async def search_by_location(self, city: str = None, state: str = None, zip_code: str = None) -> List[VeterinaryPractice]:
        """Search practices by location"""
        query = select(VeterinaryPractice).where(VeterinaryPractice.is_active == True)
        
        if city:
            query = query.where(VeterinaryPractice.city.ilike(f"%{city}%"))
        if state:
            query = query.where(VeterinaryPractice.state.ilike(f"%{state}%"))
        if zip_code:
            query = query.where(VeterinaryPractice.zip_code == zip_code)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search_by_name(self, search_term: str) -> List[VeterinaryPractice]:
        """Search practices by name"""
        result = await self.session.execute(
            select(VeterinaryPractice).where(
                VeterinaryPractice.is_active == True,
                VeterinaryPractice.name.ilike(f"%{search_term}%")
            )
        )
        return list(result.scalars().all())
    
    async def license_number_exists(self, license_number: str, exclude_id: UUID = None) -> bool:
        """Check if license number already exists"""
        query = select(VeterinaryPractice.id).where(VeterinaryPractice.license_number == license_number)
        
        if exclude_id:
            query = query.where(VeterinaryPractice.id != exclude_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def deactivate_practice(self, practice_id: UUID) -> bool:
        """Deactivate a practice"""
        return await self.update_by_id(practice_id, {"is_active": False}) is not None
    
    async def activate_practice(self, practice_id: UUID) -> bool:
        """Activate a practice"""
        return await self.update_by_id(practice_id, {"is_active": True}) is not None
