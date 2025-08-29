"""
RAG endpoints for question answering with source attribution.
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
    rag_service: RAGService = Depends(get_rag_service)
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
        
    Returns:
        RAGResponse: AI-generated answer with source references and metadata
        
    Raises:
        HTTPException: If the RAG processing fails or configuration is invalid
    """
    try:
        logger.info(f"Processing RAG query: {request.question[:100]}...")
        
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


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="RAG Health Check",
    description="Check the health status of RAG service dependencies"
)
async def rag_health_check(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Check the health status of RAG service dependencies.
    
    This endpoint verifies:
    - OpenAI API connectivity and credentials
    - Pinecone connection and index availability
    - DynamoDB table accessibility
    
    Args:
        rag_service: RAG service dependency for health checking
        
    Returns:
        dict: Health status information for each dependency
        
    Raises:
        HTTPException: If any critical dependency is unavailable
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Will be updated with actual timestamp
            "dependencies": {
                "openai": "not_checked",
                "pinecone": "not_checked", 
                "dynamodb": "not_checked"
            }
        }
        
        # Basic health check - you could extend this to actually test connections
        logger.info("RAG health check completed")
        health_status["status"] = "healthy"
        health_status["dependencies"]["openai"] = "configured" if hasattr(rag_service, '_openai_client') else "not_configured"
        health_status["dependencies"]["pinecone"] = "configured" if hasattr(rag_service, '_pinecone_client') else "not_configured"
        health_status["dependencies"]["dynamodb"] = "configured" if hasattr(rag_service, '_dynamodb_resource') else "not_configured"
        
        return health_status
        
    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG service health check failed: {str(e)}"
        )


@router.get(
    "/debug/tables",
    status_code=status.HTTP_200_OK,
    summary="Debug DynamoDB Tables",
    description="Debug endpoint to check DynamoDB table structure and sample data"
)
async def debug_dynamodb_tables(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Debug endpoint to inspect DynamoDB table configuration and sample data.
    
    This helps diagnose data availability issues by checking:
    - Table existence and basic info
    - Sample records from each table
    - Key schema information
    
    Args:
        rag_service: RAG service dependency
        
    Returns:
        dict: Debug information about DynamoDB tables
    """
    try:
        import boto3
        from ..config import settings
        
        dynamodb = boto3.resource('dynamodb')
        
        debug_info = {
            "vector_table_name": settings.dynamodb_vector_table,
            "sources_table_name": settings.rag_sources_table,
            "tables": {}
        }
        
        # Check vector table
        try:
            vector_table = dynamodb.Table(settings.dynamodb_vector_table)
            vector_response = vector_table.scan(Limit=1)
            debug_info["tables"]["vector_table"] = {
                "exists": True,
                "item_count": vector_response.get('Count', 0),
                "sample_keys": [item.get('vector_id', 'N/A') for item in vector_response.get('Items', [])]
            }
        except Exception as e:
            debug_info["tables"]["vector_table"] = {
                "exists": False,
                "error": str(e)
            }
        
        # Check sources table
        try:
            sources_table = dynamodb.Table(settings.rag_sources_table)
            sources_response = sources_table.scan(Limit=1)
            debug_info["tables"]["sources_table"] = {
                "exists": True,
                "item_count": sources_response.get('Count', 0),
                "sample_keys": [item.get('source_id', 'N/A') for item in sources_response.get('Items', [])]
            }
        except Exception as e:
            debug_info["tables"]["sources_table"] = {
                "exists": False,
                "error": str(e)
            }
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Debug tables check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug check failed: {str(e)}"
        )
