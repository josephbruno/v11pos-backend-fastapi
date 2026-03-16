"""add icon_url to modifiers

Revision ID: c9b1b5f4a6d7
Revises: a0bca7fcbf05
Create Date: 2026-03-16
"""
from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c9b1b5f4a6d7"
down_revision: Union[str, None] = "a0bca7fcbf05"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column("modifiers", sa.Column("icon_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("modifiers", "icon_url")
