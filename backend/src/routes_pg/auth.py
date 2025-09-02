"""
Authentication routes for PostgreSQL - HelpPet MVP
"""

from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from uuid import uuid4, UUID
import subprocess
import os
from typing import Optional

from ..database_pg import get_db_session
from ..models_pg.user import User, UserRole
from ..repositories_pg.user_repository import UserRepository
from ..repositories_pg.practice_repository import PracticeRepository
from ..auth.jwt_auth_pg import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: str
    role: UserRole = UserRole.VET_STAFF


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    practice_id: Optional[str] = None


class PracticeAssociation(BaseModel):
    practice_id: str


class AdminPasswordRequest(BaseModel):
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    full_name: str
    role: UserRole
    is_active: bool
    practice_id: Optional[str] = None


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db_session)
):
    """Login endpoint to get JWT token"""
    user = await authenticate_user(session, form_data.username, form_data.password)
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
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/signup", response_model=UserResponse)
async def signup(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """User registration endpoint"""
    user_repo = UserRepository(session)
    
    # Check if username already exists
    if await user_repo.username_exists(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if await user_repo.email_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        password_hash=hashed_password,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    created_user = await user_repo.create(new_user)
    
    return UserResponse(
        id=str(created_user.id),
        username=created_user.username,
        email=created_user.email,
        full_name=created_user.full_name,
        role=created_user.role,
        is_active=created_user.is_active,
        practice_id=str(created_user.practice_id) if created_user.practice_id else None
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        practice_id=str(current_user.practice_id) if current_user.practice_id else None
    )


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Update current user profile"""
    user_repo = UserRepository(session)
    
    # Prepare update data
    update_data = {}
    
    if user_update.email is not None:
        # Check if email is already taken by another user
        if user_update.email != current_user.email:
            if await user_repo.email_exists(user_update.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        update_data["email"] = user_update.email
    
    if user_update.full_name is not None:
        update_data["full_name"] = user_update.full_name
    
    if user_update.practice_id is not None:
        # Validate practice exists
        practice_repo = PracticeRepository(session)
        practice_uuid = UUID(user_update.practice_id)
        practice = await practice_repo.get_by_id(practice_uuid)
        if not practice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practice not found"
            )
        update_data["practice_id"] = practice_uuid
    
    # Update user
    updated_user = await user_repo.update_by_id(current_user.id, update_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        role=updated_user.role,
        is_active=updated_user.is_active,
        practice_id=str(updated_user.practice_id) if updated_user.practice_id else None
    )


@router.put("/me/practice", response_model=UserResponse)
async def associate_with_practice(
    practice_association: PracticeAssociation,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Associate current user with a practice"""
    user_repo = UserRepository(session)
    practice_repo = PracticeRepository(session)
    
    # Validate practice exists
    practice_uuid = UUID(practice_association.practice_id)
    practice = await practice_repo.get_by_id(practice_uuid)
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice not found"
        )
    
    # Update user's practice association
    updated_user = await user_repo.update_by_id(
        current_user.id, 
        {"practice_id": practice_uuid}
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        role=updated_user.role,
        is_active=updated_user.is_active,
        practice_id=str(updated_user.practice_id) if updated_user.practice_id else None
    )


@router.delete("/me/practice", response_model=UserResponse)
async def remove_practice_association(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Remove current user's practice association"""
    user_repo = UserRepository(session)
    
    # Update user to remove practice association
    updated_user = await user_repo.update_by_id(
        current_user.id, 
        {"practice_id": None}
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        email=updated_user.email,
        full_name=updated_user.full_name,
        role=updated_user.role,
        is_active=updated_user.is_active,
        practice_id=None
    )


@router.get("/test-credentials")
async def get_test_credentials():
    """Get test credentials for development"""
    return {
        "message": "Test credentials available",
        "credentials": [
            {"username": "vet1", "password": "password123"},
            {"username": "vet2", "password": "password123"},
            {"username": "tech1", "password": "password123"},
            {"username": "admin", "password": "admin123"}
        ]
    }


class AdminRequest(BaseModel):
    password: str


@router.post("/admin/migrate")
async def run_migrations(request: AdminRequest):
    """Run database migrations"""
    
    # Check hardcoded admin password
    if request.password != "HelpPetSeed2024!":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin password"
        )
    
    try:
        # Set RDS environment variables for alembic
        env = os.environ.copy()
        env.update({
            "RDS_HOSTNAME": "helppet-prod-postgres.c9206kio0fa8.us-west-1.rds.amazonaws.com",
            "RDS_PORT": "5432", 
            "RDS_DB_NAME": "postgres",
            "RDS_USERNAME": "helppetadmin",
            "RDS_PASSWORD": "dkxrBrYfY2Yy7R4I+knv0Z0kcMdaQZPHoSToOxuGy3g=DB"
        })
        
        # Run alembic upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd="/app",  # Docker container working directory
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {
                "message": "Database migrations completed successfully",
                "output": result.stdout,
                "errors": result.stderr if result.stderr else None
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Migration failed: {result.stderr}"
            )
            
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Migration timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration error: {str(e)}"
        )


@router.post("/admin/seed")
async def seed_test_users(
    request: AdminRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """Seed the database with test users"""
    
    # Check hardcoded admin password
    if request.password != "HelpPetSeed2024!":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid seed password"
        )
    
    # Test users to create
    test_users = [
        {
            "username": "admin",
            "password": "admin123",
            "email": "admin@helppet.ai",
            "full_name": "System Administrator",
            "role": "ADMIN"
        },
        {
            "username": "vet1",
            "password": "password123",
            "email": "vet1@helppet.ai",
            "full_name": "Dr. Sarah Johnson",
            "role": "VET_STAFF"
        },
        {
            "username": "vet2",
            "password": "password123",
            "email": "vet2@helppet.ai",
            "full_name": "Dr. Michael Chen",
            "role": "VET_STAFF"
        },
        {
            "username": "tech1",
            "password": "password123",
            "email": "tech1@helppet.ai",
            "full_name": "Lisa Rodriguez",
            "role": "VET_STAFF"
        },
        {
            "username": "justin",
            "password": "password123",
            "email": "justin@helppet.ai",
            "full_name": "Justin Zollars",
            "role": "ADMIN"
        }
    ]
    
    created_users = []
    skipped_users = []
    
    try:
        for user_data in test_users:
            # Check if user already exists
            result = await session.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": user_data["username"]}
            )
            existing_user = result.fetchone()
            
            if existing_user:
                skipped_users.append(user_data["username"])
                continue
            
            # Create new user
            user_id = str(uuid4())
            hashed_password = get_password_hash(user_data["password"])
            now = datetime.utcnow()
            
            await session.execute(
                text("""
                    INSERT INTO users (id, username, password_hash, email, full_name, role, is_active, created_at, updated_at)
                    VALUES (:id, :username, :password_hash, :email, :full_name, :role, :is_active, :created_at, :updated_at)
                """),
                {
                    "id": user_id,
                    "username": user_data["username"],
                    "password_hash": hashed_password,
                    "email": user_data["email"],
                    "full_name": user_data["full_name"],
                    "role": user_data["role"],
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now
                }
            )
            
            created_users.append({
                "username": user_data["username"],
                "full_name": user_data["full_name"],
                "role": user_data["role"]
            })
        
        await session.commit()
        
        return {
            "message": "Database seeding completed successfully",
            "created_users": created_users,
            "skipped_users": skipped_users,
            "credentials": [
                {"username": user["username"], "password": user["password"]} 
                for user in test_users
            ]
        }
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed users: {str(e)}"
        )


@router.post("/admin/reset-database")
async def reset_database(
    request: AdminPasswordRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    DANGER: Drop all tables and recreate from scratch with fresh migrations
    This will delete ALL data in the database!
    """
    if request.password != "HelpPetSeed2024!":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password"
        )
    
    try:
        # Import here to avoid circular imports
        from ..database_pg import Base
        from sqlalchemy import create_engine, MetaData
        from sqlalchemy.pool import NullPool
        from ..config import settings
        import subprocess
        import sys
        import os
        
        # Get database URL without async prefix for sync operations
        sync_db_url = settings.get_postgresql_sync_url
        
        # Create sync engine for DDL operations
        sync_engine = create_engine(sync_db_url, poolclass=NullPool)
        
        # Drop all tables
        metadata = MetaData()
        metadata.reflect(bind=sync_engine)
        metadata.drop_all(bind=sync_engine)
        
        # Delete alembic version table to reset migration state
        with sync_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
            conn.commit()
        
        sync_engine.dispose()
        
        # Run alembic migrations from scratch
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(backend_dir)
        
        # Initialize alembic and run all migrations
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True, cwd=backend_dir)
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Migration failed: {result.stderr}"
            )
        
        # Seed the database with test users
        await seed_test_users(request, session)
        
        return {
            "message": "Database reset completed successfully",
            "migration_output": result.stdout,
            "warning": "ALL previous data has been permanently deleted!"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database reset failed: {str(e)}"
        )