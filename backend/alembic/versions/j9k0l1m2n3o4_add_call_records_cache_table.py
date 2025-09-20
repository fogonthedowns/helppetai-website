"""add_call_records_cache_table

Revision ID: j9k0l1m2n3o4
Revises: i8j9k0l1m2n3
Create Date: 2025-09-20 04:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'j9k0l1m2n3o4'
down_revision: Union[str, Sequence[str], None] = 'i8j9k0l1m2n3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add call_records table for caching Retell API data."""
    
    op.create_table('call_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('practice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('call_id', sa.String(), nullable=False, unique=True),
        sa.Column('agent_id', sa.String(), nullable=True),
        sa.Column('recording_url', sa.String(), nullable=True),
        sa.Column('start_timestamp', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('end_timestamp', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('from_number', sa.String(), nullable=True),
        sa.Column('to_number', sa.String(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('call_status', sa.String(), nullable=True),
        sa.Column('disconnect_reason', sa.String(), nullable=True),
        
        # Call analysis data
        sa.Column('call_successful', sa.Boolean(), nullable=True),
        sa.Column('call_summary', sa.Text(), nullable=True),
        sa.Column('user_sentiment', sa.String(), nullable=True),
        sa.Column('in_voicemail', sa.Boolean(), nullable=True),
        sa.Column('custom_analysis_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default=sa.text("'{}'::jsonb")),
        
        # Caller identification
        sa.Column('caller_pet_owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Cache metadata
        sa.Column('last_synced_at', sa.TIMESTAMP(timezone=True), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('sync_status', sa.String(), nullable=False, default='pending'),  # pending, synced, error
        sa.Column('sync_error', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        
        sa.ForeignKeyConstraint(['practice_id'], ['veterinary_practices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['caller_pet_owner_id'], ['pet_owners.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('call_id', name='unique_call_id')
    )
    
    # Create indexes for performance
    op.create_index('idx_call_records_practice_date', 'call_records', ['practice_id', 'start_timestamp'])
    op.create_index('idx_call_records_sync_status', 'call_records', ['sync_status', 'last_synced_at'])
    op.create_index('idx_call_records_active', 'call_records', ['practice_id', 'is_active', 'start_timestamp'])
    op.create_index('idx_call_records_call_id', 'call_records', ['call_id'])
    
    # Additional performance indexes
    op.create_index('idx_call_records_practice_only', 'call_records', ['practice_id'])  # Simple practice queries
    op.create_index('idx_call_records_timestamp_desc', 'call_records', [sa.text('start_timestamp DESC')])  # Recent calls first
    op.create_index('idx_call_records_stale_sync', 'call_records', ['last_synced_at', 'sync_status'])  # Find stale records


def downgrade() -> None:
    """Remove call_records table."""
    
    # Drop additional indexes
    op.drop_index('idx_call_records_stale_sync')
    op.drop_index('idx_call_records_timestamp_desc')
    op.drop_index('idx_call_records_practice_only')
    
    # Drop original indexes
    op.drop_index('idx_call_records_call_id')
    op.drop_index('idx_call_records_active')
    op.drop_index('idx_call_records_sync_status')
    op.drop_index('idx_call_records_practice_date')
    op.drop_table('call_records')
