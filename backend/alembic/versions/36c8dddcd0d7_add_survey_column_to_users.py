"""add_survey_column_to_users

Revision ID: 36c8dddcd0d7
Revises: d25030a63888
Create Date: 2025-09-27 10:56:55.845845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36c8dddcd0d7'
down_revision: Union[str, Sequence[str], None] = 'd25030a63888'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add survey column to users table as optional JSON
    op.add_column('users', sa.Column('survey', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove survey column from users table
    op.drop_column('users', 'survey')
