"""
PostgreSQL routes package initialization.
Imports and configures all route modules with consistent API versioning.
"""

from fastapi import APIRouter
from .health import router as health_router
from .auth import router as auth_router
from .practices import router as practices_router
from .pet_owners import router as pet_owners_router
from .associations import router as associations_router
from .pets import router as pets_router
from .medical_records import router as medical_records_router
from .rag import router as rag_router
from .visit_transcripts import router as visit_transcripts_router
from .appointments import router as appointments_router
from .dashboard import router as dashboard_router
from .upload import router as upload_router
from .webhook import router as webhook_router
from .contact_form import router as contact_form_router
from .scheduling import router as scheduling_router


# Create main router
router = APIRouter()

# Health check (outside API versioning)
router.include_router(health_router, tags=["health"])

# Authentication (versioned for consistency)
router.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])

# API v1 endpoints - specific routers first to avoid conflicts
router.include_router(practices_router, prefix="/api/v1/practices", tags=["veterinary-practices"])
router.include_router(pet_owners_router, prefix="/api/v1/pet_owners", tags=["pet-owners"])
router.include_router(associations_router, prefix="/api/v1/associations", tags=["pet-owner-practice-associations"])
router.include_router(pets_router, tags=["pets"])  # pets router already has /api/v1/pets prefix
router.include_router(medical_records_router, tags=["medical-records"])  # medical records router already has prefix
router.include_router(visit_transcripts_router, tags=["visit-transcripts"])  # visit transcripts router already has prefix
router.include_router(appointments_router, tags=["appointments"])  # appointments router already has prefix
router.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["vet-dashboard"])

router.include_router(upload_router, prefix="/api/v1/upload", tags=["file-upload"])
router.include_router(rag_router, prefix="/api/v1/rag", tags=["rag-search"])
router.include_router(webhook_router, prefix="/api/v1/webhook", tags=["webhook"])
router.include_router(contact_form_router, prefix="/api/v1/vets", tags=["veterinary-contact"])
router.include_router(scheduling_router, tags=["scheduling"])  # scheduling router already has prefix

__all__ = ["router"]
