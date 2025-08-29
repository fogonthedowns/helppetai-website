"""
Health check routes for PostgreSQL version
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..database_pg import get_db_session

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "database": "postgresql",
        "message": "HelpPet API is running with PostgreSQL"
    }


@router.get("/health/db")
async def database_health_check(session: AsyncSession = Depends(get_db_session)):
    """Database connectivity health check"""
    try:
        # Test database connection
        result = await session.execute(text("SELECT 1"))
        result.scalar()
        
        return {
            "status": "healthy",
            "database": "postgresql",
            "connection": "active",
            "message": "Database connection is working"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "postgresql", 
            "connection": "failed",
            "error": str(e)
        }
