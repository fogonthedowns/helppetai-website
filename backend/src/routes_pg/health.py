"""
Health check routes for PostgreSQL version
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import time
import os

from ..database_pg import get_db_session
from ..config import settings

router = APIRouter()


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_db_session)):
    """Enhanced health check with version information"""
    try:
        # Get Alembic migration version
        try:
            migration_result = await session.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"))
            current_migration = migration_result.scalar()
        except Exception:
            current_migration = "unknown"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            "database": "postgresql",
            "migration_version": current_migration,
            "build_info": {
                "version": settings.app_version,
                "environment": settings.environment,
                "build_timestamp": os.getenv("BUILD_TIMESTAMP", "unknown")
            },
            "message": "HelpPet API is running with PostgreSQL"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            "database": "postgresql",
            "error": str(e),
            "message": "Health check failed"
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
        
        # Get migration version and history
        try:
            migration_result = await session.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"))
            current_migration = migration_result.scalar()
            
            # Check if contact_forms table exists (our newest table)
            contact_table_result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'contact_forms'
                )
            """))
            contact_table_exists = contact_table_result.scalar()
            
        except Exception as e:
            current_migration = "unknown"
            contact_table_exists = False
        
        return {
            "status": "healthy",
            "database": "postgresql",
            "connection": "active",
            "test_query": f"SELECT 1 returned {test_value}",
            "version": db_version.split('\n')[0] if db_version else "unknown",
            "public_tables": table_count,
            "migration_info": {
                "current_version": current_migration,
                "contact_forms_table_exists": contact_table_exists,
                "latest_migration": "a1b2c3d4e5f6_add_contact_forms_table"
            },
            "app_info": {
                "version": settings.app_version,
                "environment": settings.environment,
                "name": settings.app_name
            },
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
