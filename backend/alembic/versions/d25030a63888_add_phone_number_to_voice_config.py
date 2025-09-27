"""add_phone_number_to_voice_config

Revision ID: d25030a63888
Revises: 14546ef74420
Create Date: 2025-09-26 20:26:37.735866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd25030a63888'
down_revision: Union[str, Sequence[str], None] = '14546ef74420'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add phone_number column to voice_config table
    op.add_column('voice_config', sa.Column('phone_number', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove phone_number column from voice_config table
    op.drop_column('voice_config', 'phone_number')
