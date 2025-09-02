"""
Recording routes for PostgreSQL - HelpPet MVP
Audio recording upload orchestration and management
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from pydantic import BaseModel, Field

from ..database_pg import get_db_session
from ..models_pg.recording import Recording, RecordingStatus, RecordingType
from ..models_pg.visit import Visit
from ..models_pg.appointment import Appointment
from ..models_pg.user import User
from ..auth.jwt_auth_pg import get_current_user
from ..services.s3_service import s3_service

router = APIRouter(prefix="/recordings", tags=["recordings"])


# Pydantic schemas
class RecordingUploadRequest(BaseModel):
    """Request to initiate a recording upload"""
    appointment_id: Optional[uuid.UUID] = None
    visit_id: Optional[uuid.UUID] = None
    recording_type: RecordingType = RecordingType.VISIT_AUDIO
    filename: str = Field(..., max_length=255, description="Original filename")
    content_type: str = Field(default="audio/m4a", description="MIME type of the audio file")
    estimated_duration_seconds: Optional[float] = Field(None, ge=0, description="Estimated duration in seconds")


class RecordingUploadResponse(BaseModel):
    """Response with presigned upload URL and recording metadata"""
    recording_id: uuid.UUID
    upload_url: str
    upload_fields: Dict[str, Any]
    s3_key: str
    bucket: str
    expires_in: int
    max_file_size: int


class RecordingCompleteRequest(BaseModel):
    """Request to mark recording upload as complete"""
    file_size_bytes: Optional[int] = Field(None, ge=0)
    duration_seconds: Optional[float] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class RecordingResponse(BaseModel):
    """Recording response model"""
    id: uuid.UUID
    visit_id: Optional[uuid.UUID]
    appointment_id: Optional[uuid.UUID]
    recording_type: str
    status: str
    filename: str
    original_filename: Optional[str]
    file_size_bytes: Optional[int]
    duration_seconds: Optional[float]
    duration_formatted: Optional[str]
    mime_type: Optional[str]
    s3_url: Optional[str]
    transcript_text: Optional[str]
    transcript_confidence: Optional[float]
    is_transcribed: bool
    is_processing: bool
    created_at: datetime
    updated_at: datetime
    recorded_by_user_id: uuid.UUID


@router.post("/upload/initiate", response_model=RecordingUploadResponse)
async def initiate_recording_upload(
    request: RecordingUploadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Initiate a recording upload by generating a presigned S3 URL
    
    This endpoint:
    1. Validates the appointment/visit exists and user has access
    2. Creates a recording record in the database
    3. Generates a presigned S3 upload URL
    4. Returns upload instructions for the mobile client
    """
    
    # Validate that either appointment_id or visit_id is provided
    if not request.appointment_id and not request.visit_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either appointment_id or visit_id must be provided"
        )
    
    # Validate appointment or visit exists and user has access
    if request.appointment_id:
        appointment_query = select(Appointment).where(
            and_(
                Appointment.id == request.appointment_id,
                or_(
                    Appointment.assigned_vet_user_id == current_user.id,
                    Appointment.created_by_user_id == current_user.id
                )
            )
        )
        result = await db.execute(appointment_query)
        appointment = result.scalar_one_or_none()
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found or access denied"
            )
    
    if request.visit_id:
        visit_query = select(Visit).where(
            and_(
                Visit.id == request.visit_id,
                or_(
                    Visit.vet_user_id == current_user.id,
                    Visit.created_by == current_user.id
                )
            )
        )
        result = await db.execute(visit_query)
        visit = result.scalar_one_or_none()
        
        if not visit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Visit not found or access denied"
            )
    
    try:
        # Generate S3 key for the recording
        s3_key = s3_service.generate_recording_key(
            user_id=str(current_user.id),
            appointment_id=str(request.appointment_id) if request.appointment_id else None,
            visit_id=str(request.visit_id) if request.visit_id else None,
            file_extension=request.filename.split('.')[-1] if '.' in request.filename else 'm4a'
        )
        
        # Generate presigned upload URL
        upload_data = s3_service.generate_presigned_upload_url(
            s3_key=s3_key,
            content_type=request.content_type
        )
        
        # Create recording record in database
        recording = Recording(
            visit_id=request.visit_id,
            appointment_id=request.appointment_id,
            recorded_by_user_id=current_user.id,
            recording_type=request.recording_type.value,
            status=RecordingStatus.UPLOADING.value,
            filename=s3_key.split('/')[-1],  # Extract filename from S3 key
            original_filename=request.filename,
            mime_type=request.content_type,
            s3_bucket=upload_data['bucket'],
            s3_key=s3_key,
            duration_seconds=request.estimated_duration_seconds
        )
        
        db.add(recording)
        await db.commit()
        await db.refresh(recording)
        
        return RecordingUploadResponse(
            recording_id=recording.id,
            upload_url=upload_data['upload_url'],
            upload_fields=upload_data['fields'],
            s3_key=s3_key,
            bucket=upload_data['bucket'],
            expires_in=upload_data['expires_in'],
            max_file_size=upload_data['max_file_size']
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate upload: {str(e)}"
        )


@router.post("/upload/complete/{recording_id}")
async def complete_recording_upload(
    recording_id: uuid.UUID,
    request: RecordingCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Mark a recording upload as complete and update metadata
    
    This endpoint should be called by the mobile client after successfully
    uploading the file to S3 using the presigned URL.
    """
    
    # Get the recording
    recording_query = select(Recording).where(
        and_(
            Recording.id == recording_id,
            Recording.recorded_by_user_id == current_user.id
        )
    )
    result = await db.execute(recording_query)
    recording = result.scalar_one_or_none()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found or access denied"
        )
    
    if recording.status != RecordingStatus.UPLOADING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Recording is not in uploading state (current: {recording.status})"
        )
    
    try:
        # Verify file exists in S3
        if not s3_service.check_file_exists(recording.s3_key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File not found in S3. Upload may have failed."
            )
        
        # Get file metadata from S3
        s3_metadata = s3_service.get_file_metadata(recording.s3_key)
        
        # Update recording with completion data
        recording.status = RecordingStatus.UPLOADED.value
        recording.file_size_bytes = request.file_size_bytes or s3_metadata.get('content_length')
        recording.duration_seconds = request.duration_seconds or recording.duration_seconds
        recording.s3_url = s3_service.get_public_url(recording.s3_key)
        
        if request.metadata:
            recording.recording_metadata = str(request.metadata)  # Store as JSON string
        
        await db.commit()
        await db.refresh(recording)
        
        # TODO: Trigger transcription process here
        # This could be done via a background task, SQS queue, or direct API call
        
        return {"message": "Recording upload completed successfully", "recording_id": recording.id}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete upload: {str(e)}"
        )


@router.get("/", response_model=List[RecordingResponse])
async def get_recordings(
    appointment_id: Optional[uuid.UUID] = Query(None, description="Filter by appointment ID"),
    visit_id: Optional[uuid.UUID] = Query(None, description="Filter by visit ID"),
    status: Optional[RecordingStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of recordings to return"),
    offset: int = Query(0, ge=0, description="Number of recordings to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get recordings for the current user with optional filters"""
    
    query = select(Recording).where(Recording.recorded_by_user_id == current_user.id)
    
    # Apply filters
    if appointment_id:
        query = query.where(Recording.appointment_id == appointment_id)
    
    if visit_id:
        query = query.where(Recording.visit_id == visit_id)
    
    if status:
        query = query.where(Recording.status == status.value)
    
    # Apply ordering, limit, and offset
    query = query.order_by(Recording.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    recordings = result.scalars().all()
    
    return [
        RecordingResponse(
            id=recording.id,
            visit_id=recording.visit_id,
            appointment_id=recording.appointment_id,
            recording_type=recording.recording_type,
            status=recording.status,
            filename=recording.filename,
            original_filename=recording.original_filename,
            file_size_bytes=recording.file_size_bytes,
            duration_seconds=recording.duration_seconds,
            duration_formatted=recording.duration_formatted,
            mime_type=recording.mime_type,
            s3_url=recording.s3_url,
            transcript_text=recording.transcript_text,
            transcript_confidence=recording.transcript_confidence,
            is_transcribed=recording.is_transcribed,
            is_processing=recording.is_processing,
            created_at=recording.created_at,
            updated_at=recording.updated_at,
            recorded_by_user_id=recording.recorded_by_user_id
        )
        for recording in recordings
    ]


@router.get("/{recording_id}", response_model=RecordingResponse)
async def get_recording(
    recording_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific recording by ID"""
    
    recording_query = select(Recording).where(
        and_(
            Recording.id == recording_id,
            Recording.recorded_by_user_id == current_user.id
        )
    )
    result = await db.execute(recording_query)
    recording = result.scalar_one_or_none()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found or access denied"
        )
    
    return RecordingResponse(
        id=recording.id,
        visit_id=recording.visit_id,
        appointment_id=recording.appointment_id,
        recording_type=recording.recording_type,
        status=recording.status,
        filename=recording.filename,
        original_filename=recording.original_filename,
        file_size_bytes=recording.file_size_bytes,
        duration_seconds=recording.duration_seconds,
        duration_formatted=recording.duration_formatted,
        mime_type=recording.mime_type,
        s3_url=recording.s3_url,
        transcript_text=recording.transcript_text,
        transcript_confidence=recording.transcript_confidence,
        is_transcribed=recording.is_transcribed,
        is_processing=recording.is_processing,
        created_at=recording.created_at,
        updated_at=recording.updated_at,
        recorded_by_user_id=recording.recorded_by_user_id
    )


@router.get("/{recording_id}/download-url")
async def get_recording_download_url(
    recording_id: uuid.UUID,
    expires_in: int = Query(3600, ge=300, le=86400, description="URL expiration in seconds"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate a presigned download URL for a recording"""
    
    recording_query = select(Recording).where(
        and_(
            Recording.id == recording_id,
            Recording.recorded_by_user_id == current_user.id
        )
    )
    result = await db.execute(recording_query)
    recording = result.scalar_one_or_none()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found or access denied"
        )
    
    if recording.status != RecordingStatus.UPLOADED.value and recording.status != RecordingStatus.TRANSCRIBED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording is not available for download"
        )
    
    try:
        download_url = s3_service.generate_presigned_download_url(
            s3_key=recording.s3_key,
            expires_in=expires_in
        )
        
        return {
            "download_url": download_url,
            "expires_in": expires_in,
            "filename": recording.original_filename or recording.filename
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate download URL: {str(e)}"
        )


@router.delete("/{recording_id}")
async def delete_recording(
    recording_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Soft delete a recording (marks as deleted but keeps the record)"""
    
    recording_query = select(Recording).where(
        and_(
            Recording.id == recording_id,
            Recording.recorded_by_user_id == current_user.id
        )
    )
    result = await db.execute(recording_query)
    recording = result.scalar_one_or_none()
    
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found or access denied"
        )
    
    if recording.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording is already deleted"
        )
    
    try:
        # Soft delete the recording
        recording.is_deleted = True
        recording.deleted_at = datetime.utcnow()
        recording.deleted_by_user_id = current_user.id
        recording.status = RecordingStatus.DELETED.value
        
        await db.commit()
        
        # Optionally delete from S3 (uncomment if you want hard deletion)
        # s3_service.delete_file(recording.s3_key)
        
        return {"message": "Recording deleted successfully"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete recording: {str(e)}"
        )
