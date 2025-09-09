"""
Webhook endpoints for external service integrations
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..database_pg import get_db_session
from ..models_pg.visit import Visit, VisitState
from ..config import settings
from ..utils.error_handling import log_endpoint_errors

logger = logging.getLogger(__name__)

router = APIRouter()


class TranscriptionWebhookPayload(BaseModel):
    """Payload structure from AWS Transcribe Lambda"""
    originalFileKey: str = Field(..., description="Original S3 file key")
    originalBucket: str = Field(..., description="Original S3 bucket name")
    jobName: str = Field(..., description="AWS Transcribe job name")
    transcriptText: str = Field(..., description="Extracted transcript text")
    fullTranscriptData: Dict[str, Any] = Field(..., description="Full AWS Transcribe response")
    timestamp: Optional[str] = Field(None, description="Processing timestamp")
    status: str = Field(..., description="Transcription status")


def verify_webhook_token(x_webhook_token: Optional[str] = Header(None)):
    """Verify webhook authentication token"""
    expected_token = getattr(settings, 'webhook_secret_token', None) or "HelpPetWebhook2024!"
    
    if not x_webhook_token:
        logger.warning("Webhook request missing X-Webhook-Token header")
        raise HTTPException(
            status_code=401,
            detail="Missing webhook authentication token"
        )
    
    if x_webhook_token != expected_token:
        logger.warning(f"Invalid webhook token provided: {x_webhook_token[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook authentication token"
        )
    
    return True


@router.post("/transcription/complete")
@log_endpoint_errors("webhook_transcription_complete")
async def handle_transcription_complete(
    payload: TranscriptionWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    _: bool = Depends(verify_webhook_token)
):
    """
    Webhook endpoint to receive transcription completion notifications from AWS Lambda
    
    Requires X-Webhook-Token header for authentication
    
    This endpoint:
    1. Receives the transcription result from AWS Transcribe via Lambda
    2. Finds the corresponding Visit record based on the S3 file key
    3. Updates the Visit with the transcript text and status
    """
    try:
        logger.info(f"Received authenticated transcription webhook for file: {payload.originalFileKey}")
        
        # Extract visit ID from S3 file key
        # Expected format: visit-recordings/YYYY/MM/DD/pet-uuid/visit-uuid.m4a
        visit_id = extract_visit_id_from_s3_key(payload.originalFileKey)
        
        if not visit_id:
            logger.error(f"Could not extract visit ID from S3 key: {payload.originalFileKey}")
            raise HTTPException(
                status_code=400, 
                detail="Could not extract visit ID from file key"
            )
        
        # Find the visit record
        result = await db.execute(
            select(Visit).where(Visit.id == visit_id)
        )
        visit = result.scalar_one_or_none()
        
        if not visit:
            logger.error(f"Visit not found for ID: {visit_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Visit not found for ID: {visit_id}"
            )
        
        # Update visit with transcription data
        if payload.status.lower() == "completed":
            # Update visit record
            await db.execute(
                update(Visit)
                .where(Visit.id == visit_id)
                .values(
                    full_text=payload.transcriptText,
                    state=VisitState.PROCESSED.value,
                    additional_data={
                        **visit.additional_data,
                        "transcription_job_name": payload.jobName,
                        "transcription_completed_at": datetime.utcnow().isoformat(),
                        "transcript_full_data": payload.fullTranscriptData,
                        "transcription_source": "aws_transcribe"
                    },
                    updated_at=datetime.utcnow()
                )
            )
            
            await db.commit()
            
            logger.info(f"Successfully updated visit {visit_id} with transcription")
            
            return {
                "status": "success",
                "visit_id": str(visit_id),
                "message": "Transcription processed successfully"
            }
        else:
            # Mark as failed
            await db.execute(
                update(Visit)
                .where(Visit.id == visit_id)
                .values(
                    state=VisitState.FAILED.value,
                    additional_data={
                        **visit.additional_data,
                        "transcription_job_name": payload.jobName,
                        "transcription_failed_at": datetime.utcnow().isoformat(),
                        "transcription_error": f"Transcription status: {payload.status}",
                        "transcription_source": "aws_transcribe"
                    },
                    updated_at=datetime.utcnow()
                )
            )
            
            await db.commit()
            
            logger.error(f"Transcription failed for visit {visit_id}: {payload.status}")
            
            return {
                "status": "failed",
                "visit_id": str(visit_id),
                "message": f"Transcription failed: {payload.status}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing transcription webhook: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


def extract_visit_id_from_s3_key(s3_key: str) -> Optional[UUID]:
    """
    Extract visit UUID from S3 file key
    
    Expected format: visit-recordings/YYYY/MM/DD/pet-uuid/visit-uuid.m4a
    or: visit-recordings/YYYY/MM/DD/pet-uuid/recording-uuid.m4a
    
    The visit ID should be in the filename or we need to look it up by the S3 key
    """
    try:
        # Split the S3 key to get the filename
        parts = s3_key.split('/')
        if len(parts) < 2:
            return None
            
        # Get the filename (last part)
        filename = parts[-1]
        
        # Remove extension and try to extract UUID
        filename_without_ext = filename.rsplit('.', 1)[0]
        
        # Try to parse as UUID - this assumes the filename is the visit ID
        try:
            return UUID(filename_without_ext)
        except ValueError:
            # If filename is not a UUID, we need to look up by S3 key
            # This would require a database query to find the visit by audio_transcript_url
            logger.warning(f"Filename {filename_without_ext} is not a valid UUID, need to implement lookup by S3 key")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting visit ID from S3 key {s3_key}: {e}")
        return None


@router.post("/transcription/complete/by-s3-key")
@log_endpoint_errors("webhook_transcription_complete_s3")
async def handle_transcription_complete_by_s3_key(
    payload: TranscriptionWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    _: bool = Depends(verify_webhook_token)
):
    """
    Alternative webhook endpoint that finds visits by S3 key instead of filename
    Use this if the S3 filename is not the visit UUID
    
    Requires X-Webhook-Token header for authentication
    """
    try:
        logger.info(f"Received authenticated transcription webhook for S3 key: {payload.originalFileKey}")
        
        # Find visit by S3 key in audio_transcript_url
        # The upload code stores URLs in format: https://bucket.s3.region.amazonaws.com/key
        https_url = f"https://{payload.originalBucket}.s3.us-west-1.amazonaws.com/{payload.originalFileKey}"
        
        result = await db.execute(
            select(Visit).where(Visit.audio_transcript_url == https_url)
        )
        visit = result.scalar_one_or_none()
        
        if not visit:
            # Try with s3:// format as fallback
            s3_url = f"s3://{payload.originalBucket}/{payload.originalFileKey}"
            result = await db.execute(
                select(Visit).where(Visit.audio_transcript_url == s3_url)
            )
            visit = result.scalar_one_or_none()
        
        if not visit:
            # Try with simplified https format (without region)
            simple_https_url = f"https://{payload.originalBucket}.s3.amazonaws.com/{payload.originalFileKey}"
            result = await db.execute(
                select(Visit).where(Visit.audio_transcript_url == simple_https_url)
            )
            visit = result.scalar_one_or_none()
        
        if not visit:
            logger.error(f"Visit not found for S3 key: {payload.originalFileKey}")
            raise HTTPException(
                status_code=404,
                detail=f"Visit not found for S3 key: {payload.originalFileKey}"
            )
        
        # Update visit with transcription data (same logic as above)
        if payload.status.lower() == "completed":
            await db.execute(
                update(Visit)
                .where(Visit.id == visit.id)
                .values(
                    full_text=payload.transcriptText,
                    state=VisitState.PROCESSED.value,
                    additional_data={
                        **visit.additional_data,
                        "transcription_job_name": payload.jobName,
                        "transcription_completed_at": datetime.utcnow().isoformat(),
                        "transcript_full_data": payload.fullTranscriptData,
                        "transcription_source": "aws_transcribe"
                    },
                    updated_at=datetime.utcnow()
                )
            )
            
            await db.commit()
            
            logger.info(f"Successfully updated visit {visit.id} with transcription")
            
            return {
                "status": "success",
                "visit_id": str(visit.id),
                "message": "Transcription processed successfully"
            }
        else:
            # Mark as failed
            await db.execute(
                update(Visit)
                .where(Visit.id == visit.id)
                .values(
                    state=VisitState.FAILED.value,
                    additional_data={
                        **visit.additional_data,
                        "transcription_job_name": payload.jobName,
                        "transcription_failed_at": datetime.utcnow().isoformat(),
                        "transcription_error": f"Transcription status: {payload.status}",
                        "transcription_source": "aws_transcribe"
                    },
                    updated_at=datetime.utcnow()
                )
            )
            
            await db.commit()
            
            logger.error(f"Transcription failed for visit {visit.id}: {payload.status}")
            
            return {
                "status": "failed",
                "visit_id": str(visit.id),
                "message": f"Transcription failed: {payload.status}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing transcription webhook: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


class SOAPMetadataUpdatePayload(BaseModel):
    """Payload structure for SOAP metadata updates from Lambda"""
    visit_id: str = Field(..., description="Visit UUID to update")
    metadata: Dict[str, Any] = Field(..., description="SOAP metadata to merge with existing metadata")
    extraction_info: Optional[Dict[str, Any]] = Field(None, description="Information about the extraction process")


@router.put("/visit-metadata/{visit_id}")
@log_endpoint_errors("webhook_visit_metadata_update")
async def update_visit_metadata(
    visit_id: str,
    payload: SOAPMetadataUpdatePayload,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    _: bool = Depends(verify_webhook_token)
):
    """
    Webhook endpoint to update visit metadata (e.g., extracted SOAP data)
    
    Requires X-Webhook-Token header for authentication
    
    This endpoint:
    1. Receives metadata updates from external services (e.g., Lambda SOAP extractor)
    2. Finds the corresponding Visit record by UUID
    3. Merges the new metadata with existing additional_data
    """
    try:
        logger.info(f"Received authenticated metadata update webhook for visit: {visit_id}")
        
        # Try to parse as UUID first, if that fails, treat as S3 key
        visit = None
        try:
            visit_uuid = UUID(visit_id)
            # Find the visit record by UUID
            result = await db.execute(
                select(Visit).where(Visit.id == visit_uuid)
            )
            visit = result.scalar_one_or_none()
            logger.info(f"Looked up visit by UUID: {visit_id}")
        except ValueError:
            # Not a UUID, treat as S3 key and look up by audio_transcript_url
            logger.info(f"Visit ID not a UUID, treating as S3 key: {visit_id}")
            
            # Try different S3 URL formats
            s3_key = visit_id
            bucket_name = "helppetai-visit-recordings"  # From your CloudFormation template
            
            # Format 1: https://bucket.s3.region.amazonaws.com/key
            https_url = f"https://{bucket_name}.s3.us-west-1.amazonaws.com/{s3_key}"
            result = await db.execute(
                select(Visit).where(Visit.audio_transcript_url == https_url)
            )
            visit = result.scalar_one_or_none()
            
            if not visit:
                # Format 2: s3://bucket/key
                s3_url = f"s3://{bucket_name}/{s3_key}"
                result = await db.execute(
                    select(Visit).where(Visit.audio_transcript_url == s3_url)
                )
                visit = result.scalar_one_or_none()
            
            if not visit:
                # Format 3: https://bucket.s3.amazonaws.com/key (without region)
                simple_https_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
                result = await db.execute(
                    select(Visit).where(Visit.audio_transcript_url == simple_https_url)
                )
                visit = result.scalar_one_or_none()
        
        if not visit:
            logger.error(f"Visit not found for ID/S3 key: {visit_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Visit not found for ID: {visit_id}"
            )
        
        # Merge the new metadata with existing additional_data
        existing_data = visit.additional_data or {}
        updated_metadata = {**existing_data, **payload.metadata}
        
        # Add extraction information if provided
        if payload.extraction_info:
            updated_metadata["extraction_info"] = payload.extraction_info
        
        # Add timestamp for this metadata update
        updated_metadata["metadata_last_updated"] = datetime.utcnow().isoformat()
        
        # Update the visit record
        await db.execute(
            update(Visit)
            .where(Visit.id == visit_uuid)
            .values(
                additional_data=updated_metadata,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        
        logger.info(f"Successfully updated visit {visit_id} metadata with {len(payload.metadata)} fields")
        
        return {
            "status": "success",
            "visit_id": str(visit_uuid),
            "message": "Metadata updated successfully",
            "updated_fields": list(payload.metadata.keys()),
            "total_metadata_fields": len(updated_metadata)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing metadata update webhook: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/transcription/health")
async def webhook_health_check():
    """Health check endpoint for webhook service (no auth required)"""
    return {
        "status": "healthy",
        "service": "transcription_webhook",
        "timestamp": datetime.utcnow().isoformat()
    }