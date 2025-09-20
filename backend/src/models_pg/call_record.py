"""Call record model for caching Retell API data."""

from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base


class CallRecord(Base):
    """Cached call record from voice service for fast API responses."""
    
    __tablename__ = "call_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    practice_id = Column(UUID(as_uuid=True), ForeignKey("veterinary_practices.id", ondelete="CASCADE"), nullable=False)
    call_id = Column(String, nullable=False, unique=True, doc="External call identifier from voice service")
    
    # Call metadata
    agent_id = Column(String, nullable=True, doc="Voice agent identifier")
    recording_url = Column(String, nullable=True, doc="URL to call recording")
    start_timestamp = Column(TIMESTAMP(timezone=True), nullable=True, doc="When call started")
    end_timestamp = Column(TIMESTAMP(timezone=True), nullable=True, doc="When call ended")
    from_number = Column(String, nullable=True, doc="Caller's phone number")
    to_number = Column(String, nullable=True, doc="Practice's phone number")
    duration_ms = Column(Integer, nullable=True, doc="Call duration in milliseconds")
    call_status = Column(String, nullable=True, doc="Final call status")
    disconnect_reason = Column(String, nullable=True, doc="Reason call ended")
    
    # Call analysis
    call_successful = Column(Boolean, nullable=True, doc="Whether call achieved its purpose")
    call_summary = Column(Text, nullable=True, doc="AI-generated call summary")
    user_sentiment = Column(String, nullable=True, doc="Detected caller sentiment")
    in_voicemail = Column(Boolean, nullable=True, doc="Whether call went to voicemail")
    custom_analysis_data = Column("custom_analysis_data", JSONB, nullable=False, default=dict, doc="Additional analysis metadata")
    
    # Caller identification
    caller_pet_owner_id = Column(UUID(as_uuid=True), ForeignKey("pet_owners.id"), nullable=True, doc="Matched pet owner if found")
    
    # Cache management
    last_synced_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), doc="When record was last synced from API")
    sync_status = Column(String, nullable=False, default="pending", doc="Sync status: pending, synced, error")
    sync_error = Column(Text, nullable=True, doc="Last sync error message")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    practice = relationship("VeterinaryPractice", back_populates="call_records")
    caller_pet_owner = relationship("PetOwner", foreign_keys=[caller_pet_owner_id])
    
    # Indexes
    __table_args__ = (
        Index("idx_call_records_practice_date", "practice_id", "start_timestamp"),
        Index("idx_call_records_sync_status", "sync_status", "last_synced_at"),
        Index("idx_call_records_active", "practice_id", "is_active", "start_timestamp"),
        Index("idx_call_records_call_id", "call_id"),
    )
    
    def __repr__(self):
        return f"<CallRecord(call_id={self.call_id}, practice_id={self.practice_id})>"
    
    def _convert_timestamp(self, timestamp_value) -> Optional[datetime]:
        """Convert timestamp from various formats to datetime object."""
        if timestamp_value is None:
            return None
        
        # If it's already a datetime object, return as-is
        if isinstance(timestamp_value, datetime):
            return timestamp_value
        
        # If it's an integer (Unix timestamp), convert it
        if isinstance(timestamp_value, (int, float)):
            # Handle both seconds and milliseconds timestamps
            if timestamp_value > 1e12:  # Likely milliseconds
                return datetime.fromtimestamp(timestamp_value / 1000.0)
            else:  # Likely seconds
                return datetime.fromtimestamp(timestamp_value)
        
        # If it's a string, try to parse it
        if isinstance(timestamp_value, str):
            try:
                # Try parsing as ISO format first
                return datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try parsing as Unix timestamp
                    ts = float(timestamp_value)
                    if ts > 1e12:  # Likely milliseconds
                        return datetime.fromtimestamp(ts / 1000.0)
                    else:  # Likely seconds
                        return datetime.fromtimestamp(ts)
                except ValueError:
                    pass
        
        # If we can't convert it, return None
        return None
    
    @property
    def call_analysis_dict(self) -> Optional[Dict[str, Any]]:
        """Get call analysis as dictionary format matching API schema."""
        if not any([self.call_successful, self.call_summary, self.user_sentiment, self.in_voicemail]):
            return None
        
        return {
            "call_successful": self.call_successful,
            "call_summary": self.call_summary,
            "user_sentiment": self.user_sentiment,
            "in_voicemail": self.in_voicemail,
            "custom_analysis_data": self.custom_analysis_data or {}
        }
    
    def to_api_dict(self, include_details: bool = False) -> Dict[str, Any]:
        """Convert to API response format."""
        result = {
            "call_id": self.call_id,
            "recording_url": self.recording_url,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "from_number": self.from_number,
            "to_number": self.to_number,
            "duration_ms": self.duration_ms,
            "call_analysis": self.call_analysis_dict
        }
        
        # Add caller info if matched (temporarily disabled relationship)
        if self.caller_pet_owner_id:
            result["caller"] = {
                "pet_owner_id": str(self.caller_pet_owner_id),
                "name": "Pet Owner",  # Placeholder until relationship is fixed
                "phone": self.from_number
            }
        
        if include_details:
            result.update({
                "agent_id": self.agent_id,
                "call_status": self.call_status,
                "disconnect_reason": self.disconnect_reason
            })
        
        return result
    
    def update_from_api_data(self, api_data: Dict[str, Any]) -> None:
        """Update record from external API data."""
        # Basic call data
        self.agent_id = api_data.get("agent_id")
        self.recording_url = api_data.get("recording_url")
        self.start_timestamp = self._convert_timestamp(api_data.get("start_timestamp"))
        self.end_timestamp = self._convert_timestamp(api_data.get("end_timestamp"))
        self.from_number = api_data.get("from_number")
        self.to_number = api_data.get("to_number")
        self.duration_ms = api_data.get("duration_ms")
        self.call_status = api_data.get("call_status")
        self.disconnect_reason = api_data.get("disconnect_reason")
        
        # Call analysis
        call_analysis = api_data.get("call_analysis", {}) or {}
        self.call_successful = call_analysis.get("call_successful")
        self.call_summary = call_analysis.get("call_summary")
        self.user_sentiment = call_analysis.get("user_sentiment")
        self.in_voicemail = call_analysis.get("in_voicemail")
        self.custom_analysis_data = call_analysis.get("custom_analysis_data", {})
        
        # Update sync status
        self.last_synced_at = func.now()
        self.sync_status = "synced"
        self.sync_error = None
