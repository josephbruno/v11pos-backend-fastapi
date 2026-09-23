"""add printer_type and data_format to receipt_printers

Revision ID: a76ecec3f625
Revises: f1de57c350cd
Create Date: 2026-09-23 02:50:42.604557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a76ecec3f625'
down_revision: Union[str, None] = 'f1de57c350cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'receipt_printers',
        sa.Column('printer_type', sa.String(length=20), nullable=False, server_default='ZEBRA'),
    )
    op.add_column(
        'receipt_printers',
        sa.Column('data_format', sa.String(length=10), nullable=False, server_default='text'),
    )
    op.alter_column('receipt_printers', 'printer_type', server_default=None)
    op.alter_column('receipt_printers', 'data_format', server_default=None)


def downgrade() -> None:
    op.drop_column('receipt_printers', 'data_format')
    op.drop_column('receipt_printers', 'printer_type')
