"""
Pet repository for HelpPet MVP - Pet management operations
"""

from typing import List, Optional
from beanie import PydanticObjectId

from .base_repository import BaseRepository
from ..models.pet import Pet, PetSpecies


class PetRepository(BaseRepository[Pet]):
    """Repository for Pet document operations"""
    
    def __init__(self):
        super().__init__(Pet)
    
    async def get_pets_by_owner(
        self,
        owner_id: str | PydanticObjectId,
        include_deceased: bool = False,
        limit: int = 100
    ) -> List[Pet]:
        """
        Get all pets owned by a specific user
        
        Args:
            owner_id: Owner's user ID
            include_deceased: Whether to include deceased pets
            limit: Maximum number of pets to return
            
        Returns:
            List of pets owned by the user
        """
        if isinstance(owner_id, str):
            owner_id = PydanticObjectId(owner_id)
        
        filters = {"owner_id": owner_id}
        if not include_deceased:
            filters["is_deceased"] = False
        
        return await Pet.find(filters).limit(limit).to_list()
    
    async def get_pets_by_species(
        self,
        species: PetSpecies,
        is_active: bool = True,
        limit: int = 100,
        skip: int = 0
    ) -> List[Pet]:
        """
        Get pets by species
        
        Args:
            species: Pet species to filter by
            is_active: Whether to include only living pets
            limit: Maximum number of pets to return
            skip: Number of pets to skip
            
        Returns:
            List of pets of the specified species
        """
        filters = {"species": species}
        if is_active:
            filters["is_deceased"] = False
        
        return await Pet.find(filters).skip(skip).limit(limit).to_list()
    
    async def get_by_microchip(self, microchip_id: str) -> Optional[Pet]:
        """
        Get pet by microchip ID
        
        Args:
            microchip_id: Microchip ID to search for
            
        Returns:
            Pet if found, None otherwise
        """
        return await Pet.find_one({"microchip_id": microchip_id})
    
    async def search_pets(
        self,
        search_term: str,
        owner_id: Optional[str | PydanticObjectId] = None,
        species: Optional[PetSpecies] = None,
        include_deceased: bool = False,
        limit: int = 50
    ) -> List[Pet]:
        """
        Search pets by name, breed, or other characteristics
        
        Args:
            search_term: Term to search for
            owner_id: Optional owner filter
            species: Optional species filter
            include_deceased: Whether to include deceased pets
            limit: Maximum number of results
            
        Returns:
            List of matching pets
        """
        # Create regex pattern for case-insensitive search
        pattern = {"$regex": search_term, "$options": "i"}
        
        filters = {
            "$or": [
                {"name": pattern},
                {"breed": pattern},
                {"color": pattern},
                {"microchip_id": pattern},
                {"registration_number": pattern}
            ]
        }
        
        if owner_id:
            if isinstance(owner_id, str):
                owner_id = PydanticObjectId(owner_id)
            filters["owner_id"] = owner_id
        
        if species:
            filters["species"] = species
        
        if not include_deceased:
            filters["is_deceased"] = False
        
        return await Pet.find(filters).limit(limit).to_list()
    
    async def get_pets_needing_follow_up(
        self,
        owner_id: Optional[str | PydanticObjectId] = None,
        limit: int = 100
    ) -> List[Pet]:
        """
        Get pets that might need follow-up (based on age, medical conditions, etc.)
        This is a placeholder for future business logic
        
        Args:
            owner_id: Optional owner filter
            limit: Maximum number of pets to return
            
        Returns:
            List of pets that might need attention
        """
        filters = {"is_deceased": False}
        
        if owner_id:
            if isinstance(owner_id, str):
                owner_id = PydanticObjectId(owner_id)
            filters["owner_id"] = owner_id
        
        # Example logic: pets over 7 years old might need senior care
        # In the future, this could be enhanced with medical record analysis
        pets = await Pet.find(filters).limit(limit).to_list()
        
        # Filter for pets that might need attention
        follow_up_pets = []
        for pet in pets:
            # Calculate age from birth_date if available
            age = pet.get_age_from_birth_date() or pet.age
            
            if age and age >= 7:  # Senior pets
                follow_up_pets.append(pet)
            elif pet.current_medications:  # Pets on medication
                follow_up_pets.append(pet)
            elif pet.special_needs:  # Pets with special needs
                follow_up_pets.append(pet)
        
        return follow_up_pets
    
    async def get_pets_by_breed(
        self,
        breed: str,
        species: Optional[PetSpecies] = None,
        limit: int = 100
    ) -> List[Pet]:
        """
        Get pets by breed (case-insensitive)
        
        Args:
            breed: Breed to search for
            species: Optional species filter
            limit: Maximum number of pets to return
            
        Returns:
            List of pets of the specified breed
        """
        filters = {
            "breed": {"$regex": breed, "$options": "i"},
            "is_deceased": False
        }
        
        if species:
            filters["species"] = species
        
        return await Pet.find(filters).limit(limit).to_list()
    
    async def mark_deceased(
        self,
        pet_id: str | PydanticObjectId,
        date_of_death: Optional[str] = None
    ) -> bool:
        """
        Mark a pet as deceased
        
        Args:
            pet_id: Pet ID
            date_of_death: Date of death (ISO string)
            
        Returns:
            True if updated, False if not found
        """
        update_data = {"is_deceased": True}
        if date_of_death:
            from datetime import datetime
            try:
                update_data["date_of_death"] = datetime.fromisoformat(date_of_death).date()
            except ValueError:
                pass  # Invalid date format, skip setting date
        
        update_result = await self.update(pet_id, update_data)
        return update_result is not None
    
    async def get_owner_pet_count(self, owner_id: str | PydanticObjectId) -> int:
        """
        Get the number of pets owned by a specific user
        
        Args:
            owner_id: Owner's user ID
            
        Returns:
            Number of pets owned (excluding deceased)
        """
        if isinstance(owner_id, str):
            owner_id = PydanticObjectId(owner_id)
        
        return await self.count(owner_id=owner_id, is_deceased=False)
