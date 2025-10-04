"""add stripe customer table

Revision ID: k0l1m2n3o4p5
Revises: 4f5e6d7c8b9a
Create Date: 2025-10-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = 'k0l1m2n3o4p5'
down_revision = '4f5e6d7c8b9a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create stripe_customers table
    op.create_table(
        'stripe_customers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('practice_id', UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('created_by_user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('default_payment_method_id', sa.String(255), nullable=True),
        sa.Column('balance_credits_cents', sa.Integer(), nullable=False, server_default='1000'),  # $10.00 in credits
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['practice_id'], ['veterinary_practices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
    )


def downgrade() -> None:
    op.drop_table('stripe_customers')

