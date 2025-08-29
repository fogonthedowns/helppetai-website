"""
Routes package initialization.
Imports and configures all route modules with consistent API versioning.
"""

from fastapi import APIRouter
from .health import router as health_router
from .auth import router as auth_router
from .practices import router as practices_router
from .pet_owners import router as pet_owners_router
from .rag import router as rag_router
from .api import router as api_router

# Create main router
router = APIRouter()

# Health check (outside API versioning)
router.include_router(health_router, tags=["health"])

# Authentication (versioned for consistency)
router.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])

# API v1 endpoints - specific routers first to avoid conflicts
router.include_router(practices_router, prefix="/api/v1/practices", tags=["veterinary-practices"])
router.include_router(pet_owners_router, prefix="/api/v1/pet_owners", tags=["pet-owners"])
router.include_router(rag_router, prefix="/api/v1/rag", tags=["rag-search"])
router.include_router(api_router, prefix="/api/v1", tags=["general"])

__all__ = ["router"]
