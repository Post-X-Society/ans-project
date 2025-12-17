"""merge heads

Revision ID: e015fdaaaad0
Revises: 001, 74a3438eeb0f
Create Date: 2025-12-17 09:57:43.175755

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e015fdaaaad0'
down_revision: Union[str, None] = ('001', '74a3438eeb0f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
