import json
import boto3
import requests
import os
from urllib.parse import urlparse

# Initialize AWS clients
transcribe_client = boto3.client('transcribe')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    Lambda function to handle AWS Transcribe job completion events
    and POST results to specified endpoint
    """
    
    try:
        # Parse CloudWatch event for Transcribe job completion
        detail = event.get('detail', {})
        job_name = detail.get('TranscriptionJobName')
        job_status = detail.get('TranscriptionJobStatus')
        
        print(f"Processing transcription job: {job_name}, Status: {job_status}")
        
        if job_status != 'COMPLETED':
            print(f"Job not completed successfully: {job_status}")
            return {
                'statusCode': 200,
                'body': json.dumps(f'Job status: {job_status}')
            }
        
        # Get transcription job details
        job_response = transcribe_client.get_transcription_job(
            TranscriptionJobName=job_name
        )
        
        job_info = job_response['TranscriptionJob']
        transcript_uri = job_info['Transcript']['TranscriptFileUri']
        
        # Get original file information from tags
        original_file_key = None
        original_bucket = None
        
        tags_response = transcribe_client.list_tags_for_resource(
            ResourceArn=job_info['TranscriptionJobArn']
        )
        
        for tag in tags_response.get('Tags', []):
            if tag['Key'] == 'OriginalFileKey':
                original_file_key = tag['Value']
            elif tag['Key'] == 'OriginalBucket':
                original_bucket = tag['Value']
        
        # Download and parse transcription result
        transcript_content = download_transcript(transcript_uri)
        
        if transcript_content:
            # POST to webhook endpoint
            webhook_success = post_to_webhook(
                original_file_key, 
                original_bucket,
                transcript_content,
                job_name
            )
            
            if webhook_success:
                print(f"Successfully posted results for job: {job_name}")
            else:
                print(f"Failed to post webhook for job: {job_name}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Transcription processing completed')
        }
        
    except Exception as e:
        print(f"Error processing transcription completion: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

def download_transcript(transcript_uri):
    """Download transcription results from S3"""
    try:
        # Parse S3 URI
        parsed_uri = urlparse(transcript_uri)
        bucket = parsed_uri.netloc
        key = parsed_uri.path.lstrip('/')
        
        # Download transcript file
        response = s3_client.get_object(Bucket=bucket, Key=key)
        transcript_json = json.loads(response['Body'].read().decode('utf-8'))
        
        return transcript_json
        
    except Exception as e:
        print(f"Error downloading transcript: {str(e)}")
        return None

def post_to_webhook(original_file_key, original_bucket, transcript_content, job_name):
    """POST transcription results to webhook endpoint"""
    try:
        # Get webhook URL from environment variable
        webhook_url = os.environ.get('WEBHOOK_ENDPOINT_URL')
        
        if not webhook_url:
            print("No webhook URL configured")
            return False
        
        # Extract transcript text
        transcript_text = ""
        if 'results' in transcript_content and 'transcripts' in transcript_content['results']:
            transcripts = transcript_content['results']['transcripts']
            if transcripts:
                transcript_text = transcripts[0].get('transcript', '')
        
        # Prepare payload
        payload = {
            'originalFileKey': original_file_key,
            'originalBucket': original_bucket,
            'jobName': job_name,
            'transcriptText': transcript_text,
            'fullTranscriptData': transcript_content,
            'timestamp': transcript_content.get('jobName', ''),
            'status': 'completed'
        }
        
        # Set headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add authentication if configured
        webhook_auth_header = os.environ.get('WEBHOOK_AUTH_HEADER')
        webhook_auth_value = os.environ.get('WEBHOOK_AUTH_VALUE')
        
        if webhook_auth_header and webhook_auth_value:
            headers[webhook_auth_header] = webhook_auth_value
        
        # POST request
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"Webhook POST successful: {response.status_code}")
            return True
        else:
            print(f"Webhook POST failed: {response.status_code}, {response.text}")
            return False
            
    except Exception as e:
        print(f"Error posting to webhook: {str(e)}")
        return False