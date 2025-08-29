"""
MongoDB models using Beanie ODM.
"""

from datetime import datetime
from typing import List, Optional
from beanie import Document, Indexed
from pydantic import Field
from pymongo import IndexModel


class Item(Document):
    """Item document model for MongoDB."""
    
    name: Indexed(str) = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(default=None, max_length=500, description="Item description")
    category: Indexed(str) = Field(..., min_length=1, max_length=50, description="Item category")
    tags: List[str] = Field(default_factory=list, description="Item tags")
    is_active: bool = Field(default=True, description="Whether the item is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Settings:
        name = "items"
        indexes = [
            IndexModel([("name", 1)]),
            IndexModel([("category", 1)]),
            IndexModel([("is_active", 1)]),
            IndexModel([("created_at", -1)]),
        ]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
