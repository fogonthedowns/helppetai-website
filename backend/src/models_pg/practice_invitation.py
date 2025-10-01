"""
Practice Invitation model for PostgreSQL - HelpPet MVP
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import String, DateTime, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base


class PracticeInvitation(Base):
    """Practice invitation model for inviting users to join a practice"""
    
    __tablename__ = "practice_invitations"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Practice and user associations
    practice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("veterinary_practices.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    invite_code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    
    # Invitation metadata
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)  # pending, accepted, expired, revoked
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    practice: Mapped["VeterinaryPractice"] = relationship("VeterinaryPractice", backref="invitations")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self) -> str:
        return f"<PracticeInvitation(id={self.id}, email='{self.email}', practice_id={self.practice_id}, status='{self.status}')>"
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_pending(self) -> bool:
        """Check if invitation is still pending"""
        return self.status == "pending" and not self.is_expired
    
    @staticmethod
    def generate_invite_code() -> str:
        """Generate a secure invite code"""
        return str(uuid.uuid4())
    
    @staticmethod
    def get_default_expiration(days: int = 7) -> datetime:
        """Get default expiration date (7 days from now)"""
        return datetime.now(timezone.utc) + timedelta(days=days)

