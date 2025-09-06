"""
AWS Lambda function to handle AWS Transcribe job completion events
and POST results to the HelpPet API webhook endpoint
"""

import json
import boto3
import requests
import os
from urllib.parse import urlparse
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
transcribe_client = boto3.client('transcribe')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function to handle AWS Transcribe job completion events
    and POST results to specified endpoint
    
    Triggered by EventBridge when AWS Transcribe job status changes to COMPLETED or FAILED
    """
    
    try:
        logger.info(f"Processing transcribe completion event: {json.dumps(event, default=str)}")
        
        # Parse CloudWatch event for Transcribe job completion
        detail = event.get('detail', {})
        job_name = detail.get('TranscriptionJobName')
        job_status = detail.get('TranscriptionJobStatus')
        
        logger.info(f"Processing transcription job: {job_name}, Status: {job_status}")
        
        if not job_name:
            logger.error("No TranscriptionJobName found in event")
            return {
                'statusCode': 400,
                'body': json.dumps('No job name found in event')
            }
        
        # Get transcription job details
        job_response = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
        
        job_info = job_response['TranscriptionJob']
        
        # Get original file information from tags
        original_file_key = None
        original_bucket = None
        
        try:
            # Debug: log the job_info structure to see what keys are available
            logger.info(f"Job info keys: {list(job_info.keys())}")
            
            # Try to get ARN from response, or construct it if not present
            if 'TranscriptionJobArn' in job_info:
                job_arn = job_info['TranscriptionJobArn']
            else:
                # Get region and account from Lambda context
                import boto3
                sts = boto3.client('sts')
                account_id = sts.get_caller_identity()['Account']
                region = boto3.Session().region_name or 'us-west-1'
                job_arn = f"arn:aws:transcribe:{region}:{account_id}:transcription-job/{job_name}"
            
            logger.info(f"Using job ARN: {job_arn}")
            
            tags_response = transcribe_client.list_tags_for_resource(
                ResourceArn=job_arn
            )
            
            for tag in tags_response.get('Tags', []):
                if tag['Key'] == 'OriginalFileKey':
                    original_file_key = tag['Value']
                elif tag['Key'] == 'OriginalBucket':
                    original_bucket = tag['Value']
        except Exception as e:
            logger.error(f"Error retrieving tags for job {job_name}: {e}")
        
        if not original_file_key or not original_bucket:
            logger.error(f"Could not retrieve original file information for job {job_name}")
            return {
                'statusCode': 400,
                'body': json.dumps('Could not retrieve original file information')
            }
        
        # Process based on job status
        if job_status == 'COMPLETED':
            # Get transcript from our own bucket instead of AWS managed bucket
            output_bucket = os.environ.get('TRANSCRIPTION_OUTPUT_BUCKET', original_bucket)
            transcript_key = f'transcripts/{job_name}.json'
            transcript_content = download_transcript_from_s3(output_bucket, transcript_key)
            
            if transcript_content:
                # POST to webhook endpoint
                webhook_success = post_to_webhook(
                    original_file_key, 
                    original_bucket,
                    transcript_content,
                    job_name,
                    status='completed'
                )
                
                if webhook_success:
                    logger.info(f"Successfully posted transcription results for job: {job_name}")
                    return {
                        'statusCode': 200,
                        'body': json.dumps('Transcription processing completed successfully')
                    }
                else:
                    logger.error(f"Failed to post webhook for job: {job_name}")
                    return {
                        'statusCode': 500,
                        'body': json.dumps('Failed to post webhook')
                    }
            else:
                logger.error(f"Failed to download transcript for job: {job_name}")
                return {
                    'statusCode': 500,
                    'body': json.dumps('Failed to download transcript')
                }
        
        elif job_status == 'FAILED':
            # Handle failed transcription
            failure_reason = job_info.get('FailureReason', 'Unknown failure')
            logger.error(f"Transcription job {job_name} failed: {failure_reason}")
            
            # Post failure status to webhook
            webhook_success = post_to_webhook(
                original_file_key,
                original_bucket,
                {},
                job_name,
                status='failed',
                error_message=failure_reason
            )
            
            if webhook_success:
                logger.info(f"Successfully posted failure notification for job: {job_name}")
            else:
                logger.error(f"Failed to post failure webhook for job: {job_name}")
            
            return {
                'statusCode': 200,
                'body': json.dumps(f'Transcription job failed: {failure_reason}')
            }
        
        else:
            logger.info(f"Job {job_name} status {job_status} - no action needed")
            return {
                'statusCode': 200,
                'body': json.dumps(f'Job status: {job_status} - no action needed')
            }
        
    except Exception as e:
        logger.error(f"Error processing transcription completion: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

def download_transcript_from_s3(bucket, key):
    """Download transcription results from our controlled S3 bucket"""
    try:
        logger.info(f"Downloading transcript from: s3://{bucket}/{key}")
        
        # Download transcript file
        response = s3_client.get_object(Bucket=bucket, Key=key)
        transcript_json = json.loads(response['Body'].read().decode('utf-8'))
        
        logger.info("Transcript downloaded successfully")
        return transcript_json
        
    except Exception as e:
        logger.error(f"Error downloading transcript from s3://{bucket}/{key}: {str(e)}")
        return None

def download_transcript(transcript_uri):
    """Download transcription results from S3 URI (legacy function)"""
    try:
        logger.info(f"Downloading transcript from: {transcript_uri}")
        
        # Parse S3 URI
        parsed_uri = urlparse(transcript_uri)
        bucket = parsed_uri.netloc
        key = parsed_uri.path.lstrip('/')
        
        # Download transcript file
        response = s3_client.get_object(Bucket=bucket, Key=key)
        transcript_json = json.loads(response['Body'].read().decode('utf-8'))
        
        logger.info("Transcript downloaded successfully")
        return transcript_json
        
    except Exception as e:
        logger.error(f"Error downloading transcript from {transcript_uri}: {str(e)}")
        return None

def post_to_webhook(original_file_key, original_bucket, transcript_content, job_name, status='completed', error_message=None):
    """POST transcription results to webhook endpoint"""
    try:
        # Get webhook URL from environment variable
        webhook_url = os.environ.get('WEBHOOK_ENDPOINT_URL')
        
        if not webhook_url:
            logger.error("No WEBHOOK_ENDPOINT_URL environment variable configured")
            return False
        
        # Extract transcript text
        transcript_text = ""
        if status == 'completed' and 'results' in transcript_content:
            results = transcript_content['results']
            if 'transcripts' in results and results['transcripts']:
                transcript_text = results['transcripts'][0].get('transcript', '')
        
        # Prepare payload
        payload = {
            'originalFileKey': original_file_key,
            'originalBucket': original_bucket,
            'jobName': job_name,
            'transcriptText': transcript_text,
            'fullTranscriptData': transcript_content,
            'timestamp': transcript_content.get('jobName', ''),
            'status': status
        }
        
        # Add error information if failed
        if error_message:
            payload['errorMessage'] = error_message
        
        # Set headers including authentication token
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add webhook authentication token
        webhook_token = os.environ.get('WEBHOOK_SECRET_TOKEN')
        if webhook_token:
            headers['X-Webhook-Token'] = webhook_token
        else:
            logger.warning("No WEBHOOK_SECRET_TOKEN configured - webhook may fail authentication")
        
        logger.info(f"Posting to webhook: {webhook_url}")
        logger.info(f"Payload keys: {list(payload.keys())}")
        
        # POST request with timeout
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Webhook POST successful: {response.status_code}")
            logger.info(f"Webhook response: {response.text}")
            return True
        else:
            logger.error(f"Webhook POST failed: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"Webhook request timed out after 30 seconds")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook request error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error posting to webhook: {str(e)}")
        return False