import json
import boto3
import requests
import os
import uuid
import logging
from datetime import datetime
from anthropic import Anthropic
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class VeterinarySOAPExtractor:
    """
    Veterinary SOAP note extractor using Anthropic API
    Adapted from llm.py for Lambda environment
    """
    
    def __init__(self, api_key: str = None):
        if api_key:
            self.client = Anthropic(api_key=api_key)
        else:
            self.client = Anthropic()  # Uses ANTHROPIC_API_KEY env var

    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string (1 token ≈ 4 characters)"""
        return len(text) // 4

    def extract_transcript_text(self, file_content: str) -> str:
        """Extract clean transcript text from AWS transcription JSON"""
        try:
            if file_content.strip().startswith('{'):
                data = json.loads(file_content)
                transcript = data["results"]["transcripts"][0]["transcript"]
                logger.info(f"Extracted transcript from AWS JSON: {len(transcript)} characters")
                return transcript
            else:
                logger.info(f"Using plain text file: {len(file_content)} characters")
                return file_content
        except Exception as e:
            logger.warning(f"Error parsing JSON, using as plain text: {e}")
            return file_content

    def get_extraction_prompt(self) -> str:
        """Return veterinary extraction prompt for SOAP analysis"""
        return """Extract veterinary visit information from the transcript for SOAP analysis. Return ONLY valid JSON with the following structure:

{
  "visit": {
    "chief_complaint": "",
    "subjective": {
      "history_of_present_illness": "",
      "owner_observations": "",
      "duration_of_symptoms": "",
      "previous_treatment": "",
      "behavior_changes": "",
      "appetite_changes": "",
      "elimination_changes": ""
    },
    "objective": {
      "vital_signs": {
        "temperature": "",
        "heart_rate": "",
        "respiratory_rate": "",
        "blood_pressure": "",
        "mucous_membrane": "",
        "capillary_refill_time": ""
      },
      "physical_exam": {
        "weight": "",
        "body_condition_score": "",
        "pain_score": "",
        "hydration_status": "",
        "eyes": "",
        "ears": "",
        "oral_cavity": "",
        "skin_coat": "",
        "musculoskeletal": "",
        "cardiovascular": "",
        "respiratory": "",
        "gastrointestinal": "",
        "neurological": "",
        "lymph_nodes": ""
      },
      "diagnostic_tests": "",
      "test_results": ""
    },
    "assessment": {
      "primary_diagnosis": "",
      "differential_diagnoses": "",
      "prognosis": ""
    },
    "plan": {
      "treatment": "",
      "medications": [
        {
          "name": "",
          "dosage": "",
          "frequency": "",
          "duration": "",
          "route": ""
        }
      ],
      "follow_up": "",
      "client_education": ""
    }
  },
  "notes": ""
}

Rules:
- Use "Not mentioned" for missing or unclear information.
- Extract only explicitly stated information from the transcript.
- Include all clinical measurements with units.
- Ensure JSON is valid and well-structured.
- Do not infer or add information beyond the transcript.

Transcript: """

    def extract_soap_data(self, transcript: str, model: str = "claude-3-5-sonnet-latest") -> Dict[str, Any]:
        """Extract SOAP note data from veterinary transcript using Anthropic API"""
        try:
            prompt = self.get_extraction_prompt()
            input_text = prompt + transcript
            input_tokens = self.estimate_tokens(input_text)
            
            logger.info(f"Estimated input tokens: {input_tokens}")
            
            response = self.client.messages.create(
                model=model,
                max_tokens=1500,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": input_text
                    }
                ]
            )
            
            response_text = response.content[0].text
            output_tokens = self.estimate_tokens(response_text)
            logger.info(f"Estimated output tokens: {output_tokens}")
            
            # Parse JSON response
            try:
                extracted_data = json.loads(response_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    raise ValueError("No valid JSON found in response")
            
            # Add extraction metadata
            extracted_data["extraction_metadata"] = {
                "extracted_at": datetime.now().isoformat(),
                "model_used": model,
                "transcript_length": len(transcript),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "api_call_cost_usd": round((input_tokens / 1_000_000) * 3 + (output_tokens / 1_000_000) * 15, 6)
            }
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting SOAP data: {str(e)}")
            raise


def extract_visit_uuid_from_transcript_filename(filename: str) -> tuple:
    """
    Extract visit UUID by looking up the transcription job tags to get the original file path
    Expected filename format: helppet-transcribe-{job-info}-{timestamp}-{suffix}.json
    Original file format: visit-recordings/YYYY/MM/DD/pet-uuid/visit-uuid.m4a
    """
    try:
        logger.info(f"Attempting to extract visit UUID from transcript filename: {filename}")
        
        # Extract job name from filename (remove .json extension)
        job_name = filename.replace('.json', '')
        logger.info(f"Transcription job name: {job_name}")
        
        # Look up the transcription job to get the original file path from tags
        transcribe_client = boto3.client('transcribe')
        
        try:
            # Get job details and tags
            job_response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            logger.info(f"Job response keys: {list(job_response.keys())}")
            logger.info(f"TranscriptionJob keys: {list(job_response['TranscriptionJob'].keys()) if 'TranscriptionJob' in job_response else 'No TranscriptionJob key'}")
            
            # Build the ARN manually since it may not be in the response
            # ARN format: arn:aws:transcribe:region:account-id:transcription-job/job-name
            try:
                sts_client = boto3.client('sts')
                account_id = sts_client.get_caller_identity()['Account']
                region = transcribe_client.meta.region_name
                job_arn = f"arn:aws:transcribe:{region}:{account_id}:transcription-job/{job_name}"
            except Exception as sts_error:
                logger.error(f"Failed to get account ID from STS: {sts_error}")
                return None, None
            
            logger.info(f"Using constructed ARN: {job_arn}")
            
            tags_response = transcribe_client.list_tags_for_resource(
                ResourceArn=job_arn
            )
            
            # Find the OriginalFileKey tag
            original_file_key = None
            for tag in tags_response.get('Tags', []):
                if tag['Key'] == 'OriginalFileKey':
                    original_file_key = tag['Value']
                    break
                    
            if not original_file_key:
                logger.error(f"No OriginalFileKey tag found for job {job_name}")
                return None, None
                
            logger.info(f"Found original file key: {original_file_key}")
            
            # Extract visit UUID from original file path
            # Expected format: visit-recordings/YYYY/MM/DD/pet-uuid/visit-uuid.m4a
            path_parts = original_file_key.split('/')
            if len(path_parts) >= 2:
                # Get the filename part (visit-uuid.m4a) and remove extension
                filename_part = path_parts[-1]
                visit_uuid = filename_part.split('.')[0]  # Remove extension
                
                # Validate it's a proper UUID
                uuid.UUID(visit_uuid)
                logger.info(f"Successfully extracted and validated visit UUID: {visit_uuid}")
                logger.info(f"Original file key: {original_file_key}")
                return visit_uuid, original_file_key
            else:
                logger.error(f"Unexpected original file path format: {original_file_key}")
                return None, None
                
        except Exception as e:
            logger.error(f"Failed to look up transcription job {job_name}: {e}")
            return None, None
            
    except Exception as e:
        logger.error(f"Error extracting visit UUID from filename {filename}: {e}")
        return None, None


def flatten_soap_data(extracted_data: dict) -> dict:
    """Flatten SOAP data into key/value pairs for frontend consumption"""
    flattened = {}
    
    visit = extracted_data.get('visit', {})
    
    # Add chief complaint
    if visit.get('chief_complaint'):
        flattened['chief_complaint'] = visit['chief_complaint']
    
    # Flatten subjective data
    subjective = visit.get('subjective', {})
    for key, value in subjective.items():
        if value and value != "Not mentioned":
            flattened[f'subjective_{key}'] = value
    
    # Flatten objective data - vital signs
    vital_signs = visit.get('objective', {}).get('vital_signs', {})
    for key, value in vital_signs.items():
        if value and value != "Not mentioned":
            flattened[f'vital_signs_{key}'] = value
    
    # Flatten objective data - physical exam
    physical_exam = visit.get('objective', {}).get('physical_exam', {})
    for key, value in physical_exam.items():
        if value and value != "Not mentioned":
            flattened[f'physical_exam_{key}'] = value
    
    # Add diagnostic tests and results
    objective = visit.get('objective', {})
    if objective.get('diagnostic_tests') and objective['diagnostic_tests'] != "Not mentioned":
        flattened['diagnostic_tests'] = objective['diagnostic_tests']
    if objective.get('test_results') and objective['test_results'] != "Not mentioned":
        flattened['test_results'] = objective['test_results']
    
    # Flatten assessment
    assessment = visit.get('assessment', {})
    for key, value in assessment.items():
        if value and value != "Not mentioned":
            flattened[f'assessment_{key}'] = value
    
    # Flatten plan
    plan = visit.get('plan', {})
    if plan.get('treatment') and plan['treatment'] != "Not mentioned":
        flattened['treatment'] = plan['treatment']
    if plan.get('follow_up') and plan['follow_up'] != "Not mentioned":
        flattened['follow_up'] = plan['follow_up']
    if plan.get('client_education') and plan['client_education'] != "Not mentioned":
        flattened['client_education'] = plan['client_education']
    
    # Handle medications separately
    medications = plan.get('medications', [])
    if medications:
        for i, med in enumerate(medications):
            if med.get('name') and med['name'] != "Not mentioned":
                flattened[f'medication_{i+1}_name'] = med.get('name', '')
                flattened[f'medication_{i+1}_dosage'] = med.get('dosage', '')
                flattened[f'medication_{i+1}_frequency'] = med.get('frequency', '')
                flattened[f'medication_{i+1}_duration'] = med.get('duration', '')
                flattened[f'medication_{i+1}_route'] = med.get('route', '')
    
    # Add notes if present
    if extracted_data.get('notes'):
        flattened['notes'] = extracted_data['notes']
    
    # Add extraction metadata
    if extracted_data.get('extraction_metadata'):
        metadata = extracted_data['extraction_metadata']
        flattened['extraction_date'] = metadata.get('extracted_at', '')
        flattened['extraction_model'] = metadata.get('model_used', '')
        flattened['extraction_cost'] = str(metadata.get('api_call_cost_usd', ''))
        flattened['transcript_length'] = str(metadata.get('transcript_length', ''))
    
    return flattened


def call_webhook_endpoint(visit_uuid: str, metadata: dict) -> dict:
    """Call the webhook endpoint to update visit metadata"""
    api_base_url = os.getenv('API_BASE_URL', 'https://api.helppet.ai')
    webhook_token = os.getenv('API_TOKEN')
    
    if not webhook_token:
        raise ValueError("API_TOKEN environment variable not set")
    
    url = f"{api_base_url}/api/v1/webhook/visit-metadata/{visit_uuid}"
    
    headers = {
        'X-Webhook-Token': webhook_token,
        'Content-Type': 'application/json'
    }
    
    # Webhook payload format
    payload = {
        "visit_id": visit_uuid,
        "metadata": metadata,
        "extraction_info": {
            "source": "lambda_soap_extractor",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    logger.info(f"Calling webhook: PUT {url}")
    logger.info(f"Updating metadata with {len(metadata)} key/value pairs")
    
    response = requests.put(url, json=payload, headers=headers)
    
    if response.status_code not in [200, 201]:
        logger.error(f"Webhook call failed: {response.status_code} - {response.text}")
        raise Exception(f"Webhook call failed: {response.status_code} - {response.text}")
    
    return response.json()


def lambda_handler(event, context):
    """
    Lambda handler for processing new transcript files from S3
    Triggered when a new file is added to the transcripts/ folder
    """
    
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Initialize SOAP extractor
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        extractor = VeterinarySOAPExtractor(api_key=anthropic_api_key)
        
        # Process each S3 event record
        for record in event.get('Records', []):
            try:
                # Extract S3 event information
                bucket_name = record['s3']['bucket']['name']
                object_key = record['s3']['object']['key']
                
                logger.info(f"Processing file: s3://{bucket_name}/{object_key}")
                
                # Verify this is a transcript file
                if not object_key.startswith('transcripts/') or not object_key.endswith('.json'):
                    logger.info(f"Skipping non-transcript file: {object_key}")
                    continue
                
                # Extract UUID and original file key from filename
                filename = object_key.split('/')[-1]
                transcript_uuid, original_file_key = extract_visit_uuid_from_transcript_filename(filename)
                
                if not transcript_uuid or not original_file_key:
                    logger.error(f"Could not extract UUID or original file key from filename: {filename}")
                    continue
                
                logger.info(f"Processing transcript UUID: {transcript_uuid}")
                logger.info(f"Original file key: {original_file_key}")
                
                # Download the transcript file from S3
                response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
                file_content = response['Body'].read().decode('utf-8')
                
                # Extract transcript text
                transcript_text = extractor.extract_transcript_text(file_content)
                
                logger.info(f"Extracted transcript text length: {len(transcript_text)}")
                
                # Extract SOAP data using Anthropic
                logger.info("Calling Anthropic API for SOAP extraction...")
                extracted_data = extractor.extract_soap_data(transcript_text)
                
                # Flatten SOAP data into key/value pairs
                flattened_metadata = flatten_soap_data(extracted_data)
                
                # Call the webhook endpoint to update metadata using original S3 key
                logger.info(f"Calling webhook to update visit metadata using S3 key: {original_file_key}")
                api_response = call_webhook_endpoint(original_file_key, flattened_metadata)
                
                logger.info(f"Successfully processed transcript {transcript_uuid}")
                
            except Exception as record_error:
                logger.error(f"Error processing record: {str(record_error)}")
                continue
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Transcript processing completed',
                'processed_records': len(event.get('Records', []))
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Transcript processing failed'
            })
        }