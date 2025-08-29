"""
Visit repository for HelpPet MVP - Veterinary visit management with transcript support
"""

from typing import List, Optional
from beanie import PydanticObjectId
from datetime import datetime, timedelta

from .base_repository import BaseRepository
from ..models.visit import Visit, VisitType, VisitStatus


class VisitRepository(BaseRepository[Visit]):
    """Repository for Visit document operations"""
    
    def __init__(self):
        super().__init__(Visit)
    
    async def get_pet_visits(
        self,
        pet_id: str | PydanticObjectId,
        include_all_practices: bool = True,
        limit: int = 100,
        skip: int = 0
    ) -> List[Visit]:
        """
        Get all visits for a specific pet across all practices
        This enables the core value proposition of shared medical history
        
        Args:
            pet_id: Pet ID
            include_all_practices: Whether to include visits from all practices
            limit: Maximum number of visits to return
            skip: Number of visits to skip
            
        Returns:
            List of visits for the pet (newest first)
        """
        if isinstance(pet_id, str):
            pet_id = PydanticObjectId(pet_id)
        
        filters = {"pet_id": pet_id}
        
        return await Visit.find(filters).sort([
            ("visit_date", -1)
        ]).skip(skip).limit(limit).to_list()
    
    async def get_practice_visits(
        self,
        practice_id: str | PydanticObjectId,
        status: Optional[VisitStatus] = None,
        visit_date_from: Optional[datetime] = None,
        visit_date_to: Optional[datetime] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Visit]:
        """
        Get visits for a specific practice with filtering
        
        Args:
            practice_id: Practice ID
            status: Optional status filter
            visit_date_from: Optional start date filter
            visit_date_to: Optional end date filter
            limit: Maximum number of visits to return
            skip: Number of visits to skip
            
        Returns:
            List of visits for the practice
        """
        if isinstance(practice_id, str):
            practice_id = PydanticObjectId(practice_id)
        
        filters = {"practice_id": practice_id}
        
        if status:
            filters["status"] = status
        
        if visit_date_from or visit_date_to:
            date_filter = {}
            if visit_date_from:
                date_filter["$gte"] = visit_date_from
            if visit_date_to:
                date_filter["$lte"] = visit_date_to
            filters["visit_date"] = date_filter
        
        return await Visit.find(filters).sort([
            ("visit_date", -1)
        ]).skip(skip).limit(limit).to_list()
    
    async def get_vet_visits(
        self,
        vet_user_id: str | PydanticObjectId,
        status: Optional[VisitStatus] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Visit]:
        """
        Get visits for a specific veterinarian
        
        Args:
            vet_user_id: Veterinarian user ID
            status: Optional status filter
            limit: Maximum number of visits to return
            skip: Number of visits to skip
            
        Returns:
            List of visits for the veterinarian
        """
        if isinstance(vet_user_id, str):
            vet_user_id = PydanticObjectId(vet_user_id)
        
        filters = {"vet_user_id": vet_user_id}
        if status:
            filters["status"] = status
        
        return await Visit.find(filters).sort([
            ("visit_date", -1)
        ]).skip(skip).limit(limit).to_list()
    
    async def get_visits_with_transcripts(
        self,
        pet_id: Optional[str | PydanticObjectId] = None,
        practice_id: Optional[str | PydanticObjectId] = None,
        limit: int = 100
    ) -> List[Visit]:
        """
        Get visits that have audio transcripts
        
        Args:
            pet_id: Optional pet ID filter
            practice_id: Optional practice ID filter
            limit: Maximum number of visits to return
            
        Returns:
            List of visits with transcripts
        """
        filters = {"audio_transcript": {"$ne": None, "$ne": ""}}
        
        if pet_id:
            if isinstance(pet_id, str):
                pet_id = PydanticObjectId(pet_id)
            filters["pet_id"] = pet_id
        
        if practice_id:
            if isinstance(practice_id, str):
                practice_id = PydanticObjectId(practice_id)
            filters["practice_id"] = practice_id
        
        return await Visit.find(filters).sort([
            ("visit_date", -1)
        ]).limit(limit).to_list()
    
    async def get_upcoming_visits(
        self,
        practice_id: Optional[str | PydanticObjectId] = None,
        vet_user_id: Optional[str | PydanticObjectId] = None,
        days_ahead: int = 7,
        limit: int = 100
    ) -> List[Visit]:
        """
        Get upcoming scheduled visits
        
        Args:
            practice_id: Optional practice ID filter
            vet_user_id: Optional veterinarian filter
            days_ahead: Number of days ahead to look
            limit: Maximum number of visits to return
            
        Returns:
            List of upcoming visits
        """
        now = datetime.utcnow()
        future_date = now + timedelta(days=days_ahead)
        
        filters = {
            "visit_date": {"$gte": now, "$lte": future_date},
            "status": {"$in": [VisitStatus.SCHEDULED, VisitStatus.IN_PROGRESS]}
        }
        
        if practice_id:
            if isinstance(practice_id, str):
                practice_id = PydanticObjectId(practice_id)
            filters["practice_id"] = practice_id
        
        if vet_user_id:
            if isinstance(vet_user_id, str):
                vet_user_id = PydanticObjectId(vet_user_id)
            filters["vet_user_id"] = vet_user_id
        
        return await Visit.find(filters).sort([
            ("visit_date", 1)
        ]).limit(limit).to_list()
    
    async def get_overdue_visits(
        self,
        practice_id: Optional[str | PydanticObjectId] = None,
        limit: int = 100
    ) -> List[Visit]:
        """
        Get visits that are overdue (scheduled but past their date)
        
        Args:
            practice_id: Optional practice ID filter
            limit: Maximum number of visits to return
            
        Returns:
            List of overdue visits
        """
        now = datetime.utcnow()
        filters = {
            "visit_date": {"$lt": now},
            "status": VisitStatus.SCHEDULED
        }
        
        if practice_id:
            if isinstance(practice_id, str):
                practice_id = PydanticObjectId(practice_id)
            filters["practice_id"] = practice_id
        
        return await Visit.find(filters).sort([
            ("visit_date", 1)
        ]).limit(limit).to_list()
    
    async def get_visits_needing_follow_up(
        self,
        practice_id: Optional[str | PydanticObjectId] = None,
        days_overdue: int = 1,
        limit: int = 100
    ) -> List[Visit]:
        """
        Get visits that need follow-up (follow_up_required=True and past follow_up_date)
        
        Args:
            practice_id: Optional practice ID filter
            days_overdue: Number of days past follow_up_date to consider overdue
            limit: Maximum number of visits to return
            
        Returns:
            List of visits needing follow-up
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_overdue)
        filters = {
            "follow_up_required": True,
            "follow_up_date": {"$lt": cutoff_date}
        }
        
        if practice_id:
            if isinstance(practice_id, str):
                practice_id = PydanticObjectId(practice_id)
            filters["practice_id"] = practice_id
        
        return await Visit.find(filters).sort([
            ("follow_up_date", 1)
        ]).limit(limit).to_list()
    
    async def search_visits(
        self,
        search_term: str,
        pet_id: Optional[str | PydanticObjectId] = None,
        practice_id: Optional[str | PydanticObjectId] = None,
        limit: int = 50
    ) -> List[Visit]:
        """
        Search visits by chief complaint, diagnosis, notes, or transcript
        
        Args:
            search_term: Term to search for
            pet_id: Optional pet ID filter
            practice_id: Optional practice ID filter
            limit: Maximum number of visits to return
            
        Returns:
            List of matching visits
        """
        pattern = {"$regex": search_term, "$options": "i"}
        filters = {
            "$or": [
                {"chief_complaint": pattern},
                {"diagnosis": pattern},
                {"treatment_plan": pattern},
                {"notes": pattern},
                {"audio_transcript": pattern}
            ]
        }
        
        if pet_id:
            if isinstance(pet_id, str):
                pet_id = PydanticObjectId(pet_id)
            filters["pet_id"] = pet_id
        
        if practice_id:
            if isinstance(practice_id, str):
                practice_id = PydanticObjectId(practice_id)
            filters["practice_id"] = practice_id
        
        return await Visit.find(filters).sort([
            ("visit_date", -1)
        ]).limit(limit).to_list()
    
    async def update_transcript(
        self,
        visit_id: str | PydanticObjectId,
        transcript: str,
        confidence: Optional[float] = None
    ) -> bool:
        """
        Update visit with audio transcript
        
        Args:
            visit_id: Visit ID
            transcript: Audio transcript text
            confidence: Optional confidence score
            
        Returns:
            True if updated, False if not found
        """
        update_data = {
            "audio_transcript": transcript,
            "transcript_processed_at": datetime.utcnow()
        }
        
        if confidence is not None:
            update_data["transcript_confidence"] = confidence
        
        update_result = await self.update(visit_id, update_data)
        return update_result is not None
    
    async def mark_visit_completed(
        self,
        visit_id: str | PydanticObjectId,
        diagnosis: Optional[str] = None,
        treatment_plan: Optional[str] = None,
        total_cost: Optional[float] = None
    ) -> bool:
        """
        Mark a visit as completed with optional details
        
        Args:
            visit_id: Visit ID
            diagnosis: Optional diagnosis
            treatment_plan: Optional treatment plan
            total_cost: Optional total cost
            
        Returns:
            True if updated, False if not found
        """
        update_data = {
            "status": VisitStatus.COMPLETED,
            "actual_end_time": datetime.utcnow()
        }
        
        if diagnosis:
            update_data["diagnosis"] = diagnosis
        if treatment_plan:
            update_data["treatment_plan"] = treatment_plan
        if total_cost is not None:
            update_data["total_cost"] = total_cost
        
        update_result = await self.update(visit_id, update_data)
        return update_result is not None
