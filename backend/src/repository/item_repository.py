"""
Item repository implementation using MongoDB/Beanie.
"""

import logging
from datetime import datetime
from typing import List, Optional
from beanie import PydanticObjectId
from ..models.mongodb import Item
from .base import Repository


class ItemRepository(Repository[Item]):
    """MongoDB implementation of Item repository."""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
    
    async def create(self, entity: Item) -> Item:
        """Create a new item."""
        try:
            entity.created_at = datetime.utcnow()
            entity.updated_at = datetime.utcnow()
            await entity.insert()
            self._logger.info(f"Created item with ID: {entity.id}")
            return entity
        except Exception as e:
            self._logger.error(f"Error creating item: {e}")
            raise
    
    async def get_by_id(self, entity_id: str) -> Optional[Item]:
        """Get item by ID."""
        try:
            if not PydanticObjectId.is_valid(entity_id):
                return None
            item = await Item.get(PydanticObjectId(entity_id))
            return item
        except Exception as e:
            self._logger.error(f"Error getting item by ID {entity_id}: {e}")
            return None
    
    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[Item]:
        """Get all items with pagination and optional filters."""
        try:
            query = Item.find()
            
            # Apply filters
            if "category" in filters and filters["category"] is not None:
                query = query.find(Item.category == filters["category"])
            
            if "is_active" in filters and filters["is_active"] is not None:
                query = query.find(Item.is_active == filters["is_active"])
            
            # Apply pagination
            items = await query.skip(skip).limit(limit).to_list()
            return items
            
        except Exception as e:
            self._logger.error(f"Error getting items: {e}")
            return []
    
    async def update(self, entity_id: str, update_data: dict) -> Optional[Item]:
        """Update an existing item."""
        try:
            if not PydanticObjectId.is_valid(entity_id):
                return None
                
            item = await Item.get(PydanticObjectId(entity_id))
            if not item:
                return None
            
            # Update only provided fields
            for field, value in update_data.items():
                if hasattr(item, field) and value is not None:
                    setattr(item, field, value)
            
            item.updated_at = datetime.utcnow()
            await item.save()
            
            self._logger.info(f"Updated item with ID: {entity_id}")
            return item
            
        except Exception as e:
            self._logger.error(f"Error updating item {entity_id}: {e}")
            return None
    
    async def delete(self, entity_id: str) -> bool:
        """Delete item by ID."""
        try:
            if not PydanticObjectId.is_valid(entity_id):
                return False
                
            item = await Item.get(PydanticObjectId(entity_id))
            if not item:
                return False
            
            await item.delete()
            self._logger.info(f"Deleted item with ID: {entity_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Error deleting item {entity_id}: {e}")
            return False
