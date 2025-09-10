"""
Contact Form API routes for handling veterinary contact form submissions
"""

import logging
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from ..database_pg import get_db_session
    from ..models_pg.contact_form import ContactForm
    from ..repositories_pg.contact_form_repository import ContactFormRepository
    from ..schemas.contact_form_schemas import ContactFormCreate, ContactFormResponse
    from ..schemas.base import BaseResponse
except ImportError:
    from database_pg import get_db_session
    from models_pg.contact_form import ContactForm
    from repositories_pg.contact_form_repository import ContactFormRepository
    from schemas.contact_form_schemas import ContactFormCreate, ContactFormResponse
    from schemas.base import BaseResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/contact", response_model=BaseResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    form_data: ContactFormCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Submit a veterinary contact form.
    
    This endpoint allows veterinary practices to submit contact forms
    to connect with HelpPet.ai services.
    """
    try:
        logger.info(f"Received contact form submission from {form_data.email} for practice {form_data.practice_name}")
        
        # Create new contact form record
        contact_form = ContactForm(
            id=uuid4(),
            name=form_data.name,
            email=form_data.email,
            phone=form_data.phone,
            practice_name=form_data.practice_name,
            message=form_data.message
        )
        
        # Save to database
        repository = ContactFormRepository(session)
        saved_form = await repository.create(contact_form)
        
        logger.info(f"Contact form submitted successfully with ID: {saved_form.id}")
        
        return BaseResponse(
            success=True,
            message="Contact form submitted successfully! We'll be in touch within 24 hours."
        )
        
    except Exception as e:
        logger.error(f"Error submitting contact form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit contact form. Please try again later."
        )


@router.get("/contact/{contact_id}", response_model=ContactFormResponse)
async def get_contact_form(
    contact_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific contact form by ID.
    Note: In a production system, this would require authentication.
    """
    try:
        repository = ContactFormRepository(session)
        contact_form = await repository.get_by_id(contact_id)
        
        if not contact_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact form not found"
            )
        
        return ContactFormResponse(
            id=str(contact_form.id),
            name=contact_form.name,
            email=contact_form.email,
            phone=contact_form.phone,
            practice_name=contact_form.practice_name,
            message=contact_form.message,
            created_at=contact_form.created_at,
            updated_at=contact_form.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving contact form {contact_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve contact form"
        )