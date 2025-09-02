"""
AWS S3 Service for HelpPet Audio Recordings
Handles presigned URLs for secure direct uploads from mobile clients
"""

import boto3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for managing S3 operations for audio recordings"""
    
    def __init__(self):
        """Initialize S3 client with AWS credentials"""
        try:
            # Initialize S3 client
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region
                )
            else:
                # Use default credential chain (IAM roles, env vars, etc.)
                self.s3_client = boto3.client('s3', region_name=settings.aws_region)
                
            self.bucket_name = settings.s3_bucket_name
            self.recordings_prefix = settings.s3_recordings_prefix
            self.presigned_url_expiration = settings.s3_presigned_url_expiration
            
            logger.info(f"S3Service initialized for bucket: {self.bucket_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise
    
    def generate_recording_key(self, 
                             user_id: str, 
                             appointment_id: Optional[str] = None,
                             visit_id: Optional[str] = None,
                             file_extension: str = "m4a") -> str:
        """
        Generate a unique S3 key for a recording
        
        Args:
            user_id: ID of the user creating the recording
            appointment_id: Optional appointment ID
            visit_id: Optional visit ID
            file_extension: File extension (default: m4a for iOS)
            
        Returns:
            S3 key string
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # Create a hierarchical structure
        if appointment_id:
            context = f"appointment_{appointment_id}"
        elif visit_id:
            context = f"visit_{visit_id}"
        else:
            context = "general"
            
        filename = f"{timestamp}_{unique_id}.{file_extension}"
        s3_key = f"{self.recordings_prefix}{user_id}/{context}/{filename}"
        
        return s3_key
    
    def generate_presigned_upload_url(self, 
                                    s3_key: str,
                                    content_type: str = "audio/m4a",
                                    max_file_size: int = 100 * 1024 * 1024) -> Dict[str, Any]:
        """
        Generate a presigned URL for uploading a file to S3
        
        Args:
            s3_key: The S3 key where the file will be stored
            content_type: MIME type of the file
            max_file_size: Maximum file size in bytes (default: 100MB)
            
        Returns:
            Dictionary containing presigned URL and form fields
        """
        try:
            # Generate presigned POST URL
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields={
                    'Content-Type': content_type,
                    'x-amz-server-side-encryption': 'AES256'
                },
                Conditions=[
                    {'Content-Type': content_type},
                    {'x-amz-server-side-encryption': 'AES256'},
                    ['content-length-range', 1, max_file_size]
                ],
                ExpiresIn=self.presigned_url_expiration
            )
            
            logger.info(f"Generated presigned upload URL for key: {s3_key}")
            
            return {
                'upload_url': response['url'],
                'fields': response['fields'],
                's3_key': s3_key,
                'bucket': self.bucket_name,
                'expires_in': self.presigned_url_expiration,
                'max_file_size': max_file_size
            }
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {str(e)}")
            raise Exception(f"Failed to generate upload URL: {str(e)}")
    
    def generate_presigned_download_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for downloading a file from S3
        
        Args:
            s3_key: The S3 key of the file
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned download URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            
            logger.info(f"Generated presigned download URL for key: {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned download URL for {s3_key}: {str(e)}")
            raise Exception(f"Failed to generate download URL: {str(e)}")
    
    def check_file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3
        
        Args:
            s3_key: The S3 key to check
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking file existence for {s3_key}: {str(e)}")
                raise Exception(f"Error checking file: {str(e)}")
    
    def get_file_metadata(self, s3_key: str) -> Dict[str, Any]:
        """
        Get metadata for a file in S3
        
        Args:
            s3_key: The S3 key of the file
            
        Returns:
            Dictionary containing file metadata
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                'content_length': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', ''),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"Failed to get metadata for {s3_key}: {str(e)}")
            raise Exception(f"Failed to get file metadata: {str(e)}")
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3
        
        Args:
            s3_key: The S3 key of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted file: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file {s3_key}: {str(e)}")
            return False
    
    def get_public_url(self, s3_key: str) -> str:
        """
        Get the public URL for a file (if bucket allows public access)
        
        Args:
            s3_key: The S3 key of the file
            
        Returns:
            Public URL string
        """
        return f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"


# Global S3 service instance
s3_service = S3Service()
