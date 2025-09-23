"""add_unix_timestamp_scheduling_tables

Revision ID: f3717ef87724
Revises: f5c47625eb88
Create Date: 2025-09-23 07:49:22.475606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3717ef87724'
down_revision: Union[str, Sequence[str], None] = 'f5c47625eb88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add Unix timestamp scheduling tables.
    
    This implements the major timezone refactor from suggestion.txt:
    - Replace date + start_time + end_time with start_at + end_at TIMESTAMPTZ
    - Store everything in UTC using Unix timestamps
    - Eliminate timezone ambiguity and phantom shifts
    """
    
    # Create vet_availability_unix table with Unix timestamps
    op.execute("""
        CREATE TABLE vet_availability_unix (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            vet_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            practice_id UUID NOT NULL REFERENCES veterinary_practices(id) ON DELETE CASCADE,
            start_at TIMESTAMPTZ NOT NULL,
            end_at TIMESTAMPTZ NOT NULL,
            availability_type VARCHAR(50) NOT NULL DEFAULT 'AVAILABLE'
                CHECK (availability_type IN ('AVAILABLE', 'SURGERY_BLOCK', 'UNAVAILABLE', 'EMERGENCY_ONLY')),
            notes TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    
    # Create indexes for performance
    op.execute("""
        CREATE INDEX idx_vet_availability_unix_vet_user_id 
        ON vet_availability_unix(vet_user_id)
    """)
    
    op.execute("""
        CREATE INDEX idx_vet_availability_unix_practice_id 
        ON vet_availability_unix(practice_id)
    """)
    
    op.execute("""
        CREATE INDEX idx_vet_availability_unix_start_at 
        ON vet_availability_unix(start_at)
    """)
    
    op.execute("""
        CREATE INDEX idx_vet_availability_unix_end_at 
        ON vet_availability_unix(end_at)
    """)
    
    # Create advanced time range index for efficient overlap queries
    op.execute("""
        CREATE INDEX idx_vet_availability_unix_timerange 
        ON vet_availability_unix USING GIST (tstzrange(start_at, end_at))
    """)
    
    # Create appointments_unix table with Unix timestamps
    op.execute("""
        CREATE TABLE appointments_unix (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            practice_id UUID NOT NULL REFERENCES veterinary_practices(id) ON DELETE CASCADE,
            pet_owner_id UUID NOT NULL REFERENCES pet_owners(id) ON DELETE CASCADE,
            assigned_vet_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            created_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
            appointment_at TIMESTAMPTZ NOT NULL,
            duration_minutes INTEGER NOT NULL DEFAULT 30,
            appointment_type VARCHAR(50) NOT NULL DEFAULT 'CHECKUP',
            status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED'
                CHECK (status IN ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW')),
            title VARCHAR(200) NOT NULL,
            description TEXT,
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    
    # Create indexes for appointments_unix
    op.execute("""
        CREATE INDEX idx_appointments_unix_practice_id 
        ON appointments_unix(practice_id)
    """)
    
    op.execute("""
        CREATE INDEX idx_appointments_unix_assigned_vet_user_id 
        ON appointments_unix(assigned_vet_user_id)
    """)
    
    op.execute("""
        CREATE INDEX idx_appointments_unix_appointment_at 
        ON appointments_unix(appointment_at)
    """)
    
    op.execute("""
        CREATE INDEX idx_appointments_unix_status 
        ON appointments_unix(status)
    """)
    
    # Combined index for common queries
    op.execute("""
        CREATE INDEX idx_appointments_unix_practice_date_status 
        ON appointments_unix(practice_id, appointment_at, status)
    """)
    
    op.execute("""
        CREATE INDEX idx_appointments_unix_vet_date_status 
        ON appointments_unix(assigned_vet_user_id, appointment_at, status)
    """)
    
    # NOTE: Data migration removed - tables created empty
    # Services will start fresh with Unix timestamp tables
    
    # Add trigger to keep updated_at current for both tables
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)
    
    op.execute("""
        CREATE TRIGGER update_vet_availability_unix_updated_at 
        BEFORE UPDATE ON vet_availability_unix 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)
    
    op.execute("""
        CREATE TRIGGER update_appointments_unix_updated_at 
        BEFORE UPDATE ON appointments_unix 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
    """)


def downgrade() -> None:
    """Remove Unix timestamp tables and triggers."""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_appointments_unix_updated_at ON appointments_unix")
    op.execute("DROP TRIGGER IF EXISTS update_vet_availability_unix_updated_at ON vet_availability_unix")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_appointments_unix_vet_date_status")
    op.execute("DROP INDEX IF EXISTS idx_appointments_unix_practice_date_status") 
    op.execute("DROP INDEX IF EXISTS idx_appointments_unix_status")
    op.execute("DROP INDEX IF EXISTS idx_appointments_unix_appointment_at")
    op.execute("DROP INDEX IF EXISTS idx_appointments_unix_assigned_vet_user_id")
    op.execute("DROP INDEX IF EXISTS idx_appointments_unix_practice_id")
    
    op.execute("DROP INDEX IF EXISTS idx_vet_availability_unix_timerange")
    op.execute("DROP INDEX IF EXISTS idx_vet_availability_unix_end_at")
    op.execute("DROP INDEX IF EXISTS idx_vet_availability_unix_start_at")
    op.execute("DROP INDEX IF EXISTS idx_vet_availability_unix_practice_id")
    op.execute("DROP INDEX IF EXISTS idx_vet_availability_unix_vet_user_id")
    
    # Drop tables
    op.execute("DROP TABLE IF EXISTS appointments_unix")
    op.execute("DROP TABLE IF EXISTS vet_availability_unix")
