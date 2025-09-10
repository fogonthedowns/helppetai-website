"""
Contact Form repository for PostgreSQL operations
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

try:
    from ..models_pg.contact_form import ContactForm
    from .base_repository import BaseRepository
except ImportError:
    from models_pg.contact_form import ContactForm
    from base_repository import BaseRepository


class ContactFormRepository(BaseRepository[ContactForm]):
    """Repository for contact form operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ContactForm, session)
    
    async def get_recent_submissions(self, limit: int = 50) -> List[ContactForm]:
        """Get recent contact form submissions, newest first"""
        result = await self.session.execute(
            select(ContactForm)
            .order_by(desc(ContactForm.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_email(self, email: str, limit: int = 10) -> List[ContactForm]:
        """Get contact form submissions by email address"""
        result = await self.session.execute(
            select(ContactForm)
            .where(ContactForm.email == email)
            .order_by(desc(ContactForm.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())