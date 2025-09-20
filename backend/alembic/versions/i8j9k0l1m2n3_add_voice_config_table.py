"""add_voice_config_table

Revision ID: i8j9k0l1m2n3
Revises: h7i8j9k0l1m2
Create Date: 2025-09-20 00:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'i8j9k0l1m2n3'
down_revision: Union[str, Sequence[str], None] = 'h7i8j9k0l1m2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add voice_config table for practice voice settings."""
    
    op.create_table('voice_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('practice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('timezone', sa.String(), nullable=True, default='UTC'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default=sa.text("'{}'::jsonb")),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['practice_id'], ['veterinary_practices.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('practice_id', name='unique_practice_voice_config')
    )
    
    # Create indexes for performance
    op.create_index('idx_voice_config_practice_id', 'voice_config', ['practice_id'])
    op.create_index('idx_voice_config_agent_id', 'voice_config', ['agent_id'])
    op.create_index('idx_voice_config_active', 'voice_config', ['practice_id', 'is_active'])


def downgrade() -> None:
    """Remove voice_config table."""
    
    op.drop_index('idx_voice_config_active')
    op.drop_index('idx_voice_config_agent_id') 
    op.drop_index('idx_voice_config_practice_id')
    op.drop_table('voice_config')
