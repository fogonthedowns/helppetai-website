# Visit Transcript Recording Setup Guide

## Overview
The Visit Transcript Recording feature allows veterinarians to record audio during visits with offline-first capability and automatic S3 upload.

## Features
- ✅ **Offline Recording**: Records locally even without internet
- ✅ **High-Quality Audio**: WebM/Opus format with noise suppression
- ✅ **Pause/Resume**: Full recording control
- ✅ **Auto-Upload**: Syncs to S3 when internet is available
- ✅ **State Tracking**: Tracks upload status and local storage

## S3 Bucket Setup

### 1. Create S3 Bucket
```bash
# Using AWS CLI
aws s3 mb s3://helppetai-visit-recordings --region us-west-1
```

### 2. Configure Bucket Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowVisitRecordingUploads",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/helppetai-upload-user"
      },
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::helppetai-visit-recordings/*"
    }
  ]
}
```

### 3. Create IAM User
```bash
# Create user for uploads
aws iam create-user --user-name helppetai-upload-user

# Create access key
aws iam create-access-key --user-name helppetai-upload-user
```

### 4. Environment Variables

**Backend (.env)**:
```bash
S3_BUCKET_NAME=helppetai-visit-recordings
S3_REGION=us-west-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
```

**Frontend (.env.local)**:
```bash
REACT_APP_S3_BUCKET_NAME=helppetai-visit-recordings
REACT_APP_S3_REGION=us-west-1
REACT_APP_API_URL=http://localhost:8000
```

## Usage

### 1. Start Recording
- Navigate to dashboard
- Click "Start Visit" in Quick Actions
- Allow microphone permissions
- Click "Start Recording"

### 2. Recording Controls
- **Pause**: Temporarily stop recording
- **Resume**: Continue recording
- **Finish**: Complete recording and prepare for upload

### 3. Upload Process
- Recording is automatically saved locally
- Click "Upload Recording" to sync to S3
- Upload status is tracked and displayed
- Auto-redirects to dashboard on success

## File Storage

### Local Storage Format
```javascript
{
  "data": "data:audio/webm;base64,GkXf...", // Base64 audio data
  "timestamp": "2025-08-31T14:30:00.000Z",
  "appointmentId": "uuid-or-null",
  "userId": "user-uuid",
  "uploaded": false, // Upload status
  "s3Url": "https://bucket.s3.region.amazonaws.com/key", // After upload
  "s3Key": "visit-recordings/2025/08/31/user-id/uuid.webm" // S3 key
}
```

### S3 Key Structure
```
visit-recordings/
  └── YYYY/MM/DD/
      └── user-id/
          └── unique-id.webm
```

## API Endpoints

### Upload Audio
```
POST /api/v1/upload/audio
Content-Type: multipart/form-data

Form Data:
- audio: File (WebM audio blob)
- bucketName: String (optional)
```

### Check Upload Status
```
GET /api/v1/upload/status
```

## Routes

- `/visit-transcripts/record` - New recording
- `/visit-transcripts/record/:appointmentId` - Recording for specific appointment

## Browser Compatibility

- **Chrome/Edge**: Full support (WebM/Opus)
- **Firefox**: Full support (WebM/Opus)
- **Safari**: Partial support (may use different codec)

## Troubleshooting

### Microphone Permission Denied
- Check browser permissions
- Ensure HTTPS in production
- Try refreshing the page

### Upload Failures
- Check S3 credentials
- Verify bucket exists and permissions
- Check network connectivity
- Recording remains in localStorage for retry

### Audio Quality Issues
- Check microphone settings
- Ensure quiet environment
- Verify browser audio permissions

## Security Considerations

- Audio files contain sensitive medical information
- S3 bucket should have restricted access
- Consider encryption at rest
- Implement proper access controls
- Regular cleanup of old recordings
