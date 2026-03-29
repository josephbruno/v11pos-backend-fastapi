"""Merge multiple heads

Revision ID: cb0f4438b485
Revises: 8551eace5f9a, c9b1b5f4a6d7
Create Date: 2026-03-29 13:13:24.456102

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb0f4438b485'
down_revision: Union[str, None] = ('8551eace5f9a', 'c9b1b5f4a6d7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
