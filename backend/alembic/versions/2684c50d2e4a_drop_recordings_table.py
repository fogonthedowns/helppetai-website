"""drop_recordings_table

Revision ID: 2684c50d2e4a
Revises: f1a2b3c4d5e6
Create Date: 2025-09-02 00:56:11.659589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2684c50d2e4a'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop recordings table - replaced by simplified Visit_Transcripts approach."""
    # Drop indexes first
    op.drop_index('ix_recordings_visit_id', table_name='recordings')
    op.drop_index('ix_recordings_status', table_name='recordings')
    op.drop_index('ix_recordings_recorded_by_user_id', table_name='recordings')
    op.drop_index('ix_recordings_is_deleted', table_name='recordings')
    op.drop_index('ix_recordings_appointment_id', table_name='recordings')
    
    # Drop the table
    op.drop_table('recordings')


def downgrade() -> None:
    """Recreate recordings table if needed to rollback."""
    # This would recreate the recordings table, but since we're eliminating it,
    # we'll leave this empty. If rollback is needed, restore from the previous migration.
    pass
