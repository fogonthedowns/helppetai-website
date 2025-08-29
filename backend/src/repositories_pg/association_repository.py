"""
Pet Owner Practice Association repository for PostgreSQL - HelpPet MVP
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

try:
    from .base_repository import BaseRepository
    from ..models_pg.pet_owner_practice_association import PetOwnerPracticeAssociation, AssociationStatus, AssociationRequestType
except ImportError:
    from base_repository import BaseRepository
    from models_pg.pet_owner_practice_association import PetOwnerPracticeAssociation, AssociationStatus, AssociationRequestType


class AssociationRepository(BaseRepository[PetOwnerPracticeAssociation]):
    """Repository for PetOwnerPracticeAssociation operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(PetOwnerPracticeAssociation, session)
    
    async def get_by_pet_owner_id(self, pet_owner_id: UUID) -> List[PetOwnerPracticeAssociation]:
        """Get all associations for a pet owner"""
        result = await self.session.execute(
            select(PetOwnerPracticeAssociation).where(
                PetOwnerPracticeAssociation.pet_owner_id == pet_owner_id
            )
        )
        return list(result.scalars().all())
    
    async def get_by_practice_id(self, practice_id: UUID) -> List[PetOwnerPracticeAssociation]:
        """Get all associations for a practice"""
        result = await self.session.execute(
            select(PetOwnerPracticeAssociation).where(
                PetOwnerPracticeAssociation.practice_id == practice_id
            )
        )
        return list(result.scalars().all())
    
    async def get_by_practice_and_status(self, practice_id: UUID, status: AssociationStatus) -> List[PetOwnerPracticeAssociation]:
        """Get associations for a practice with specific status"""
        result = await self.session.execute(
            select(PetOwnerPracticeAssociation).where(
                PetOwnerPracticeAssociation.practice_id == practice_id,
                PetOwnerPracticeAssociation.status == status
            )
        )
        return list(result.scalars().all())
    
    async def get_pet_owners_for_practice(self, practice_id: UUID, status: AssociationStatus = AssociationStatus.APPROVED) -> List[UUID]:
        """Get list of pet owner IDs associated with a practice"""
        result = await self.session.execute(
            select(PetOwnerPracticeAssociation.pet_owner_id).where(
                PetOwnerPracticeAssociation.practice_id == practice_id,
                PetOwnerPracticeAssociation.status == status
            )
        )
        return [row[0] for row in result.fetchall()]
    
    async def get_practices_for_pet_owner(self, pet_owner_id: UUID, status: AssociationStatus = AssociationStatus.APPROVED) -> List[UUID]:
        """Get list of practice IDs associated with a pet owner"""
        result = await self.session.execute(
            select(PetOwnerPracticeAssociation.practice_id).where(
                PetOwnerPracticeAssociation.pet_owner_id == pet_owner_id,
                PetOwnerPracticeAssociation.status == status
            )
        )
        return [row[0] for row in result.fetchall()]
    
    async def check_association_exists(self, pet_owner_id: UUID, practice_id: UUID) -> Optional[PetOwnerPracticeAssociation]:
        """Check if association already exists between pet owner and practice"""
        result = await self.session.execute(
            select(PetOwnerPracticeAssociation).where(
                PetOwnerPracticeAssociation.pet_owner_id == pet_owner_id,
                PetOwnerPracticeAssociation.practice_id == practice_id
            )
        )
        return result.scalar_one_or_none()
    
    async def get_pending_requests_for_practice(self, practice_id: UUID) -> List[PetOwnerPracticeAssociation]:
        """Get pending association requests for a practice"""
        return await self.get_by_practice_and_status(practice_id, AssociationStatus.PENDING)
    
    async def get_active_associations_for_practice(self, practice_id: UUID) -> List[PetOwnerPracticeAssociation]:
        """Get approved associations for a practice"""
        return await self.get_by_practice_and_status(practice_id, AssociationStatus.APPROVED)
    
    async def approve_association(self, association_id: UUID, approved_by_user_id: UUID) -> Optional[PetOwnerPracticeAssociation]:
        """Approve an association request"""
        association = await self.get_by_id(association_id)
        if not association:
            return None
        
        association.status = AssociationStatus.APPROVED
        association.approved_by_user_id = approved_by_user_id
        association.approved_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(association)
        return association
    
    async def reject_association(self, association_id: UUID, rejected_by_user_id: UUID, notes: Optional[str] = None) -> Optional[PetOwnerPracticeAssociation]:
        """Reject an association request"""
        association = await self.get_by_id(association_id)
        if not association:
            return None
        
        association.status = AssociationStatus.REJECTED
        association.approved_by_user_id = rejected_by_user_id  # Track who rejected
        if notes:
            association.notes = notes
        
        await self.session.commit()
        await self.session.refresh(association)
        return association
    
    async def get_primary_practice_for_pet_owner(self, pet_owner_id: UUID) -> Optional[PetOwnerPracticeAssociation]:
        """Get the primary practice association for a pet owner"""
        result = await self.session.execute(
            select(PetOwnerPracticeAssociation).where(
                PetOwnerPracticeAssociation.pet_owner_id == pet_owner_id,
                PetOwnerPracticeAssociation.status == AssociationStatus.APPROVED,
                PetOwnerPracticeAssociation.primary_contact == True
            )
        )
        return result.scalar_one_or_none()
    
    async def update_last_visit(self, association_id: UUID, visit_date: datetime = None) -> Optional[PetOwnerPracticeAssociation]:
        """Update last visit date for an association"""
        if visit_date is None:
            visit_date = datetime.utcnow()
        
        return await self.update_by_id(association_id, {"last_visit_date": visit_date})
