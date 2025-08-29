"""
Routes package initialization.
Imports and configures all route modules.
"""

from fastapi import APIRouter
from .health import router as health_router
from .api import router as api_router
from .rag import router as rag_router
from .auth import router as auth_router

# Create main router
router = APIRouter()

# Include all route modules
router.include_router(health_router, tags=["health"])
router.include_router(api_router, prefix="/api/v1", tags=["api"])
router.include_router(rag_router, prefix="/api/v1/rag", tags=["rag"])
router.include_router(auth_router, tags=["auth"])

__all__ = ["router"]
