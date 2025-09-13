-- Complete PostgreSQL Schema for Veterinary Scheduling System
-- MVP Version with Practice Hours Hard Constraint

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE user_role AS ENUM ('VET_STAFF', 'PET_OWNER', 'ADMIN');
CREATE TYPE preferred_communication AS ENUM ('EMAIL', 'SMS', 'PHONE');
CREATE TYPE association_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'INACTIVE');
CREATE TYPE association_request_type AS ENUM ('NEW_CLIENT', 'REFERRAL', 'TRANSFER', 'EMERGENCY');
CREATE TYPE appointment_type AS ENUM ('CHECKUP', 'EMERGENCY', 'SURGERY', 'CONSULTATION', 'FOLLOW_UP', 'VACCINATION');
CREATE TYPE appointment_status AS ENUM ('SCHEDULED', 'IN_PROGRESS', 'COMPLETE', 'ERROR', 'CONFIRMED', 'COMPLETED', 'CANCELLED', 'NO_SHOW');
CREATE TYPE visit_state AS ENUM ('NEW', 'PROCESSING', 'PROCESSED', 'FAILED');
CREATE TYPE availability_type AS ENUM ('AVAILABLE', 'SURGERY_BLOCK', 'UNAVAILABLE', 'EMERGENCY_ONLY');
CREATE TYPE conflict_type AS ENUM ('DOUBLE_BOOKED', 'OVERLAPPING', 'OUTSIDE_AVAILABILITY', 'PRACTICE_CLOSED');
CREATE TYPE conflict_severity AS ENUM ('WARNING', 'ERROR');

-- ============================================================================
-- EXISTING CORE TABLES (from your original schema)
-- ============================================================================

CREATE TABLE veterinary_practice (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    description TEXT,
    phone VARCHAR,
    email VARCHAR,
    website VARCHAR,
    address_line1 VARCHAR,
    address_line2 VARCHAR,
    city VARCHAR,
    state VARCHAR,
    zip_code VARCHAR,
    country VARCHAR DEFAULT 'US',
    license_number VARCHAR UNIQUE,
    tax_id VARCHAR,
    hours_of_operation TEXT, -- Legacy field, use practice_hours table instead
    emergency_contact VARCHAR,
    max_appointments_per_day INTEGER,
    is_active BOOLEAN DEFAULT true,
    accepts_new_patients BOOLEAN DEFAULT true,
    specialties JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    email VARCHAR UNIQUE,
    full_name VARCHAR NOT NULL,
    role user_role NOT NULL,
    practice_id UUID REFERENCES veterinary_practice(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pet_owner (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    full_name VARCHAR NOT NULL,
    email VARCHAR,
    phone VARCHAR,
    emergency_contact VARCHAR,
    secondary_phone VARCHAR,
    address TEXT,
    preferred_communication preferred_communication DEFAULT 'EMAIL',
    notifications_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pet (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES pet_owner(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    species VARCHAR NOT NULL,
    breed VARCHAR,
    color VARCHAR,
    gender VARCHAR,
    weight DECIMAL(5,2),
    date_of_birth DATE,
    microchip_id VARCHAR UNIQUE,
    spayed_neutered BOOLEAN,
    allergies TEXT,
    medications TEXT,
    medical_notes TEXT,
    emergency_contact VARCHAR,
    emergency_phone VARCHAR,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE appointment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_id UUID NOT NULL REFERENCES veterinary_practice(id),
    pet_owner_id UUID NOT NULL REFERENCES pet_owner(id),
    assigned_vet_user_id UUID REFERENCES users(id),
    created_by_user_id UUID NOT NULL REFERENCES users(id),
    appointment_date TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    appointment_type appointment_type DEFAULT 'CHECKUP',
    status appointment_status DEFAULT 'SCHEDULED',
    title VARCHAR NOT NULL,
    description TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE appointment_pet (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointment(id) ON DELETE CASCADE,
    pet_id UUID NOT NULL REFERENCES pet(id) ON DELETE CASCADE,
    UNIQUE(appointment_id, pet_id)
);

CREATE TABLE visit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID REFERENCES appointment(id), -- NEW: Link to appointment
    pet_id UUID NOT NULL REFERENCES pet(id),
    practice_id UUID NOT NULL REFERENCES veterinary_practice(id),
    vet_user_id UUID REFERENCES users(id),
    visit_date TIMESTAMP WITH TIME ZONE NOT NULL,
    full_text TEXT NOT NULL,
    audio_transcript_url VARCHAR,
    summary TEXT,
    state visit_state DEFAULT 'NEW',
    additional_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE TABLE pet_owner_practice_association (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_owner_id UUID NOT NULL REFERENCES pet_owner(id) ON DELETE CASCADE,
    practice_id UUID NOT NULL REFERENCES veterinary_practice(id) ON DELETE CASCADE,
    status association_status DEFAULT 'PENDING',
    request_type association_request_type DEFAULT 'NEW_CLIENT',
    requested_by_user_id UUID REFERENCES users(id),
    approved_by_user_id UUID REFERENCES users(id),
    requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP WITH TIME ZONE,
    last_visit_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    primary_contact BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- NEW SCHEDULING TABLES
-- ============================================================================

-- Practice operating hours (hard constraint)
CREATE TABLE practice_hours (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    practice_id UUID NOT NULL REFERENCES veterinary_practice(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6), -- 0=Sunday, 6=Saturday
    open_time TIME, -- NULL means closed all day
    close_time TIME, -- NULL means closed all day
    effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_until DATE, -- NULL means indefinite
    notes TEXT, -- e.g., "Closed for holidays"
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_times CHECK (
        (open_time IS NULL AND close_time IS NULL) OR 
        (open_time IS NOT NULL AND close_time IS NOT NULL AND open_time < close_time)
    ),
    CONSTRAINT valid_effective_dates CHECK (effective_until IS NULL OR effective_until >= effective_from),
    
    -- Unique constraint to prevent overlapping schedules
    UNIQUE(practice_id, day_of_week, effective_from, effective_until)
);

-- Individual vet availability
CREATE TABLE vet_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vet_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    practice_id UUID NOT NULL REFERENCES veterinary_practice(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    availability_type availability_type DEFAULT 'AVAILABLE',
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_availability_times CHECK (start_time < end_time),
    CONSTRAINT vet_is_staff CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = vet_user_id AND role = 'VET_STAFF'
        )
    ),
    
    -- Unique constraint to prevent overlapping availability for same vet
    UNIQUE(vet_user_id, date, start_time, end_time)
);

-- Recurring availability templates (to generate vet_availability records)
CREATE TABLE recurring_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vet_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    practice_id UUID NOT NULL REFERENCES veterinary_practice(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    availability_type availability_type DEFAULT 'AVAILABLE',
    effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_until DATE, -- NULL means indefinite
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_recurring_times CHECK (start_time < end_time),
    CONSTRAINT valid_recurring_dates CHECK (effective_until IS NULL OR effective_until >= effective_from),
    CONSTRAINT recurring_vet_is_staff CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = vet_user_id AND role = 'VET_STAFF'
        )
    ),
    
    -- Unique constraint to prevent overlapping recurring schedules
    UNIQUE(vet_user_id, day_of_week, start_time, end_time, effective_from)
);

-- Track scheduling conflicts (informational, doesn't block)
CREATE TABLE appointment_conflict (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointment(id) ON DELETE CASCADE,
    conflicting_appointment_id UUID REFERENCES appointment(id) ON DELETE CASCADE,
    conflict_type conflict_type NOT NULL,
    severity conflict_severity DEFAULT 'WARNING',
    message TEXT NOT NULL,
    resolved BOOLEAN DEFAULT false,
    resolved_by_user_id UUID REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- ============================================================================
-- CORE SCHEDULING INDEXES (Most Critical)
-- ============================================================================

-- Main appointment queries - compound indexes for common filtering patterns
CREATE INDEX idx_appointment_practice_date_status ON appointment(practice_id, appointment_date, status);
CREATE INDEX idx_appointment_vet_date_status ON appointment(assigned_vet_user_id, appointment_date, status);
CREATE INDEX idx_appointment_date_range ON appointment(appointment_date) WHERE status NOT IN ('CANCELLED', 'NO_SHOW', 'COMPLETED');

-- Vet availability queries - optimized for scheduling lookups
CREATE INDEX idx_vet_availability_lookup ON vet_availability(practice_id, date, vet_user_id, is_active);
CREATE INDEX idx_vet_availability_active_date ON vet_availability(vet_user_id, date, is_active) WHERE is_active = true;
CREATE INDEX idx_vet_availability_date_range ON vet_availability(date, practice_id) WHERE is_active = true;

-- Practice hours - optimized for business hours checks
CREATE INDEX idx_practice_hours_lookup ON practice_hours(practice_id, day_of_week, effective_from, effective_until, is_active);
CREATE INDEX idx_practice_hours_active ON practice_hours(practice_id, day_of_week) WHERE is_active = true;

-- ============================================================================
-- SCHEDULING CONFLICT DETECTION INDEXES
-- ============================================================================

-- Overlap detection for double-booking prevention
CREATE INDEX idx_appointment_overlap_detection ON appointment(assigned_vet_user_id, appointment_date, duration_minutes) 
    WHERE status NOT IN ('CANCELLED', 'NO_SHOW', 'COMPLETED');

-- Time-based availability checks
CREATE INDEX idx_vet_availability_time_overlap ON vet_availability(vet_user_id, date, start_time, end_time, availability_type)
    WHERE is_active = true;

-- Recurring availability pattern matching
CREATE INDEX idx_recurring_availability_active ON recurring_availability(vet_user_id, practice_id, day_of_week, effective_from, effective_until)
    WHERE is_active = true;

-- ============================================================================
-- SEARCH AND FILTER INDEXES
-- ============================================================================

-- Pet owner searches and associations
CREATE INDEX idx_pet_owner_search ON pet_owner(practice_id, full_name) WHERE full_name IS NOT NULL;
CREATE INDEX idx_pet_owner_contact ON pet_owner(email, phone) WHERE email IS NOT NULL OR phone IS NOT NULL;

-- Pet searches within owner
CREATE INDEX idx_pet_search ON pet(owner_id, name, species, is_active) WHERE is_active = true;
CREATE INDEX idx_pet_microchip ON pet(microchip_id) WHERE microchip_id IS NOT NULL;

-- User role-based queries
CREATE INDEX idx_users_practice_role ON users(practice_id, role, is_active) WHERE is_active = true;
CREATE INDEX idx_users_vet_staff ON users(practice_id, role) WHERE role = 'VET_STAFF' AND is_active = true;

-- ============================================================================
-- RELATIONSHIP AND JOIN OPTIMIZATION
-- ============================================================================

-- Appointment-Pet many-to-many optimization
CREATE INDEX idx_appointment_pet_lookup ON appointment_pet(appointment_id, pet_id);
CREATE INDEX idx_appointment_pet_reverse ON appointment_pet(pet_id, appointment_id);

-- Visit-Appointment relationship
CREATE INDEX idx_visit_appointment_date ON visit(appointment_id, visit_date);
CREATE INDEX idx_visit_pet_date ON visit(pet_id, visit_date);
CREATE INDEX idx_visit_practice_date ON visit(practice_id, visit_date, state);

-- Practice associations
CREATE INDEX idx_pet_owner_practice_status ON pet_owner_practice_association(practice_id, pet_owner_id, status);
CREATE INDEX idx_pet_owner_practice_primary ON pet_owner_practice_association(pet_owner_id, practice_id) WHERE primary_contact = true;

-- ============================================================================
-- REPORTING AND ANALYTICS INDEXES
-- ============================================================================

-- Daily/weekly scheduling reports
CREATE INDEX idx_appointment_reporting ON appointment(practice_id, appointment_date::date, appointment_type, status);
CREATE INDEX idx_appointment_vet_reporting ON appointment(assigned_vet_user_id, appointment_date::date, status);

-- Vet utilization analysis
CREATE INDEX idx_vet_availability_utilization ON vet_availability(vet_user_id, date, availability_type) WHERE is_active = true;

-- Visit tracking and follow-ups
CREATE INDEX idx_visit_follow_up ON visit(pet_id, visit_date, state) WHERE state = 'PROCESSED';

-- ============================================================================
-- CONFLICT AND AUDIT INDEXES
-- ============================================================================

-- Appointment conflict tracking
CREATE INDEX idx_appointment_conflict_unresolved ON appointment_conflict(appointment_id, conflict_type, severity) WHERE resolved = false;
CREATE INDEX idx_appointment_conflict_timeline ON appointment_conflict(created_at, severity, resolved);

-- ============================================================================
-- PARTIAL INDEXES (PostgreSQL-Specific Optimizations)
-- ============================================================================

-- Active appointments only (excludes completed/cancelled)
CREATE INDEX idx_appointment_active_only ON appointment(practice_id, appointment_date, assigned_vet_user_id) 
    WHERE status IN ('SCHEDULED', 'IN_PROGRESS', 'CONFIRMED');

-- Today's appointments (for daily view optimization)
CREATE INDEX idx_appointment_today ON appointment(practice_id, assigned_vet_user_id, appointment_date) 
    WHERE appointment_date::date = CURRENT_DATE AND status NOT IN ('CANCELLED', 'NO_SHOW');

-- Available vets only
CREATE INDEX idx_vet_availability_available_only ON vet_availability(practice_id, date, vet_user_id, start_time, end_time)
    WHERE is_active = true AND availability_type IN ('AVAILABLE', 'EMERGENCY_ONLY');

-- Emergency appointments
CREATE INDEX idx_appointment_emergency ON appointment(practice_id, appointment_date, status)
    WHERE appointment_type = 'EMERGENCY';

-- ============================================================================
-- TEXT SEARCH INDEXES (for names, notes, etc.)
-- ============================================================================

-- Full-text search on pet owner names and contact info
CREATE INDEX idx_pet_owner_text_search ON pet_owner USING gin(to_tsvector('english', 
    COALESCE(full_name, '') || ' ' || COALESCE(email, '') || ' ' || COALESCE(phone, '')));

-- Pet name and breed searching
CREATE INDEX idx_pet_text_search ON pet USING gin(to_tsvector('english', 
    COALESCE(name, '') || ' ' || COALESCE(breed, '') || ' ' || COALESCE(species, '')));

-- Appointment title and notes search
CREATE INDEX idx_appointment_text_search ON appointment USING gin(to_tsvector('english',
    COALESCE(title, '') || ' ' || COALESCE(description, '') || ' ' || COALESCE(notes, '')));

-- ============================================================================
-- UNIQUE CONSTRAINTS AS INDEXES
-- ============================================================================

-- Prevent duplicate vet availability for same time slot
CREATE UNIQUE INDEX idx_vet_availability_unique_slot ON vet_availability(vet_user_id, date, start_time, end_time)
    WHERE is_active = true;

-- Ensure one primary contact per practice
CREATE UNIQUE INDEX idx_pet_owner_practice_primary_unique ON pet_owner_practice_association(pet_owner_id, practice_id)
    WHERE primary_contact = true AND status = 'APPROVED';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to check if practice is open at a specific time
CREATE OR REPLACE FUNCTION is_practice_open(
    p_practice_id UUID,
    p_check_time TIMESTAMP WITH TIME ZONE
) RETURNS BOOLEAN AS $$
DECLARE
    v_day_of_week INTEGER;
    v_check_time TIME;
    v_open_time TIME;
    v_close_time TIME;
    v_found BOOLEAN := FALSE;
BEGIN
    -- Extract day of week and time
    v_day_of_week := EXTRACT(DOW FROM p_check_time);
    v_check_time := p_check_time::TIME;
    
    -- Find matching practice hours
    SELECT ph.open_time, ph.close_time INTO v_open_time, v_close_time
    FROM practice_hours ph
    WHERE ph.practice_id = p_practice_id
        AND ph.day_of_week = v_day_of_week
        AND ph.is_active = true
        AND ph.effective_from <= p_check_time::DATE
        AND (ph.effective_until IS NULL OR ph.effective_until >= p_check_time::DATE);
    
    GET DIAGNOSTICS v_found = FOUND;
    
    -- If no hours found or times are NULL (closed), return false
    IF NOT v_found OR v_open_time IS NULL OR v_close_time IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Check if time is within operating hours
    RETURN v_check_time >= v_open_time AND v_check_time <= v_close_time;
END;
$$ LANGUAGE plpgsql;

-- Function to get available appointment slots for a vet on a specific date
CREATE OR REPLACE FUNCTION get_available_slots(
    p_practice_id UUID,
    p_vet_user_id UUID,
    p_date DATE,
    p_slot_duration_minutes INTEGER DEFAULT 30
) RETURNS TABLE(
    slot_start TIME,
    slot_end TIME,
    availability_type availability_type
) AS $$
BEGIN
    RETURN QUERY
    WITH vet_schedule AS (
        SELECT va.start_time, va.end_time, va.availability_type
        FROM vet_availability va
        WHERE va.vet_user_id = p_vet_user_id
            AND va.practice_id = p_practice_id
            AND va.date = p_date
            AND va.is_active = true
    ),
    time_slots AS (
        SELECT 
            generate_series(
                vs.start_time,
                vs.end_time - INTERVAL '1 minute' * p_slot_duration_minutes,
                INTERVAL '1 minute' * p_slot_duration_minutes
            )::TIME as start_time,
            vs.availability_type
        FROM vet_schedule vs
    ),
    existing_appointments AS (
        SELECT 
            a.appointment_date::TIME as appt_start,
            (a.appointment_date + INTERVAL '1 minute' * a.duration_minutes)::TIME as appt_end
        FROM appointment a
        WHERE a.assigned_vet_user_id = p_vet_user_id
            AND a.appointment_date::DATE = p_date
            AND a.status NOT IN ('CANCELLED', 'NO_SHOW', 'COMPLETED')
    )
    SELECT 
        ts.start_time as slot_start,
        (ts.start_time + INTERVAL '1 minute' * p_slot_duration_minutes)::TIME as slot_end,
        ts.availability_type
    FROM time_slots ts
    LEFT JOIN existing_appointments ea ON (
        ea.appt_start < (ts.start_time + INTERVAL '1 minute' * p_slot_duration_minutes)
        AND ea.appt_end > ts.start_time
    )
    WHERE ea.appt_start IS NULL  -- No conflict
    ORDER BY ts.start_time;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_veterinary_practice_updated_at BEFORE UPDATE ON veterinary_practice FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pet_owner_updated_at BEFORE UPDATE ON pet_owner FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pet_updated_at BEFORE UPDATE ON pet FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_appointment_updated_at BEFORE UPDATE ON appointment FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_visit_updated_at BEFORE UPDATE ON visit FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pet_owner_practice_association_updated_at BEFORE UPDATE ON pet_owner_practice_association FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_practice_hours_updated_at BEFORE UPDATE ON practice_hours FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vet_availability_updated_at BEFORE UPDATE ON vet_availability FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_recurring_availability_updated_at BEFORE UPDATE ON recurring_availability FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SAMPLE DATA INSERTS (for testing)
-- ============================================================================

-- Sample practice
INSERT INTO veterinary_practice (id, name, phone, email, is_active) 
VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Happy Paws Veterinary Clinic', '555-0123', 'info@happypaws.com', true);

-- Sample practice hours (Monday-Friday 8 AM - 6 PM, Saturday 9 AM - 4 PM, Sunday closed)
INSERT INTO practice_hours (practice_id, day_of_week, open_time, close_time) VALUES
('550e8400-e29b-41d4-a716-446655440000', 1, '08:00:00', '18:00:00'), -- Monday
('550e8400-e29b-41d4-a716-446655440000', 2, '08:00:00', '18:00:00'), -- Tuesday
('550e8400-e29b-41d4-a716-446655440000', 3, '08:00:00', '18:00:00'), -- Wednesday
('550e8400-e29b-41d4-a716-446655440000', 4, '08:00:00', '18:00:00'), -- Thursday
('550e8400-e29b-41d4-a716-446655440000', 5, '08:00:00', '18:00:00'), -- Friday
('550e8400-e29b-41d4-a716-446655440000', 6, '09:00:00', '16:00:00'), -- Saturday
('550e8400-e29b-41d4-a716-446655440000', 0, NULL, NULL);             -- Sunday (closed)

-- Sample vet
INSERT INTO users (id, username, password_hash, email, full_name, role, practice_id) 
VALUES ('660e8400-e29b-41d4-a716-446655440000', 'dr.smith', 'hashed_password', 'smith@happypaws.com', 'Dr. Sarah Smith', 'VET_STAFF', '550e8400-e29b-41d4-a716-446655440000');

-- Sample recurring availability for Dr. Smith (Monday-Friday 9 AM - 5 PM)
INSERT INTO recurring_availability (vet_user_id, practice_id, day_of_week, start_time, end_time) VALUES
('660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 1, '09:00:00', '17:00:00'), -- Monday
('660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 2, '09:00:00', '17:00:00'), -- Tuesday
('660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 3, '09:00:00', '17:00:00'), -- Wednesday
('660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 4, '09:00:00', '17:00:00'), -- Thursday
('660e8400-e29b-41d4-a716-446655440000', '550e8400-e29b-41d4-a716-446655440000', 5, '09:00:00', '17:00:00'); -- Friday

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE practice_hours IS 'Practice operating hours - hard constraint for scheduling';
COMMENT ON TABLE vet_availability IS 'Individual vet availability for specific dates';
COMMENT ON TABLE recurring_availability IS 'Templates for generating regular vet schedules';
COMMENT ON TABLE appointment_conflict IS 'Tracks scheduling conflicts for staff review';

COMMENT ON FUNCTION is_practice_open(UUID, TIMESTAMP WITH TIME ZONE) IS 'Returns true if practice is open at the specified time';
COMMENT ON FUNCTION get_available_slots(UUID, UUID, DATE, INTEGER) IS 'Returns available appointment slots for a vet on a specific date';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================