"""
Pydantic schemas for practice invitations
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, UUID4


class PracticeInvitationCreate(BaseModel):
    """Schema for creating a practice invitation"""
    email: EmailStr
    expiration_days: Optional[int] = 7


class PracticeInvitationResponse(BaseModel):
    """Schema for practice invitation response"""
    id: UUID4
    practice_id: UUID4
    email: str
    status: str
    created_by: UUID4
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PracticeInvitationPublic(BaseModel):
    """Public schema for invitation (without sensitive data like invite_code)"""
    id: UUID4
    practice_id: UUID4
    practice_name: Optional[str] = None
    email: str
    status: str
    created_at: datetime
    expires_at: datetime
    
    class Config:
        from_attributes = True


class PracticeInvitationAccept(BaseModel):
    """Schema for accepting an invitation"""
    invite_code: str


class PracticeInvitationVerify(BaseModel):
    """Schema for verifying an invitation (query params)"""
    code: str

