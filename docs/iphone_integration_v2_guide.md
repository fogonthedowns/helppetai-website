# iPhone Integration v2.0 Guide - Simplified Audio Recording System

## Overview

This guide details the complete iPhone integration for HelpPet.ai's simplified audio recording system. Version 2.0 eliminates the complex recordings table in favor of a streamlined Visit_Transcripts approach with one recording per pet per day.

## Key Concepts

### Appointment → Pet → Visit → Recording Relationship

```
Appointment (1)
├── Pet A (1) → Visit A (1) → Audio Recording A (1)
├── Pet B (1) → Visit B (1) → Audio Recording B (1)
└── Pet C (1) → Visit C (1) → Audio Recording C (1)
```

**Important Rules:**
- ✅ **One recording per pet per day** - prevents duplicates and confusion
- ✅ **Each pet gets its own Visit record** - clean data separation
- ✅ **Appointments can have multiple pets** - multi-pet appointments supported
- ✅ **Direct S3 upload** - no server bottleneck for large audio files
- ✅ **Presigned URLs for security** - time-limited access to S3 resources

## Authentication

All API calls require JWT authentication:

```swift
// Set auth header for all requests
APIClient.setAuthToken("your-jwt-token")
// OR add to each request
headers["Authorization"] = "Bearer \(jwtToken)"
```

## Complete iPhone Integration Flow

### 1. Appointment Context Setup

When starting a recording session, the iPhone app should:

```swift
// Get appointment details with associated pets
let appointment = await APIClient.getAppointment(appointmentId: appointmentId)

// appointment.pets will contain array of pets for this appointment
for pet in appointment.pets {
    print("Pet: \(pet.name) - ID: \(pet.id)")
}
```

**Expected Response Structure:**
```json
{
  "id": "appointment-uuid",
  "title": "Annual Checkup",
  "appointment_date": 1703001600,
  "pets": [
    {
      "id": "pet-a-uuid",
      "name": "Fluffy",
      "species": "Cat",
      "breed": "Persian"
    },
    {
      "id": "pet-b-uuid", 
      "name": "Max",
      "species": "Dog",
      "breed": "Golden Retriever"
    }
  ]
}
```

### 2. Recording Initiation Per Pet

For **each pet** in the appointment, initiate a separate recording:

#### Endpoint: `POST /api/v1/visit-transcripts/audio/upload/initiate`

**Request Body:**
```json
{
  "pet_id": "pet-uuid-string",
  "filename": "appointment_123_pet_fluffy_20241219_143022.m4a",
  "content_type": "audio/m4a",
  "estimated_duration_seconds": 180.5
}
```

**Request Types:**
```swift
struct AudioUploadRequest: Codable {
    let petId: String           // Required: UUID of the specific pet
    let filename: String        // Required: Descriptive filename for organization
    let contentType: String     // Required: "audio/m4a" for iPhone recordings
    let estimatedDurationSeconds: Double? // Optional: Estimated recording length
}
```

**Response:**
```json
{
  "visit_id": "visit-uuid-created-for-this-pet",
  "upload_url": "https://helppetai-visit-recordings.s3.amazonaws.com/",
  "upload_fields": {
    "key": "visit-recordings/2024/12/19/pet-a-uuid/unique-id.m4a",
    "Content-Type": "audio/m4a",
    "policy": "eyJleHBpcmF0aW9uIjoi...",
    "x-amz-credential": "AKIA.../20241219/us-east-1/s3/aws4_request",
    "x-amz-algorithm": "AWS4-HMAC-SHA256",
    "x-amz-date": "20241219T143022Z",
    "x-amz-signature": "abc123..."
  },
  "s3_key": "visit-recordings/2024/12/19/pet-a-uuid/unique-id.m4a",
  "bucket": "helppetai-visit-recordings",
  "expires_in": 3600
}
```

**Response Types:**
```swift
struct AudioUploadResponse: Codable {
    let visitId: String                    // UUID of created visit record
    let uploadUrl: String                  // S3 bucket URL for POST upload
    let uploadFields: [String: String]     // Form fields for S3 POST request
    let s3Key: String                      // S3 object key for this recording
    let bucket: String                     // S3 bucket name
    let expiresIn: Int                     // URL expiration in seconds (3600 = 1 hour)
}
```

### 3. Audio Recording

Record audio for the specific pet using AVAudioRecorder:

```swift
class PetAudioRecorder {
    private var audioRecorder: AVAudioRecorder?
    private let currentPet: Pet
    private let visitId: String
    private let uploadResponse: AudioUploadResponse
    
    func startRecording() {
        let documentsPath = FileManager.default.urls(for: .documentDirectory, 
                                                   in: .userDomainMask)[0]
        let audioFilename = documentsPath.appendingPathComponent("temp_\(currentPet.id).m4a")
        
        let settings = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: 44100,
            AVNumberOfChannelsKey: 1,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
        ]
        
        do {
            audioRecorder = try AVAudioRecorder(url: audioFilename, settings: settings)
            audioRecorder?.record()
            
            // Update UI to show recording for this specific pet
            updateRecordingUI(for: currentPet, status: .recording)
        } catch {
            print("Recording failed: \(error)")
        }
    }
    
    func stopRecording() -> Data? {
        audioRecorder?.stop()
        
        // Get recorded audio data
        guard let url = audioRecorder?.url else { return nil }
        return try? Data(contentsOf: url)
    }
}
```

### 4. Direct S3 Upload

Upload the recorded audio directly to S3 using the presigned POST URL:

```swift
func uploadAudioToS3(audioData: Data, uploadResponse: AudioUploadResponse) async throws {
    var request = URLRequest(url: URL(string: uploadResponse.uploadUrl)!)
    request.httpMethod = "POST"
    
    // Create multipart form data
    let boundary = "Boundary-\(UUID().uuidString)"
    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
    
    var body = Data()
    
    // Add all the upload fields from the response
    for (key, value) in uploadResponse.uploadFields {
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
        body.append("\(value)\r\n".data(using: .utf8)!)
    }
    
    // Add the audio file
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"file\"; filename=\"recording.m4a\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: audio/m4a\r\n\r\n".data(using: .utf8)!)
    body.append(audioData)
    body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
    
    request.httpBody = body
    
    let (_, response) = try await URLSession.shared.data(for: request)
    
    guard let httpResponse = response as? HTTPURLResponse,
          httpResponse.statusCode == 204 else {
        throw AudioUploadError.s3UploadFailed
    }
    
    print("✅ Audio uploaded successfully to S3 for pet \(currentPet.name)")
}
```

### 5. Mark Upload Complete

After successful S3 upload, notify the backend:

#### Endpoint: `POST /api/v1/visit-transcripts/audio/upload/complete/{visit_id}`

**Request Body:**
```json
{
  "file_size_bytes": 2048576,
  "duration_seconds": 185.3,
  "device_metadata": {
    "device_model": "iPhone 15 Pro",
    "ios_version": "17.2.1",
    "app_version": "2.0.0",
    "recording_quality": "high",
    "sample_rate": 44100
  }
}
```

**Request Types:**
```swift
struct AudioUploadCompleteRequest: Codable {
    let fileSizeBytes: Int?                    // Actual file size after recording
    let durationSeconds: Double?               // Actual recording duration
    let deviceMetadata: [String: Any]?         // Device and app information
}
```

**Response:**
```json
{
  "uuid": "visit-uuid",
  "pet_id": "pet-uuid",
  "visit_date": 1703001234,
  "full_text": "",
  "audio_transcript_url": "https://bucket.s3.amazonaws.com/visit-recordings/path/file.m4a",
  "state": "processing",
  "metadata": {
    "s3_key": "visit-recordings/2024/12/19/pet-uuid/unique-id.m4a",
    "s3_bucket": "helppetai-visit-recordings",
    "filename": "appointment_123_pet_fluffy_20241219_143022.m4a",
    "upload_completed_at": "2024-12-19T14:30:22Z",
    "file_size_bytes": 2048576,
    "duration_seconds": 185.3
  }
}
```

### 6. Audio Playback

To play back a previously recorded audio file:

#### Endpoint: `GET /api/v1/visit-transcripts/audio/playback/{visit_id}`

**Response:**
```json
{
  "presigned_url": "https://bucket.s3.amazonaws.com/path/file.m4a?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...",
  "expires_in": 900,
  "visit_id": "visit-uuid",
  "filename": "appointment_123_pet_fluffy_20241219_143022.m4a"
}
```

**Playback Implementation:**
```swift
func playAudio(for visitId: String) async {
    do {
        let playbackResponse = try await APIClient.getAudioPlaybackUrl(visitId: visitId)
        
        guard let url = URL(string: playbackResponse.presignedUrl) else { return }
        
        let player = AVPlayer(url: url)
        player.play()
        
        // Update UI to show playing status
        updatePlaybackUI(for: visitId, status: .playing)
        
    } catch {
        print("Playback failed: \(error)")
    }
}
```

## Multi-Pet Appointment Example

Here's a complete example of handling an appointment with multiple pets:

```swift
class MultiPetRecordingManager {
    private let appointment: Appointment
    private var petRecordings: [String: PetRecordingSession] = [:]
    
    func startRecordingSession() async {
        for pet in appointment.pets {
            do {
                // 1. Initiate upload for this pet
                let uploadRequest = AudioUploadRequest(
                    petId: pet.id,
                    filename: "appointment_\(appointment.id)_pet_\(pet.name)_\(dateFormatter.string(from: Date())).m4a",
                    contentType: "audio/m4a",
                    estimatedDurationSeconds: nil
                )
                
                let uploadResponse = try await APIClient.initiateAudioUpload(uploadRequest)
                
                // 2. Create recording session for this pet
                let recordingSession = PetRecordingSession(
                    pet: pet,
                    visitId: uploadResponse.visitId,
                    uploadResponse: uploadResponse
                )
                
                petRecordings[pet.id] = recordingSession
                
                print("✅ Ready to record for \(pet.name) - Visit ID: \(uploadResponse.visitId)")
                
            } catch {
                print("❌ Failed to initiate recording for \(pet.name): \(error)")
            }
        }
    }
    
    func recordForPet(petId: String) async {
        guard let session = petRecordings[petId] else {
            print("❌ No recording session found for pet \(petId)")
            return
        }
        
        // Record audio for this specific pet
        session.startRecording()
        
        // User interface shows recording for this pet
        updateUI(petId: petId, status: .recording)
    }
    
    func stopRecordingForPet(petId: String) async {
        guard let session = petRecordings[petId] else { return }
        
        guard let audioData = session.stopRecording() else {
            print("❌ Failed to get audio data for pet \(petId)")
            return
        }
        
        do {
            // Upload to S3
            try await uploadAudioToS3(audioData: audioData, 
                                    uploadResponse: session.uploadResponse)
            
            // Mark complete
            let completeRequest = AudioUploadCompleteRequest(
                fileSizeBytes: audioData.count,
                durationSeconds: session.recordingDuration,
                deviceMetadata: deviceMetadata
            )
            
            let visitTranscript = try await APIClient.completeAudioUpload(
                visitId: session.visitId,
                request: completeRequest
            )
            
            session.visitTranscript = visitTranscript
            updateUI(petId: petId, status: .completed)
            
            print("✅ Recording complete for \(session.pet.name)")
            
        } catch {
            print("❌ Upload failed for \(session.pet.name): \(error)")
            updateUI(petId: petId, status: .failed)
        }
    }
}
```

## Error Handling

### Common Error Scenarios

#### 1. Duplicate Recording (409 Conflict)
```json
{
  "detail": "Audio recording already exists for pet abc-123 today. Visit ID: existing-visit-uuid"
}
```

**Handling:**
```swift
if case .duplicateRecording(let existingVisitId) = error {
    // Option 1: Show existing recording
    showExistingRecording(visitId: existingVisitId)
    
    // Option 2: Allow user to replace
    showReplaceRecordingDialog(existingVisitId: existingVisitId)
}
```

#### 2. Upload Timeout (Presigned URL Expired)
```swift
// Presigned URLs expire in 1 hour - handle timeout
if uploadError.code == .urlExpired {
    // Re-request presigned URL
    let newUploadResponse = try await APIClient.initiateAudioUpload(originalRequest)
    // Retry upload with new URL
}
```

#### 3. File Too Large
```swift
// Check file size before upload (100MB limit)
if audioData.count > 100 * 1024 * 1024 {
    throw AudioUploadError.fileTooLarge
}
```

#### 4. Network Connectivity
```swift
// Implement retry logic for network failures
func uploadWithRetry(audioData: Data, maxRetries: Int = 3) async throws {
    for attempt in 1...maxRetries {
        do {
            try await uploadAudioToS3(audioData: audioData, uploadResponse: uploadResponse)
            return // Success
        } catch {
            if attempt == maxRetries {
                throw error // Final failure
            }
            
            // Exponential backoff
            try await Task.sleep(nanoseconds: UInt64(pow(2.0, Double(attempt)) * 1_000_000_000))
        }
    }
}
```

## Data Validation

### Input Validation
```swift
extension AudioUploadRequest {
    func validate() throws {
        guard UUID(uuidString: petId) != nil else {
            throw ValidationError.invalidPetId
        }
        
        guard filename.hasSuffix(".m4a") else {
            throw ValidationError.invalidFilename
        }
        
        guard contentType == "audio/m4a" else {
            throw ValidationError.invalidContentType
        }
        
        if let duration = estimatedDurationSeconds, duration <= 0 || duration > 3600 {
            throw ValidationError.invalidDuration
        }
    }
}
```

### Response Validation
```swift
extension AudioUploadResponse {
    func validate() throws {
        guard UUID(uuidString: visitId) != nil else {
            throw ValidationError.invalidVisitId
        }
        
        guard URL(string: uploadUrl) != nil else {
            throw ValidationError.invalidUploadUrl
        }
        
        guard expiresIn > 0 && expiresIn <= 3600 else {
            throw ValidationError.invalidExpiration
        }
    }
}
```

## UI/UX Considerations

### Recording Status Management
```swift
enum RecordingStatus {
    case ready          // Ready to start recording
    case recording      // Currently recording
    case uploading      // Uploading to S3
    case processing     // Upload complete, processing
    case completed      // Fully complete
    case failed         // Error occurred
}

class PetRecordingView {
    func updateStatus(_ status: RecordingStatus, for pet: Pet) {
        DispatchQueue.main.async {
            switch status {
            case .ready:
                recordButton.setTitle("Record \(pet.name)", for: .normal)
                recordButton.backgroundColor = .systemBlue
                
            case .recording:
                recordButton.setTitle("Stop Recording", for: .normal)
                recordButton.backgroundColor = .systemRed
                showRecordingTimer()
                
            case .uploading:
                recordButton.setTitle("Uploading...", for: .normal)
                recordButton.backgroundColor = .systemGray
                recordButton.isEnabled = false
                showProgressIndicator()
                
            case .completed:
                recordButton.setTitle("✓ Recorded", for: .normal)
                recordButton.backgroundColor = .systemGreen
                showPlaybackButton()
                
            case .failed:
                recordButton.setTitle("⚠ Retry", for: .normal)
                recordButton.backgroundColor = .systemOrange
            }
        }
    }
}
```

### Multi-Pet UI Layout
```swift
// Show one recording section per pet
VStack {
    ForEach(appointment.pets, id: \.id) { pet in
        PetRecordingCard(
            pet: pet,
            status: recordingStatuses[pet.id] ?? .ready,
            onRecord: { recordForPet(petId: pet.id) },
            onStop: { stopRecordingForPet(petId: pet.id) },
            onPlayback: { playAudio(for: visitIds[pet.id]) }
        )
        .padding()
    }
}
```

## Migration from v1.0 to v2.0

### What Changed

#### v1.0 (Complex Recordings System)
```
❌ Complex Recording model with many fields
❌ Separate recordings table and API routes  
❌ Multiple recordings per visit possible
❌ Complex state management across models
❌ Recording entities separate from visits
```

#### v2.0 (Simplified Visit_Transcripts)
```
✅ Simple Visit model with audio_transcript_url
✅ Integrated audio upload in visit_transcripts routes
✅ One recording per pet per day (enforced)
✅ Streamlined state management 
✅ Audio metadata stored in Visit.additional_data JSON
```

### Migration Steps

#### 1. Database Migration
```sql
-- Automatic migration will:
-- 1. Drop recordings table and indexes
-- 2. Keep existing visits table structure
-- 3. Continue using audio_transcript_url field in visits
```

#### 2. API Endpoint Changes

**OLD v1.0 Endpoints (DEPRECATED):**
```
❌ POST /api/v1/recordings/upload/initiate
❌ POST /api/v1/recordings/upload/complete/{recording_id}  
❌ GET /api/v1/recordings/{recording_id}/download-url
❌ GET /api/v1/recordings/
❌ DELETE /api/v1/recordings/{recording_id}
```

**NEW v2.0 Endpoints:**
```
✅ POST /api/v1/visit-transcripts/audio/upload/initiate
✅ POST /api/v1/visit-transcripts/audio/upload/complete/{visit_id}
✅ GET /api/v1/visit-transcripts/audio/playback/{visit_id}
```

#### 3. iPhone App Code Migration

**OLD v1.0 Code:**
```swift
// OLD - Don't use this anymore
let recordingResponse = await APIClient.initiateRecordingUpload(request)
await APIClient.completeRecordingUpload(recordingId: recordingResponse.recordingId, request: completeRequest)
let downloadUrl = await APIClient.getRecordingDownloadUrl(recordingId: recordingId)
```

**NEW v2.0 Code:**
```swift
// NEW - Use this instead
let uploadResponse = await APIClient.initiateAudioUpload(request)
await APIClient.completeAudioUpload(visitId: uploadResponse.visitId, request: completeRequest)  
let playbackResponse = await APIClient.getAudioPlaybackUrl(visitId: visitId)
```

#### 4. Data Model Changes

**OLD v1.0 Models:**
```swift
struct Recording {
    let id: String
    let visitId: String?
    let appointmentId: String?
    let status: RecordingStatus
    let filename: String
    // ... many more fields
}
```

**NEW v2.0 Models:**
```swift
struct VisitTranscript {
    let uuid: String  // This is the visit ID
    let petId: String
    let audioTranscriptUrl: String?
    let state: VisitState  // "new", "processing", "processed", "failed"
    let metadata: [String: Any]  // Contains S3 info and file details
}
```

### Migration Benefits

#### Complexity Reduction
- **Before**: Recording model (25+ fields) + Visit model + complex relationships
- **After**: Just Visit model with audio_transcript_url + metadata JSON

#### Duplicate Prevention  
- **Before**: Multiple recordings per visit possible, causing confusion
- **After**: One recording per pet per day, enforced at API level

#### Simplified iPhone Integration
- **Before**: Track recording IDs separately from visit IDs
- **After**: Single visit ID handles both visit and audio recording

#### Better Performance
- **Before**: Complex JOINs between recordings and visits tables
- **After**: Single table queries with JSON metadata

### Breaking Changes

#### iPhone App Updates Required
1. **Update API endpoints** - New URLs for audio upload/playback
2. **Update data models** - Use VisitTranscript instead of Recording
3. **Update ID handling** - Use visit_id instead of recording_id
4. **Update UI logic** - Show recording status per pet, not per appointment

#### Backend Changes
1. **Remove recording routes** - No longer available
2. **Database migration** - Recordings table will be dropped
3. **Update visit queries** - Audio info now in Visit.additional_data

### Migration Timeline

#### Phase 1: Preparation
- [ ] Update iPhone app to use new v2.0 endpoints
- [ ] Test v2.0 endpoints in staging environment
- [ ] Update documentation and integration guides

#### Phase 2: Database Migration  
- [ ] Run migration to drop recordings table
- [ ] Verify existing visit data integrity
- [ ] Update API routes registration

#### Phase 3: Cleanup
- [ ] Remove old recording-related code
- [ ] Update monitoring and logging
- [ ] Train users on new simplified workflow

### Backward Compatibility

**Note: This is a breaking change.** v1.0 recording endpoints will no longer work after migration. iPhone apps must be updated to use v2.0 endpoints before the database migration runs.

The migration prioritizes simplicity and the "one recording per pet" workflow over backward compatibility, as this provides a much better user experience for veterinarians.
