"""
Pet Owner Practice Association model for PostgreSQL - HelpPet MVP
Join table to manage which pet owners are associated with which practices
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, UUID, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base


class AssociationStatus(str, Enum):
    """Status of the association request"""
    PENDING = "pending"
    APPROVED = "approved" 
    REJECTED = "rejected"
    INACTIVE = "inactive"


class AssociationRequestType(str, Enum):
    """Type of association request"""
    NEW_CLIENT = "new_client"        # New pet owner requesting to join practice
    REFERRAL = "referral"            # Referred from another practice
    TRANSFER = "transfer"            # Transferring from another practice
    EMERGENCY = "emergency"          # Emergency visit


class PetOwnerPracticeAssociation(Base):
    """
    Association between pet owners and veterinary practices
    Acts as a join table with additional metadata
    """
    
    __tablename__ = "pet_owner_practice_associations"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    pet_owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pet_owners.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    practice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("veterinary_practices.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Association metadata
    status: Mapped[AssociationStatus] = mapped_column(
        SQLEnum(AssociationStatus), 
        nullable=False, 
        default=AssociationStatus.PENDING,
        index=True
    )
    request_type: Mapped[AssociationRequestType] = mapped_column(
        SQLEnum(AssociationRequestType), 
        nullable=False, 
        default=AssociationRequestType.NEW_CLIENT
    )
    
    # Request details
    requested_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_visit_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Additional info
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    primary_contact: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    pet_owner: Mapped["PetOwner"] = relationship("PetOwner", back_populates="practice_associations")
    practice: Mapped["VeterinaryPractice"] = relationship("VeterinaryPractice")
    requested_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[requested_by_user_id])
    approved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by_user_id])
    
    # Unique constraint to prevent duplicate associations
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self) -> str:
        return f"<PetOwnerPracticeAssociation(id={self.id}, pet_owner_id={self.pet_owner_id}, practice_id={self.practice_id}, status='{self.status}')>"
    
    def approve(self, approved_by_user_id: uuid.UUID) -> None:
        """Approve the association request"""
        self.status = AssociationStatus.APPROVED
        self.approved_by_user_id = approved_by_user_id
        self.approved_at = datetime.utcnow()
    
    def reject(self, rejected_by_user_id: uuid.UUID, notes: Optional[str] = None) -> None:
        """Reject the association request"""
        self.status = AssociationStatus.REJECTED
        self.approved_by_user_id = rejected_by_user_id  # Track who rejected
        if notes:
            self.notes = notes
