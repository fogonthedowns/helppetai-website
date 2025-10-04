"""
Stripe Customer model for PostgreSQL - HelpPet AI
Tracks Stripe customer information for billing and payments
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base


class StripeCustomer(Base):
    """Stripe customer model - one per practice for billing"""
    
    __tablename__ = "stripe_customers"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    practice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("veterinary_practices.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One Stripe customer per practice
        index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False
    )
    
    # Stripe information
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    default_payment_method_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Credits balance in cents (starts at $10.00 = 1000 cents)
    balance_credits_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    # practice: Mapped["VeterinaryPractice"] = relationship("VeterinaryPractice", back_populates="stripe_customer")
    # created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    
    def __repr__(self) -> str:
        return f"<StripeCustomer(id={self.id}, practice_id={self.practice_id}, stripe_customer_id='{self.stripe_customer_id}')>"
    
    @property
    def balance_credits_dollars(self) -> float:
        """Get credits balance in dollars"""
        return self.balance_credits_cents / 100.0
    
    @property
    def has_payment_method(self) -> bool:
        """Check if customer has a payment method on file"""
        return self.default_payment_method_id is not None

