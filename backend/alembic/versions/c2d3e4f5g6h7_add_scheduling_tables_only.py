"""add_scheduling_tables_only

Revision ID: c2d3e4f5g6h7
Revises: a1b2c3d4e5f6
Create Date: 2025-09-13 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5g6h7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add scheduling system enums and tables."""
    
    connection = op.get_bind()
    
    # Create enums first (only if they don't exist)
    result = connection.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'availabilitytype'"))
    if not result.fetchone():
        op.execute("CREATE TYPE availabilitytype AS ENUM ('AVAILABLE', 'SURGERY_BLOCK', 'UNAVAILABLE', 'EMERGENCY_ONLY')")
    
    result = connection.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'conflicttype'"))
    if not result.fetchone():
        op.execute("CREATE TYPE conflicttype AS ENUM ('DOUBLE_BOOKED', 'OVERLAPPING', 'OUTSIDE_AVAILABILITY', 'PRACTICE_CLOSED')")
    
    result = connection.execute(sa.text("SELECT 1 FROM pg_type WHERE typname = 'conflictseverity'"))
    if not result.fetchone():
        op.execute("CREATE TYPE conflictseverity AS ENUM ('WARNING', 'ERROR')")
    
    # Create practice_hours table (only if it doesn't exist)
    result = connection.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = 'practice_hours'"))
    if not result.fetchone():
        op.execute("""
            CREATE TABLE practice_hours (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                practice_id UUID NOT NULL REFERENCES veterinary_practices(id) ON DELETE CASCADE,
                day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
                open_time TIME,
                close_time TIME,
                effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
                effective_until DATE,
                notes TEXT,
                is_active BOOLEAN NOT NULL DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT valid_times CHECK (
                    (open_time IS NULL AND close_time IS NULL) OR 
                    (open_time IS NOT NULL AND close_time IS NOT NULL AND open_time < close_time)
                ),
                CONSTRAINT valid_effective_dates CHECK (effective_until IS NULL OR effective_until >= effective_from),
                UNIQUE(practice_id, day_of_week, effective_from, effective_until)
            )
        """)
        
        # Create indexes for practice_hours
        op.execute("CREATE INDEX idx_practice_hours_lookup ON practice_hours(practice_id, day_of_week, effective_from, effective_until, is_active)")
    
    # Create vet_availability table (only if it doesn't exist)
    result = connection.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = 'vet_availability'"))
    if not result.fetchone():
        op.execute("""
            CREATE TABLE vet_availability (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                vet_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                practice_id UUID NOT NULL REFERENCES veterinary_practices(id) ON DELETE CASCADE,
                date DATE NOT NULL,
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                availability_type availabilitytype NOT NULL DEFAULT 'AVAILABLE',
                notes TEXT,
                is_active BOOLEAN NOT NULL DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT valid_availability_times CHECK (start_time < end_time),
                UNIQUE(vet_user_id, date, start_time, end_time)
            )
        """)
        
        # Create indexes for vet_availability
        op.execute("CREATE INDEX idx_vet_availability_lookup ON vet_availability(practice_id, date, vet_user_id, is_active)")
        op.execute("CREATE INDEX idx_vet_availability_active_date ON vet_availability(vet_user_id, date, is_active)")
    
    # Create recurring_availability table (only if it doesn't exist)
    result = connection.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = 'recurring_availability'"))
    if not result.fetchone():
        op.execute("""
            CREATE TABLE recurring_availability (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                vet_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                practice_id UUID NOT NULL REFERENCES veterinary_practices(id) ON DELETE CASCADE,
                day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6),
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                availability_type availabilitytype NOT NULL DEFAULT 'AVAILABLE',
                effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
                effective_until DATE,
                is_active BOOLEAN NOT NULL DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT valid_recurring_times CHECK (start_time < end_time),
                CONSTRAINT valid_recurring_dates CHECK (effective_until IS NULL OR effective_until >= effective_from),
                UNIQUE(vet_user_id, day_of_week, start_time, end_time, effective_from)
            )
        """)
        
        # Create indexes for recurring_availability
        op.execute("CREATE INDEX idx_recurring_availability_active ON recurring_availability(vet_user_id, practice_id, day_of_week, effective_from, effective_until)")
    
    # Create appointment_conflict table (only if it doesn't exist)
    result = connection.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = 'appointment_conflict'"))
    if not result.fetchone():
        op.execute("""
            CREATE TABLE appointment_conflict (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
                conflicting_appointment_id UUID REFERENCES appointments(id) ON DELETE CASCADE,
                conflict_type conflicttype NOT NULL,
                severity conflictseverity NOT NULL DEFAULT 'WARNING',
                message TEXT NOT NULL,
                resolved BOOLEAN NOT NULL DEFAULT false,
                resolved_by_user_id UUID REFERENCES users(id),
                resolved_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for appointment_conflict
        op.execute("CREATE INDEX idx_appointment_conflict_unresolved ON appointment_conflict(appointment_id, conflict_type, severity)")
    
    # Add appointment_id column to visits table (linking visits to appointments)
    result = connection.execute(sa.text("""
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'visits' AND column_name = 'appointment_id'
    """))
    if not result.fetchone():
        op.execute("ALTER TABLE visits ADD COLUMN appointment_id UUID REFERENCES appointments(id)")
    
    # Create additional performance indexes
    try:
        op.execute("CREATE INDEX idx_appointment_practice_date_status ON appointments(practice_id, appointment_date, status)")
    except:
        pass  # Index might already exist
    
    try:
        op.execute("CREATE INDEX idx_appointment_vet_date_status ON appointments(assigned_vet_user_id, appointment_date, status)")
    except:
        pass  # Index might already exist


def downgrade() -> None:
    """Remove scheduling system tables."""
    
    # Drop indexes (ignore errors if they don't exist)
    try:
        op.execute("DROP INDEX IF EXISTS idx_appointment_vet_date_status")
        op.execute("DROP INDEX IF EXISTS idx_appointment_practice_date_status")
        op.execute("DROP INDEX IF EXISTS idx_appointment_conflict_unresolved")
        op.execute("DROP INDEX IF EXISTS idx_recurring_availability_active")
        op.execute("DROP INDEX IF EXISTS idx_vet_availability_active_date")
        op.execute("DROP INDEX IF EXISTS idx_vet_availability_lookup")
        op.execute("DROP INDEX IF EXISTS idx_practice_hours_lookup")
    except:
        pass
    
    # Remove appointment_id column from visits
    try:
        op.execute("ALTER TABLE visits DROP COLUMN IF EXISTS appointment_id")
    except:
        pass
    
    # Drop tables
    op.execute("DROP TABLE IF EXISTS appointment_conflict")
    op.execute("DROP TABLE IF EXISTS recurring_availability")
    op.execute("DROP TABLE IF EXISTS vet_availability")
    op.execute("DROP TABLE IF EXISTS practice_hours")
