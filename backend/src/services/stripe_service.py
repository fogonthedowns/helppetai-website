"""
Stripe Service for HelpPet AI
Handles Stripe API interactions for payment processing
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
import stripe
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from ..config import Settings
    from ..repositories_pg.stripe_customer_repository import StripeCustomerRepository
    from ..models_pg.stripe_customer import StripeCustomer
except ImportError:
    from config import Settings
    from repositories_pg.stripe_customer_repository import StripeCustomerRepository
    from models_pg.stripe_customer import StripeCustomer


logger = logging.getLogger(__name__)


class StripeService:
    """Service for Stripe payment operations"""
    
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.repository = StripeCustomerRepository(session)
        
        # Initialize Stripe API
        if settings.stripe_api_key:
            stripe.api_key = settings.stripe_api_key
        else:
            logger.warning("Stripe API key not configured")
    
    async def create_customer(
        self, 
        practice_id: UUID, 
        user_id: UUID, 
        email: str,
        practice_name: str
    ) -> StripeCustomer:
        """
        Create a new Stripe customer for a practice
        Automatically adds $10 in credits
        """
        try:
            # Check if customer already exists for this practice
            existing = await self.repository.get_by_practice_id(practice_id)
            if existing:
                logger.info(f"Stripe customer already exists for practice {practice_id}")
                return existing
            
            # Create customer in Stripe
            stripe_customer = stripe.Customer.create(
                email=email,
                description=f"Practice: {practice_name}",
                metadata={
                    "practice_id": str(practice_id),
                    "created_by_user_id": str(user_id)
                }
            )
            
            logger.info(f"Created Stripe customer {stripe_customer.id} for practice {practice_id}")
            
            # Save to database with $10 in credits (1000 cents)
            db_customer = StripeCustomer(
                practice_id=practice_id,
                created_by_user_id=user_id,
                stripe_customer_id=stripe_customer.id,
                email=email,
                balance_credits_cents=1000  # $10.00 in credits
            )
            
            created = await self.repository.create(db_customer)
            logger.info(f"Saved Stripe customer to database with $10 credits")
            
            return created
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error: {e}")
            raise Exception(f"Failed to create Stripe customer: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating Stripe customer: {e}")
            raise
    
    async def add_payment_method(
        self, 
        practice_id: UUID, 
        payment_method_id: str,
        set_as_default: bool = True
    ) -> Dict[str, Any]:
        """
        Add a payment method to a customer and optionally set as default
        """
        try:
            customer = await self.repository.get_by_practice_id(practice_id)
            if not customer:
                raise ValueError(f"No Stripe customer found for practice {practice_id}")
            
            # Attach payment method to customer
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer.stripe_customer_id,
            )
            
            logger.info(f"Attached payment method {payment_method_id} to customer {customer.stripe_customer_id}")
            
            # Set as default if requested
            if set_as_default:
                stripe.Customer.modify(
                    customer.stripe_customer_id,
                    invoice_settings={
                        'default_payment_method': payment_method_id,
                    },
                )
                
                # Update in database
                await self.repository.update_payment_method(practice_id, payment_method_id)
                logger.info(f"Set payment method {payment_method_id} as default")
            
            return {
                "success": True,
                "payment_method_id": payment_method_id,
                "is_default": set_as_default,
                "card": {
                    "brand": payment_method.card.brand,
                    "last4": payment_method.card.last4,
                    "exp_month": payment_method.card.exp_month,
                    "exp_year": payment_method.card.exp_year,
                }
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error: {e}")
            raise Exception(f"Failed to add payment method: {str(e)}")
        except Exception as e:
            logger.error(f"Error adding payment method: {e}")
            raise
    
    async def remove_payment_method(
        self, 
        practice_id: UUID, 
        payment_method_id: str
    ) -> Dict[str, Any]:
        """
        Remove a payment method from a customer
        """
        try:
            customer = await self.repository.get_by_practice_id(practice_id)
            if not customer:
                raise ValueError(f"No Stripe customer found for practice {practice_id}")
            
            # Detach payment method
            stripe.PaymentMethod.detach(payment_method_id)
            
            logger.info(f"Detached payment method {payment_method_id} from customer {customer.stripe_customer_id}")
            
            # If this was the default, clear it in database
            if customer.default_payment_method_id == payment_method_id:
                await self.repository.update_payment_method(practice_id, None)
            
            return {
                "success": True,
                "message": "Payment method removed successfully"
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error: {e}")
            raise Exception(f"Failed to remove payment method: {str(e)}")
        except Exception as e:
            logger.error(f"Error removing payment method: {e}")
            raise
    
    async def list_payment_methods(self, practice_id: UUID) -> List[Dict[str, Any]]:
        """
        List all payment methods for a customer
        """
        try:
            customer = await self.repository.get_by_practice_id(practice_id)
            if not customer:
                return []
            
            # Get payment methods from Stripe
            payment_methods = stripe.PaymentMethod.list(
                customer=customer.stripe_customer_id,
                type="card",
            )
            
            result = []
            for pm in payment_methods.data:
                result.append({
                    "id": pm.id,
                    "brand": pm.card.brand,
                    "last4": pm.card.last4,
                    "exp_month": pm.card.exp_month,
                    "exp_year": pm.card.exp_year,
                    "is_default": pm.id == customer.default_payment_method_id
                })
            
            return result
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error: {e}")
            raise Exception(f"Failed to list payment methods: {str(e)}")
        except Exception as e:
            logger.error(f"Error listing payment methods: {e}")
            raise
    
    async def set_default_payment_method(
        self, 
        practice_id: UUID, 
        payment_method_id: str
    ) -> Dict[str, Any]:
        """
        Set a payment method as the default for a customer
        """
        try:
            customer = await self.repository.get_by_practice_id(practice_id)
            if not customer:
                raise ValueError(f"No Stripe customer found for practice {practice_id}")
            
            # Update in Stripe
            stripe.Customer.modify(
                customer.stripe_customer_id,
                invoice_settings={
                    'default_payment_method': payment_method_id,
                },
            )
            
            # Update in database
            await self.repository.update_payment_method(practice_id, payment_method_id)
            
            logger.info(f"Set payment method {payment_method_id} as default for practice {practice_id}")
            
            return {
                "success": True,
                "message": "Default payment method updated successfully"
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error: {e}")
            raise Exception(f"Failed to set default payment method: {str(e)}")
        except Exception as e:
            logger.error(f"Error setting default payment method: {e}")
            raise
    
    async def get_customer_info(self, practice_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get customer information including balance and payment methods
        """
        try:
            customer = await self.repository.get_by_practice_id(practice_id)
            if not customer:
                return None
            
            payment_methods = await self.list_payment_methods(practice_id)
            
            return {
                "stripe_customer_id": customer.stripe_customer_id,
                "email": customer.email,
                "balance_credits_cents": customer.balance_credits_cents,
                "balance_credits_dollars": customer.balance_credits_dollars,
                "has_payment_method": customer.has_payment_method,
                "default_payment_method_id": customer.default_payment_method_id,
                "payment_methods": payment_methods,
                "created_at": customer.created_at.isoformat(),
                "updated_at": customer.updated_at.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error getting customer info: {e}")
            raise
    
    async def create_setup_intent(self, practice_id: UUID) -> Dict[str, Any]:
        """
        Create a SetupIntent for adding a payment method
        Returns the client_secret for frontend to complete the setup
        """
        try:
            customer = await self.repository.get_by_practice_id(practice_id)
            if not customer:
                raise ValueError(f"No Stripe customer found for practice {practice_id}")
            
            # Create SetupIntent
            setup_intent = stripe.SetupIntent.create(
                customer=customer.stripe_customer_id,
                payment_method_types=['card'],
            )
            
            logger.info(f"Created SetupIntent {setup_intent.id} for practice {practice_id}")
            
            return {
                "client_secret": setup_intent.client_secret,
                "setup_intent_id": setup_intent.id,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error: {e}")
            raise Exception(f"Failed to create setup intent: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating setup intent: {e}")
            raise
    
    async def has_payment_method(self, practice_id: UUID) -> bool:
        """
        Check if a practice has a payment method on file
        """
        return await self.repository.has_payment_method(practice_id)

