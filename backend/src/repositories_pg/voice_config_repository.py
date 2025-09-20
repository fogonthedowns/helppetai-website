"""Repository for voice configuration operations."""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models_pg.voice_config import VoiceConfig


class VoiceConfigRepository:
    """Repository for voice configuration database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_practice_id(self, practice_id: UUID) -> Optional[VoiceConfig]:
        """Get voice config by practice ID."""
        query = select(VoiceConfig).where(
            VoiceConfig.practice_id == practice_id,
            VoiceConfig.is_active == True
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_agent_id(self, agent_id: str) -> Optional[VoiceConfig]:
        """Get voice config by agent ID."""
        query = select(VoiceConfig).where(
            VoiceConfig.agent_id == agent_id,
            VoiceConfig.is_active == True
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, voice_config: VoiceConfig) -> VoiceConfig:
        """Create a new voice config."""
        self.session.add(voice_config)
        await self.session.flush()
        await self.session.refresh(voice_config)
        return voice_config
    
    async def update(self, voice_config: VoiceConfig) -> VoiceConfig:
        """Update an existing voice config."""
        await self.session.flush()
        await self.session.refresh(voice_config)
        return voice_config
    
    async def delete(self, voice_config: VoiceConfig) -> None:
        """Soft delete a voice config by marking it inactive."""
        voice_config.is_active = False
        await self.session.flush()
