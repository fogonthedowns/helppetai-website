"""
Repository pattern base classes and interfaces.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
from uuid import UUID

T = TypeVar('T')

class Repository(ABC, Generic[T]):
    """Abstract base class for repositories."""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity. All methods are asynchronous."""
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Get all entities with pagination and optional filters."""
    
    @abstractmethod
    async def update(self, entity_id: str, entity: T) -> Optional[T]:
        """Update an existing entity."""
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
