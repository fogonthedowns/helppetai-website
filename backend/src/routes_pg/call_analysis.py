"""API routes for call analysis operations."""

from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database_pg import get_db_session
from ..repositories_pg.voice_config_repository import VoiceConfigRepository
from ..repositories_pg.call_record_repository import CallRecordRepository
from ..services.call_analysis_service import CallAnalysisService
from ..auth.jwt_auth_pg import get_current_user
from ..models_pg.user import User
from ..schemas.call_analysis import CallListResponse, CallDetailResponse, VoiceConfigResponse
from ..models_pg.voice_config import VoiceConfig
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/call-analysis", tags=["Call Analysis"])


class CreateVoiceConfigRequest(BaseModel):
    """Request model for creating voice configuration."""
    agent_id: str
    timezone: str = "UTC"
    metadata: Dict[str, Any] = {}


def get_call_analysis_service(session: AsyncSession = Depends(get_db_session)) -> CallAnalysisService:
    """Dependency to get call analysis service."""
    voice_config_repo = VoiceConfigRepository(session)
    call_record_repo = CallRecordRepository(session)
    return CallAnalysisService(voice_config_repo, call_record_repo)


@router.get("/practice/{practice_id}/calls", response_model=CallListResponse)
async def get_practice_calls(
    practice_id: UUID,
    limit: int = Query(default=10, ge=1, le=50, description="Number of calls to retrieve"),
    offset: int = Query(default=0, ge=0, description="Number of calls to skip for pagination"),
    current_user: User = Depends(get_current_user),
    call_service: CallAnalysisService = Depends(get_call_analysis_service)
) -> CallListResponse:
    """
    Get call analysis data for a practice.
    
    Returns paginated call analysis data including:
    - call_id
    - recording_url
    - start_timestamp
    - end_timestamp
    - call_analysis (call_successful, call_summary, user_sentiment, in_voicemail, custom_analysis_data)
    """
    try:
        # TODO: Add authorization check to ensure user has access to this practice
        # For now, we'll rely on the voice config existing as basic validation
        
        calls = await call_service.get_call_analysis_for_practice(
            practice_id=practice_id,
            limit=limit,
            offset=offset
        )
        
        return CallListResponse(
            practice_id=str(practice_id),
            calls=calls,
            pagination={
                "limit": limit,
                "offset": offset,
                "count": len(calls),
                "has_more": len(calls) == limit,  # Assume more if we got full page
                "total_count": None  # We don't have total count from Retell API
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving calls: {str(e)}")


@router.get("/practice/{practice_id}/calls/{call_id}", response_model=CallDetailResponse)
async def get_call_detail(
    practice_id: UUID,
    call_id: str,
    current_user: User = Depends(get_current_user),
    call_service: CallAnalysisService = Depends(get_call_analysis_service)
) -> CallDetailResponse:
    """
    Get detailed information for a specific call.
    
    Returns detailed call information including full call analysis and metadata.
    """
    try:
        # TODO: Add authorization check to ensure user has access to this practice
        
        call_detail = await call_service.get_call_detail(
            practice_id=practice_id,
            call_id=call_id
        )
        
        return CallDetailResponse(
            practice_id=str(practice_id),
            call=call_detail
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving call detail: {str(e)}")


@router.get("/practice/{practice_id}/voice-config", response_model=VoiceConfigResponse)
async def get_voice_config(
    practice_id: UUID,
    current_user: User = Depends(get_current_user),
    call_service: CallAnalysisService = Depends(get_call_analysis_service)
) -> VoiceConfigResponse:
    """Get voice configuration for a practice."""
    try:
        # Get the voice config through the repository
        voice_config_repo = VoiceConfigRepository(call_service.voice_config_repo.session)
        voice_config = await voice_config_repo.get_by_practice_id(practice_id)
        
        if not voice_config:
            raise HTTPException(status_code=404, detail="Voice configuration not found")
        
        return VoiceConfigResponse(
            practice_id=str(practice_id),
            agent_id=voice_config.agent_id,
            timezone=voice_config.timezone,
            metadata=voice_config.config_metadata,
            is_active=voice_config.is_active,
            created_at=voice_config.created_at,
            updated_at=voice_config.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving voice config: {str(e)}")


@router.post("/practice/{practice_id}/voice-config", response_model=VoiceConfigResponse)
async def create_voice_config(
    practice_id: UUID,
    request: CreateVoiceConfigRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> VoiceConfigResponse:
    """Create voice configuration for a practice."""
    try:
        voice_config_repo = VoiceConfigRepository(session)
        
        # Check if config already exists
        existing_config = await voice_config_repo.get_by_practice_id(practice_id)
        if existing_config:
            raise HTTPException(status_code=400, detail="Voice configuration already exists for this practice")
        
        # Create new voice config
        voice_config = VoiceConfig(
            practice_id=practice_id,
            agent_id=request.agent_id,
            timezone=request.timezone,
            config_metadata=request.metadata
        )
        
        created_config = await voice_config_repo.create(voice_config)
        await session.commit()
        
        return VoiceConfigResponse(
            practice_id=str(practice_id),
            agent_id=created_config.agent_id,
            timezone=created_config.timezone,
            metadata=created_config.config_metadata,
            is_active=created_config.is_active,
            created_at=created_config.created_at,
            updated_at=created_config.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating voice config: {str(e)}")
