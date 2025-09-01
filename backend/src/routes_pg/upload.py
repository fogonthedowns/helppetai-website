"""
Audio Upload REST API endpoints for S3
Handles visit transcript audio file uploads
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.jwt_auth_pg import get_current_user, User
from ..database_pg import get_db_session
from ..models_pg.visit import Visit, VisitState
from ..models_pg.appointment import Appointment, AppointmentPet, AppointmentStatus

router = APIRouter()

# S3 Configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'helppetai-visit-recordings')
S3_REGION = os.getenv('S3_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Presigned URL expiration (15 minutes)
PRESIGNED_URL_EXPIRATION = 900

def get_s3_client():
    """Get configured S3 client"""
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 credentials not configured"
        )
    
    return boto3.client(
        's3',
        region_name=S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

@router.post(
    "/audio",
    status_code=status.HTTP_201_CREATED,
    summary="Upload Audio File",
    description="Upload visit transcript audio file to S3 storage"
)
async def upload_audio_file(
    audio: UploadFile = File(..., description="Audio file to upload"),
    appointment_id: Optional[str] = Form(None, description="Appointment ID for visit recording"),
    pet_id: Optional[str] = Form(None, description="Specific pet ID for this recording"),
    bucket_name: Optional[str] = Form(None, description="S3 bucket name (optional)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Upload audio file to S3 bucket.
    Returns the S3 URL and key for the uploaded file.
    """
    
    # Validate file type
    if not audio.content_type or not audio.content_type.startswith('audio/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an audio file"
        )
    
    # Validate file size (max 100MB)
    max_size = 100 * 1024 * 1024  # 100MB
    if audio.size and audio.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum 100MB allowed."
        )
    
    try:
        # Handle appointment and pet validation
        appointment = None
        target_pet_id = None
        
        if appointment_id and pet_id:
            try:
                appointment_uuid = uuid.UUID(appointment_id)
                pet_uuid = uuid.UUID(pet_id)
                
                # Use async query
                from sqlalchemy import select
                appointment_result = await db.execute(
                    select(Appointment).where(Appointment.id == appointment_uuid)
                )
                appointment = appointment_result.scalar_one_or_none()
                
                if not appointment:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Appointment {appointment_id} not found"
                    )
                
                # Verify this pet is part of the appointment
                appointment_pet_result = await db.execute(
                    select(AppointmentPet).where(
                        AppointmentPet.appointment_id == appointment_uuid,
                        AppointmentPet.pet_id == pet_uuid
                    )
                )
                appointment_pet = appointment_pet_result.scalar_one_or_none()
                
                if not appointment_pet:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Pet {pet_id} is not associated with appointment {appointment_id}"
                    )
                
                target_pet_id = pet_uuid
                
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid appointment ID or pet ID format"
                )
        elif appointment_id or pet_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both appointment_id and pet_id are required for visit recording"
            )
        
        # Get S3 client
        s3_client = get_s3_client()
        
        # Use provided bucket name or default
        bucket = bucket_name or S3_BUCKET_NAME
        
        # Generate unique key for the file
        timestamp = datetime.now().strftime('%Y/%m/%d')
        unique_id = str(uuid.uuid4())
        # Force MP3 extension for consistency
        file_extension = '.mp3'
        
        # Include appointment info in S3 key if available
        if appointment:
            s3_key = f"visit-recordings/{timestamp}/appointment-{appointment.id}/{unique_id}{file_extension}"
        else:
            s3_key = f"visit-recordings/{timestamp}/{current_user.id}/{unique_id}{file_extension}"
        
        # Read file content
        file_content = await audio.read()
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=file_content,
            ContentType=audio.content_type,
            Metadata={
                'user_id': str(current_user.id),
                'uploaded_at': datetime.now().isoformat(),
                'original_filename': audio.filename or 'audio.webm'
            }
        )
        
        # Generate S3 URL
        s3_url = f"https://{bucket}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        
        # Create visit record for the specific pet if appointment and pet provided
        created_visit = None
        if appointment and target_pet_id:
            # Check if a visit already exists for this appointment and pet
            from sqlalchemy import select, and_
            existing_visit_result = await db.execute(
                select(Visit).where(
                    and_(
                        Visit.additional_data.op('->>')('appointment_id') == str(appointment.id),
                        Visit.pet_id == target_pet_id
                    )
                )
            )
            existing_visit = existing_visit_result.scalar_one_or_none()
            
            if existing_visit:
                # Visit already exists, return error
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Recording already exists for this appointment and pet. Visit ID: {existing_visit.id}"
                )
            
            visit = Visit(
                pet_id=target_pet_id,
                practice_id=appointment.practice_id,
                vet_user_id=current_user.id,
                visit_date=appointment.appointment_date,
                full_text="",  # Will be populated when transcription is processed
                audio_transcript_url=s3_url,
                state=VisitState.NEW.value,
                additional_data={
                    "appointment_id": str(appointment.id),
                    "audio_s3_key": s3_key,
                    "audio_filename": audio.filename or f"recording-{unique_id}.mp3",
                    "recorded_by": str(current_user.id),
                    "file_size": len(file_content)
                },
                created_by=current_user.id
            )
            db.add(visit)
            
            # Commit the visit record
            await db.commit()
            
            # Refresh to get ID
            await db.refresh(visit)
            created_visit = visit
            
            # Update appointment status to complete
            if appointment:
                appointment.status = AppointmentStatus.COMPLETE.value
                appointment.updated_at = datetime.utcnow()
                await db.commit()
                await db.refresh(appointment)
        
        response_content = {
            "success": True,
            "message": "Audio file uploaded successfully",
            "url": s3_url,
            "key": s3_key,
            "bucket": bucket,
            "size": len(file_content),
            "content_type": "audio/mpeg"  # Changed to MP3
        }
        
        # Add visit information if created
        if created_visit:
            response_content["visit_created"] = {
                "visit_id": str(created_visit.id),
                "pet_id": str(created_visit.pet_id),
                "state": created_visit.state,
                "appointment_id": str(appointment.id) if appointment else None
            }
            response_content["message"] = f"Audio uploaded and visit record created for pet {created_visit.pet_id}"
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_content
        )
        
    except NoCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AWS credentials not found"
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 bucket '{bucket}' does not exist"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 upload failed: {str(e)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="Check Upload Service Status",
    description="Check if S3 upload service is properly configured"
)
async def check_upload_status():
    """
    Check if the upload service is properly configured.
    """
    try:
        # Check if credentials are available
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "configured": False,
                    "message": "S3 credentials not configured",
                    "bucket": S3_BUCKET_NAME,
                    "region": S3_REGION
                }
            )
        
        # Try to create S3 client and list buckets (basic connectivity test)
        s3_client = get_s3_client()
        s3_client.list_buckets()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "configured": True,
                "message": "S3 upload service is configured and accessible",
                "bucket": S3_BUCKET_NAME,
                "region": S3_REGION
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "configured": False,
                "message": f"S3 configuration error: {str(e)}",
                "bucket": S3_BUCKET_NAME,
                "region": S3_REGION
            }
        )


@router.get(
    "/audio/{visit_id}/presigned-url",
    summary="Get Presigned URL for Audio Playback",
    description="Generate a secure, temporary URL for audio playback"
)
async def get_audio_presigned_url(
    visit_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate a presigned URL for secure audio playback.
    Only authenticated users can access visit audio.
    """
    
    try:
        # Validate visit ID format
        visit_uuid = uuid.UUID(visit_id)
        
        # Get visit record from database
        from sqlalchemy import select
        visit_result = await db.execute(
            select(Visit).where(Visit.id == visit_uuid)
        )
        visit = visit_result.scalar_one_or_none()
        
        if not visit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Visit {visit_id} not found"
            )
        
        # Check if user has access to this visit
        # For now, any authenticated user can access any visit
        # TODO: Add proper authorization based on practice/user relationship
        
        # Extract S3 key from additional_data
        s3_key = visit.additional_data.get('audio_s3_key')
        if not s3_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No audio file found for this visit"
            )
        
        # Generate presigned URL
        s3_client = get_s3_client()
        
        try:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': S3_BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=PRESIGNED_URL_EXPIRATION
            )
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "presigned_url": presigned_url,
                    "expires_in": PRESIGNED_URL_EXPIRATION,
                    "visit_id": str(visit.id),
                    "audio_filename": visit.additional_data.get('audio_filename', 'recording.mp3')
                }
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Audio file not found in storage"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate presigned URL: {error_code}"
                )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid visit ID format"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )
