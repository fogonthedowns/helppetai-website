"""
Practice Invitation routes for PostgreSQL - HelpPet MVP
"""

from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database_pg import get_db_session
from ..models_pg.practice_invitation import PracticeInvitation
from ..models_pg.user import User, UserRole
from ..models_pg.practice import VeterinaryPractice
from ..repositories_pg.invitation_repository import InvitationRepository
from ..repositories_pg.practice_repository import PracticeRepository
from ..repositories_pg.user_repository import UserRepository
from ..schemas.invitation_schemas import (
    PracticeInvitationCreate,
    PracticeInvitationResponse,
    PracticeInvitationPublic,
    PracticeInvitationAccept
)
from ..auth.jwt_auth_pg import get_current_user
from ..utils.email_service import send_practice_invitation_email

router = APIRouter()


@router.get("/invites/my-invitations", response_model=List[dict])
async def get_my_invitations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> List[dict]:
    """
    Get all pending invitations for the current user's email.
    
    Returns invitations sent to the user's email address.
    """
    invitation_repo = InvitationRepository(session)
    
    # Get all invitations for this email
    invitations = await invitation_repo.get_by_email(current_user.email)
    
    # Get practice details for each invitation
    practice_repo = PracticeRepository(session)
    user_repo = UserRepository(session)
    
    result = []
    for inv in invitations:
        practice = await practice_repo.get_by_id(inv.practice_id)
        inviter = await user_repo.get_by_id(inv.created_by)
        
        result.append({
            "id": str(inv.id),
            "practice_id": str(inv.practice_id),
            "practice_name": practice.name if practice else "Unknown Practice",
            "email": inv.email,
            "status": inv.status.value if hasattr(inv.status, 'value') else str(inv.status),
            "invite_code": str(inv.invite_code),
            "created_at": inv.created_at.isoformat(),
            "expires_at": inv.expires_at.isoformat(),
            "inviter_name": inviter.full_name if inviter else "Unknown"
        })
    
    return result


@router.post("/practices/{practice_id}/invites", response_model=PracticeInvitationPublic, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    practice_id: UUID = Path(..., description="Practice ID"),
    invitation_data: PracticeInvitationCreate = ...,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> PracticeInvitationPublic:
    """
    Create an invitation to join a practice.
    
    Only VET_STAFF or ADMIN users belonging to the practice can create invitations.
    """
    # Verify user has permission to invite (must be PRACTICE_ADMIN or SYSTEM_ADMIN)
    if current_user.role not in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practice administrators can send invitations"
        )
    
    if current_user.practice_id != practice_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only send invitations for your own practice"
        )
    
    # Verify practice exists
    practice_repo = PracticeRepository(session)
    practice = await practice_repo.get_by_id(practice_id)
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice not found"
        )
    
    # Check if user with this email already exists in the practice
    user_repo = UserRepository(session)
    existing_user = await user_repo.get_by_email(invitation_data.email)
    if existing_user and existing_user.practice_id == practice_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this practice"
        )
    
    # Check for existing pending invitation
    invitation_repo = InvitationRepository(session)
    existing_invitation = await invitation_repo.check_existing_invitation(practice_id, invitation_data.email)
    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending invitation for this email already exists"
        )
    
    # Create invitation
    new_invitation = PracticeInvitation(
        practice_id=practice_id,
        email=invitation_data.email,
        invite_code=PracticeInvitation.generate_invite_code(),
        created_by=current_user.id,
        expires_at=PracticeInvitation.get_default_expiration(invitation_data.expiration_days),
        status="pending"
    )
    
    created_invitation = await invitation_repo.create(new_invitation)
    
    # Send invitation email
    try:
        email_sent = send_practice_invitation_email(
            recipient_email=invitation_data.email,
            practice_name=practice.name,
            inviter_name=current_user.full_name or current_user.username,
            invite_id=str(created_invitation.id),
            invite_code=created_invitation.invite_code,
            inviter_email=current_user.email
        )
        if not email_sent:
            # Log warning but don't fail the invitation creation
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to send invitation email to {invitation_data.email}")
    except Exception as e:
        # Log error but continue - invitation was created successfully
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending invitation email to {invitation_data.email}: {str(e)}")
    
    # Return without invite_code for security
    return PracticeInvitationPublic(
        id=created_invitation.id,
        practice_id=created_invitation.practice_id,
        practice_name=practice.name,
        email=created_invitation.email,
        status=created_invitation.status,
        created_at=created_invitation.created_at,
        expires_at=created_invitation.expires_at
    )


@router.get("/practices/{practice_id}/members", response_model=List[dict])
async def list_practice_members(
    practice_id: UUID = Path(..., description="Practice ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> List[dict]:
    """
    Get all active members of a practice.
    
    Only VET_STAFF or ADMIN users belonging to the practice can view members.
    """
    # Verify user has permission (any practice staff can view members)
    if current_user.role not in [UserRole.VET_STAFF, UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practice staff can view team members"
        )
    
    if current_user.practice_id != practice_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view members of your own practice"
        )
    
    # Get all users for this practice
    user_repo = UserRepository(session)
    members = await user_repo.get_by_practice_id(practice_id)
    
    return [
        {
            "id": str(member.id),
            "username": member.username,
            "full_name": member.full_name,
            "email": member.email,
            "role": member.role.value,
            "is_active": member.is_active,
            "created_at": member.created_at.isoformat()
        }
        for member in members
        if member.role != UserRole.PENDING_INVITE  # Exclude pending invites
    ]


@router.delete("/practices/{practice_id}/members/{user_id}", status_code=status.HTTP_200_OK)
async def remove_practice_member(
    practice_id: UUID = Path(..., description="Practice ID"),
    user_id: UUID = Path(..., description="User ID to remove"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Remove a member from a practice.
    
    Only ADMIN users belonging to the practice can remove members.
    Cannot remove yourself.
    """
    # Only PRACTICE_ADMIN or SYSTEM_ADMIN can remove members
    if current_user.role not in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practice administrators can remove team members"
        )
    
    if current_user.practice_id != practice_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only remove members from your own practice"
        )
    
    # Cannot remove yourself
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from the practice"
        )
    
    # Get the user to remove
    user_repo = UserRepository(session)
    user_to_remove = await user_repo.get_by_id(user_id)
    
    if not user_to_remove:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify user belongs to this practice
    if user_to_remove.practice_id != practice_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user does not belong to your practice"
        )
    
    # Don't allow removing other practice admins or system admins
    if user_to_remove.role in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove administrator users. Please change their role first."
        )
    
    # Change user's role to PENDING_INVITE (keeps them in practice but removes access)
    user_to_remove.role = UserRole.PENDING_INVITE
    user_to_remove.practice_id = None
    await session.commit()
    await session.refresh(user_to_remove)
    
    return {
        "message": "User removed from practice successfully",
        "user_id": str(user_id)
    }


@router.get("/practices/{practice_id}/invites", response_model=List[PracticeInvitationResponse])
async def list_practice_invitations(
    practice_id: UUID = Path(..., description="Practice ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> List[PracticeInvitationResponse]:
    """
    Get all invitations for a specific practice.
    
    Only VET_STAFF or ADMIN users belonging to the practice can view invitations.
    """
    # Verify user has permission (any practice staff can view invitations)
    if current_user.role not in [UserRole.VET_STAFF, UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practice staff can view invitations"
        )
    
    if current_user.practice_id != practice_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view invitations for your own practice"
        )
    
    # Get invitations
    invitation_repo = InvitationRepository(session)
    invitations = await invitation_repo.get_by_practice_id(practice_id)
    
    return [
        PracticeInvitationResponse(
            id=inv.id,
            practice_id=inv.practice_id,
            email=inv.email,
            status=inv.status,
            created_by=inv.created_by,
            created_at=inv.created_at,
            expires_at=inv.expires_at,
            accepted_at=inv.accepted_at
        )
        for inv in invitations
    ]


@router.get("/invites/{invite_id}", response_model=PracticeInvitationPublic)
async def get_invitation_details(
    invite_id: UUID = Path(..., description="Invitation ID"),
    code: str = Query(..., description="Invitation code for verification"),
    session: AsyncSession = Depends(get_db_session)
) -> PracticeInvitationPublic:
    """
    Get invitation details by ID and code.
    
    This is a public endpoint that requires the invite code for verification.
    """
    invitation_repo = InvitationRepository(session)
    invitation = await invitation_repo.get_by_id_and_code(invite_id, code)
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or invalid code"
        )
    
    # Check if expired
    if invitation.is_expired:
        # Mark as expired in database
        await invitation_repo.mark_as_expired(invitation)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )
    
    # Check if already used
    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation is no longer pending (status: {invitation.status})"
        )
    
    # Get practice name
    practice_repo = PracticeRepository(session)
    practice = await practice_repo.get_by_id(invitation.practice_id)
    
    return PracticeInvitationPublic(
        id=invitation.id,
        practice_id=invitation.practice_id,
        practice_name=practice.name if practice else None,
        email=invitation.email,
        status=invitation.status,
        created_at=invitation.created_at,
        expires_at=invitation.expires_at
    )


@router.delete("/practices/{practice_id}/invites/{invite_id}", status_code=status.HTTP_200_OK)
async def revoke_invitation(
    practice_id: UUID = Path(..., description="Practice ID"),
    invite_id: UUID = Path(..., description="Invitation ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Revoke/cancel a pending invitation.
    
    Only VET_STAFF or ADMIN users belonging to the practice can revoke invitations.
    """
    # Verify user has permission (only admins can revoke invitations)
    if current_user.role not in [UserRole.PRACTICE_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only practice administrators can revoke invitations"
        )
    
    if current_user.practice_id != practice_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only revoke invitations for your own practice"
        )
    
    # Get the invitation
    invitation_repo = InvitationRepository(session)
    invitation = await invitation_repo.get_by_id(invite_id)
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    # Verify invitation belongs to this practice
    if invitation.practice_id != practice_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation does not belong to your practice"
        )
    
    # Check if invitation is already accepted or revoked
    if invitation.status == "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke an invitation that has already been accepted"
        )
    
    if invitation.status == "revoked":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation has already been revoked"
        )
    
    # Revoke the invitation
    await invitation_repo.mark_as_revoked(invitation)
    
    return {
        "message": "Invitation revoked successfully",
        "invitation_id": str(invite_id)
    }


@router.post("/invites/{invite_id}/accept", response_model=dict, status_code=status.HTTP_200_OK)
async def accept_invitation(
    invite_id: UUID = Path(..., description="Invitation ID"),
    accept_data: PracticeInvitationAccept = ...,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Accept a practice invitation.
    
    The authenticated user must match the email of the invitation.
    This will update the user's role from PENDING_INVITE to VET_STAFF
    and associate them with the practice.
    """
    invitation_repo = InvitationRepository(session)
    invitation = await invitation_repo.get_by_id_and_code(invite_id, accept_data.invite_code)
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or invalid code"
        )
    
    # Verify the current user's email matches the invitation email
    if current_user.email != invitation.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation is for a different email address"
        )
    
    # Check if expired
    if invitation.is_expired:
        await invitation_repo.mark_as_expired(invitation)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )
    
    # Check if already used
    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation has already been {invitation.status}"
        )
    
    # Update user's practice and role
    user_repo = UserRepository(session)
    current_user.practice_id = invitation.practice_id
    
    # If user was PENDING_INVITE, change to VET_STAFF
    if current_user.role == UserRole.PENDING_INVITE:
        current_user.role = UserRole.VET_STAFF
    
    await session.commit()
    await session.refresh(current_user)
    
    # Mark invitation as accepted
    await invitation_repo.mark_as_accepted(invitation)
    
    # Get practice details
    practice_repo = PracticeRepository(session)
    practice = await practice_repo.get_by_id(invitation.practice_id)
    
    return {
        "message": "Invitation accepted successfully",
        "practice": {
            "id": str(practice.id),
            "name": practice.name
        },
        "user": {
            "id": str(current_user.id),
            "role": current_user.role.value
        }
    }

