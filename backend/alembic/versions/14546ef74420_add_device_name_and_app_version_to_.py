"""add device_name and app_version to device_tokens

Revision ID: 14546ef74420
Revises: 1c30fd4a2aa5
Create Date: 2025-09-24 19:36:01.284849

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14546ef74420'
down_revision: Union[str, Sequence[str], None] = '1c30fd4a2aa5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing columns to device_tokens table
    op.add_column('device_tokens', sa.Column('device_name', sa.String(length=100), nullable=True))
    op.add_column('device_tokens', sa.Column('app_version', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the added columns
    op.drop_column('device_tokens', 'app_version')
    op.drop_column('device_tokens', 'device_name')
