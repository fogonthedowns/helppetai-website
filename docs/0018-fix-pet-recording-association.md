# Fix Pet-Recording Association Issue

## Problem Statement

**CRITICAL DATA MODEL FLAW**: Recordings are currently associated with appointments but NOT with specific pets. This creates an impossible situation for the iOS team when trying to display pet-specific recordings.

### Current Broken Flow:
1. Appointment has multiple pets (e.g., Fluffy and Rex)
2. Recording is made during appointment 
3. Recording is linked to `appointment_id` only
4. **NO WAY to determine which pet the recording belongs to!**

### iOS Team Impact:
```swift
// This ALWAYS returns empty because recording.petId doesn't exist!
recordings.filter { recording in
    recording.petId == pet.id  // petId is nil!
}
```

## Root Cause Analysis

Looking at the current schema:

```sql
-- Appointments can have multiple pets
appointments 1 --> * appointment_pets * <-- 1 pets

-- Recordings are linked to appointments but NOT pets  
recordings * --> 1 appointments
recordings * --> 1 visits (visits are pet-specific)

-- THE PROBLEM: Missing direct pet association in recordings!
```

## Proposed Solution

### Option 1: Add Direct Pet Association (Recommended)

**Add `pet_id` to recordings table:**

```sql
ALTER TABLE recordings ADD COLUMN pet_id UUID;
ALTER TABLE recordings ADD CONSTRAINT fk_recordings_pet_id 
    FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE;
```

**Updated Recording Model:**
```python
class Recording(Base):
    # ... existing fields ...
    
    # NEW: Direct pet association
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,  # REQUIRED!
        index=True
    )
    
    # Keep existing appointment/visit associations for context
    appointment_id: Mapped[Optional[uuid.UUID]] = ...
    visit_id: Mapped[Optional[uuid.UUID]] = ...
```

### Option 2: Always Create Pet-Specific Visits

**Ensure every recording creates a corresponding visit:**

```python
# When recording is completed for appointment
for pet in appointment.pets:
    if recording_is_for_this_pet(recording, pet):
        visit = Visit(
            pet_id=pet.id,
            appointment_id=appointment.id,
            # ... other fields
        )
```

### Option 3: Hybrid Approach (Best Solution)

**Combine both approaches:**

1. **Add `pet_id` to recordings** for direct association
2. **Link visits to appointments** for full context
3. **Update API responses** to include pet-specific data

## Implementation Plan

### Phase 1: Database Migration

```sql
-- Add pet_id to recordings
ALTER TABLE recordings ADD COLUMN pet_id UUID;

-- Add appointment_id to visits for context
ALTER TABLE visits ADD COLUMN appointment_id UUID;

-- Add foreign key constraints
ALTER TABLE recordings ADD CONSTRAINT fk_recordings_pet_id 
    FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE;

ALTER TABLE visits ADD CONSTRAINT fk_visits_appointment_id 
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE;

-- Create indexes
CREATE INDEX idx_recordings_pet_id ON recordings(pet_id);
CREATE INDEX idx_visits_appointment_id ON visits(appointment_id);
```

### Phase 2: Update Models

```python
# Updated Recording model
class Recording(Base):
    # ... existing fields ...
    pet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("pets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relationships
    pet: Mapped["Pet"] = relationship("Pet", back_populates="recordings")

# Updated Visit model  
class Visit(Base):
    # ... existing fields ...
    appointment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Relationships
    appointment: Mapped[Optional["Appointment"]] = relationship("Appointment", back_populates="visits")
```

### Phase 3: Update API Responses

```python
class RecordingResponse(BaseModel):
    # ... existing fields ...
    pet_id: uuid.UUID  # NEW: Include pet_id in response
    
class AppointmentResponse(BaseModel):
    # ... existing fields ...
    recordings: List[RecordingResponse] = []  # NEW: Include recordings
    visits: List[VisitResponse] = []  # NEW: Include visits
```

### Phase 4: Update Recording Creation Logic

```python
@router.post("/upload/initiate")
async def initiate_recording_upload(
    request: RecordingUploadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    # REQUIRE pet_id for appointment recordings
    if request.appointment_id and not request.pet_id:
        raise HTTPException(
            status_code=400, 
            detail="pet_id is required for appointment recordings"
        )
    
    # Validate pet belongs to appointment
    if request.appointment_id and request.pet_id:
        appointment_pet = await db.execute(
            select(AppointmentPet).where(
                and_(
                    AppointmentPet.appointment_id == request.appointment_id,
                    AppointmentPet.pet_id == request.pet_id
                )
            )
        )
        if not appointment_pet.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Pet is not associated with this appointment"
            )
    
    # Create recording with pet_id
    recording = Recording(
        appointment_id=request.appointment_id,
        pet_id=request.pet_id,  # REQUIRED!
        # ... other fields
    )
```

## iOS Team Fix

After implementing the solution, iOS can filter correctly:

```swift
// This will now work correctly!
recordings.filter { recording in
    recording.petId == pet.id
}
```

## Data Validation Rules

1. **For appointment recordings**: `pet_id` must be provided and pet must be associated with appointment
2. **For standalone recordings**: `pet_id` must be provided  
3. **For visit creation**: Both `pet_id` and optional `appointment_id` are stored

## Migration Strategy

1. **Backward Compatibility**: Keep existing recordings working during transition
2. **Data Backfill**: For existing recordings, attempt to infer `pet_id` from related visits
3. **Gradual Rollout**: Implement new constraints only for new recordings initially

## Testing Scenarios

1. **Single Pet Appointment**: Recording correctly associated with pet
2. **Multi Pet Appointment**: Each recording associated with correct pet
3. **Visit Creation**: Visit links to both pet and appointment
4. **API Responses**: Recordings properly filtered by pet
5. **Error Cases**: Invalid pet/appointment combinations rejected

This fix resolves the fundamental data model flaw and enables proper pet-specific recording functionality.
