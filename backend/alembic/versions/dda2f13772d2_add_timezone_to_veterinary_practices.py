"""add_timezone_to_veterinary_practices

Revision ID: dda2f13772d2
Revises: c2d3e4f5g6h7
Create Date: 2025-09-14 07:16:26.296819

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dda2f13772d2'
down_revision: Union[str, Sequence[str], None] = 'c2d3e4f5g6h7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add timezone column to veterinary_practices table."""
    # Add timezone column with default value
    op.add_column('veterinary_practices', sa.Column('timezone', sa.String(length=50), nullable=False, server_default='America/Los_Angeles'))


def downgrade() -> None:
    """Remove timezone column from veterinary_practices table."""
    op.drop_column('veterinary_practices', 'timezone')
