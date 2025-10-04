"""
Stripe Customer repository for PostgreSQL - HelpPet AI
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

try:
    from .base_repository import BaseRepository
    from ..models_pg.stripe_customer import StripeCustomer
except ImportError:
    from base_repository import BaseRepository
    from models_pg.stripe_customer import StripeCustomer


class StripeCustomerRepository(BaseRepository[StripeCustomer]):
    """Repository for StripeCustomer operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(StripeCustomer, session)
    
    async def get_by_practice_id(self, practice_id: UUID) -> Optional[StripeCustomer]:
        """Get Stripe customer by practice ID"""
        result = await self.session.execute(
            select(StripeCustomer).where(StripeCustomer.practice_id == practice_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[StripeCustomer]:
        """Get Stripe customer by Stripe customer ID"""
        result = await self.session.execute(
            select(StripeCustomer).where(StripeCustomer.stripe_customer_id == stripe_customer_id)
        )
        return result.scalar_one_or_none()
    
    async def update_payment_method(self, practice_id: UUID, payment_method_id: str) -> Optional[StripeCustomer]:
        """Update default payment method for a practice"""
        stmt = (
            update(StripeCustomer)
            .where(StripeCustomer.practice_id == practice_id)
            .values(default_payment_method_id=payment_method_id)
            .returning(StripeCustomer)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()
    
    async def update_balance(self, practice_id: UUID, balance_cents: int) -> Optional[StripeCustomer]:
        """Update balance credits for a practice"""
        stmt = (
            update(StripeCustomer)
            .where(StripeCustomer.practice_id == practice_id)
            .values(balance_credits_cents=balance_cents)
            .returning(StripeCustomer)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one_or_none()
    
    async def deduct_credits(self, practice_id: UUID, amount_cents: int) -> Optional[StripeCustomer]:
        """Deduct credits from a practice's balance"""
        customer = await self.get_by_practice_id(practice_id)
        if not customer:
            return None
        
        new_balance = customer.balance_credits_cents - amount_cents
        return await self.update_balance(practice_id, new_balance)
    
    async def add_credits(self, practice_id: UUID, amount_cents: int) -> Optional[StripeCustomer]:
        """Add credits to a practice's balance"""
        customer = await self.get_by_practice_id(practice_id)
        if not customer:
            return None
        
        new_balance = customer.balance_credits_cents + amount_cents
        return await self.update_balance(practice_id, new_balance)
    
    async def has_payment_method(self, practice_id: UUID) -> bool:
        """Check if practice has a payment method on file"""
        customer = await self.get_by_practice_id(practice_id)
        return customer is not None and customer.default_payment_method_id is not None

