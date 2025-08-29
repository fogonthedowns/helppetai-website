"""
Base Pydantic models and schemas for the FastAPI application.
Defines common request/response models and validation schemas.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model for API endpoints."""
    
    success: bool = Field(default=True, description="Indicates if the request was successful")
    message: str = Field(default="Success", description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseResponse):
    """Error response model for API endpoints."""
    
    success: bool = Field(default=False)
    message: str = Field(description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code for debugging")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class HealthResponse(BaseResponse):
    """Health check response model."""
    
    status: str = Field(description="Application status")
    version: str = Field(description="Application version")
    uptime: Optional[float] = Field(default=None, description="Application uptime in seconds")
    environment: str = Field(description="Current environment")
    

class ItemBase(BaseModel):
    """Base model for items."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(default=None, max_length=500, description="Item description")
    category: str = Field(..., min_length=1, max_length=50, description="Item category")
    tags: List[str] = Field(default_factory=list, description="Item tags")
    is_active: bool = Field(default=True, description="Whether the item is active")


class ItemCreate(ItemBase):
    """Model for creating new items."""
    pass


class ItemUpdate(BaseModel):
    """Model for updating existing items."""
    
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(default=None, max_length=500, description="Item description") 
    category: Optional[str] = Field(default=None, min_length=1, max_length=50, description="Item category")
    tags: Optional[List[str]] = Field(default=None, description="Item tags")
    is_active: Optional[bool] = Field(default=None, description="Whether the item is active")


class ItemResponse(ItemBase):
    """Model for item responses."""
    
    id: str = Field(..., description="Item ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# RAG Models for question answering with source attribution

class RAGQueryRequest(BaseModel):
    """Request model for RAG query endpoint."""
    
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    max_results: int = Field(default=5, ge=1, le=10, description="Maximum number of search results to retrieve")
    
    # Filtering options (matching query_pinecone.py)
    doc_type: Optional[str] = Field(default=None, description="Filter by document type")
    species: Optional[List[str]] = Field(default=None, description="Filter by species (e.g., ['dog', 'cat'])")
    symptoms: Optional[List[str]] = Field(default=None, description="Filter by symptoms/conditions")
    medical_system: Optional[str] = Field(default=None, description="Filter by medical system")
    audience: Optional[str] = Field(default=None, description="Filter by audience type", pattern="^(expert|pet-owner)$")
    source_id: Optional[str] = Field(default=None, description="Filter by specific source ID")
    chunk_index: Optional[int] = Field(default=None, description="Filter by specific chunk index")
    version: Optional[str] = Field(default=None, description="Filter by classification version")


class SourceReference(BaseModel):
    """Model for source reference in RAG responses."""
    
    id: str = Field(..., description="Document ID from Pinecone")
    title: str = Field(..., description="Document title")
    url: Optional[str] = Field(default=None, description="Source URL")
    chunk_info: str = Field(..., description="Chunk information (e.g., 'Chunk: #8.0')")
    relevance_score: float = Field(..., description="Similarity score from Pinecone")
    audience: Optional[str] = Field(default=None, description="Target audience (e.g., 'pet-owner')")
    authority_level: Optional[str] = Field(default=None, description="Authority level (e.g., 'expert')")
    publisher: Optional[str] = Field(default=None, description="Publisher name")
    publication_year: Optional[int] = Field(default=None, description="Publication year")
    species: Optional[List[str]] = Field(default=None, description="Related species")
    symptoms: Optional[List[str]] = Field(default=None, description="Related symptoms/tags")


class RAGResponse(BaseModel):
    """Response model for RAG query endpoint."""
    
    answer: str = Field(..., description="AI-generated response to the user's question")
    sources: List[SourceReference] = Field(..., description="List of source documents used")
    query_metadata: Dict[str, Any] = Field(..., description="Query processing metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
