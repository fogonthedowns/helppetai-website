# iPhone Audio Upload to S3 Integration

## Overview

This document describes the complete implementation of a robust AWS S3 audio upload system for the HelpPet iPhone app. The system orchestrates secure direct uploads from mobile clients to S3 while maintaining proper database records and API management.

## Architecture

```
iPhone App → HelpPet API → AWS S3
     ↓           ↓           ↓
  Recording   Database   Audio File
  Interface   Records    Storage
```

### Key Components

1. **S3 Service** (`src/services/s3_service.py`) - Manages AWS S3 operations
2. **Recording Model** (`src/models_pg/recording.py`) - Database model for recordings
3. **Recording Routes** (`src/routes_pg/recordings.py`) - API endpoints
4. **Database Migration** - New recordings table

## Database Schema

### Recordings Table

```sql
CREATE TABLE recordings (
    id UUID PRIMARY KEY,
    visit_id UUID REFERENCES visits(id),
    appointment_id UUID REFERENCES appointments(id),
    recorded_by_user_id UUID NOT NULL REFERENCES users(id),
    
    -- Recording metadata
    recording_type VARCHAR(50) NOT NULL DEFAULT 'visit_audio',
    status VARCHAR(20) NOT NULL DEFAULT 'uploading',
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_size_bytes INTEGER,
    duration_seconds FLOAT,
    mime_type VARCHAR(100),
    
    -- S3 information
    s3_bucket VARCHAR(100) NOT NULL,
    s3_key VARCHAR(500) NOT NULL,
    s3_url VARCHAR(1000),
    
    -- Transcription results
    transcript_text TEXT,
    transcript_confidence FLOAT,
    transcript_language VARCHAR(10),
    transcription_service VARCHAR(50),
    
    -- Processing metadata
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT,
    
    -- Additional metadata as JSON
    recording_metadata VARCHAR(2000),
    
    -- Soft delete
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by_user_id UUID REFERENCES users(id),
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Recording Status Flow

```
uploading → uploaded → processing → transcribed
     ↓           ↓           ↓           ↓
   Initial   S3 Upload   AI Processing  Complete
   State     Complete    Started       Success
                ↓           ↓
              failed     failed
```

## API Endpoints

### 1. Initiate Recording Upload

**POST** `/api/v1/recordings/upload/initiate`

Generates a presigned S3 URL for direct upload from the iPhone app.

**Request:**
```json
{
    "appointment_id": "uuid-string",
    "visit_id": "uuid-string",
    "recording_type": "visit_audio",
    "filename": "recording_20241219_143022.m4a",
    "content_type": "audio/m4a",
    "estimated_duration_seconds": 120.5
}
```

**Response:**
```json
{
    "recording_id": "uuid-string",
    "upload_url": "https://helppet-audio-recordings.s3.amazonaws.com/",
    "upload_fields": {
        "key": "recordings/user-id/appointment_uuid/20241219_143022_abc123.m4a",
        "Content-Type": "audio/m4a",
        "x-amz-server-side-encryption": "AES256",
        "policy": "base64-encoded-policy",
        "x-amz-credential": "...",
        "x-amz-algorithm": "AWS4-HMAC-SHA256",
        "x-amz-date": "...",
        "x-amz-signature": "..."
    },
    "s3_key": "recordings/user-id/appointment_uuid/20241219_143022_abc123.m4a",
    "bucket": "helppet-audio-recordings",
    "expires_in": 3600,
    "max_file_size": 104857600
}
```

### 2. Complete Recording Upload

**POST** `/api/v1/recordings/upload/complete/{recording_id}`

Marks the upload as complete and updates metadata.

**Request:**
```json
{
    "file_size_bytes": 2048576,
    "duration_seconds": 125.3,
    "recording_metadata": {
        "device_model": "iPhone 15 Pro",
        "ios_version": "17.2",
        "app_version": "1.0.0"
    }
}
```

### 3. Get Recordings

**GET** `/api/v1/recordings/`

Query parameters:
- `appointment_id` (optional)
- `visit_id` (optional) 
- `status` (optional)
- `limit` (default: 50)
- `offset` (default: 0)

### 4. Get Recording Details

**GET** `/api/v1/recordings/{recording_id}`

### 5. Get Download URL

**GET** `/api/v1/recordings/{recording_id}/download-url`

Generates a presigned download URL for playback.

### 6. Delete Recording

**DELETE** `/api/v1/recordings/{recording_id}`

Soft deletes the recording (marks as deleted but keeps the record).

## iPhone App Integration

### 1. Start Recording Flow

```swift
// 1. Start a visit
let visitId = startVisit(appointmentId: appointmentId)

// 2. Request recording permission
AVAudioSession.sharedInstance().requestRecordPermission { granted in
    if granted {
        // Show recording interface
        showRecordingInterface()
    } else {
        // Show permission denied message
        showPermissionDeniedAlert()
    }
}
```

### 2. Recording Interface

```swift
class RecordingViewController: UIViewController {
    @IBOutlet weak var recordButton: UIButton!
    @IBOutlet weak var durationLabel: UILabel!
    @IBOutlet weak var playButton: UIButton!
    @IBOutlet weak var uploadButton: UIButton!
    
    var audioRecorder: AVAudioRecorder?
    var audioPlayer: AVAudioPlayer?
    var recordingTimer: Timer?
    var recordingDuration: TimeInterval = 0
    
    @IBAction func recordButtonTapped(_ sender: UIButton) {
        if audioRecorder?.isRecording == true {
            stopRecording()
        } else {
            startRecording()
        }
    }
    
    @IBAction func uploadButtonTapped(_ sender: UIButton) {
        uploadRecording()
    }
}
```

### 3. Upload Process

```swift
func uploadRecording() {
    // 1. Initiate upload with HelpPet API
    let request = RecordingUploadRequest(
        appointmentId: appointmentId,
        visitId: visitId,
        recordingType: .visitAudio,
        filename: recordingFilename,
        contentType: "audio/m4a",
        estimatedDurationSeconds: recordingDuration
    )
    
    APIClient.shared.initiateRecordingUpload(request) { result in
        switch result {
        case .success(let response):
            // 2. Upload directly to S3 using presigned URL
            self.uploadToS3(response: response)
        case .failure(let error):
            self.showError(error)
        }
    }
}

func uploadToS3(response: RecordingUploadResponse) {
    let uploadRequest = S3UploadRequest(
        url: response.uploadUrl,
        fields: response.uploadFields,
        fileData: recordingData
    )
    
    S3Client.shared.upload(uploadRequest) { result in
        switch result {
        case .success:
            // 3. Mark upload as complete
            self.completeUpload(recordingId: response.recordingId)
        case .failure(let error):
            self.showError(error)
        }
    }
}

func completeUpload(recordingId: UUID) {
    let request = RecordingCompleteRequest(
        fileSizeBytes: recordingData.count,
        durationSeconds: recordingDuration,
        recordingMetadata: [
            "device_model": UIDevice.current.model,
            "ios_version": UIDevice.current.systemVersion,
            "app_version": Bundle.main.appVersion
        ]
    )
    
    APIClient.shared.completeRecordingUpload(recordingId, request) { result in
        switch result {
        case .success:
            self.showSuccess()
            self.dismiss(animated: true)
        case .failure(let error):
            self.showError(error)
        }
    }
}
```

## AWS Configuration

### S3 Bucket Setup

1. **Create S3 Bucket:**
```bash
aws s3 mb s3://helppet-audio-recordings --region us-east-1
```

2. **Configure CORS:**
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "POST", "PUT"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
```

3. **Set Bucket Policy:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPresignedUploads",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::helppet-audio-recordings/*",
            "Condition": {
                "StringEquals": {
                    "s3:x-amz-server-side-encryption": "AES256"
                }
            }
        }
    ]
}
```

### IAM Configuration

**IAM Policy for HelpPet Backend:**
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectVersion",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::helppet-audio-recordings",
                "arn:aws:s3:::helppet-audio-recordings/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListAllMyBuckets"
            ],
            "Resource": "*"
        }
    ]
}
```

## Environment Variables

Add to your `.env` file:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key

# S3 Configuration for Audio Recordings
S3_BUCKET_NAME=helppet-audio-recordings
S3_RECORDINGS_PREFIX=recordings/
S3_PRESIGNED_URL_EXPIRATION=3600
```

## Security Features

### 1. Presigned URLs
- Limited time expiration (1 hour default)
- Specific content type enforcement
- File size limits (100MB default)
- Server-side encryption required

### 2. Access Control
- User authentication required for all endpoints
- Users can only access their own recordings
- Appointment/visit ownership validation

### 3. File Organization
- Hierarchical S3 key structure: `recordings/{user_id}/{context}/{filename}`
- Unique filenames with timestamps and UUIDs
- Proper MIME type validation

## Error Handling

### Common Error Scenarios

1. **Upload Timeout:**
   - Presigned URL expires (1 hour)
   - Solution: Request new presigned URL

2. **File Size Exceeded:**
   - File larger than 100MB limit
   - Solution: Compress audio or split recording

3. **Network Failure:**
   - Upload interrupted
   - Solution: Retry mechanism with exponential backoff

4. **Permission Denied:**
   - User doesn't have access to appointment/visit
   - Solution: Verify user permissions

### Error Response Format

```json
{
    "message": "Upload failed",
    "error_code": "UPLOAD_TIMEOUT",
    "details": {
        "recording_id": "uuid-string",
        "s3_key": "recordings/...",
        "retry_after": 300
    }
}
```

## Future Enhancements

### 1. Automatic Transcription
- Integration with AWS Transcribe
- OpenAI Whisper API support
- Real-time transcription streaming

### 2. Audio Processing
- Noise reduction
- Audio compression
- Format conversion

### 3. Backup and Recovery
- Cross-region replication
- Automated backups
- Disaster recovery procedures

### 4. Analytics
- Upload success rates
- File size distributions
- Processing times

## Testing

### Unit Tests
- S3 service functionality
- Recording model validation
- API endpoint responses

### Integration Tests
- End-to-end upload flow
- Error handling scenarios
- Permission validation

### Load Testing
- Concurrent upload handling
- S3 rate limiting
- Database performance

## Monitoring

### CloudWatch Metrics
- S3 upload success/failure rates
- API response times
- Error rates by endpoint

### Application Logs
- Upload initiation events
- Completion confirmations
- Error details and stack traces

### Alerts
- High error rates
- Unusual upload patterns
- S3 bucket quota warnings

## Deployment Checklist

- [ ] S3 bucket created and configured
- [ ] IAM policies and roles set up
- [ ] Environment variables configured
- [ ] Database migration applied
- [ ] API endpoints tested
- [ ] iPhone app integration complete
- [ ] Monitoring and alerts configured
- [ ] Documentation updated

## API Testing Examples

### Using cURL

**1. Initiate Upload:**
```bash
curl -X POST "https://api.helppet.ai/api/v1/recordings/upload/initiate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "appointment_id": "123e4567-e89b-12d3-a456-426614174000",
    "recording_type": "visit_audio",
    "filename": "test_recording.m4a",
    "content_type": "audio/m4a"
  }'
```

**2. Complete Upload:**
```bash
curl -X POST "https://api.helppet.ai/api/v1/recordings/upload/complete/RECORDING_ID" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_size_bytes": 1024000,
    "duration_seconds": 60.5
  }'
```

This implementation provides a robust, secure, and scalable solution for iPhone audio uploads to AWS S3 while maintaining proper database records and API orchestration.
