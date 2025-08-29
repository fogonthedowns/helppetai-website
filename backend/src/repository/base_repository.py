"""
Base repository class providing common CRUD operations for all MongoDB collections
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any
from beanie import Document, PydanticObjectId
from pymongo.errors import DuplicateKeyError
from datetime import datetime


DocumentType = TypeVar("DocumentType", bound=Document)


class BaseRepository(ABC, Generic[DocumentType]):
    """
    Abstract base repository providing common CRUD operations
    All specific repositories should inherit from this class
    """
    
    def __init__(self, document_class: type[DocumentType]):
        self.document_class = document_class
    
    async def create(self, document: DocumentType) -> DocumentType:
        """
        Create a new document
        
        Args:
            document: Document instance to create
            
        Returns:
            Created document with generated ID
            
        Raises:
            DuplicateKeyError: If document violates unique constraints
        """
        try:
            await document.insert()
            return document
        except DuplicateKeyError as e:
            raise ValueError(f"Duplicate key error: {str(e)}")
    
    async def get_by_id(self, document_id: str | PydanticObjectId) -> Optional[DocumentType]:
        """
        Get document by ID
        
        Args:
            document_id: Document ID (string or ObjectId)
            
        Returns:
            Document if found, None otherwise
        """
        if isinstance(document_id, str):
            try:
                document_id = PydanticObjectId(document_id)
            except Exception:
                return None
        
        return await self.document_class.get(document_id)
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "_id",
        sort_order: int = 1,
        **filters
    ) -> List[DocumentType]:
        """
        Get all documents with pagination and filtering
        
        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort_by: Field to sort by
            sort_order: Sort order (1 for ascending, -1 for descending)
            **filters: Additional filter criteria
            
        Returns:
            List of documents
        """
        # Remove None values from filters
        clean_filters = {k: v for k, v in filters.items() if v is not None}
        
        query = self.document_class.find(clean_filters)
        query = query.skip(skip).limit(limit).sort([(sort_by, sort_order)])
        
        return await query.to_list()
    
    async def update(
        self,
        document_id: str | PydanticObjectId,
        update_data: Dict[str, Any]
    ) -> Optional[DocumentType]:
        """
        Update document by ID
        
        Args:
            document_id: Document ID
            update_data: Fields to update
            
        Returns:
            Updated document if found, None otherwise
        """
        document = await self.get_by_id(document_id)
        if not document:
            return None
        
        # Update timestamp if the field exists
        if hasattr(document, 'updated_at'):
            update_data['updated_at'] = datetime.utcnow()
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(document, field):
                setattr(document, field, value)
        
        await document.save()
        return document
    
    async def delete(self, document_id: str | PydanticObjectId) -> bool:
        """
        Delete document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        document = await self.get_by_id(document_id)
        if not document:
            return False
        
        await document.delete()
        return True
    
    async def count(self, **filters) -> int:
        """
        Count documents matching filters
        
        Args:
            **filters: Filter criteria
            
        Returns:
            Number of matching documents
        """
        clean_filters = {k: v for k, v in filters.items() if v is not None}
        return await self.document_class.find(clean_filters).count()
    
    async def exists(self, **filters) -> bool:
        """
        Check if any documents match the given filters
        
        Args:
            **filters: Filter criteria
            
        Returns:
            True if any documents match, False otherwise
        """
        clean_filters = {k: v for k, v in filters.items() if v is not None}
        document = await self.document_class.find_one(clean_filters)
        return document is not None
    
    async def bulk_create(self, documents: List[DocumentType]) -> List[DocumentType]:
        """
        Create multiple documents in a single operation
        
        Args:
            documents: List of documents to create
            
        Returns:
            List of created documents
        """
        if not documents:
            return []
        
        await self.document_class.insert_many(documents)
        return documents
    
    async def find_by_field(
        self,
        field_name: str,
        field_value: Any,
        limit: int = 100
    ) -> List[DocumentType]:
        """
        Find documents by a specific field value
        
        Args:
            field_name: Name of the field to search
            field_value: Value to search for
            limit: Maximum number of documents to return
            
        Returns:
            List of matching documents
        """
        return await self.document_class.find(
            {field_name: field_value}
        ).limit(limit).to_list()
    
    async def soft_delete(self, document_id: str | PydanticObjectId) -> bool:
        """
        Soft delete document (set is_active to False if field exists)
        
        Args:
            document_id: Document ID
            
        Returns:
            True if soft deleted, False if not found or no is_active field
        """
        document = await self.get_by_id(document_id)
        if not document or not hasattr(document, 'is_active'):
            return False
        
        document.is_active = False
        if hasattr(document, 'updated_at'):
            document.updated_at = datetime.utcnow()
        
        await document.save()
        return True
