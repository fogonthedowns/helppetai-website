"""
Recording model for PostgreSQL - HelpPet MVP
Audio recordings linked to visits and appointments
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, UUID, ForeignKey, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum

try:
    from ..database_pg import Base
except ImportError:
    from database_pg import Base

if TYPE_CHECKING:
    from .visit import Visit
    from .appointment import Appointment
    from .user import User


class RecordingStatus(str, Enum):
    """Recording processing status"""
    UPLOADING = "uploading"      # Currently being uploaded to S3
    UPLOADED = "uploaded"        # Successfully uploaded to S3
    PROCESSING = "processing"    # Being processed for transcription
    TRANSCRIBED = "transcribed"  # Transcription completed
    FAILED = "failed"           # Processing failed
    DELETED = "deleted"         # Soft deleted


class RecordingType(str, Enum):
    """Type of recording"""
    VISIT_AUDIO = "visit_audio"           # Main visit recording
    VISIT_NOTE = "visit_note"             # Additional voice note
    APPOINTMENT_MEMO = "appointment_memo"  # Pre-appointment memo
    FOLLOW_UP = "follow_up"               # Follow-up recording


class Recording(Base):
    """Recording model - audio files linked to visits/appointments"""
    
    __tablename__ = "recordings"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys - can be linked to either visit or appointment
    visit_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("visits.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True
    )
    
    # Recording metadata
    recording_type: Mapped[str] = mapped_column(String(50), nullable=False, default=RecordingType.VISIT_AUDIO.value)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=RecordingStatus.UPLOADING.value, index=True)
    
    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # S3 information
    s3_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    s3_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    # Transcription results
    transcript_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transcript_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    transcript_language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Processing metadata
    transcription_service: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'whisper', 'aws_transcribe', etc.
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Additional metadata as JSON
    recording_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(String(2000), nullable=True)  # JSON string for compatibility
    
    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    visit: Mapped[Optional["Visit"]] = relationship("Visit", back_populates="recordings")
    appointment: Mapped[Optional["Appointment"]] = relationship("Appointment", back_populates="recordings")
    recorded_by: Mapped["User"] = relationship("User", foreign_keys=[recorded_by_user_id], back_populates="recordings")
    deleted_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[deleted_by_user_id])
    
    def __repr__(self) -> str:
        return f"<Recording(id={self.id}, filename={self.filename}, status={self.status})>"
    
    @property
    def is_transcribed(self) -> bool:
        """Check if recording has been transcribed"""
        return self.status == RecordingStatus.TRANSCRIBED.value and bool(self.transcript_text)
    
    @property
    def is_processing(self) -> bool:
        """Check if recording is currently being processed"""
        return self.status in [RecordingStatus.PROCESSING.value, RecordingStatus.UPLOADING.value]
    
    @property
    def duration_formatted(self) -> Optional[str]:
        """Get formatted duration string (MM:SS)"""
        if not self.duration_seconds:
            return None
        
        minutes = int(self.duration_seconds // 60)
        seconds = int(self.duration_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "visit_id": str(self.visit_id) if self.visit_id else None,
            "appointment_id": str(self.appointment_id) if self.appointment_id else None,
            "recording_type": self.recording_type,
            "status": self.status,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size_bytes": self.file_size_bytes,
            "duration_seconds": self.duration_seconds,
            "duration_formatted": self.duration_formatted,
            "mime_type": self.mime_type,
            "s3_url": self.s3_url,
            "transcript_text": self.transcript_text,
            "transcript_confidence": self.transcript_confidence,
            "transcript_language": self.transcript_language,
            "transcription_service": self.transcription_service,
            "is_transcribed": self.is_transcribed,
            "is_processing": self.is_processing,
            "processing_started_at": self.processing_started_at.isoformat() if self.processing_started_at else None,
            "processing_completed_at": self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            "processing_error": self.processing_error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "recorded_by_user_id": str(self.recorded_by_user_id),
        }
