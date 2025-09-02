# HelpPet.ai - Application Documentation

## Overview

HelpPet.ai is a comprehensive veterinary practice management system that streamlines the process of recording, transcribing, and managing veterinary visits. The application features a modern web interface for practice management and a mobile audio recording system designed specifically for iPhone users.

## What This Application Does

### Primary Purpose
HelpPet.ai helps veterinary professionals:
- **Record audio during pet visits** using iPhone devices with seamless cloud upload
- **Automatically transcribe conversations** between veterinarians and pet owners
- **Manage pet records and medical histories** across multiple veterinary practices  
- **Schedule and track appointments** with integrated visit recording capabilities
- **Store and share visit transcripts** securely in the cloud

### Key Features
- **Secure Audio Recording**: Direct iPhone-to-S3 upload with presigned URLs
- **One Recording Per Pet Per Day**: Simplified workflow preventing duplicate recordings
- **Automatic Transcription**: AI-powered speech-to-text processing
- **Multi-Practice Support**: Veterinary practices can collaborate and share pet histories
- **Role-Based Access**: Different permissions for admins, veterinarians, and pet owners
- **RESTful API**: Complete backend API for mobile and web applications

## Architecture

### System Components
- **Frontend**: React TypeScript application with responsive design
- **Backend**: FastAPI Python application with PostgreSQL database
- **Storage**: AWS S3 for audio file storage with presigned URL security
- **Authentication**: JWT-based authentication with role-based access control
- **Database**: PostgreSQL with async SQLAlchemy ORM

### Design Patterns
- **Repository Pattern**: Data access abstraction for PostgreSQL operations
- **Service Layer**: Business logic separation with dedicated service classes
- **RESTful API Design**: Consistent HTTP method usage and resource naming
- **Async Processing**: Non-blocking database and S3 operations throughout

## API Documentation

### Authentication
All API endpoints require JWT authentication via `Authorization: Bearer <token>` header.

#### POST `/api/v1/auth/login`
```json
{
  "username": "vet@example.com",
  "password": "password"
}
```
**Response:**
```json
{
  "access_token": "jwt-token-here",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "vet@example.com",
    "role": "VET"
  }
}
```

### Visit Transcripts (Core Audio Recording API)

#### POST `/api/v1/visit-transcripts/audio/upload/initiate`
**Purpose**: iPhone app requests presigned S3 upload URL for new audio recording

**Request:**
```json
{
  "pet_id": "uuid-string",
  "filename": "recording_20241219_143022.m4a",
  "content_type": "audio/m4a",
  "estimated_duration_seconds": 125.3
}
```

**Response:**
```json
{
  "visit_id": "uuid-string",
  "upload_url": "https://helppetai-visit-recordings.s3.amazonaws.com/",
  "upload_fields": {
    "key": "visit-recordings/2024/12/19/pet-uuid/unique-id.m4a",
    "Content-Type": "audio/m4a",
    "policy": "base64-encoded-policy",
    "x-amz-credential": "...",
    "x-amz-algorithm": "AWS4-HMAC-SHA256",
    "x-amz-date": "...",
    "x-amz-signature": "..."
  },
  "s3_key": "visit-recordings/2024/12/19/pet-uuid/unique-id.m4a",
  "bucket": "helppetai-visit-recordings",
  "expires_in": 3600
}
```

#### POST `/api/v1/visit-transcripts/audio/upload/complete/{visit_id}`
**Purpose**: Mark upload as complete after successful S3 upload

**Request:**
```json
{
  "file_size_bytes": 2048576,
  "duration_seconds": 125.3,
  "device_metadata": {
    "device_model": "iPhone 15 Pro",
    "ios_version": "17.2",
    "app_version": "1.0.0"
  }
}
```

**Response:**
```json
{
  "uuid": "visit-uuid",
  "pet_id": "pet-uuid", 
  "visit_date": 1703001234,
  "full_text": "",
  "audio_transcript_url": "https://bucket.s3.region.amazonaws.com/key",
  "state": "processing",
  "metadata": {
    "s3_key": "visit-recordings/...",
    "file_size_bytes": 2048576,
    "duration_seconds": 125.3
  }
}
```

#### GET `/api/v1/visit-transcripts/audio/playback/{visit_id}`
**Purpose**: Get presigned URL for audio playback

**Response:**
```json
{
  "presigned_url": "https://bucket.s3.amazonaws.com/key?X-Amz-Algorithm=...",
  "expires_in": 900,
  "visit_id": "uuid",
  "filename": "recording.m4a"
}
```

### Other Key Endpoints

#### GET `/api/v1/visit-transcripts/pet/{pet_uuid}`
List all visit transcripts for a specific pet

#### GET `/api/v1/visit-transcripts/{transcript_uuid}`  
Get detailed visit transcript information

#### POST `/api/v1/visit-transcripts`
Create a new visit transcript (for manual entry)

#### GET `/api/v1/pets`
List pets accessible to the current user

#### GET `/api/v1/appointments`
List appointments for the current user

## iPhone Audio Recording Flow

### Complete End-to-End Process

#### 1. Authentication
```swift
// iPhone app logs in and stores JWT token
let loginRequest = AuthRequest(username: "vet@example.com", password: "password")
let authResponse = await APIClient.login(loginRequest)
APIClient.setAuthToken(authResponse.access_token)
```

#### 2. Select Pet and Initiate Recording
```swift
// User selects pet from list and starts recording
let selectedPet = pets[indexPath.row]
let request = AudioUploadRequest(
    petId: selectedPet.id,
    filename: "recording_\(dateFormatter.string(from: Date())).m4a",
    contentType: "audio/m4a",
    estimatedDurationSeconds: nil
)

let uploadResponse = await APIClient.initiateAudioUpload(request)
```

#### 3. Record Audio and Upload to S3
```swift
// Record audio using AVAudioRecorder
let audioRecorder = AVAudioRecorder(url: localURL, settings: audioSettings)
audioRecorder.record()

// Stop recording and get audio data
audioRecorder.stop()
let audioData = try Data(contentsOf: localURL)

// Upload directly to S3 using presigned POST
let uploadSuccess = await S3Client.uploadFile(
    data: audioData,
    to: uploadResponse.uploadUrl,
    with: uploadResponse.uploadFields
)
```

#### 4. Mark Upload Complete
```swift
// Notify backend that upload is complete
let completeRequest = AudioUploadCompleteRequest(
    fileSizeBytes: audioData.count,
    durationSeconds: recordingDuration,
    deviceMetadata: [
        "device_model": UIDevice.current.model,
        "ios_version": UIDevice.current.systemVersion,
        "app_version": Bundle.main.appVersion
    ]
)

let visitTranscript = await APIClient.completeAudioUpload(
    visitId: uploadResponse.visitId,
    request: completeRequest
)
```

#### 5. Playback Audio (Later)
```swift
// Get presigned URL for playback
let playbackResponse = await APIClient.getAudioPlaybackUrl(visitId: visitId)

// Play audio using AVPlayer
let player = AVPlayer(url: URL(string: playbackResponse.presignedUrl)!)
player.play()
```

## Setup & Installation

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp env.template .env
# Edit .env with your database and AWS credentials
alembic upgrade head
python -m uvicorn main:app --reload
```

### Frontend Setup  
```bash
cd frontend
npm install
npm start
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/helppet
DATABASE_URL_SYNC=postgresql://user:pass@localhost/helppet

# AWS S3 
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key  
S3_BUCKET_NAME=helppetai-visit-recordings
S3_REGION=us-east-1

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Database Schema

### Core Tables
- **users**: Veterinarians, staff, pet owners, and admins
- **veterinary_practices**: Veterinary clinic information  
- **pets**: Pet information linked to owners
- **visits**: Visit transcripts with audio URLs (replaces complex recordings table)
- **appointments**: Scheduled appointments
- **pet_owner_practice_associations**: Many-to-many relationship for multi-practice access

### Simplified Visit Model
```sql
CREATE TABLE visits (
    id UUID PRIMARY KEY,
    pet_id UUID REFERENCES pets(id),
    practice_id UUID REFERENCES veterinary_practices(id), 
    vet_user_id UUID REFERENCES users(id),
    visit_date TIMESTAMP WITH TIME ZONE,
    full_text TEXT NOT NULL DEFAULT '',
    audio_transcript_url VARCHAR(500),
    summary TEXT,
    state VARCHAR(20) DEFAULT 'new', -- new, processing, processed, failed
    additional_data JSONB DEFAULT '{}', -- Contains S3 metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Security Features

### Audio Upload Security
- **Presigned URLs**: Time-limited (1 hour) S3 upload URLs
- **Content-Type Validation**: Enforced audio/* MIME types  
- **File Size Limits**: Maximum 100MB per recording
- **One Recording Per Pet Per Day**: Prevents duplicate uploads
- **Server-Side Encryption**: AES256 encryption for stored audio files

### Authentication & Authorization
- **JWT Tokens**: Secure, stateless authentication
- **Role-Based Access**: VET, VET_STAFF, PET_OWNER, ADMIN roles
- **API Rate Limiting**: Protection against abuse
- **CORS Configuration**: Restricted to allowed origins

## Error Handling

### Common Error Scenarios
- **409 Conflict**: Recording already exists for pet today
- **403 Forbidden**: Insufficient permissions  
- **404 Not Found**: Pet/visit not found
- **500 Server Error**: S3 configuration or upload failures

### Error Response Format
```json
{
  "detail": "Audio recording already exists for pet today. Visit ID: uuid"
}
```

## Performance Considerations

### Database Optimization
- **Async SQLAlchemy**: Non-blocking database operations
- **Connection Pooling**: Efficient database connection management
- **Indexed Queries**: Optimized queries on pet_id, visit_date, state

### S3 Optimization  
- **Direct Upload**: iPhone uploads directly to S3, bypassing server
- **Presigned URLs**: Eliminates server proxy for large files
- **Regional Storage**: S3 buckets in optimal geographic regions

## Known Limitations

- **Single Recording Per Pet Per Day**: Intentional constraint to simplify workflow
- **Audio Format**: Currently optimized for iPhone .m4a format
- **Transcription**: Manual process (automatic transcription planned)
- **Multi-Practice Access**: Pet owner associations need manual configuration

## Future Improvements

### Planned Features
- **Automatic Transcription**: Integration with OpenAI Whisper or AWS Transcribe
- **Real-Time Audio Streaming**: Live transcription during recording
- **Enhanced Search**: Full-text search across all visit transcripts  
- **Mobile App**: Native iOS app to replace web interface for recording
- **Backup and Recovery**: Automated S3 cross-region replication
- **Analytics Dashboard**: Recording statistics and usage metrics

### Technical Debt
- **Type Annotations**: Complete type coverage in Python codebase
- **Test Coverage**: Comprehensive unit and integration tests
- **Error Monitoring**: Integration with Sentry or similar service
- **API Documentation**: OpenAPI/Swagger documentation generation
