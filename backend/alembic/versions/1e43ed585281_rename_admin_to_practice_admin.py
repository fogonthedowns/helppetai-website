"""rename_admin_to_practice_admin

Revision ID: 1e43ed585281
Revises: e35dfc936408
Create Date: 2025-10-01 13:49:48.870668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e43ed585281'
down_revision: Union[str, Sequence[str], None] = 'e35dfc936408'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing enum values and rename ADMIN role to PRACTICE_ADMIN."""
    # PostgreSQL enum alterations must be done outside of a transaction
    # So we use execute with the appropriate isolation level
    
    # Get the connection
    connection = op.get_bind()
    
    # Execute enum additions outside transaction using COMMIT/BEGIN trick
    connection.execute(sa.text("COMMIT"))
    try:
        # Add PENDING_INVITE (was missing from previous migration)
        connection.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'PENDING_INVITE'"))
        # Add new admin role types
        connection.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'PRACTICE_ADMIN'"))
        connection.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SYSTEM_ADMIN'"))
    finally:
        connection.execute(sa.text("BEGIN"))
    
    # Now update existing users with ADMIN role to PRACTICE_ADMIN
    op.execute("UPDATE users SET role = 'PRACTICE_ADMIN' WHERE role = 'ADMIN'")


def downgrade() -> None:
    """Revert PRACTICE_ADMIN back to ADMIN."""
    # Revert PRACTICE_ADMIN back to ADMIN
    op.execute("UPDATE users SET role = 'ADMIN' WHERE role = 'PRACTICE_ADMIN'")
    # Note: Cannot easily remove enum values in PostgreSQL, so PRACTICE_ADMIN and SYSTEM_ADMIN will remain
