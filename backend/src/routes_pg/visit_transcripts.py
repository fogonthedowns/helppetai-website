"""
Visit Transcripts REST API Routes
Based on spec in docs/0009_VisitTranscript.md
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel, Field

from ..auth.jwt_auth_pg import get_current_user
from ..models_pg.user import User
from ..models_pg.visit import Visit, VisitState
from ..models_pg.pet import Pet
from ..database_pg import get_db_session


router = APIRouter(prefix="/api/v1/visit-transcripts", tags=["visit-transcripts"])


# S3 Configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'helppetai-visit-recordings')
S3_REGION = os.getenv('S3_REGION', 'us-west-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Presigned URL expiration (1 hour)
PRESIGNED_URL_EXPIRATION = 3600


class TranscriptState(str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

# Simplified response model for visit transcript summaries
class VisitTranscriptSummaryResponse(BaseModel):
    uuid: str
    visit_date: int  # Unix timestamp
    state: TranscriptState
    has_audio: bool
    summary: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None
    # Only include essential extracted data
    chief_complaint: Optional[str] = None

# Pydantic models for visit transcripts
class VisitTranscriptCreate(BaseModel):
    pet_id: str
    visit_date: int  # Unix timestamp
    full_text: str
    audio_transcript_url: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    summary: Optional[str] = None


class VisitTranscriptUpdate(BaseModel):
    visit_date: Optional[int] = None
    full_text: Optional[str] = None
    audio_transcript_url: Optional[str] = None
    metadata: Optional[dict] = None
    summary: Optional[str] = None
    state: Optional[VisitState] = None


class VisitTranscriptResponse(BaseModel):
    uuid: str
    pet_id: str
    visit_date: int
    full_text: str
    audio_transcript_url: Optional[str] = None
    metadata: dict
    summary: Optional[str] = None
    state: VisitState
    created_at: str
    updated_at: str
    created_by: Optional[str] = None


# New Pydantic models for audio upload
class AudioUploadRequest(BaseModel):
    pet_id: str
    filename: str
    content_type: str = "audio/m4a"  # Default to M4A, but accept WebM too
    estimated_duration_seconds: Optional[float] = None
    appointment_id: Optional[str] = None  # Add appointment association


class AudioUploadResponse(BaseModel):
    visit_id: str
    upload_url: str
    upload_fields: Dict[str, str]
    s3_key: str
    bucket: str
    expires_in: int


class AudioUploadCompleteRequest(BaseModel):
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    device_metadata: Optional[Dict[str, Any]] = None


class AudioPlaybackResponse(BaseModel):
    presigned_url: str
    expires_in: int
    visit_id: str
    filename: str


# Helper functions
def get_s3_client():
    """Get configured S3 client using IAM role or explicit credentials"""
    try:
        # Try to use IAM role first (recommended for ECS/EC2)
        return boto3.client('s3', region_name=S3_REGION)
    except NoCredentialsError:
        # Fallback to explicit credentials if IAM role not available
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="S3 credentials not configured and IAM role not available"
            )
        
        return boto3.client(
            's3',
            region_name=S3_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )


async def check_pet_access(pet_id: str, user: User, db: AsyncSession) -> Pet:
    """Check if user has access to the pet"""
    try:
        pet_uuid = uuid.UUID(pet_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pet ID format")
    
    # Get pet from database
    result = await db.execute(select(Pet).where(Pet.id == pet_uuid))
    pet = result.scalar_one_or_none()
    
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    
    # Admin can access all pets
    if user.role in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"]:
        return pet
    
    # Vet can access pets from their associated practices
    if user.role in ["VET_STAFF", "VET", "PRACTICE_ADMIN"]:
        # TODO: Check if user's practice is associated with pet owner
        return pet
    
    # Pet owner can access their own pets
    if user.role == "PET_OWNER":
        # TODO: Check if user owns this pet
        return pet
    
    raise HTTPException(status_code=403, detail="Access denied")


def visit_to_transcript_response(visit: Visit) -> VisitTranscriptResponse:
    """Convert Visit model to VisitTranscriptResponse"""
    return VisitTranscriptResponse(
        uuid=str(visit.id),
        pet_id=str(visit.pet_id),
        visit_date=int(visit.visit_date.timestamp()),
        full_text=visit.full_text,
        audio_transcript_url=visit.audio_transcript_url,
        metadata=visit.additional_data or {},
        summary=visit.summary,
        state=VisitState(visit.state),
        created_at=visit.created_at.isoformat(),
        updated_at=visit.updated_at.isoformat(),
        created_by=str(visit.created_by) if visit.created_by else None
    )


@router.get("/pet/{pet_uuid}")
async def list_pet_visit_transcripts(
    pet_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> List[VisitTranscriptSummaryResponse]:
    """
    List all visit transcripts for a pet (summary view)
    Access: Admin | Pet Owner | Associated Vet
    """
    pet = await check_pet_access(pet_uuid, current_user, db)
    
    result = await db.execute(
        select(Visit)
        .where(Visit.pet_id == pet.id)
        .order_by(Visit.visit_date.desc())
    )
    visits = result.scalars().all()
    
    return [
        VisitTranscriptSummaryResponse(
            uuid=str(visit.id),
            visit_date=int(visit.visit_date.timestamp()),
            state=visit.state,
            has_audio=bool(visit.audio_transcript_url),
            summary=visit.summary,
            created_at=visit.created_at,
            created_by=str(visit.created_by) if visit.created_by else None,
            chief_complaint=visit.additional_data.get('chief_complaint') if visit.additional_data else None
        ) 
        for visit in visits
    ]


@router.get("/appointments/{appointment_id}/visits")
async def get_visits_by_appointment(
    appointment_id: str,
    pet_id: Optional[str] = Query(None, description="Optional pet ID to filter visits"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> List[VisitTranscriptResponse]:
    """
    Get all visits for an appointment, optionally filtered by pet
    Access: Admin | Vet | Pet Owner
    """
    try:
        appointment_uuid = uuid.UUID(appointment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid appointment ID format")
    
    # Build query for visits by appointment (appointment_id is stored in additional_data)
    query = select(Visit).where(
        Visit.additional_data.op('->>')('appointment_id') == str(appointment_uuid)
    )
    
    # Optionally filter by pet
    if pet_id:
        try:
            pet_uuid = uuid.UUID(pet_id)
            query = query.where(Visit.pet_id == pet_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid pet ID format")
    
    # Order by visit date descending
    query = query.order_by(Visit.visit_date.desc())
    
    result = await db.execute(query)
    visits = result.scalars().all()
    
    # TODO: Add proper access control - check if user has access to this appointment
    # For now, allow all authenticated users
    
    return [visit_to_transcript_response(visit) for visit in visits]


@router.get("/debug/{visit_id}")
async def debug_visit_audio(
    visit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Debug endpoint to check visit audio configuration
    """
    try:
        visit_uuid = uuid.UUID(visit_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid visit ID format")
    
    # Get visit from database
    result = await db.execute(select(Visit).where(Visit.id == visit_uuid))
    visit = result.scalar_one_or_none()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    # Check access to the pet
    await check_pet_access(str(visit.pet_id), current_user, db)
    
    debug_info = {
        "visit_id": str(visit.id),
        "visit_state": visit.state,
        "audio_transcript_url": visit.audio_transcript_url,
        "additional_data": visit.additional_data,
        "s3_key": visit.additional_data.get('s3_key'),
        "audio_s3_key": visit.additional_data.get('audio_s3_key'),
        "filename": visit.additional_data.get('filename'),
        "audio_filename": visit.additional_data.get('audio_filename'),
        "content_type": visit.additional_data.get('content_type'),
        "s3_bucket": S3_BUCKET_NAME
    }
    
    # Check if file exists in S3
    s3_key = visit.additional_data.get('s3_key') or visit.additional_data.get('audio_s3_key')
    if s3_key:
        try:
            s3_client = get_s3_client()
            response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            debug_info["s3_file_exists"] = True
            debug_info["s3_file_size"] = response.get('ContentLength')
            debug_info["s3_content_type"] = response.get('ContentType')
            debug_info["s3_last_modified"] = response.get('LastModified').isoformat() if response.get('LastModified') else None
        except ClientError as e:
            debug_info["s3_file_exists"] = False
            debug_info["s3_error"] = e.response['Error']['Code']
    else:
        debug_info["s3_file_exists"] = False
        debug_info["s3_error"] = "No S3 key found"
    
    return debug_info


@router.get("/{transcript_uuid}")
async def get_visit_transcript(
    transcript_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> VisitTranscriptResponse:
    """
    View single visit transcript
    Access: Admin | Pet Owner | Associated Vet
    """
    try:
        visit_uuid = uuid.UUID(transcript_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transcript ID format")
    
    # Get visit from database
    result = await db.execute(select(Visit).where(Visit.id == visit_uuid))
    visit = result.scalar_one_or_none()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit transcript not found")
    
    # Check access to the pet
    await check_pet_access(str(visit.pet_id), current_user, db)
    
    return visit_to_transcript_response(visit)


@router.post("")
async def create_visit_transcript(
    transcript_data: VisitTranscriptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> VisitTranscriptResponse:
    """
    Create visit transcript
    Access: Vet or Admin only
    """
    if current_user.role not in ["VET_STAFF", "VET", "PRACTICE_ADMIN", "SYSTEM_ADMIN"]:
        raise HTTPException(
            status_code=403, 
            detail="Only veterinarians and admins can create visit transcripts"
        )
    
    # Verify pet exists and user has access
    pet = await check_pet_access(transcript_data.pet_id, current_user, db)
    
    # Convert unix timestamp to datetime
    visit_datetime = datetime.fromtimestamp(transcript_data.visit_date)
    
    # Create new visit
    visit = Visit(
        pet_id=pet.id,
        practice_id=current_user.practice_id if hasattr(current_user, 'practice_id') else None,
        vet_user_id=current_user.id,
        visit_date=visit_datetime,
        full_text=transcript_data.full_text,
        audio_transcript_url=transcript_data.audio_transcript_url,
        summary=transcript_data.summary,
        state=VisitState.PROCESSED.value,  # Transcripts are for completed visits
        additional_data=transcript_data.metadata,
        created_by=current_user.id
    )
    
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    
    return visit_to_transcript_response(visit)


@router.put("/{transcript_uuid}")
async def update_visit_transcript(
    transcript_uuid: str,
    transcript_data: VisitTranscriptUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> VisitTranscriptResponse:
    """
    Update visit transcript
    Access: Admin | Creating Vet only
    """
    try:
        visit_uuid = uuid.UUID(transcript_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transcript ID format")
    
    # Get visit from database
    result = await db.execute(select(Visit).where(Visit.id == visit_uuid))
    visit = result.scalar_one_or_none()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit transcript not found")
    
    # Check permissions
    if current_user.role not in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"] and visit.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only admins or the creating veterinarian can update this transcript"
        )
    
    # Update fields
    if transcript_data.visit_date is not None:
        visit.visit_date = datetime.fromtimestamp(transcript_data.visit_date)
    if transcript_data.full_text is not None:
        visit.full_text = transcript_data.full_text
    if transcript_data.summary is not None:
        visit.summary = transcript_data.summary
    if transcript_data.audio_transcript_url is not None:
        visit.audio_transcript_url = transcript_data.audio_transcript_url
    if transcript_data.metadata is not None:
        visit.additional_data = transcript_data.metadata
    if transcript_data.state is not None:
        visit.state = transcript_data.state.value
    
    visit.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(visit)
    
    return visit_to_transcript_response(visit)


@router.delete("/{transcript_uuid}")
async def delete_visit_transcript(
    transcript_uuid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Delete visit transcript
    Access: Admin only
    """
    if current_user.role not in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only admins can delete visit transcripts"
        )
    
    try:
        visit_uuid = uuid.UUID(transcript_uuid)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transcript ID format")
    
    # Get visit from database
    result = await db.execute(select(Visit).where(Visit.id == visit_uuid))
    visit = result.scalar_one_or_none()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit transcript not found")
    
    await db.delete(visit)
    await db.commit()
    
    return {"message": "Visit transcript deleted successfully"}


# NEW AUDIO UPLOAD ENDPOINTS FOR IPHONE

@router.post("/audio/upload/initiate")
async def initiate_audio_upload(
    request: AudioUploadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> AudioUploadResponse:
    """
    Initiate audio upload for iPhone - generates presigned S3 URL
    Creates a new visit record in 'new' state for the pet
    """
    if current_user.role not in ["VET_STAFF", "VET", "PRACTICE_ADMIN", "SYSTEM_ADMIN"]:
        raise HTTPException(
            status_code=403, 
            detail="Only veterinarians and admins can upload audio"
        )
    
    # Verify pet exists and user has access
    pet = await check_pet_access(request.pet_id, current_user, db)
    
    # Handle appointment validation if provided
    appointment = None
    appointment_date = datetime.now()  # Default to now if no appointment
    
    if request.appointment_id:
        try:
            appointment_uuid = uuid.UUID(request.appointment_id)
            from ..models_pg.appointment import Appointment, AppointmentPet
            
            # Get appointment
            appointment_result = await db.execute(
                select(Appointment).where(Appointment.id == appointment_uuid)
            )
            appointment = appointment_result.scalar_one_or_none()
            
            if not appointment:
                raise HTTPException(
                    status_code=404,
                    detail=f"Appointment {request.appointment_id} not found"
                )
            
            # Verify this pet is part of the appointment
            appointment_pet_result = await db.execute(
                select(AppointmentPet).where(
                    AppointmentPet.appointment_id == appointment_uuid,
                    AppointmentPet.pet_id == pet.id
                )
            )
            appointment_pet = appointment_pet_result.scalar_one_or_none()
            
            if not appointment_pet:
                raise HTTPException(
                    status_code=400,
                    detail=f"Pet {request.pet_id} is not associated with appointment {request.appointment_id}"
                )
            
            appointment_date = appointment.appointment_date
            
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid appointment ID format"
            )
    
    # Check if there's already a recording for this specific appointment and pet combination
    if request.appointment_id:
        existing_visit_result = await db.execute(
            select(Visit).where(
                and_(
                    Visit.additional_data.op('->>')('appointment_id') == request.appointment_id,
                    Visit.pet_id == pet.id,
                    Visit.audio_transcript_url.isnot(None)  # Has audio
                )
            )
        )
        existing_visit = existing_visit_result.scalar_one_or_none()
        
        if existing_visit:
            raise HTTPException(
                status_code=409,
                detail=f"Audio recording already exists for this appointment and pet. Visit ID: {existing_visit.id}"
            )
    
    try:
        # Generate unique S3 key with appropriate extension
        timestamp = datetime.now().strftime('%Y/%m/%d')
        unique_id = str(uuid.uuid4())
        
        # Determine file extension from content type
        file_extension = "m4a"  # default
        if "webm" in request.content_type.lower():
            file_extension = "webm"
        elif "mp4" in request.content_type.lower():
            file_extension = "m4a"
        elif "mpeg" in request.content_type.lower() or "mp3" in request.content_type.lower():
            file_extension = "mp3"
        
        s3_key = f"visit-recordings/{timestamp}/pet-{pet.id}/{unique_id}.{file_extension}"
        
        # Create metadata with appointment info
        metadata = {
            "s3_key": s3_key,
            "s3_bucket": S3_BUCKET_NAME,
            "filename": request.filename,
            "content_type": request.content_type,
            "estimated_duration": request.estimated_duration_seconds,
            "uploaded_by": str(current_user.id),
            "upload_initiated_at": datetime.now().isoformat()
        }
        
        # Add appointment_id to metadata if provided
        if request.appointment_id:
            metadata["appointment_id"] = request.appointment_id
        
        # Create new visit record in NEW state
        visit = Visit(
            pet_id=pet.id,
            practice_id=current_user.practice_id if hasattr(current_user, 'practice_id') else None,
            vet_user_id=current_user.id,
            visit_date=appointment_date,  # Use appointment date, not datetime.now()
            full_text="",  # Will be populated after transcription
            audio_transcript_url=None,  # Will be set after upload completion
            state=VisitState.NEW.value,
            additional_data=metadata,
            created_by=current_user.id
        )
        
        db.add(visit)
        await db.commit()
        await db.refresh(visit)
        
        # Generate presigned POST URL for S3 upload
        s3_client = get_s3_client()
        
        # Generate presigned POST
        conditions = [
            {'bucket': S3_BUCKET_NAME},
            {'key': s3_key},
            {'Content-Type': request.content_type},
            ['content-length-range', 1, 104857600]  # 1 byte to 100MB
        ]
        
        presigned_post = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Fields={'Content-Type': request.content_type},
            Conditions=conditions,
            ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        
        return AudioUploadResponse(
            visit_id=str(visit.id),
            upload_url=presigned_post['url'],
            upload_fields=presigned_post['fields'],
            s3_key=s3_key,
            bucket=S3_BUCKET_NAME,
            expires_in=PRESIGNED_URL_EXPIRATION
        )
        
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate upload URL: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload initiation failed: {str(e)}"
        )


@router.post("/audio/upload/complete/{visit_id}")
async def complete_audio_upload(
    visit_id: str,
    request: AudioUploadCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> VisitTranscriptResponse:
    """
    Mark audio upload as complete and update visit record
    """
    try:
        visit_uuid = uuid.UUID(visit_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid visit ID format")
    
    # Get visit from database
    result = await db.execute(select(Visit).where(Visit.id == visit_uuid))
    visit = result.scalar_one_or_none()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    # Check if user can complete this upload
    if visit.created_by != current_user.id and current_user.role not in ["SYSTEM_ADMIN", "PRACTICE_ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only the uploading user or admin can complete this upload"
        )
    
    # Update visit with upload completion details
    s3_key = visit.additional_data.get('s3_key')
    bucket = visit.additional_data.get('s3_bucket', S3_BUCKET_NAME)
    
    # Generate final S3 URL
    audio_url = f"https://{bucket}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
    
    # Update visit record
    visit.audio_transcript_url = audio_url
    visit.state = VisitState.PROCESSING.value  # Ready for transcription
    
    # Update metadata with completion details
    updated_metadata = visit.additional_data.copy()
    updated_metadata.update({
        "upload_completed_at": datetime.now().isoformat(),
        "file_size_bytes": request.file_size_bytes,
        "duration_seconds": request.duration_seconds,
        "device_metadata": request.device_metadata or {}
    })
    visit.additional_data = updated_metadata
    visit.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(visit)
    
    return visit_to_transcript_response(visit)


@router.get("/audio/playback/{visit_id}")
async def get_audio_playback_url(
    visit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> AudioPlaybackResponse:
    """
    Generate presigned URL for audio playback
    """
    try:
        visit_uuid = uuid.UUID(visit_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid visit ID format")
    
    # Get visit from database
    result = await db.execute(select(Visit).where(Visit.id == visit_uuid))
    visit = result.scalar_one_or_none()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    # Check access to the pet
    await check_pet_access(str(visit.pet_id), current_user, db)
    
    # Check if audio exists - support both new and old formats
    s3_key = visit.additional_data.get('s3_key') or visit.additional_data.get('audio_s3_key')
    if not s3_key:
        raise HTTPException(
            status_code=404,
            detail="No S3 key found for this visit's audio file"
        )
    
    # Verify the file exists in S3 before generating presigned URL
    s3_client = get_s3_client()
    try:
        s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey' or error_code == '404':
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found in storage at key: {s3_key}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to verify audio file existence: {error_code}"
            )
    
    try:
        # Generate presigned URL for download
        s3_client = get_s3_client()
        
        # Determine content type based on file extension
        filename = visit.additional_data.get('filename') or visit.additional_data.get('audio_filename', 'recording.m4a')
        content_type = 'audio/mp4'  # M4A files should use audio/mp4 MIME type
        if filename.lower().endswith('.mp3'):
            content_type = 'audio/mpeg'
        elif filename.lower().endswith('.wav'):
            content_type = 'audio/wav'
        elif filename.lower().endswith('.m4a'):
            content_type = 'audio/mp4'
        
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET_NAME,
                'Key': s3_key,
                'ResponseContentType': content_type,
                'ResponseContentDisposition': f'inline; filename="{filename}"'
            },
            ExpiresIn=900  # 15 minutes for playback
        )
        
        return AudioPlaybackResponse(
            presigned_url=presigned_url,
            expires_in=900,
            visit_id=str(visit.id),
            filename=filename
        )
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchKey':
            raise HTTPException(
                status_code=404,
                detail=f"Audio file not found in storage at key: {s3_key}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate playback URL: {error_code}"
            )
