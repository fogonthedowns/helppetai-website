"""
Authentication routes for JWT-based authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from pydantic import BaseModel

from ..auth.jwt_auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..models.user import User as UserDocument

router = APIRouter(tags=["Authentication"])

@router.get("/ping")
async def ping():
    """Test endpoint to verify auth routes are working."""
    return {"message": "Auth routes are working!"}

class Token(BaseModel):
    access_token: str
    token_type: str

class SignupRequest(BaseModel):
    username: str
    password: str

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint that returns JWT token."""
    try:
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token, 
            "token_type": "bearer"
        }
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

@router.post("/signup", response_model=dict)
async def signup(signup_data: SignupRequest):
    """Simple signup endpoint."""
    # Check if user already exists
    existing_user = await UserDocument.find_one(UserDocument.username == signup_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user in MongoDB
    hashed_password = get_password_hash(signup_data.password)
    new_user = UserDocument(
        username=signup_data.username,
        hashed_password=hashed_password
    )
    await new_user.insert()
    
    return {"message": f"User {signup_data.username} created successfully"}

@router.get("/me")
async def read_users_me(current_user: UserDocument = Depends(get_current_user)):
    """Get current user info."""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "practice_id": str(current_user.practice_id) if current_user.practice_id else None,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "is_active": current_user.is_active
    }
