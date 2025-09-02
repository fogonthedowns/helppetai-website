# iOS App API Integration Fixes

## Critical API Response Format Clarification

### The Problem
The iPhone LLM was confused about the recordings API response format, expecting a wrapped object but receiving a direct array.

### The Actual Backend API Response Format

**Endpoint:** `GET /api/v1/recordings/`

**Backend Code:**
```python
@router.get("/", response_model=List[RecordingResponse])
async def get_recordings(...):
    # Returns a direct array of recordings
    return [RecordingResponse(...) for recording in recordings]
```

**Actual Response Format:**
```json
[
  {
    "id": "uuid",
    "appointment_id": "uuid", 
    "visit_id": "uuid",
    "recording_type": "visit_audio",
    "status": "uploaded",
    "filename": "recording.m4a",
    "original_filename": "recording.m4a",
    "file_size_bytes": 1024000,
    "duration_seconds": 60.5,
    "mime_type": "audio/m4a",
    "s3_url": "https://...",
    "transcript_text": null,
    "is_transcribed": false,
    "created_at": "2024-01-01T12:00:00Z",
    "recorded_by_user_id": "uuid"
  }
]
```

### What the LLM Incorrectly Expected
```json
{
  "recordings": [...],
  "total": 10,
  "page": 1
}
```

### Correct iOS Swift Implementation

**WRONG (what LLM thought):**
```swift
struct RecordingsListResponse: Codable {
    let recordings: [Recording]
    let total: Int?
    let page: Int?
}
```

**CORRECT (actual API):**
```swift
// Option 1: Use typealias
typealias RecordingsListResponse = [Recording]

// Option 2: Use [Recording] directly
func getRecordings(appointmentId: UUID) async throws -> [Recording] {
    let url = URL(string: "\(baseURL)/api/v1/recordings/?appointment_id=\(appointmentId)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    
    // Decode directly as array, not as wrapper object
    return try JSONDecoder().decode([Recording].self, from: data)
}
```

### Other iOS Fixes Needed

1. **Audio Permission API (iOS 17+ Deprecation):**
```swift
// OLD (deprecated):
AVAudioSession.sharedInstance().requestRecordPermission { granted in ... }

// NEW (iOS 17+):
let audioSession = AVAudioSession.sharedInstance()
try await audioSession.requestRecordPermission()
```

2. **Async/Await Syntax Errors:**
- Add `await` keywords for async function calls
- Mark functions as `async` when calling async APIs
- Use proper async context in SwiftUI views

3. **Dashboard Loading:**
- Ensure proper error handling for API responses
- Handle empty states gracefully
- Add loading indicators

### Key Takeaway for LLM
**The HelpPet backend returns simple arrays directly, not wrapped in pagination objects. Always check the actual FastAPI route definition (`response_model=List[Model]`) to understand the response format.**

### Status
- ✅ Backend API working correctly
- ✅ Authentication fixed
- ✅ Database migration completed
- ⚠️ iOS app needs response format fix
- ⚠️ iOS app needs async/await syntax fixes
- ⚠️ iOS app needs audio permission API update
