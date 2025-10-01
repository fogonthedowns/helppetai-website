"""
Practice Invitation repository for PostgreSQL - HelpPet MVP
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

try:
    from .base_repository import BaseRepository
    from ..models_pg.practice_invitation import PracticeInvitation
except ImportError:
    from base_repository import BaseRepository
    from models_pg.practice_invitation import PracticeInvitation


class InvitationRepository(BaseRepository[PracticeInvitation]):
    """Repository for PracticeInvitation operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(PracticeInvitation, session)
    
    async def get_by_email(self, email: str) -> List[PracticeInvitation]:
        """Get all invitations for an email address"""
        result = await self.session.execute(
            select(PracticeInvitation).where(PracticeInvitation.email == email)
        )
        return list(result.scalars().all())
    
    async def get_pending_by_email(self, email: str) -> List[PracticeInvitation]:
        """Get pending invitations for an email address"""
        result = await self.session.execute(
            select(PracticeInvitation).where(
                and_(
                    PracticeInvitation.email == email,
                    PracticeInvitation.status == "pending",
                    PracticeInvitation.expires_at > datetime.utcnow()
                )
            )
        )
        return list(result.scalars().all())
    
    async def get_by_practice_id(self, practice_id: UUID) -> List[PracticeInvitation]:
        """Get all invitations for a practice"""
        result = await self.session.execute(
            select(PracticeInvitation).where(PracticeInvitation.practice_id == practice_id)
        )
        return list(result.scalars().all())
    
    async def get_pending_by_practice_id(self, practice_id: UUID) -> List[PracticeInvitation]:
        """Get pending invitations for a practice"""
        result = await self.session.execute(
            select(PracticeInvitation).where(
                and_(
                    PracticeInvitation.practice_id == practice_id,
                    PracticeInvitation.status == "pending",
                    PracticeInvitation.expires_at > datetime.utcnow()
                )
            )
        )
        return list(result.scalars().all())
    
    async def get_by_invite_code(self, invite_code: str) -> Optional[PracticeInvitation]:
        """Get invitation by invite code"""
        result = await self.session.execute(
            select(PracticeInvitation).where(PracticeInvitation.invite_code == invite_code)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id_and_code(self, invite_id: UUID, invite_code: str) -> Optional[PracticeInvitation]:
        """Get invitation by ID and verify code"""
        result = await self.session.execute(
            select(PracticeInvitation).where(
                and_(
                    PracticeInvitation.id == invite_id,
                    PracticeInvitation.invite_code == invite_code
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def check_existing_invitation(self, practice_id: UUID, email: str) -> Optional[PracticeInvitation]:
        """Check if there's already a pending invitation for this email to this practice"""
        result = await self.session.execute(
            select(PracticeInvitation).where(
                and_(
                    PracticeInvitation.practice_id == practice_id,
                    PracticeInvitation.email == email,
                    PracticeInvitation.status == "pending",
                    PracticeInvitation.expires_at > datetime.utcnow()
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def mark_as_accepted(self, invitation: PracticeInvitation) -> PracticeInvitation:
        """Mark invitation as accepted"""
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(invitation)
        return invitation
    
    async def mark_as_expired(self, invitation: PracticeInvitation) -> PracticeInvitation:
        """Mark invitation as expired"""
        invitation.status = "expired"
        await self.session.commit()
        await self.session.refresh(invitation)
        return invitation
    
    async def mark_as_revoked(self, invitation: PracticeInvitation) -> PracticeInvitation:
        """Mark invitation as revoked"""
        invitation.status = "revoked"
        await self.session.commit()
        await self.session.refresh(invitation)
        return invitation

