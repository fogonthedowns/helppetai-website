"""merge_heads

Revision ID: f5c47625eb88
Revises: 8efd67cd4a0a
Create Date: 2025-09-19 22:25:06.676535

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5c47625eb88'
down_revision: Union[str, Sequence[str], None] = '8efd67cd4a0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
