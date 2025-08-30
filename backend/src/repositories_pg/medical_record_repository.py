"""
Medical Record Repository for PostgreSQL - HelpPet MVP
"""

import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, update
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from ..models_pg.medical_record import MedicalRecord
from ..models_pg.pet import Pet
from ..models_pg.user import User


class MedicalRecordRepository(BaseRepository[MedicalRecord]):
    """Repository for Medical Record CRUD operations with versioning support"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(MedicalRecord, session)
    
    async def get_by_pet_id(self, pet_id: uuid.UUID, include_historical: bool = True) -> List[MedicalRecord]:
        """Get all medical records for a specific pet"""
        query = select(MedicalRecord).where(MedicalRecord.pet_id == pet_id)
        
        if not include_historical:
            query = query.where(MedicalRecord.is_current == True)
            
        query = query.order_by(desc(MedicalRecord.visit_date), desc(MedicalRecord.version))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_current_records_by_pet_id(self, pet_id: uuid.UUID) -> List[MedicalRecord]:
        """Get only current (latest version) medical records for a pet - should return only ONE record"""
        query = select(MedicalRecord).where(
            and_(
                MedicalRecord.pet_id == pet_id,
                MedicalRecord.is_current == True
            )
        ).order_by(desc(MedicalRecord.visit_date), desc(MedicalRecord.version)).limit(1)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_record_history(self, pet_id: uuid.UUID) -> List[MedicalRecord]:
        """Get all versions of medical records for a pet, ordered by version"""
        query = select(MedicalRecord).where(
            MedicalRecord.pet_id == pet_id
        ).order_by(desc(MedicalRecord.version), desc(MedicalRecord.created_at))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_with_relationships(self, record_id: uuid.UUID) -> Optional[MedicalRecord]:
        """Get medical record with pet and creator information loaded"""
        query = select(MedicalRecord).options(
            selectinload(MedicalRecord.pet),
            selectinload(MedicalRecord.created_by)
        ).where(MedicalRecord.id == record_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_records_by_veterinarian(self, user_id: uuid.UUID) -> List[MedicalRecord]:
        """Get all medical records created by a specific veterinarian"""
        query = select(MedicalRecord).where(
            MedicalRecord.created_by_user_id == user_id
        ).order_by(desc(MedicalRecord.visit_date))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_new_version(self, existing_record: MedicalRecord, update_data: dict, created_by_user_id: uuid.UUID) -> MedicalRecord:
        """Create a new version of an existing medical record"""
        # First, mark the specific record as not current
        await self.session.execute(
            update(MedicalRecord)
            .where(MedicalRecord.id == existing_record.id)
            .values(is_current=False)
        )
        
        # Create new record with incremented version
        new_record_data = {
            'pet_id': existing_record.pet_id,
            'version': existing_record.version + 1,
            'is_current': True,
            'created_by_user_id': created_by_user_id,
            # Copy existing data
            'record_type': existing_record.record_type,
            'title': existing_record.title,
            'description': existing_record.description,
            'medical_data': existing_record.medical_data,
            'visit_date': existing_record.visit_date,
            'veterinarian_name': existing_record.veterinarian_name,
            'clinic_name': existing_record.clinic_name,
            'diagnosis': existing_record.diagnosis,
            'treatment': existing_record.treatment,
            'medications': existing_record.medications,
            'follow_up_required': existing_record.follow_up_required,
            'follow_up_date': existing_record.follow_up_date,
            'weight': existing_record.weight,
            'temperature': existing_record.temperature,
            'cost': existing_record.cost,
        }
        
        # Apply updates
        new_record_data.update(update_data)
        
        # Create new record
        new_record = MedicalRecord(**new_record_data)
        return await self.create(new_record)
    
    async def get_records_requiring_follow_up(self, before_date: Optional[datetime] = None) -> List[MedicalRecord]:
        """Get records that require follow-up by a certain date"""
        if before_date is None:
            before_date = datetime.now(timezone.utc)
            
        query = select(MedicalRecord).where(
            and_(
                MedicalRecord.is_current == True,
                MedicalRecord.follow_up_required == True,
                MedicalRecord.follow_up_date <= before_date
            )
        ).order_by(MedicalRecord.follow_up_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_records_by_date_range(
        self, 
        pet_id: uuid.UUID, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[MedicalRecord]:
        """Get medical records within a date range for a specific pet"""
        query = select(MedicalRecord).where(
            and_(
                MedicalRecord.pet_id == pet_id,
                MedicalRecord.visit_date >= start_date,
                MedicalRecord.visit_date <= end_date
            )
        ).order_by(desc(MedicalRecord.visit_date))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_records_by_type(self, pet_id: uuid.UUID, record_type: str) -> List[MedicalRecord]:
        """Get medical records of a specific type for a pet"""
        query = select(MedicalRecord).where(
            and_(
                MedicalRecord.pet_id == pet_id,
                MedicalRecord.record_type == record_type
            )
        ).order_by(desc(MedicalRecord.visit_date))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search_records(
        self, 
        pet_id: Optional[uuid.UUID] = None,
        search_term: Optional[str] = None,
        record_type: Optional[str] = None,
        veterinarian_name: Optional[str] = None
    ) -> List[MedicalRecord]:
        """Search medical records with various filters"""
        query = select(MedicalRecord)
        
        conditions = []
        
        if pet_id:
            conditions.append(MedicalRecord.pet_id == pet_id)
            
        if search_term:
            search_pattern = f"%{search_term}%"
            conditions.append(
                MedicalRecord.title.ilike(search_pattern) |
                MedicalRecord.description.ilike(search_pattern) |
                MedicalRecord.diagnosis.ilike(search_pattern) |
                MedicalRecord.treatment.ilike(search_pattern)
            )
            
        if record_type:
            conditions.append(MedicalRecord.record_type == record_type)
            
        if veterinarian_name:
            conditions.append(MedicalRecord.veterinarian_name.ilike(f"%{veterinarian_name}%"))
        
        if conditions:
            query = query.where(and_(*conditions))
            
        query = query.order_by(desc(MedicalRecord.visit_date))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_latest_weight_record(self, pet_id: uuid.UUID) -> Optional[MedicalRecord]:
        """Get the most recent medical record with weight information"""
        query = select(MedicalRecord).where(
            and_(
                MedicalRecord.pet_id == pet_id,
                MedicalRecord.weight.isnot(None)
            )
        ).order_by(desc(MedicalRecord.visit_date)).limit(1)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
