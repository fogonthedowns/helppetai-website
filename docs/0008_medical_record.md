Medical Records - REST API & Frontend Spec
Backend Requirements
REST Endpoints
Role Options: PetOwner, Admin, Vet

GET /api/v1/medical-records/pet/{pet_uuid} - List all medical records for a pet (Admin | Pet Owner | Associated Vet)
GET /api/v1/medical-records/{uuid} - View single medical record (Admin | Pet Owner | Associated Vet)
POST /api/v1/medical-records - Create medical record (Must be logged in - Vet or Admin only)
PUT /api/v1/medical-records/{uuid} - Update medical record (Admin | Creating Vet only)
DELETE /api/v1/medical-records/{uuid} - Delete medical record (Admin only)

React paths:

pets/{uuid}/medical-records
pets/{uuid}/medical-records/{uuid}

Technical Specs

Use UUID primary keys
Must be logged in for all operations
Link to pets via pet_id foreign key
Version control: create new record with incremented version instead of updating
Current record flagged with is_current: true
JSON content field for flexible medical data storage

Frontend Requirements
Pages/Components

Medical Records section within Pet detail view
Medical History timeline showing all versions
Add Medical Record button (Vets/Admins only)
Medical Record create/edit form
Medical Record detail modal

Design

Follow existing UI patterns from /pets and /pet_owners
Timeline/accordion view for medical history
Version indicator for each record
Role-based rendering (Pet Owners: read-only, Vets: can add/edit)

React Integration

Medical Records displayed under Pet detail page (/pets/{uuid})
Add Medical Record button for authorized users
Expandable timeline showing record versions
Modal for detailed record view

Acceptance Criteria

✅ All REST endpoints with proper HTTP methods
✅ UUID-based routing
✅ User must be logged in for all operations
✅ Only Vets/Admins can create/edit medical records
✅ Pet Owners can view all records for their pets
✅ Version control maintains medical history
✅ Records accessible via Pet detail page
✅ Cross-practice visibility (any associated vet can view full history)