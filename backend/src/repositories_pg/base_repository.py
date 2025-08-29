"""
Base repository for PostgreSQL operations
"""

from typing import TypeVar, Generic, List, Optional, Type
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, obj: T) -> T:
        """Create a new record"""
        try:
            self.session.add(obj)
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except IntegrityError:
            await self.session.rollback()
            raise
    
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get record by ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all records with pagination"""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    async def update_by_id(self, id: UUID, update_data: dict) -> Optional[T]:
        """Update record by ID"""
        try:
            # First get the record
            obj = await self.get_by_id(id)
            if not obj:
                return None
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except IntegrityError:
            await self.session.rollback()
            raise
    
    async def delete_by_id(self, id: UUID) -> bool:
        """Delete record by ID"""
        try:
            result = await self.session.execute(
                delete(self.model).where(self.model.id == id)
            )
            await self.session.commit()
            return result.rowcount > 0
        except IntegrityError:
            await self.session.rollback()
            raise
    
    async def count(self) -> int:
        """Count total records"""
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(self.model.id))
        )
        return result.scalar() or 0
    
    async def exists(self, id: UUID) -> bool:
        """Check if record exists"""
        result = await self.session.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None
