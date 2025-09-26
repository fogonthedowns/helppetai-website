"""
Voice Agent routes for managing Retell voice agents
"""

from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
import logging

from ..database_pg import get_db_session
from ..models_pg.voice_config import VoiceConfig
from ..repositories_pg.practice_repository import PracticeRepository
from ..auth.jwt_auth_pg import get_current_user
from ..models_pg.user import User
from ..services.retell_service import retell_service, load_helppetai_config

logger = logging.getLogger(__name__)
router = APIRouter()


class VoiceAgentCreate(BaseModel):
    timezone: str = "US/Pacific"
    metadata: Optional[dict] = {}


class VoiceAgentUpdate(BaseModel):
    timezone: Optional[str] = None
    metadata: Optional[dict] = None
    is_active: Optional[bool] = None


class VoiceAgentPersonalityUpdate(BaseModel):
    personality_text: str


class VoiceAgentResponse(BaseModel):
    id: str
    practice_id: str
    agent_id: str
    timezone: str
    metadata: dict
    is_active: bool
    created_at: str
    updated_at: str


@router.get("/{practice_id}/voice-agent", response_model=VoiceAgentResponse)
async def get_voice_agent(
    practice_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> VoiceAgentResponse:
    """Get voice agent for a specific practice"""
    
    query = select(VoiceConfig).where(
        VoiceConfig.practice_id == UUID(practice_id),
        VoiceConfig.is_active == True
    )
    
    result = await session.execute(query)
    voice_config = result.scalars().first()
    
    if not voice_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No voice agent found for practice {practice_id}"
        )
    
    return VoiceAgentResponse(
        id=str(voice_config.id),
        practice_id=str(voice_config.practice_id),
        agent_id=voice_config.agent_id,
        timezone=voice_config.timezone,
        metadata=voice_config.config_metadata or {},
        is_active=voice_config.is_active,
        created_at=voice_config.created_at.isoformat(),
        updated_at=voice_config.updated_at.isoformat()
    )


@router.post("/{practice_id}/voice-agent", response_model=VoiceAgentResponse)
async def create_voice_agent(
    practice_id: str,
    agent_data: VoiceAgentCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> VoiceAgentResponse:
    """Create/register a new voice agent for the practice"""
    
    # Get practice information for agent naming
    practice_repo = PracticeRepository(session)
    practice = await practice_repo.get_by_id(practice_id)
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with ID {practice_id} not found"
        )
    
    # Check if voice agent already exists for this practice
    existing_query = select(VoiceConfig).where(VoiceConfig.practice_id == UUID(practice_id))
    existing_result = await session.execute(existing_query)
    existing_voice_config = existing_result.scalar_one_or_none()
    
    if existing_voice_config:
        logger.info(f"🔄 Voice agent already exists for practice {practice_id}, returning existing agent")
        return VoiceAgentResponse(
            id=str(existing_voice_config.id),
            practice_id=str(existing_voice_config.practice_id),
            agent_id=existing_voice_config.agent_id,
            timezone=existing_voice_config.timezone,
            metadata=existing_voice_config.config_metadata or {},
            is_active=existing_voice_config.is_active,
            created_at=existing_voice_config.created_at.isoformat(),
            updated_at=existing_voice_config.updated_at.isoformat()
        )
    
    # Create simple agent config (no config file needed!)
    practice_agent_name = f"{practice.name} - HelpPetAI"
    agent_config = {
        "agent_name": practice_agent_name,
        "voice_id": "11labs-Adrian",
        "language": "en-US",
        "webhook_url": "https://api.helppet.ai/api/v1/retell/webhook",
        "max_call_duration_ms": 900000,
        "interruption_sensitivity": 1
    }
    
    logger.info(f"🏥 Creating voice agent for practice: {practice.name} (ID: {practice_id})")
    
    # Create agent on Retell using working conversation flow
    agent_id = await retell_service.create_agent(
        agent_config, 
        practice_id=practice_id, 
        timezone=agent_data.timezone
    )
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent on Retell"
        )
    
    # Create voice config in database
    voice_config = VoiceConfig(
        practice_id=UUID(practice_id),
        agent_id=agent_id,
        timezone=agent_data.timezone,
        config_metadata=agent_data.metadata or {},
        is_active=True
    )
    
    try:
        session.add(voice_config)
        await session.commit()
        await session.refresh(voice_config)
    except IntegrityError as e:
        await session.rollback()
        if "unique_practice_voice_config" in str(e):
            # Race condition - another request created the agent
            logger.info(f"🔄 Race condition detected, voice agent was created by another request for practice {practice_id}")
            existing_result = await session.execute(existing_query)
            existing_voice_config = existing_result.scalar_one()
            return VoiceAgentResponse(
                id=str(existing_voice_config.id),
                practice_id=str(existing_voice_config.practice_id),
                agent_id=existing_voice_config.agent_id,
                timezone=existing_voice_config.timezone,
                metadata=existing_voice_config.config_metadata or {},
                is_active=existing_voice_config.is_active,
                created_at=existing_voice_config.created_at.isoformat(),
                updated_at=existing_voice_config.updated_at.isoformat()
            )
        else:
            logger.error(f"Database integrity error creating voice agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create voice agent due to database constraint violation"
            )
    
    logger.info(f"✅ Created voice agent {agent_id} for practice {practice_id}")
    
    return VoiceAgentResponse(
        id=str(voice_config.id),
        practice_id=str(voice_config.practice_id),
        agent_id=voice_config.agent_id,
        timezone=voice_config.timezone,
        metadata=voice_config.config_metadata or {},
        is_active=voice_config.is_active,
        created_at=voice_config.created_at.isoformat(),
        updated_at=voice_config.updated_at.isoformat()
    )


@router.put("/{practice_id}/voice-agent", response_model=VoiceAgentResponse)
async def update_voice_agent(
    practice_id: str,
    agent_data: VoiceAgentUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> VoiceAgentResponse:
    """Alternative create/update endpoint for voice agent"""
    
    # Get practice information for agent naming
    practice_repo = PracticeRepository(session)
    practice = await practice_repo.get_by_id(practice_id)
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with ID {practice_id} not found"
        )
    
    # Check if voice agent already exists for this practice
    existing_query = select(VoiceConfig).where(VoiceConfig.practice_id == UUID(practice_id))
    existing_result = await session.execute(existing_query)
    existing_voice_config = existing_result.scalar_one_or_none()
    
    if existing_voice_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Voice agent already exists for practice {practice_id}. Use PUT to update or DELETE to remove the existing agent first."
        )
    
    # Create simple agent config (no config file needed!)
    practice_agent_name = f"{practice.name} - HelpPetAI"
    agent_config = {
        "agent_name": practice_agent_name,
        "voice_id": "11labs-Adrian",
        "language": "en-US",
        "webhook_url": "https://api.helppet.ai/api/v1/retell/webhook",
        "max_call_duration_ms": 900000,
        "interruption_sensitivity": 1
    }
    
    logger.info(f"🏥 Creating voice agent for practice: {practice.name} (ID: {practice_id})")
    
    # Create agent on Retell using working conversation flow
    agent_id = await retell_service.create_agent(
        agent_config, 
        practice_id=practice_id, 
        timezone=agent_data.timezone
    )
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent on Retell"
        )
    
    # Create voice config in database
    voice_config = VoiceConfig(
        practice_id=UUID(practice_id),
        agent_id=agent_id,
        timezone=agent_data.timezone,
        config_metadata=agent_data.metadata or {},
        is_active=True
    )
    
    try:
        session.add(voice_config)
        await session.commit()
        await session.refresh(voice_config)
    except IntegrityError as e:
        await session.rollback()
        if "unique_practice_voice_config" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Voice agent already exists for practice {practice_id}. Use PUT to update or DELETE to remove the existing agent first."
            )
        else:
            logger.error(f"Database integrity error creating voice agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create voice agent due to database constraint violation"
            )
    
    logger.info(f"✅ Created voice agent {agent_id} for practice {practice_id}")
    
    return VoiceAgentResponse(
        id=str(voice_config.id),
        practice_id=str(voice_config.practice_id),
        agent_id=voice_config.agent_id,
        timezone=voice_config.timezone,
        metadata=voice_config.config_metadata or {},
        is_active=voice_config.is_active,
        created_at=voice_config.created_at.isoformat(),
        updated_at=voice_config.updated_at.isoformat()
    )


@router.delete("/{practice_id}/voice-agent", response_model=VoiceAgentResponse)
async def delete_voice_agent(
    practice_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> VoiceAgentResponse:
    """Soft delete a voice agent for a practice (set is_active to False)"""
    
    # Get existing voice config for the practice
    result = await session.execute(
        select(VoiceConfig).where(VoiceConfig.practice_id == UUID(practice_id))
    )
    voice_config = result.scalar_one_or_none()
    
    if not voice_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No voice agent found for practice {practice_id}"
        )
    
    # Soft delete - set is_active to False
    await session.execute(
        update(VoiceConfig)
        .where(VoiceConfig.practice_id == UUID(practice_id))
        .values(is_active=False)
    )
    await session.commit()
    await session.refresh(voice_config)
    
    logger.info(f"✅ Soft deleted voice agent {voice_config.agent_id} for practice {practice_id}")
    
    return VoiceAgentResponse(
        id=str(voice_config.id),
        practice_id=str(voice_config.practice_id),
        agent_id=voice_config.agent_id,
        timezone=voice_config.timezone,
        metadata=voice_config.config_metadata or {},
        is_active=voice_config.is_active,
        created_at=voice_config.created_at.isoformat(),
        updated_at=voice_config.updated_at.isoformat()
    )


@router.patch("/{practice_id}/voice-agent/node/{node_name}/message", response_model=dict)
async def update_voice_agent_node_message(
    practice_id: str,
    node_name: str,
    personality_update: VoiceAgentPersonalityUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Update any node's instruction message in the voice agent's conversation flow
    
    This endpoint can update ANY node by name (e.g., "Welcome Node", "Goodbye Node", etc.)
    """
    logger.info("=" * 80)
    logger.info(f"🎭 NODE MESSAGE UPDATE STARTED for practice {practice_id}")
    logger.info(f"🎯 Target node: '{node_name}'")
    logger.info(f"📝 New message text length: {len(personality_update.personality_text)} characters")
    logger.info(f"📝 Text preview: {personality_update.personality_text[:200]}...")
    logger.info("=" * 80)
    
    try:
        # Step 1: Get the voice agent configuration for this practice
        logger.info(f"📋 STEP 1: Getting voice agent for practice {practice_id}")
        
        voice_config_query = select(VoiceConfig).where(
            VoiceConfig.practice_id == UUID(practice_id),
            VoiceConfig.is_active == True
        )
        
        result = await session.execute(voice_config_query)
        voice_config = result.scalars().first()
        
        if not voice_config:
            logger.error(f"❌ STEP 1 FAILED: No voice agent found for practice {practice_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No voice agent found for practice {practice_id}"
            )
        
        agent_id = voice_config.agent_id
        logger.info(f"✅ STEP 1 SUCCESS: Found voice agent {agent_id}")
        
        # Step 2: Get agent details from Retell to retrieve conversation_flow_id
        logger.info(f"📋 STEP 2: Getting agent details from Retell for agent {agent_id}")
        
        agent_details = retell_service.get_agent(agent_id)
        if not agent_details:
            logger.error(f"❌ STEP 2 FAILED: Could not retrieve agent details from Retell")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve agent details from Retell"
            )
        
        # Extract conversation flow ID and current version
        response_engine = agent_details.get("response_engine")
        logger.info(f"🔍 Response engine type: {type(response_engine)}")
        logger.info(f"🔍 Response engine attributes: {dir(response_engine) if response_engine else 'None'}")
        
        if not response_engine:
            logger.error(f"❌ STEP 2 FAILED: No response_engine found in agent response")
            logger.error(f"🔍 Agent details keys: {list(agent_details.keys())}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent does not have a response engine configured"
            )
        
        # Access conversation_flow_id and version as attributes, not dict keys
        try:
            conversation_flow_id = getattr(response_engine, 'conversation_flow_id', None)
            current_version = getattr(response_engine, 'version', 1)
            
            logger.info(f"🔍 Extracted conversation_flow_id: {conversation_flow_id}")
            logger.info(f"🔍 Extracted version: {current_version}")
            
        except Exception as attr_error:
            logger.error(f"❌ Failed to extract attributes: {attr_error}")
            # Try as dict fallback
            if hasattr(response_engine, '__dict__'):
                engine_dict = response_engine.__dict__
                conversation_flow_id = engine_dict.get('conversation_flow_id')
                current_version = engine_dict.get('version', 1)
                logger.info(f"🔍 Fallback - extracted from __dict__: flow_id={conversation_flow_id}, version={current_version}")
            else:
                raise
        
        if not conversation_flow_id:
            logger.error(f"❌ STEP 2 FAILED: No conversation_flow_id found in agent response")
            logger.error(f"🔍 Response engine dict: {response_engine.__dict__ if hasattr(response_engine, '__dict__') else 'No __dict__'}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent does not have a conversation flow configured"
            )
        
        logger.info(f"✅ STEP 2 SUCCESS: Found conversation_flow_id {conversation_flow_id}, current version {current_version}")
        
        # Step 3: Update the conversation flow with new personality text
        logger.info(f"📋 STEP 3: Updating conversation flow {conversation_flow_id}")
        
        flow_update_result = retell_service.update_conversation_flow(
            conversation_flow_id=conversation_flow_id,
            personality_text=personality_update.personality_text,
            node_name=node_name
        )
        
        if not flow_update_result:
            logger.error(f"❌ STEP 3 FAILED: Could not update conversation flow")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update conversation flow"
            )
        
        logger.info(f"✅ STEP 3 SUCCESS: Updated conversation flow")
        
        # NOTE: No need to update agent version - agent automatically uses latest conversation flow version
        logger.info(f"ℹ️  SKIPPING agent version update - agent will automatically use updated conversation flow")
        
        # Success! Return summary
        logger.info("=" * 80)
        logger.info(f"🎉 PERSONALITY UPDATE COMPLETED SUCCESSFULLY!")
        logger.info(f"🆔 Agent ID: {agent_id}")
        logger.info(f"🔗 Conversation Flow ID: {conversation_flow_id}")
        logger.info(f"📝 Text length: {len(personality_update.personality_text)} characters")
        logger.info(f"ℹ️  Agent will automatically use the updated conversation flow")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "message": "Voice agent personality updated successfully - agent will automatically use updated conversation flow",
            "agent_id": agent_id,
            "conversation_flow_id": conversation_flow_id,
            "current_version": current_version,
            "personality_text_length": len(personality_update.personality_text),
            "note": "Agent automatically uses latest conversation flow version"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"💥 PERSONALITY UPDATE FAILED with unexpected error: {e}")
        logger.error(f"🔍 Practice ID: {practice_id}")
        logger.error(f"🔍 Error type: {type(e).__name__}")
        logger.error("=" * 80)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during personality update: {str(e)}"
        )


@router.get("/{practice_id}/voice-agent/node/{node_name}/message", response_model=dict)
async def get_voice_agent_node_message(
    practice_id: str,
    node_name: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get the current instruction message from any node in the voice agent's conversation flow
    """
    logger.info(f"🔍 Getting message from node '{node_name}' for practice {practice_id}")
    
    try:
        # Step 1: Get the voice agent configuration for this practice
        voice_config_query = select(VoiceConfig).where(
            VoiceConfig.practice_id == UUID(practice_id),
            VoiceConfig.is_active == True
        )
        
        result = await session.execute(voice_config_query)
        voice_config = result.scalars().first()
        
        if not voice_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No voice agent found for practice {practice_id}"
            )
        
        agent_id = voice_config.agent_id
        logger.info(f"✅ Found voice agent {agent_id}")
        
        # Step 2: Get agent details to get conversation_flow_id
        agent_details = retell_service.get_agent(agent_id)
        if not agent_details:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve agent details from Retell"
            )
        
        response_engine = agent_details.get("response_engine")
        if not response_engine:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent does not have a response engine configured"
            )
        
        conversation_flow_id = getattr(response_engine, 'conversation_flow_id', None)
        if not conversation_flow_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent does not have a conversation flow configured"
            )
        
        logger.info(f"✅ Found conversation_flow_id: {conversation_flow_id}")
        
        # Step 3: Get the conversation flow and extract message from specified node
        node_message = retell_service.get_node_message(conversation_flow_id, node_name)
        if node_message is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node '{node_name}' not found or has no instruction message"
            )
        
        logger.info(f"✅ Retrieved message from node '{node_name}': {node_message[:100]}...")
        
        return {
            "success": True,
            "node_name": node_name,
            "message": node_message,
            "agent_id": agent_id,
            "conversation_flow_id": conversation_flow_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get welcome message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
