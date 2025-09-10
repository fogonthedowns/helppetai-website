"""
Contact Form schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class ContactFormCreate(BaseModel):
    """Schema for creating a new contact form submission."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Contact person's name")
    email: EmailStr = Field(..., description="Contact person's email address")
    phone: Optional[str] = Field(default=None, max_length=20, description="Contact person's phone number")
    practice_name: str = Field(..., min_length=1, max_length=200, description="Veterinary practice name")
    message: str = Field(..., min_length=1, description="Contact message")


class ContactFormResponse(BaseModel):
    """Schema for contact form response."""
    
    id: str = Field(..., description="Contact form submission ID")
    name: str = Field(..., description="Contact person's name")
    email: str = Field(..., description="Contact person's email address")
    phone: Optional[str] = Field(default=None, description="Contact person's phone number")
    practice_name: str = Field(..., description="Veterinary practice name")
    message: str = Field(..., description="Contact message")
    created_at: datetime = Field(..., description="Submission timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }