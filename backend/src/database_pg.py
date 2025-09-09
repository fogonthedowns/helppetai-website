"""
PostgreSQL database configuration and connection management
"""

import asyncio
import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
try:
    from .config import settings
except ImportError:
    # Handle case when imported from alembic
    from config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    pass


class DatabasePG:
    """PostgreSQL database connection manager"""
    
    def __init__(self):
        self.engine = None
        self.async_session_maker = None
    
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            # Create async engine - use RDS if configured
            database_url = settings.get_postgresql_url
            self.engine = create_async_engine(
                database_url,
                echo=settings.debug,  # Log SQL queries in debug mode
                pool_size=20,
                max_overflow=0,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"server_settings": {"application_name": "helppet_api"}},
            )
            
            # Create session maker
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Log connection without exposing credentials
            if settings.rds_hostname:
                logger.info(f"Connected to PostgreSQL RDS at {settings.rds_hostname}:{settings.rds_port}/{settings.rds_db_name}")
            else:
                logger.info("Connected to PostgreSQL (local development)")
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from PostgreSQL database"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Disconnected from PostgreSQL")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with connection resilience"""
        if not self.async_session_maker:
            logger.error("Database session maker not initialized - attempting reconnection")
            try:
                await self.connect()
            except Exception as e:
                logger.error(f"Failed to reconnect to database: {e}")
                raise RuntimeError(f"Database not connected and reconnection failed: {e}")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with self.async_session_maker() as session:
                    # Test the connection with a simple query
                    await session.execute(text("SELECT 1"))
                    try:
                        yield session
                    except Exception:
                        await session.rollback()
                        raise
                    finally:
                        await session.close()
                    return
            except Exception as e:
                logger.warning(f"Database session attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    try:
                        await self.connect()  # Try to reconnect
                    except Exception as reconnect_error:
                        logger.error(f"Reconnection attempt {attempt + 1} failed: {reconnect_error}")
                else:
                    logger.error(f"All database session attempts failed: {e}")
                    raise


# Global database instance
database_pg = DatabasePG()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async for session in database_pg.get_session():
        yield session
