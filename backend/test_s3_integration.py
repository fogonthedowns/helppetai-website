#!/usr/bin/env python3
"""
Test script for S3 integration
Run this to verify S3 service is working correctly
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.s3_service import s3_service
from src.config import settings

async def test_s3_integration():
    """Test S3 service functionality"""
    
    print("🧪 Testing HelpPet S3 Integration")
    print("=" * 50)
    
    # Test 1: Generate recording key
    print("\n1. Testing S3 key generation...")
    try:
        s3_key = s3_service.generate_recording_key(
            user_id="test-user-123",
            appointment_id="test-appointment-456",
            file_extension="m4a"
        )
        print(f"✅ Generated S3 key: {s3_key}")
    except Exception as e:
        print(f"❌ Failed to generate S3 key: {e}")
        return False
    
    # Test 2: Generate presigned upload URL
    print("\n2. Testing presigned upload URL generation...")
    try:
        upload_data = s3_service.generate_presigned_upload_url(
            s3_key=s3_key,
            content_type="audio/m4a"
        )
        print(f"✅ Generated presigned URL")
        print(f"   Bucket: {upload_data['bucket']}")
        print(f"   Expires in: {upload_data['expires_in']} seconds")
        print(f"   Max file size: {upload_data['max_file_size']} bytes")
    except Exception as e:
        print(f"❌ Failed to generate presigned URL: {e}")
        return False
    
    # Test 3: Generate presigned download URL
    print("\n3. Testing presigned download URL generation...")
    try:
        download_url = s3_service.generate_presigned_download_url(
            s3_key=s3_key,
            expires_in=3600
        )
        print(f"✅ Generated presigned download URL")
        print(f"   URL length: {len(download_url)} characters")
    except Exception as e:
        print(f"❌ Failed to generate presigned download URL: {e}")
        return False
    
    # Test 4: Check file exists (should return False for test key)
    print("\n4. Testing file existence check...")
    try:
        exists = s3_service.check_file_exists(s3_key)
        print(f"✅ File existence check: {exists} (expected: False)")
    except Exception as e:
        print(f"❌ Failed to check file existence: {e}")
        return False
    
    # Test 5: Get public URL
    print("\n5. Testing public URL generation...")
    try:
        public_url = s3_service.get_public_url(s3_key)
        print(f"✅ Generated public URL: {public_url}")
    except Exception as e:
        print(f"❌ Failed to generate public URL: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All S3 integration tests passed!")
    print("\n📋 Configuration Summary:")
    print(f"   AWS Region: {settings.aws_region}")
    print(f"   S3 Bucket: {settings.s3_bucket_name}")
    print(f"   Recordings Prefix: {settings.s3_recordings_prefix}")
    print(f"   URL Expiration: {settings.s3_presigned_url_expiration}s")
    
    return True

def main():
    """Main test function"""
    
    print("🔧 HelpPet S3 Integration Test")
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Check environment
    print("\n🔍 Checking environment...")
    if not settings.s3_bucket_name:
        print("❌ S3_BUCKET_NAME not configured")
        return
    
    if not settings.aws_region:
        print("❌ AWS_REGION not configured")
        return
    
    print(f"✅ Environment configured")
    print(f"   Bucket: {settings.s3_bucket_name}")
    print(f"   Region: {settings.aws_region}")
    
    # Run async tests
    try:
        success = asyncio.run(test_s3_integration())
        if success:
            print("\n🚀 Ready for iPhone app integration!")
            print("\n📱 Next steps:")
            print("   1. Configure AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
            print("   2. Create S3 bucket: aws s3 mb s3://helppet-audio-recordings")
            print("   3. Configure bucket CORS policy")
            print("   4. Run database migration: make migrate")
            print("   5. Start the API server: make dev")
            print("   6. Test with iPhone app")
        else:
            print("\n❌ Some tests failed. Check AWS configuration.")
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")

if __name__ == "__main__":
    main()
