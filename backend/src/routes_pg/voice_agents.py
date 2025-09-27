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
import requests

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

class PhoneRegistrationRequest(BaseModel):
    area_code: Optional[int] = None
    toll_free: bool = False
    nickname: Optional[str] = None


class VoiceAgentResponse(BaseModel):
    id: str
    practice_id: str
    agent_id: str
    phone_number: Optional[str] = None
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
    
    logger.info(f"📞 Using cached phone number: {voice_config.phone_number}")
    
    return VoiceAgentResponse(
        id=str(voice_config.id),
        practice_id=str(voice_config.practice_id),
        agent_id=voice_config.agent_id,
        phone_number=voice_config.phone_number,
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
            updated_at=existing_voice_config.updated_at.isoformat(),
            phone_number=None
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
        timezone=practice.timezone
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
        timezone=practice.timezone,
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
        updated_at=voice_config.updated_at.isoformat(),
        phone_number=None
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
        timezone=practice.timezone
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
        timezone=practice.timezone,
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
        updated_at=voice_config.updated_at.isoformat(),
        phone_number=None
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
        updated_at=voice_config.updated_at.isoformat(),
        phone_number=None
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
        
        # Step 4: Publish the agent to make changes live for phone calls
        logger.info(f"📋 STEP 4: Publishing agent {agent_id} to make changes live")
        
        publish_success = retell_service.publish_agent(agent_id)
        if not publish_success:
            logger.error(f"❌ STEP 4 FAILED: Could not publish agent")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish agent - changes may not be live for phone calls"
            )
        
        logger.info(f"✅ STEP 4 SUCCESS: Agent published - our changes are now live!")
        
        # Step 5: Update phone numbers to use latest published version (auto-detects)
        logger.info(f"📋 STEP 5: Updating phone numbers to use latest published version")
        
        phone_numbers = retell_service.find_phone_numbers_for_agent(agent_id)
        if phone_numbers:
            phone_update_results = []
            for phone_number in phone_numbers:
                result = retell_service.update_phone_number_to_latest_version(phone_number, agent_id)
                phone_update_results.append(result)
                
            if all(phone_update_results):
                logger.info(f"✅ STEP 5 SUCCESS: Updated {len(phone_numbers)} phone numbers")
            else:
                logger.warning(f"⚠️ STEP 5 PARTIAL: Some phone numbers failed to update")
        else:
            logger.info(f"ℹ️  STEP 5 SKIPPED: No phone numbers found for agent {agent_id}")
        
        # Success! Return summary
        logger.info("=" * 80)
        logger.info(f"🎉 PERSONALITY UPDATE COMPLETED SUCCESSFULLY!")
        logger.info(f"🆔 Agent ID: {agent_id}")
        logger.info(f"🔗 Conversation Flow ID: {conversation_flow_id}")
        logger.info(f"📝 Text length: {len(personality_update.personality_text)} characters")
        logger.info(f"📢 Agent published and live for phone calls")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "message": "Voice agent personality updated, published, and phone numbers updated - changes are now live for all phone calls",
            "agent_id": agent_id,
            "conversation_flow_id": conversation_flow_id,
            "current_version": current_version,
            "personality_text_length": len(personality_update.personality_text),
            "published": True,
            "phone_numbers_updated": len(phone_numbers),
            "note": "Agent is published and all phone numbers updated to use latest version"
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


@router.post("/{practice_id}/voice-agent/{voice_uuid}/register-phone", response_model=dict)
async def register_phone_number(
    practice_id: str,
    voice_uuid: str,
    phone_request: PhoneRegistrationRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Register/buy a new phone number and bind it to the voice agent
    """
    logger.info("=" * 80)
    logger.info(f"📞 PHONE REGISTRATION STARTED for practice {practice_id}")
    logger.info(f"🎯 Voice agent UUID: {voice_uuid}")
    logger.info(f"📋 Area code: {phone_request.area_code}")
    logger.info(f"📋 Toll-free: {phone_request.toll_free}")
    logger.info(f"📋 Nickname: {phone_request.nickname}")
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
        
        # Step 2: Prepare the phone registration payload
        logger.info(f"📋 STEP 2: Preparing phone registration payload")
        
        # Build the payload for Retell API
        payload = {
            "inbound_agent_id": agent_id,
            "outbound_agent_id": agent_id,
            "country_code": "US",  # Hard-coded as requested
        }
        
        # Add optional fields
        if phone_request.area_code:
            payload["area_code"] = phone_request.area_code
            
        if phone_request.nickname:
            payload["nickname"] = phone_request.nickname
        else:
            payload["nickname"] = f"HelpPet.ai - {voice_config.practice_id}"
            
        payload["toll_free"] = phone_request.toll_free
        
        logger.info(f"🔍 Registration payload: {payload}")
        
        # Step 3: Call Retell API to register phone number
        logger.info(f"📋 STEP 3: Calling Retell API to register phone number")
        
        # Get API key from retell_service
        api_key = retell_service.api_key
        
        # response = requests.post(
        #     "https://api.retellai.com/create-phone-number",
        #     headers={
        #         "Authorization": f"Bearer {api_key}",
        #         "Content-Type": "application/json"
        #     },
        #     json=payload
        # )
        
        # Mock response for testing
        class MockResponse:
            def __init__(self, json_data, status_code):
                self._json_data = json_data
                self.status_code = status_code

            def json(self):
                return self._json_data

        response = MockResponse({
            "phone_number": "+14157774444",
            "phone_number_type": "retell-twilio", 
            "phone_number_pretty": "+1 (415) 777-4444",
            "inbound_agent_id": agent_id,
            "inbound_agent_version": 1,
            "outbound_agent_version": 1,
            "area_code": 415,
            "nickname": "Frontdesk Number",
            "last_modification_timestamp": 1703413636133
        }, 200)
        
        if response.status_code != 200:
            logger.error(f"❌ STEP 3 FAILED: Retell API error {response.status_code}")
            logger.error(f"🔍 Response: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register phone number: {response.text}"
            )
        
        phone_data = response.json()
        logger.info(f"✅ STEP 3 SUCCESS: Phone number registered")
        logger.info(f"🔍 Phone data: {phone_data}")
        
        # Step 4: Update the voice_config with the new phone number
        logger.info(f"📋 STEP 4: Updating voice_config with phone number")
        
        registered_phone = phone_data.get("phone_number")
        if registered_phone:
            voice_config.phone_number = registered_phone
            await session.commit()
            logger.info(f"✅ STEP 4 SUCCESS: Updated voice_config with phone number {registered_phone}")
        else:
            logger.warning(f"⚠️ STEP 4 WARNING: No phone_number in response, skipping database update")
        
        # Success! Return phone registration details
        logger.info("=" * 80)
        logger.info(f"🎉 PHONE REGISTRATION COMPLETED SUCCESSFULLY!")
        logger.info(f"📞 Phone number: {phone_data.get('phone_number', 'Unknown')}")
        logger.info(f"🆔 Agent ID: {agent_id}")
        logger.info(f"🏷️ Nickname: {payload.get('nickname', 'N/A')}")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "message": "Phone number registered and bound to voice agent successfully",
            "phone_number": phone_data.get("phone_number"),
            "agent_id": agent_id,
            "nickname": payload.get("nickname"),
            "toll_free": phone_request.toll_free,
            "area_code": phone_request.area_code,
            "country_code": "US",
            "phone_data": phone_data
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"💥 PHONE REGISTRATION FAILED with unexpected error: {e}")
        logger.error(f"🔍 Practice ID: {practice_id}")
        logger.error(f"🔍 Voice UUID: {voice_uuid}")
        logger.error(f"🔍 Error type: {type(e).__name__}")
        logger.error("=" * 80)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during phone registration: {str(e)}"
        )
