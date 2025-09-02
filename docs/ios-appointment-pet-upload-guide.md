# iOS Engineering Guide: Appointments and Pet Uploads

## CRITICAL ISSUE IDENTIFIED

The iOS engineers are incorrectly propagating a single pet upload across ALL appointments. This is fundamentally wrong and violates the core data model.

## How the System ACTUALLY Works (per React Implementation)

### 1. Data Model Relationships

```
Appointment (1) ←→ (M) AppointmentPet (M) ←→ (1) Pet
Visit (1) ←→ (1) Pet
Visit.additional_data.appointment_id ←→ Appointment.id
```

**Key Points:**
- Each **Visit** is linked to exactly **ONE Pet**
- Each **Visit** can optionally be linked to **ONE Appointment**
- Each **Appointment** can have **MULTIPLE Pets**
- Each **Pet** upload creates a **SEPARATE Visit record**

### 2. Correct Upload Workflow

When uploading audio for an appointment with multiple pets:

```
Appointment ABC123 has pets: [Pet1, Pet2, Pet3]

Correct approach:
- Upload for Pet1 → Creates Visit1 (pet_id=Pet1, appointment_id=ABC123)
- Upload for Pet2 → Creates Visit2 (pet_id=Pet2, appointment_id=ABC123) 
- Upload for Pet3 → Creates Visit3 (pet_id=Pet3, appointment_id=ABC123)

WRONG approach (what iOS is doing):
- Upload for Pet1 → Creates Visit1 for Pet1, Pet2, Pet3 (WRONG!)
```

### 3. API Endpoints iOS Must Use

#### Upload Audio for Specific Pet in Appointment
```http
POST /api/v1/upload/audio
Content-Type: multipart/form-data

Fields:
- audio: [audio file]
- appointment_id: "abc123-def4-5678-90ab-cdef12345678"  
- pet_id: "pet456-789a-bcde-f012-3456789abcde"
```

**Critical Requirements:**
1. **BOTH** `appointment_id` AND `pet_id` are REQUIRED
2. Each upload call creates ONE visit for ONE pet
3. The backend validates that the pet belongs to the appointment
4. If a visit already exists for this appointment+pet combination, returns HTTP 409 Conflict

#### Get Appointments for Pet Owner
```http
GET /api/v1/appointments/pet-owner/{ownerUuid}
Authorization: Bearer {token}
```

Response includes pets array for each appointment:
```json
{
  "id": "appointment-uuid",
  "pets": [
    {"id": "pet1-uuid", "name": "Fluffy", "species": "dog"},
    {"id": "pet2-uuid", "name": "Mittens", "species": "cat"}
  ],
  // ... other appointment fields
}
```

### 4. React Frontend Implementation (CORRECT EXAMPLE)

From `AppointmentPetRecorder.tsx`:

```typescript
// Separate recording state per pet
const [recordings, setRecordings] = useState<Record<string, RecordingState>>({});

// Upload function - ONE pet at a time
const uploadRecording = async (petId: string) => {
  const recording = recordings[petId];
  if (!recording.audioBlob || !appointmentId) return;

  // Generate filename for THIS specific pet and appointment
  const fileName = generateAudioFileName(appointmentId, petId);
  
  // Upload with BOTH appointment and pet IDs
  const result = await uploadAudioToS3(
    recording.audioBlob, 
    fileName, 
    appointmentId,  // ← Required
    petId          // ← Required  
  );

  // Update ONLY this pet's recording state
  setRecordings(prev => ({
    ...prev,
    [petId]: {
      ...prev[petId],
      isUploading: false,
      uploadSuccess: true,
      visitId: result.visitId  // ← Each pet gets its own visit ID
    }
  }));
};
```

### 5. Backend Validation Logic

The backend enforces correctness:

```python
# From upload.py lines 104-117
# Verify this pet is part of the appointment
appointment_pet_result = await db.execute(
    select(AppointmentPet).where(
        AppointmentPet.appointment_id == appointment_uuid,
        AppointmentPet.pet_id == pet_uuid
    )
)
appointment_pet = appointment_pet_result.scalar_one_or_none()

if not appointment_pet:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Pet {pet_id} is not associated with appointment {appointment_id}"
    )
```

### 6. Visit Record Creation (Per Pet)

Each upload creates ONE visit:

```python
# From upload.py lines 191-207
visit = Visit(
    pet_id=target_pet_id,                    # ← Specific pet only
    practice_id=appointment.practice_id,
    vet_user_id=current_user.id,
    visit_date=appointment.appointment_date,
    audio_transcript_url=s3_url,
    additional_data={
        "appointment_id": str(appointment.id),  # ← Links to appointment
        "audio_s3_key": s3_key,
        "recorded_by": str(current_user.id),
    },
    created_by=current_user.id
)
```

### 7. iOS Implementation Requirements

**Must Do:**
1. Store appointment-to-pets mapping from API response
2. Record audio separately for each pet
3. Upload each recording with correct `appointment_id` + `pet_id` combination
4. Handle each upload response individually
5. Track upload status per pet (not per appointment)

**Must NOT Do:**
1. ❌ Upload one recording for multiple pets
2. ❌ Propagate single upload across all pets in appointment  
3. ❌ Create visit records for pets that weren't actually recorded

### 8. Example iOS Flow

```swift
// 1. Get appointment with pets
let appointment = await getAppointment(id: appointmentId)
let pets = appointment.pets

// 2. Record for each pet individually
for pet in pets {
    // Start recording for THIS pet only
    let recording = startRecordingForPet(pet.id)
    
    // Stop and upload for THIS pet only
    let audioData = stopRecording()
    
    // Upload with BOTH IDs
    let uploadResult = await uploadAudio(
        audioData: audioData,
        appointmentId: appointment.id,
        petId: pet.id  // ← Critical: specific pet ID
    )
    
    // Store visit ID for THIS pet
    petVisitMap[pet.id] = uploadResult.visitId
}
```

### 9. Common Mistakes iOS Is Making

1. **Single Upload for Multiple Pets**: Creating one visit record and trying to associate it with multiple pets
2. **Missing Pet ID**: Not sending the specific pet_id in upload requests  
3. **State Propagation**: Updating UI state for all pets when only one pet's upload completes
4. **Wrong Data Model Understanding**: Thinking appointments have recordings instead of pets having recordings

### 10. API Error Responses to Handle

```http
HTTP 400 Bad Request
{
  "detail": "Both appointment_id and pet_id are required for visit recording"
}

HTTP 400 Bad Request  
{
  "detail": "Pet {pet_id} is not associated with appointment {appointment_id}"
}

HTTP 409 Conflict
{
  "detail": "Recording already exists for this appointment and pet. Visit ID: {visit_id}"
}
```

### 11. Testing Your Implementation

Verify your iOS implementation by:
1. Creating an appointment with 3 pets
2. Recording audio for each pet separately  
3. Checking that 3 separate visit records are created in the database
4. Ensuring each visit has the correct pet_id and appointment_id
5. Verifying uploads don't interfere with each other

---

## SUMMARY FOR iOS ENGINEERS

**The fundamental rule**: Each pet gets its own recording, its own upload, and its own visit record. There is NO such thing as an "appointment recording" - only "pet recordings" that happen to be associated with an appointment.

Stop thinking in terms of appointments having recordings. Start thinking in terms of pets having recordings that are optionally linked to appointments.

The React team got this right. Follow their implementation pattern.
