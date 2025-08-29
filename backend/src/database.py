"""
MongoDB database connection and initialization using Beanie ODM.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from .models.mongodb import Item
from .config import settings


logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""
    
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        """Create database connection."""
        try:
            cls.client = AsyncIOMotorClient(settings.mongodb_url)
            
            # Initialize Beanie with the Item model
            await init_beanie(
                database=cls.client[settings.database_name],
                document_models=[Item]
            )
            
            logger.info(f"Connected to MongoDB at {settings.mongodb_url}")
            logger.info(f"Using database: {settings.database_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close database connection."""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")

