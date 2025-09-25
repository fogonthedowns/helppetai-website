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
    practice_id: str
    timezone: str = "US/Pacific"
    metadata: Optional[dict] = {}


class VoiceAgentUpdate(BaseModel):
    timezone: Optional[str] = None
    metadata: Optional[dict] = None
    is_active: Optional[bool] = None


class VoiceAgentResponse(BaseModel):
    id: str
    practice_id: str
    agent_id: str
    timezone: str
    metadata: dict
    is_active: bool
    created_at: str
    updated_at: str


@router.get("/", response_model=List[VoiceAgentResponse])
async def get_voice_agents(
    practice_id: Optional[str] = None,
    is_active: Optional[bool] = True,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> List[VoiceAgentResponse]:
    """Get all voice agents, optionally filtered by practice"""
    
    query = select(VoiceConfig)
    
    if practice_id:
        query = query.where(VoiceConfig.practice_id == UUID(practice_id))
    
    if is_active is not None:
        query = query.where(VoiceConfig.is_active == is_active)
    
    result = await session.execute(query)
    voice_configs = result.scalars().all()
    
    return [
        VoiceAgentResponse(
            id=str(config.id),
            practice_id=str(config.practice_id),
            agent_id=config.agent_id,
            timezone=config.timezone,
            metadata=config.config_metadata or {},
            is_active=config.is_active,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )
        for config in voice_configs
    ]


@router.post("/", response_model=VoiceAgentResponse)
async def create_or_update_voice_agent(
    agent_data: VoiceAgentCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> VoiceAgentResponse:
    """Create a new voice agent or return existing one for the practice"""
    
    # Get practice information for agent naming
    practice_repo = PracticeRepository(session)
    practice = await practice_repo.get_by_id(agent_data.practice_id)
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with ID {agent_data.practice_id} not found"
        )
    
    # Check if voice agent already exists for this practice
    existing_query = select(VoiceConfig).where(VoiceConfig.practice_id == UUID(agent_data.practice_id))
    existing_result = await session.execute(existing_query)
    existing_voice_config = existing_result.scalar_one_or_none()
    
    if existing_voice_config:
        logger.info(f"🔄 Voice agent already exists for practice {agent_data.practice_id}, returning existing agent")
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
    
    logger.info(f"🏥 Creating voice agent for practice: {practice.name} (ID: {agent_data.practice_id})")
    
    # Create agent on Retell using working conversation flow
    agent_id = await retell_service.create_agent(
        agent_config, 
        practice_id=agent_data.practice_id, 
        timezone=agent_data.timezone
    )
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent on Retell"
        )
    
    # Create voice config in database
    voice_config = VoiceConfig(
        practice_id=UUID(agent_data.practice_id),
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
            logger.info(f"🔄 Race condition detected, voice agent was created by another request for practice {agent_data.practice_id}")
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
    
    logger.info(f"✅ Created voice agent {agent_id} for practice {agent_data.practice_id}")
    
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


@router.post("/register/", response_model=VoiceAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_voice_agent(
    agent_data: VoiceAgentCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> VoiceAgentResponse:
    """Create a new voice agent using HelpPetAI.json configuration"""
    
    # Get practice information for agent naming
    practice_repo = PracticeRepository(session)
    practice = await practice_repo.get_by_id(agent_data.practice_id)
    if not practice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice with ID {agent_data.practice_id} not found"
        )
    
    # Check if voice agent already exists for this practice
    existing_query = select(VoiceConfig).where(VoiceConfig.practice_id == UUID(agent_data.practice_id))
    existing_result = await session.execute(existing_query)
    existing_voice_config = existing_result.scalar_one_or_none()
    
    if existing_voice_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Voice agent already exists for practice {agent_data.practice_id}. Use PUT to update or DELETE to remove the existing agent first."
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
    
    logger.info(f"🏥 Creating voice agent for practice: {practice.name} (ID: {agent_data.practice_id})")
    
    # Create agent on Retell using working conversation flow
    agent_id = await retell_service.create_agent(
        agent_config, 
        practice_id=agent_data.practice_id, 
        timezone=agent_data.timezone
    )
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent on Retell"
        )
    
    # Create voice config in database
    voice_config = VoiceConfig(
        practice_id=UUID(agent_data.practice_id),
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
                detail=f"Voice agent already exists for practice {agent_data.practice_id}. Use PUT to update or DELETE to remove the existing agent first."
            )
        else:
            logger.error(f"Database integrity error creating voice agent: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create voice agent due to database constraint violation"
            )
    
    logger.info(f"✅ Created voice agent {agent_id} for practice {agent_data.practice_id}")
    
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


@router.get("/{voice_config_id}", response_model=VoiceAgentResponse)
async def get_voice_agent(
    voice_config_id: UUID = Path(..., description="Voice config ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> VoiceAgentResponse:
    """Get a specific voice agent by ID"""
    
    result = await session.execute(
        select(VoiceConfig).where(VoiceConfig.id == voice_config_id)
    )
    voice_config = result.scalar_one_or_none()
    
    if not voice_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice agent with ID {voice_config_id} not found"
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


@router.put("/{voice_config_id}", response_model=VoiceAgentResponse)
async def update_voice_agent(
    voice_config_id: UUID = Path(..., description="Voice config ID"),
    agent_update: VoiceAgentUpdate = ...,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> VoiceAgentResponse:
    """Update a voice agent"""
    
    # Get existing voice config
    result = await session.execute(
        select(VoiceConfig).where(VoiceConfig.id == voice_config_id)
    )
    voice_config = result.scalar_one_or_none()
    
    if not voice_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice agent with ID {voice_config_id} not found"
        )
    
    # Update voice config in database
    update_data = agent_update.dict(exclude_unset=True)
    
    if update_data:
        await session.execute(
            update(VoiceConfig)
            .where(VoiceConfig.id == voice_config_id)
            .values(**update_data)
        )
        await session.commit()
        await session.refresh(voice_config)
    
    # If timezone changed, we might want to update the Retell agent too
    if "timezone" in update_data:
        agent_config = load_helppetai_config(
            practice_id=str(voice_config.practice_id),
            timezone=update_data["timezone"]
        )
        if agent_config:
            # Update the timezone in the global prompt
            if "conversationFlow" in agent_config and "global_prompt" in agent_config["conversationFlow"]:
                global_prompt = agent_config["conversationFlow"]["global_prompt"]
                # Update the timezone placeholder
                global_prompt = global_prompt.replace(
                    '{{timezone}} = "US/Pacific"',
                    f'{{{{timezone}}}} = "{voice_config.timezone}"'
                )
                agent_config["conversationFlow"]["global_prompt"] = global_prompt
            
            # Update agent on Retell
            retell_service.update_agent(voice_config.agent_id, agent_config)
    
    logger.info(f"✅ Updated voice agent {voice_config.agent_id}")
    
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


@router.delete("/{voice_config_id}", response_model=VoiceAgentResponse)
async def delete_voice_agent(
    voice_config_id: UUID = Path(..., description="Voice config ID"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> VoiceAgentResponse:
    """Soft delete a voice agent (set is_active to False)"""
    
    # Get existing voice config
    result = await session.execute(
        select(VoiceConfig).where(VoiceConfig.id == voice_config_id)
    )
    voice_config = result.scalar_one_or_none()
    
    if not voice_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice agent with ID {voice_config_id} not found"
        )
    
    # Soft delete - set is_active to False
    await session.execute(
        update(VoiceConfig)
        .where(VoiceConfig.id == voice_config_id)
        .values(is_active=False)
    )
    await session.commit()
    await session.refresh(voice_config)
    
    logger.info(f"✅ Soft deleted voice agent {voice_config.agent_id} (set is_active=False)")
    
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
