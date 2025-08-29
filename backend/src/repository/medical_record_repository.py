"""
Medical Record repository for HelpPet MVP - Versioned medical history management
"""

from typing import List, Optional, Dict, Any
from beanie import PydanticObjectId
from datetime import datetime

from .base_repository import BaseRepository
from ..models.medical_record import MedicalRecord


class MedicalRecordRepository(BaseRepository[MedicalRecord]):
    """Repository for MedicalRecord document operations with versioning support"""
    
    def __init__(self):
        super().__init__(MedicalRecord)
    
    async def create_new_version(
        self,
        pet_id: str | PydanticObjectId,
        content: Dict[str, Any],
        updated_by: str | PydanticObjectId,
        change_summary: Optional[str] = None,
        change_type: str = "update",
        source_visit_id: Optional[str | PydanticObjectId] = None,
        source_practice_id: Optional[str | PydanticObjectId] = None
    ) -> MedicalRecord:
        """
        Create a new version of medical records for a pet
        
        Args:
            pet_id: Pet ID
            content: Medical record content
            updated_by: User ID who made the update
            change_summary: Summary of changes
            change_type: Type of change (create, update, emergency, routine)
            source_visit_id: Optional visit ID that generated this record
            source_practice_id: Optional practice ID where update was made
            
        Returns:
            Created medical record
        """
        # Convert string IDs to ObjectIds
        if isinstance(pet_id, str):
            pet_id = PydanticObjectId(pet_id)
        if isinstance(updated_by, str):
            updated_by = PydanticObjectId(updated_by)
        if isinstance(source_visit_id, str):
            source_visit_id = PydanticObjectId(source_visit_id)
        if isinstance(source_practice_id, str):
            source_practice_id = PydanticObjectId(source_practice_id)
        
        # Get the latest version number for this pet
        latest_record = await MedicalRecord.get_latest_version(pet_id)
        next_version = (latest_record.version + 1) if latest_record else 1
        
        # Create new medical record version
        medical_record = MedicalRecord(
            pet_id=pet_id,
            version=next_version,
            content=content,
            change_summary=change_summary,
            change_type=change_type,
            updated_by=updated_by,
            source_visit_id=source_visit_id,
            source_practice_id=source_practice_id
        )
        
        return await self.create(medical_record)
    
    async def get_latest_version(self, pet_id: str | PydanticObjectId) -> Optional[MedicalRecord]:
        """
        Get the latest version of medical records for a pet
        
        Args:
            pet_id: Pet ID
            
        Returns:
            Latest medical record or None
        """
        if isinstance(pet_id, str):
            pet_id = PydanticObjectId(pet_id)
        
        return await MedicalRecord.get_latest_version(pet_id)
    
    async def get_version_history(
        self,
        pet_id: str | PydanticObjectId,
        limit: int = 50,
        skip: int = 0
    ) -> List[MedicalRecord]:
        """
        Get version history for a pet's medical records
        
        Args:
            pet_id: Pet ID
            limit: Maximum number of versions to return
            skip: Number of versions to skip
            
        Returns:
            List of medical record versions (newest first)
        """
        if isinstance(pet_id, str):
            pet_id = PydanticObjectId(pet_id)
        
        return await MedicalRecord.find(
            {"pet_id": pet_id}
        ).sort([("version", -1)]).skip(skip).limit(limit).to_list()
    
    async def get_specific_version(
        self,
        pet_id: str | PydanticObjectId,
        version: int
    ) -> Optional[MedicalRecord]:
        """
        Get a specific version of medical records for a pet
        
        Args:
            pet_id: Pet ID
            version: Version number
            
        Returns:
            Medical record for specified version or None
        """
        if isinstance(pet_id, str):
            pet_id = PydanticObjectId(pet_id)
        
        return await MedicalRecord.find_one({
            "pet_id": pet_id,
            "version": version
        })
    
    async def get_records_by_practice(
        self,
        practice_id: str | PydanticObjectId,
        limit: int = 100,
        skip: int = 0
    ) -> List[MedicalRecord]:
        """
        Get medical records updated by a specific practice
        
        Args:
            practice_id: Practice ID
            limit: Maximum number of records to return
            skip: Number of records to skip
            
        Returns:
            List of medical records from the practice
        """
        if isinstance(practice_id, str):
            practice_id = PydanticObjectId(practice_id)
        
        return await MedicalRecord.find(
            {"source_practice_id": practice_id}
        ).sort([("updated_at", -1)]).skip(skip).limit(limit).to_list()
    
    async def get_records_by_user(
        self,
        user_id: str | PydanticObjectId,
        limit: int = 100,
        skip: int = 0
    ) -> List[MedicalRecord]:
        """
        Get medical records updated by a specific user
        
        Args:
            user_id: User ID
            limit: Maximum number of records to return
            skip: Number of records to skip
            
        Returns:
            List of medical records updated by the user
        """
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        return await MedicalRecord.find(
            {"updated_by": user_id}
        ).sort([("updated_at", -1)]).skip(skip).limit(limit).to_list()
    
    async def search_records_by_content(
        self,
        search_term: str,
        pet_id: Optional[str | PydanticObjectId] = None,
        limit: int = 50
    ) -> List[MedicalRecord]:
        """
        Search medical records by content (text search)
        
        Args:
            search_term: Term to search for in content
            pet_id: Optional pet ID filter
            limit: Maximum number of records to return
            
        Returns:
            List of matching medical records
        """
        # Build text search query
        filters = {
            "$or": [
                {"content": {"$regex": search_term, "$options": "i"}},
                {"change_summary": {"$regex": search_term, "$options": "i"}}
            ]
        }
        
        if pet_id:
            if isinstance(pet_id, str):
                pet_id = PydanticObjectId(pet_id)
            filters["pet_id"] = pet_id
        
        return await MedicalRecord.find(filters).limit(limit).to_list()
    
    async def get_recent_updates(
        self,
        days: int = 7,
        practice_id: Optional[str | PydanticObjectId] = None,
        limit: int = 100
    ) -> List[MedicalRecord]:
        """
        Get recently updated medical records
        
        Args:
            days: Number of days to look back
            practice_id: Optional practice filter
            limit: Maximum number of records to return
            
        Returns:
            List of recently updated medical records
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        filters = {"updated_at": {"$gte": cutoff_date}}
        
        if practice_id:
            if isinstance(practice_id, str):
                practice_id = PydanticObjectId(practice_id)
            filters["source_practice_id"] = practice_id
        
        return await MedicalRecord.find(filters).sort([
            ("updated_at", -1)
        ]).limit(limit).to_list()
    
    async def get_emergency_records(
        self,
        pet_id: Optional[str | PydanticObjectId] = None,
        limit: int = 50
    ) -> List[MedicalRecord]:
        """
        Get emergency medical records
        
        Args:
            pet_id: Optional pet ID filter
            limit: Maximum number of records to return
            
        Returns:
            List of emergency medical records
        """
        filters = {"change_type": "emergency"}
        
        if pet_id:
            if isinstance(pet_id, str):
                pet_id = PydanticObjectId(pet_id)
            filters["pet_id"] = pet_id
        
        return await MedicalRecord.find(filters).sort([
            ("updated_at", -1)
        ]).limit(limit).to_list()
    
    async def get_version_count(self, pet_id: str | PydanticObjectId) -> int:
        """
        Get the number of medical record versions for a pet
        
        Args:
            pet_id: Pet ID
            
        Returns:
            Number of medical record versions
        """
        if isinstance(pet_id, str):
            pet_id = PydanticObjectId(pet_id)
        
        return await self.count(pet_id=pet_id)
