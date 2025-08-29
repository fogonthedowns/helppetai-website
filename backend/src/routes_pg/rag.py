"""
RAG endpoints for question answering with source attribution - PostgreSQL version.
Provides RAG (Retrieval-Augmented Generation) functionality using Pinecone and OpenAI.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends

from ..models.base import (
    RAGQueryRequest,
    RAGResponse,
    ErrorResponse
)
from ..services.rag_service import RAGService
from ..auth.jwt_auth_pg import get_current_user
from ..models_pg.user import User

logger = logging.getLogger(__name__)

# Router for RAG endpoints
router = APIRouter()


def get_rag_service() -> RAGService:
    """Dependency to get RAG service."""
    return RAGService()


@router.post(
    "/query",
    response_model=RAGResponse,
    status_code=status.HTTP_200_OK,
    summary="RAG Query",
    description="Process a question using Retrieval-Augmented Generation with source attribution",
    responses={
        200: {
            "description": "Successful RAG response with answer and sources",
            "model": RAGResponse
        },
        400: {
            "description": "Invalid request parameters",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error during RAG processing",
            "model": ErrorResponse
        }
    }
)
async def rag_query(
    request: RAGQueryRequest,
    rag_service: RAGService = Depends(get_rag_service),
    current_user: User = Depends(get_current_user)
) -> RAGResponse:
    """
    Process a question using Retrieval-Augmented Generation (RAG).
    
    This endpoint:
    1. Embeds the user's question using OpenAI embeddings
    2. Applies optional filters (species, symptoms, audience, etc.)
    3. Searches for relevant documents in Pinecone vector database
    4. Retrieves full document content from DynamoDB
    5. Generates a comprehensive answer using OpenAI GPT-4o-mini (low temperature for consistency)
    6. Returns the answer with properly attributed sources
    
    Available filters:
    - doc_type: Filter by document type
    - species: Filter by species (e.g., ["dog", "cat"])
    - symptoms: Filter by symptoms/conditions
    - medical_system: Filter by medical system
    - audience: Filter by audience type ("expert" or "pet-owner")
    - source_id: Filter by specific source ID
    - chunk_index: Filter by specific chunk index
    - version: Filter by classification version
    
    Args:
        request: RAG query request containing the question and parameters
        rag_service: RAG service dependency for processing
        current_user: Authenticated user (required for access)
        
    Returns:
        RAGResponse: AI-generated answer with source references and metadata
        
    Raises:
        HTTPException: If the RAG processing fails or configuration is invalid
    """
    try:
        logger.info(f"Processing RAG query for user {current_user.username}: {request.question[:100]}...")
        
        # Validate that required configuration is present
        if not hasattr(rag_service, '_validate_config'):
            # Add basic validation here if needed
            pass
        
        # Process the RAG query
        response = await rag_service.process_rag_query(request)
        
        logger.info(f"RAG query completed successfully with {len(response.sources)} sources")
        return response
        
    except ValueError as e:
        # Configuration or validation errors
        logger.error(f"RAG configuration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG service configuration error: {str(e)}"
        )
    except Exception as e:
        # General processing errors
        logger.error(f"RAG processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing RAG query: {str(e)}"
        )
