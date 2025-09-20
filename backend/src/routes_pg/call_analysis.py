"""API routes for call analysis operations."""

from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
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


@router.post("/webhook")
async def retell_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Webhook endpoint for Retell AI call events.
    Receives call_started, call_ended, and call_analyzed events.
    """
    try:
        # Parse the webhook payload
        payload = await request.json()
        event_type = payload.get("event")
        call_data = payload.get("call", {})
        
        if not call_data:
            print("❌ No call data in webhook payload")
            return {"status": "error", "message": "No call data provided"}
        
        agent_id = call_data.get("agent_id")
        if not agent_id:
            print("❌ No agent_id in webhook payload")
            return {"status": "error", "message": "No agent_id provided"}
        
        call_id = call_data.get("call_id")
        if not call_id:
            print("❌ No call_id in webhook payload")
            return {"status": "error", "message": "No call_id provided"}
        
        print(f"🔔 Webhook received: {event_type} for agent {agent_id}, call {call_id}")
        
        # Find the practice associated with this agent
        voice_config_repo = VoiceConfigRepository(session)
        voice_config = await voice_config_repo.get_by_agent_id(agent_id)
        
        if not voice_config:
            print(f"❌ No voice config found for agent {agent_id}")
            return {"status": "error", "message": f"Agent {agent_id} not found"}
        
        practice_id = voice_config.practice_id
        print(f"✅ Found practice {practice_id} for agent {agent_id}")
        
        # Save the call to database
        call_record_repo = CallRecordRepository(session)
        
        # Convert webhook data to our format
        api_data = {
            "call_id": call_id,
            "agent_id": call_data.get("agent_id"),
            "recording_url": call_data.get("recording_url"),
            "start_timestamp": call_data.get("start_timestamp"),
            "end_timestamp": call_data.get("end_timestamp"),
            "from_number": call_data.get("from_number"),
            "to_number": call_data.get("to_number"),
            "duration_ms": call_data.get("duration_ms"),
            "call_status": call_data.get("call_status"),
            "disconnect_reason": call_data.get("disconnection_reason"),
            "call_analysis": call_data.get("call_analysis")
        }
        
        # Get or create call record
        existing_record = await call_record_repo.get_by_call_id(call_id)
        if existing_record:
            call_record = existing_record
        else:
            from ..models_pg.call_record import CallRecord
            call_record = CallRecord(practice_id=practice_id, call_id=call_id)
        
        # Update the record with webhook data
        call_record.update_from_api_data(api_data)
        
        # Save to database
        await call_record_repo.create_or_update(call_record)
        await session.commit()
        
        print(f"✅ Saved call {call_id} for practice {practice_id} (event: {event_type})")
        
        return {
            "status": "success", 
            "message": f"Call {call_id} processed successfully",
            "event": event_type,
            "call_id": call_id
        }
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return 200 even on error to prevent retries for non-recoverable errors
        return {"status": "error", "message": str(e)}
