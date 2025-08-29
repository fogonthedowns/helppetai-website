"""
Pet Owner Practice Association repository for HelpPet MVP
"""

from typing import List, Optional
from beanie import PydanticObjectId

from .base_repository import BaseRepository
from ..models.pet_owner_practice_association import (
    PetOwnerPracticeAssociation, 
    AssociationStatus
)


class PetOwnerPracticeAssociationRepository(BaseRepository[PetOwnerPracticeAssociation]):
    """Repository for PetOwnerPracticeAssociation document operations"""

    def __init__(self):
        super().__init__(PetOwnerPracticeAssociation)

    async def get_by_uuid(self, uuid: str) -> Optional[PetOwnerPracticeAssociation]:
        """Get association by UUID"""
        return await PetOwnerPracticeAssociation.find_one({"uuid": uuid})

    async def get_by_pet_owner_uuid(self, pet_owner_uuid: str) -> List[PetOwnerPracticeAssociation]:
        """Get all associations for a pet owner"""
        return await PetOwnerPracticeAssociation.find({"pet_owner_uuid": pet_owner_uuid}).to_list()

    async def get_by_practice_uuid(self, practice_uuid: str) -> List[PetOwnerPracticeAssociation]:
        """Get all associations for a practice"""
        return await PetOwnerPracticeAssociation.find({"practice_uuid": practice_uuid}).to_list()

    async def get_by_practice_uuid_and_status(
        self, 
        practice_uuid: str, 
        status: AssociationStatus
    ) -> List[PetOwnerPracticeAssociation]:
        """Get associations for a practice with specific status"""
        return await PetOwnerPracticeAssociation.find({
            "practice_uuid": practice_uuid,
            "status": status
        }).to_list()

    async def get_pet_owners_for_practice(
        self, 
        practice_uuid: str, 
        status: AssociationStatus = AssociationStatus.APPROVED
    ) -> List[str]:
        """Get list of pet owner UUIDs associated with a practice"""
        associations = await self.get_by_practice_uuid_and_status(practice_uuid, status)
        return [assoc.pet_owner_uuid for assoc in associations]

    async def get_practices_for_pet_owner(
        self, 
        pet_owner_uuid: str,
        status: AssociationStatus = AssociationStatus.APPROVED
    ) -> List[str]:
        """Get list of practice UUIDs associated with a pet owner"""
        associations = await PetOwnerPracticeAssociation.find({
            "pet_owner_uuid": pet_owner_uuid,
            "status": status
        }).to_list()
        return [assoc.practice_uuid for assoc in associations]

    async def check_association_exists(
        self, 
        pet_owner_uuid: str, 
        practice_uuid: str
    ) -> Optional[PetOwnerPracticeAssociation]:
        """Check if association already exists between pet owner and practice"""
        return await PetOwnerPracticeAssociation.find_one({
            "pet_owner_uuid": pet_owner_uuid,
            "practice_uuid": practice_uuid
        })

    async def get_pending_requests_for_practice(self, practice_uuid: str) -> List[PetOwnerPracticeAssociation]:
        """Get pending association requests for a practice"""
        return await self.get_by_practice_uuid_and_status(practice_uuid, AssociationStatus.PENDING)

    async def get_active_associations_for_practice(self, practice_uuid: str) -> List[PetOwnerPracticeAssociation]:
        """Get approved associations for a practice"""
        return await self.get_by_practice_uuid_and_status(practice_uuid, AssociationStatus.APPROVED)

    async def approve_association(
        self, 
        uuid: str, 
        approved_by_user_id: str
    ) -> Optional[PetOwnerPracticeAssociation]:
        """Approve an association request"""
        from datetime import datetime
        
        association = await self.get_by_uuid(uuid)
        if not association:
            return None

        association.status = AssociationStatus.APPROVED
        association.approved_by_user_id = PydanticObjectId(approved_by_user_id)
        association.approved_at = datetime.utcnow()
        association.updated_at = datetime.utcnow()

        await association.save()
        return association

    async def reject_association(
        self, 
        uuid: str, 
        rejected_by_user_id: str,
        notes: Optional[str] = None
    ) -> Optional[PetOwnerPracticeAssociation]:
        """Reject an association request"""
        from datetime import datetime
        
        association = await self.get_by_uuid(uuid)
        if not association:
            return None

        association.status = AssociationStatus.REJECTED
        association.approved_by_user_id = PydanticObjectId(rejected_by_user_id)  # Track who rejected
        association.updated_at = datetime.utcnow()
        
        if notes:
            association.notes = notes

        await association.save()
        return association

    async def update_by_uuid(self, uuid: str, update_data: dict) -> Optional[PetOwnerPracticeAssociation]:
        """Update association by UUID"""
        from datetime import datetime
        
        association = await self.get_by_uuid(uuid)
        if not association:
            return None

        for key, value in update_data.items():
            if hasattr(association, key):
                setattr(association, key, value)

        association.updated_at = datetime.utcnow()
        await association.save()
        return association

    async def delete_by_uuid(self, uuid: str) -> bool:
        """Delete association by UUID"""
        association = await self.get_by_uuid(uuid)
        if not association:
            return False

        await association.delete()
        return True

    async def get_user_accessible_pet_owner_uuids(self, user_practice_uuid: str) -> List[str]:
        """
        Get pet owner UUIDs that a user (vet) can access based on their practice
        Used for permission filtering
        """
        return await self.get_pet_owners_for_practice(user_practice_uuid, AssociationStatus.APPROVED)
