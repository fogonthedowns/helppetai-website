"""
MongoDB database connection and initialization using Beanie ODM.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from .models.mongodb import Item
from .models.user import User
from .models.practice import VeterinaryPractice
from .models.pet_owner import PetOwner
from .models.pet import Pet
from .models.associations import PetPracticeAssociation
from .models.medical_record import MedicalRecord
from .models.visit import Visit
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
            
            # Initialize Beanie with all document models
            await init_beanie(
                database=cls.client[settings.database_name],
                document_models=[
                    Item,
                    User,
                    VeterinaryPractice,
                    PetOwner,
                    Pet,
                    PetPracticeAssociation,
                    MedicalRecord,
                    Visit
                ]
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

