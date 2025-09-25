"""add_device_tokens_table_for_push_notifications

Revision ID: 1c30fd4a2aa5
Revises: ac61e7d88beb
Create Date: 2025-09-24 18:52:28.641308

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c30fd4a2aa5'
down_revision: Union[str, Sequence[str], None] = 'ac61e7d88beb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create device_tokens table for push notifications
    op.create_table(
        'device_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('device_token', sa.String(length=200), nullable=False),
        sa.Column('device_type', sa.String(length=20), nullable=False, server_default='ios'),
        sa.Column('device_name', sa.String(length=100), nullable=True),
        sa.Column('app_version', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('device_token')
    )
    
    # Create indexes for performance
    op.create_index('ix_device_tokens_user_id', 'device_tokens', ['user_id'])
    op.create_index('ix_device_tokens_is_active', 'device_tokens', ['is_active'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('ix_device_tokens_is_active', table_name='device_tokens')
    op.drop_index('ix_device_tokens_user_id', table_name='device_tokens')
    
    # Drop table
    op.drop_table('device_tokens')
