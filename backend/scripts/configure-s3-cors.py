#!/usr/bin/env python3
"""
Configure S3 bucket CORS for audio playback
"""

import boto3
import json
import os
from botocore.exceptions import ClientError

def configure_s3_cors():
    """Configure CORS for the S3 bucket used for audio storage"""
    
    # Get S3 configuration from environment
    bucket_name = os.getenv('S3_BUCKET_NAME', 'helppetai-visit-recordings')
    aws_region = os.getenv('AWS_REGION', 'us-west-1')
    
    # Initialize S3 client
    try:
        s3_client = boto3.client('s3', region_name=aws_region)
    except Exception as e:
        print(f"Failed to initialize S3 client: {e}")
        return False
    
    # Load CORS configuration
    cors_config_path = os.path.join(os.path.dirname(__file__), '..', 's3-cors-config.json')
    try:
        with open(cors_config_path, 'r') as f:
            cors_configuration = json.load(f)
    except Exception as e:
        print(f"Failed to load CORS configuration: {e}")
        return False
    
    # Apply CORS configuration
    try:
        s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        print(f"Successfully configured CORS for bucket: {bucket_name}")
        
        # Verify the configuration
        response = s3_client.get_bucket_cors(Bucket=bucket_name)
        print("Current CORS configuration:")
        print(json.dumps(response['CORSRules'], indent=2))
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"Bucket {bucket_name} does not exist")
        else:
            print(f"Failed to configure CORS: {error_code} - {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Configuring S3 CORS for audio playback...")
    success = configure_s3_cors()
    if success:
        print("CORS configuration completed successfully!")
    else:
        print("CORS configuration failed!")
        exit(1)
