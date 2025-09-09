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
    """Database connectivity health check with detailed connection info"""
    try:
        # Test database connection with multiple queries
        result = await session.execute(text("SELECT 1 as test"))
        test_value = result.scalar()
        
        # Get database version
        version_result = await session.execute(text("SELECT version()"))
        db_version = version_result.scalar()
        
        # Test a simple table count (this will fail if tables don't exist)
        try:
            tables_result = await session.execute(text("""
                SELECT count(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = tables_result.scalar()
        except Exception:
            table_count = "unknown"
        
        return {
            "status": "healthy",
            "database": "postgresql",
            "connection": "active",
            "test_query": f"SELECT 1 returned {test_value}",
            "version": db_version.split('\n')[0] if db_version else "unknown",
            "public_tables": table_count,
            "message": "Database connection is working"
        }
    except Exception as e:
        import traceback
        return {
            "status": "unhealthy",
            "database": "postgresql", 
            "connection": "failed",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "message": "Database connection failed"
        }
