"""add_pending_invite_to_userrole

Revision ID: 4f5e6d7c8b9a
Revises: 1e43ed585281
Create Date: 2025-10-02 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f5e6d7c8b9a'
down_revision: Union[str, Sequence[str], None] = '1e43ed585281'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add PENDING_INVITE to userrole enum."""
    # PostgreSQL enum alterations must be done outside of a transaction
    # So we use execute with the appropriate isolation level
    
    # Get the connection
    connection = op.get_bind()
    
    # Execute enum additions outside transaction using COMMIT/BEGIN trick
    connection.execute(sa.text("COMMIT"))
    try:
        connection.execute(sa.text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'PENDING_INVITE'"))
    finally:
        connection.execute(sa.text("BEGIN"))


def downgrade() -> None:
    """No downgrade possible for enum alterations."""
    pass
