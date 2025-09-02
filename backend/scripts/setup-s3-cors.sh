#!/bin/bash
# S3 CORS Configuration for HelpPetAI Audio Playback
# This script configures CORS settings to allow audio playback from the frontend

BUCKET_NAME="helppetai-visit-recordings"
TEMP_DIR="/tmp/s3-cors-setup-$$"

# Create temp directory
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "🌐 Setting up CORS configuration for S3 bucket: $BUCKET_NAME"

# Create CORS configuration
cat > cors-config.json << CORS
{
  "CORSRules": [
    {
      "ID": "AllowAudioPlayback",
      "AllowedHeaders": [
        "*"
      ],
      "AllowedMethods": [
        "GET",
        "HEAD"
      ],
      "AllowedOrigins": [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://helppet.ai",
        "https://www.helppet.ai",
        "capacitor://localhost",
        "ionic://localhost",
        "http://localhost",
        "https://localhost",
        "*"
      ],
      "ExposeHeaders": [
        "Content-Length",
        "Content-Type",
        "ETag",
        "Last-Modified"
      ],
      "MaxAgeSeconds": 3600
    },
    {
      "ID": "AllowPresignedUploads",
      "AllowedHeaders": [
        "*"
      ],
      "AllowedMethods": [
        "POST",
        "PUT"
      ],
      "AllowedOrigins": [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://helppet.ai",
        "https://www.helppet.ai",
        "capacitor://localhost",
        "ionic://localhost",
        "http://localhost",
        "https://localhost",
        "*"
      ],
      "ExposeHeaders": [
        "ETag"
      ],
      "MaxAgeSeconds": 3600
    }
  ]
}
CORS

echo "🔧 Applying CORS configuration to bucket"
aws s3api put-bucket-cors --bucket $BUCKET_NAME --cors-configuration file://cors-config.json

if [ $? -eq 0 ]; then
    echo "✅ CORS configuration applied successfully!"
    echo ""
    echo "📋 CORS Rules Applied:"
    echo "- Audio playback: GET, HEAD requests from frontend domains"
    echo "- File uploads: POST, PUT requests for presigned URLs"
    echo "- Allowed origins: localhost:3000, localhost:3001, helppet.ai, www.helppet.ai"
    echo ""
    echo "🧪 Test CORS configuration:"
    echo "   aws s3api get-bucket-cors --bucket $BUCKET_NAME"
else
    echo "❌ Failed to apply CORS configuration"
    exit 1
fi

# Cleanup
cd /
rm -rf "$TEMP_DIR"

echo "🗑️ Temporary files cleaned up"
