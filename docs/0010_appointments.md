Appointments - REST API & Frontend Spec
Backend Requirements
Database Schema
sqlCREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_id UUID NOT NULL REFERENCES veterinary_practices(id) ON DELETE CASCADE,
    pet_owner_id UUID NOT NULL REFERENCES pet_owners(id) ON DELETE CASCADE,
    assigned_vet_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    appointment_date TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 30,
    appointment_type VARCHAR(50) NOT NULL, -- 'checkup', 'emergency', 'surgery', 'consultation'
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled', -- 'scheduled', 'confirmed', 'completed', 'cancelled', 'no_show'
    title VARCHAR(200) NOT NULL,
    description TEXT,
    notes TEXT,
    created_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE appointment_pets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    UNIQUE(appointment_id, pet_id)
);
REST Endpoints
Role Options: PetOwner, Admin, Vet

GET /api/v1/appointments/practice/{practice_uuid} - List appointments by practice (Admin | Practice Vets)
GET /api/v1/appointments/pet-owner/{owner_uuid} - List appointments by pet owner (Admin | Pet Owner | Associated Vets)
GET /api/v1/appointments/{uuid} - View single appointment (Admin | Pet Owner | Practice Vets)
POST /api/v1/appointments - Create appointment (Must be logged in - Vet or Admin)
PUT /api/v1/appointments/{uuid} - Update appointment (Admin | Practice Vets | Pet Owner for limited fields)
DELETE /api/v1/appointments/{uuid} - Cancel appointment (Admin | Practice Vets | Pet Owner)

Technical Specs

Use UUID primary keys
Must be logged in for all operations
Support multiple pets per appointment via junction table
Duration-based scheduling (default 30 minutes)
Status tracking for appointment lifecycle

Frontend Requirements
Pages/Components

Appointments section within Practice dashboard
Pet Owner appointments view within Pet Owner detail
Calendar/schedule view for practice staff
Create/Edit appointment modal
Appointment detail modal with pet selection
Appointment status management (confirm, complete, cancel)

Design

Follow existing UI patterns
Calendar/timeline view for scheduling
Multi-pet selection component
Status badges and workflow actions
Role-based rendering (Pet Owners: view/cancel, Vets: full CRUD)

React Integration

Appointments accessible from Practice dashboard (/practices/{uuid}/appointments)
Pet Owner appointments on Pet Owner detail (/pet_owners/{uuid})
Calendar component for scheduling
Pet multi-select in appointment forms

Acceptance Criteria

✅ All REST endpoints with proper HTTP methods
✅ UUID-based routing
✅ User must be logged in for all operations
✅ Support multiple pets per appointment
✅ Practice-based appointment management
✅ Pet Owners can view and cancel their appointments
✅ Vets can manage all practice appointments
✅ Status workflow (scheduled → confirmed → completed)
✅ Duration-based scheduling system
✅ Complex appointment support (multiple pets, times)

MVP Limitations:

Single practice per appointment (no multi-practice scheduling)
Basic time slot management (no conflict detection initially)
Simple appointment types (extensible via enum)