"""
Stripe routes for payment processing - HelpPet AI
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..database_pg import get_db_session
from ..models_pg.user import User
from ..auth.jwt_auth_pg import get_current_user
from ..services.stripe_service import StripeService
from ..config import Settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class CreateCustomerRequest(BaseModel):
    practice_id: str
    email: str
    practice_name: str


class AddPaymentMethodRequest(BaseModel):
    payment_method_id: str
    set_as_default: bool = True


class RemovePaymentMethodRequest(BaseModel):
    payment_method_id: str


class SetDefaultPaymentMethodRequest(BaseModel):
    payment_method_id: str


class SetupIntentRequest(BaseModel):
    practice_id: str


# Dependency to get settings
def get_settings() -> Settings:
    """Get application settings"""
    from ..config import Settings
    return Settings()


@router.post("/customers")
async def create_stripe_customer(
    request: CreateCustomerRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
):
    """
    Create a Stripe customer for a practice
    Automatically adds $10 in credits
    """
    try:
        # Verify user belongs to the practice or is admin
        if str(current_user.practice_id) != request.practice_id and not current_user.is_practice_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to create a Stripe customer for this practice"
            )
        
        service = StripeService(session, settings)
        customer = await service.create_customer(
            practice_id=UUID(request.practice_id),
            user_id=current_user.id,
            email=request.email,
            practice_name=request.practice_name
        )
        
        return {
            "success": True,
            "message": "Stripe customer created successfully with $10 in credits",
            "customer": {
                "id": str(customer.id),
                "stripe_customer_id": customer.stripe_customer_id,
                "email": customer.email,
                "balance_credits_dollars": customer.balance_credits_dollars,
                "created_at": customer.created_at.isoformat()
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating Stripe customer: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/customers/{practice_id}")
async def get_customer_info(
    practice_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
):
    """
    Get Stripe customer information including balance and payment methods
    """
    try:
        # Verify user belongs to the practice or is admin
        if str(current_user.practice_id) != practice_id and not current_user.is_practice_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this practice's billing information"
            )
        
        service = StripeService(session, settings)
        customer_info = await service.get_customer_info(UUID(practice_id))
        
        if not customer_info:
            return {
                "success": False,
                "message": "No Stripe customer found for this practice",
                "customer": None
            }
        
        return {
            "success": True,
            "customer": customer_info
        }
        
    except Exception as e:
        logger.error(f"Error getting customer info: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/customers/{practice_id}/setup-intent")
async def create_setup_intent(
    practice_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
):
    """
    Create a SetupIntent for adding a payment method
    Returns client_secret for frontend to complete the setup
    """
    try:
        # Verify user belongs to the practice or is admin
        if str(current_user.practice_id) != practice_id and not current_user.is_practice_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to manage payment methods for this practice"
            )
        
        service = StripeService(session, settings)
        setup_intent = await service.create_setup_intent(UUID(practice_id))
        
        return {
            "success": True,
            **setup_intent
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating setup intent: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/customers/{practice_id}/payment-methods")
async def add_payment_method(
    practice_id: str,
    request: AddPaymentMethodRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
):
    """
    Add a payment method to a customer
    """
    try:
        # Verify user belongs to the practice or is admin
        if str(current_user.practice_id) != practice_id and not current_user.is_practice_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to manage payment methods for this practice"
            )
        
        service = StripeService(session, settings)
        result = await service.add_payment_method(
            practice_id=UUID(practice_id),
            payment_method_id=request.payment_method_id,
            set_as_default=request.set_as_default
        )
        
        return {
            "success": True,
            "message": "Payment method added successfully",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding payment method: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/customers/{practice_id}/payment-methods/{payment_method_id}")
async def remove_payment_method(
    practice_id: str,
    payment_method_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
):
    """
    Remove a payment method from a customer
    """
    try:
        # Verify user belongs to the practice or is admin
        if str(current_user.practice_id) != practice_id and not current_user.is_practice_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to manage payment methods for this practice"
            )
        
        service = StripeService(session, settings)
        result = await service.remove_payment_method(
            practice_id=UUID(practice_id),
            payment_method_id=payment_method_id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing payment method: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/customers/{practice_id}/payment-methods")
async def list_payment_methods(
    practice_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
):
    """
    List all payment methods for a customer
    """
    try:
        # Verify user belongs to the practice or is admin
        if str(current_user.practice_id) != practice_id and not current_user.is_practice_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view payment methods for this practice"
            )
        
        service = StripeService(session, settings)
        payment_methods = await service.list_payment_methods(UUID(practice_id))
        
        return {
            "success": True,
            "payment_methods": payment_methods
        }
        
    except Exception as e:
        logger.error(f"Error listing payment methods: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/customers/{practice_id}/payment-methods/{payment_method_id}/set-default")
async def set_default_payment_method(
    practice_id: str,
    payment_method_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
):
    """
    Set a payment method as the default
    """
    try:
        # Verify user belongs to the practice or is admin
        if str(current_user.practice_id) != practice_id and not current_user.is_practice_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to manage payment methods for this practice"
            )
        
        service = StripeService(session, settings)
        result = await service.set_default_payment_method(
            practice_id=UUID(practice_id),
            payment_method_id=payment_method_id
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting default payment method: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/customers/{practice_id}/has-payment-method")
async def check_has_payment_method(
    practice_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings)
):
    """
    Check if practice has a payment method on file (for paywall checks)
    """
    try:
        # Verify user belongs to the practice or is admin
        if str(current_user.practice_id) != practice_id and not current_user.is_practice_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view billing information for this practice"
            )
        
        service = StripeService(session, settings)
        has_payment = await service.has_payment_method(UUID(practice_id))
        
        return {
            "success": True,
            "has_payment_method": has_payment
        }
        
    except Exception as e:
        logger.error(f"Error checking payment method: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/config")
async def get_stripe_config(
    settings: Settings = Depends(get_settings)
):
    """
    Get Stripe publishable key for frontend
    """
    return {
        "publishable_key": settings.stripe_publishable_key
    }

