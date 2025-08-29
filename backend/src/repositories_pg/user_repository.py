"""
User repository for PostgreSQL - HelpPet MVP
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

try:
    from .base_repository import BaseRepository
    from ..models_pg.user import User, UserRole
except ImportError:
    from base_repository import BaseRepository
    from models_pg.user import User, UserRole


class UserRepository(BaseRepository[User]):
    """Repository for User operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        result = await self.session.execute(
            select(User).where(User.role == role)
        )
        return list(result.scalars().all())
    
    async def get_by_practice_id(self, practice_id: UUID) -> List[User]:
        """Get users by practice ID"""
        result = await self.session.execute(
            select(User).where(User.practice_id == practice_id)
        )
        return list(result.scalars().all())
    
    async def get_active_users(self) -> List[User]:
        """Get all active users"""
        result = await self.session.execute(
            select(User).where(User.is_active == True)
        )
        return list(result.scalars().all())
    
    async def username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        result = await self.session.execute(
            select(User.id).where(User.username == username)
        )
        return result.scalar_one_or_none() is not None
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        result = await self.session.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None
    
    async def deactivate_user(self, user_id: UUID) -> bool:
        """Deactivate a user"""
        return await self.update_by_id(user_id, {"is_active": False}) is not None
    
    async def activate_user(self, user_id: UUID) -> bool:
        """Activate a user"""
        return await self.update_by_id(user_id, {"is_active": True}) is not None
