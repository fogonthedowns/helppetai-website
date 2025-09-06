import json
import boto3
import urllib.parse
import os
import uuid
from datetime import datetime

# Initialize AWS clients
s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')

def lambda_handler(event, context):
    """
    Lambda function to handle S3 audio file uploads and start transcription
    """
    
    try:
        # Parse S3 event
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = urllib.parse.unquote_plus(record['s3']['object']['key'], encoding='utf-8')
            
            print(f"Processing file: {key} from bucket: {bucket}")
            
            # Check if file is audio format we support
            if not is_supported_audio_format(key):
                print(f"Unsupported file format: {key}")
                continue
            
            # Start transcription job
            job_name = create_transcription_job(bucket, key)
            
            if job_name:
                print(f"Started transcription job: {job_name}")
            else:
                print(f"Failed to start transcription for: {key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Processing completed successfully')
        }
        
    except Exception as e:
        print(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

def is_supported_audio_format(file_key):
    """Check if the file format is supported (m4a, mp3)"""
    supported_formats = ['.m4a', '.mp3', '.wav', '.flac']
    return any(file_key.lower().endswith(fmt) for fmt in supported_formats)

def create_transcription_job(bucket, key):
    """Create AWS Transcribe job"""
    try:
        # Generate unique job name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = key.split('/')[-1].split('.')[0]  # Get filename without extension
        job_name = f"transcribe_{file_name}_{timestamp}_{str(uuid.uuid4())[:8]}"
        
        # S3 URI for the audio file
        media_uri = f"s3://{bucket}/{key}"
        
        # Determine media format
        if key.lower().endswith('.m4a'):
            media_format = 'm4a'
        elif key.lower().endswith('.mp3'):
            media_format = 'mp3'
        elif key.lower().endswith('.wav'):
            media_format = 'wav'
        elif key.lower().endswith('.flac'):
            media_format = 'flac'
        else:
            media_format = 'mp3'  # default
        
        # Output S3 bucket for transcription results
        output_bucket = os.environ.get('TRANSCRIPTION_OUTPUT_BUCKET', bucket)
        output_key = f"transcriptions/{file_name}_{timestamp}.json"
        
        # Start transcription job
        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': media_uri},
            MediaFormat=media_format,
            LanguageCode='en-US',  # Change as needed
            OutputBucketName=output_bucket,
            OutputKey=output_key,
            Settings={
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 10,
                'ShowAlternatives': True,
                'MaxAlternatives': 3
            },
            # Store original file key in job metadata for callback
            Tags=[
                {
                    'Key': 'OriginalFileKey',
                    'Value': key
                },
                {
                    'Key': 'OriginalBucket',
                    'Value': bucket
                }
            ]
        )
        
        return job_name
        
    except Exception as e:
        print(f"Error creating transcription job: {str(e)}")
        return None