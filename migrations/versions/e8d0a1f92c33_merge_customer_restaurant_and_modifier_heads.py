"""merge customer restaurant head with modifier relationships head

Revision ID: e8d0a1f92c33
Revises: 4f41bbce5566, f3a9c1e47d20
Create Date: 2026-05-02

"""
from typing import Sequence, Union

from alembic import op


revision: str = "e8d0a1f92c33"
down_revision: Union[str, None] = ("4f41bbce5566", "f3a9c1e47d20")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
