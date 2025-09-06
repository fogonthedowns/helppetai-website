"""
AWS Lambda function to process audio files uploaded to S3
and start AWS Transcribe jobs
"""

import json
import boto3
import urllib.parse
import os
import uuid
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')

def lambda_handler(event, context):
    """
    Lambda function to handle S3 audio file uploads and start transcription
    
    Triggered by S3 ObjectCreated events for .m4a and .mp3 files
    """
    
    try:
        logger.info(f"Processing S3 event: {json.dumps(event, default=str)}")
        
        # Parse S3 event
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = urllib.parse.unquote_plus(record['s3']['object']['key'], encoding='utf-8')
            
            logger.info(f"Processing file: {key} from bucket: {bucket}")
            
            # Check if file is audio format we support
            if not is_supported_audio_format(key):
                logger.warning(f"Unsupported file format: {key}")
                continue
            
            # Start transcription job
            job_name = create_transcription_job(bucket, key)
            
            if job_name:
                logger.info(f"Started transcription job: {job_name} for file: {key}")
            else:
                logger.error(f"Failed to start transcription for: {key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Processing completed successfully',
                'processedFiles': len(event['Records'])
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

def is_supported_audio_format(file_key):
    """Check if the file format is supported by AWS Transcribe"""
    supported_formats = ['.m4a', '.mp3', '.wav', '.flac']
    return any(file_key.lower().endswith(fmt) for fmt in supported_formats)

def create_transcription_job(bucket, key):
    """Create AWS Transcribe job with proper configuration"""
    try:
        # Generate unique job name (must be unique across all AWS Transcribe jobs)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = key.split('/')[-1].split('.')[0]  # Get filename without extension
        random_suffix = str(uuid.uuid4())[:8]
        job_name = f"helppet-transcribe-{file_name}-{timestamp}-{random_suffix}"
        
        # S3 URI for the audio file
        media_uri = f"s3://{bucket}/{key}"
        
        # Determine media format based on file extension
        media_format = get_media_format(key)
        
        # Get output bucket from environment or use the same bucket as input
        output_bucket = os.environ.get('TRANSCRIPTION_OUTPUT_BUCKET', bucket)
        
        # Start transcription job with proper settings for medical transcription
        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': media_uri},
            MediaFormat=media_format,
            LanguageCode='en-US',
            OutputBucketName=output_bucket,
            OutputKey=f'transcripts/{job_name}.json',
            Settings={
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 10,  # Veterinarian + pet owner conversations
                'ShowAlternatives': True,
                'MaxAlternatives': 3
            },
            # Add tags to track the original file for webhook processing
            Tags=[
                {
                    'Key': 'OriginalFileKey',
                    'Value': key
                },
                {
                    'Key': 'OriginalBucket', 
                    'Value': bucket
                },
                {
                    'Key': 'Project',
                    'Value': 'HelpPetAI'
                },
                {
                    'Key': 'ProcessedAt',
                    'Value': datetime.utcnow().isoformat()
                }
            ]
        )
        
        logger.info(f"Transcription job created successfully: {job_name}")
        logger.info(f"Job details: {json.dumps(response, default=str)}")
        
        return job_name
        
    except Exception as e:
        logger.error(f"Error creating transcription job for {key}: {str(e)}")
        return None

def get_media_format(file_key):
    """Determine the media format based on file extension"""
    file_key_lower = file_key.lower()
    
    if file_key_lower.endswith('.m4a'):
        return 'm4a'
    elif file_key_lower.endswith('.mp3'):
        return 'mp3'
    elif file_key_lower.endswith('.wav'):
        return 'wav'
    elif file_key_lower.endswith('.flac'):
        return 'flac'
    else:
        # Default to mp3 if we can't determine
        logger.warning(f"Unknown file format for {file_key}, defaulting to mp3")
        return 'mp3'