"""
Practice and Association repositories for HelpPet MVP
"""

from typing import List, Optional
from beanie import PydanticObjectId

from .base_repository import BaseRepository
from ..models.practice import VeterinaryPractice
from ..models.associations import PetPracticeAssociation


class PracticeRepository(BaseRepository[VeterinaryPractice]):
    """Repository for VeterinaryPractice document operations"""
    
    def __init__(self):
        super().__init__(VeterinaryPractice)
    
    async def get_by_uuid(self, uuid: str) -> Optional[VeterinaryPractice]:
        """
        Get practice by UUID
        
        Args:
            uuid: Practice UUID
            
        Returns:
            Practice if found, None otherwise
        """
        return await VeterinaryPractice.find_one({"uuid": uuid})
    
    async def update_by_uuid(self, uuid: str, update_data: dict) -> Optional[VeterinaryPractice]:
        """
        Update practice by UUID
        
        Args:
            uuid: Practice UUID
            update_data: Data to update
            
        Returns:
            Updated practice if found, None otherwise
        """
        practice = await self.get_by_uuid(uuid)
        if not practice:
            return None
        
        for key, value in update_data.items():
            if hasattr(practice, key):
                setattr(practice, key, value)
        
        await practice.save()
        return practice
    
    async def delete_by_uuid(self, uuid: str) -> bool:
        """
        Delete practice by UUID
        
        Args:
            uuid: Practice UUID
            
        Returns:
            True if deleted, False if not found
        """
        practice = await self.get_by_uuid(uuid)
        if not practice:
            return False
        
        await practice.delete()
        return True

    async def get_by_admin(self, admin_user_id: str | PydanticObjectId) -> Optional[VeterinaryPractice]:
        """
        Get practice by admin user ID
        
        Args:
            admin_user_id: Admin user ID
            
        Returns:
            Practice if found, None otherwise
        """
        if isinstance(admin_user_id, str):
            admin_user_id = PydanticObjectId(admin_user_id)
        
        return await VeterinaryPractice.find_one({"admin_user_id": admin_user_id})
    
    async def search_practices(
        self,
        search_term: str,
        specialty: Optional[str] = None,
        limit: int = 50
    ) -> List[VeterinaryPractice]:
        """
        Search practices by name, address, or specialties
        
        Args:
            search_term: Term to search for
            specialty: Optional specialty filter
            limit: Maximum number of practices to return
            
        Returns:
            List of matching practices
        """
        pattern = {"$regex": search_term, "$options": "i"}
        filters = {
            "$or": [
                {"name": pattern},
                {"address": pattern},
                {"specialties": pattern}
            ],
            "is_active": True
        }
        
        if specialty:
            filters["specialties"] = {"$regex": specialty, "$options": "i"}
        
        return await VeterinaryPractice.find(filters).limit(limit).to_list()
    
    async def get_by_specialty(self, specialty: str, limit: int = 50) -> List[VeterinaryPractice]:
        """
        Get practices by specialty
        
        Args:
            specialty: Specialty to search for
            limit: Maximum number of practices to return
            
        Returns:
            List of practices with the specified specialty
        """
        return await VeterinaryPractice.find({
            "specialties": {"$regex": specialty, "$options": "i"},
            "is_active": True
        }).limit(limit).to_list()


class PetPracticeAssociationRepository(BaseRepository[PetPracticeAssociation]):
    """Repository for PetPracticeAssociation document operations"""
    
    def __init__(self):
        super().__init__(PetPracticeAssociation)
    
    async def get_pet_practices(
        self,
        pet_id: str | PydanticObjectId,
        is_active: bool = True
    ) -> List[PetPracticeAssociation]:
        """
        Get all practices associated with a pet
        
        Args:
            pet_id: Pet ID
            is_active: Whether to include only active associations
            
        Returns:
            List of practice associations for the pet
        """
        if isinstance(pet_id, str):
            pet_id = PydanticObjectId(pet_id)
        
        filters = {"pet_id": pet_id}
        if is_active:
            filters["is_active"] = True
        
        return await PetPracticeAssociation.find(filters).to_list()
    
    async def get_practice_pets(
        self,
        practice_id: str | PydanticObjectId,
        is_active: bool = True,
        limit: int = 100,
        skip: int = 0
    ) -> List[PetPracticeAssociation]:
        """
        Get all pets associated with a practice
        
        Args:
            practice_id: Practice ID
            is_active: Whether to include only active associations
            limit: Maximum number of associations to return
            skip: Number of associations to skip
            
        Returns:
            List of pet associations for the practice
        """
        if isinstance(practice_id, str):
            practice_id = PydanticObjectId(practice_id)
        
        filters = {"practice_id": practice_id}
        if is_active:
            filters["is_active"] = True
        
        return await PetPracticeAssociation.find(filters).skip(skip).limit(limit).to_list()
    
    async def get_association(
        self,
        pet_id: str | PydanticObjectId,
        practice_id: str | PydanticObjectId
    ) -> Optional[PetPracticeAssociation]:
        """
        Get specific association between a pet and practice
        
        Args:
            pet_id: Pet ID
            practice_id: Practice ID
            
        Returns:
            Association if found, None otherwise
        """
        if isinstance(pet_id, str):
            pet_id = PydanticObjectId(pet_id)
        if isinstance(practice_id, str):
            practice_id = PydanticObjectId(practice_id)
        
        return await PetPracticeAssociation.find_one({
            "pet_id": pet_id,
            "practice_id": practice_id
        })
    
    async def create_association(
        self,
        pet_id: str | PydanticObjectId,
        practice_id: str | PydanticObjectId,
        relationship_type: str = "patient",
        is_primary_practice: bool = False,
        notes: Optional[str] = None,
        created_by: Optional[str | PydanticObjectId] = None
    ) -> PetPracticeAssociation:
        """
        Create association between pet and practice
        
        Args:
            pet_id: Pet ID
            practice_id: Practice ID
            relationship_type: Type of relationship (patient, emergency, referral, specialist)
            is_primary_practice: Whether this is the pet's primary practice
            notes: Optional notes about the relationship
            created_by: User who created the association
            
        Returns:
            Created association
        """
        # Convert string IDs to ObjectIds
        if isinstance(pet_id, str):
            pet_id = PydanticObjectId(pet_id)
        if isinstance(practice_id, str):
            practice_id = PydanticObjectId(practice_id)
        if isinstance(created_by, str):
            created_by = PydanticObjectId(created_by)
        
        # Check if association already exists
        existing = await self.get_association(pet_id, practice_id)
        if existing:
            # Reactivate if it was deactivated
            if not existing.is_active:
                existing.is_active = True
                existing.relationship_type = relationship_type
                existing.is_primary_practice = is_primary_practice
                if notes:
                    existing.notes = notes
                await existing.save()
                return existing
            else:
                raise ValueError("Association already exists and is active")
        
        # If setting as primary practice, unset other primary associations for this pet
        if is_primary_practice:
            await self.unset_primary_practice(pet_id)
        
        association = PetPracticeAssociation(
            pet_id=pet_id,
            practice_id=practice_id,
            relationship_type=relationship_type,
            is_primary_practice=is_primary_practice,
            notes=notes,
            created_by=created_by
        )
        
        return await self.create(association)
    
    async def unset_primary_practice(self, pet_id: str | PydanticObjectId) -> None:
        """
        Unset primary practice flag for all associations of a pet
        
        Args:
            pet_id: Pet ID
        """
        if isinstance(pet_id, str):
            pet_id = PydanticObjectId(pet_id)
        
        associations = await PetPracticeAssociation.find({
            "pet_id": pet_id,
            "is_primary_practice": True
        }).to_list()
        
        for association in associations:
            association.is_primary_practice = False
            await association.save()
    
    async def get_primary_practice(
        self,
        pet_id: str | PydanticObjectId
    ) -> Optional[PetPracticeAssociation]:
        """
        Get the primary practice association for a pet
        
        Args:
            pet_id: Pet ID
            
        Returns:
            Primary practice association if found, None otherwise
        """
        if isinstance(pet_id, str):
            pet_id = PydanticObjectId(pet_id)
        
        return await PetPracticeAssociation.find_one({
            "pet_id": pet_id,
            "is_primary_practice": True,
            "is_active": True
        })
    
    async def verify_practice_access(
        self,
        pet_id: str | PydanticObjectId,
        practice_id: str | PydanticObjectId
    ) -> bool:
        """
        Verify that a practice has access to a pet's records
        Core function for implementing access control
        
        Args:
            pet_id: Pet ID
            practice_id: Practice ID
            
        Returns:
            True if practice has access, False otherwise
        """
        association = await self.get_association(pet_id, practice_id)
        return association is not None and association.is_active
    
    async def deactivate_association(
        self,
        pet_id: str | PydanticObjectId,
        practice_id: str | PydanticObjectId
    ) -> bool:
        """
        Deactivate association between pet and practice
        
        Args:
            pet_id: Pet ID
            practice_id: Practice ID
            
        Returns:
            True if deactivated, False if not found
        """
        association = await self.get_association(pet_id, practice_id)
        if not association:
            return False
        
        association.is_active = False
        await association.save()
        return True
