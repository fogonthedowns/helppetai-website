# HelpPet.ai Data Model: What Gets Saved After a Visit Recording Upload

Based on analysis of the codebase, here's exactly what happens when a recording is uploaded for a pet appointment:

## 1. Initial Upload Process

When a recording is uploaded for a pet appointment, the system creates a **Visit** record immediately:

```sql
-- Visit record gets created in the "visits" table
INSERT INTO visits (
    id,                    -- UUID (auto-generated)
    pet_id,               -- Links to specific pet
    practice_id,          -- Links to veterinary practice  
    vet_user_id,          -- Links to the veterinarian user
    visit_date,           -- Date from the appointment
    full_text,            -- Empty initially (populated after transcription)
    audio_transcript_url, -- S3 URL of the uploaded audio
    summary,              -- NULL initially
    state,                -- "NEW" → "PROCESSING" → "PROCESSED"
    additional_data,      -- JSON metadata about the recording
    created_by,           -- User who uploaded
    created_at,           -- Timestamp
    updated_at            -- Timestamp
);
```

## 2. Visit Record Details

The **Visit** model contains:

- **Core Data:**
  - `pet_id`: Links to the specific pet in the appointment
  - `practice_id`: The veterinary practice
  - `vet_user_id`: The veterinarian who recorded
  - `visit_date`: Uses the appointment date (not upload time)

- **Audio/Transcript Data:**
  - `audio_transcript_url`: S3 URL where the audio file is stored
  - `full_text`: Empty initially, populated after transcription processing
  - `summary`: NULL initially, can be populated later

- **Processing State:**
  - `state`: Follows the lifecycle: `NEW` → `PROCESSING` → `PROCESSED` → `FAILED`

- **Metadata (JSON):**
  ```json
  {
    "appointment_id": "uuid-of-appointment",
    "audio_s3_key": "visit-recordings/2024/01/15/pet-uuid/recording-uuid.m4a",
    "audio_filename": "original-filename.m4a",
    "recorded_by": "user-uuid",
    "file_size": 1234567,
    "upload_completed_at": "2024-01-15T10:30:00Z",
    "duration_seconds": 180,
    "device_metadata": {...}
  }
  ```

## 3. Appointment Status Update

The related **Appointment** record gets updated:
- `status` changes from `"SCHEDULED"` to `"COMPLETE"`

## 4. Key Relationships in the Data Model

```
Appointment (1) ←→ (M) AppointmentPet ←→ (M) Pet
     ↓
   Visit (1 per pet per appointment)
     ↓
MedicalRecord (created separately by vets, not automatically)
```

## 5. What Does NOT Get Created Automatically

**Important:** The system does **NOT** automatically create:
- **Medical Records** - These must be created manually by veterinarians
- **Transcribed text** - The `full_text` field remains empty until processed
- **AI-generated summaries** - No automatic transcription service is currently implemented

## 6. Current State vs. Future Processing

**Current Implementation:**
- Audio file uploaded to S3
- Visit record created with metadata
- State set to "PROCESSING" but no actual processing occurs

**Missing/Future Features:**
- No transcription service (OpenAI Whisper, AWS Transcribe, etc.)
- No automatic medical record generation
- No AI analysis of visit content

## 7. Complete Data Flow

1. **User uploads recording** → Creates `Visit` record in `NEW` state
2. **Upload completes** → Updates `Visit` to `PROCESSING` state, sets S3 URL
3. **Appointment marked complete** → Updates `Appointment.status`
4. **Manual vet action needed** → Veterinarian must manually create `MedicalRecord`

## 8. Database Tables Involved

From the schema, these tables are involved in the visit recording process:

- `visits` - The main visit transcript record
- `appointments` - Updated to "complete" status  
- `appointment_pets` - Junction table linking appointments to pets
- `pets` - The pet being examined
- `veterinary_practices` - The practice where visit occurred
- `users` - The veterinarian who recorded
- `medical_records` - **Separate manual creation** by vets later

## 9. Agent Mode Context

I am now operating in agent mode with access to the full codebase. The system is designed to capture and store visit recordings but currently requires manual veterinarian input to convert those recordings into structured medical records.

**Key Files Analyzed:**
- `backend/src/models_pg/visit.py` - Visit model with state management
- `backend/src/models_pg/appointment.py` - Appointment and AppointmentPet models
- `backend/src/models_pg/medical_record.py` - Medical record model (manual creation)
- `backend/src/routes_pg/upload.py` - Audio upload endpoints
- `backend/src/routes_pg/visit_transcripts.py` - Visit transcript management
- `backend/src/services/s3_service.py` - S3 file handling
- `backend/src/services/rag_service.py` - RAG/AI services (for future transcription)

The system architecture supports future AI-powered transcription and medical record generation, but these features are not yet implemented.
