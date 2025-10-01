"""add_practice_invitations_table

Revision ID: e35dfc936408
Revises: 36c8dddcd0d7
Create Date: 2025-10-01 10:18:25.265857

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e35dfc936408'
down_revision: Union[str, Sequence[str], None] = '36c8dddcd0d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create practice_invitations table
    op.create_table(
        'practice_invitations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('practice_id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('invite_code', sa.String(length=255), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['practice_id'], ['veterinary_practices.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invite_code')
    )
    
    # Create indexes
    op.create_index(op.f('ix_practice_invitations_email'), 'practice_invitations', ['email'], unique=False)
    op.create_index(op.f('ix_practice_invitations_practice_id'), 'practice_invitations', ['practice_id'], unique=False)
    op.create_index(op.f('ix_practice_invitations_status'), 'practice_invitations', ['status'], unique=False)
    op.create_index(op.f('ix_practice_invitations_invite_code'), 'practice_invitations', ['invite_code'], unique=True)
    
    # Add PENDING_INVITE to UserRole enum (if not using native enum)
    # Since we're using String-based enum, no migration needed for the enum itself


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_practice_invitations_invite_code'), table_name='practice_invitations')
    op.drop_index(op.f('ix_practice_invitations_status'), table_name='practice_invitations')
    op.drop_index(op.f('ix_practice_invitations_practice_id'), table_name='practice_invitations')
    op.drop_index(op.f('ix_practice_invitations_email'), table_name='practice_invitations')
    
    # Drop table
    op.drop_table('practice_invitations')
