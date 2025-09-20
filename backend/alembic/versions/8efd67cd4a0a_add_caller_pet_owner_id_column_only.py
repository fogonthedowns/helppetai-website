"""add_caller_pet_owner_id_column_only

Revision ID: 8efd67cd4a0a
Revises: c7c5853cc1eb
Create Date: 2025-09-19 22:17:25.534092

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8efd67cd4a0a'
down_revision: Union[str, Sequence[str], None] = 'j9k0l1m2n3o4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add caller_pet_owner_id column to call_records table."""
    # Add the column without foreign key constraint for now
    op.add_column('call_records', sa.Column('caller_pet_owner_id', postgresql.UUID(as_uuid=True), nullable=True))


def downgrade() -> None:
    """Remove caller_pet_owner_id column from call_records table."""
    op.drop_column('call_records', 'caller_pet_owner_id')
