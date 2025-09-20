"""fix_midnight_spanning_availability

Revision ID: h7i8j9k0l1m2
Revises: c2d3e4f5g6h7
Create Date: 2025-09-20 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'h7i8j9k0l1m2'
down_revision: Union[str, Sequence[str], None] = 'dda2f13772d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove the broken constraint that prevents midnight-spanning availability."""
    
    # Drop the existing broken constraint that prevents midnight-spanning times
    op.execute("ALTER TABLE vet_availability DROP CONSTRAINT IF EXISTS valid_availability_times")
    
    # Also fix the recurring_availability table
    op.execute("ALTER TABLE recurring_availability DROP CONSTRAINT IF EXISTS valid_recurring_times")
    
    # Add a comment explaining that midnight-spanning times are allowed
    op.execute("""
        COMMENT ON COLUMN vet_availability.start_time IS 'Start time - can be greater than end_time for midnight-spanning slots'
    """)
    op.execute("""
        COMMENT ON COLUMN vet_availability.end_time IS 'End time - can be less than start_time for midnight-spanning slots'
    """)


def downgrade() -> None:
    """Restore the original (broken) constraints."""
    
    # WARNING: This will break midnight-spanning availability slots!
    op.execute("ALTER TABLE vet_availability ADD CONSTRAINT valid_availability_times CHECK (start_time < end_time)")
    op.execute("ALTER TABLE recurring_availability ADD CONSTRAINT valid_recurring_times CHECK (start_time < end_time)")
    
    # Remove comments
    op.execute("COMMENT ON COLUMN vet_availability.start_time IS NULL")
    op.execute("COMMENT ON COLUMN vet_availability.end_time IS NULL")

