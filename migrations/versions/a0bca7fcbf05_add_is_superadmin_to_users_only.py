"""add_is_superadmin_to_users_only

Revision ID: a0bca7fcbf05
Revises: 206573838321
Create Date: 2025-12-31 15:48:30.575119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0bca7fcbf05'
down_revision: Union[str, None] = '206573838321'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_superadmin', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'is_superadmin')
