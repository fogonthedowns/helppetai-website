"""
Pet Owner repository for HelpPet MVP
"""

from typing import List, Optional
from beanie import PydanticObjectId

from .base_repository import BaseRepository
from ..models.pet_owner import PetOwner


class PetOwnerRepository(BaseRepository[PetOwner]):
    """Repository for PetOwner document operations"""
    
    def __init__(self):
        super().__init__(PetOwner)
    
    async def get_by_uuid(self, uuid: str) -> Optional[PetOwner]:
        """
        Get pet owner by UUID
        
        Args:
            uuid: Pet Owner UUID
            
        Returns:
            Pet owner if found, None otherwise
        """
        return await PetOwner.find_one({"uuid": uuid})
    
    async def get_by_user_id(self, user_id: str | PydanticObjectId) -> Optional[PetOwner]:
        """
        Get pet owner by user ID (optional reference)
        
        Args:
            user_id: User ID
            
        Returns:
            Pet owner if found, None otherwise
        """
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        return await PetOwner.find_one({"user_id": user_id})
    
    async def get_by_user_id_list(self, user_ids: List[str | PydanticObjectId]) -> List[PetOwner]:
        """
        Get multiple pet owners by user IDs (for future batch operations)
        
        Args:
            user_ids: List of User IDs
            
        Returns:
            List of pet owners
        """
        object_ids = []
        for user_id in user_ids:
            if isinstance(user_id, str):
                object_ids.append(PydanticObjectId(user_id))
            else:
                object_ids.append(user_id)
        
        return await PetOwner.find({"user_id": {"$in": object_ids}}).to_list()
    
    async def update_by_uuid(self, uuid: str, update_data: dict) -> Optional[PetOwner]:
        """
        Update pet owner by UUID
        
        Args:
            uuid: Pet Owner UUID
            update_data: Data to update
            
        Returns:
            Updated pet owner if found, None otherwise
        """
        pet_owner = await self.get_by_uuid(uuid)
        if not pet_owner:
            return None
        
        for key, value in update_data.items():
            if hasattr(pet_owner, key):
                setattr(pet_owner, key, value)
        
        # Update the updated_at timestamp
        from datetime import datetime
        pet_owner.updated_at = datetime.utcnow()
        
        await pet_owner.save()
        return pet_owner
    
    async def delete_by_uuid(self, uuid: str) -> bool:
        """
        Delete pet owner by UUID
        
        Args:
            uuid: Pet Owner UUID
            
        Returns:
            True if deleted, False if not found
        """
        pet_owner = await self.get_by_uuid(uuid)
        if not pet_owner:
            return False
        
        await pet_owner.delete()
        return True
    
    async def search_pet_owners(
        self,
        search_term: str,
        limit: int = 50
    ) -> List[PetOwner]:
        """
        Search pet owners by various fields
        
        Args:
            search_term: Term to search for
            limit: Maximum number of pet owners to return
            
        Returns:
            List of matching pet owners
        """
        pattern = {"$regex": search_term, "$options": "i"}
        filters = {
            "$or": [
                {"emergency_contact": pattern},
                {"secondary_phone": pattern},
                {"address": pattern}
            ]
        }
        
        return await PetOwner.find(filters).limit(limit).to_list()
