"""Normalize all restaurant timezones to Asia/Kolkata (IST).

Revision ID: a3b4c5d6e7f8
Revises: e1f2a3b4c5d6
Create Date: 2026-06-26

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

IST_TIMEZONE = "Asia/Kolkata"


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE restaurants "
            "SET timezone = :tz "
            "WHERE timezone IS NULL OR timezone <> :tz"
        ).bindparams(tz=IST_TIMEZONE)
    )


def downgrade() -> None:
    # Data migration: previous per-restaurant timezone values are not preserved.
    pass
