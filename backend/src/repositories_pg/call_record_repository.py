"""Repository for call record cache operations."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload

from ..models_pg.call_record import CallRecord


class CallRecordRepository:
    """Repository for call record database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_call_id(self, call_id: str) -> Optional[CallRecord]:
        """Get call record by external call ID."""
        query = select(CallRecord).where(CallRecord.call_id == call_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_practice_id(
        self, 
        practice_id: UUID, 
        limit: int = 50, 
        offset: int = 0,
        include_inactive: bool = False
    ) -> List[CallRecord]:
        """Get call records for a practice with pagination."""
        query = select(CallRecord).where(CallRecord.practice_id == practice_id)
        
        if not include_inactive:
            query = query.where(CallRecord.is_active == True)
        
        query = query.order_by(desc(CallRecord.start_timestamp)).offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_stale_records(
        self, 
        max_age_minutes: int = 60,
        limit: int = 100
    ) -> List[CallRecord]:
        """Get records that need syncing (older than max_age_minutes or have sync errors)."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        query = select(CallRecord).where(
            and_(
                CallRecord.is_active == True,
                or_(
                    CallRecord.last_synced_at < cutoff_time,
                    CallRecord.sync_status == "pending",
                    CallRecord.sync_status == "error"
                )
            )
        ).order_by(CallRecord.last_synced_at).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_calls_needing_sync(
        self, 
        practice_id: UUID,
        hours_back: int = 24
    ) -> List[CallRecord]:
        """Get recent calls that might need syncing."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        query = select(CallRecord).where(
            and_(
                CallRecord.practice_id == practice_id,
                CallRecord.is_active == True,
                CallRecord.created_at >= cutoff_time,
                or_(
                    CallRecord.sync_status == "pending",
                    CallRecord.sync_status == "error"
                )
            )
        ).order_by(desc(CallRecord.created_at))
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create_or_update(self, call_record: CallRecord) -> CallRecord:
        """Create new call record or update existing one."""
        existing = await self.get_by_call_id(call_record.call_id)
        
        if existing:
            # Update existing record
            for key, value in call_record.__dict__.items():
                if not key.startswith('_') and key not in ['id', 'created_at']:
                    setattr(existing, key, value)
            existing.updated_at = func.now()
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new record
            self.session.add(call_record)
            await self.session.flush()
            await self.session.refresh(call_record)
            return call_record
    
    async def create_placeholder(
        self, 
        practice_id: UUID, 
        call_id: str,
        agent_id: Optional[str] = None
    ) -> CallRecord:
        """Create a placeholder record for a call we know exists but haven't synced yet."""
        call_record = CallRecord(
            practice_id=practice_id,
            call_id=call_id,
            agent_id=agent_id,
            sync_status="pending"
        )
        
        return await self.create_or_update(call_record)
    
    async def update_sync_status(
        self, 
        call_record: CallRecord, 
        status: str, 
        error: Optional[str] = None
    ) -> CallRecord:
        """Update sync status of a call record."""
        call_record.sync_status = status
        call_record.sync_error = error
        call_record.last_synced_at = func.now()
        
        await self.session.flush()
        await self.session.refresh(call_record)
        return call_record
    
    async def get_stats(self, practice_id: UUID) -> Dict[str, Any]:
        """Get statistics about call records for a practice."""
        # Total calls
        total_query = select(func.count(CallRecord.id)).where(
            and_(CallRecord.practice_id == practice_id, CallRecord.is_active == True)
        )
        total_result = await self.session.execute(total_query)
        total_calls = total_result.scalar() or 0
        
        # Calls needing sync
        pending_query = select(func.count(CallRecord.id)).where(
            and_(
                CallRecord.practice_id == practice_id,
                CallRecord.is_active == True,
                or_(
                    CallRecord.sync_status == "pending",
                    CallRecord.sync_status == "error"
                )
            )
        )
        pending_result = await self.session.execute(pending_query)
        pending_calls = pending_result.scalar() or 0
        
        # Recent calls (last 24h)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_query = select(func.count(CallRecord.id)).where(
            and_(
                CallRecord.practice_id == practice_id,
                CallRecord.is_active == True,
                CallRecord.created_at >= recent_cutoff
            )
        )
        recent_result = await self.session.execute(recent_query)
        recent_calls = recent_result.scalar() or 0
        
        return {
            "total_calls": total_calls,
            "pending_sync": pending_calls,
            "recent_24h": recent_calls,
            "sync_health": "good" if pending_calls < 10 else "needs_attention"
        }
    
    async def delete_old_records(
        self, 
        practice_id: UUID, 
        days_old: int = 90
    ) -> int:
        """Soft delete old call records to manage storage."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        query = select(CallRecord).where(
            and_(
                CallRecord.practice_id == practice_id,
                CallRecord.created_at < cutoff_date,
                CallRecord.is_active == True
            )
        )
        
        result = await self.session.execute(query)
        old_records = list(result.scalars().all())
        
        count = 0
        for record in old_records:
            record.is_active = False
            count += 1
        
        await self.session.flush()
        return count
