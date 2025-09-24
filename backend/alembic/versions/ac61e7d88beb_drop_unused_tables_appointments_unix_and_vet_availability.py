"""drop_unused_appointments_unix_and_vet_availability_tables

Drop unused tables:
1. appointments_unix - Created but never used by production systems
2. vet_availability - Old table replaced by vet_availability_unix

Investigation Results (2025-09-24):
✅ Voice system uses UnixTimestampSchedulingService → vet_availability_unix table
✅ iPhone uses /api/v1/appointments endpoints (regular appointments table)  
✅ Old /api/v1/scheduling/vet-availability endpoints return HTTP 418 (deprecated)
✅ New /api/v1/scheduling-unix/vet-availability endpoints are active
✅ AppointmentUnix model/repository are commented out (never used)
✅ Old VetAvailability model/repository are only used by deprecated endpoints

SAFE TO DROP: No production impact - systems use vet_availability_unix and appointments

Revision ID: ac61e7d88beb
Revises: f3717ef87724
Create Date: 2025-09-24 12:31:38.474075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ac61e7d88beb'
down_revision: Union[str, Sequence[str], None] = 'f3717ef87724'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the unused tables."""
    # Drop the unused appointments_unix table and all associated constraints/indexes
    op.drop_table('appointments_unix')
    
    # Drop the old vet_availability table (replaced by vet_availability_unix)
    op.drop_table('vet_availability')


def downgrade() -> None:
    """Recreate both tables if needed for rollback."""
    
    # 1. Recreate vet_availability table (old table structure)
    op.execute("""
        CREATE TABLE vet_availability (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            vet_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            practice_id UUID NOT NULL REFERENCES veterinary_practices(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            availability_type VARCHAR(50) NOT NULL DEFAULT 'AVAILABLE'
                CHECK (availability_type IN ('AVAILABLE', 'SURGERY_BLOCK', 'UNAVAILABLE', 'EMERGENCY_ONLY')),
            notes TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT valid_availability_times CHECK (start_time < end_time),
            UNIQUE(vet_user_id, date, start_time, end_time)
        )
    """)
    
    # Recreate vet_availability indexes
    op.execute("CREATE INDEX idx_vet_availability_lookup ON vet_availability(practice_id, date, vet_user_id, is_active)")
    op.execute("CREATE INDEX idx_vet_availability_active_date ON vet_availability(vet_user_id, date, is_active)")
    
    # 2. Recreate appointments_unix table (never used but for rollback)
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
    
    # Recreate appointments_unix indexes
    op.execute("CREATE INDEX idx_appointments_unix_practice_id ON appointments_unix(practice_id)")
    op.execute("CREATE INDEX idx_appointments_unix_assigned_vet_user_id ON appointments_unix(assigned_vet_user_id)")
    op.execute("CREATE INDEX idx_appointments_unix_appointment_at ON appointments_unix(appointment_at)")
    op.execute("CREATE INDEX idx_appointments_unix_status ON appointments_unix(status)")
    op.execute("CREATE INDEX idx_appointments_unix_vet_date_status ON appointments_unix(assigned_vet_user_id, appointment_at, status)")
    op.execute("CREATE INDEX idx_appointments_unix_practice_date_status ON appointments_unix(practice_id, appointment_at, status)")
    
    # Add triggers for updated_at
    op.execute("CREATE TRIGGER update_vet_availability_updated_at BEFORE UPDATE ON vet_availability FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")
    op.execute("CREATE TRIGGER update_appointments_unix_updated_at BEFORE UPDATE ON appointments_unix FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()")
