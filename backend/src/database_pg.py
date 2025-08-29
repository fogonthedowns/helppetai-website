"""
PostgreSQL database configuration and connection management
"""

import logging
from typing import AsyncGenerator
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
            # Create async engine
            self.engine = create_async_engine(
                settings.postgresql_url,
                echo=settings.debug,  # Log SQL queries in debug mode
                pool_size=20,
                max_overflow=0,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            
            # Create session maker
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info(f"Connected to PostgreSQL at {settings.postgresql_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from PostgreSQL database"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Disconnected from PostgreSQL")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if not self.async_session_maker:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database instance
database_pg = DatabasePG()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async for session in database_pg.get_session():
        yield session
