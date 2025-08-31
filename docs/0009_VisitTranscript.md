Visit Transcripts - REST API & Frontend Spec
Backend Requirements
REST Endpoints
Role Options: PetOwner, Admin, Vet

GET /api/v1/visit-transcripts/pet/{pet_uuid} - List all visit transcripts for a pet (Admin | Pet Owner | Associated Vet)
GET /api/v1/visit-transcripts/{uuid} - View single visit transcript (Admin | Pet Owner | Associated Vet)
POST /api/v1/visit-transcripts - Create visit transcript (Must be logged in - Vet or Admin only)
PUT /api/v1/visit-transcripts/{uuid} - Update visit transcript (Admin | Creating Vet only)
DELETE /api/v1/visit-transcripts/{uuid} - Delete visit transcript (Admin only)

Technical Specs

Use UUID primary keys
Must be logged in for all operations
Link to pets via pet_id foreign key
Fields: uuid, pet_id, visit_date (int32 unix timestamp), full_text, audio_transcript_url, metadata (JSON), summary, state
State enum: processed | processing | new | failed
Multiple transcripts per pet (one-to-many relationship)

Frontend Requirements
Pages/Components

Visit Transcripts section within Pet detail view
Visit History list showing all transcripts chronologically
Add Visit Transcript button (Vets/Admins only)
Visit Transcript create/edit form
Visit Transcript detail modal with audio player
Processing status indicators for transcript states

Design

Follow existing UI patterns from /pets and medical records
Chronological list/timeline view
State badges (Processing spinner, Success checkmark, Failed warning)
Audio player component for transcript URLs
Role-based rendering (Pet Owners: read-only, Vets: can add/edit)

React Integration

Visit Transcripts displayed under Pet detail page (/pets/{uuid})
Separate tab/section from Medical Records
Add Visit Transcript button for authorized users
Expandable cards showing transcript summary with full detail modal
Real-time state updates for processing transcripts

Acceptance Criteria

✅ All REST endpoints with proper HTTP methods
✅ UUID-based routing
✅ User must be logged in for all operations
✅ Only Vets/Admins can create/edit visit transcripts
✅ Pet Owners can view all transcripts for their pets
✅ Multiple transcripts per pet supported
✅ State management with visual indicators
✅ Audio transcript URL playback capability
✅ Transcripts accessible via Pet detail page
✅ Cross-practice visibility (any associated vet can view full history)
✅ Unix timestamp handling for visit dates