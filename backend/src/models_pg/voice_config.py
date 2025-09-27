"""Voice configuration model for practices."""

from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base


class VoiceConfig(Base):
    """Voice configuration settings for veterinary practices."""
    
    __tablename__ = "voice_config"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("veterinary_practices.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(String, nullable=False, doc="External voice agent identifier")
    phone_number = Column(String(20), nullable=True, doc="Phone number associated with the voice agent")
    timezone = Column(String, nullable=True, default="UTC", doc="Practice timezone for voice calls")
    config_metadata = Column("metadata", JSONB, nullable=False, default=dict, doc="Additional voice configuration settings")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("VeterinaryPractice", back_populates="voice_config")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("practice_id", name="unique_practice_voice_config"),
        Index("idx_voice_config_practice_id", "practice_id"),
        Index("idx_voice_config_agent_id", "agent_id"),
        Index("idx_voice_config_active", "practice_id", "is_active"),
    )
    
    def __repr__(self):
        return f"<VoiceConfig(practice_id={self.practice_id}, agent_id={self.agent_id})>"
