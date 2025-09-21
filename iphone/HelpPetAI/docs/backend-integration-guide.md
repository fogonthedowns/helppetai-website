# Backend Integration Guide - Pet-Recording Association Fix

## Executive Summary

The iOS team has implemented comprehensive pet-recording association fixes that require backend alignment to ensure proper data integrity. This document outlines the required API changes, database modifications, and validation logic needed to support the new iOS implementation.

## 🚨 Critical Backend Changes Required

### 1. **Recordings API Must Always Return `pet_id`**

**Current Issue:** Recording responses sometimes return `petId: null`, breaking iOS filtering logic.

**Required Fix:** Ensure all recording responses include a valid `pet_id` field.

### 2. **Add Pet-Appointment Validation**

**Current Issue:** No server-side validation prevents recordings from being created for invalid pet/appointment combinations.

**Required Fix:** Add validation logic to ensure pets belong to appointments before allowing recording creation.

### 3. **Database Schema Enhancements**

**Current Issue:** Missing foreign key constraints and optional `pet_id` field allow data inconsistencies.

**Required Fix:** Add NOT NULL constraints and proper foreign keys.

---

## API Endpoints & Requirements

### 1. Recording Upload Initiation

#### Endpoint
```
POST /api/v1/recordings/upload/initiate
```

#### iOS Request
```json
{
  "appointment_id": "appt-123e4567-e89b-12d3-a456-426614174000",
  "pet_id": "pet-987fcdeb-51a2-43d1-9c4f-123456789abc",
  "visit_id": null,
  "recording_type": "visit_audio",
  "filename": "visit_recording_20250901_143022.m4a",
  "content_type": "audio/mp4",
  "estimated_duration_seconds": 180.5
}
```

#### Required Backend Validation
```python
# CRITICAL: Add this validation logic
async def validate_recording_request(request):
    # 1. Validate pet_id is provided
    if not request.pet_id:
        raise HTTPException(400, "pet_id is required for all recordings")
    
    # 2. Validate appointment exists
    appointment = await get_appointment(request.appointment_id)
    if not appointment:
        raise HTTPException(404, "Appointment not found")
    
    # 3. CRITICAL: Validate pet belongs to appointment
    appointment_pets = await get_appointment_pets(request.appointment_id)
    pet_ids = [pet.id for pet in appointment_pets]
    
    if request.pet_id not in pet_ids:
        raise HTTPException(400, {
            "error": "pet_not_in_appointment",
            "message": "Pet is not associated with this appointment",
            "pet_id": request.pet_id,
            "appointment_id": request.appointment_id,
            "valid_pet_ids": pet_ids
        })
    
    # 4. Validate recording type
    valid_types = ["visit_audio", "appointment_audio", "consultation_audio"]
    if request.recording_type not in valid_types:
        raise HTTPException(400, f"Invalid recording_type: {request.recording_type}")
```

#### Expected Response
```json
{
  "recording_id": "rec-456e7890-e89b-12d3-a456-426614174111",
  "upload_url": "https://helppet-recordings.s3.amazonaws.com/upload",
  "upload_fields": {
    "key": "recordings/2025/09/01/rec-456e7890-e89b-12d3-a456-426614174111.m4a",
    "AWSAccessKeyId": "AKIAIOSFODNN7EXAMPLE",
    "policy": "eyJleHBpcmF0aW9uIjoi...",
    "signature": "qgk2gCLyvJrYyTSVHn..."
  },
  "s3_key": "recordings/2025/09/01/rec-456e7890-e89b-12d3-a456-426614174111.m4a",
  "bucket": "helppet-recordings",
  "expires_in": 3600,
  "max_file_size": 104857600
}
```

### 2. Recording Upload Completion

#### Endpoint
```
POST /api/v1/recordings/upload/complete/{recording_id}
```

#### iOS Request
```json
{
  "file_size_bytes": 2048576,
  "duration_seconds": 180.5,
  "recording_metadata": {
    "device_type": "iPhone",
    "ios_version": "17.0",
    "app_version": "1.2.0",
    "audio_quality": "high",
    "sample_rate": "44100"
  }
}
```

#### Required Backend Processing
```python
async def complete_recording_upload(recording_id: str, request):
    # 1. Update recording with actual file info
    recording = await update_recording(recording_id, {
        "status": "uploaded",
        "file_size_bytes": request.file_size_bytes,
        "duration_seconds": request.duration_seconds,
        "metadata": request.recording_metadata,
        "uploaded_at": datetime.utcnow()
    })
    
    # 2. CRITICAL: Ensure pet_id is preserved and returned
    if not recording.pet_id:
        logger.error(f"Recording {recording_id} missing pet_id after upload")
        # Try to infer from appointment if possible
        recording.pet_id = await infer_pet_from_context(recording)
    
    # 3. Trigger post-processing (transcription, etc.)
    await trigger_recording_processing(recording_id)
    
    return {"status": "completed", "recording_id": recording_id}
```

### 3. Get Recordings (CRITICAL UPDATE REQUIRED)

#### Endpoint
```
GET /api/v1/recordings/?appointment_id={appointment_id}&limit=50
```

#### Current Problematic Response
```json
[
  {
    "id": "rec-456e7890-e89b-12d3-a456-426614174111",
    "appointment_id": "appt-123e4567-e89b-12d3-a456-426614174000",
    "pet_id": null,  // ❌ THIS BREAKS iOS FILTERING
    "status": "uploaded",
    "filename": "visit_recording_20250901_143022.m4a"
  }
]
```

#### Required Fixed Response
```json
[
  {
    "id": "rec-456e7890-e89b-12d3-a456-426614174111",
    "visit_id": "visit-789abc12-3def-4567-8901-234567890def",
    "appointment_id": "appt-123e4567-e89b-12d3-a456-426614174000",
    "pet_id": "pet-987fcdeb-51a2-43d1-9c4f-123456789abc",  // ✅ REQUIRED
    "recorded_by_user_id": "user-111222333444555666777888",
    "recording_type": "visit_audio",
    "status": "uploaded",
    "filename": "rec-456e7890-e89b-12d3-a456-426614174111.m4a",
    "original_filename": "visit_recording_20250901_143022.m4a",
    "file_size_bytes": 2048576,
    "duration_seconds": 180.5,
    "duration_formatted": "3:00",
    "mime_type": "audio/mp4",
    "s3_url": "https://helppet-recordings.s3.amazonaws.com/recordings/2025/09/01/rec-456e7890-e89b-12d3-a456-426614174111.m4a",
    "transcript_text": null,
    "transcript_confidence": null,
    "is_transcribed": false,
    "is_processing": false,
    "created_at": "2025-09-01T14:30:22Z",
    "updated_at": "2025-09-01T14:31:45Z"
  }
]
```

### 4. Get Appointment Details (NEW REQUIREMENT)

#### Endpoint
```
GET /api/v1/appointments/{appointment_id}
```

#### iOS Usage
The iOS app now validates pet-appointment associations before allowing recordings:

```swift
// iOS calls this to validate pet belongs to appointment
let appointment = try await APIManager.shared.getAppointmentDetails(appointmentId: appointmentId)
let petExists = appointment.pets.contains { $0.id == petId }
```

#### Required Response
```json
{
  "id": "appt-123e4567-e89b-12d3-a456-426614174000",
  "practice_id": "practice-999888777666555444333222",
  "pet_owner_id": "owner-aaa111bbb222ccc333ddd444",
  "assigned_vet_user_id": "vet-555666777888999000111222",
  "appointment_date": "2025-09-01T14:00:00Z",
  "duration_minutes": 30,
  "appointment_type": "routine_checkup",
  "status": "in_progress",
  "title": "Routine Checkup - Fluffy & Rex",
  "description": "Annual wellness exam for both pets",
  "notes": "Both pets due for vaccinations",
  "pets": [
    {
      "id": "pet-987fcdeb-51a2-43d1-9c4f-123456789abc",
      "name": "Fluffy",
      "species": "Dog",
      "breed": "Golden Retriever"
    },
    {
      "id": "pet-111aaa222bbb333ccc444ddd",
      "name": "Rex",
      "species": "Dog", 
      "breed": "German Shepherd"
    }
  ],
  "created_at": "2025-08-25T09:15:30Z",
  "updated_at": "2025-09-01T13:45:12Z"
}
```

### 5. Visit Management APIs (NEW FEATURE)

The iOS app is ready to support full visit management. These endpoints are optional but recommended for enhanced clinical workflows.

#### Create Visit
```
POST /api/v1/visits/
```

```json
// Request
{
  "pet_id": "pet-987fcdeb-51a2-43d1-9c4f-123456789abc",
  "appointment_id": "appt-123e4567-e89b-12d3-a456-426614174000",
  "visit_type": "routine_checkup",
  "chief_complaint": "Annual wellness exam",
  "notes": "Pet appears healthy and energetic"
}

// Response
{
  "id": "visit-789abc12-3def-4567-8901-234567890def",
  "pet_id": "pet-987fcdeb-51a2-43d1-9c4f-123456789abc",
  "appointment_id": "appt-123e4567-e89b-12d3-a456-426614174000",
  "visit_date": "2025-09-01T14:00:00Z",
  "visit_type": "routine_checkup",
  "status": "in_progress",
  "chief_complaint": "Annual wellness exam",
  "diagnosis": null,
  "treatment_plan": null,
  "notes": "Pet appears healthy and energetic",
  "follow_up_required": false,
  "follow_up_date": null,
  "recordings": [],
  "created_by": "vet-555666777888999000111222",
  "created_at": "2025-09-01T14:00:00Z",
  "updated_at": "2025-09-01T14:00:00Z"
}
```

#### Get Visits
```
GET /api/v1/visits/?pet_id={pet_id}&appointment_id={appointment_id}&limit=50
```

---

## Database Schema Requirements

### 1. Recordings Table Updates

```sql
-- CRITICAL: Make pet_id NOT NULL
ALTER TABLE recordings 
ALTER COLUMN pet_id SET NOT NULL;

-- Add foreign key constraint
ALTER TABLE recordings 
ADD CONSTRAINT fk_recordings_pet_id 
FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE;

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_recordings_pet_id ON recordings(pet_id);

-- Add appointment_id index if not exists
CREATE INDEX IF NOT EXISTS idx_recordings_appointment_id ON recordings(appointment_id);
```

### 2. Visits Table (NEW - Optional but Recommended)

```sql
CREATE TABLE visits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL,
    appointment_id UUID,
    visit_date TIMESTAMP WITH TIME ZONE NOT NULL,
    visit_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    chief_complaint TEXT,
    diagnosis TEXT,
    treatment_plan TEXT,
    notes TEXT,
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_visits_pet_id 
        FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE,
    CONSTRAINT fk_visits_appointment_id 
        FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
    CONSTRAINT fk_visits_created_by 
        FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE INDEX idx_visits_pet_id ON visits(pet_id);
CREATE INDEX idx_visits_appointment_id ON visits(appointment_id);
CREATE INDEX idx_visits_visit_date ON visits(visit_date);
```

### 3. Add visit_id to Recordings (Optional)

```sql
-- Link recordings to visits for enhanced clinical records
ALTER TABLE recordings ADD COLUMN visit_id UUID;

ALTER TABLE recordings 
ADD CONSTRAINT fk_recordings_visit_id 
FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE;

CREATE INDEX idx_recordings_visit_id ON recordings(visit_id);
```

---

## Data Migration Requirements

### 1. Backfill Missing pet_id Values

```sql
-- Find recordings without pet_id
SELECT r.id, r.appointment_id, r.filename 
FROM recordings r 
WHERE r.pet_id IS NULL;

-- Attempt to infer pet_id from appointment context
-- This may require business logic to determine which pet each recording belongs to
UPDATE recordings 
SET pet_id = (
    SELECT ap.pet_id 
    FROM appointment_pets ap 
    WHERE ap.appointment_id = recordings.appointment_id 
    LIMIT 1
)
WHERE pet_id IS NULL 
AND appointment_id IS NOT NULL;

-- Manual review may be required for ambiguous cases
```

### 2. Data Validation Queries

```sql
-- Verify all recordings have valid pet associations
SELECT 
    COUNT(*) as total_recordings,
    COUNT(pet_id) as recordings_with_pet_id,
    COUNT(*) - COUNT(pet_id) as missing_pet_id
FROM recordings;

-- Find recordings with invalid pet/appointment associations
SELECT r.id, r.pet_id, r.appointment_id
FROM recordings r
LEFT JOIN appointment_pets ap ON r.appointment_id = ap.appointment_id AND r.pet_id = ap.pet_id
WHERE r.appointment_id IS NOT NULL 
AND ap.pet_id IS NULL;
```

---

## Error Handling Requirements

### 1. Validation Error Responses

When iOS sends invalid requests, return structured error responses:

```json
// Pet not in appointment error
{
  "error": "validation_error",
  "error_code": "pet_not_in_appointment", 
  "message": "Pet is not associated with this appointment",
  "details": {
    "pet_id": "pet-987fcdeb-51a2-43d1-9c4f-123456789abc",
    "appointment_id": "appt-123e4567-e89b-12d3-a456-426614174000",
    "valid_pet_ids": [
      "pet-111aaa222bbb333ccc444ddd",
      "pet-222bbb333ccc444ddd555eee"
    ]
  }
}

// Missing pet_id error
{
  "error": "validation_error",
  "error_code": "missing_pet_id",
  "message": "pet_id is required for all recording uploads",
  "details": {
    "field": "pet_id",
    "required": true
  }
}
```

### 2. Logging Requirements

Add comprehensive logging for debugging:

```python
# Log all recording creation attempts
logger.info(f"Recording upload initiated", extra={
    "recording_id": recording.id,
    "pet_id": request.pet_id,
    "appointment_id": request.appointment_id,
    "user_id": current_user.id,
    "filename": request.filename
})

# Log validation failures
logger.warning(f"Pet-appointment validation failed", extra={
    "pet_id": request.pet_id,
    "appointment_id": request.appointment_id,
    "valid_pet_ids": valid_pet_ids,
    "user_id": current_user.id
})
```

---

## Testing Requirements

### 1. Unit Tests

```python
def test_recording_upload_validation():
    # Test valid pet/appointment combination
    request = RecordingUploadRequest(
        appointment_id="appt-123",
        pet_id="pet-456",
        recording_type="visit_audio"
    )
    response = await initiate_recording_upload(request)
    assert response.recording_id is not None
    
    # Test invalid pet/appointment combination
    request.pet_id = "pet-invalid"
    with pytest.raises(HTTPException) as exc:
        await initiate_recording_upload(request)
    assert exc.value.status_code == 400
    assert "pet_not_in_appointment" in exc.value.detail["error_code"]

def test_recordings_response_includes_pet_id():
    recordings = await get_recordings(appointment_id="appt-123")
    for recording in recordings:
        assert recording.pet_id is not None
        assert isinstance(recording.pet_id, str)
```

### 2. Integration Tests

```python
def test_multi_pet_appointment_recording_flow():
    # Create appointment with 2 pets
    appointment = create_test_appointment(pet_ids=["pet-1", "pet-2"])
    
    # Record for first pet
    recording1 = await create_recording(appointment.id, "pet-1")
    
    # Record for second pet  
    recording2 = await create_recording(appointment.id, "pet-2")
    
    # Verify recordings are properly associated
    recordings = await get_recordings(appointment_id=appointment.id)
    
    pet1_recordings = [r for r in recordings if r.pet_id == "pet-1"]
    pet2_recordings = [r for r in recordings if r.pet_id == "pet-2"]
    
    assert len(pet1_recordings) == 1
    assert len(pet2_recordings) == 1
    assert pet1_recordings[0].id == recording1.id
    assert pet2_recordings[0].id == recording2.id
```

---

## Performance Considerations

### 1. Database Indexes

Ensure these indexes exist for optimal performance:

```sql
-- Critical for iOS recording queries
CREATE INDEX CONCURRENTLY idx_recordings_appointment_pet 
ON recordings(appointment_id, pet_id);

-- For visit-based queries
CREATE INDEX CONCURRENTLY idx_recordings_visit_pet 
ON recordings(visit_id, pet_id) WHERE visit_id IS NOT NULL;

-- For pet-specific queries
CREATE INDEX CONCURRENTLY idx_recordings_pet_status 
ON recordings(pet_id, status);
```

### 2. API Response Optimization

```python
# Optimize recordings endpoint with proper joins
async def get_recordings(appointment_id: str = None, pet_id: str = None):
    query = """
    SELECT r.*, p.name as pet_name, a.title as appointment_title
    FROM recordings r
    LEFT JOIN pets p ON r.pet_id = p.id
    LEFT JOIN appointments a ON r.appointment_id = a.id
    WHERE ($1::uuid IS NULL OR r.appointment_id = $1)
    AND ($2::uuid IS NULL OR r.pet_id = $2)
    ORDER BY r.created_at DESC
    """
    
    return await database.fetch_all(query, appointment_id, pet_id)
```

---

## Security Considerations

### 1. Authorization Checks

```python
async def validate_recording_access(user: User, pet_id: str, appointment_id: str):
    # Ensure user has access to the pet
    pet = await get_pet(pet_id)
    if not await user_can_access_pet(user, pet):
        raise HTTPException(403, "Access denied to pet records")
    
    # Ensure user has access to the appointment
    appointment = await get_appointment(appointment_id)
    if not await user_can_access_appointment(user, appointment):
        raise HTTPException(403, "Access denied to appointment")
```

### 2. Data Privacy

```python
# Ensure recordings are only returned for authorized pets/appointments
async def get_recordings_for_user(user: User, filters: RecordingFilters):
    # Get user's accessible pets
    accessible_pets = await get_user_accessible_pets(user)
    pet_ids = [pet.id for pet in accessible_pets]
    
    # Filter recordings by accessible pets
    recordings = await get_recordings(
        appointment_id=filters.appointment_id,
        pet_id=filters.pet_id
    )
    
    # Security check: ensure all returned recordings are for accessible pets
    return [r for r in recordings if r.pet_id in pet_ids]
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] Database schema updates applied
- [ ] Data migration completed and validated
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Performance testing completed
- [ ] Security review completed

### Deployment
- [ ] API validation logic deployed
- [ ] Monitoring and logging configured
- [ ] Error handling verified
- [ ] iOS team notified of deployment

### Post-Deployment
- [ ] Monitor error rates for validation failures
- [ ] Verify all recordings include pet_id
- [ ] Check iOS app functionality
- [ ] Review logs for any data inconsistencies

---

## Support & Troubleshooting

### Common Issues

1. **iOS reports "recordings always empty"**
   - Check: Are recording responses including `pet_id`?
   - Check: Database query for missing pet_id values
   - Fix: Ensure recording creation sets pet_id properly

2. **Recording upload fails with "pet_not_in_appointment"**
   - Check: Pet-appointment associations in database
   - Check: iOS is sending correct pet_id
   - Fix: Verify appointment_pets table data

3. **Performance issues with recording queries**
   - Check: Database indexes are in place
   - Check: Query execution plans
   - Fix: Add missing indexes, optimize queries

### Monitoring Queries

```sql
-- Check for recordings without pet_id (should be 0 after migration)
SELECT COUNT(*) FROM recordings WHERE pet_id IS NULL;

-- Check validation failure rates
SELECT DATE(created_at), COUNT(*) 
FROM api_logs 
WHERE error_code = 'pet_not_in_appointment' 
GROUP BY DATE(created_at);

-- Monitor recording upload success rates
SELECT 
    DATE(created_at),
    COUNT(*) as total_uploads,
    COUNT(CASE WHEN status = 'uploaded' THEN 1 END) as successful_uploads
FROM recordings 
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at);
```

---

## Summary for Backend Team

### Immediate Actions Required (High Priority)

1. **🚨 Fix Recordings API Response**
   - Ensure `pet_id` is never null in `/api/v1/recordings/` responses
   - This is breaking iOS recording display functionality

2. **🚨 Add Pet-Appointment Validation**
   - Validate pet belongs to appointment before allowing recording creation
   - Return structured error responses for validation failures

3. **🚨 Database Constraints**
   - Make `recordings.pet_id` NOT NULL
   - Add foreign key constraints for data integrity

### Optional Enhancements (Medium Priority)

4. **📋 Visit Management APIs**
   - Implement visit CRUD operations
   - Enable enhanced clinical workflow features

5. **🔍 Enhanced Logging**
   - Add comprehensive logging for debugging
   - Monitor validation failures and success rates

### Long-term Improvements (Low Priority)

6. **⚡ Performance Optimization**
   - Add database indexes for recording queries
   - Optimize API responses with proper joins

7. **🔒 Security Enhancements**
   - Add authorization checks for recording access
   - Implement data privacy controls

The iOS team has implemented comprehensive fixes that will work immediately once the backend ensures `pet_id` is properly returned in recording responses. The validation and error handling improvements will provide a much better user experience for veterinarians using the app.
